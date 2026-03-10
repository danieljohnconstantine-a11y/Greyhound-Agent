#!/usr/bin/env python3
"""
train_xgb_models.py
===================
Trains XGBoost models for each track using real PDF form data and race results.

Strategy:
  1. Load race results from data/results_*.csv (factual data only)
  2. Match results to PDF form data in data/ directory
  3. For each track with sufficient data, train a calibrated XGBoost model
  4. Use the EXISTING per-track scaler so XGB features are consistent with RF+GB
  5. Save models/{track_name}_xgb.pkl alongside the existing RF+GB models

FACTUAL DATA ONLY — no synthetic or generated race data is used.

Usage:
    python train_xgb_models.py
    python train_xgb_models.py --tracks "Angle Park" BALLARAT BENDIGO
    python train_xgb_models.py --min-samples 20
"""

import argparse
import gc
import glob
import os
import pickle
import re
import sys
import traceback
import warnings
# Suppress known non-critical warnings from XGBoost and sklearn calibration
warnings.filterwarnings("ignore", category=UserWarning, module="xgboost")
warnings.filterwarnings("ignore", category=FutureWarning, module="sklearn")
warnings.filterwarnings("ignore", message=".*use_label_encoder.*")

import numpy as np
import pandas as pd
from sklearn.calibration import CalibratedClassifierCV
from sklearn.metrics import accuracy_score, roc_auc_score
from sklearn.model_selection import train_test_split

try:
    import xgboost as xgb
    HAS_XGBOOST = True
except ImportError:
    HAS_XGBOOST = False
    print("ERROR: XGBoost not installed.  Run: pip install xgboost")
    sys.exit(1)

# ---------------------------------------------------------------------------
# Track name normalisation (must match the same logic used in training data)
# ---------------------------------------------------------------------------
_TRACK_MAP = {
    'angle park': 'ANGL',
    'ballarat': 'BRAT',
    'bendigo': 'BDGO',
    'bulli': 'BULI',
    'cannington': 'CANN',
    'capalaba': 'CAPA',
    'betdeluxe capalaba': 'CAPA',
    'casino': 'CSNO',
    'darwin': 'DRWN',
    'dubbo': 'DUBB',
    'gawler': 'GAWL',
    'geelong': 'GEEL',
    'gosford': 'GOSF',
    'goulburn': 'GOUL',
    'grafton': 'GRAF',
    'gunnedah': 'GUNN',
    'healesville': 'HEAL',
    'hobart': 'ELWK',
    'horsham': 'HSHM',
    'launceston': 'ELWK',
    'maitland': 'MAIT',
    'mandurah': 'MAND',
    'meadows': 'MEAD',
    'the meadows': 'MEAD',
    'mount gambier': 'MTGG',
    'murray bridge': 'MBRS',
    'murray bridge straight': 'MBRS',
    'nowra': 'NOWR',
    'richmond': 'RICH',
    'rockhampton': 'ROCK',
    'betdeluxe rockhampton': 'ROCK',
    'sale': 'SALE',
    'sandown': 'SAND',
    'shepparton': 'SHEP',
    'temora': 'TEMO',
    'townsville': 'TOWN',
    'bet nation townsville': 'TOWN',
    'wagga': 'WAGG',
    'warragul': 'WARG',
    'wentworth park': 'WENP',
    'wollongong': 'WNBL',
    'ladbrokes q1 lakeside': 'QLAK',
    'ladbrokes q2 parklands': 'QPRK',
    'ladbrokes q straight': 'QSTR',
    'albion park': 'QSTR',
    'ipswich': 'QPRK',
}


def _normalise_track(name: str) -> str:
    lower = str(name).lower().strip()
    if lower in _TRACK_MAP:
        return _TRACK_MAP[lower]
    for full, code in _TRACK_MAP.items():
        if full in lower or lower in full:
            return code
    return name[:4].upper()


def _parse_result(result_str: str) -> list:
    """Parse compact result string '1875' -> [1,8,7,5].  '0' = box 10."""
    boxes = []
    for ch in str(result_str).strip():
        boxes.append(10 if ch == '0' else int(ch))
    return boxes


def load_results(data_dir: str = 'data') -> list:
    """Load all race results from data/results_*.csv files.

    Returns a list of dicts with keys:
        date, track, track_code, race, winner, 2nd, 3rd, 4th
    """
    results = []

    # Handle two CSV formats:
    #   1. Proper format: Track, Date, Race, Winner, 2nd, 3rd, 4th
    #   2. Compact format: Track, Race, Result  (date embedded in Track field)
    for csv_path in sorted(glob.glob(os.path.join(data_dir, 'results_*.csv'))):
        filename = os.path.basename(csv_path)
        date_match = re.search(r'results_(\d{4}-\d{2}-\d{2})\.csv', filename)
        file_date = date_match.group(1) if date_match else ''

        try:
            df = pd.read_csv(csv_path)
        except Exception as exc:
            print(f"  [WARN] Could not read {csv_path}: {exc}")
            continue

        cols = set(df.columns)

        for _, row in df.iterrows():
            track_raw = str(row.get('Track', ''))
            race_str  = str(row.get('Race', row.get('RaceNumber', '0')))
            race_num  = int(race_str.replace('R', '').replace('r', ''))

            # Determine date
            if 'Date' in cols and pd.notna(row.get('Date')):
                date = str(row['Date']).strip()
            else:
                date = file_date

            # Handle compact Result column ("1875") vs explicit Winner/2nd/3rd/4th
            if 'Result' in cols:
                boxes = _parse_result(row['Result'])
                winner = boxes[0] if len(boxes) > 0 else 0
                second = boxes[1] if len(boxes) > 1 else 0
                third  = boxes[2] if len(boxes) > 2 else 0
                fourth = boxes[3] if len(boxes) > 3 else 0
                # Strip embedded date from track name if present, e.g. "Angle Park25/11/25"
                track_m = re.match(r'^(.+?)\d{2}/\d{2}/\d{2}$', track_raw.strip())
                track = track_m.group(1).strip() if track_m else track_raw.strip()
            else:
                track = track_raw.strip()
                winner = 0
                for col in ('Winner', 'Position1'):
                    if col in cols and pd.notna(row.get(col)):
                        val = str(row[col]).strip().upper()
                        if val == 'ABD':
                            winner = -1
                            break
                        winner = int(row[col])
                        break
                if winner == -1:
                    continue  # abandoned race
                second = int(row['2nd']) if '2nd' in cols and pd.notna(row.get('2nd')) else 0
                third  = int(row['3rd']) if '3rd' in cols and pd.notna(row.get('3rd')) else 0
                fourth = int(row['4th']) if '4th' in cols and pd.notna(row.get('4th')) else 0

            if not (track and race_num and winner and date):
                continue

            results.append({
                'date': date,
                'track': track,
                'track_code': _normalise_track(track),
                'race': race_num,
                'winner': winner,
                '2nd': second,
                '3rd': third,
                '4th': fourth,
            })

    return results


def load_pdf_races(data_dir: str = 'data', track_codes_needed: set = None) -> dict:
    """Parse PDFs in data_dir and return {key: race_df}.

    Key format: "{date}_{TRACK_CODE}_R{race_num}"  or  "{TRACK_CODE}_R{race_num}"

    Args:
        data_dir: directory containing PDF files
        track_codes_needed: if provided, only parse PDFs whose filename track code
                            is in this set (e.g. {'ANGL', 'BRAT'}).  Parsing 73
                            PDFs can take 5-10 minutes; filtering to the 1-3 we
                            actually need cuts this to seconds.
    """
    try:
        import pdfplumber
    except ImportError:
        print("ERROR: pdfplumber not installed.  Run: pip install pdfplumber")
        sys.exit(1)

    from src.parser import parse_race_form
    from src.features import compute_features

    pdf_races = {}
    all_pdf_files = sorted(glob.glob(os.path.join(data_dir, '*form.pdf')))

    # Filter to only the PDFs we need
    pdf_files = []
    for pdf_path in all_pdf_files:
        filename = os.path.basename(pdf_path)
        m = re.match(r'([A-Z]+)G(\d{2})(\d{2})form\.pdf', filename)
        if m and track_codes_needed is not None:
            if m.group(1) in track_codes_needed:
                pdf_files.append(pdf_path)
        else:
            pdf_files.append(pdf_path)

    if track_codes_needed:
        print(f"  Parsing {len(pdf_files)}/{len(all_pdf_files)} PDFs "
              f"(filtered to tracks: {sorted(track_codes_needed)})…")
    else:
        print(f"  Parsing {len(pdf_files)} PDF files…")

    for i, pdf_path in enumerate(pdf_files, 1):
        filename = os.path.basename(pdf_path)
        m = re.match(r'([A-Z]+)G(\d{2})(\d{2})form\.pdf', filename)
        pdf_date = None
        pdf_code = None
        if m:
            pdf_code = m.group(1)
            day, mon = m.group(2), m.group(3)
            # Infer year: use the current year for the most recent season.
            # PDF filenames encode only DDMM; we assume the file belongs to the
            # most recent matching calendar year relative to today's date.
            import datetime
            today = datetime.date.today()
            # Try current year first; if the resulting date is more than
            # 6 months in the future, fall back to the previous year.
            candidate = datetime.date(today.year, int(mon), int(day))
            if (candidate - today).days > 180:
                year = str(today.year - 1)
            else:
                year = str(today.year)
            pdf_date = f"{year}-{mon}-{day}"

        try:
            with pdfplumber.open(pdf_path) as pdf:
                text = ''.join(
                    (page.extract_text() or '') + '\n'
                    for page in pdf.pages
                )
            df = parse_race_form(text)
            if df is None or df.empty:
                continue
            df = compute_features(df)
            # Downcast to save memory
            for col in df.select_dtypes('float64').columns:
                df[col] = df[col].astype('float32')

            if 'Track' in df.columns and 'RaceNumber' in df.columns:
                for (_, race_num), df_race in df.groupby(['Track', 'RaceNumber']):
                    if pdf_date and pdf_code:
                        key = f"{pdf_date}_{pdf_code}_R{race_num}"
                    else:
                        key = f"{filename[:4]}_R{race_num}"
                    pdf_races[key] = df_race
        except Exception:
            pass

        if i % 20 == 0:
            gc.collect()
            print(f"  … {i}/{len(pdf_files)} done")

    gc.collect()
    return pdf_races


def _get_training_data(results: list, pdf_races: dict, target_track_code: str) -> pd.DataFrame:
    """Assemble training rows for one track code from matching PDF+result pairs.

    Uses Top-4 weighted training:
        1st = weight 1.0, 2nd = 0.7, 3rd = 0.5, 4th = 0.3
    """
    rows = []

    for r in results:
        if r['track_code'] != target_track_code:
            continue
        date, race_num = r['date'], r['race']
        key_date = f"{date}_{target_track_code}_R{race_num}"
        key_plain = f"{target_track_code}_R{race_num}"

        df_race = pdf_races.get(key_date)
        if df_race is None:
            df_race = pdf_races.get(key_plain)
        if df_race is None or df_race.empty:
            continue

        for box, weight in [
            (r['winner'], 1.0),
            (r.get('2nd', 0), 0.7),
            (r.get('3rd', 0), 0.5),
            (r.get('4th', 0), 0.3),
        ]:
            if box and box in df_race['Box'].values:
                tmp = df_race.copy()
                tmp['_target'] = (tmp['Box'] == box).astype(int)
                tmp['_weight'] = np.where(tmp['Box'] == box, weight, 0.05)
                rows.append(tmp)

    if not rows:
        return pd.DataFrame()
    return pd.concat(rows, ignore_index=True)


def train_xgb_for_track(
    track_name: str,
    feature_cols: list,
    scaler,
    X_all: np.ndarray,
    y_all: np.ndarray,
    w_all: np.ndarray,
    min_positive: int = 5,
) -> object:
    """Train and calibrate an XGBoost model for one track.

    Uses the EXISTING scaler so features are on the same scale as RF+GB.
    Returns calibrated CalibratedClassifierCV or None on failure.
    """
    n_samples = len(X_all)
    n_pos = int(y_all.sum())
    print(f"    Samples: {n_samples}  |  Positive labels: {n_pos}")

    if n_pos < min_positive:
        print(f"    [SKIP] Too few positive samples ({n_pos} < {min_positive})")
        return None

    # Scale using the pre-fitted scaler (same as RF+GB)
    X_scaled = scaler.transform(X_all)

    # For calibration we need at least 2 samples per class and enough for CV splits
    cv = min(3, n_pos) if n_pos >= 3 else None
    if cv is None or n_pos < 3:
        print(f"    [SKIP] Not enough samples for calibrated training")
        return None

    # Adaptive complexity based on dataset size
    n_estimators = 200 if n_samples > 400 else 150 if n_samples > 200 else 100
    max_depth     = 6   if n_samples > 400 else 5   if n_samples > 200 else 4

    xgb_model = xgb.XGBClassifier(
        n_estimators=n_estimators,
        max_depth=max_depth,
        learning_rate=0.05,
        subsample=0.8,
        colsample_bytree=0.8,
        min_child_weight=3,
        use_label_encoder=False,
        eval_metric='logloss',
        random_state=42,
        verbosity=0,
        n_jobs=1,
    )
    xgb_model.fit(X_scaled, y_all, sample_weight=w_all)

    # Calibrate with isotonic regression
    print(f"    Calibrating with cv={cv}…")
    cal = CalibratedClassifierCV(xgb_model, method='isotonic', cv=cv)
    cal.fit(X_scaled, y_all, sample_weight=w_all)

    # Quick accuracy check
    try:
        preds = cal.predict_proba(X_scaled)[:, 1]
        preds_binary = (preds >= 0.5).astype(int)
        acc = accuracy_score(y_all, preds_binary)
        n_unique = len(set(preds.round(6)))
        print(f"    Train accuracy: {acc:.1%}  |  Unique probs (train): {n_unique}/{n_samples}")
    except Exception:
        pass

    return cal


def save_xgb_model(model, track_name: str, models_dir: str = 'models') -> str:
    path = os.path.join(models_dir, f"{track_name}_xgb.pkl")
    with open(path, 'wb') as f:
        pickle.dump(model, f)
    return path


def main() -> int:
    parser = argparse.ArgumentParser(description='Train XGBoost models for each track.')
    parser.add_argument('--data-dir',    default='data',   help='Directory with PDFs and results CSVs')
    parser.add_argument('--models-dir',  default='models', help='Models directory')
    parser.add_argument('--tracks',      nargs='*',        help='Specific track names to train (default: all)')
    parser.add_argument('--min-samples', type=int, default=20, help='Min training samples per track')
    args = parser.parse_args()

    print('=' * 70)
    print(' XGBoost Model Training — FACTUAL DATA ONLY')
    print('=' * 70)

    # ------------------------------------------------------------------
    # Load results
    # ------------------------------------------------------------------
    print('\n[1/4] Loading race results from CSV files…')
    results = load_results(args.data_dir)
    if not results:
        print('ERROR: No race results found.  Ensure data/results_*.csv exists.')
        return 1
    track_codes = {}
    for r in results:
        code = r['track_code']
        track_codes[code] = track_codes.get(code, [])
        track_codes[code].append(r['track'])
    # Resolve track_code → canonical track name (most common)
    code_to_canonical = {
        code: max(set(names), key=names.count)
        for code, names in track_codes.items()
    }
    print(f'  Loaded {len(results)} race results for {len(track_codes)} track codes')

    # ------------------------------------------------------------------
    # Load ensemble config (feature list + track names)
    # ------------------------------------------------------------------
    config_path = os.path.join(args.models_dir, 'ensemble_config.json')
    import json
    with open(config_path) as f:
        ensemble_cfg = json.load(f)
    all_feature_cols = ensemble_cfg.get('feature_cols', [])
    registered_tracks = ensemble_cfg.get('tracks', [])

    # ------------------------------------------------------------------
    # Parse PDFs — only the ones matching tracks that have results
    # ------------------------------------------------------------------
    print('\n[2/4] Parsing PDF form guides…')
    # Determine which PDF track codes we actually need
    result_codes = {r['track_code'] for r in results}
    # Intersect with tracks that have a scaler (i.e. registered tracks)
    codes_with_scaler = set()
    for reg_track in registered_tracks:
        code = _normalise_track(reg_track)
        scaler_path = os.path.join(args.models_dir, f'{reg_track}_scaler.pkl')
        if os.path.exists(scaler_path) and code in result_codes:
            codes_with_scaler.add(code)
    print(f'  Track codes with both results and scaler: {sorted(codes_with_scaler)}')
    pdf_races = load_pdf_races(args.data_dir, track_codes_needed=codes_with_scaler or None)
    print(f'  Extracted {len(pdf_races)} race groups from PDFs')

    if not pdf_races:
        print('ERROR: No races extracted from PDFs.')
        return 1

    # ------------------------------------------------------------------
    # Train XGBoost for registered tracks that have a scaler
    # ------------------------------------------------------------------
    # Always train all registered tracks (Angle Park, BALLARAT, BENDIGO).
    # Tracks without their own results use cross-track fallback data (real
    # factual data from other venues on the same feature space).
    all_registered = registered_tracks if registered_tracks else list(
        code_to_canonical.values()
    )
    requested_set = set(args.tracks) if args.tracks else set(all_registered)
    # Also include any track that has a scaler + results
    for reg_track in all_registered:
        if os.path.exists(os.path.join(args.models_dir, f'{reg_track}_scaler.pkl')):
            requested_set.add(reg_track)

    # Build combined cross-track dataset for fallback
    all_track_df = None

    # ------------------------------------------------------------------
    # Train XGBoost for each track
    # ------------------------------------------------------------------
    print(f'\n[3/4] Training XGBoost for {len(requested_set)} track(s)…')
    trained = []
    skipped = []

    for track_name in sorted(requested_set):
        track_code = _normalise_track(track_name)
        print(f'\n  Track: {track_name} [{track_code}]')

        # Load the existing scaler for this track
        scaler_path = os.path.join(args.models_dir, f'{track_name}_scaler.pkl')
        if not os.path.exists(scaler_path):
            print(f'    [SKIP] Scaler not found: {scaler_path}')
            skipped.append(track_name)
            continue

        with open(scaler_path, 'rb') as f:
            scaler = pickle.load(f)

        # Determine actual feature columns (reconcile with scaler)
        if hasattr(scaler, 'feature_names_in_'):
            feature_cols = list(scaler.feature_names_in_)
        else:
            n_scaler = len(scaler.mean_) if hasattr(scaler, 'mean_') else len(all_feature_cols)
            feature_cols = all_feature_cols[:n_scaler]

        print(f'    Features: {len(feature_cols)}')

        # Assemble training data — track-specific first, then cross-track fallback
        df_train = _get_training_data(results, pdf_races, track_code)
        used_fallback = False

        if df_train.empty:
            # Cross-track fallback: use all available result+PDF pairs from any track.
            # This is factual data from real races; the feature space is the same
            # 74-feature vector normalised by the per-track scaler.
            print(f'    No track-specific data → using cross-track fallback (all available PDF+result data)')
            if all_track_df is None:
                # Build once and reuse
                frames = []
                for code in set(r['track_code'] for r in results):
                    df_tmp = _get_training_data(results, pdf_races, code)
                    if not df_tmp.empty:
                        frames.append(df_tmp)
                all_track_df = pd.concat(frames, ignore_index=True) if frames else pd.DataFrame()
            df_train = all_track_df.copy()
            used_fallback = True

        if df_train.empty:
            print(f'    [SKIP] No training data available (even cross-track fallback is empty)')
            skipped.append(track_name)
            continue

        # Build feature matrix
        missing_cols = [c for c in feature_cols if c not in df_train.columns]
        for col in missing_cols:
            df_train[col] = 0.0

        X = df_train[feature_cols].fillna(0).values.astype(float)
        y = df_train['_target'].values.astype(int)
        w = df_train['_weight'].values.astype(float)

        source = 'cross-track fallback' if used_fallback else 'track-specific'
        print(f'    Training rows: {len(X)}  |  positive: {int(y.sum())}  [{source}]')

        if len(X) < args.min_samples:
            print(f'    [SKIP] Not enough training samples ({len(X)} < {args.min_samples})')
            skipped.append(track_name)
            continue

        model = train_xgb_for_track(track_name, feature_cols, scaler, X, y, w)
        if model is None:
            skipped.append(track_name)
            continue

        # Save
        save_path = save_xgb_model(model, track_name, args.models_dir)
        size_kb = os.path.getsize(save_path) // 1024
        print(f'    ✅  Saved → {save_path}  ({size_kb} KB)')
        trained.append(track_name)

    # ------------------------------------------------------------------
    # Summary
    # ------------------------------------------------------------------
    print('\n[4/4] Summary')
    print('=' * 70)
    print(f'  Trained ({len(trained)}): {trained}')
    print(f'  Skipped ({len(skipped)}): {skipped}')

    if not trained:
        print('\nERROR: No XGBoost models were trained.')
        return 1

    print('\n✅  XGBoost training complete.')
    return 0


if __name__ == '__main__':
    sys.exit(main())
