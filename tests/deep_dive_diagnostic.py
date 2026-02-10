"""
DEEP DIVE DIAGNOSTIC: Why are scores nearly identical despite varying features?
===============================================================================

This script investigates the actual model weights and scaled feature values
to understand why predictions are so similar despite feature variation.
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
    text = ""
    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            text += page.extract_text() + "\n"
    return text

def main():
    print("="*80)
    print("🔬 DEEP DIVE: Why Identical Scores Despite Varying Features?")
    print("="*80)
    
    # Load first PDF
    import glob
    pdf_files = glob.glob("data_predictions/*.pdf")
    pdf_file = sorted(pdf_files)[0]
    
    print(f"\nAnalyzing: {os.path.basename(pdf_file)}")
    
    # Parse and compute features
    pdf_text = extract_text_from_pdf(pdf_file)
    race_df = parse_race_form(pdf_text)
    race_df = compute_features(race_df)
    
    # Take first race only (easier to analyze)
    first_race = race_df[race_df['RaceNumber'] == race_df['RaceNumber'].iloc[0]].copy()
    print(f"\nFocusing on Race {first_race['RaceNumber'].iloc[0]}: {len(first_race)} dogs")
    
    # Load model config
    with open("models/track_ensemble/config.pkl", 'rb') as f:
        config = pickle.load(f)
    
    # Load DARWIN models (we're using these for test)
    with open("models/track_ensemble/DARWIN_scaler.pkl", 'rb') as f:
        scaler = pickle.load(f)
    with open("models/track_ensemble/DARWIN_rf.pkl", 'rb') as f:
        rf_model = pickle.load(f)
    
    print(f"\nModel expects {len(config['feature_cols'])} features")
    
    # Prepare features
    X = first_race[config['feature_cols']].fillna(0)
    
    print("\n" + "="*80)
    print("FEATURE VALUES (RAW - Before Scaling)")
    print("="*80)
    
    # Show feature values for each dog
    print(f"\nShowing top 20 features for each dog:")
    important_features = ['Box', 'BestTimeSec', 'SectionalSec', 'CareerWins', 'CareerStarts', 
                         'WinRate', 'PlaceRate', 'Speed_kmh', 'DLWFactor', 'DrawFactor',
                         'BoxPositionBias', 'ConsistencyIndex', 'EarlySpeedIndex', 'RestFactor',
                         'TrainerStrikeRate', 'BoxPenaltyFactor', 'BestTimePercentile', 'RTCFactor',
                         'AgeFactor', 'GradeFactor']
    
    available_features = [f for f in important_features if f in X.columns]
    
    for idx, row in first_race.iterrows():
        dog_name = row['DogName']
        box = row['Box']
        feature_vals = []
        for feat in available_features[:10]:  # Show first 10
            val = X.loc[idx, feat]
            feature_vals.append(f"{feat}={val:.3f}")
        print(f"Box {box} ({dog_name}): {', '.join(feature_vals)}")
    
    # Scale features
    X_scaled = scaler.transform(X)
    
    print("\n" + "="*80)
    print("FEATURE VALUES (SCALED - After StandardScaler)")
    print("="*80)
    
    print(f"\nAfter scaling, showing same features:")
    for i, idx in enumerate(first_race.index):
        row = first_race.loc[idx]
        dog_name = row['DogName']
        box = row['Box']
        feature_vals = []
        for j, feat in enumerate(available_features[:10]):
            feat_idx = config['feature_cols'].index(feat)
            val = X_scaled[i, feat_idx]
            feature_vals.append(f"{feat}={val:.3f}")
        print(f"Box {box} ({dog_name}): {', '.join(feature_vals)}")
    
    # Get feature importances from RF model
    print("\n" + "="*80)
    print("FEATURE IMPORTANCES (Random Forest)")
    print("="*80)
    
    # Model is wrapped in CalibratedClassifierCV - extract base estimator
    base_model = rf_model.calibrated_classifiers_[0].estimator if hasattr(rf_model, 'calibrated_classifiers_') else rf_model
    
    feature_importances = pd.DataFrame({
        'feature': config['feature_cols'],
        'importance': base_model.feature_importances_
    }).sort_values('importance', ascending=False)
    
    print(f"\nTop 30 most important features:")
    for idx, row in feature_importances.head(30).iterrows():
        print(f"   {row['feature']:30s}: {row['importance']:.6f}")
    
    # Check if top features vary
    print("\n" + "="*80)
    print("DO TOP FEATURES ACTUALLY VARY?")
    print("="*80)
    
    top_features = feature_importances.head(20)['feature'].tolist()
    print(f"\nChecking variance of top 20 features in this race:")
    
    for feat in top_features:
        if feat in X.columns:
            values = X[feat].values
            unique_count = len(np.unique(values))
            val_range = values.max() - values.min()
            std = values.std()
            
            if unique_count == 1:
                print(f"   ❌ {feat:30s}: CONSTANT ({values[0]:.3f})")
            elif std < 0.01:
                print(f"   ⚠️  {feat:30s}: Nearly constant (std={std:.6f})")
            else:
                print(f"   ✅ {feat:30s}: Varies (unique={unique_count}, std={std:.3f}, range={val_range:.3f})")
    
    # Generate predictions to see final scores
    predictions = rf_model.predict_proba(X_scaled)[:, 1]
    
    print("\n" + "="*80)
    print("FINAL PREDICTION SCORES")
    print("="*80)
    
    print(f"\nPredictions for each dog:")
    for i, idx in enumerate(first_race.index):
        row = first_race.loc[idx]
        print(f"   Box {row['Box']:2.0f} - {row['DogName']:20s}: {predictions[i]*100:.2f}%")
    
    score_range = predictions.max() - predictions.min()
    print(f"\nScore range: {score_range*100:.2f}%")
    print(f"Score std: {predictions.std()*100:.2f}%")
    
    # CRITICAL ANALYSIS
    print("\n" + "="*80)
    print("🎯 ROOT CAUSE IDENTIFICATION")
    print("="*80)
    
    # Count constant features among top 20
    constant_in_top20 = 0
    for feat in top_features[:20]:
        if feat in X.columns:
            if len(np.unique(X[feat].values)) == 1:
                constant_in_top20 += 1
    
    print(f"\n📊 Analysis:")
    print(f"   Top 20 features account for ~{feature_importances.head(20)['importance'].sum()*100:.1f}% of model decision")
    print(f"   {constant_in_top20}/20 top features are CONSTANT in this race")
    print(f"   This means {(constant_in_top20/20)*100:.0f}% of the model's 'important' signal is lost")
    
    if constant_in_top20 >= 10:
        print(f"\n🚨 CRITICAL ISSUE IDENTIFIED:")
        print(f"   The model's most important features ({constant_in_top20} of top 20) are constant!")
        print(f"   Even though 83% of ALL features vary, the IMPORTANT features don't vary enough.")
        print(f"   This is why predictions are nearly identical.")
    
    # Show which important features are constant
    print(f"\n🔍 Constant features in top 20 most important:")
    for i, feat in enumerate(top_features[:20], 1):
        if feat in X.columns and len(np.unique(X[feat].values)) == 1:
            importance = feature_importances[feature_importances['feature'] == feat]['importance'].iloc[0]
            print(f"   {i:2d}. {feat:30s} (importance={importance:.4f}) = {X[feat].iloc[0]:.3f}")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
