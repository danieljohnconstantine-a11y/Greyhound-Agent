#!/usr/bin/env python3
"""
VALIDATION TEST - Test system accuracy on historical races

This script:
1. Loads results for 29/01 and 30/01 (273 races total)
2. For each race, generates predictions using the ML models
3. Compares predictions to actual results
4. Calculates Top-1 and Top-3 accuracy
5. Provides comprehensive report on system performance
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

import pandas as pd
import numpy as np
import pickle
from pathlib import Path
from datetime import datetime
import warnings
warnings.filterwarnings('ignore')

# Import our modules
from parser import parse_race_form
from features import compute_features

def load_results_file(filepath):
    """Load results CSV file"""
    try:
        df = pd.read_csv(filepath)
        print(f"✓ Loaded {len(df)} races from {filepath}")
        return df
    except Exception as e:
        print(f"✗ Error loading {filepath}: {e}")
        return None

def find_pdf_for_race(track_name, date_str):
    """Find PDF file for a specific track and date"""
    # Map track names to PDF codes
    track_codes = {
        'Casino': 'CSNO',
        'Richmond Straight': 'RIST',
        'Nowra': 'NOWR',
        'Wentworth Park': 'WENP',
        'Shepparton': 'SHEP',
        'Mount Gambier': 'MTGG',
        'Ladbrokes Q Straight': 'QSTR',
        'Warragul': 'WARG',
        'Warrnambool': 'WNBL',
        'Sandown': 'SAND',
        'Hobart': 'ELWK',  # Elwick
        'Ladbrokes Q2 Parklands': 'QPRK',
        'Angle Park': 'ANGL',
        'Mandurah': 'MAND',
        'Wagga': 'WAGG',
        'Goulburn': 'GOUL',
        'Ladbrokes Gardens': 'GARD',
        'Richmond': 'RICH',
        'Bendigo': 'BDGO',
        'Healesville': 'HEAL',
        'Bet Nation Townsville': 'TOWN',
        'Geelong': 'GEEL',
        'Ladbrokes Q1 Lakeside': 'QLAK',
    }
    
    track_code = track_codes.get(track_name)
    if not track_code:
        return None
    
    # Parse date (format: DDMM from date_str like "2026-01-29")
    try:
        date_obj = datetime.strptime(date_str, "%Y-%m-%d")
        date_code = date_obj.strftime("%d%m")
    except:
        return None
    
    # Try to find PDF
    pdf_patterns = [
        f"data/{track_code}G{date_code}form.pdf",
        f"data/{track_code}G{date_code}12form.pdf",
        f"data/{track_code}G{date_code}01form.pdf",
    ]
    
    for pattern in pdf_patterns:
        if os.path.exists(pattern):
            return pattern
    
    return None

def load_models(track_name=None):
    """Load trained ML models"""
    models = {}
    
    # Try track-specific models first
    if track_name:
        track_dir = f"models/{track_name}"
        if os.path.exists(track_dir):
            for model_file in ['rf.pkl', 'gb.pkl', 'xgb.pkl']:
                path = f"{track_dir}/{model_file}"
                if os.path.exists(path):
                    try:
                        with open(path, 'rb') as f:
                            models[model_file.replace('.pkl', '')] = pickle.load(f)
                    except:
                        pass
    
    # Fallback to generic models
    if not models:
        for model_dir in ['models/SALE', 'models/WENTWORTH PARK', 'models']:
            for model_file in ['rf.pkl', 'gb.pkl', 'xgb.pkl']:
                path = f"{model_dir}/{model_file}"
                if os.path.exists(path) and model_file.replace('.pkl', '') not in models:
                    try:
                        with open(path, 'rb') as f:
                            models[model_file.replace('.pkl', '')] = pickle.load(f)
                    except:
                        pass
            if models:
                break
    
    return models

def predict_race(pdf_path, race_number, models):
    """Generate prediction for a specific race"""
    try:
        # Parse PDF
        all_races = parse_race_form(pdf_path)
        
        # Find the specific race
        race_data = None
        for race in all_races:
            if race.get('race_number') == race_number:
                race_data = race
                break
        
        if not race_data or 'dogs' not in race_data:
            return None
        
        # Compute features for each dog
        dogs_df = pd.DataFrame(race_data['dogs'])
        features_df = compute_features(dogs_df, race_data.get('track_name', ''), 
                                       race_data.get('distance', 520))
        
        if features_df.empty or len(features_df) == 0:
            return None
        
        # Make predictions with ensemble
        predictions = []
        for idx, row in features_df.iterrows():
            # Prepare features (drop non-feature columns)
            feature_cols = [col for col in features_df.columns 
                          if col not in ['Box', 'DogName', 'Form', 'TrainerName', 'OwnerName']]
            X = row[feature_cols].values.reshape(1, -1)
            
            # Ensemble predictions
            probs = []
            for model_name, model in models.items():
                try:
                    if hasattr(model, 'predict_proba'):
                        prob = model.predict_proba(X)[0][1] if len(model.classes_) > 1 else model.predict_proba(X)[0][0]
                    else:
                        prob = model.predict(X)[0]
                    probs.append(prob)
                except:
                    pass
            
            if probs:
                avg_prob = np.mean(probs)
                predictions.append({
                    'box': row.get('Box', idx + 1),
                    'dog_name': row.get('DogName', ''),
                    'probability': avg_prob
                })
        
        if not predictions:
            return None
        
        # Sort by probability
        predictions.sort(key=lambda x: x['probability'], reverse=True)
        
        return predictions
        
    except Exception as e:
        print(f"  Error predicting race {race_number}: {e}")
        return None

def main():
    print("=" * 80)
    print("VALIDATION TEST - SYSTEM ACCURACY ON HISTORICAL RACES")
    print("=" * 80)
    print()
    print("Testing on 29/01/2026 and 30/01/2026 races...")
    print()
    
    # Load results
    results_29 = load_results_file("data/results_2026-01-29.csv")
    results_30 = load_results_file("data/results_2026-01-30.csv")
    
    if results_29 is None and results_30 is None:
        print("ERROR: Could not load any results files!")
        return
    
    # Combine results
    all_results = []
    if results_29 is not None:
        for _, row in results_29.iterrows():
            all_results.append({
                'track': row['Track'],
                'race': int(row['Race']),
                'winner': int(row['Position1']),
                'second': int(row['Position2']),
                'third': int(row['Position3']),
                'date': '2026-01-29'
            })
    
    if results_30 is not None:
        for _, row in results_30.iterrows():
            all_results.append({
                'track': row['Track'],
                'race': int(row['Race']),
                'winner': int(row['Position1']),
                'second': int(row['Position2']),
                'third': int(row['Position3']),
                'date': '2026-01-30'
            })
    
    print(f"\nTotal races to test: {len(all_results)}")
    print()
    
    # Load models
    print("Loading ML models...")
    models = load_models()
    if not models:
        print("ERROR: No models found!")
        return
    print(f"✓ Loaded {len(models)} models: {list(models.keys())}")
    print()
    
    # Test each race
    print("=" * 80)
    print("RUNNING PREDICTIONS...")
    print("=" * 80)
    print()
    
    top1_correct = 0
    top3_correct = 0
    total_tested = 0
    failed_predictions = 0
    
    track_stats = {}
    
    for i, result in enumerate(all_results):
        track = result['track']
        race_num = result['race']
        winner = result['winner']
        top3 = [result['winner'], result['second'], result['third']]
        date = result['date']
        
        # Find PDF
        pdf_path = find_pdf_for_race(track, date)
        if not pdf_path:
            failed_predictions += 1
            continue
        
        # Generate prediction
        predictions = predict_race(pdf_path, race_num, models)
        if not predictions:
            failed_predictions += 1
            continue
        
        # Check accuracy
        predicted_winner = predictions[0]['box']
        predicted_top3 = [p['box'] for p in predictions[:3]]
        
        total_tested += 1
        
        # Check if winner predicted correctly
        if predicted_winner == winner:
            top1_correct += 1
            status = "✓ CORRECT"
        else:
            status = "✗ Wrong"
        
        # Check if winner in top 3
        if winner in predicted_top3:
            top3_correct += 1
        
        # Track stats
        if track not in track_stats:
            track_stats[track] = {'tested': 0, 'top1': 0, 'top3': 0}
        track_stats[track]['tested'] += 1
        if predicted_winner == winner:
            track_stats[track]['top1'] += 1
        if winner in predicted_top3:
            track_stats[track]['top3'] += 1
        
        # Print progress every 10 races
        if (i + 1) % 10 == 0:
            print(f"Progress: {i + 1}/{len(all_results)} races processed...")
    
    # Calculate final accuracy
    print()
    print("=" * 80)
    print("VALIDATION RESULTS")
    print("=" * 80)
    print()
    
    if total_tested == 0:
        print("ERROR: No races could be tested!")
        return
    
    top1_accuracy = (top1_correct / total_tested) * 100
    top3_accuracy = (top3_correct / total_tested) * 100
    random_top1 = 12.5  # 1/8 dogs
    random_top3 = 37.5  # 3/8 dogs
    
    print(f"Total Races Tested: {total_tested}")
    print(f"Failed Predictions: {failed_predictions}")
    print()
    print(f"TOP-1 ACCURACY (Winner Picked): {top1_correct}/{total_tested} = {top1_accuracy:.2f}%")
    print(f"  Random Baseline: {random_top1:.2f}%")
    print(f"  Improvement: {top1_accuracy - random_top1:.2f}% {'✓' if top1_accuracy > random_top1 else '✗'}")
    print()
    print(f"TOP-3 ACCURACY (Winner in Top 3): {top3_correct}/{total_tested} = {top3_accuracy:.2f}%")
    print(f"  Random Baseline: {random_top3:.2f}%")
    print(f"  Improvement: {top3_accuracy - random_top3:.2f}% {'✓' if top3_accuracy > random_top3 else '✗'}")
    print()
    
    # Assessment
    print("=" * 80)
    print("ASSESSMENT")
    print("=" * 80)
    print()
    
    if top1_accuracy > 20:
        print("✓ EXCELLENT: System beats random by significant margin!")
        print("  Production ready for extended testing.")
    elif top1_accuracy > 15:
        print("✓ GOOD: System beats random consistently.")
        print("  Continue testing, consider tuning.")
    elif top1_accuracy > 12.5:
        print("⚠ MARGINAL: Slightly better than random.")
        print("  Needs investigation and improvement.")
    else:
        print("✗ POOR: Not better than random guessing.")
        print("  Major debugging required.")
    
    print()
    
    # Per-track stats
    if track_stats:
        print("=" * 80)
        print("PER-TRACK BREAKDOWN")
        print("=" * 80)
        print()
        for track in sorted(track_stats.keys()):
            stats = track_stats[track]
            if stats['tested'] > 0:
                t1_acc = (stats['top1'] / stats['tested']) * 100
                t3_acc = (stats['top3'] / stats['tested']) * 100
                print(f"{track:30s}: {stats['tested']:2d} races | Top-1: {t1_acc:5.1f}% | Top-3: {t3_acc:5.1f}%")
    
    print()
    print("=" * 80)
    print("VALIDATION COMPLETE")
    print("=" * 80)
    
    # Save report
    report_path = "VALIDATION_TEST_RESULTS.txt"
    with open(report_path, 'w') as f:
        f.write(f"VALIDATION TEST RESULTS\n")
        f.write(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"\n")
        f.write(f"Races Tested: {total_tested}\n")
        f.write(f"Top-1 Accuracy: {top1_accuracy:.2f}%\n")
        f.write(f"Top-3 Accuracy: {top3_accuracy:.2f}%\n")
        f.write(f"\n")
        f.write(f"Assessment: ")
        if top1_accuracy > 20:
            f.write("EXCELLENT - Production Ready\n")
        elif top1_accuracy > 15:
            f.write("GOOD - Continue Testing\n")
        elif top1_accuracy > 12.5:
            f.write("MARGINAL - Needs Improvement\n")
        else:
            f.write("POOR - Major Debugging Needed\n")
    
    print(f"\n✓ Results saved to {report_path}")

if __name__ == "__main__":
    main()
