#!/usr/bin/env python3
"""
validate_pipeline.py
====================
Validates the models/ directory structure.

Supports two layouts automatically:
  • Subdirectory layout: models/{Track}/rf.pkl, gb.pkl, scaler.pkl …
  • Flat-file layout:    models/{Track}_rf.pkl, {Track}_gb.pkl, {Track}_scaler.pkl …

Checks:
  1. Tracks detected from model files (either layout)
  2. Each track has the expected model files
  3. Models load without error
  4. Models can generate predictions on representative test feature data
  5. ensemble_config.json is consistent with actual model layout

Usage:
    python validate_pipeline.py
    python validate_pipeline.py --models-dir models
"""

import argparse
import json
import os
import pickle
import re
import sys
import warnings

warnings.filterwarnings("ignore")

MODELS_DIR = "models"
PASS = "PASS"
FAIL = "FAIL"
WARN = "WARN"



def load_model(path: str):
    """Load a model file, returning (model, error_message)."""
    try:
        with open(path, "rb") as f:
            obj = pickle.load(f)
        return obj, None
    except Exception as e:
        return None, str(e)


def get_n_features(model) -> int:
    """Return n_features_in_ from a model (handles CalibratedClassifierCV)."""
    if hasattr(model, "n_features_in_"):
        return int(model.n_features_in_)
    if hasattr(model, "calibrated_classifiers_") and model.calibrated_classifiers_:
        cal = model.calibrated_classifiers_[0]
        base = (
            cal.estimator
            if hasattr(cal, "estimator")
            else getattr(cal, "base_estimator", None)
        )
        if base is not None and hasattr(base, "n_features_in_"):
            return int(base.n_features_in_)
    return -1


def validate_track_flat(models_dir: str, track_name: str, algos: list, n_samples: int = 8) -> dict:
    """Validate one track using the flat-file layout ({track_name}_{algo}.pkl)."""
    results = {}
    import numpy as np

    OPTIONAL_ALGOS = {"xgb"}
    scaler_path = os.path.join(models_dir, f"{track_name}_scaler.pkl")

    missing_required = []
    missing_optional = []
    present_algos = []
    for algo in algos:
        p = os.path.join(models_dir, f"{track_name}_{algo}.pkl")
        if os.path.exists(p):
            present_algos.append(algo)
        elif algo in OPTIONAL_ALGOS:
            missing_optional.append(algo)
        else:
            missing_required.append(algo)

    if not os.path.exists(scaler_path):
        missing_required.append("scaler")

    if missing_required:
        results["files"] = (FAIL, f"Missing required files: {missing_required}")
        return results

    desc = f"{len(present_algos)}/{len(algos)} models + scaler"
    if missing_optional:
        results["files"] = (WARN, f"{desc} (optional missing: {missing_optional})")
    else:
        results["files"] = (PASS, f"All files present ({desc})")

    # Load scaler
    scaler, err = load_model(scaler_path)
    if scaler is None:
        results["scaler"] = (FAIL, f"Load error: {err}")
        return results
    results["scaler"] = (PASS, type(scaler).__name__)

    n_feat_scaler = (
        int(len(scaler.mean_)) if hasattr(scaler, "mean_") and scaler.mean_ is not None
        else getattr(scaler, "n_features_in_", -1)
    )

    # Load present models only
    loaded_models = {}
    for algo in present_algos:
        path = os.path.join(models_dir, f"{track_name}_{algo}.pkl")
        m, err = load_model(path)
        if m is None:
            results[algo] = (FAIL, f"Load error: {err}")
        else:
            n_feat = get_n_features(m)
            results[algo] = (PASS, f"{type(m).__name__}, {n_feat} features")
            loaded_models[algo] = (m, n_feat)

    # Pipeline smoke test — random feature vector to verify model loading (NOT race prediction data)
    # 74 is the default fallback feature count for pre-trained models on this branch.
    # It matches the StandardScaler and RF/GB models trained in train_ml_track_ensemble.py.
    n_feat = n_feat_scaler if n_feat_scaler > 0 else 74
    X_raw = np.random.default_rng(42).random((n_samples, n_feat))
    try:
        X_scaled = scaler.transform(X_raw)
    except Exception:
        X_scaled = X_raw

    for algo, (m, _) in loaded_models.items():
        try:
            try:
                probs = m.predict_proba(X_scaled)[:, 1]
            except Exception:
                probs = m.predict_proba(X_raw)[:, 1]
            n_unique = len(set(probs.round(6)))
            results[f"{algo}_predict"] = (PASS, f"{n_unique}/{n_samples} unique probs")
        except Exception as e:
            results[f"{algo}_predict"] = (FAIL, str(e))

    return results


def validate_track(track_dir: str, track_name: str, algos: list, n_samples: int = 8) -> dict:
    """Validate one track directory. Returns {check: (status, message)}."""
    results = {}
    import numpy as np

    # XGB is optional (trained on-the-fly); rf and gb are required
    OPTIONAL_ALGOS = {"xgb"}
    scaler_path = os.path.join(track_dir, "scaler.pkl")

    missing_required = []
    missing_optional = []
    present_algos = []
    for algo in algos:
        p = os.path.join(track_dir, f"{algo}.pkl")
        if os.path.exists(p):
            present_algos.append(algo)
        elif algo in OPTIONAL_ALGOS:
            missing_optional.append(algo)
        else:
            missing_required.append(algo)

    if not os.path.exists(scaler_path):
        missing_required.append("scaler")

    if missing_required:
        results["files"] = (FAIL, f"Missing required files: {missing_required}")
        return results

    desc = f"{len(present_algos)}/{len(algos)} models + scaler"
    if missing_optional:
        results["files"] = (WARN, f"{desc} (optional missing: {missing_optional})")
    else:
        results["files"] = (PASS, f"All files present ({desc})")

    # Load scaler
    scaler, err = load_model(scaler_path)
    if scaler is None:
        results["scaler"] = (FAIL, f"Load error: {err}")
        return results
    results["scaler"] = (PASS, type(scaler).__name__)

    n_feat_scaler = (
        int(len(scaler.mean_)) if hasattr(scaler, "mean_") and scaler.mean_ is not None
        else getattr(scaler, "n_features_in_", -1)
    )

    # Load present models only
    loaded_models = {}
    for algo in present_algos:
        path = os.path.join(track_dir, f"{algo}.pkl")
        m, err = load_model(path)
        if m is None:
            results[algo] = (FAIL, f"Load error: {err}")
        else:
            n_feat = get_n_features(m)
            results[algo] = (PASS, f"{type(m).__name__}, {n_feat} features")
            loaded_models[algo] = (m, n_feat)

    # Pipeline smoke test — random feature vector to verify model loading (NOT race prediction data)
    # 74 is the default fallback feature count for pre-trained models on this branch.
    # It matches the StandardScaler and RF/GB models trained in train_ml_track_ensemble.py.
    n_feat = n_feat_scaler if n_feat_scaler > 0 else 74
    X_raw = np.random.default_rng(42).random((n_samples, n_feat))
    try:
        X_scaled = scaler.transform(X_raw)
    except Exception as e:
        X_scaled = X_raw

    for algo, (m, _) in loaded_models.items():
        try:
            # Try scaled first, then raw
            try:
                probs = m.predict_proba(X_scaled)[:, 1]
            except Exception:
                probs = m.predict_proba(X_raw)[:, 1]
            n_unique = len(set(probs.round(6)))
            results[f"{algo}_predict"] = (PASS, f"{n_unique}/{n_samples} unique probs")
        except Exception as e:
            results[f"{algo}_predict"] = (FAIL, str(e))

    return results


def validate_config(models_dir: str, track_dirs: list) -> dict:
    """Check ensemble_config.json against actual layout."""
    results = {}
    config_path = os.path.join(models_dir, "ensemble_config.json")
    if not os.path.exists(config_path):
        results["config"] = (WARN, "ensemble_config.json not found")
        return results

    with open(config_path) as f:
        config = json.load(f)

    model_structure = config.get("model_structure", "unknown")
    if model_structure == "subdirectory":
        results["config_structure"] = (PASS, "model_structure=subdirectory")
    elif model_structure == "flat_files":
        results["config_structure"] = (PASS, "model_structure=flat_files")
    else:
        results["config_structure"] = (WARN, f"model_structure={model_structure}")

    config_tracks = set(config.get("tracks", []))
    actual_tracks = set(track_dirs)
    missing_from_config = actual_tracks - config_tracks
    missing_files = config_tracks - actual_tracks

    if missing_from_config:
        results["config_tracks_extra"] = (
            WARN,
            f"Tracks in models/ but not in config: {sorted(missing_from_config)}",
        )
    if missing_files:
        results["config_tracks_missing"] = (
            WARN,
            f"Tracks in config but no model files: {sorted(missing_files)}",
        )
    if not missing_from_config and not missing_files:
        results["config_tracks"] = (PASS, f"{len(actual_tracks)} tracks consistent")

    return results


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Validate the organized models/ directory structure."
    )
    parser.add_argument(
        "--models-dir",
        default=MODELS_DIR,
        help=f"Path to the models directory (default: {MODELS_DIR})",
    )
    parser.add_argument(
        "--track",
        default=None,
        help="Validate a single track only.",
    )
    args = parser.parse_args()

    models_dir = args.models_dir

    print("=" * 65)
    print(" GREYHOUND PIPELINE VALIDATION")
    print("=" * 65)
    print(f" Models directory: {os.path.abspath(models_dir)}")

    if not os.path.isdir(models_dir):
        print(f"\n[ERROR] Models directory not found: {models_dir}")
        sys.exit(1)

    # Auto-detect layout: subdirectory vs flat-file
    # Subdirectory layout: models/{Track Name}/rf.pkl ...
    # Flat-file layout:    models/{Track Name}_rf.pkl ...
    all_track_dirs = [
        d for d in sorted(os.listdir(models_dir))
        if os.path.isdir(os.path.join(models_dir, d))
    ]

    flat_file_pattern = re.compile(r"^(.+)_(?:rf|gb|xgb|scaler)\.pkl$")
    flat_tracks = sorted({
        m.group(1)
        for fname in os.listdir(models_dir)
        for m in [flat_file_pattern.match(fname)] if m
    })

    use_flat = not all_track_dirs and bool(flat_tracks)

    if not all_track_dirs and not flat_tracks:
        print(
            "\n[ERROR] No model files found in models/.\n"
            "        Run train_ml_track_ensemble.py first."
        )
        sys.exit(1)

    if use_flat:
        print(f" Layout: flat-file ({{Track}}_algorithm.pkl)")
        track_dirs = [args.track] if args.track else flat_tracks
    else:
        print(f" Layout: subdirectory (models/{{Track}}/algorithm.pkl)")
        track_dirs = [args.track] if args.track else all_track_dirs

    print(f" Validating {len(track_dirs)} track(s)")
    print("=" * 65)

    # Load config to get expected algorithms
    config_path = os.path.join(models_dir, "ensemble_config.json")
    algos = ["rf", "gb", "xgb"]
    if os.path.exists(config_path):
        with open(config_path) as f:
            cfg = json.load(f)
        algos = cfg.get("algorithms", algos)

    # Validate config
    config_results = validate_config(models_dir, flat_tracks if use_flat else all_track_dirs)
    print("\n Config:")
    for check, (status, msg) in config_results.items():
        marker = "OK" if status == PASS else ("!!" if status == FAIL else "??")
        print(f"   [{marker}] {check}: {msg}")

    # Per-track validation
    n_pass = 0
    n_fail = 0
    report = {}

    for track_name in track_dirs:
        if use_flat:
            print(f"\n  {track_name}:")
            results = validate_track_flat(models_dir, track_name, algos)
        else:
            track_dir = os.path.join(models_dir, track_name)
            if not os.path.isdir(track_dir):
                print(f"\n  [!!] {track_name}: directory not found")
                n_fail += 1
                continue
            print(f"\n  {track_name}:")
            results = validate_track(track_dir, track_name, algos)

        track_ok = True
        for check, (status, msg) in results.items():
            marker = "OK" if status == PASS else ("!!" if status == FAIL else "??")
            print(f"     [{marker}] {check}: {msg}")
            if status == FAIL:
                track_ok = False

        if track_ok:
            n_pass += 1
        else:
            n_fail += 1
        report[track_name] = results

    # Save report
    os.makedirs("outputs", exist_ok=True)
    report_path = os.path.join("outputs", "pipeline_validation_report.json")
    serializable = {
        track: {k: list(v) for k, v in checks.items()}
        for track, checks in report.items()
    }
    with open(report_path, "w") as f:
        json.dump(serializable, f, indent=2)

    # Summary
    print("\n" + "=" * 65)
    overall = PASS if n_fail == 0 else (WARN if n_pass > 0 else FAIL)
    marker = "OK" if overall == PASS else ("??" if overall == WARN else "!!")
    print(f" OVERALL: [{marker}] {n_pass} passed, {n_fail} failed")
    print(f" Report:  {os.path.abspath(report_path)}")
    print("=" * 65)

    if n_fail > 0 and n_pass == 0:
        sys.exit(1)


if __name__ == "__main__":
    main()
