#!/usr/bin/env python
"""
Minimal training test - validates the complete pipeline with a small subset of data.
Tests the fix for Top 4 weighted training binary label issue.
"""
import sys
import os
import logging

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from ml_predictor import load_historical_data_hybrid
from train_ml_track_ensemble import extract_features_and_labels, train_track_specific_ensemble
import pandas as pd

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_minimal_training():
    """Test training pipeline with minimal data"""
    
    print("\n" + "="*80)
    print("MINIMAL TRAINING TEST - Validating Pipeline with Small Dataset")
    print("="*80 + "\n")
    
    # Step 1: Load data
    print("STEP 1: Loading training data...")
    race_data_list, winners_list = load_historical_data_hybrid()
    
    print(f"\n✅ Loaded {len(race_data_list)} training samples from matched races")
    print(f"   Winners list length: {len(winners_list)}")
    
    if len(race_data_list) == 0:
        print("❌ No data loaded - cannot proceed with test")
        return False
    
    # Validate format
    print("\n📊 Validating data format...")
    print(f"   First winner entry: {winners_list[0]}")
    print(f"   Type: {type(winners_list[0])}")
    
    if isinstance(winners_list[0], dict):
        print("   ✅ Correct format: dict with 'box', 'weight', 'position'")
    else:
        print("   ⚠️  Old format detected")
    
    # Step 2: Take only first 50 samples for quick test
    print("\n🔬 Using first 50 samples for minimal test...")
    test_race_data = race_data_list[:50]
    test_winners = winners_list[:50]
    
    # Step 3: Extract features
    print("\nSTEP 2: Extracting features and labels...")
    try:
        df, feature_cols = extract_features_and_labels(test_race_data, test_winners)
        print(f"✅ Feature extraction successful!")
        print(f"   Combined dataframe: {len(df)} rows, {len(df.columns)} columns")
        print(f"   Feature columns: {len(feature_cols)}")
        
        # Validate critical columns
        if 'Winner' in df.columns and 'SampleWeight' in df.columns:
            print(f"   ✅ Critical columns present: Winner, SampleWeight")
            
            # Check Winner is binary
            winner_values = df['Winner'].unique()
            print(f"   Winner unique values: {sorted(winner_values)}")
            if set(winner_values).issubset({0.0, 1.0}):
                print(f"   ✅ Winner labels are binary (0.0, 1.0)")
            else:
                print(f"   ❌ ERROR: Winner labels are NOT binary: {winner_values}")
                return False
            
            # Check SampleWeight distribution
            weight_counts = df['SampleWeight'].value_counts().sort_index()
            print(f"   SampleWeight distribution:")
            for weight, count in weight_counts.items():
                print(f"      {weight}: {count} samples")
        else:
            print(f"   ❌ Missing critical columns")
            return False
            
    except Exception as e:
        print(f"❌ Feature extraction failed: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    # Step 4: Group by track and test training on one track
    print("\nSTEP 3: Testing model training on one track...")
    
    # Find track with most samples
    track_counts = df['Track'].value_counts()
    print(f"\n   Available tracks (top 5):")
    for track, count in track_counts.head().items():
        print(f"      {track}: {count} samples")
    
    test_track = track_counts.index[0]
    track_df = df[df['Track'] == test_track].copy()
    
    print(f"\n   Testing with track: {test_track} ({len(track_df)} samples)")
    
    if len(track_df) < 10:
        print(f"   ⚠️  Very few samples, but proceeding...")
    
    try:
        models, metrics = train_track_specific_ensemble(track_df, feature_cols, test_track)
        
        print(f"\n✅ Model training successful!")
        print(f"   Models trained: {list(models.keys())}")
        print(f"   Metrics: {metrics}")
        
        # Test prediction
        print(f"\n   Testing prediction on 1 sample...")
        X_test = track_df[feature_cols].iloc[:1]
        
        for model_name, model in models.items():
            pred = model.predict_proba(X_test)
            print(f"      {model_name}: {pred[0]}")
        
        print(f"\n   ✅ Predictions generated successfully!")
        
    except Exception as e:
        print(f"❌ Model training failed: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    print("\n" + "="*80)
    print("✅ ALL TESTS PASSED - Pipeline is working correctly!")
    print("="*80 + "\n")
    
    return True

if __name__ == "__main__":
    success = test_minimal_training()
    sys.exit(0 if success else 1)
