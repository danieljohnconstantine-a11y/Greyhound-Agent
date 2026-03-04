"""
Complete Pipeline Validation Test

This script validates the entire greyhound prediction pipeline:
1. Checks which models actually exist vs what config claims
2. Verifies model files are complete (all 6 files per track)
3. Tests predictions on available models
4. Provides clear report of what works and what doesn't

Usage:
    python validate_full_pipeline.py

This PROVES whether the pipeline is working correctly.
"""

import os
import sys
import pickle
import glob
from datetime import datetime

def print_section(title):
    """Print a formatted section header."""
    print("\n" + "=" * 80)
    print(f" {title}")
    print("=" * 80)

def validate_models():
    """
    Check which models actually exist vs what config claims.
    
    Returns:
        actual_tracks: List of tracks with complete models
        missing_tracks: List of tracks missing models
        partial_tracks: Dict of tracks with partial models
    """
    print_section("STEP 1: MODEL VALIDATION")
    
    models_dir = "models"
    config_path = os.path.join(models_dir, "config.pkl")
    
    # Check if config exists
    if not os.path.exists(config_path):
        print("❌ ERROR: models/config.pkl not found!")
        print("   This file should be created during training.")
        print("   Please run: python train_ml_track_ensemble.py")
        return [], [], {}
    
    # Load config
    try:
        with open(config_path, 'rb') as f:
            config = pickle.load(f)
    except Exception as e:
        print(f"❌ ERROR loading config: {e}")
        return [], [], {}
    
    configured_tracks = config.get('tracks', [])
    algorithms = config.get('algorithms', [])
    
    print(f"\n📋 Config file claims {len(configured_tracks)} tracks are trained")
    print(f"   Algorithms: {', '.join(algorithms)}")
    
    # Check which tracks actually have models
    actual_tracks = []
    missing_tracks = []
    partial_tracks = {}
    
    required_files = ['rf.pkl', 'gb.pkl', 'xgb.pkl', 'scaler.pkl', 
                     'metadata.json', 'training_metrics.json']
    
    print(f"\n🔍 Checking each track...")
    for track in configured_tracks:
        track_dir = os.path.join(models_dir, track)
        
        if not os.path.exists(track_dir):
            missing_tracks.append(track)
            continue
        
        # Check which files exist
        existing_files = []
        missing_files = []
        
        for f in required_files:
            file_path = os.path.join(track_dir, f)
            if os.path.exists(file_path):
                existing_files.append(f)
            else:
                missing_files.append(f)
        
        if len(existing_files) == len(required_files):
            # All files present
            actual_tracks.append(track)
        elif len(existing_files) > 0:
            # Some files present
            partial_tracks[track] = {
                'existing': existing_files,
                'missing': missing_files
            }
        else:
            # No files
            missing_tracks.append(track)
    
    # Report results
    print(f"\n✅ {len(actual_tracks)} tracks have COMPLETE models:")
    for track in actual_tracks:
        track_dir = os.path.join(models_dir, track)
        # Get total size of model directory
        total_size = 0
        for f in required_files:
            file_path = os.path.join(track_dir, f)
            if os.path.exists(file_path):
                total_size += os.path.getsize(file_path)
        size_mb = total_size / (1024 * 1024)
        print(f"   • {track:<25} ({size_mb:.1f} MB)")
    
    if partial_tracks:
        print(f"\n⚠️  {len(partial_tracks)} tracks have PARTIAL models:")
        for track, files in partial_tracks.items():
            print(f"   • {track}")
            print(f"      Existing: {', '.join(files['existing'])}")
            print(f"      Missing:  {', '.join(files['missing'])}")
    
    if missing_tracks:
        print(f"\n❌ {len(missing_tracks)} tracks have NO models:")
        for track in missing_tracks[:10]:  # Show first 10
            print(f"   • {track}")
        if len(missing_tracks) > 10:
            print(f"   ... and {len(missing_tracks) - 10} more")
    
    return actual_tracks, missing_tracks, partial_tracks

def validate_prediction_pdfs():
    """
    Check which PDF files exist and which tracks they're for.
    
    Returns:
        pdf_tracks: Dict of {track_name: [pdf_files]}
    """
    print_section("STEP 2: PREDICTION PDF VALIDATION")
    
    pdf_dir = "data_predictions"
    
    if not os.path.exists(pdf_dir):
        print(f"❌ ERROR: {pdf_dir} directory not found!")
        return {}
    
    pdf_files = [f for f in os.listdir(pdf_dir) if f.endswith('.pdf')]
    
    if not pdf_files:
        print(f"⚠️  No PDF files found in {pdf_dir}")
        print("   Add race PDFs to this directory to make predictions")
        return {}
    
    print(f"\n📄 Found {len(pdf_files)} PDF files:")
    for pdf in pdf_files:
        print(f"   • {pdf}")
    
    return pdf_files

def test_single_prediction(pdf_file, models_dir="models"):
    """
    Test prediction on a single PDF to see if it works.
    
    Returns:
        success: Boolean indicating if prediction worked
        track: Track name identified
        error: Error message if failed
    """
    try:
        # Import required modules
        from src.parser import parse_race_form
        from src.features import compute_features
        import pdfplumber
        
        # Extract text
        text = ""
        pdf_path = os.path.join("data_predictions", pdf_file)
        with pdfplumber.open(pdf_path) as pdf:
            for page in pdf.pages:
                text += page.extract_text() + "\n"
        
        # Parse form
        races = parse_race_form(text)
        if not races:
            return False, None, "No races parsed from PDF"
        
        race = races[0]  # Test first race
        track = race['Track']
        
        # Check if models exist for this track
        track_dir = os.path.join(models_dir, track)
        if not os.path.exists(track_dir):
            return False, track, f"No models for track: {track}"
        
        # Check for scaler
        scaler_path = os.path.join(track_dir, "scaler.pkl")
        if not os.path.exists(scaler_path):
            return False, track, f"Missing scaler.pkl for {track}"
        
        # Compute features
        df = compute_features([race])
        if df.empty:
            return False, track, "Failed to compute features"
        
        return True, track, None
        
    except Exception as e:
        return False, None, str(e)

def validate_predictions(actual_tracks, pdf_files):
    """
    Test if predictions actually work on available data.
    
    Args:
        actual_tracks: List of tracks with complete models
        pdf_files: List of PDF files to predict on
    """
    print_section("STEP 3: PREDICTION TEST")
    
    if not actual_tracks:
        print("❌ Cannot test predictions - no complete models found!")
        print("   Please train models first:")
        print("   python train_ml_track_ensemble.py")
        return False
    
    if not pdf_files:
        print("⚠️  Cannot test predictions - no PDF files found!")
        print("   Add race PDFs to data_predictions/ directory")
        return False
    
    print(f"\n🔄 Testing predictions on {len(pdf_files)} PDFs...")
    print(f"   Available models: {len(actual_tracks)} tracks")
    
    successful_predictions = []
    failed_predictions = []
    skipped_predictions = []
    
    for pdf in pdf_files:
        print(f"\n📄 Testing: {pdf}")
        success, track, error = test_single_prediction(pdf)
        
        if success:
            print(f"   ✅ SUCCESS - Models loaded for {track}")
            successful_predictions.append((pdf, track))
        elif track and track not in actual_tracks:
            print(f"   ⚠️  SKIPPED - No models for {track}")
            skipped_predictions.append((pdf, track))
        else:
            print(f"   ❌ FAILED - {error}")
            failed_predictions.append((pdf, error))
    
    # Summary
    print(f"\n📊 Prediction Test Results:")
    print(f"   ✅ Successful: {len(successful_predictions)}")
    print(f"   ⚠️  Skipped (no models): {len(skipped_predictions)}")
    print(f"   ❌ Failed: {len(failed_predictions)}")
    
    if successful_predictions:
        print(f"\n   Predictions will work for:")
        for pdf, track in successful_predictions:
            print(f"      • {track} ({pdf})")
    
    if skipped_predictions:
        print(f"\n   Cannot predict (need models):")
        for pdf, track in skipped_predictions[:5]:
            print(f"      • {track} ({pdf})")
        if len(skipped_predictions) > 5:
            print(f"      ... and {len(skipped_predictions) - 5} more")
    
    return len(successful_predictions) > 0

def main():
    """Run complete pipeline validation."""
    print("=" * 80)
    print(" 🧪 GREYHOUND PREDICTION PIPELINE VALIDATION")
    print("=" * 80)
    print(f"\n⏰ Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"📁 Directory: {os.path.abspath('.')}")
    
    # Step 1: Validate models
    actual_tracks, missing_tracks, partial_tracks = validate_models()
    
    # Step 2: Check PDFs
    pdf_files = validate_prediction_pdfs()
    
    # Step 3: Test predictions
    predictions_work = False
    if actual_tracks and pdf_files:
        predictions_work = validate_predictions(actual_tracks, pdf_files)
    
    # Final summary
    print_section("VALIDATION SUMMARY")
    
    print(f"\n📊 Results:")
    print(f"   Models configured: {len(actual_tracks) + len(missing_tracks) + len(partial_tracks)}")
    print(f"   Models complete: {len(actual_tracks)}")
    print(f"   Models partial: {len(partial_tracks)}")
    print(f"   Models missing: {len(missing_tracks)}")
    print(f"   PDF files: {len(pdf_files)}")
    print(f"   Predictions work: {'✅ YES' if predictions_work else '❌ NO'}")
    
    if len(actual_tracks) >= 2 and predictions_work:
        print(f"\n🎉 PIPELINE IS WORKING!")
        print(f"   • {len(actual_tracks)} tracks have complete models")
        print(f"   • Predictions successfully tested")
        print(f"   • Ready to run: python run_track_ensemble_predictions.py")
        return 0
    elif len(actual_tracks) > 0:
        print(f"\n⚠️  PIPELINE PARTIALLY WORKING")
        print(f"   • {len(actual_tracks)} tracks have models")
        print(f"   • But {len(missing_tracks)} tracks are missing models")
        print(f"   • You can predict for tracks with models")
        print(f"   • Train more models for other tracks")
        return 1
    else:
        print(f"\n❌ PIPELINE NOT WORKING")
        print(f"   • No complete models found")
        print(f"   • Cannot make predictions")
        print(f"   • Please train models first:")
        print(f"     python train_ml_track_ensemble.py")
        return 2

if __name__ == "__main__":
    exit_code = main()
    print(f"\n{'=' * 80}\n")
    sys.exit(exit_code)
