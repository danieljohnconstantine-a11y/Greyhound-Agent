#!/usr/bin/env python3
"""
Validate Complete Pipeline

This script validates that all models (RF, GB, XGB) can be loaded
and used for predictions.

Author: GitHub Copilot
Date: 2026-03-04
"""

import os
import json
import pickle
import numpy as np
from pathlib import Path
from datetime import datetime

def test_model_loading(model_path):
    """Test if a model can be loaded."""
    try:
        with open(model_path, 'rb') as f:
            model = pickle.load(f)
        return True, "OK"
    except Exception as e:
        return False, str(e)

def test_model_prediction(model, X_test):
    """Test if a model can make predictions."""
    try:
        predictions = model.predict(X_test)
        return True, f"Shape: {predictions.shape}"
    except Exception as e:
        return False, str(e)

def validate_pipeline():
    """Validate the complete prediction pipeline."""
    
    models_dir = Path("models")
    outputs_dir = Path("outputs")
    outputs_dir.mkdir(exist_ok=True)
    
    if not models_dir.exists():
        print(f"❌ ERROR: {models_dir} directory not found!")
        return False
    
    print(f"🔍 Validating pipeline...")
    print()
    
    # Find all track directories
    track_dirs = [d for d in models_dir.iterdir() if d.is_dir()]
    
    if not track_dirs:
        print("❌ No track directories found!")
        return False
    
    print(f"📊 Found {len(track_dirs)} tracks to validate")
    print()
    
    validation_results = {
        "timestamp": datetime.now().isoformat(),
        "total_tracks": len(track_dirs),
        "tracks": {}
    }
    
    complete_tracks = 0
    incomplete_tracks = 0
    working_tracks = 0
    
    for track_dir in sorted(track_dirs):
        track_name = track_dir.name
        print(f"📂 {track_name}/")
        
        track_result = {
            "track_name": track_name,
            "files_present": {},
            "models_loadable": {},
            "models_functional": {},
            "status": "unknown"
        }
        
        # Check file presence
        rf_path = track_dir / "rf.pkl"
        gb_path = track_dir / "gb.pkl"
        xgb_path = track_dir / "xgb.pkl"
        scaler_path = track_dir / "scaler.pkl"
        
        track_result["files_present"] = {
            "rf": rf_path.exists(),
            "gb": gb_path.exists(),
            "xgb": xgb_path.exists(),
            "scaler": scaler_path.exists()
        }
        
        # Check completeness
        if all(track_result["files_present"].values()):
            print(f"   ✅ All 4 files present")
            complete_tracks += 1
        else:
            missing = [k for k, v in track_result["files_present"].items() if not v]
            print(f"   ⚠️  Incomplete: missing {', '.join(missing)}")
            incomplete_tracks += 1
            track_result["status"] = "incomplete"
            validation_results["tracks"][track_name] = track_result
            continue
        
        # Test model loading
        models_to_test = [
            ("rf", rf_path),
            ("gb", gb_path),
            ("xgb", xgb_path),
            ("scaler", scaler_path)
        ]
        
        all_loaded = True
        loaded_models = {}
        
        for model_name, model_path in models_to_test:
            can_load, msg = test_model_loading(model_path)
            track_result["models_loadable"][model_name] = can_load
            
            if can_load:
                print(f"   ✅ {model_name}.pkl loads successfully")
                with open(model_path, 'rb') as f:
                    loaded_models[model_name] = pickle.load(f)
            else:
                print(f"   ❌ {model_name}.pkl failed to load: {msg}")
                all_loaded = False
        
        if not all_loaded:
            track_result["status"] = "load_failed"
            validation_results["tracks"][track_name] = track_result
            continue
        
        # Test model functionality with dummy data
        try:
            # Create dummy feature data (76 features as per the system)
            X_test = np.random.rand(5, 76)
            
            # Transform with scaler
            X_scaled = loaded_models["scaler"].transform(X_test)
            print(f"   ✅ Scaler transforms successfully")
            
            # Test each model
            for model_name in ["rf", "gb", "xgb"]:
                can_predict, msg = test_model_prediction(loaded_models[model_name], X_scaled)
                track_result["models_functional"][model_name] = can_predict
                
                if can_predict:
                    print(f"   ✅ {model_name} predicts successfully ({msg})")
                else:
                    print(f"   ❌ {model_name} prediction failed: {msg}")
                    all_loaded = False
            
            if all_loaded:
                print(f"   ✅ PIPELINE WORKING")
                track_result["status"] = "working"
                working_tracks += 1
            else:
                track_result["status"] = "prediction_failed"
                
        except Exception as e:
            print(f"   ❌ Pipeline test failed: {e}")
            track_result["status"] = "error"
            track_result["error"] = str(e)
        
        validation_results["tracks"][track_name] = track_result
        print()
    
    # Summary
    validation_results["summary"] = {
        "complete_tracks": complete_tracks,
        "incomplete_tracks": incomplete_tracks,
        "working_tracks": working_tracks,
        "success_rate": f"{(working_tracks/len(track_dirs)*100):.1f}%"
    }
    
    print("="*60)
    print("📊 VALIDATION SUMMARY")
    print("="*60)
    print(f"Total tracks: {len(track_dirs)}")
    print(f"✅ Complete tracks: {complete_tracks}")
    print(f"⚠️  Incomplete tracks: {incomplete_tracks}")
    print(f"✅ Working pipelines: {working_tracks}")
    print(f"Success rate: {validation_results['summary']['success_rate']}")
    print("="*60)
    
    # Save report
    report_file = outputs_dir / "pipeline_validation_report.json"
    with open(report_file, 'w') as f:
        json.dump(validation_results, f, indent=2)
    print(f"\n📄 Report saved to: {report_file}")
    
    return working_tracks == len(track_dirs)


if __name__ == "__main__":
    import sys
    
    print("="*60)
    print("🔬 PIPELINE VALIDATION")
    print("="*60)
    print()
    
    try:
        success = validate_pipeline()
        
        if success:
            print("\n✅ SUCCESS: All tracks validated")
            sys.exit(0)
        else:
            print("\n⚠️  WARNING: Some tracks have issues")
            print("   Check outputs/pipeline_validation_report.json for details")
            sys.exit(1)
            
    except Exception as e:
        print(f"\n❌ CRITICAL ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
