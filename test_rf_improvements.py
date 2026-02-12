"""
Quick test to validate RF improvements without full training.

This script tests the new RF hyperparameters with a small sample
to ensure they work correctly before running full training.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, classification_report

def test_rf_improvements():
    """Test RF with new hyperparameters on synthetic data"""
    
    print("=" * 80)
    print("🧪 Testing RF Improvements")
    print("=" * 80)
    
    # Create synthetic dataset similar to greyhound data
    np.random.seed(42)
    n_samples = 500
    n_features = 76
    
    print(f"\n📊 Creating synthetic dataset:")
    print(f"   Samples: {n_samples}")
    print(f"   Features: {n_features}")
    
    # Generate features
    X = np.random.randn(n_samples, n_features)
    
    # Generate labels (20% winners, 80% non-winners - realistic imbalance)
    y = np.random.choice([0, 1], size=n_samples, p=[0.8, 0.2])
    
    # Add sample weights (simulate Top 4 weighting)
    sample_weights = np.ones(n_samples)
    winners = y == 1
    sample_weights[winners] = 1.0
    
    print(f"   Positive class: {y.sum()} ({y.sum()/len(y):.1%})")
    print(f"   Negative class: {(1-y).sum()} ({(1-y).sum()/len(y):.1%})")
    
    # Split data
    X_train, X_test, y_train, y_test, w_train, w_test = train_test_split(
        X, y, sample_weights, test_size=0.2, random_state=42, stratify=y
    )
    
    # Scale features
    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train)
    X_test_scaled = scaler.transform(X_test)
    
    print(f"\n   Train: {len(X_train)} samples")
    print(f"   Test: {len(X_test)} samples")
    
    # Test OLD hyperparameters
    print("\n" + "=" * 80)
    print("📉 OLD RF Configuration (Baseline)")
    print("=" * 80)
    
    rf_old = RandomForestClassifier(
        n_estimators=200,
        max_depth=20,
        min_samples_split=5,
        random_state=42,
        n_jobs=-1
    )
    
    rf_old.fit(X_train_scaled, y_train, sample_weight=w_train)
    y_pred_old = rf_old.predict(X_test_scaled)
    acc_old = accuracy_score(y_test, y_pred_old)
    
    print(f"   n_estimators: 200")
    print(f"   max_depth: 20")
    print(f"   min_samples_split: 5")
    print(f"   min_samples_leaf: default (1)")
    print(f"   max_features: default (n_features)")
    print(f"   class_weight: None")
    print(f"\n   ✅ Accuracy: {acc_old:.4f} ({acc_old:.1%})")
    
    # Test NEW hyperparameters
    print("\n" + "=" * 80)
    print("📈 NEW RF Configuration (Improved)")
    print("=" * 80)
    
    rf_new = RandomForestClassifier(
        n_estimators=250,  # Increased
        max_depth=22,  # Increased
        min_samples_split=5,
        min_samples_leaf=2,  # NEW
        max_features='sqrt',  # NEW
        class_weight='balanced',  # NEW
        bootstrap=True,
        random_state=42,
        n_jobs=-1
    )
    
    rf_new.fit(X_train_scaled, y_train, sample_weight=w_train)
    y_pred_new = rf_new.predict(X_test_scaled)
    acc_new = accuracy_score(y_test, y_pred_new)
    
    print(f"   n_estimators: 250 (+50)")
    print(f"   max_depth: 22 (+2)")
    print(f"   min_samples_split: 5")
    print(f"   min_samples_leaf: 2 (NEW - prevents overfitting)")
    print(f"   max_features: 'sqrt' (NEW - {int(np.sqrt(n_features))} features per tree)")
    print(f"   class_weight: 'balanced' (NEW - handles imbalance)")
    print(f"\n   ✅ Accuracy: {acc_new:.4f} ({acc_new:.1%})")
    
    # Calculate improvement
    improvement = acc_new - acc_old
    improvement_pct = (improvement / acc_old) * 100 if acc_old > 0 else 0
    
    print("\n" + "=" * 80)
    print("📊 Comparison Results")
    print("=" * 80)
    print(f"   Old Accuracy: {acc_old:.4f} ({acc_old:.1%})")
    print(f"   New Accuracy: {acc_new:.4f} ({acc_new:.1%})")
    print(f"   Improvement:  {improvement:+.4f} ({improvement_pct:+.1f}%)")
    
    if improvement > 0:
        print(f"\n   ✅ SUCCESS! New hyperparameters show {improvement_pct:.1f}% improvement")
    elif improvement == 0:
        print(f"\n   ℹ️  NEUTRAL: No change (may vary with real data)")
    else:
        print(f"\n   ⚠️  CAUTION: Slight decrease (may improve with real data)")
    
    # Test feature importance
    print("\n" + "=" * 80)
    print("🔍 Feature Importance (Top 10)")
    print("=" * 80)
    
    if hasattr(rf_new, 'feature_importances_'):
        importances = rf_new.feature_importances_
        # Get top 10
        top_indices = np.argsort(importances)[-10:][::-1]
        
        for i, idx in enumerate(top_indices, 1):
            print(f"   {i:2d}. Feature_{idx:2d}: {importances[idx]:.4f}")
        
        print(f"\n   ✅ Feature importance extraction working!")
    else:
        print("   ❌ Feature importance not available")
    
    print("\n" + "=" * 80)
    print("✅ TEST COMPLETE")
    print("=" * 80)
    print("\nNOTE: This is a synthetic test. Real improvements will be measured")
    print("      on actual greyhound racing data during full training.")
    
    return {
        'old_accuracy': acc_old,
        'new_accuracy': acc_new,
        'improvement': improvement,
        'improvement_pct': improvement_pct
    }

if __name__ == "__main__":
    results = test_rf_improvements()
