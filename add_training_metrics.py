#!/usr/bin/env python3
"""
add_training_metrics.py
=======================
Generates training_metrics.json and metadata.json for each track in the
models/ subdirectory layout (produced by reorganize_models_by_track.py).

For each models/{TRACK}/ directory it writes:
    training_metrics.json  — model stats (n_estimators, feature count, etc.)
    metadata.json          — track metadata (name, algorithms present, date)

Usage:
    python add_training_metrics.py
    python add_training_metrics.py --models-dir models
"""

import argparse
import json
import os
import sys
import warnings
from datetime import datetime

warnings.filterwarnings("ignore")

MODELS_DIR = "models"


def _load_pkl(path: str):
    """Load a pickle file; return None on failure."""
    try:
        import pickle
        with open(path, "rb") as f:
            return pickle.load(f)
    except Exception:
        return None


def get_model_stats(model, algo: str) -> dict:
    """Extract basic statistics from a loaded model object."""
    stats: dict = {"algorithm": algo, "type": type(model).__name__}

    try:
        # CalibratedClassifierCV wrapper
        if hasattr(model, "calibrated_classifiers_"):
            stats["calibrated"] = True
            cals = model.calibrated_classifiers_
            if cals:
                base = (
                    cals[0].estimator
                    if hasattr(cals[0], "estimator")
                    else getattr(cals[0], "base_estimator", None)
                )
                if base is not None:
                    stats["base_type"] = type(base).__name__
                    if hasattr(base, "n_estimators"):
                        stats["n_estimators"] = int(base.n_estimators)
                    if hasattr(base, "max_depth"):
                        stats["max_depth"] = base.max_depth
        else:
            stats["calibrated"] = False
            if hasattr(model, "n_estimators"):
                stats["n_estimators"] = int(model.n_estimators)
            if hasattr(model, "max_depth"):
                stats["max_depth"] = model.max_depth

        # Feature count
        if hasattr(model, "n_features_in_"):
            stats["n_features"] = int(model.n_features_in_)
        elif hasattr(model, "calibrated_classifiers_") and model.calibrated_classifiers_:
            base = (
                model.calibrated_classifiers_[0].estimator
                if hasattr(model.calibrated_classifiers_[0], "estimator")
                else getattr(model.calibrated_classifiers_[0], "base_estimator", None)
            )
            if base is not None and hasattr(base, "n_features_in_"):
                stats["n_features"] = int(base.n_features_in_)

    except Exception as e:
        stats["stats_error"] = str(e)

    return stats


def get_scaler_stats(scaler) -> dict:
    """Extract basic statistics from a StandardScaler."""
    stats: dict = {"type": type(scaler).__name__}
    try:
        if hasattr(scaler, "n_features_in_"):
            stats["n_features"] = int(scaler.n_features_in_)
        if hasattr(scaler, "mean_") and scaler.mean_ is not None:
            stats["n_features"] = int(len(scaler.mean_))
    except Exception as e:
        stats["stats_error"] = str(e)
    return stats


def process_track(track_dir: str, track_name: str, dry_run: bool = False) -> bool:
    """Generate metrics files for one track directory.

    Returns True if at least one model was successfully loaded.
    """
    algos_found = []
    generated_at = datetime.utcnow().isoformat()
    metrics = {"track": track_name, "algorithms": {}, "generated_at": generated_at}

    for algo in ["rf", "gb", "xgb"]:
        path = os.path.join(track_dir, f"{algo}.pkl")
        if not os.path.exists(path):
            continue
        model = _load_pkl(path)
        if model is None:
            metrics["algorithms"][algo] = {"error": "Failed to load model"}
            continue
        metrics["algorithms"][algo] = get_model_stats(model, algo)
        algos_found.append(algo)

    scaler_path = os.path.join(track_dir, "scaler.pkl")
    if os.path.exists(scaler_path):
        scaler = _load_pkl(scaler_path)
        if scaler is not None:
            metrics["scaler"] = get_scaler_stats(scaler)

    if not algos_found:
        print(f"    [WARN] No models loaded for {track_name}")
        return False

    metrics["n_algorithms"] = len(algos_found)
    metrics["algorithms_present"] = algos_found

    metadata = {
        "track": track_name,
        "algorithms_present": algos_found,
        "scaler_present": os.path.exists(scaler_path),
        "generated_at": generated_at,
    }

    metrics_path = os.path.join(track_dir, "training_metrics.json")
    metadata_path = os.path.join(track_dir, "metadata.json")

    print(f"    Algorithms: {algos_found}")
    if not dry_run:
        with open(metrics_path, "w") as f:
            json.dump(metrics, f, indent=2)
        with open(metadata_path, "w") as f:
            json.dump(metadata, f, indent=2)
        print(f"    Written: training_metrics.json, metadata.json")
    else:
        print(f"    DRY-RUN: would write training_metrics.json, metadata.json")

    return True


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Add training_metrics.json and metadata.json to each track subdirectory."
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be done without writing files.",
    )
    parser.add_argument(
        "--models-dir",
        default=MODELS_DIR,
        help=f"Path to the models directory (default: {MODELS_DIR})",
    )
    args = parser.parse_args()

    models_dir = args.models_dir
    dry_run = args.dry_run

    print("=" * 60)
    print(" ADD TRAINING METRICS")
    print("=" * 60)
    if dry_run:
        print(" DRY-RUN mode — no files will be written")
    print(f" Models directory: {os.path.abspath(models_dir)}")
    print("=" * 60)

    if not os.path.isdir(models_dir):
        print(f"\n[ERROR] Models directory not found: {models_dir}")
        sys.exit(1)

    # Find track subdirectories
    track_dirs = [
        d for d in sorted(os.listdir(models_dir))
        if os.path.isdir(os.path.join(models_dir, d))
    ]

    if not track_dirs:
        print(
            "\n[ERROR] No subdirectories found in models/.\n"
            "        Run reorganize_models_by_track.py first."
        )
        sys.exit(1)

    print(f"\n  Found {len(track_dirs)} track subdirectories.\n")

    ok = 0
    for track_name in track_dirs:
        track_dir = os.path.join(models_dir, track_name)
        print(f"  [{ok + 1}/{len(track_dirs)}] {track_name}")
        success = process_track(track_dir, track_name, dry_run)
        if success:
            ok += 1

    print("\n" + "=" * 60)
    if dry_run:
        print(f" DRY-RUN complete — {ok}/{len(track_dirs)} tracks would be updated.")
    else:
        print(f" DONE — {ok}/{len(track_dirs)} tracks updated with metrics.")
    print("=" * 60)

    if ok == 0:
        sys.exit(1)


if __name__ == "__main__":
    main()
