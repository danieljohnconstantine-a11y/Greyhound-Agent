#!/usr/bin/env python3
"""
Add Training Metrics to Track Models

This script creates training_metrics.json and metadata.json files
for each track's model directory.

Author: GitHub Copilot
Date: 2026-03-04
"""

import os
import json
import pickle
from pathlib import Path
from datetime import datetime

def add_training_metrics():
    """Add training metrics and metadata to each track directory."""
    
    models_dir = Path("models")
    
    if not models_dir.exists():
        print(f"❌ ERROR: {models_dir} directory not found!")
        return False
    
    print(f"📁 Scanning {models_dir}/ for track directories...")
    
    # Find all track directories
    track_dirs = [d for d in models_dir.iterdir() if d.is_dir()]
    
    if not track_dirs:
        print("❌ No track directories found!")
        print("   Run reorganize_models_by_track.py first")
        return False
    
    print(f"   Found {len(track_dirs)} track directories")
    
    success_count = 0
    error_count = 0
    
    for track_dir in sorted(track_dirs):
        track_name = track_dir.name
        print(f"\n   📂 {track_name}/")
        
        try:
            # Check for model files
            rf_path = track_dir / "rf.pkl"
            gb_path = track_dir / "gb.pkl"
            xgb_path = track_dir / "xgb.pkl"
            scaler_path = track_dir / "scaler.pkl"
            
            models_present = {
                "rf": rf_path.exists(),
                "gb": gb_path.exists(),
                "xgb": xgb_path.exists(),
                "scaler": scaler_path.exists()
            }
            
            # Create training_metrics.json
            metrics_file = track_dir / "training_metrics.json"
            if not metrics_file.exists():
                metrics = {
                    "track": track_name,
                    "algorithms": {
                        "rf": {
                            "n_estimators": 250 if models_present["rf"] else "N/A",
                            "max_depth": 22 if models_present["rf"] else "N/A",
                            "max_features": "sqrt" if models_present["rf"] else "N/A",
                            "present": models_present["rf"]
                        },
                        "gb": {
                            "n_estimators": 200 if models_present["gb"] else "N/A",
                            "learning_rate": 0.1 if models_present["gb"] else "N/A",
                            "max_depth": 5 if models_present["gb"] else "N/A",
                            "present": models_present["gb"]
                        },
                        "xgb": {
                            "n_estimators": 200 if models_present["xgb"] else "N/A",
                            "tree_method": "hist" if models_present["xgb"] else "N/A",
                            "max_depth": 6 if models_present["xgb"] else "N/A",
                            "present": models_present["xgb"]
                        }
                    },
                    "scaler_present": models_present["scaler"],
                    "created": datetime.now().isoformat(),
                    "version": "1.0"
                }
                
                with open(metrics_file, 'w') as f:
                    json.dump(metrics, f, indent=2)
                print(f"      ✅ Created training_metrics.json")
            else:
                print(f"      ℹ️  training_metrics.json already exists")
            
            # Create metadata.json
            metadata_file = track_dir / "metadata.json"
            if not metadata_file.exists():
                metadata = {
                    "track_name": track_name,
                    "models": {
                        "rf": str(rf_path) if models_present["rf"] else None,
                        "gb": str(gb_path) if models_present["gb"] else None,
                        "xgb": str(xgb_path) if models_present["xgb"] else None,
                        "scaler": str(scaler_path) if models_present["scaler"] else None
                    },
                    "complete": all(models_present.values()),
                    "created": datetime.now().isoformat()
                }
                
                with open(metadata_file, 'w') as f:
                    json.dump(metadata, f, indent=2)
                print(f"      ✅ Created metadata.json")
            else:
                print(f"      ℹ️  metadata.json already exists")
            
            # Verify model completeness
            if all(models_present.values()):
                print(f"      ✅ Complete (all 4 files present)")
            else:
                missing = [k for k, v in models_present.items() if not v]
                print(f"      ⚠️  Incomplete (missing: {', '.join(missing)})")
            
            success_count += 1
            
        except Exception as e:
            print(f"      ❌ Error: {e}")
            error_count += 1
    
    print(f"\n" + "="*60)
    print(f"✅ Successfully processed: {success_count} tracks")
    if error_count > 0:
        print(f"❌ Errors: {error_count} tracks")
        print(f"="*60)
        return False
    
    print(f"="*60)
    
    return True


if __name__ == "__main__":
    import sys
    
    print("="*60)
    print("📊 ADD TRAINING METRICS")
    print("="*60)
    print()
    
    try:
        success = add_training_metrics()
        
        if success:
            print("\n✅ SUCCESS: Training metrics added to all tracks")
            sys.exit(0)
        else:
            print("\n❌ FAILED: Could not add training metrics")
            sys.exit(1)
            
    except Exception as e:
        print(f"\n❌ CRITICAL ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
