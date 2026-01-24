"""
Quick Test Training - 3 Tracks
Tests maiden race fixes with Cannington, Dubbo, and Wentworth Park
"""
import sys
sys.path.insert(0, 'src')

from ml_predictor import TrackEnsemblePredictor
import logging

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

print("=" * 60)
print("QUICK TEST TRAINING - 3 TRACKS")
print("=" * 60)
print()
print("Testing tracks:")
print("  1. Cannington")
print("  2. Dubbo") 
print("  3. Wentworth Park")
print()
print("=" * 60)
print()

try:
    # Initialize predictor
    predictor = TrackEnsemblePredictor()
    
    # Train with test data
    print("Starting training...")
    print()
    print("WATCH FOR THESE MESSAGES:")
    print("  ⚠️ MAIDEN RACE - Using CareerStarts for differentiation")
    print("  ⚠️ MAIDEN RACE (DLW='Mdn') - neutral DLWFactor")
    print()
    print("=" * 60)
    print()
    
    predictor.train_track_ensembles(
        pdf_dir='data_test',
        csv_dir='data_test',
        output_dir='models/track_ensemble_test'
    )
    
    print()
    print("=" * 60)
    print("✅ TEST TRAINING COMPLETE!")
    print("=" * 60)
    print()
    print("Models saved to: models/track_ensemble_test/")
    print()
    
except Exception as e:
    print()
    print("=" * 60)
    print("❌ ERROR DURING TRAINING")
    print("=" * 60)
    print()
    print(f"Error: {str(e)}")
    print()
    import traceback
    traceback.print_exc()
    sys.exit(1)
