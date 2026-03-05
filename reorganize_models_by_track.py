"""
Reorganize Models By Track
==========================
Moves flat model files from models/ root into track-specific subdirectories.

Before: models/Angle Park_rf.pkl, models/BALLARAT_gb.pkl, ...
After:  models/Angle Park/rf.pkl, models/BALLARAT/gb.pkl, ...

This is required by ORGANIZE_ALL_TRACKS.bat and is a prerequisite for
run_track_ensemble_predictions.py which loads models from subdirectories.
"""

import os
import sys
import shutil
import json
import pickle
from datetime import datetime


MODELS_DIR = "models"
ALGORITHMS = ["rf", "gb", "xgb"]


def find_flat_model_files(models_dir):
    """
    Discover flat model files in models_dir.

    Flat naming convention:  {TrackName}_{algorithm}.pkl
                             {TrackName}_scaler.pkl

    Returns a dict: {track_name: {algorithm: filepath, 'scaler': filepath}}
    """
    tracks = {}

    for filename in os.listdir(models_dir):
        if not filename.endswith(".pkl"):
            continue
        filepath = os.path.join(models_dir, filename)
        if os.path.isdir(filepath):
            continue

        basename = filename[:-4]  # strip .pkl

        # Try to match against known algorithms
        matched = False
        for alg in ALGORITHMS:
            suffix = f"_{alg}"
            if basename.endswith(suffix):
                track_name = basename[: -len(suffix)]
                tracks.setdefault(track_name, {})[alg] = filepath
                matched = True
                break

        if not matched and basename.endswith("_scaler"):
            track_name = basename[: -len("_scaler")]
            tracks.setdefault(track_name, {})["scaler"] = filepath

    return tracks


def reorganize(models_dir=MODELS_DIR, dry_run=False):
    """
    Reorganize flat model files into track subdirectories.

    Returns:
        int: number of tracks reorganized
    """
    print(f"\n🗂️  Scanning {models_dir}/ for flat model files...")
    flat_tracks = find_flat_model_files(models_dir)

    if not flat_tracks:
        print("   ℹ️  No flat model files found – nothing to reorganize.")
        return 0

    print(f"   Found {len(flat_tracks)} track(s) with flat model files:")
    for track_name, files in flat_tracks.items():
        print(f"      {track_name}: {', '.join(sorted(files.keys()))}")

    organized = 0

    for track_name, files in flat_tracks.items():
        track_dir = os.path.join(models_dir, track_name)

        if not dry_run:
            os.makedirs(track_dir, exist_ok=True)

        print(f"\n   📁 {track_name}/ ← ", end="")
        moved = []

        for key, src_path in sorted(files.items()):
            # Destination: models/{track_name}/{algorithm}.pkl or scaler.pkl
            dst_filename = f"{key}.pkl"
            dst_path = os.path.join(track_dir, dst_filename)

            if dry_run:
                print(f"\n      [DRY-RUN] Would copy: {os.path.basename(src_path)} → {dst_path}")
                moved.append(key)
                continue

            if os.path.exists(dst_path):
                print(f"\n      ⏭️  Already exists: {dst_path} (skipping)")
            else:
                shutil.copy2(src_path, dst_path)
                moved.append(key)

        if moved:
            print(", ".join(moved))
            organized += 1

    if not dry_run and organized > 0:
        # Update config.pkl model_structure field if present
        config_path = os.path.join(models_dir, "config.pkl")
        if os.path.exists(config_path):
            with open(config_path, "rb") as f:
                config = pickle.load(f)

            config["model_structure"] = "track_subdirectories"
            config["model_path_template"] = "models/{track}/{algorithm}.pkl"
            config["reorganized_at"] = datetime.now().isoformat()

            with open(config_path, "wb") as f:
                pickle.dump(config, f)

            print(f"\n   ✅ Updated config.pkl: model_structure = track_subdirectories")

    print(f"\n✅ Reorganized {organized} track(s)")
    return organized


if __name__ == "__main__":
    dry_run = "--dry-run" in sys.argv
    if dry_run:
        print("🔍 DRY-RUN mode – no files will be moved")

    os.chdir(os.path.dirname(os.path.abspath(__file__)))

    count = reorganize(MODELS_DIR, dry_run=dry_run)

    if count == 0 and not dry_run:
        # Check if subdirectory structure already exists
        has_subdirs = any(
            os.path.isdir(os.path.join(MODELS_DIR, d))
            for d in os.listdir(MODELS_DIR)
        )
        if has_subdirs:
            print("   ℹ️  Track subdirectories already exist.")
            sys.exit(0)
        else:
            print("   ⚠️  No flat model files and no subdirectories found.")
            sys.exit(1)

    sys.exit(0)
