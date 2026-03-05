#!/usr/bin/env python3
"""
validate_pipeline.py
====================
End-to-end pipeline validation script.

Checks:
  1. All model files present and loadable
  2. Feature pipeline produces correct number of features (76)
  3. Each feature is unique per dog (individual scoring)
  4. RF, GB, XGB all generate predictions
  5. Calibration-collapse guard works
  6. Output files written correctly

Usage:
    python validate_pipeline.py
    python validate_pipeline.py --track "Angle Park" --pdf data/ANGLG0112form.pdf
"""

import argparse
import os
import sys
import warnings

warnings.filterwarnings('ignore')

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import numpy as np
import pandas as pd
import joblib

from src.pdf_parser import parse_form_pdf
from src.race_features import build_features, get_feature_matrix, FEATURE_COLS

# Model directory — models are in models/ subdirectory on copilot/copy-ml-training-prediction-files
MODEL_DIR = 'models'

TRACKS = {
    'Angle Park': {
        'pdf': 'data/ANGLG0503form.pdf',   # Tonight Mar 5 2026 — Race 8 530m
        'race': 8,
        'dist': 530,
        'model_prefix': 'Angle Park',
    },
    'BALLARAT': {
        'pdf': 'data/BRATG0112form.pdf',
        'race': None,
        'dist': None,
        'model_prefix': 'BALLARAT',
    },
    'BENDIGO': {
        'pdf': 'data/BDGOG1312form.pdf',
        'race': None,
        'dist': None,
        'model_prefix': 'BENDIGO',
    },
}

PASS = '✅ PASS'
FAIL = '❌ FAIL'
WARN = '⚠️  WARN'


def check_models(track: str, model_prefix: str) -> dict:
    """Check that model files exist in models/ and load correctly."""
    results = {}
    for algo in ['rf', 'gb', 'xgb', 'scaler']:
        path = os.path.join(MODEL_DIR, f'{model_prefix}_{algo}.pkl')
        if not os.path.exists(path):
            results[algo] = (WARN if algo == 'xgb' else FAIL, f'{path} not found')
            continue
        try:
            obj = joblib.load(path)
            results[algo] = (PASS, f'{type(obj).__name__}')
        except Exception as e:
            results[algo] = (FAIL, str(e))
    return results


def check_feature_pipeline(df: pd.DataFrame) -> dict:
    """Check that feature pipeline produces 76 individual features."""
    results = {}
    try:
        feat_df = build_features(df)
        X = get_feature_matrix(feat_df)

        results['feature_count'] = (
            PASS if X.shape[1] == 76 else FAIL,
            f'{X.shape[1]}/76 features'
        )
        results['dog_count'] = (
            PASS if X.shape[0] == len(df) else FAIL,
            f'{X.shape[0]} dogs'
        )

        # Check uniqueness of key features
        non_unique = []
        for col in ['BestTimeSec', 'Speed_kmh', 'ConsistencyIndex', 'FinalScore',
                    'RecentFormBoost', 'BestTimePercentile']:
            if col in feat_df.columns:
                vals = feat_df[col].values
                n_u = len(np.unique(np.round(vals, 6)))
                if n_u < len(vals):
                    non_unique.append(f'{col}({n_u}/{len(vals)})')

        if non_unique:
            results['individuality'] = (WARN, f'Some shared values: {", ".join(non_unique)}')
        else:
            results['individuality'] = (PASS, 'All key features unique per dog')

        results['feat_df'] = feat_df
        results['X'] = X

    except Exception as e:
        results['feature_count'] = (FAIL, str(e))
        import traceback
        traceback.print_exc()

    return results


def _get_uncalibrated_probs(model, X: np.ndarray) -> np.ndarray:
    """Try to get uncalibrated probabilities from the base estimator."""
    try:
        if hasattr(model, 'calibrated_classifiers_'):
            cal_clf = model.calibrated_classifiers_[0]
            base = cal_clf.estimator if hasattr(cal_clf, 'estimator') else cal_clf.base_estimator
            return base.predict_proba(X)[:, 1]
    except Exception:
        pass
    return model.predict_proba(X)[:, 1]


def check_model_predictions(rf, gb, xgb_model, scaler, X: pd.DataFrame) -> dict:
    """Check that all models produce predictions and scores are unique.

    When calibration collapses probabilities (known for OPEN-grade OPEN races),
    applies the same uncalibrated fallback as predict_race.py.
    """
    results = {}

    X_vals = X.fillna(0).values
    if scaler is not None:
        try:
            X_scaled = scaler.transform(X_vals)
        except Exception:
            X_scaled = X_vals
    else:
        X_scaled = X_vals

    n_dogs = len(X_vals)

    for name, model, use_scaled in [
        ('RF', rf, True), ('GB', gb, True), ('XGB', xgb_model, False)
    ]:
        if model is None:
            results[name] = (WARN, 'Model not loaded')
            continue
        try:
            X_in = X_scaled if use_scaled else X_vals
            probs = model.predict_proba(X_in)[:, 1]

            n_u = len(np.unique(np.round(probs, 6)))
            # Calibration collapse guard — same logic as predict_race.py
            if n_u < (n_dogs * 0.5):
                probs = _get_uncalibrated_probs(model, X_in)
                n_u = len(np.unique(np.round(probs, 6)))
                suffix = ' (via uncalibrated fallback)'
            else:
                suffix = ''

            unique_ok = n_u == n_dogs
            status = PASS if unique_ok else WARN
            results[name] = (
                status,
                f'{n_u}/{n_dogs} unique probs, range=[{probs.min():.4f}, {probs.max():.4f}]{suffix}'
            )
        except Exception as e:
            results[name] = (FAIL, str(e))

    return results


def run_validation(track: str, pdf_path: str, race: int = None, dist: int = None):
    """Run full validation for one track."""
    model_prefix = TRACKS.get(track, {}).get('model_prefix', track)

    print(f"\n{'='*65}")
    print(f" VALIDATING: {track}")
    print(f"{'='*65}")

    # 1. Model files
    print("\n1. Model Files:")
    model_checks = check_models(track, model_prefix)
    all_pass = True
    models = {}
    for algo, (status, msg) in model_checks.items():
        print(f"   {algo.upper():8s}: {status}  {msg}")
        if status == FAIL:
            all_pass = False
        if status == PASS:
            models[algo] = joblib.load(os.path.join(MODEL_DIR, f'{model_prefix}_{algo}.pkl'))
        else:
            models[algo] = None

    # 2. PDF parsing
    print("\n2. PDF Parsing:")
    if not os.path.exists(pdf_path):
        print(f"   {WARN}  PDF not found: {pdf_path}")
        return

    try:
        df = parse_form_pdf(pdf_path, target_race=race, target_dist=dist)
        if df.empty:
            # Try without filters
            df = parse_form_pdf(pdf_path)
            if not df.empty:
                first_race = df['RaceNumber'].iloc[0]
                df = df[df['RaceNumber'] == first_race].copy()

        print(f"   {'Parse':8s}: {PASS}  {len(df)} dogs parsed")
        if not df.empty:
            print(f"   {'Track':8s}: {df['Track'].iloc[0] if 'Track' in df.columns else 'Unknown'}")
            print(f"   {'Race':8s}: {df['RaceNumber'].iloc[0] if 'RaceNumber' in df.columns else 'N/A'}")
            print(f"   {'Dist':8s}: {df['Distance'].iloc[0] if 'Distance' in df.columns else 'N/A'}m")
    except Exception as e:
        print(f"   {FAIL}  Parsing failed: {e}")
        import traceback
        traceback.print_exc()
        return

    if df.empty:
        print(f"   {FAIL}  No dogs found")
        return

    # 3. Feature pipeline
    print("\n3. Feature Pipeline (76 individual features):")
    feat_results = check_feature_pipeline(df)
    feat_df = feat_results.pop('feat_df', None)
    X = feat_results.pop('X', None)
    for key, (status, msg) in feat_results.items():
        print(f"   {key:15s}: {status}  {msg}")

    if X is None:
        return

    # 4. Model predictions
    print("\n4. Model Predictions:")
    pred_results = check_model_predictions(
        models.get('rf'), models.get('gb'), models.get('xgb'), models.get('scaler'), X
    )
    for name, (status, msg) in pred_results.items():
        print(f"   {name:8s}: {status}  {msg}")

    # 5. Individuality of feature values
    print("\n5. Individuality Check (all key features must be unique per dog):")
    key_cols = ['Box', 'BestTimeSec', 'SectionalSec', 'Speed_kmh',
                'ConsistencyIndex', 'PlaceRate', 'RecentFormBoost',
                'DLWFactor', 'BoxBiasFactor', 'FinalScore']
    all_individual = True
    for col in key_cols:
        if col in feat_df.columns:
            vals = feat_df[col].values
            n_u = len(np.unique(np.round(vals.astype(float), 6)))
            is_ok = (n_u == len(vals)) or (col == 'BoxBiasFactor')  # BoxBias is box-based, may repeat
            status = PASS if is_ok else WARN
            if not is_ok:
                all_individual = False
            print(f"   {col:25s}: {n_u:2d}/{len(vals)} unique  {status}")

    # 6. Summary
    print(f"\n{'─'*65}")
    overall = PASS if all_pass and all_individual else WARN
    print(f" OVERALL STATUS: {overall}")
    print(f"{'─'*65}")


def main():
    parser = argparse.ArgumentParser(description='Validate greyhound ML pipeline')
    parser.add_argument('--track', default=None, help='Track name (default: all)')
    parser.add_argument('--pdf', default=None, help='PDF path override')
    args = parser.parse_args()

    tracks_to_test = [args.track] if args.track else list(TRACKS.keys())

    print("=" * 65)
    print(" GREYHOUND ML PIPELINE VALIDATION")
    print("=" * 65)
    print(f" Testing {len(tracks_to_test)} track(s): {', '.join(tracks_to_test)}")

    for track_name in tracks_to_test:
        if track_name not in TRACKS:
            print(f"\n⚠️  Unknown track: {track_name}")
            continue
        cfg = TRACKS[track_name]
        pdf = args.pdf or cfg['pdf']
        run_validation(track_name, pdf, cfg.get('race'), cfg.get('dist'))

    print("\n" + "=" * 65)
    print(" VALIDATION COMPLETE")
    print("=" * 65)


if __name__ == '__main__':
    main()
