#!/usr/bin/env python3
"""
reorganize_models_by_track.py
==============================
Reorganizes flat model files in models/ into per-track subdirectories.

Before:
    models/Angle Park_rf.pkl
    models/Angle Park_gb.pkl
    models/Angle Park_scaler.pkl
    models/BALLARAT_rf.pkl
    ...

After:
    models/Angle Park/rf.pkl
    models/Angle Park/gb.pkl
    models/Angle Park/scaler.pkl
    models/BALLARAT/rf.pkl
    ...

Also updates ensemble_config.json to reflect the new structure.

Usage:
    python reorganize_models_by_track.py
    python reorganize_models_by_track.py --dry-run
"""

import argparse
import json
import os
import re
import shutil
import sys


MODELS_DIR = "models"
SKIP_FILES = {"README.md", "config.pkl", "ensemble_config.json"}


def find_flat_model_files(models_dir: str) -> dict:
    """Return {track_name: {algo: filepath}} for all flat model files."""
    track_map: dict = {}
    for fname in os.listdir(models_dir):
        if fname in SKIP_FILES:
            continue
        m = re.match(r"^(.+?)_(rf|gb|xgb|scaler)\.pkl$", fname)
        if not m:
            continue
        track = m.group(1)
        algo = m.group(2)
        if track not in track_map:
            track_map[track] = {}
        track_map[track][algo] = os.path.join(models_dir, fname)
    return track_map


def reorganize(models_dir: str, dry_run: bool = False) -> int:
    """Move flat files into per-track subdirectories.

    Returns the number of tracks processed.
    """
    track_map = find_flat_model_files(models_dir)
    if not track_map:
        print("  No flat model files found — nothing to reorganize.")
        return 0

    processed = 0
    for track, algos in sorted(track_map.items()):
        track_dir = os.path.join(models_dir, track)
        print(f"\n  Track: {track}")
        print(f"    Destination: {track_dir}")

        if not dry_run:
            os.makedirs(track_dir, exist_ok=True)

        for algo, src_path in sorted(algos.items()):
            dst_path = os.path.join(track_dir, f"{algo}.pkl")
            action = "COPY" if dry_run else "Moving"
            print(f"    {action}: {os.path.basename(src_path)} -> {algo}.pkl")
            if not dry_run:
                shutil.copy2(src_path, dst_path)
                # Remove the original flat file after copying
                os.remove(src_path)

        processed += 1

    return processed


def update_ensemble_config(models_dir: str, tracks: list, dry_run: bool = False) -> None:
    """Update ensemble_config.json to reflect subdirectory layout."""
    config_path = os.path.join(models_dir, "ensemble_config.json")
    if not os.path.exists(config_path):
        print(f"\n  ensemble_config.json not found — skipping config update.")
        return

    with open(config_path, "r") as f:
        config = json.load(f)

    config["model_structure"] = "subdirectory"
    config["model_path_template"] = "models/{track_name}/{algorithm}.pkl"

    print(f"\n  Updating ensemble_config.json:")
    print(f"    model_structure  -> subdirectory")
    print(f"    model_path_template -> models/{{track_name}}/{{algorithm}}.pkl")

    if not dry_run:
        with open(config_path, "w") as f:
            json.dump(config, f, indent=2)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Reorganize flat model files into per-track subdirectories."
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be done without making changes.",
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
    print(" REORGANIZE MODELS BY TRACK")
    print("=" * 60)
    if dry_run:
        print(" DRY-RUN mode — no files will be changed")
    print(f" Models directory: {os.path.abspath(models_dir)}")
    print("=" * 60)

    if not os.path.isdir(models_dir):
        print(f"\n[ERROR] Models directory not found: {models_dir}")
        sys.exit(1)

    # Discover and move files
    track_map = find_flat_model_files(models_dir)
    if not track_map:
        # Check if already organized
        subdirs = [
            d for d in os.listdir(models_dir)
            if os.path.isdir(os.path.join(models_dir, d))
        ]
        if subdirs:
            print(f"\n  Models already organized into {len(subdirs)} subdirectories.")
            print("  Nothing to do.")
            return
        print("\n[ERROR] No model files found in models/")
        sys.exit(1)

    n_tracks = reorganize(models_dir, dry_run)
    update_ensemble_config(models_dir, list(track_map.keys()), dry_run)

    print("\n" + "=" * 60)
    if dry_run:
        print(f" DRY-RUN complete — {n_tracks} tracks would be reorganized.")
    else:
        print(f" DONE — {n_tracks} tracks reorganized into subdirectories.")
    print("=" * 60)


if __name__ == "__main__":
    main()
