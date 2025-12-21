"""
ML Optimization Phases 2-4
Enhanced training with hyperparameter optimization, time-series validation, and feature importance analysis.
"""

import numpy as np
import pandas as pd
from sklearn.model_selection import GridSearchCV, TimeSeriesSplit
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import accuracy_score, classification_report
import logging

logger = logging.getLogger(__name__)

try:
    import xgboost as xgb
    HAS_XGBOOST = True
except ImportError:
    HAS_XGBOOST = False


class MLOptimizationPhases:
    """
    Implements Phases 2-4 of ML optimization:
    - Phase 2: Hyperparameter optimization with grid search
    - Phase 3: Time-series validation strategy
    - Phase 4: Feature importance analysis
    """
    
    def __init__(self):
        self.best_params = {}
        self.feature_importances = {}
        self.scaler = StandardScaler()
    
    # ===== PHASE 2: HYPERPARAMETER OPTIMIZATION =====
    
    def optimize_hyperparameters_rf(self, X_train, y_train, cv_splits=3):
        """
        Phase 2: Optimize Random Forest hyperparameters using grid search.
        
        Args:
            X_train: Training features
            y_train: Training labels
            cv_splits: Number of cross-validation splits
        
        Returns:
            dict: Best hyperparameters found
        """
        logger.info("🔧 Phase 2: Optimizing RandomForest hyperparameters...")
        
        param_grid = {
            'n_estimators': [100, 200, 300],
            'max_depth': [10, 20, 30, None],
            'min_samples_split': [2, 5, 10],
            'min_samples_leaf': [1, 2, 4],
            'max_features': ['sqrt', 'log2']
        }
        
        rf = RandomForestClassifier(random_state=42, n_jobs=-1)
        
        grid_search = GridSearchCV(
            rf, param_grid,
            cv=min(cv_splits, 3),
            scoring='accuracy',
            n_jobs=-1,
            verbose=1
        )
        
        grid_search.fit(X_train, y_train)
        
        self.best_params['random_forest'] = grid_search.best_params_
        logger.info(f"✅ Best RF params: {grid_search.best_params_}")
        logger.info(f"   Best CV score: {grid_search.best_score_:.4f}")
        
        return grid_search.best_estimator_
    
    def optimize_hyperparameters_gb(self, X_train, y_train, cv_splits=3):
        """
        Phase 2: Optimize Gradient Boosting hyperparameters using grid search.
        
        Args:
            X_train: Training features
            y_train: Training labels
            cv_splits: Number of cross-validation splits
        
        Returns:
            Fitted model with best parameters
        """
        logger.info("🔧 Phase 2: Optimizing GradientBoosting hyperparameters...")
        
        param_grid = {
            'n_estimators': [100, 200, 300],
            'learning_rate': [0.01, 0.05, 0.1],
            'max_depth': [3, 5, 7],
            'min_samples_split': [2, 5],
            'subsample': [0.8, 1.0]
        }
        
        gb = GradientBoostingClassifier(random_state=42)
        
        grid_search = GridSearchCV(
            gb, param_grid,
            cv=min(cv_splits, 3),
            scoring='accuracy',
            n_jobs=-1,
            verbose=1
        )
        
        grid_search.fit(X_train, y_train)
        
        self.best_params['gradient_boosting'] = grid_search.best_params_
        logger.info(f"✅ Best GB params: {grid_search.best_params_}")
        logger.info(f"   Best CV score: {grid_search.best_score_:.4f}")
        
        return grid_search.best_estimator_
    
    def optimize_hyperparameters_xgb(self, X_train, y_train, cv_splits=3):
        """
        Phase 2: Optimize XGBoost hyperparameters using grid search.
        
        Args:
            X_train: Training features
            y_train: Training labels
            cv_splits: Number of cross-validation splits
        
        Returns:
            Fitted XGBoost model with best parameters
        """
        if not HAS_XGBOOST:
            logger.warning("⚠️  XGBoost not available, skipping optimization")
            return None
        
        logger.info("🔧 Phase 2: Optimizing XGBoost hyperparameters...")
        
        param_grid = {
            'n_estimators': [100, 200, 300],
            'learning_rate': [0.01, 0.05, 0.1],
            'max_depth': [3, 5, 7],
            'min_child_weight': [1, 3, 5],
            'subsample': [0.8, 1.0],
            'colsample_bytree': [0.8, 1.0]
        }
        
        xgb_model = xgb.XGBClassifier(
            random_state=42,
            n_jobs=-1,
            use_label_encoder=False,
            eval_metric='logloss'
        )
        
        grid_search = GridSearchCV(
            xgb_model, param_grid,
            cv=min(cv_splits, 3),
            scoring='accuracy',
            n_jobs=-1,
            verbose=1
        )
        
        grid_search.fit(X_train, y_train)
        
        self.best_params['xgboost'] = grid_search.best_params_
        logger.info(f"✅ Best XGB params: {grid_search.best_params_}")
        logger.info(f"   Best CV score: {grid_search.best_score_:.4f}")
        
        return grid_search.best_estimator_
    
    def apply_feature_scaling(self, X_train, X_val=None, X_test=None):
        """
        Phase 2: Apply feature scaling/normalization.
        
        Args:
            X_train: Training features
            X_val: Validation features (optional)
            X_test: Test features (optional)
        
        Returns:
            Scaled features (train, val, test)
        """
        logger.info("📊 Phase 2: Applying feature scaling...")
        
        X_train_scaled = self.scaler.fit_transform(X_train)
        
        results = [X_train_scaled]
        
        if X_val is not None:
            X_val_scaled = self.scaler.transform(X_val)
            results.append(X_val_scaled)
        
        if X_test is not None:
            X_test_scaled = self.scaler.transform(X_test)
            results.append(X_test_scaled)
        
        logger.info("✅ Feature scaling complete")
        
        return tuple(results) if len(results) > 1 else results[0]
    
    # ===== PHASE 3: TIME-SERIES VALIDATION =====
    
    def implement_time_series_split(self, df, train_ratio=0.6, val_ratio=0.2):
        """
        Phase 3: Implement time-series validation strategy.
        
        Ensures training on older races, testing on newer races.
        Prevents data leakage and provides realistic accuracy estimates.
        
        Args:
            df: DataFrame with race data including 'Date' column
            train_ratio: Proportion for training (default 0.6)
            val_ratio: Proportion for validation (default 0.2)
        
        Returns:
            train_df, val_df, test_df: Split datasets
        """
        logger.info("📅 Phase 3: Implementing time-series validation...")
        
        # Sort by date
        df_sorted = df.sort_values('Date').reset_index(drop=True)
        
        # Calculate split points
        n = len(df_sorted)
        train_end = int(n * train_ratio)
        val_end = int(n * (train_ratio + val_ratio))
        
        # Split chronologically
        train_df = df_sorted.iloc[:train_end].copy()
        val_df = df_sorted.iloc[train_end:val_end].copy()
        test_df = df_sorted.iloc[val_end:].copy()
        
        logger.info(f"✅ Time-series split complete:")
        logger.info(f"   Train: {len(train_df)} races ({train_df['Date'].min()} to {train_df['Date'].max()})")
        logger.info(f"   Val:   {len(val_df)} races ({val_df['Date'].min()} to {val_df['Date'].max()})")
        logger.info(f"   Test:  {len(test_df)} races ({test_df['Date'].min()} to {test_df['Date'].max()})")
        
        return train_df, val_df, test_df
    
    def cross_validate_time_series(self, X, y, model, n_splits=5):
        """
        Phase 3: Perform time-series cross-validation.
        
        Args:
            X: Features (numpy array or pandas DataFrame)
            y: Labels (numpy array or pandas Series)
            model: ML model to validate
            n_splits: Number of time-series splits
        
        Returns:
            dict: Cross-validation scores
        """
        logger.info(f"📊 Phase 3: Time-series cross-validation ({n_splits} splits)...")
        
        # Convert to numpy if needed for indexing compatibility
        X_array = X.values if hasattr(X, 'values') else X
        y_array = y.values if hasattr(y, 'values') else y
        
        tscv = TimeSeriesSplit(n_splits=n_splits)
        scores = []
        
        for fold, (train_idx, test_idx) in enumerate(tscv.split(X_array), 1):
            X_train_fold, X_test_fold = X_array[train_idx], X_array[test_idx]
            y_train_fold, y_test_fold = y_array[train_idx], y_array[test_idx]
            
            model.fit(X_train_fold, y_train_fold)
            score = model.score(X_test_fold, y_test_fold)
            scores.append(score)
            
            logger.info(f"   Fold {fold}: {score:.4f}")
        
        results = {
            'scores': scores,
            'mean': np.mean(scores),
            'std': np.std(scores)
        }
        
        logger.info(f"✅ CV Mean: {results['mean']:.4f} ± {results['std']:.4f}")
        
        return results
    
    # ===== PHASE 4: FEATURE IMPORTANCE ANALYSIS =====
    
    def analyze_feature_importance(self, model, feature_names, top_n=20):
        """
        Phase 4: Analyze and report feature importance.
        
        Args:
            model: Trained model with feature_importances_ attribute
            feature_names: List of feature names
            top_n: Number of top features to display
        
        Returns:
            DataFrame with feature importances
        """
        logger.info("🔍 Phase 4: Analyzing feature importance...")
        
        if not hasattr(model, 'feature_importances_'):
            logger.warning("⚠️  Model does not have feature_importances_ attribute")
            return None
        
        importances = model.feature_importances_
        indices = np.argsort(importances)[::-1]
        
        # Create DataFrame
        importance_df = pd.DataFrame({
            'Feature': [feature_names[i] for i in indices],
            'Importance': importances[indices],
            'Rank': range(1, len(indices) + 1)
        })
        
        self.feature_importances = importance_df
        
        logger.info(f"✅ Feature importance analysis complete")
        logger.info(f"\n📊 Top {top_n} Most Important Features:")
        logger.info("=" * 60)
        
        for idx, row in importance_df.head(top_n).iterrows():
            logger.info(f"   {row['Rank']:2d}. {row['Feature']:40s} {row['Importance']:.4f}")
        
        return importance_df
    
    def identify_redundant_features(self, importance_df, threshold=0.001):
        """
        Phase 4: Identify potentially redundant features.
        
        Args:
            importance_df: DataFrame from analyze_feature_importance
            threshold: Minimum importance threshold
        
        Returns:
            list: Names of potentially redundant features
        """
        logger.info(f"🔍 Phase 4: Identifying redundant features (threshold={threshold})...")
        
        redundant = importance_df[importance_df['Importance'] < threshold]['Feature'].tolist()
        
        logger.info(f"✅ Found {len(redundant)} potentially redundant features")
        if redundant:
            logger.info("   Consider removing these features:")
            for feat in redundant[:10]:  # Show first 10
                logger.info(f"     - {feat}")
            if len(redundant) > 10:
                logger.info(f"     ... and {len(redundant) - 10} more")
        
        return redundant
    
    def get_optimization_summary(self):
        """
        Get summary of all optimization phases.
        
        Returns:
            dict: Summary of optimization results
        """
        summary = {
            'best_hyperparameters': self.best_params,
            'feature_importances': self.feature_importances.head(20).to_dict() if isinstance(self.feature_importances, pd.DataFrame) else None,
            'scaling_applied': self.scaler is not None
        }
        
        return summary
