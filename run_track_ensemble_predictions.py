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

def load_track_ensemble(track_name, models_dir="models/track_ensemble"):
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
    
    # Load models
    models = {}
    for alg in config['algorithms']:
        model_path = os.path.join(models_dir, f"{track_name}_{alg}.pkl")
        if os.path.exists(model_path):
            with open(model_path, 'rb') as f:
                models[alg] = pickle.load(f)
    
    # Load scaler
    scaler_path = os.path.join(models_dir, f"{track_name}_scaler.pkl")
    if os.path.exists(scaler_path):
        with open(scaler_path, 'rb') as f:
            scaler = pickle.load(f)
    else:
        scaler = None
    
    return models, scaler, config

def predict_with_ensemble(df, models, scaler, feature_cols, ensemble_weights):
    """
    Generate ensemble predictions for a race.
    
    Args:
        df: DataFrame with race data (all dogs in race)
        models: Dict of {algorithm: model}
        scaler: StandardScaler
        feature_cols: List of feature column names
        ensemble_weights: Dict of {algorithm: weight}
    
    Returns:
        predictions: Array of ensemble probabilities for each dog
    """
    # Prepare features
    # Check for missing features and warn user
    missing_features = [col for col in feature_cols if col not in df.columns]
    if missing_features:
        print(f"      ⚠️  Warning: {len(missing_features)} features missing from race data (will be filled with 0)")
        if len(missing_features) <= 5:
            print(f"         Missing: {', '.join(missing_features)}")
    
    # Extract features and fill missing with 0
    X = df[feature_cols].fillna(0)
    
    # Check for feature variability - warn if features don't vary between dogs
    constant_features = []
    for col in feature_cols:
        if col in df.columns and df[col].nunique() == 1:
            constant_features.append(col)
    
    if constant_features and len(constant_features) > len(feature_cols) * 0.5:
        print(f"      ⚠️  Warning: {len(constant_features)}/{len(feature_cols)} features have same value for all dogs")
        print(f"         This may cause similar prediction scores. Check feature computation.")
    
    X_scaled = scaler.transform(X)
    
    # Get predictions from each algorithm
    all_predictions = []
    used_weights = []
    
    for alg, model in models.items():
        pred_proba = model.predict_proba(X_scaled)[:, 1]
        weight = ensemble_weights.get(alg, 1.0 / len(models))
        all_predictions.append(pred_proba * weight)
        used_weights.append(weight)
    
    # Normalize weights and compute weighted average
    total_weight = sum(used_weights)
    ensemble_pred = np.sum(all_predictions, axis=0) / total_weight
    
    return ensemble_pred

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
    models_dir = "models/track_ensemble"
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
                
                if models is None:
                    print(f"   ⚠️  No models found for {track_name}, skipping")
                    continue
                
                print(f"   Models loaded: {', '.join(models.keys())}")
                
                # Generate predictions
                ensemble_pred = predict_with_ensemble(
                    race_df, models, scaler, config['feature_cols'], config['ensemble_weights']
                )
                
                # Add to race_df
                race_df['ML_Confidence'] = (ensemble_pred * 100).round(1)
                race_df['Ensemble_Score'] = ensemble_pred
                
                # Add ranking
                race_df['ML_Rank'] = race_df['ML_Confidence'].rank(ascending=False, method='dense').astype(int)
                
                # Get top pick
                top_dog = race_df.loc[race_df['ML_Confidence'].idxmax()]
                print(f"   ✅ Top pick: Box {top_dog['Box']} - {top_dog['DogName']} ({top_dog['ML_Confidence']:.1f}%)")
                
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
        
        # Reorder columns: Track, RaceNumber, Box, DogName, ML_Confidence, then rest
        priority_cols = ['Track', 'RaceNumber', 'Box', 'DogName', 'ML_Confidence']
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
                        f.write(f"  Race {race_num}: Box {top['Box']} - {top['DogName']} ({top['ML_Confidence']:.1f}%)\n")
        
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
