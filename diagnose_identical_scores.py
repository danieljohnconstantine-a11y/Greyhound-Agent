"""
DIAGNOSTIC SCRIPT: Identify Root Cause of Identical Prediction Scores
======================================================================

This script performs detailed analysis to identify why all dogs in a race
receive identical prediction scores.

Analysis steps:
1. Parse a single PDF to extract raw data
2. Compute features with detailed logging
3. Check which features vary vs constant
4. Identify specific issues in feature computation
5. Report exact lines causing identical scores
"""

import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from src.parser import parse_race_form
from src.features import compute_features
import pandas as pd
import numpy as np
import pdfplumber
import pickle

def extract_text_from_pdf(pdf_path):
    """Extract text from PDF"""
    text = ""
    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            text += page.extract_text() + "\n"
    return text

def analyze_feature_variance(df, feature_cols):
    """
    Analyze which features vary between dogs vs which are constant.
    Returns detailed report.
    """
    print("\n" + "="*80)
    print("FEATURE VARIANCE ANALYSIS")
    print("="*80)
    
    varying_features = []
    constant_features = []
    missing_features = []
    
    for col in feature_cols:
        if col not in df.columns:
            missing_features.append(col)
            continue
            
        unique_count = df[col].nunique()
        if unique_count == 1:
            constant_features.append({
                'name': col,
                'value': df[col].iloc[0],
                'count': len(df)
            })
        else:
            varying_features.append({
                'name': col,
                'unique_values': unique_count,
                'min': df[col].min(),
                'max': df[col].max(),
                'std': df[col].std()
            })
    
    print(f"\n📊 Summary:")
    print(f"   Total features expected: {len(feature_cols)}")
    print(f"   Missing features: {len(missing_features)}")
    print(f"   Constant features: {len(constant_features)}")
    print(f"   Varying features: {len(varying_features)}")
    
    print(f"\n❌ CONSTANT FEATURES (IDENTICAL FOR ALL DOGS):")
    if constant_features:
        for feat in constant_features[:20]:  # Show first 20
            print(f"   • {feat['name']}: {feat['value']}")
        if len(constant_features) > 20:
            print(f"   ... and {len(constant_features) - 20} more constant features")
    else:
        print("   None - all features vary!")
    
    print(f"\n✅ VARYING FEATURES (DIFFER BETWEEN DOGS):")
    if varying_features:
        for feat in varying_features[:10]:  # Show first 10
            print(f"   • {feat['name']}: {feat['unique_values']} unique values (min={feat['min']:.3f}, max={feat['max']:.3f}, std={feat['std']:.3f})")
        if len(varying_features) > 10:
            print(f"   ... and {len(varying_features) - 10} more varying features")
    else:
        print("   ❌ NO VARYING FEATURES - This will cause identical predictions!")
    
    print(f"\n⚠️ MISSING FEATURES (NOT IN PARSED DATA):")
    if missing_features:
        for feat in missing_features[:15]:
            print(f"   • {feat}")
        if len(missing_features) > 15:
            print(f"   ... and {len(missing_features) - 15} more missing features")
    
    # Calculate percentage of constant features
    total_features = len(feature_cols) - len(missing_features)
    if total_features > 0:
        constant_pct = (len(constant_features) / total_features) * 100
        varying_pct = (len(varying_features) / total_features) * 100
        
        print(f"\n📈 Percentages:")
        print(f"   Constant: {constant_pct:.1f}%")
        print(f"   Varying: {varying_pct:.1f}%")
        
        if constant_pct > 50:
            print(f"\n🚨 CRITICAL ISSUE: {constant_pct:.1f}% of features are constant!")
            print(f"   This will cause all dogs to receive nearly identical scores.")
            print(f"   Expected: <30% constant features for good predictions")
    
    return varying_features, constant_features, missing_features

def show_raw_parsed_data(df):
    """Show raw parsed data from PDF"""
    print("\n" + "="*80)
    print("RAW PARSED DATA (Before Feature Computation)")
    print("="*80)
    
    # Show critical columns that should vary
    critical_cols = ['Box', 'DogName', 'Weight', 'BestTimeSec', 'SectionalSec', 
                    'CareerWins', 'CareerStarts', 'DLR', 'DLW']
    
    available_cols = [col for col in critical_cols if col in df.columns]
    
    print(f"\nShowing {len(df)} dogs with columns: {', '.join(available_cols)}")
    print("-" * 80)
    
    # Show data for each dog
    for idx, row in df.iterrows():
        values = [f"{col}={row[col]}" for col in available_cols]
        print(f"Dog {idx+1}: {', '.join(values)}")
    
    # Check for duplicate values
    print("\n📊 Data Variance Check:")
    for col in available_cols:
        unique_count = df[col].nunique()
        if unique_count == 1:
            print(f"   ❌ {col}: ALL IDENTICAL ({df[col].iloc[0]})")
        elif unique_count == len(df):
            print(f"   ✅ {col}: All unique ({unique_count} different values)")
        else:
            print(f"   ⚠️  {col}: {unique_count}/{len(df)} unique values")

def main():
    print("="*80)
    print("🔍 GREYHOUND PREDICTION DIAGNOSTIC - ROOT CAUSE ANALYSIS")
    print("="*80)
    
    # Use first PDF file from data_predictions/
    import glob
    pdf_files = glob.glob("data_predictions/*.pdf")
    
    if not pdf_files:
        print("❌ No PDF files found in data_predictions/")
        return 1
    
    # Use first PDF
    pdf_file = sorted(pdf_files)[0]
    print(f"\n📄 Analyzing: {os.path.basename(pdf_file)}")
    
    # Step 1: Extract text from PDF
    print(f"\n[1/5] Extracting text from PDF...")
    pdf_text = extract_text_from_pdf(pdf_file)
    print(f"   ✓ Extracted {len(pdf_text)} characters")
    
    # Step 2: Parse PDF
    print(f"\n[2/5] Parsing race form...")
    race_df = parse_race_form(pdf_text)
    
    if race_df is None or len(race_df) == 0:
        print("   ❌ Failed to parse PDF - no data extracted")
        return 1
    
    print(f"   ✓ Parsed {len(race_df)} dogs")
    print(f"   ✓ Columns: {', '.join(race_df.columns[:10])}...")
    
    # Show raw parsed data
    show_raw_parsed_data(race_df)
    
    # Step 3: Compute features with detailed logging
    print(f"\n[3/5] Computing features...")
    print("-" * 80)
    
    # Compute features (this will print warnings)
    race_df_with_features = compute_features(race_df)
    
    print("-" * 80)
    print(f"   ✓ Features computed - now {len(race_df_with_features.columns)} columns")
    
    # Step 4: Load model configuration to see what features are expected
    print(f"\n[4/5] Loading model configuration...")
    config_path = "models/track_ensemble/config.pkl"
    
    if not os.path.exists(config_path):
        print("   ❌ Model configuration not found - cannot check feature compatibility")
        return 1
    
    with open(config_path, 'rb') as f:
        config = pickle.load(f)
    
    print(f"   ✓ Loaded config")
    print(f"   Model expects {len(config['feature_cols'])} features")
    print(f"   Features: {', '.join(config['feature_cols'][:15])}...")
    
    # Step 5: Analyze feature variance
    print(f"\n[5/5] Analyzing feature variance...")
    varying, constant, missing = analyze_feature_variance(race_df_with_features, config['feature_cols'])
    
    # ROOT CAUSE ANALYSIS
    print("\n" + "="*80)
    print("🎯 ROOT CAUSE ANALYSIS")
    print("="*80)
    
    # Check specific issues
    issues_found = []
    
    # Issue 1: Too many constant features
    total_features = len(config['feature_cols']) - len(missing)
    constant_pct = (len(constant) / total_features * 100) if total_features > 0 else 0
    
    if constant_pct > 50:
        issues_found.append({
            'severity': 'CRITICAL',
            'issue': f'{constant_pct:.1f}% of features are constant',
            'impact': 'All dogs receive nearly identical scores',
            'location': 'src/features.py - multiple feature computation functions',
            'explanation': 'When most features have the same value for all dogs, the ML model cannot differentiate between them.'
        })
    
    # Issue 2: Key dog-specific features are constant
    key_features = ['Box', 'Weight', 'BestTimeSec', 'SectionalSec', 'CareerWins', 
                   'CareerStarts', 'WinRate', 'PlaceRate', 'DLWFactor', 'WeightFactor']
    constant_key_features = [f['name'] for f in constant if f['name'] in key_features]
    
    if constant_key_features:
        issues_found.append({
            'severity': 'HIGH',
            'issue': f'Key dog-specific features are constant: {", ".join(constant_key_features)}',
            'impact': 'Model cannot distinguish between individual dog performance',
            'location': 'src/features.py - lines 20-400',
            'explanation': 'These features should vary between dogs based on their individual stats, but all dogs have the same value.'
        })
    
    # Issue 3: Missing critical timing data
    timing_features = ['BestTimeSec', 'SectionalSec', 'Speed_kmh', 'EarlySpeedIndex']
    missing_timing = [f for f in timing_features if f in [m for m in missing]]
    constant_timing = [f['name'] for f in constant if f['name'] in timing_features]
    
    if missing_timing or constant_timing:
        issues_found.append({
            'severity': 'HIGH',
            'issue': f'Timing data issues - Missing: {missing_timing}, Constant: {constant_timing}',
            'impact': 'Speed-based differentiation is lost',
            'location': 'src/parser.py + src/features.py lines 60-174',
            'explanation': 'Timing data (BestTimeSec, SectionalSec) is not being parsed correctly or is identical for all dogs.'
        })
    
    # Issue 4: Check if Box varies (it MUST vary)
    if 'Box' in [f['name'] for f in constant]:
        issues_found.append({
            'severity': 'CRITICAL',
            'issue': 'Box number is constant (all dogs have same box)',
            'impact': 'Fundamental race data is incorrect',
            'location': 'src/parser.py - Box number parsing',
            'explanation': 'Box numbers should be 1-8 and different for each dog. This indicates parsing failure.'
        })
    
    # Print all issues
    if issues_found:
        print(f"\n🚨 FOUND {len(issues_found)} CRITICAL ISSUES:\n")
        for i, issue in enumerate(issues_found, 1):
            print(f"{i}. [{issue['severity']}] {issue['issue']}")
            print(f"   Impact: {issue['impact']}")
            print(f"   Location: {issue['location']}")
            print(f"   Explanation: {issue['explanation']}")
            print()
    else:
        print("\n✅ No critical issues found - features appear to vary correctly.")
    
    # Show sample predictions to verify issue
    print("\n" + "="*80)
    print("🔮 SAMPLE PREDICTION TEST")
    print("="*80)
    
    # Load track-specific model
    track_name = race_df['Track'].iloc[0]
    print(f"\nTrack: {track_name}")
    
    # Check if we have models for this track
    model_path = f"models/track_ensemble/{track_name}_rf.pkl"
    if not os.path.exists(model_path):
        print(f"⚠️  No models found for {track_name} - using DARWIN models for test")
        track_name = "DARWIN"
    
    # Load scaler and one model for quick test
    scaler_path = f"models/track_ensemble/{track_name}_scaler.pkl"
    model_path = f"models/track_ensemble/{track_name}_rf.pkl"
    
    if os.path.exists(scaler_path) and os.path.exists(model_path):
        with open(scaler_path, 'rb') as f:
            scaler = pickle.load(f)
        with open(model_path, 'rb') as f:
            model = pickle.load(f)
        
        # Prepare features
        X = race_df_with_features[config['feature_cols']].fillna(0)
        X_scaled = scaler.transform(X)
        
        # Get predictions
        predictions = model.predict_proba(X_scaled)[:, 1]
        
        # Show results
        print(f"\nPrediction scores:")
        for idx, (box, dog, score) in enumerate(zip(race_df['Box'], race_df['DogName'], predictions)):
            print(f"   Box {box} - {dog}: {score*100:.1f}%")
        
        # Check score variance
        score_range = predictions.max() - predictions.min()
        print(f"\nScore range: {score_range*100:.2f}%")
        
        if score_range < 0.002:  # Less than 0.2%
            print(f"❌ CONFIRMED: Scores are virtually identical (range < 0.2%)")
            print(f"   This confirms the feature computation issue.")
        else:
            print(f"✅ Scores vary by {score_range*100:.1f}% - features are working correctly")
    
    print("\n" + "="*80)
    print("📋 DIAGNOSTIC COMPLETE")
    print("="*80)
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
