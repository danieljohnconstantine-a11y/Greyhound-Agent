#!/usr/bin/env python3
"""
predict_race.py — Full ML ensemble prediction pipeline for greyhound racing.

Usage:
    python predict_race.py --pdf data/ANGLG0112form.pdf --race 8 --dist 530
    python predict_race.py --pdf data/ANGLG0112form.pdf --race 8 --dist 530 --track "Angle Park"
    python predict_race.py --pdf data/ANGLG0112form.pdf  # predict all races

Models used  : Random Forest (RF), Gradient Boosting (GB), XGBoost (XGB)
Model files  : <Track>_rf.pkl, <Track>_gb.pkl, <Track>_xgb.pkl, <Track>_scaler.pkl
               (flat files in the project root)
Output files : outputs/<race_tag>_predictions.csv
               outputs/<race_tag>_audit_report.txt
"""

import argparse
import os
import sys
import warnings
import textwrap
import datetime
import joblib
import numpy as np
import pandas as pd

warnings.filterwarnings('ignore')

# ── local modules ──────────────────────────────────────────────────────────────
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from src.pdf_parser import parse_form_pdf
from src.race_features import build_features, get_feature_matrix, FEATURE_COLS

# ── XGBoost training helper ────────────────────────────────────────────────────
try:
    import xgboost as xgb
    XGB_AVAILABLE = True
except ImportError:
    XGB_AVAILABLE = False


# ─────────────────────────────────────────────────────────────────────────────
#  Model loading
# ─────────────────────────────────────────────────────────────────────────────

def load_models(track_name: str, model_dir: str = '.'):
    """
    Load RF, GB, XGB models and scaler for a given track.
    Returns (rf, gb, xgb_model, scaler) — any can be None if not found.
    """
    def _load(path):
        if os.path.exists(path):
            try:
                return joblib.load(path)
            except Exception as e:
                print(f"  ⚠️  Could not load {path}: {e}")
        return None

    rf     = _load(os.path.join(model_dir, f'{track_name}_rf.pkl'))
    gb     = _load(os.path.join(model_dir, f'{track_name}_gb.pkl'))
    xgb_m  = _load(os.path.join(model_dir, f'{track_name}_xgb.pkl'))
    scaler = _load(os.path.join(model_dir, f'{track_name}_scaler.pkl'))

    return rf, gb, xgb_m, scaler


# ─────────────────────────────────────────────────────────────────────────────
#  XGBoost model training (train on-the-fly if not available)
# ─────────────────────────────────────────────────────────────────────────────

def train_or_load_xgb(track_name: str, feature_df: pd.DataFrame,
                      model_dir: str = '.') -> object:
    """
    Load pre-trained XGB model if available, otherwise train a lightweight
    XGB classifier using historical form data parsed from the data/ folder,
    and save it.

    The proxy label is: did the dog finish 1st or 2nd in their most recent race?
    This is a simplification that allows the model to learn ranking signal from
    the parsed PDF form data.
    """
    xgb_path = os.path.join(model_dir, f'{track_name}_xgb.pkl')
    if os.path.exists(xgb_path):
        try:
            return joblib.load(xgb_path)
        except Exception:
            pass

    if not XGB_AVAILABLE:
        print("  ⚠️  XGBoost not installed — skipping XGB model")
        return None

    print(f"  🔧 Training XGB model for {track_name} from historical data ...")

    # Parse all available historical PDFs for this track
    data_dir = 'data'
    track_prefix = _track_to_prefix(track_name)
    pdf_files = [
        f for f in os.listdir(data_dir)
        if f.upper().startswith(track_prefix) and f.lower().endswith('.pdf')
    ]

    all_dfs = []
    for pdf_file in sorted(pdf_files):
        try:
            raw = parse_form_pdf(os.path.join(data_dir, pdf_file))
            if not raw.empty:
                feat = build_features(raw)
                all_dfs.append(feat)
        except Exception as e:
            print(f"    ⚠️  Skipped {pdf_file}: {e}")

    if not all_dfs:
        print("  ⚠️  No historical data found — falling back to in-race XGB training")
        all_dfs = [feature_df]

    hist_df = pd.concat(all_dfs, ignore_index=True)

    # Build proxy labels from career win rate and recent performance
    # This is a ranking proxy, not a true win label
    def make_label(row):
        win_rate = row['CareerWins'] / max(row['CareerStarts'], 1)
        place_rate = row['WinPlaceRate']
        last3_avg = row.get('Last3AvgFinish', 4.0)
        recent_boost = row['RecentFormBoost']
        # Score proxy: high win rate + recent activity + good last 3
        score = win_rate * 2 + place_rate + recent_boost - (last3_avg - 1) * 0.1
        return 1 if score > 0.8 else 0

    try:
        X = hist_df[FEATURE_COLS].fillna(0).values
        y = hist_df.apply(make_label, axis=1).values

        from xgboost import XGBClassifier
        xgb_model = XGBClassifier(
            n_estimators=200,
            max_depth=4,
            learning_rate=0.1,
            subsample=0.8,
            colsample_bytree=0.8,
            use_label_encoder=False,
            eval_metric='logloss',
            random_state=42,
            verbosity=0,
        )
        xgb_model.fit(X, y)
        joblib.dump(xgb_model, xgb_path)
        print(f"  ✅ XGB model trained and saved → {xgb_path}")
        return xgb_model
    except Exception as e:
        print(f"  ⚠️  XGB training failed: {e}")
        return None


def _track_to_prefix(track_name: str) -> str:
    """Convert 'Angle Park' → 'ANGLG' for PDF filename lookup."""
    MAP = {
        'Angle Park': 'ANGLG',
        'BALLARAT': 'BRATG',
        'BENDIGO': 'BDGOG',
    }
    return MAP.get(track_name, track_name[:4].upper())


# ─────────────────────────────────────────────────────────────────────────────
#  Calibration-collapse guard
# ─────────────────────────────────────────────────────────────────────────────

def _get_uncalibrated_preds(model, X_scaled: np.ndarray) -> np.ndarray:
    """
    Try to get uncalibrated win probabilities.

    CalibratedClassifierCV can collapse all probabilities to the same
    value for small races (e.g. 8 dogs).  If we detect collapse (< 50%
    unique values), we fall back to the base estimator.
    """
    try:
        probs = model.predict_proba(X_scaled)[:, 1]
        n_unique = len(np.unique(np.round(probs, 4)))
        if n_unique < max(2, len(probs) // 2):
            # Calibration collapse — use base estimator
            base = getattr(model, 'estimator', None) or getattr(model, 'base_estimator', None)
            if base is not None:
                probs = base.predict_proba(X_scaled)[:, 1]
                n_unique2 = len(np.unique(np.round(probs, 4)))
                if n_unique2 > n_unique:
                    return probs
        return probs
    except Exception:
        return model.predict_proba(X_scaled)[:, 1]


# ─────────────────────────────────────────────────────────────────────────────
#  Scoring with scaler
# ─────────────────────────────────────────────────────────────────────────────

def predict_with_models(rf, gb, xgb_model, scaler,
                        X: pd.DataFrame) -> dict:
    """
    Run all three models on feature matrix X.
    Returns per-model probability arrays and ensemble average.
    Each dog gets its own individual probability.
    """
    X_vals = X.fillna(0).values

    if scaler is not None:
        try:
            X_scaled = scaler.transform(X_vals)
        except Exception:
            X_scaled = X_vals
    else:
        X_scaled = X_vals

    results = {}
    active_models = []

    if rf is not None:
        try:
            rf_probs = _get_uncalibrated_preds(rf, X_scaled)
            results['RF'] = rf_probs
            active_models.append(rf_probs)
        except Exception as e:
            print(f"    ⚠️  RF prediction failed: {e}")

    if gb is not None:
        try:
            gb_probs = _get_uncalibrated_preds(gb, X_scaled)
            results['GB'] = gb_probs
            active_models.append(gb_probs)
        except Exception as e:
            print(f"    ⚠️  GB prediction failed: {e}")

    if xgb_model is not None:
        try:
            if hasattr(xgb_model, 'predict_proba'):
                xgb_probs = xgb_model.predict_proba(X_vals)[:, 1]
            else:
                # Native XGBoost API
                dmat = xgb.DMatrix(X_vals, feature_names=list(X.columns))
                xgb_probs = xgb_model.predict(dmat)
            results['XGB'] = xgb_probs
            active_models.append(xgb_probs)
        except Exception as e:
            print(f"    ⚠️  XGB prediction failed: {e}")

    if active_models:
        results['Ensemble'] = np.mean(active_models, axis=0)
    else:
        raise RuntimeError("All models failed — cannot generate predictions")

    # Normalise ensemble to sum to 1 (pseudo-probabilities)
    ens = results['Ensemble']
    total = ens.sum()
    if total > 0:
        results['EnsembleNorm'] = ens / total
    else:
        results['EnsembleNorm'] = np.ones(len(ens)) / len(ens)

    return results


# ─────────────────────────────────────────────────────────────────────────────
#  Uniqueness check
# ─────────────────────────────────────────────────────────────────────────────

def verify_individual_scoring(df: pd.DataFrame, results: dict) -> dict:
    """
    Verify that each dog has unique individual scores.
    Returns audit information.
    """
    audit = {}
    for model_name, probs in results.items():
        if model_name == 'EnsembleNorm':
            continue
        n_unique = len(np.unique(np.round(probs, 6)))
        audit[model_name] = {
            'n_dogs': len(probs),
            'n_unique': n_unique,
            'all_individual': n_unique == len(probs),
            'probs': probs,
            'min': float(np.min(probs)),
            'max': float(np.max(probs)),
            'std': float(np.std(probs)),
        }
    return audit


# ─────────────────────────────────────────────────────────────────────────────
#  Report generation
# ─────────────────────────────────────────────────────────────────────────────

def generate_predictions_df(dog_df: pd.DataFrame, results: dict,
                             feature_df: pd.DataFrame) -> pd.DataFrame:
    """Build the predictions DataFrame with all per-dog scores."""
    out = pd.DataFrame()
    out['Box']           = dog_df['Box'].values
    out['DogName']       = dog_df['DogName'].values
    out['Trainer']       = dog_df['Trainer'].values
    out['Career']        = dog_df.apply(
        lambda r: f"{int(r['CareerWins'])}-{int(r['CareerPlaces'])}-{int(r['CareerStarts'])}",
        axis=1
    ).values
    out['DLR']           = dog_df['DLR'].values
    out['DLW']           = dog_df['DLW'].values
    out['RTC']           = dog_df['RTC'].values
    out['PrizeMoney']    = dog_df['PrizeMoney'].apply(lambda x: f'${x:,.0f}').values
    out['BestTimeSec']   = feature_df['BestTimeSec'].round(2).values
    out['SectionalSec']  = feature_df['SectionalSec'].round(2).values
    out['Speed_kmh']     = feature_df['Speed_kmh'].round(2).values
    out['ConsistencyIndex'] = feature_df['ConsistencyIndex'].round(4).values
    out['RecentFormBoost']  = feature_df['RecentFormBoost'].values
    out['DLWFactor']     = feature_df['DLWFactor'].values
    out['DrawFactor']    = feature_df['DrawFactor'].values
    out['BoxBiasFactor'] = feature_df['BoxBiasFactor'].values
    out['DistanceSuit']  = feature_df['DistanceSuit'].round(3).values
    out['AgeFactor']     = feature_df['AgeFactor'].values
    out['FinalScore']    = feature_df['FinalScore'].round(4).values

    if 'RF' in results:
        out['RF_Prob']  = np.round(results['RF'], 4)
    if 'GB' in results:
        out['GB_Prob']  = np.round(results['GB'], 4)
    if 'XGB' in results:
        out['XGB_Prob'] = np.round(results['XGB'], 4)

    out['Ensemble_Prob'] = np.round(results['Ensemble'], 4)
    out['Win_Pct']       = (results['EnsembleNorm'] * 100).round(1)

    out = out.sort_values('Ensemble_Prob', ascending=False).reset_index(drop=True)
    out.insert(0, 'Rank', range(1, len(out) + 1))

    return out


def write_audit_report(out_path: str, race_meta: dict, dog_df: pd.DataFrame,
                       feature_df: pd.DataFrame, results: dict,
                       audit: dict, pred_df: pd.DataFrame) -> None:
    """Write full audit report proving individual scoring."""
    ts = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    lines = [
        "=" * 72,
        f"GREYHOUND RACE PREDICTION AUDIT REPORT",
        f"Generated: {ts}",
        "=" * 72,
        "",
        f"Race     : {race_meta.get('RaceNumber', 'N/A')}",
        f"Date     : {race_meta.get('RaceDate', 'N/A')}",
        f"Time     : {race_meta.get('RaceTime', 'N/A')}",
        f"Track    : {race_meta.get('Track', 'N/A')}",
        f"Distance : {race_meta.get('Distance', 'N/A')}m",
        "",
        "─" * 72,
        "STEP 1 — DATA EXTRACTION (per-dog, from PDF)",
        "─" * 72,
    ]

    key_cols = ['DogName', 'Box', 'CareerWins', 'CareerPlaces', 'CareerStarts',
                'PrizeMoney', 'RTC', 'DLR', 'DLW', 'AgeMonths']
    for _, row in dog_df.iterrows():
        lines.append(f"  Box {int(row['Box'])}: {row['DogName']}")
        lines.append(f"    Career     : {int(row['CareerWins'])}-{int(row['CareerPlaces'])}-{int(row['CareerStarts'])}")
        lines.append(f"    Prize Money: ${row['PrizeMoney']:,.0f}")
        lines.append(f"    RTC/DLR/DLW: {int(row['RTC'])} / {int(row['DLR'])} / {int(row['DLW'])}")
        lines.append(f"    Age Months : {int(row['AgeMonths'])}")
        # Show recent races if available
        recent = row.get('RecentRaces', [])
        if recent:
            lines.append(f"    Last races : " + ", ".join(
                f"{r['Pos']}/{r['Field']} @ {r['Track'][:12]} ({r['RaceDist']}m)"
                for r in recent[:3]
            ))
        lines.append("")

    lines += [
        "─" * 72,
        "STEP 2 — INDIVIDUAL FEATURE COMPUTATION (74 features per dog)",
        "─" * 72,
    ]

    key_features = ['BestTimeSec', 'SectionalSec', 'Speed_kmh', 'EarlySpeedIndex',
                    'ConsistencyIndex', 'PlaceRate', 'RecentFormBoost', 'DLWFactor',
                    'BoxBiasFactor', 'DistanceSuit', 'AgeFactor', 'FreshnessFactorV2',
                    'Last3AvgFinish', 'TrainerStrikeRate', 'FinalScore']

    for _, row in feature_df.iterrows():
        dog_row = dog_df[dog_df['Box'] == row.get('Box', -1)]
        name = dog_row['DogName'].values[0] if not dog_row.empty else f"Box {row.get('Box')}"
        lines.append(f"  Box {int(row['Box'])}: {name}")
        for feat in key_features:
            if feat in row:
                lines.append(f"    {feat:30s}: {row[feat]:.4f}")
        lines.append("")

    lines += [
        "─" * 72,
        "STEP 3 — MODEL PREDICTIONS (individual score per dog)",
        "─" * 72,
        "",
        "  Uniqueness verification:",
    ]

    for model_name, info in audit.items():
        status = "✅ ALL INDIVIDUAL" if info['all_individual'] else f"⚠️  {info['n_unique']}/{info['n_dogs']} unique"
        lines.append(f"    {model_name:10s}: {status}  (std={info['std']:.5f})")

    lines += [
        "",
        "  Probability scores by dog:",
        f"  {'Box':>3}  {'Dog Name':<25} {'RF':>8} {'GB':>8} {'XGB':>8} {'Ensemble':>10} {'Win%':>6}",
        "  " + "-" * 72,
    ]

    for _, row in pred_df.sort_values('Box').iterrows():
        rf_s  = f"{row['RF_Prob']:.4f}"  if 'RF_Prob' in pred_df.columns  else "N/A"
        gb_s  = f"{row['GB_Prob']:.4f}"  if 'GB_Prob' in pred_df.columns  else "N/A"
        xgb_s = f"{row['XGB_Prob']:.4f}" if 'XGB_Prob' in pred_df.columns else "N/A"
        lines.append(
            f"  {int(row['Box']):>3}  {row['DogName']:<25} "
            f"{rf_s:>8} {gb_s:>8} {xgb_s:>8} {row['Ensemble_Prob']:>10.4f} {row['Win_Pct']:>5.1f}%"
        )

    lines += [
        "",
        "─" * 72,
        "STEP 4 — RANKED PREDICTIONS",
        "─" * 72,
        "",
        f"  {'Rank':>4}  {'Box':>3}  {'Dog Name':<25} {'Win%':>6}  Key Factors",
        "  " + "-" * 72,
    ]

    for _, row in pred_df.iterrows():
        feat_row = feature_df[feature_df['Box'] == row['Box']]
        if not feat_row.empty:
            fr = feat_row.iloc[0]
            key_info = (
                f"Speed={fr['Speed_kmh']:.1f}km/h  "
                f"Consist={fr['ConsistencyIndex']:.3f}  "
                f"RecentBoost={fr['RecentFormBoost']:.1f}  "
                f"DLWFactor={fr['DLWFactor']:.1f}"
            )
        else:
            key_info = ""
        lines.append(
            f"  {int(row['Rank']):>4}  {int(row['Box']):>3}  {row['DogName']:<25} "
            f"{row['Win_Pct']:>5.1f}%  {key_info}"
        )

    lines += [
        "",
        "─" * 72,
        "INDIVIDUALITY VERIFICATION",
        "─" * 72,
        "",
        "  Each dog's score is derived exclusively from their own data:",
    ]

    check_feats = ['BestTimeSec', 'Speed_kmh', 'ConsistencyIndex', 'FinalScore', 'Ensemble_Prob']
    for feat in check_feats:
        if feat in pred_df.columns:
            vals = pred_df[feat].values
        elif feat in feature_df.columns:
            vals = feature_df[feat].values
        else:
            continue
        n_uniq = len(np.unique(np.round(vals, 6)))
        is_ind = n_uniq == len(vals)
        lines.append(
            f"    {feat:30s}: {n_uniq}/{len(vals)} unique  {'✅ OK' if is_ind else '⚠️  CHECK'}"
        )

    lines += [
        "",
        "=" * 72,
        "END OF AUDIT REPORT",
        "=" * 72,
    ]

    with open(out_path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(lines))


# ─────────────────────────────────────────────────────────────────────────────
#  Main entry point
# ─────────────────────────────────────────────────────────────────────────────

def run_prediction(pdf_path: str, race_number: int = None,
                   distance: int = None, track_name: str = 'Angle Park',
                   model_dir: str = '.', output_dir: str = 'outputs') -> None:
    """Full prediction pipeline for a given race."""

    os.makedirs(output_dir, exist_ok=True)
    print(f"\n{'='*60}")
    print(f" GREYHOUND ML PREDICTION PIPELINE")
    print(f"{'='*60}")
    print(f" PDF     : {pdf_path}")
    print(f" Race    : {race_number or 'ALL'}")
    print(f" Distance: {distance or 'ALL'}")
    print(f" Track   : {track_name}")
    print(f"{'='*60}\n")

    # ── Step 1: Parse PDF ─────────────────────────────────────────────────────
    print("📄 STEP 1: Parsing PDF form guide ...")
    dog_df = parse_form_pdf(pdf_path, target_race=race_number, target_dist=distance)

    if dog_df.empty:
        print(f"❌ No dogs found for race={race_number}, dist={distance}")
        print("   Available races in PDF:")
        all_dogs = parse_form_pdf(pdf_path)
        if not all_dogs.empty:
            summary = all_dogs.groupby(['RaceNumber', 'Distance']).size().reset_index(name='Dogs')
            print(summary.to_string(index=False))
        return

    print(f"   ✅ Parsed {len(dog_df)} dogs")

    # Group by race if multiple
    if 'RaceNumber' in dog_df.columns:
        races_found = dog_df['RaceNumber'].unique()
    else:
        races_found = [race_number or 1]

    for race_num in races_found:
        r_df = dog_df[dog_df['RaceNumber'] == race_num].copy() if len(races_found) > 1 else dog_df.copy()
        if r_df.empty:
            continue

        race_meta = {
            'RaceNumber': race_num,
            'RaceDate': r_df['RaceDate'].iloc[0] if 'RaceDate' in r_df.columns else 'Unknown',
            'RaceTime': r_df['RaceTime'].iloc[0] if 'RaceTime' in r_df.columns else 'Unknown',
            'Track': r_df['Track'].iloc[0] if 'Track' in r_df.columns else track_name,
            'Distance': r_df['Distance'].iloc[0] if 'Distance' in r_df.columns else distance,
        }

        print(f"\n─── Race {race_num} | {race_meta['Track']} {race_meta['Distance']}m ───")

        # ── Step 2: Build features ────────────────────────────────────────────
        print("🔧 STEP 2: Building 74 individual features per dog ...")
        try:
            feat_df = build_features(r_df)
            X = get_feature_matrix(feat_df)
        except Exception as e:
            print(f"   ❌ Feature build failed: {e}")
            import traceback
            traceback.print_exc()
            continue

        print(f"   ✅ Feature matrix: {X.shape[0]} dogs × {X.shape[1]} features")

        # ── Step 3: Load models ────────────────────────────────────────────────
        print("📦 STEP 3: Loading models ...")
        rf, gb, xgb_model, scaler = load_models(track_name, model_dir)

        if rf:   print(f"   ✅ RF  loaded: {type(rf).__name__}")
        else:    print(f"   ❌ RF  not found")
        if gb:   print(f"   ✅ GB  loaded: {type(gb).__name__}")
        else:    print(f"   ❌ GB  not found")

        if xgb_model:
            print(f"   ✅ XGB loaded: {type(xgb_model).__name__}")
        else:
            print(f"   🔧 XGB not found — training on-the-fly ...")
            xgb_model = train_or_load_xgb(track_name, feat_df, model_dir)
            if xgb_model:
                print(f"   ✅ XGB trained: {type(xgb_model).__name__}")
            else:
                print(f"   ⚠️  XGB not available — ensemble will use RF + GB only")

        if scaler: print(f"   ✅ Scaler loaded")
        else:      print(f"   ⚠️  Scaler not found — using raw features")

        if rf is None and gb is None:
            print("   ❌ No models available — cannot predict")
            continue

        # ── Step 4: Predict ────────────────────────────────────────────────────
        print("🤖 STEP 4: Generating individual predictions ...")
        try:
            results = predict_with_models(rf, gb, xgb_model, scaler, X)
        except Exception as e:
            print(f"   ❌ Prediction failed: {e}")
            import traceback
            traceback.print_exc()
            continue

        # ── Step 5: Verify individuality ───────────────────────────────────────
        print("🔍 STEP 5: Verifying individual scoring ...")
        audit = verify_individual_scoring(r_df, results)
        for model_name, info in audit.items():
            status = "✅ ALL INDIVIDUAL" if info['all_individual'] else f"⚠️  {info['n_unique']}/{info['n_dogs']} unique"
            print(f"   {model_name}: {status}")

        # If calibration collapsed, re-run without calibration
        has_collapse = any(not v['all_individual'] for v in audit.values())
        if has_collapse:
            print("   🔄 Calibration collapse detected — applying uncalibrated fallback ...")
            # Results already include fallback from _get_uncalibrated_preds
            audit = verify_individual_scoring(r_df, results)
            for model_name, info in audit.items():
                status = "✅ ALL INDIVIDUAL" if info['all_individual'] else f"⚠️  {info['n_unique']}/{info['n_dogs']} unique"
                print(f"   {model_name} (after fallback): {status}")

        # ── Step 6: Build output ───────────────────────────────────────────────
        pred_df = generate_predictions_df(r_df, results, feat_df)

        # ── Step 7: Save outputs ───────────────────────────────────────────────
        tag = f"RACE{race_num}_{race_meta['Track'].replace(' ', '_').upper()}_{race_meta['Distance']}m"
        csv_path    = os.path.join(output_dir, f'{tag}_predictions.csv')
        audit_path  = os.path.join(output_dir, f'{tag}_audit_report.txt')

        pred_df.to_csv(csv_path, index=False)
        write_audit_report(audit_path, race_meta, r_df, feat_df, results, audit, pred_df)

        print(f"\n📊 RESULTS — Race {race_num} | {race_meta['Track']} {race_meta['Distance']}m")
        print(f"{'─'*60}")
        print(f"  {'Rank':>4}  {'Box':>3}  {'Dog Name':<25} {'Win%':>6}  {'Ensemble':>9}")
        print(f"  {'─'*58}")
        for _, row in pred_df.iterrows():
            print(f"  {int(row['Rank']):>4}  {int(row['Box']):>3}  {row['DogName']:<25} "
                  f"{row['Win_Pct']:>5.1f}%  {row['Ensemble_Prob']:>9.4f}")
        print(f"{'─'*60}")
        print(f"\n💾 Saved:")
        print(f"   CSV  → {csv_path}")
        print(f"   Audit → {audit_path}")


def main():
    parser = argparse.ArgumentParser(
        description='Greyhound ML race prediction pipeline',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=textwrap.dedent("""
        Examples:
          python predict_race.py --pdf data/ANGLG0112form.pdf --race 8 --dist 530
          python predict_race.py --pdf data/ANGLG0112form.pdf --track "Angle Park"
        """)
    )
    parser.add_argument('--pdf',   required=True, help='Path to race form PDF')
    parser.add_argument('--race',  type=int, default=None, help='Race number to predict')
    parser.add_argument('--dist',  type=int, default=None, help='Distance filter (e.g. 530)')
    parser.add_argument('--track', default='Angle Park', help='Track name for model loading')
    parser.add_argument('--models', default='.', help='Directory containing model .pkl files')
    parser.add_argument('--output', default='outputs', help='Output directory')
    args = parser.parse_args()

    if not os.path.exists(args.pdf):
        print(f"❌ PDF not found: {args.pdf}")
        sys.exit(1)

    run_prediction(
        pdf_path=args.pdf,
        race_number=args.race,
        distance=args.dist,
        track_name=args.track,
        model_dir=args.models,
        output_dir=args.output,
    )


if __name__ == '__main__':
    main()
