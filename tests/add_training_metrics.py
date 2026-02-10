#!/usr/bin/env python3
"""
Add Training Metrics to Track Models

This script adds comprehensive training metrics to each track's model directory:
- Accuracy, Precision, Recall, F1 scores
- Feature importance rankings
- Sample counts and data quality metrics
- Cross-validation scores
"""

import json
import pickle
import os
from pathlib import Path
from datetime import datetime
import numpy as np

def add_metrics_to_track(track_dir):
    """Add training metrics to a track directory"""
    track_name = track_dir.name
    print(f"\n📊 Adding metrics for {track_name}...")
    
    metrics = {
        "track_name": track_name,
        "generated_at": datetime.now().isoformat(),
        "models": {},
        "ensemble_performance": {},
        "data_quality": {},
        "feature_importance": {}
    }
    
    # Load each model and extract metrics
    model_files = {
        "rf": "rf.pkl",
        "gb": "gb.pkl", 
        "xgb": "xgb.pkl"
    }
    
    for model_name, filename in model_files.items():
        model_path = track_dir / filename
        if model_path.exists():
            try:
                with open(model_path, 'rb') as f:
                    model = pickle.load(f)
                
                # Extract model-specific metrics
                model_metrics = {
                    "type": model_name.upper(),
                    "n_estimators": getattr(model, 'n_estimators', 'N/A'),
                    "max_depth": getattr(model, 'max_depth', 'N/A'),
                    "n_features": getattr(model, 'n_features_in_', 'Unknown')
                }
                
                # Feature importance if available
                if hasattr(model, 'feature_importances_'):
                    importances = model.feature_importances_
                    top_5_indices = np.argsort(importances)[-5:][::-1]
                    model_metrics["top_5_features"] = [
                        {"rank": i+1, "importance": float(importances[idx])}
                        for i, idx in enumerate(top_5_indices)
                    ]
                
                metrics["models"][model_name] = model_metrics
                print(f"   ✅ Extracted metrics from {filename}")
                
            except Exception as e:
                print(f"   ⚠️  Could not load {filename}: {e}")
                metrics["models"][model_name] = {"error": str(e)}
    
    # Add placeholder performance metrics (to be filled by actual training)
    metrics["ensemble_performance"] = {
        "accuracy": "To be measured",
        "precision": "To be measured",
        "recall": "To be measured",
        "f1_score": "To be measured",
        "top_4_accuracy": "To be measured",
        "notes": "Run training with validation to populate these metrics"
    }
    
    # Add data quality metrics
    metrics["data_quality"] = {
        "total_samples": "Check training logs",
        "features_used": metrics["models"].get("rf", {}).get("n_features", "Unknown"),
        "missing_data_pct": "To be calculated",
        "outliers_removed": "To be calculated"
    }
    
    # Save metrics
    metrics_file = track_dir / "training_metrics.json"
    with open(metrics_file, 'w') as f:
        json.dump(metrics, f, indent=2)
    
    print(f"   💾 Saved metrics to {metrics_file.name}")
    return metrics

def main():
    print("=" * 80)
    print("ADDING TRAINING METRICS TO TRACK MODELS")
    print("=" * 80)
    
    models_dir = Path("models")
    
    # Find all track subdirectories
    track_dirs = [d for d in models_dir.iterdir() if d.is_dir() and d.name not in ['combined', '__pycache__']]
    
    if not track_dirs:
        print("\n❌ No track directories found in models/")
        print("   Run reorganize_models_by_track.py first")
        return
    
    print(f"\n📁 Found {len(track_dirs)} track directories")
    print("=" * 80)
    
    success_count = 0
    for track_dir in sorted(track_dirs):
        try:
            add_metrics_to_track(track_dir)
            success_count += 1
        except Exception as e:
            print(f"\n❌ Error processing {track_dir.name}: {e}")
    
    print("\n" + "=" * 80)
    print(f"✅ Successfully added metrics to {success_count}/{len(track_dirs)} tracks")
    print("=" * 80)
    
    print("\n📝 Metrics files created:")
    print("   Location: models/TRACK_NAME/training_metrics.json")
    print("   Contents: Model info, performance placeholders, data quality")
    print("\n💡 Next steps:")
    print("   1. Run training with validation to populate performance metrics")
    print("   2. Update metrics after each training run")
    print("   3. Use metrics for model comparison and tracking")

if __name__ == "__main__":
    main()
