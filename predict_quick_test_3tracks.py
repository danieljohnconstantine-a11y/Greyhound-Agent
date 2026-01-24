"""
Quick Test Predictions - 3 Tracks
Runs predictions using test models to verify varied scores
"""
import sys
sys.path.insert(0, 'src')

from ml_predictor import TrackEnsemblePredictor
import pandas as pd
import os

print("=" * 60)
print("QUICK TEST PREDICTIONS - 3 TRACKS")
print("=" * 60)
print()

try:
    # Initialize predictor with test models
    predictor = TrackEnsemblePredictor()
    predictor.model_dir = 'models/track_ensemble_test'
    
    # Load test models
    print("Loading test models...")
    predictor.load_models()
    print(f"  Loaded {len(predictor.models)} track models")
    print()
    
    # Run predictions on test PDFs
    print("Running predictions...")
    results = predictor.predict_from_pdfs('data_test')
    
    # Create output directory
    os.makedirs('outputs', exist_ok=True)
    
    # Generate summary
    summary_file = 'outputs/test_predictions_summary.txt'
    with open(summary_file, 'w') as f:
        f.write("=" * 60 + "\n")
        f.write("QUICK TEST PREDICTIONS SUMMARY\n")
        f.write("=" * 60 + "\n\n")
        
        for track in results.keys():
            f.write(f"\n{track}:\n")
            f.write("-" * 40 + "\n")
            
            track_results = results[track]
            for race_num in sorted(track_results.keys()):
                race_data = track_results[race_num]
                f.write(f"\nRace {race_num}:\n")
                
                # Sort by probability
                sorted_dogs = sorted(
                    race_data.items(),
                    key=lambda x: x[1]['probability'],
                    reverse=True
                )
                
                for dog_name, dog_data in sorted_dogs:
                    prob = dog_data['probability']
                    box = dog_data.get('box', '?')
                    f.write(f"  Box {box}: {dog_name:30s} - {prob:5.1f}%\n")
    
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
    
    all_scores = []
    for track in results.values():
        for race in track.values():
            for dog in race.values():
                all_scores.append(dog['probability'])
    
    if all_scores:
        min_score = min(all_scores)
        max_score = max(all_scores)
        score_range = max_score - min_score
        
        print(f"Score range: {min_score:.1f}% - {max_score:.1f}% (spread: {score_range:.1f}%)")
        print()
        
        if score_range < 2.0:
            print("⚠️  WARNING: Scores are very similar (spread < 2%)")
            print("    This suggests the fix may not be working.")
            print("    Check test_training.log for maiden race messages.")
        elif score_range < 5.0:
            print("⚠️  CAUTION: Scores show limited variation (spread < 5%)")
            print("    Results are improved but may need verification.")
        else:
            print("✅ SUCCESS: Scores show good variation (spread >= 5%)")
            print("    The fix appears to be working correctly!")
    
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
