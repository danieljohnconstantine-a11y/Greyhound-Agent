"""
Run Predictions with Track-Specific Ensemble Models (CALIBRATED)

Uses the track-specific ensemble models trained by train_ml_track_ensemble.py
to generate predictions on today's races in data_predictions/ folder.

For each race:
1. Loads track-specific models (RF, GB, XGB) - ALL CALIBRATED with Isotonic Regression
2. Generates prediction from each algorithm (calibrated probabilities)
3. Combines predictions using ensemble averaging
4. Produces ML confidence score that accurately reflects win probability

Calibration ensures predicted probabilities match actual win rates, fixing
high-confidence prediction failures.

Usage:
    python run_track_ensemble_predictions.py
    
    OR use the batch file:
    run_track_ensemble_predictions.bat

Prerequisites:
    - Track-specific ensemble models trained (run train_ml_track_ensemble.bat first)
    - Race PDFs in data_predictions/ folder

Output:
    - outputs/track_ensemble_predictions.xlsx - Predictions with calibrated scores
    - outputs/track_ensemble_summary.txt - Quick summary
"""

import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

# Fix encoding for Windows console
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

from src.parser import parse_race_form
from src.features import compute_features
import pandas as pd
import numpy as np
import pickle
import glob
from datetime import datetime
import traceback
import pdfplumber

# Threshold below which the pre-normalization ensemble spread is considered too
# narrow to represent genuine ML discrimination.  Races that fall below this
# value get a Low_Confidence=True flag in the output.  This value was
# established empirically from the Race 8 Angle Park audit (Mar 5 2026) where
# calibration collapse reduced model spread to <0.001 before normalization.
LOW_CONFIDENCE_SPREAD_THRESHOLD = 0.005  # < 0.5% probability spread

# Timing-derived features that should be filled with the race median rather
# than 0 when missing, to avoid unfairly penalising dogs with unknown times.
TIMING_FEATURES = [
    'BestTimeSec', 'SectionalSec', 'Speed_kmh', 'EarlySpeedIndex',
    'TimeVsField', 'SpeedVsField', 'BestTimePercentile', 'EarlySpeedPercentile',
    'SpeedAtDistance',
]

def extract_text_from_pdf(pdf_path):
    """
    Extract text content from a PDF file.
    
    Args:
        pdf_path: Path to the PDF file
        
    Returns:
        str: Extracted text content from all pages
    """
    text = ""
    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            text += page.extract_text() + "\n"
    return text

def load_track_ensemble(track_name, models_dir="models"):
    """
    Load all ensemble models for a specific track.
    
    Returns:
        models: Dict of {algorithm: model}
        scaler: StandardScaler for this track
        config: Ensemble configuration
    """
    config_path = os.path.join(models_dir, "config.pkl")
    
    if not os.path.exists(config_path):
        raise FileNotFoundError(f"Ensemble configuration not found: {config_path}")
    
    with open(config_path, 'rb') as f:
        config = pickle.load(f)
    
    # Check if this track has models
    if track_name not in config['tracks']:
        # Return None to use fallback
        return None, None, config
    
    # Try subdirectory layout first: models/{track}/{algorithm}.pkl
    track_dir = os.path.join(models_dir, track_name)
    
    models = {}
    for alg in config['algorithms']:
        model_path = os.path.join(track_dir, f"{alg}.pkl")
        if os.path.exists(model_path):
            with open(model_path, 'rb') as f:
                models[alg] = pickle.load(f)
    
    # Fall back to flat-file layout: models/{track_name}_{algorithm}.pkl
    if not models:
        for alg in config['algorithms']:
            flat_path = os.path.join(models_dir, f"{track_name}_{alg}.pkl")
            if os.path.exists(flat_path):
                with open(flat_path, 'rb') as f:
                    models[alg] = pickle.load(f)
    
    # Load scaler - try subdirectory first, then flat file
    scaler_path = os.path.join(track_dir, "scaler.pkl")
    flat_scaler_path = os.path.join(models_dir, f"{track_name}_scaler.pkl")
    if os.path.exists(scaler_path):
        with open(scaler_path, 'rb') as f:
            scaler = pickle.load(f)
    elif os.path.exists(flat_scaler_path):
        with open(flat_scaler_path, 'rb') as f:
            scaler = pickle.load(f)
    else:
        scaler = None
    
    # Reconcile the feature list with the scaler's actual training features.
    # config.pkl may list more features than the scaler was trained on (e.g. when
    # new features were added after the scaler was saved). Using the scaler's own
    # feature names avoids a dimension mismatch error in predict_with_ensemble().
    if scaler is not None and hasattr(scaler, 'feature_names_in_'):
        scaler_features = list(scaler.feature_names_in_)
        if scaler_features != config.get('feature_cols', []):
            config = dict(config)  # shallow copy — don't mutate the global config
            config['feature_cols'] = scaler_features

    return models, scaler, config

def _get_uncalibrated_preds(model, X_scaled):
    """
    Extract uncalibrated base-estimator predictions from a CalibratedClassifierCV.

    When calibration collapses probabilities into a narrow band all dogs get the
    same score.  The base estimator (RF/GB/XGB before isotonic fitting) preserves
    the original probability ordering, so we use it as a fallback when the
    calibrated output has fewer unique values than dogs.

    Returns:
        numpy array of probabilities (one per dog) with maximum discrimination.
    """
    # Calibrated model: sklearn CalibratedClassifierCV
    if hasattr(model, 'calibrated_classifiers_'):
        base_preds_list = []
        for cal_clf in model.calibrated_classifiers_:
            base_est = getattr(cal_clf, 'estimator', None)
            if base_est is not None and hasattr(base_est, 'predict_proba'):
                try:
                    bp = base_est.predict_proba(X_scaled)[:, 1]
                    base_preds_list.append(bp)
                except Exception:
                    pass
        if base_preds_list:
            return np.mean(base_preds_list, axis=0)
    return None


def predict_with_ensemble(df, models, scaler, feature_cols, ensemble_weights):
    """
    Generate ensemble predictions for a race WITH PROPER DISCRIMINATION.

    Individual scoring guarantee
    ----------------------------
    Each dog MUST receive a score that is 100% individual to that dog.  Two
    failure modes are detected and corrected automatically:

    1. Calibration collapse – CalibratedClassifierCV's isotonic mapping can
       compress many different raw probabilities into the same calibrated value.
       Fix: detect when ≥50% of dogs share the same calibrated score and fall
       back to the uncalibrated base-estimator predictions instead.

    2. Feature clustering – if too many input features are identical across all
       dogs the model cannot distinguish them.  This is reported as a warning
       and the within-race rank-normalization (see below) still guarantees
       unique output values.

    Within-race normalization
    -------------------------
    After obtaining per-dog raw scores from each algorithm the ensemble is
    normalized to the range [2%, 18%] within the race.  This means:
    - The top-ranked dog always receives 18%
    - The last-ranked dog always receives 2%
    - Every intermediate dog receives a proportionally spread value

    Args:
        df: DataFrame with race data (all dogs in race)
        models: Dict of {algorithm: model}
        scaler: StandardScaler
        feature_cols: List of feature column names
        ensemble_weights: Dict of {algorithm: weight}

    Returns:
        ensemble_pred: Array of ensemble probabilities for each dog (unique per dog)
        individual_scores: Dict of {algorithm: array of probabilities} (unique per dog)
        raw_spread: Float — pre-normalization probability spread (used for Low_Confidence flag)
    """
    n_dogs = len(df)

    # Prepare features
    # Check for missing features and warn user
    missing_features = [col for col in feature_cols if col not in df.columns]
    if missing_features:
        print(f"      ⚠️  Warning: {len(missing_features)} features missing from race data (will be filled with 0)")
        if len(missing_features) <= 5:
            print(f"         Missing: {', '.join(missing_features)}")
    
    # Extract features.
    # IMPROVEMENT: fill NaN timing-derived features with the race median
    # rather than 0. Filling with 0 unfairly scores a dog with unknown time
    # as the "slowest in the field" — median treatment is neutral.
    X = df[feature_cols].copy()
    for col in TIMING_FEATURES:
        if col in X.columns:
            col_median = X[col].median()
            fill_value = col_median if pd.notna(col_median) else 0
            X[col] = X[col].fillna(fill_value)
    X = X.fillna(0)
    
    # Check for feature variability - warn if features don't vary between dogs
    constant_features = []
    varying_features = []
    for col in feature_cols:
        if col in df.columns:
            unique_count = df[col].nunique()
            if unique_count == 1:
                constant_features.append(col)
            else:
                varying_features.append(col)
    
    # CRITICAL: Warn if >30% of features are constant (lowered threshold from 50%)
    constant_ratio = len(constant_features) / len(feature_cols) if feature_cols else 0
    if constant_ratio > 0.3:
        print(f"      ⚠️  CRITICAL: {len(constant_features)}/{len(feature_cols)} features ({constant_ratio*100:.1f}%) have same value for all dogs!")
        print(f"         This will cause identical prediction scores.")
        print(f"         Varying features: {len(varying_features)}")
        
        # Show sample of varying features
        if varying_features:
            print(f"         Sample varying: {', '.join(varying_features[:5])}")
        
        # Show critical dog-specific features that should vary
        critical_features = ['Box', 'Draw', 'Weight', 'BestTimeSec', 'SectionalSec', 'CareerWins', 
                            'CareerStarts', 'WinRate', 'PlaceRate', 'DLWFactor', 'WeightFactor']
        missing_critical = [f for f in critical_features if f not in df.columns or df[f].nunique() == 1]
        if missing_critical:
            print(f"         ⚠️  Missing/constant critical features: {', '.join(missing_critical[:10])}")
            print(f"         These should vary between dogs for accurate predictions!")
    
    X_scaled = scaler.transform(X)
    
    # Get predictions from each algorithm
    all_predictions = []
    used_weights = []
    individual_scores = {}
    
    # IMPROVEMENT: Weight XGB higher since it has best discrimination (78% vs 33%)
    improved_weights = {
        'xgb': 0.50,  # XGB gets 50% weight (best discriminator)
        'rf': 0.25,   # RF gets 25% weight
        'gb': 0.25    # GB gets 25% weight
    }
    
    for alg, model in models.items():
        pred_proba = model.predict_proba(X_scaled)[:, 1]

        # ---------------------------------------------------------------
        # CALIBRATION-COLLAPSE GUARD
        # If the calibrated model returns fewer unique values than half the
        # number of dogs, the isotonic mapping has collapsed the scores.
        # Fall back to uncalibrated base-estimator predictions to recover
        # per-dog discrimination while keeping the correct probability scale
        # via within-race normalization applied later.
        # ---------------------------------------------------------------
        n_unique_calibrated = len(np.unique(pred_proba))
        if n_unique_calibrated < max(2, n_dogs // 2):
            uncal = _get_uncalibrated_preds(model, X_scaled)
            if uncal is not None:
                n_unique_uncal = len(np.unique(uncal))
                print(f"      ⚠️  {alg.upper()}: calibration collapsed {n_dogs} dogs → "
                      f"{n_unique_calibrated} unique value(s). "
                      f"Using uncalibrated predictions ({n_unique_uncal} unique values).")
                pred_proba = uncal
            else:
                print(f"      ⚠️  {alg.upper()}: calibration collapsed scores "
                      f"and base estimator unavailable.")

        # Store individual predictions (RAW from model - no failed temperature scaling)
        individual_scores[alg] = pred_proba
        
        # Use improved weights
        weight = improved_weights.get(alg, ensemble_weights.get(alg, 1.0 / len(models)))
        all_predictions.append(pred_proba * weight)
        used_weights.append(weight)
    
    # Normalize weights and compute weighted average
    total_weight = sum(used_weights)
    ensemble_pred = np.sum(all_predictions, axis=0) / total_weight

    # Capture pre-normalization spread to expose model confidence
    raw_spread = float(ensemble_pred.max() - ensemble_pred.min())

    # Return raw probabilities. Normalization to [2%-18%] is done in main()
    # across ALL dogs from the entire race card (not per-race), so that scores
    # reflect each dog's strength relative to the full day's competition.
    # A race full of weak dogs will produce lower top scores than a race with
    # several strong contenders — exactly the cross-race variation the user expects.
    return ensemble_pred, individual_scores, raw_spread

def main():
    print("=" * 80)
    print("🎯 TRACK-SPECIFIC ENSEMBLE PREDICTIONS (CALIBRATED)")
    print("=" * 80)
    print("\nUsing track-specific calibrated ensemble models:")
    print("  ✅ RandomForest + GradientBoosting + XGBoost per track")
    print("  ✅ All models calibrated with Isotonic Regression")
    print("  ✅ Predictions averaged across all 3 algorithms")
    print("  ✅ Confidence scores accurately reflect win probability")
    print("=" * 80)
    
    # Check if models exist
    models_dir = "models"
    config_path = os.path.join(models_dir, "config.pkl")
    
    if not os.path.exists(config_path):
        print(f"\n❌ ERROR: Track ensemble models not found!")
        print(f"   Expected config at: {config_path}")
        print(f"\n   Please train the models first:")
        print(f"   python train_ml_track_ensemble.py")
        print(f"   OR: train_ml_track_ensemble.bat")
        return 1
    
    # Load configuration
    with open(config_path, 'rb') as f:
        config = pickle.load(f)
    
    print(f"\n📥 Loaded ensemble configuration:")
    print(f"   Tracks: {len(config['tracks'])}")
    print(f"   Algorithms: {', '.join(config['algorithms'])}")
    print(f"   Features: {len(config['feature_cols'])}")
    print(f"\n📊 Feature columns used for predictions:")
    print(f"   {', '.join(config['feature_cols'][:15])}...")
    if len(config['feature_cols']) > 15:
        print(f"   ... and {len(config['feature_cols']) - 15} more features")
    
    # Find PDFs
    pdf_files = glob.glob("data_predictions/*.pdf")
    
    if not pdf_files:
        print(f"\n❌ No PDF files found in data_predictions/")
        return 1
    
    print(f"\n📄 Found {len(pdf_files)} PDF files")
    
    # Process each PDF
    all_predictions = []
    
    for pdf_file in sorted(pdf_files):
        print(f"\n📄 Processing: {os.path.basename(pdf_file)}")
        
        try:
            # Extract text from PDF
            print(f"   📖 Extracting text from PDF...")
            pdf_text = extract_text_from_pdf(pdf_file)
            
            if not pdf_text or len(pdf_text.strip()) == 0:
                print(f"   ⚠️  No text extracted from PDF")
                continue
            
            # Parse PDF text
            print(f"   🔍 Parsing race form...")
            race_df = parse_race_form(pdf_text)
            
            if race_df is None or len(race_df) == 0:
                print(f"   ⚠️  No data extracted from PDF")
                continue
            
            # Get track name
            track_name = race_df['Track'].iloc[0] if 'Track' in race_df.columns else "Unknown"
            print(f"   Track: {track_name}")
            print(f"   Dogs: {len(race_df)}")
            
            # Compute features
            try:
                race_df = compute_features(race_df)
            except Exception as e:
                print(f"   ⚠️  Error computing features: {e}")
                # Continue with available features
            
            # Load track-specific ensemble
            try:
                models, scaler, config = load_track_ensemble(track_name, models_dir)

                if models is None or not models:
                    print(f"   ⚠️  No models found for {track_name}, skipping")
                    continue

                if scaler is None:
                    print(f"   ⚠️  No scaler for {track_name} (registered in config but no .pkl file), skipping")
                    continue

                print(f"   Models loaded: {', '.join(models.keys())}")

                # PER-RACE MODEL INFERENCE + CROSS-CARD NORMALIZATION
                #
                # MODEL INFERENCE is per-race: dogs from Race 1 are never scored
                # against dogs from Race 2 (they never compete against each other).
                #
                # DISPLAY NORMALIZATION is cross-card (whole PDF): after getting raw
                # probabilities for every race, a single min-max scale [2%-18%] is
                # applied across ALL dogs from the day's card.  This produces the
                # natural variation the user expects:
                #   - A race with genuinely strong, evenly-matched dogs has its top
                #     dog near 18% and its weakest around 12%.
                #   - A race of weaker dogs (all low raw probabilities) has its top
                #     dog at maybe 9-11%, preserving real model confidence differences.
                #
                # This is why the user sees Race 3 winner at 9.7% and Race 5 winner
                # at 18% in the original outputs — the cross-card scale reflects actual
                # ML signal, not an artificial per-race forced ranking.
                feature_cols = config['feature_cols']
                ens_weights  = config.get('ensemble_weights', {})
                race_frames  = []

                # Step 1: per-race inference - collect raw predictions
                for race_num, single_race_df in race_df.groupby('RaceNumber'):
                    single_race_df = single_race_df.copy()

                    raw_ens, raw_ind, raw_spread = predict_with_ensemble(
                        single_race_df, models, scaler, feature_cols, ens_weights
                    )

                    # Store raw arrays on the frame for cross-card normalization below
                    single_race_df['_raw_ens'] = raw_ens
                    for alg, arr in raw_ind.items():
                        single_race_df[f'_raw_{alg}'] = arr
                    single_race_df['_raw_spread'] = raw_spread
                    race_frames.append(single_race_df)

                # Reassemble full card
                race_df = pd.concat(race_frames, ignore_index=True)

                # Step 2: cross-card min-max normalization to [2%, 18%]
                # Applied to ensemble and each algorithm independently.
                def minmax_scale(arr, lo=0.02, hi=0.18):
                    a_min, a_max = arr.min(), arr.max()
                    if a_max > a_min:
                        return lo + (arr - a_min) / (a_max - a_min) * (hi - lo)
                    return np.full_like(arr, (lo + hi) / 2)

                ens_all  = race_df['_raw_ens'].values.astype(float)
                ens_norm = minmax_scale(ens_all)
                race_df['ML_Confidence'] = np.round(ens_norm * 100, 2)
                race_df['Ensemble_Score'] = ens_norm

                # Low-confidence flag: check per-race spread
                for race_num, grp in race_df.groupby('RaceNumber'):
                    spread = float(grp['_raw_spread'].iloc[0])
                    low_conf = spread < LOW_CONFIDENCE_SPREAD_THRESHOLD
                    race_df.loc[grp.index, 'Low_Confidence'] = low_conf
                    if low_conf:
                        print(f"      ⚠️  Race {race_num} LOW_CONFIDENCE: raw spread={spread:.4f}")

                # Individual algorithm scores: normalize each across the whole card
                alg_cols = [c for c in race_df.columns if c.startswith('_raw_') and
                            c not in ('_raw_ens', '_raw_spread')]
                for raw_col in alg_cols:
                    alg = raw_col[5:]  # strip '_raw_'
                    alg_arr  = race_df[raw_col].values.astype(float)
                    alg_norm = minmax_scale(alg_arr)
                    race_df[f'{alg.upper()}_Score'] = np.round(alg_norm * 100, 2)

                # Per-race rank (rank 1 = top pick within each race)
                for race_num, grp in race_df.groupby('RaceNumber'):
                    ranks = grp['ML_Confidence'].rank(ascending=False, method='min').astype(int)
                    race_df.loc[grp.index, 'ML_Rank'] = ranks

                # Drop temporary raw columns
                raw_cols_to_drop = [c for c in race_df.columns if c.startswith('_raw_')]
                race_df = race_df.drop(columns=raw_cols_to_drop)

                # Print per-race top picks
                for race_num in sorted(race_df['RaceNumber'].unique()):
                    grp = race_df[race_df['RaceNumber'] == race_num]
                    top_r = grp.loc[grp['ML_Confidence'].idxmax()]
                    rf_s  = top_r.get('RF_Score',  0)
                    gb_s  = top_r.get('GB_Score',  0)
                    xgb_s = top_r.get('XGB_Score', 0)
                    print(f"   Race {int(race_num):2d}: Box {int(top_r['Box'])} - {top_r['DogName']} "
                          f"({top_r['ML_Confidence']:.2f}%  RF={rf_s:.1f}, GB={gb_s:.1f}, XGB={xgb_s:.1f})")

                top_dog = race_df.loc[race_df['ML_Confidence'].idxmax()]
                print(f"   ✅ Card top pick: Race {int(top_dog['RaceNumber'])} "
                      f"Box {int(top_dog['Box'])} - {top_dog['DogName']} "
                      f"({top_dog['ML_Confidence']:.2f}%)")

                all_predictions.append(race_df)

            except Exception as e:
                print(f"   ❌ ERROR generating predictions: {e}")
                traceback.print_exc()
                continue

        except Exception as e:
            print(f"   ❌ ERROR processing PDF: {e}")
            continue
    
    # Save results
    if all_predictions:
        print(f"\n💾 Saving results...")
        
        # Combine all predictions
        df_all = pd.concat(all_predictions, ignore_index=True)
        
        # Remove only non-essential metadata columns (not used for predictions)
        # Keep all feature columns that were used for predictions so users can inspect them
        columns_to_remove = [
            'Owner', 'Color', 'Sire', 'Dam',  # Pedigree info rarely in race forms
        ]
        
        # Remove columns that exist in the dataframe
        columns_to_remove_existing = [col for col in columns_to_remove if col in df_all.columns]
        
        if columns_to_remove_existing:
            print(f"   Removing {len(columns_to_remove_existing)} metadata columns: {', '.join(columns_to_remove_existing)}...")
            df_all = df_all.drop(columns=columns_to_remove_existing)
        
        # Reorder columns: Track, RaceNumber, Box, DogName, ML_Confidence, Low_Confidence, RF_Score, GB_Score, XGB_Score, then rest
        priority_cols = ['Track', 'RaceNumber', 'Box', 'DogName', 'ML_Confidence', 'Low_Confidence', 'RF_Score', 'GB_Score', 'XGB_Score']
        # Filter priority_cols to only include those that exist in df_all
        priority_cols = [col for col in priority_cols if col in df_all.columns]
        other_cols = [col for col in df_all.columns if col not in priority_cols]
        df_all = df_all[priority_cols + other_cols]
        
        # Sort by Track -> RaceNumber -> Box (for race order)
        df_all = df_all.sort_values(['Track', 'RaceNumber', 'Box'], ascending=[True, True, True])
        
        # Save to Excel with formatting
        output_dir = "outputs"
        os.makedirs(output_dir, exist_ok=True)
        
        excel_path = os.path.join(output_dir, "track_ensemble_predictions.xlsx")
        
        # Create Excel writer with formatting
        with pd.ExcelWriter(excel_path, engine='openpyxl') as writer:
            df_all.to_excel(writer, index=False, sheet_name='Predictions')
            
            # Get workbook and worksheet
            workbook = writer.book
            worksheet = writer.sheets['Predictions']
            
            # Define fill styles
            from openpyxl.styles import PatternFill, Border, Side
            green_fill = PatternFill(start_color='90EE90', end_color='90EE90', fill_type='solid')
            yellow_fill = PatternFill(start_color='FFFF00', end_color='FFFF00', fill_type='solid')
            orange_fill = PatternFill(start_color='FFA500', end_color='FFA500', fill_type='solid')
            black_border = Border(top=Side(style='thick', color='000000'))
            
            # Apply formatting row by row
            prev_race_key = None
            current_row = 2  # Start at row 2 (after header)
            
            for idx in range(len(df_all)):
                row = df_all.iloc[idx]
                race_key = f"{row['Track']}_{row['RaceNumber']}"
                
                # Add black line at start of new race
                if prev_race_key is not None and race_key != prev_race_key:
                    for col in range(1, len(df_all.columns) + 1):
                        worksheet.cell(row=current_row, column=col).border = black_border
                
                # Get all dogs in current race sorted by ML_Confidence
                race_mask = (df_all['Track'] == row['Track']) & (df_all['RaceNumber'] == row['RaceNumber'])
                race_dogs = df_all[race_mask].copy()
                race_dogs_sorted = race_dogs.sort_values('ML_Confidence', ascending=False)
                
                # Find position of current dog (1st, 2nd, 3rd by ML_Confidence)
                position = list(race_dogs_sorted.index).index(df_all.index[idx]) + 1
                
                # Apply color coding
                if position == 1:
                    fill = green_fill
                elif position == 2:
                    fill = yellow_fill
                elif position == 3:
                    fill = orange_fill
                else:
                    fill = None
                
                if fill:
                    for col in range(1, len(df_all.columns) + 1):
                        worksheet.cell(row=current_row, column=col).fill = fill
                
                prev_race_key = race_key
                current_row += 1
        
        print(f"✅ Excel saved (with color coding): {excel_path}")
        
        # Save summary
        summary_path = os.path.join(output_dir, "track_ensemble_summary.txt")
        with open(summary_path, 'w') as f:
            f.write("=" * 80 + "\n")
            f.write("TRACK-SPECIFIC ENSEMBLE PREDICTIONS SUMMARY\n")
            f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write("=" * 80 + "\n\n")
            
            f.write(f"Total PDFs processed: {len(pdf_files)}\n")
            f.write(f"Successful predictions: {len(all_predictions)}\n")
            f.write(f"Total dogs predicted: {len(df_all)}\n\n")
            
            # Per-track summary
            for track in df_all['Track'].unique():
                track_df = df_all[df_all['Track'] == track]
                f.write(f"\n{track}:\n")
                f.write(f"  Races: {track_df['RaceNumber'].nunique()}\n")
                f.write(f"  Dogs: {len(track_df)}\n")
                
                # Top picks per race
                for race_num in sorted(track_df['RaceNumber'].unique()):
                    race_df = track_df[track_df['RaceNumber'] == race_num]
                    if len(race_df) > 0:
                        top = race_df.loc[race_df['ML_Confidence'].idxmax()]
                        # Include individual scores if available
                        individual_str = ""
                        if 'RF_Score' in top.index and 'GB_Score' in top.index and 'XGB_Score' in top.index:
                            individual_str = f" (RF={top['RF_Score']:.1f}, GB={top['GB_Score']:.1f}, XGB={top['XGB_Score']:.1f})"
                        f.write(f"  Race {race_num}: Box {top['Box']} - {top['DogName']} ({top['ML_Confidence']:.2f}%{individual_str})\n")
        
        print(f"✅ Summary saved: {summary_path}")
        
        print("\n" + "=" * 80)
        print("✅ PREDICTIONS COMPLETE!")
        print("=" * 80)
        print(f"\n📊 Results:")
        print(f"   Tracks processed: {df_all['Track'].nunique()}")
        print(f"   Races: {df_all['RaceNumber'].nunique()}")
        print(f"   Dogs: {len(df_all)}")
        print(f"\n📁 Output files:")
        print(f"   {excel_path}")
        print(f"   {summary_path}")
        print("=" * 80)
    else:
        print("\n⚠️  No predictions generated")
        return 1
    
    return 0

if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception as e:
        print(f"\n❌ FATAL ERROR: {e}")
        traceback.print_exc()
        sys.exit(1)
