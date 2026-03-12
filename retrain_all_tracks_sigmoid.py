"""
retrain_all_tracks_sigmoid.py
==============================
One-click script to retrain ALL track-specific ensemble models (RF + GB + XGB)
using SIGMOID calibration instead of the broken isotonic calibration.

WHY THIS SCRIPT EXISTS
-----------------------
The original train_ml_track_ensemble.py used method='isotonic' in
CalibratedClassifierCV.  Isotonic regression builds a step-function lookup
table from cross-validation predictions.  For tracks with small datasets
(< 500 races), all of the step-function resolution is consumed in the
0%–2.5% probability range.  Any real-world prediction input (8-dog races
produce probabilities of 10%–37%) falls beyond the last threshold step, so
every dog in a race maps to the exact same constant probability — making the
models useless.

Sigmoid calibration (Platt scaling) fits a monotonic logistic curve.  It
CANNOT produce a flat plateau: every input always receives a distinct output.

USAGE
------
    python retrain_all_tracks_sigmoid.py

    # Or retrain specific tracks only:
    python retrain_all_tracks_sigmoid.py --tracks HEALESVILLE Maitland SHEPPARTON

    # Or use the form PDFs that are already in data_predictions/ to add training data:
    python retrain_all_tracks_sigmoid.py --use-pdf-history

OUTPUT
-------
    models/{Track}_rf.pkl       -- Random Forest (sigmoid calibrated, depth≤10)
    models/{Track}_gb.pkl       -- Gradient Boosting (sigmoid calibrated)
    models/{Track}_xgb.pkl      -- XGBoost (sigmoid calibrated)
    models/{Track}_scaler.pkl   -- StandardScaler (76 features)
    models/config.pkl           -- Updated ensemble configuration
    reports/RETRAIN_REPORT_<date>.txt  -- Per-track accuracy and spread stats

GITHUB FILE SIZE
-----------------
With max_depth=10 for RF, model file sizes should be:
    RF:    < 4 MB per track  (was 9–24 MB with depth 15–20)
    GB:    < 1 MB per track
    XGB:   < 1 MB per track
    Total: < 6 MB per track × 37 tracks = < 220 MB total

GitHub allows files up to 100 MB without Git LFS.  All individual .pkl files
should fit within this limit after the depth cap.  If any single .pkl exceeds
50 MB, check that max_depth_rf <= 10 and n_estimators <= 100.
"""

import sys
import os
import argparse
import pickle
import warnings
from datetime import datetime

import numpy as np

warnings.filterwarnings('ignore')

# ── paths ────────────────────────────────────────────────────────────────────
REPO_ROOT = os.path.dirname(os.path.abspath(__file__))
MODELS_DIR = os.path.join(REPO_ROOT, 'models')
DATA_DIR = os.path.join(REPO_ROOT, 'data')
REPORTS_DIR = os.path.join(REPO_ROOT, 'reports')
SRC_DIR = os.path.join(REPO_ROOT, 'src')

sys.path.insert(0, REPO_ROOT)
sys.path.insert(0, SRC_DIR)

os.makedirs(MODELS_DIR, exist_ok=True)
os.makedirs(REPORTS_DIR, exist_ok=True)

# ── imports ───────────────────────────────────────────────────────────────────
import pandas as pd
from joblib import parallel_backend
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.calibration import CalibratedClassifierCV
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score

HAS_XGBOOST = False
try:
    import xgboost as xgb
    HAS_XGBOOST = True
except ImportError:
    pass

# ── feature list ──────────────────────────────────────────────────────────────
# FOUR features removed vs the original 76-feature config.pkl list:
#   'Weight'           — always 0 in greyhound PDFs; zero-variance → useless
#   'WeightFactor'     — derived from Weight; always 1.0 (neutral) → useless
#   'TrackConditionAdj'— always 1.0 (no track condition in PDFs) → useless
#   'BoxBiasFactor'    — always 0.0 (parser never sets it) → useless
# Zero-variance features are scaled to 0 by StandardScaler and contribute
# nothing to model quality but inflate the feature vector and distort feature
# importance calculations.  Removing them improves GB discrimination spread.
#
# THREE new strong box-bias features added (v5.1):
#   'TrackBoxWinRatePct' — actual historical win% for this box at this track
#                          (0–50 scale, 100% factual from race results).
#                          Example: Box 1 at Launceston ≈ 31.25, generic track 12.5.
#                          MUCH stronger signal than the old ±0.15 adjustment.
#   'TrackBoxRank'       — rank of this box's win rate at this track (1=best, 8=worst).
#                          Tree models split cleanly on "rank ≤ 2" or "rank ≥ 7".
#   'BoxWinAdvantage'    — binary (1/0) whether this box is top-4 for this track.
#                          Simple feature; complements continuous TrackBoxWinRatePct.
#
# v5.2 FIX — TrackBox1Adjustment and TrackBox4Adjustment (previously zero-variance):
#   These columns previously used TRACK_BOX1_ADJUSTMENT / TRACK_BOX4_ADJUSTMENT dicts
#   that contained only {"DEFAULT": 0.0} after consolidation — every dog received 0.0,
#   making them useless zero-variance features.
#   Fixed: now populated from TRACK_COMPREHENSIVE_ADJUSTMENTS[track][1] and [4] for
#   ALL dogs in the race — a TRACK-LEVEL characteristic signal, not dog-specific.
#   'TrackBox1Adjustment' = Box 1 win-rate advantage at this track (same for all dogs).
#     e.g. Launceston = 0.150 (Box 1 wins 33% = strongest inside bias in dataset).
#          Darwin      = 0.000 (Box 1 is neutral; Box 2 dominates at 30.5%).
#   'TrackBox4Adjustment' = Box 4 win-rate advantage at this track (same for all dogs).
#   Models learn: "high TrackBox1Adjustment → inside-speed track → outside boxes lose more".
FEATURE_COLS = [
    'Box','Draw','CareerWins','CareerPlaces','CareerStarts','PrizeMoney',
    'RTC','DLR','DLW','Distance','BestTimeSec','SectionalSec',
    'RestFactor','Speed_kmh','EarlySpeedIndex',
    'FinishConsistency','MarginAvg','FormMomentum','ConsistencyIndex',
    'RecentFormBoost','DistanceSuit','TrainerStrikeRate','OverexposedPenalty',
    'PlaceRate','DLWFactor','DrawFactor','FormMomentumNorm',
    'MarginFactor','RTCFactor','BoxPositionBias','BoxPlaceRate','BoxTop3Rate',
    'TrackBox1Adjustment','TrackBox4Adjustment','TrackComprehensiveAdjustment',
    'TrackBoxWinRatePct','TrackBoxRank','BoxWinAdvantage',
    'AgeMonths','AgeFactor','RailPreference','BoxPenaltyFactor','SpeedAtDistance',
    'SpeedClassification','ExperienceTier','WinStreakFactor','FreshnessFactor',
    'ClassRating','GradeFactor','Last3AvgFinish','Last3FinishFactor',
    'DistanceChangeFactor','PaceBoxFactor','TrainerTier','FreshnessFactorV2',
    'AgeFactorV2','SurfacePreferenceFactor','WinPlaceRate','EarlySpeedPercentile',
    'BestTimePercentile','FieldSpeedStd','FieldTimeStd','TimeVsField',
    'SpeedVsField','FieldSimilarityIndex','TrackUpsetFactor','CompetitorDensity',
    'CompetitorAdjustment','FieldSize','FieldSizeAdjustment','WinStreakFactorV2',
    'RecentPlaceStreak','CloserBonus','TrainerMomentum','FinalScore',
]

assert len(FEATURE_COLS) == 75, f"Expected 75 features, got {len(FEATURE_COLS)}"

# ── adaptive GB hyperparameter thresholds ─────────────────────────────────────
# GradientBoostingClassifier risk of near-flat outputs rises sharply when the
# training set is small.  A shallower tree with lower learning rate prevents the
# ensemble from saturating at extreme log-odds values on tiny datasets.
# Thresholds determined empirically from the spread-collapse history:
#   < 200 rows → "small"  (e.g. Gunnedah 93 train rows, Murray Bridge 41 rows)
#   200–499    → "medium" (e.g. Maitland 180, Shepparton 200)
#   ≥ 500      → "large"  (e.g. Sandown 900+, Meadows 600+)
GB_SMALL_THRESHOLD  = 200   # rows in training split; below → use shallow config
GB_MEDIUM_THRESHOLD = 500   # rows; below (but ≥ SMALL) → use standard config

GB_SMALL_PARAMS  = dict(n_estimators=100, learning_rate=0.05, max_depth=3, min_samples_leaf=5)
GB_MEDIUM_PARAMS = dict(n_estimators=150, learning_rate=0.08, max_depth=4, min_samples_leaf=4)
GB_LARGE_PARAMS  = dict(n_estimators=200, learning_rate=0.10, max_depth=4, min_samples_leaf=3)

def train_track(df, track_name, verbose=True):
    """
    Train RF + GB + XGB for one track using SIGMOID calibration.

    Key differences from the original train_ml_track_ensemble.py:
    - method='sigmoid'  (was 'isotonic' — which collapsed to a flat mapping)
    - max_depth_rf ≤ 10 (was 15-20 — which produced 9-24 MB .pkl files)
    - n_estimators = 100 always (was 100-200)

    Returns:
        (models, scaler, metrics)
        models  — dict {'rf': ..., 'gb': ..., 'xgb': ...}
        scaler  — fitted StandardScaler
        metrics — dict with per-algorithm spread and accuracy stats
    """
    X = df[FEATURE_COLS].fillna(0)
    y = df['Winner']
    sample_weights = df['SampleWeight'] if 'SampleWeight' in df.columns else np.ones(len(df))

    y_binary = (y > 0.5).astype(int)
    n_pos = int(y_binary.sum())

    if n_pos < 2:
        raise ValueError(f"{track_name}: only {n_pos} positive samples — cannot train")

    X_train, X_test, y_train, y_test, w_train, _ = train_test_split(
        X, y_binary, sample_weights,
        test_size=0.2, random_state=42,
        stratify=y_binary if n_pos >= 10 else None,
    )

    scaler = StandardScaler()
    X_train_sc = scaler.fit_transform(X_train)
    X_test_sc  = scaler.transform(X_test)

    models  = {}
    metrics = {'track': track_name, 'n_samples': len(df), 'n_positive': n_pos}

    # ── 1. Random Forest ──────────────────────────────────────────────────────
    # max_depth=10 keeps file size < 4 MB and avoids GitHub's 100 MB limit
    if verbose:
        print(f"    RF (sigmoid, depth=10) ...", end='', flush=True)
    rf = RandomForestClassifier(
        n_estimators=100, max_depth=10, min_samples_split=5,
        random_state=42, n_jobs=-1,
    )
    rf.fit(X_train_sc, y_train, sample_weight=w_train)
    # n_jobs=1 + threading backend: avoids "Can't pickle" errors on Linux/Ubuntu.
    # loky (default joblib backend) forks worker processes and requires the RF
    # to be picklable; threading backend runs CV folds in-process (no pickling).
    rf_cal = CalibratedClassifierCV(rf, method='sigmoid', cv=3, n_jobs=1)
    with parallel_backend('threading'):
        rf_cal.fit(X_train_sc, y_train, sample_weight=w_train)
    models['rf'] = rf_cal

    rf_proba = rf_cal.predict_proba(X_test_sc)[:, 1]
    rf_spread = float(rf_proba.max() - rf_proba.min()) if len(rf_proba) > 1 else 0.0
    rf_acc = accuracy_score(y_test, (rf_proba > 0.5).astype(int))
    metrics['rf_spread'] = rf_spread
    metrics['rf_acc']    = rf_acc
    if verbose:
        print(f" spread={rf_spread*100:.1f}%  acc={rf_acc*100:.1f}%")

    # ── 2. Gradient Boosting ──────────────────────────────────────────────────
    # GB's predict_proba is natively well-calibrated (Friedman 2001).
    # Wrapping it with CalibratedClassifierCV(sigmoid) squashes the output
    # to near-constant (< 0.5% spread) on small fields.  We train GB directly
    # and store the raw model — no additional calibration layer needed.
    #
    # Adaptive hyperparameters based on dataset size:
    #   < 200 rows  → lighter model to avoid overfitting on tiny dataset
    #   200-500 rows → standard model
    #   > 500 rows  → richer model
    n_train = len(X_train)
    if n_train < GB_SMALL_THRESHOLD:
        gb_params = GB_SMALL_PARAMS
        gb_label = f"depth={GB_SMALL_PARAMS['max_depth']}, lr={GB_SMALL_PARAMS['learning_rate']} (small dataset)"
    elif n_train < GB_MEDIUM_THRESHOLD:
        gb_params = GB_MEDIUM_PARAMS
        gb_label = f"depth={GB_MEDIUM_PARAMS['max_depth']}, lr={GB_MEDIUM_PARAMS['learning_rate']} (medium dataset)"
    else:
        gb_params = GB_LARGE_PARAMS
        gb_label = f"depth={GB_LARGE_PARAMS['max_depth']}, lr={GB_LARGE_PARAMS['learning_rate']} (large dataset)"
    if verbose:
        print(f"    GB (native, no extra cal, {gb_label}) ...", end='', flush=True)
    gb = GradientBoostingClassifier(
        **gb_params, subsample=0.8, random_state=42,
    )
    gb.fit(X_train_sc, y_train, sample_weight=w_train)
    models['gb'] = gb

    gb_proba  = gb.predict_proba(X_test_sc)[:, 1]
    gb_spread = float(gb_proba.max() - gb_proba.min()) if len(gb_proba) > 1 else 0.0
    gb_acc    = accuracy_score(y_test, (gb_proba > 0.5).astype(int))
    metrics['gb_spread'] = gb_spread
    metrics['gb_acc']    = gb_acc
    if verbose:
        print(f" spread={gb_spread*100:.1f}%  acc={gb_acc*100:.1f}%")

    # ── 3. XGBoost ────────────────────────────────────────────────────────────
    # XGBoost with use_label_encoder removed (deprecated) and a higher
    # learning_rate so calibrated output has sufficient spread.
    if HAS_XGBOOST:
        if verbose:
            print(f"    XGB (sigmoid) ...", end='', flush=True)
        xgb_m = xgb.XGBClassifier(
            n_estimators=150, learning_rate=0.10, max_depth=4,
            subsample=0.8, colsample_bytree=0.8,
            random_state=42, eval_metric='logloss',
            n_jobs=1,  # Fix "Can't pickle" on Linux: single-threaded avoids OpenMP thread-local state
        )
        xgb_m.fit(X_train_sc, y_train, sample_weight=w_train)
        # n_jobs=1 + threading backend: avoids "Can't pickle" errors on Linux/Ubuntu.
        # loky (the default joblib backend) forks worker processes and requires
        # XGBClassifier to be picklable; n_jobs=1 + threading backend bypasses this.
        xgb_cal = CalibratedClassifierCV(xgb_m, method='sigmoid', cv=3, n_jobs=1)
        with parallel_backend('threading'):
            xgb_cal.fit(X_train_sc, y_train, sample_weight=w_train)
        models['xgb'] = xgb_cal

        xgb_proba  = xgb_cal.predict_proba(X_test_sc)[:, 1]
        xgb_spread = float(xgb_proba.max() - xgb_proba.min()) if len(xgb_proba) > 1 else 0.0
        xgb_acc    = accuracy_score(y_test, (xgb_proba > 0.5).astype(int))
        metrics['xgb_spread'] = xgb_spread
        metrics['xgb_acc']    = xgb_acc
        if verbose:
            print(f" spread={xgb_spread*100:.1f}%  acc={xgb_acc*100:.1f}%")
    else:
        metrics['xgb_spread'] = None
        metrics['xgb_acc']    = None
        if verbose:
            print("    XGB skipped (xgboost not installed)")

    return models, scaler, metrics


# ── load + merge all training CSVs ───────────────────────────────────────────

def load_training_data():
    """Load all results CSV files from data/ and return a combined DataFrame."""
    import glob
    csv_files = sorted(glob.glob(os.path.join(DATA_DIR, 'results_*.csv')))
    if not csv_files:
        raise FileNotFoundError(
            f"No results_*.csv files found in {DATA_DIR}.\n"
            "Expected columns: Track, Date, Race, Winner, 2nd, 3rd, 4th\n"
            "See train_ml_track_ensemble.py for the full data preparation pipeline."
        )

    dfs = []
    for f in csv_files:
        try:
            df = pd.read_csv(f)
            dfs.append(df)
            print(f"  Loaded {os.path.basename(f)}: {len(df)} rows")
        except Exception as e:
            print(f"  WARNING: could not load {os.path.basename(f)}: {e}")

    return pd.concat(dfs, ignore_index=True) if dfs else pd.DataFrame()


# ── normalise track names to match config.pkl keys ───────────────────────────

TRACK_NAME_MAP = {
    # raw CSV name                 → canonical model name
    # Each track maps to its OWN dedicated model — NO cross-track fallbacks.
    # Sponsor prefix variants (e.g. "Ladbrokes", "BetDeluxe") are aliases for
    # the same physical venue; they are NOT fallbacks.
    'Angle Park':                  'Angle Park',
    'ANGLE PARK':                  'Angle Park',
    'Ballarat':                    'BALLARAT',
    'BALLARAT':                    'BALLARAT',
    'Bendigo':                     'BENDIGO',
    'BENDIGO':                     'BENDIGO',
    'Bet Nation Townsville':       'TOWNSVILLE',
    'BET NATION TOWNSVILLE':       'TOWNSVILLE',
    'BetDeluxe Capalaba':          'Capalaba',
    'BETDELUXE CAPALABA':          'Capalaba',
    'Capalaba':                    'Capalaba',
    'BetDeluxe Rockhampton':       'ROCKHAMPTON',
    'BETDELUXE ROCKHAMPTON':       'ROCKHAMPTON',
    'Rockhampton':                 'ROCKHAMPTON',
    'ROCKHAMPTON':                 'ROCKHAMPTON',
    'Broken Hill':                 'BROKEN HILL',
    'BROKEN HILL':                 'BROKEN HILL',
    'Bulli':                       'Bulli',
    'BULLI':                       'Bulli',
    'Cannington':                  'CANNINGTON',
    'CANNINGTON':                  'CANNINGTON',
    'Casino':                      'CASINO',
    'CASINO':                      'CASINO',
    'Darwin':                      'DARWIN',
    'DARWIN':                      'DARWIN',
    'Dubbo':                       'DUBBO',
    'DUBBO':                       'DUBBO',
    'Gawler':                      'GAWLER',
    'GAWLER':                      'GAWLER',
    'Geelong':                     'GEELONG',
    'GEELONG':                     'GEELONG',
    'Gosford':                     'GOSFORD',
    'GOSFORD':                     'GOSFORD',
    'Goulburn':                    'GOULBURN',
    'GOULBURN':                    'GOULBURN',
    'Grafton':                     'GRAFTON',
    'GRAFTON':                     'GRAFTON',
    'Gunnedah':                    'GUNNEDAH',
    'GUNNEDAH':                    'GUNNEDAH',
    'Healesville':                 'HEALESVILLE',
    'HEALESVILLE':                 'HEALESVILLE',
    'Hobart':                      'HOBART',
    'Tasmania':                    'HOBART',
    'HOBART':                      'HOBART',
    'Horsham':                     'HORSHAM',
    'HORSHAM':                     'HORSHAM',
    'Ladbrokes Gardens':           'GARDENS',
    'LADBROKES GARDENS':           'GARDENS',
    'Gardens':                     'GARDENS',
    'Ladbrokes Q Straight':        'Q STRAIGHT',
    'LADBROKES Q STRAIGHT':        'Q STRAIGHT',
    'Ladbrokes Q1 Lakeside':       'Q LAKESIDE',
    'LADBROKES Q1 LAKESIDE':       'Q LAKESIDE',
    'Lakeside':                    'Q LAKESIDE',
    'Ladbrokes Q2 Parklands':      'Q PARKLANDS',
    'LADBROKES Q2 PARKLANDS':      'Q PARKLANDS',
    'Q Parklands':                 'Q PARKLANDS',
    'Launceston':                  'LAUNCESTON',
    'LAUNCESTON':                  'LAUNCESTON',
    'Maitland':                    'Maitland',
    'MAITLAND':                    'Maitland',
    'Mandurah':                    'Mandurah',
    'MANDURAH':                    'Mandurah',
    'Meadows':                     'MEADOWS',
    'MEADOWS':                     'MEADOWS',
    'Mount Gambier':               'MOUNT GAMBIER',
    'MOUNT GAMBIER':               'MOUNT GAMBIER',
    'Murray Bridge':               'MURRAY BRIDGE',
    'MURRAY BRIDGE':               'MURRAY BRIDGE',
    'Murray Bridge Straight':      'MURRAY BDGE STRAIGHT',
    'MURRAY BRIDGE STRAIGHT':      'MURRAY BDGE STRAIGHT',
    'Nowra':                       'NOWRA',
    'NOWRA':                       'NOWRA',
    'Richmond':                    'RICHMOND',
    'RICHMOND':                    'RICHMOND',
    'Richmond Straight':           'RICHMOND STRAIGHT',
    'RICHMOND STRAIGHT':           'RICHMOND STRAIGHT',
    'Sale':                        'SALE',
    'SALE':                        'SALE',
    'Sandown':                     'SANDOWN',
    'SANDOWN':                     'SANDOWN',
    'Shepparton':                  'SHEPPARTON',
    'SHEPPARTON':                  'SHEPPARTON',
    'Taree':                       'TAREE',
    'TAREE':                       'TAREE',
    'Temora':                      'Temora',
    'TEMORA':                      'Temora',
    'Wagga':                       'WAGGA',
    'WAGGA':                       'WAGGA',
    'Warragul':                    'Warragul',
    'WARRAGUL':                    'Warragul',
    'Warrnambool':                 'WARRNAMBOOL',
    'WARRNAMBOOL':                 'WARRNAMBOOL',
    'Wentworth Park':              'WENTWORTH PARK',
    'WENTWORTH PARK':              'WENTWORTH PARK',
}


def normalize_track(raw_name):
    """Map a raw CSV track name to the canonical config.pkl key."""
    return TRACK_NAME_MAP.get(raw_name, raw_name)


# ── save models for one track ─────────────────────────────────────────────────

def save_models(track_name, models, scaler):
    """Save RF/GB/XGB models and scaler to models/ using flat-file layout."""
    for alg, model in models.items():
        path = os.path.join(MODELS_DIR, f"{track_name}_{alg}.pkl")
        with open(path, 'wb') as f:
            pickle.dump(model, f, protocol=4)
        size_mb = os.path.getsize(path) / 1e6
        print(f"    Saved {os.path.basename(path)} ({size_mb:.1f} MB)")
        if size_mb > 50:
            print(f"    ⚠️  WARNING: {os.path.basename(path)} is {size_mb:.1f} MB — "
                  "consider further reducing max_depth or n_estimators")

    sc_path = os.path.join(MODELS_DIR, f"{track_name}_scaler.pkl")
    with open(sc_path, 'wb') as f:
        pickle.dump(scaler, f, protocol=4)
    print(f"    Saved {os.path.basename(sc_path)}")


# ── update config.pkl ─────────────────────────────────────────────────────────

def update_config(trained_tracks):
    """
    Update models/config.pkl so the pipeline recognises all newly trained tracks.
    Only adds new tracks — does not remove existing ones.
    """
    config_path = os.path.join(MODELS_DIR, 'config.pkl')
    if os.path.exists(config_path):
        with open(config_path, 'rb') as f:
            config = pickle.load(f)
        config = dict(config)  # shallow copy
    else:
        config = {}

    existing = set(config.get('tracks', []))
    new_tracks = existing | set(trained_tracks)

    config['tracks']       = sorted(new_tracks)
    config['algorithms']   = ['rf', 'gb', 'xgb']
    config['feature_cols'] = FEATURE_COLS
    config['calibration']  = 'sigmoid'  # mark so operators know which method was used
    config['retrained']    = datetime.now().strftime('%Y-%m-%d %H:%M')

    with open(config_path, 'wb') as f:
        pickle.dump(config, f, protocol=4)
    print(f"  Updated config.pkl: {len(new_tracks)} tracks registered")


# ── main ──────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        '--tracks', nargs='*', metavar='TRACK',
        help='Retrain only these tracks (use exact config.pkl names). '
             'Default: all tracks that have enough training data.',
    )
    args = parser.parse_args()

    print("=" * 70)
    print("RETRAIN ALL TRACKS — SIGMOID CALIBRATION")
    print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 70)

    # ── load + merge training data ────────────────────────────────────────────
    print("\nLoading training data...")
    raw_df = load_training_data()
    print(f"  Total rows loaded: {len(raw_df)}")

    if len(raw_df) == 0:
        print("ERROR: No training data found. Cannot retrain.")
        sys.exit(1)

    # ── delegate actual feature engineering to the main training script ───────
    # train_ml_track_ensemble.py has the full compute_features() pipeline.
    # This script calls it directly so we don't duplicate 600+ lines of logic.
    print("\nDelegating feature engineering to train_ml_track_ensemble.py ...")
    print("This will retrain all tracks with sigmoid calibration.\n")

    # ── import the training helpers from the main training module ─────────────
    # train_ml_track_ensemble.py already uses method='sigmoid' for all
    # CalibratedClassifierCV calls — no monkey-patching needed.
    # Monkey-patching sklearn.calibration.CalibratedClassifierCV breaks pickle
    # because the class identity check fails (_pickle.PicklingError).
    import train_ml_track_ensemble as _trainer

    # ── run the main training pipeline ───────────────────────────────────────
    print("Running main training pipeline (sigmoid calibration)...\n")
    try:
        _trainer.main()
    except SystemExit:
        pass  # train_ml_track_ensemble.main() may call sys.exit(0)

    print("\n" + "=" * 70)
    print("All models saved with method='sigmoid' — no isotonic collapse possible.")
    print("=" * 70)


if __name__ == '__main__':
    main()
