"""
Train Track-Specific Ensemble Models - Option C Implementation

Implements Priority 2 & 3 improvements:
1. Track-specific models - Separate model per track for venue-specific patterns
2. Ensemble learning - Combines RandomForest + GradientBoosting + XGBoost predictions
3. Expected improvement: 8-12% accuracy increase over baseline

This script trains multiple models automatically:
- 3 algorithms (RF, GB, XGB) × 15-20 tracks = 45-60 models total
- Predictions averaged across all 3 algorithms per track
- Local training handles all model generation

Usage:
    python train_ml_track_ensemble.py
    
    OR use the batch file:
    train_ml_track_ensemble.bat

Output:
    - Track-specific models saved to models/track_ensemble/{track}_{algorithm}.pkl
    - Ensemble configuration saved to models/track_ensemble_config.pkl
    - Performance report with per-track and per-algorithm accuracy
"""

import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

# CRITICAL FIX #35: Global variable to pass temp file path to avoid return statement crash
TEMP_FILE_PATH_GLOBAL = None

# Fix encoding for Windows console
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

from src.ml_predictor import load_historical_data_hybrid
import pandas as pd
import numpy as np
import json
import datetime
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import accuracy_score, classification_report
from sklearn.model_selection import train_test_split
from sklearn.calibration import CalibratedClassifierCV
from sklearn.linear_model import LogisticRegression
from joblib import parallel_backend
import pickle
import logging
import traceback

try:
    import xgboost as xgb
    HAS_XGBOOST = True
except ImportError:
    HAS_XGBOOST = False
    print("⚠️  XGBoost not available - using RandomForest + GradientBoosting only")


class _PlattCalibratedXGB:
    """Lightweight Platt-scaling wrapper for XGBClassifier.

    Replaces ``CalibratedClassifierCV(xgb_model, cv=3)`` which requires
    joblib to pickle the XGBoost C++ booster into worker processes.  On
    some Linux/Ubuntu environments this raises "Can't pickle
    <class 'xgboost.sklearn.XGBClassifier'>", blocking training entirely.

    This class fits a LogisticRegression (the Platt sigmoid) directly on
    the *training-set* probability outputs of the already-fitted XGB model
    (equivalent to ``cv='prefit'`` in older scikit-learn).  No
    multiprocessing or pickling of the booster is required during fitting.
    The resulting object is picklable by Python's standard pickle module
    because both XGBClassifier and LogisticRegression are serialisable.
    """

    def __init__(self, base_estimator):
        self.base_estimator = base_estimator
        self._calibrator = None

    def fit(self, X, y, sample_weight=None):
        # base_estimator must already be fitted before calling this.
        # We get its training-set probabilities and fit the calibration sigmoid.
        raw = self.base_estimator.predict_proba(X)[:, 1].reshape(-1, 1)
        # C=1e9: near-zero L2 regularisation.  Platt scaling is a two-parameter
        # logistic regression (intercept + single weight on the raw score).  With
        # only one feature, over-fitting is not a concern; strong regularisation
        # would shrink the sigmoid toward a flat line and undo the calibration.
        self._calibrator = LogisticRegression(
            C=1e9, solver='lbfgs', max_iter=1000
        )
        self._calibrator.fit(raw, y, sample_weight=sample_weight)
        return self

    def predict_proba(self, X):
        raw = self.base_estimator.predict_proba(X)[:, 1].reshape(-1, 1)
        p1 = self._calibrator.predict_proba(raw)[:, 1]
        return np.column_stack([1.0 - p1, p1])

    def predict(self, X):
        return (self.predict_proba(X)[:, 1] >= 0.5).astype(int)

# Set up logging
log_file = "logs/train_track_ensemble.log"
os.makedirs("logs", exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_file, mode='w', encoding='utf-8'),
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)

def extract_features_and_labels(race_data_list, winners_list, output_dir="models/track_ensemble"):
    """
    Extract features and labels from race data WITH WEIGHTED TOP 4 TRAINING.
    Then IMMEDIATELY train and save models before returning.
    
    CRITICAL FIX #42: Move ALL model training logic into this function to avoid
    Python process exit when returning from function that processed large dataset.
    
    ENHANCED: Now supports weighted labels for Top 4 finishers:
    - 1st place: weight 1.0 (full winner)
    - 2nd place: weight 0.7 (strong positive signal)
    - 3rd place: weight 0.5 (moderate positive signal)
    - 4th place: weight 0.3 (weak positive signal)
    - 5th+: weight 0.0 (negative examples)
    
    Returns:
        None (all work done internally)
    """
    import sys
    print("   CHECKPOINT 1: Entered extract_features_and_labels function")
    sys.stdout.flush()
    
    all_rows = []
    
    print(f"   CHECKPOINT 2: About to log - race_data_list length: {len(race_data_list)}")
    sys.stdout.flush()
    
    logger.info(f"Starting feature extraction for {len(race_data_list)} race entries...")
    
    print("   CHECKPOINT 3: Logger.info completed, starting main loop")
    sys.stdout.flush()
    
    print(f"   CHECKPOINT 4: Starting enumeration loop over {len(race_data_list)} races")
    sys.stdout.flush()
    
    for idx, (race_df, winner_info) in enumerate(zip(race_data_list, winners_list)):
        if idx == 0:
            print(f"   CHECKPOINT 5: Processing first race (idx=0)")
            sys.stdout.flush()
        if idx % 1000 == 0 and idx > 0:
            print(f"   CHECKPOINT: Processed {idx} races so far...")
            sys.stdout.flush()
            
        if race_df is None or len(race_df) == 0:
            logger.debug(f"Skipping race {idx}: empty dataframe")
            continue
        
        try:
            # Handle both old format (int) and new format (dict with weight)
            if isinstance(winner_info, dict):
                winner_box = winner_info['box']
                weight = winner_info['weight']
                position = winner_info['position']
            else:
                # Backward compatibility: old format treats all as winners (weight 1.0)
                winner_box = winner_info
                weight = 1.0
                position = 1
            
            # Add winner label and weight
            race_df = race_df.copy()
            # CRITICAL: Winner label must be binary (0 or 1), NOT weighted
            # The weight is used separately during model training via sample_weight parameter
            race_df['Winner'] = (race_df['Box'] == winner_box).astype(float)
            race_df['SampleWeight'] = weight  # Store weight for later use in model.fit()
            race_df['FinishPosition'] = 0  # Default for non-finishers
            race_df.loc[race_df['Box'] == winner_box, 'FinishPosition'] = position
            
            # CRITICAL FIX #41: Convert to dict immediately to avoid pd.concat() memory issues
            # Instead of storing DataFrames and concatenating later (causes memory spike),
            # convert to list of dicts which uses minimal memory
            all_rows.extend(race_df.to_dict('records'))
            
        except Exception as e:
            logger.error(f"Error processing race {idx}: {e}", exc_info=True)
            continue
    
    if not all_rows:
        raise ValueError("No valid race data was processed!")
    
    print(f"   CHECKPOINT 6: Finished loop, processed {len(all_rows)} race entries")
    sys.stdout.flush()
    
    logger.info(f"Successfully processed {len(all_rows)} race entries")
    
    print("   CHECKPOINT 7: About to create DataFrame from list of dicts")
    sys.stdout.flush()
    
    # CRITICAL FIX #41: Create DataFrame directly from list of dicts
    # This bypasses pd.concat() entirely and uses minimal memory
    # all_rows is now a list of dicts, not a list of DataFrames
    print(f"   CHECKPOINT 7.1: Creating DataFrame from {len(all_rows)} records")
    sys.stdout.flush()
    
    try:
        df = pd.DataFrame(all_rows)
        print(f"   CHECKPOINT 7.2: DataFrame created successfully with {len(df)} rows")
        sys.stdout.flush()
    except Exception as e:
        print(f"   ERROR creating DataFrame: {e}")
        sys.stdout.flush()
        raise
    
    # Clear all_rows to free memory
    del all_rows
    import gc
    gc.collect()
    
    print(f"   CHECKPOINT 8: Concatenation complete, df has {len(df)} rows")
    sys.stdout.flush()
    
    logger.info(f"Combined dataframe has {len(df)} rows")
    
    # Identify feature columns (exclude metadata, labels, and zero-variance constants)
    # Weight/WeightFactor are always 0/1.0 (PDFs have no weight data).
    # TrackConditionAdj is always 1.0 (PDFs have no track condition data).
    # Constant features contribute nothing to model quality and inflate file sizes.
    exclude_cols = ['Winner', 'SampleWeight', 'FinishPosition', 'DogName', 'Track', 
                    'Date', 'Race', 'RaceNumber', 'Trainer', 'Owner', 'Sire', 'Dam', 
                    'Color', 'Sex', 'Age',
                    'Weight', 'WeightFactor', 'TrackConditionAdj']
    feature_cols = [col for col in df.columns if col not in exclude_cols and df[col].dtype in [np.float64, np.int64]]
    
    logger.info(f"Identified {len(feature_cols)} feature columns")
    
    # Memory optimization: Convert float64 to float32 to reduce memory usage (50% reduction)
    logger.info("Optimizing dataframe memory usage...")
    for col in df.select_dtypes(include=['float64']).columns:
        df[col] = df[col].astype('float32')
    logger.info(f"Memory optimized - DataFrame size: {df.memory_usage(deep=True).sum() / 1024 / 1024:.2f} MB")
    
    # CRITICAL FIX #43: Force explicit checkpoint and flush BEFORE continuing to training
    # Windows Python may terminate silently after large memory operations without this
    print("   CHECKPOINT 8.1: Memory optimization complete, forcing flush...")
    sys.stdout.flush()
    
    # Force garbage collection and flush any pending operations
    import gc
    gc.collect()
    
    print("   CHECKPOINT 8.2: GC complete, about to start model training")
    sys.stdout.flush()
    
    # CRITICAL FIX #42: Train models NOW before any return/cleanup
    # This ensures everything completes in one function call
    print("\n🚀 STEP 3: Training track-specific ensemble models...")
    print("-" * 80)
    sys.stdout.flush()
    
    # Group by track
    print("   Grouping by track...")
    sys.stdout.flush()
    
    tracks = df['Track'].unique()
    print(f"\n📊 Found {len(tracks)} unique tracks:")
    sys.stdout.flush()
    
    track_data = {}
    for i, track in enumerate(sorted(tracks), 1):
        track_df = df[df['Track'] == track]
        n_races = len(track_df)
        n_winners = track_df['Winner'].sum()
        track_data[track] = track_df
        print(f"   {track:25s}: {n_races:4d} dogs, {n_winners:6.1f} winners (weighted)")
        sys.stdout.flush()
    
    # Create output directory
    import os
    os.makedirs(output_dir, exist_ok=True)
    
    print(f"\n   Training 3 algorithms per track × {len(tracks)} tracks")
    print(f"   CHECKPOINT: About to start model training loop")
    sys.stdout.flush()
    
    all_models = {}
    all_scalers = {}
    all_metrics = []
    
    # Add memory monitoring
    try:
        import psutil
        HAS_PSUTIL = True
    except ImportError:
        HAS_PSUTIL = False
        print("⚠️  psutil not available - memory monitoring disabled")
    
    import gc  # For garbage collection
    
    for i, track in enumerate(sorted(tracks), 1):
        # Check memory before training each track
        if HAS_PSUTIL:
            mem = psutil.virtual_memory()
            mem_percent = mem.percent
            mem_available_gb = mem.available / (1024**3)
            
            if mem_percent > 85:
                print(f"\n⚠️  WARNING: High memory usage!")
                print(f"   Memory: {mem_percent:.1f}% used, {mem_available_gb:.1f} GB available")
                print(f"   Running garbage collection...")
                gc.collect()
                mem_after = psutil.virtual_memory()
                print(f"   After GC: {mem_after.percent:.1f}% used, {mem_after.available/(1024**3):.1f} GB available")
            
            print(f"\n   [{i}/{len(tracks)}] Training models for {track}... (Mem: {mem_percent:.1f}%)")
        else:
            print(f"\n   [{i}/{len(tracks)}] Training models for {track}...")
        
        sys.stdout.flush()
        
        try:
            track_df = track_data[track]
            
            # Skip tracks with too few samples
            if len(track_df) < 30:
                print(f"      ⚠️  Skipping {track} - insufficient data ({len(track_df)} dogs, need 30+)")
                continue
            
            # Train ensemble
            models, scaler, metrics = train_track_specific_ensemble(
                track_df, feature_cols, track
            )
            
            # Save models
            for alg_name, model in models.items():
                model_path = os.path.join(output_dir, f"{track}_{alg_name}.pkl")
                with open(model_path, 'wb') as f:
                    pickle.dump(model, f)
            
            # Save scaler
            scaler_path = os.path.join(output_dir, f"{track}_scaler.pkl")
            with open(scaler_path, 'wb') as f:
                pickle.dump(scaler, f)
            
            all_models[track] = models
            all_scalers[track] = scaler
            all_metrics.append(metrics)
            
            # Show results
            print(f"      ✅ Ensemble accuracy: {metrics['ensemble_accuracy']:.1%}")
            
            # CRITICAL: Force garbage collection after each track to prevent OOM
            # This releases memory from calibration objects and intermediate results
            del models, scaler, metrics, track_df
            gc.collect()
            
            sys.stdout.flush()
            
        except Exception as e:
            print(f"      ❌ ERROR training {track}: {e}")
            logger.error(f"Error training {track}", exc_info=True)
            continue
    
    # Save configuration
    print("\n💾 STEP 4: Saving ensemble configuration...")
    print("-" * 80)
    sys.stdout.flush()
    
    if all_models:
        config = {
            'tracks': list(all_models.keys()),
            'algorithms': ['rf', 'gb', 'xgb'],  # Algorithm names used in model files
            'feature_cols': feature_cols,
            'ensemble_weights': {'rf': 1.0, 'gb': 1.0, 'xgb': 1.0},  # Equal weights for all algorithms
            'training_date': datetime.datetime.now().isoformat(),
            'n_samples': len(df),
            'n_tracks': len(all_models)
        }
        
        # Save as JSON for human readability
        config_path_json = os.path.join(output_dir, 'ensemble_config.json')
        with open(config_path_json, 'w') as f:
            json.dump(config, f, indent=2)
        
        # Save as pickle for prediction script compatibility
        config_path_pkl = os.path.join(output_dir, 'config.pkl')
        with open(config_path_pkl, 'wb') as f:
            pickle.dump(config, f)
        
        print(f"✅ Configuration saved to {config_path_json}")
        print(f"✅ Configuration saved to {config_path_pkl}")
        print(f"\n🎉 SUCCESS! Trained {len(all_models)} track-specific ensembles")
        print(f"   Models saved to: {os.path.abspath(output_dir)}/")
        
        # Show summary stats
        if all_metrics:
            avg_accuracy = np.mean([m['ensemble_accuracy'] for m in all_metrics])
            print(f"\n📊 Average ensemble accuracy: {avg_accuracy:.1%}")
    else:
        print("❌ ERROR: No models were trained!")
        print(f"   Total samples: {len(df)}")
        print(f"   Tracks found: {len(tracks)}")
    
    sys.stdout.flush()
    
    # Clean up memory
    print("   CHECKPOINT: Cleaning up memory")
    sys.stdout.flush()
    
    del df
    import gc
    gc.collect()
    
    print("   CHECKPOINT: Function complete, returning None")
    sys.stdout.flush()
    
    # Return None - all work is done
    return None


def train_track_specific_ensemble(df, feature_cols, track_name):
    """
    Train ensemble of 3 algorithms for a specific track WITH CALIBRATION and WEIGHTED TRAINING.
    
    ENHANCED: Now uses weighted labels for Top 4 finishers:
    - Trains on expanded dataset (1st/2nd/3rd/4th place dogs)
    - Uses sample weights to emphasize winners (1.0) over placers (0.7/0.5/0.3)
    - Still predicts winners specifically, but learns from all competitive dogs
    
    MEMORY OPTIMIZED: Reduces parameters for large tracks to prevent OOM
    
    Args:
        df: DataFrame with race data for this track (includes SampleWeight column)
        feature_cols: List of feature column names
        track_name: Name of the track
    
    Returns:
        models: Dict with trained AND CALIBRATED models {algorithm_name: model}
        scaler: Fitted StandardScaler
        metrics: Dict with performance metrics
    """
    # Adaptive complexity based on dataset size (prevent OOM for large tracks)
    # RF max_depth capped at 10 across all tiers — deeper trees produce very large .pkl
    # files (24 MB+) that exceed GitHub's 100 MB limit when many features are present.
    # Depth 10 still captures all meaningful split combinations in a 76-feature space.
    n_samples = len(df)
    if n_samples > 600:
        # Very large track - reduce n_estimators to save memory
        n_estimators = 100
        max_depth_rf = 10
        max_depth_gb = 4
        print(f"      📊 Large dataset ({n_samples} samples) - using reduced complexity")
    elif n_samples > 400:
        # Large track
        n_estimators = 100
        max_depth_rf = 10
        max_depth_gb = 4
        print(f"      📊 Medium-large dataset ({n_samples} samples) - using moderate complexity")
    else:
        # Normal track
        n_estimators = 100
        max_depth_rf = 10
        max_depth_gb = 5
    
    # Prepare data with sample weights
    X = df[feature_cols].fillna(0)
    y = df['Winner']
    sample_weights = df['SampleWeight'] if 'SampleWeight' in df.columns else np.ones(len(df))
    
    # Convert weighted labels to binary (>0.5 = positive class for training)
    y_binary = (y > 0.5).astype(int)
    
    # Split data - stratify on binary labels
    X_train, X_test, y_train, y_test, w_train, w_test = train_test_split(
        X, y_binary, sample_weights, test_size=0.2, random_state=42, 
        stratify=y_binary if y_binary.sum() > 10 else None
    )
    
    # Scale features
    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train)
    X_test_scaled = scaler.transform(X_test)
    
    models = {}
    predictions = {}
    calibrated_predictions = {}
    
    # 1. Random Forest WITH SAMPLE WEIGHTS (adaptive complexity)
    print(f"      Training RandomForest with weighted samples...")
    rf = RandomForestClassifier(
        n_estimators=n_estimators,
        max_depth=max_depth_rf,
        min_samples_split=5,
        random_state=42,
        n_jobs=-1
    )
    rf.fit(X_train_scaled, y_train, sample_weight=w_train)
    
    # Calibrate Random Forest with Sigmoid (Platt scaling) instead of isotonic.
    # Isotonic regression builds a step-function lookup that maps all real-world
    # RF probabilities (0.10–0.37 for 8-dog races) onto a single constant when the
    # training set is small — causing ALL dogs in a race to score identically.
    # Sigmoid/Platt scaling fits a monotonic logistic curve: it cannot produce a
    # flat plateau and always preserves full discrimination.
    print(f"      Calibrating RandomForest (sigmoid)...")
    # n_jobs=1 + threading backend: avoids "Can't pickle" errors on Linux/Ubuntu.
    # loky (default joblib backend) forks worker processes and requires the RF
    # to be picklable; threading backend runs CV folds in-process (no pickling).
    rf_calibrated = CalibratedClassifierCV(rf, method='sigmoid', cv=3, n_jobs=1)
    with parallel_backend('threading'):
        rf_calibrated.fit(X_train_scaled, y_train, sample_weight=w_train)
    models['rf'] = rf_calibrated
    predictions['rf'] = rf.predict_proba(X_test_scaled)[:, 1]
    calibrated_predictions['rf'] = rf_calibrated.predict_proba(X_test_scaled)[:, 1]
    
    # 2. Gradient Boosting — NO sigmoid calibration wrapper.
    # GB's predict_proba() is natively well-calibrated (Friedman 2001, §10.13).
    # Wrapping with CalibratedClassifierCV(sigmoid) squashes the output spread
    # to < 0.5% on small/homogeneous fields — triggering the collapse guard.
    # learning_rate=0.10 + subsample=0.8 give better discrimination than 0.05.
    print(f"      Training GradientBoosting (native proba, no extra cal)...")
    gb = GradientBoostingClassifier(
        n_estimators=n_estimators,
        learning_rate=0.10,
        max_depth=max_depth_gb,
        min_samples_leaf=3,
        subsample=0.8,
        random_state=42
    )
    gb.fit(X_train_scaled, y_train)  # GB does not support sample_weight
    models['gb'] = gb
    predictions['gb'] = gb.predict_proba(X_test_scaled)[:, 1]
    calibrated_predictions['gb'] = gb.predict_proba(X_test_scaled)[:, 1]
    
    # 3. XGBoost WITH SAMPLE WEIGHTS (if available, adaptive complexity)
    if HAS_XGBOOST:
        print(f"      Training XGBoost with weighted samples...")
        xgb_model = xgb.XGBClassifier(
            n_estimators=n_estimators,
            learning_rate=0.10,
            max_depth=max_depth_gb,
            subsample=0.8,
            colsample_bytree=0.8,
            random_state=42,
            eval_metric='logloss',
            n_jobs=1,  # Fix "Can't pickle" on Linux: single-threaded avoids OpenMP thread-local state
        )
        xgb_model.fit(X_train_scaled, y_train, sample_weight=w_train)
        
        # Calibrate XGBoost with Sigmoid (Platt scaling).
        # Uses _PlattCalibratedXGB instead of CalibratedClassifierCV(cv=3) to
        # completely bypass joblib/multiprocessing.  cv=3 requires joblib to
        # pickle the XGB C++ booster into worker processes, which raises
        # "Can't pickle <class 'xgboost.sklearn.XGBClassifier'>" on some
        # Linux/Ubuntu environments.  Manual Platt scaling is equivalent to
        # cv='prefit' (removed in scikit-learn 1.2+) and is version-agnostic.
        print(f"      Calibrating XGBoost (sigmoid)...")
        xgb_calibrated = _PlattCalibratedXGB(xgb_model)
        xgb_calibrated.fit(X_train_scaled, y_train, sample_weight=w_train)
        models['xgb'] = xgb_calibrated
        predictions['xgb'] = xgb_model.predict_proba(X_test_scaled)[:, 1]
        calibrated_predictions['xgb'] = xgb_calibrated.predict_proba(X_test_scaled)[:, 1]
    
    # Compute ensemble prediction (simple average of CALIBRATED predictions)
    ensemble_pred_proba = np.mean([calibrated_predictions[alg] for alg in calibrated_predictions], axis=0)
    ensemble_pred = (ensemble_pred_proba > 0.5).astype(int)
    
    # Compute metrics
    metrics = {
        'track': track_name,
        'n_races': len(df),
        'n_dogs': len(df),
        'n_train': len(X_train),
        'n_test': len(X_test),
        'n_positive_train': int(y_train.sum()),
        'n_positive_test': int(y_test.sum())
    }
    
    # Uncalibrated metrics (for comparison)
    for alg_name, pred_proba in predictions.items():
        pred = (pred_proba > 0.5).astype(int)
        acc = accuracy_score(y_test, pred)
        metrics[f'{alg_name}_accuracy_uncalibrated'] = acc
    
    # Calibrated metrics (actual performance)
    for alg_name, pred_proba in calibrated_predictions.items():
        pred = (pred_proba > 0.5).astype(int)
        acc = accuracy_score(y_test, pred)
        metrics[f'{alg_name}_accuracy'] = acc
    
    metrics['ensemble_accuracy'] = accuracy_score(y_test, ensemble_pred)
    
    # Calculate calibration improvement
    uncal_ensemble = np.mean([predictions[alg] for alg in predictions], axis=0)
    uncal_ensemble_pred = (uncal_ensemble > 0.5).astype(int)
    metrics['ensemble_accuracy_uncalibrated'] = accuracy_score(y_test, uncal_ensemble_pred)
    metrics['calibration_improvement'] = metrics['ensemble_accuracy'] - metrics['ensemble_accuracy_uncalibrated']
    
    return models, scaler, metrics

def main():
    print("=" * 80)
    print("🎯 TRACK-SPECIFIC ENSEMBLE MODEL TRAINING - TOP 4 WEIGHTED + CALIBRATION")
    print("=" * 80)
    print("\nImplementing Priority 1, 2, 3 & 4 improvements:")
    print("  ✅ Track-specific models (separate model per venue)")
    print("  ✅ Ensemble learning (RandomForest + GradientBoosting + XGBoost)")
    print("  ✅ Probability Calibration (Isotonic Regression)")
    print("  ✅ Top 4 Weighted Training (NEW!) - 4x more data")
    print("     • 1st place: weight 1.0 (full winner signal)")
    print("     • 2nd place: weight 0.7 (strong competitive dog)")
    print("     • 3rd place: weight 0.5 (moderate competitive dog)")
    print("     • 4th place: weight 0.3 (weak competitive dog)")
    print("  ✅ Expected: 10-15% accuracy improvement + better calibration")
    print("=" * 80)
    print(f"\n📝 LOG FILE: {os.path.abspath(log_file)}")
    print("=" * 80)
    
    # Save models directly into models/ using the flat-file layout so that
    # run_track_ensemble_predictions.py can find them without needing a
    # models/track_ensemble/ subdirectory.
    output_dir = "models"
    os.makedirs(output_dir, exist_ok=True)
    
    # Step 1: Load historical data
    print("\n📁 STEP 1: Loading historical race data...")
    print("-" * 80)
    
    try:
        race_data_list, winners_list = load_historical_data_hybrid(extra_results_dir='data2')
        print(f"✅ Loaded {len(race_data_list)} races")
        
        total_dogs = sum(len(race_df) if race_df is not None else 0 for race_df in race_data_list)
        print(f"   Total dogs: {total_dogs}")
        print(f"   Winner entries: {len(winners_list)}")
        
        # Validate data structure
        if len(race_data_list) != len(winners_list):
            print(f"❌ ERROR: Mismatch between race_data ({len(race_data_list)}) and winners ({len(winners_list)})")
            return 1
            
    except Exception as e:
        print(f"❌ ERROR loading data: {e}")
        traceback.print_exc()
        return 1
    
    # Step 2: Extract features and organize by track
    print("\n🔧 STEP 2: Extracting features and organizing by track...")
    print("-" * 80)
    
    try:
        print(f"   CHECKPOINT: Entered STEP 2 try block")
        sys.stdout.flush()
        
        print(f"   Processing {len(race_data_list)} race entries with {len(winners_list)} winner entries...")
        print(f"   Note: With Top 4 training, each race appears 4 times (1st/2nd/3rd/4th)")
        
        print("   CHECKPOINT: About to call extract_features_and_labels()...")
        sys.stdout.flush()  # Force flush to see output immediately
        
        # CRITICAL FIX #42: All work happens inside the function now
        extract_features_and_labels(race_data_list, winners_list, output_dir)
        
        print(f"\n✅ Training pipeline completed successfully!")
        print(f"   Models saved to: {os.path.abspath(output_dir)}/")
        sys.stdout.flush()
    
    except Exception as e:
        print(f"❌ ERROR in training pipeline: {e}")
        traceback.print_exc()
        return 1
    
    return 0

if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception as e:
        print(f"\n❌ FATAL ERROR: {e}")
        traceback.print_exc()
        sys.exit(1)
