"""
Test limited training pipeline with 2-3 PDFs only
"""
import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(__file__))

print('Testing limited pipeline with ~50 races...')
print('=' * 80)

from src.ml_predictor import load_historical_data_hybrid
import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score
import pickle

# Load limited data
print('\n1. Loading limited data (first 50 races for speed)...')
race_data_list, winners_list = load_historical_data_hybrid()

# Limit to first 50 races for quick test
race_data_list = race_data_list[:50]
winners_list = winners_list[:50]

print(f'   Loaded {len(race_data_list)} races with {len(winners_list)} training samples')

# Extract features
print('\n2. Extracting features...')
from train_ml_track_ensemble import extract_features_and_labels

try:
    df, feature_cols = extract_features_and_labels(race_data_list, winners_list)
    print(f'   ✅ Feature extraction successful!')
    print(f'   DataFrame shape: {df.shape}')
    print(f'   Feature columns: {len(feature_cols)}')
    print(f'   Memory usage: {df.memory_usage(deep=True).sum() / 1024 / 1024:.2f} MB')
except Exception as e:
    print(f'   ❌ Feature extraction failed: {e}')
    import traceback
    traceback.print_exc()
    sys.exit(1)

# Check for NaN/Inf
print('\n3. Checking data quality...')
nan_counts = df[feature_cols].isna().sum()
print(f'   NaN values: {nan_counts[nan_counts > 0].sum()} total')

inf_counts = np.isinf(df[feature_cols].select_dtypes(include=[np.number])).sum()
print(f'   Inf values: {inf_counts[inf_counts > 0].sum()} total')

# Try grouping by track
print('\n4. Grouping by track...')
try:
    tracks = df['Track'].unique()
    print(f'   ✅ Found {len(tracks)} unique tracks: {list(tracks[:5])}')
    
    for track in tracks:
        track_count = len(df[df['Track'] == track])
        print(f'      - {track}: {track_count} samples')
except Exception as e:
    print(f'   ❌ Track grouping failed: {e}')
    import traceback
    traceback.print_exc()
    sys.exit(1)

# Test training on first track with enough data
print('\n5. Testing model training...')
trained = False
for track in tracks:
    track_df = df[df['Track'] == track].copy()
    print(f'   Trying track: {track}, Samples: {len(track_df)}')
    
    if len(track_df) >= 30:
        try:
            X = track_df[feature_cols].fillna(0)
            y = track_df['Winner']
            weights = track_df['SampleWeight']
            
            # Split data
            X_train, X_test, y_train, y_test, w_train, w_test = train_test_split(
                X, y, weights, test_size=0.2, random_state=42
            )
            
            # Scale
            scaler = StandardScaler()
            X_train_scaled = scaler.fit_transform(X_train)
            X_test_scaled = scaler.transform(X_test)
            
            # Train RF
            print('      Training RandomForest...')
            rf = RandomForestClassifier(n_estimators=50, random_state=42, n_jobs=2, max_depth=10)
            rf.fit(X_train_scaled, y_train, sample_weight=w_train)
            
            # Test
            y_pred = rf.predict(X_test_scaled)
            accuracy = accuracy_score(y_test, y_pred)
            print(f'      ✅ Test Accuracy: {accuracy:.2%}')
            
            trained = True
            break
        except Exception as e:
            print(f'      ❌ Training failed: {e}')
            import traceback
            traceback.print_exc()
    else:
        print(f'      ⚠️  Insufficient data ({len(track_df)} < 30 samples)')

if trained:
    print('\n✅ LIMITED PIPELINE TEST PASSED!')
    print('   All components working correctly')
    print('=' * 80)
else:
    print('\n⚠️  Could not train - no track with >= 30 samples')
    print('=' * 80)
