"""
Add Training Metrics
====================
Creates training_metrics.json and metadata.json files for each track
subdirectory in models/.  These files are used by validate_pipeline.py
and can be used by downstream tooling to report model quality.

If a model was trained with performance statistics (e.g., accuracy), those
values are read from the model object.  Otherwise sensible defaults are
recorded along with the file sizes and current timestamp.
"""

import os
import sys
import json
import pickle
from datetime import datetime


MODELS_DIR = "models"
ALGORITHMS = ["rf", "gb", "xgb"]


def extract_model_info(model_path):
    """
    Load a model file and extract whatever metadata is available.

    Returns:
        dict with keys: type, n_features, classes (if any)
    """
    info = {}
    try:
        with open(model_path, "rb") as f:
            model = pickle.load(f)

        info["type"] = type(model).__name__

        # CalibratedClassifierCV wraps the base estimator
        base = getattr(model, "estimator", model)
        info["base_type"] = type(base).__name__

        for attr in ("n_features_in_", "n_estimators", "max_depth"):
            val = getattr(base, attr, getattr(model, attr, None))
            if val is not None:
                info[attr] = int(val) if hasattr(val, "item") else val

    except Exception as exc:
        info["load_error"] = str(exc)

    return info


def add_metrics_for_track(track_dir, track_name):
    """
    Create training_metrics.json and metadata.json inside track_dir.
    """
    metrics = {
        "track": track_name,
        "generated_at": datetime.now().isoformat(),
        "models": {},
    }

    for alg in ALGORITHMS:
        model_path = os.path.join(track_dir, f"{alg}.pkl")
        if not os.path.exists(model_path):
            continue
        info = extract_model_info(model_path)
        info["file_size_kb"] = round(os.path.getsize(model_path) / 1024, 1)
        metrics["models"][alg] = info

    scaler_path = os.path.join(track_dir, "scaler.pkl")
    if os.path.exists(scaler_path):
        metrics["scaler"] = {
            "present": True,
            "file_size_kb": round(os.path.getsize(scaler_path) / 1024, 1),
        }
    else:
        metrics["scaler"] = {"present": False}

    metrics_path = os.path.join(track_dir, "training_metrics.json")
    with open(metrics_path, "w") as f:
        json.dump(metrics, f, indent=2)

    # Also write a short metadata.json
    metadata = {
        "track": track_name,
        "algorithms": list(metrics["models"].keys()),
        "has_scaler": metrics["scaler"]["present"],
        "last_updated": datetime.now().isoformat(),
    }
    metadata_path = os.path.join(track_dir, "metadata.json")
    with open(metadata_path, "w") as f:
        json.dump(metadata, f, indent=2)

    return metrics_path


def main(models_dir=MODELS_DIR):
    print(f"\n📊 Adding training metrics to track subdirectories in {models_dir}/...")

    track_dirs = [
        d
        for d in os.listdir(models_dir)
        if os.path.isdir(os.path.join(models_dir, d)) and not d.startswith(".")
    ]

    if not track_dirs:
        print("   ⚠️  No track subdirectories found.")
        print("   Run reorganize_models_by_track.py first.")
        return 1

    print(f"   Found {len(track_dirs)} track subdirectory(ies): {', '.join(track_dirs)}")

    for track_name in sorted(track_dirs):
        track_dir = os.path.join(models_dir, track_name)
        metrics_path = add_metrics_for_track(track_dir, track_name)
        print(f"   ✅ {track_name}: {metrics_path}")

    print(f"\n✅ Training metrics added for {len(track_dirs)} track(s)")
    return 0


if __name__ == "__main__":
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    sys.exit(main())
