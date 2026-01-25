"""
Quick Test Predictions - 3 Tracks
Runs predictions using test models to verify varied scores
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

print("=" * 60)
print("QUICK TEST PREDICTIONS - 3 TRACKS")
print("=" * 60)
print()

try:
    # Import after path setup
    import pandas as pd
    import numpy as np
    import pickle
    import json
    from src.pdf_parser import parse_greyhound_pdf
    from src.features import build_feature_matrix
    import logging
    
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)
    
    # Load config
    config_path = 'models/track_ensemble_test/config.pkl'
    if not os.path.exists(config_path):
        print(f"❌ Config file not found: {config_path}")
        print("Please run training first.")
        sys.exit(1)
    
    with open(config_path, 'rb') as f:
        config = pickle.load(f)
    
    logger.info(f"Loaded config for {len(config['tracks'])} tracks")
    
    # Find test PDFs
    pdf_dir = 'data_test'
    pdf_files = [f for f in os.listdir(pdf_dir) if f.endswith('.pdf')]
    
    logger.info(f"Found {len(pdf_files)} PDF files")
    
    # Create output directory
    os.makedirs('outputs', exist_ok=True)
    
    # Generate predictions
    all_results = {}
    all_scores = []
    
    for pdf_file in pdf_files:
        pdf_path = os.path.join(pdf_dir, pdf_file)
        logger.info(f"Processing {pdf_file}...")
        
        try:
            # Parse PDF
            races = parse_greyhound_pdf(pdf_path)
            
            for race in races:
                track = race.get('track', 'Unknown')
                race_num = race.get('race', 1)
                
                # Check if we have a model for this track
                if track not in config['tracks']:
                    logger.warning(f"No model for track: {track}")
                    continue
                
                # Load model
                model_file = config['tracks'][track]['models'][0]  # Use first model (RF)
                model_path = os.path.join('models/track_ensemble_test', model_file)
                
                with open(model_path, 'rb') as f:
                    model_data = pickle.load(f)
                
                model = model_data['model']
                feature_names = model_data['features']
                
                # Build features
                df = pd.DataFrame(race['dogs'])
                feature_matrix = build_feature_matrix(df)
                
                if feature_matrix is None or len(feature_matrix) == 0:
                    continue
                
                # Filter to model features
                X = feature_matrix[feature_names].fillna(0)
                
                # Get predictions
                probas = model.predict_proba(X)
                win_probs = probas[:, 1] if probas.shape[1] > 1 else probas[:, 0]
                
                # Normalize to percentages
                win_probs = win_probs / win_probs.sum() * 100
                
                # Store results
                if track not in all_results:
                    all_results[track] = {}
                if race_num not in all_results[track]:
                    all_results[track][race_num] = []
                
                for i, dog in enumerate(race['dogs']):
                    prob = float(win_probs[i])
                    all_scores.append(prob)
                    all_results[track][race_num].append({
                        'box': dog.get('Box', i+1),
                        'name': dog.get('Dog', f'Dog{i+1}'),
                        'probability': prob
                    })
        
        except Exception as e:
            logger.error(f"Error processing {pdf_file}: {e}")
            continue
    
    # Generate summary and save to outputs folder
    summary_file = 'outputs/test_predictions_summary.txt'
    with open(summary_file, 'w') as f:
        f.write("=" * 60 + "\n")
        f.write("QUICK TEST PREDICTIONS SUMMARY\n")
        f.write("=" * 60 + "\n\n")
        
        for track in sorted(all_results.keys()):
            f.write(f"\n{track}:\n")
            f.write("-" * 40 + "\n")
            
            track_results = all_results[track]
            for race_num in sorted(track_results.keys()):
                race_dogs = track_results[race_num]
                f.write(f"\nRace {race_num}:\n")
                
                # Sort by probability
                sorted_dogs = sorted(race_dogs, key=lambda x: x['probability'], reverse=True)
                
                for dog in sorted_dogs:
                    prob = dog['probability']
                    box = dog['box']
                    name = dog['name']
                    f.write(f"  Box {box}: {name:30s} - {prob:5.1f}%\n")
    
    print()
    print("=" * 60)
    print("✅ PREDICTIONS COMPLETE!")
    print("=" * 60)
    print()
    print(f"Summary saved to: {summary_file}")
    print()
    
    # Show summary
    print("RESULTS PREVIEW:")
    print("-" * 60)
    with open(summary_file, 'r') as f:
        print(f.read())
    print()
    
    # Analyze results
    print("=" * 60)
    print("ANALYSIS")
    print("=" * 60)
    print()
    
    if all_scores:
        min_score = min(all_scores)
        max_score = max(all_scores)
        score_range = max_score - min_score
        
        print(f"Score range: {min_score:.1f}% - {max_score:.1f}% (spread: {score_range:.1f}%)")
        print()
        
        if score_range < 2.0:
            print("⚠️  WARNING: Scores are very similar (spread < 2%)")
            print("    This suggests the fix may not be working.")
            print("    Check test_training_output.txt for maiden race messages.")
        elif score_range < 5.0:
            print("⚠️  CAUTION: Scores show limited variation (spread < 5%)")
            print("    Results are improved but may need verification.")
        else:
            print("✅ SUCCESS: Scores show good variation (spread >= 5%)")
            print("    The fix appears to be working correctly!")
    else:
        print("⚠️  WARNING: No predictions generated")
    
    print()
    
except Exception as e:
    print()
    print("=" * 60)
    print("❌ ERROR DURING PREDICTIONS")
    print("=" * 60)
    print()
    print(f"Error: {str(e)}")
    print()
    import traceback
    traceback.print_exc()
    sys.exit(1)
