"""
Validate Pipeline
=================
Checks that all required pipeline components are present and correct:

1. models/config.pkl  – ensemble configuration
2. models/{track}/    – track subdirectories with rf.pkl, gb.pkl, xgb.pkl, scaler.pkl
3. data_predictions/  – PDF files to predict on
4. src/               – required source modules

Outputs:
    outputs/pipeline_validation_report.json  – full report
    Console summary
"""

import os
import sys
import json
import pickle
from datetime import datetime


MODELS_DIR = "models"
DATA_PREDICTIONS_DIR = "data_predictions"
SRC_DIR = "src"
OUTPUT_DIR = "outputs"
ALGORITHMS = ["rf", "gb", "xgb"]
REQUIRED_SRC_MODULES = ["parser.py", "features.py"]


def validate_config(models_dir):
    """Validate models/config.pkl."""
    result = {"status": "ok", "issues": []}
    config_path = os.path.join(models_dir, "config.pkl")

    if not os.path.exists(config_path):
        result["status"] = "error"
        result["issues"].append(f"config.pkl not found at {config_path}")
        return result, None

    try:
        with open(config_path, "rb") as f:
            config = pickle.load(f)

        result["tracks"] = config.get("tracks", [])
        result["algorithms"] = config.get("algorithms", [])
        result["n_features"] = len(config.get("feature_cols", []))
        result["model_structure"] = config.get("model_structure", "unknown")
        result["training_date"] = config.get("training_date", "unknown")

        if not config.get("tracks"):
            result["issues"].append("No tracks defined in config.pkl")
        if not config.get("feature_cols"):
            result["issues"].append("No feature_cols defined in config.pkl")

    except Exception as exc:
        result["status"] = "error"
        result["issues"].append(f"Failed to load config.pkl: {exc}")
        return result, None

    return result, config


def validate_track_models(models_dir, config):
    """Validate that each track has the expected model files."""
    result = {"status": "ok", "tracks": {}, "issues": []}
    tracks = config.get("tracks", []) if config else []

    for track_name in tracks:
        track_dir = os.path.join(models_dir, track_name)
        track_info = {"status": "ok", "files": {}, "issues": []}

        if not os.path.exists(track_dir):
            track_info["status"] = "missing"
            track_info["issues"].append(f"Track directory not found: {track_dir}")
            result["issues"].append(f"Missing track directory: {track_name}")
            result["tracks"][track_name] = track_info
            continue

        for alg in ALGORITHMS:
            model_path = os.path.join(track_dir, f"{alg}.pkl")
            if os.path.exists(model_path):
                track_info["files"][alg] = {
                    "present": True,
                    "size_kb": round(os.path.getsize(model_path) / 1024, 1),
                }
            else:
                track_info["files"][alg] = {"present": False}
                track_info["issues"].append(f"Missing {alg}.pkl")

        scaler_path = os.path.join(track_dir, "scaler.pkl")
        track_info["files"]["scaler"] = {
            "present": os.path.exists(scaler_path),
            "size_kb": round(os.path.getsize(scaler_path) / 1024, 1)
            if os.path.exists(scaler_path)
            else 0,
        }

        if track_info["issues"]:
            track_info["status"] = "incomplete"
            result["issues"] += track_info["issues"]

        result["tracks"][track_name] = track_info

    # Count tracks with full model sets
    full_tracks = sum(
        1
        for t in result["tracks"].values()
        if t["status"] == "ok"
    )
    result["full_tracks"] = full_tracks
    result["total_tracks_in_config"] = len(tracks)

    if full_tracks == 0:
        result["status"] = "error"
        result["issues"].insert(0, "No tracks have a complete model set!")

    return result


def validate_data_predictions(data_dir):
    """Check for prediction PDFs."""
    result = {"status": "ok", "pdfs": [], "issues": []}

    if not os.path.exists(data_dir):
        result["status"] = "error"
        result["issues"].append(f"data_predictions/ directory not found: {data_dir}")
        return result

    pdfs = [f for f in os.listdir(data_dir) if f.lower().endswith(".pdf")]
    result["pdfs"] = sorted(pdfs)
    result["count"] = len(pdfs)

    if not pdfs:
        result["status"] = "warning"
        result["issues"].append("No PDF files found in data_predictions/")

    return result


def validate_src(src_dir):
    """Check required source modules are present."""
    result = {"status": "ok", "modules": {}, "issues": []}

    for module in REQUIRED_SRC_MODULES:
        path = os.path.join(src_dir, module)
        present = os.path.exists(path)
        result["modules"][module] = {"present": present}
        if not present:
            result["issues"].append(f"Missing source module: {path}")
            result["status"] = "error"

    return result


def main():
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    print("\n" + "=" * 60)
    print("🔍 PIPELINE VALIDATION")
    print("=" * 60)

    report = {
        "generated_at": datetime.now().isoformat(),
        "sections": {},
    }

    # 1. Validate config
    print("\n[1/4] Validating models/config.pkl...")
    config_result, config = validate_config(MODELS_DIR)
    report["sections"]["config"] = config_result
    if config_result["status"] == "ok":
        print(f"   ✅ Config OK: {len(config_result.get('tracks', []))} tracks, "
              f"{config_result.get('n_features', 0)} features")
    else:
        print(f"   ❌ Config ERRORS: {config_result['issues']}")

    # 2. Validate track models
    print("\n[2/4] Validating track model subdirectories...")
    model_result = validate_track_models(MODELS_DIR, config)
    report["sections"]["models"] = model_result
    full = model_result["full_tracks"]
    total = model_result["total_tracks_in_config"]
    if model_result["status"] == "ok":
        print(f"   ✅ Models OK: {full}/{total} tracks have complete model sets")
    else:
        print(f"   ⚠️  Models INCOMPLETE: {full}/{total} tracks complete")
        for issue in model_result["issues"][:10]:
            print(f"      - {issue}")

    # 3. Validate data_predictions
    print("\n[3/4] Validating data_predictions/ folder...")
    data_result = validate_data_predictions(DATA_PREDICTIONS_DIR)
    report["sections"]["data_predictions"] = data_result
    if data_result["status"] == "ok":
        print(f"   ✅ PDFs found: {data_result['count']} file(s)")
        for pdf in data_result["pdfs"]:
            print(f"      {pdf}")
    elif data_result["status"] == "warning":
        print(f"   ⚠️  No PDFs in data_predictions/ (add PDFs to generate predictions)")
    else:
        print(f"   ❌ {data_result['issues']}")

    # 4. Validate src modules
    print("\n[4/4] Validating src/ modules...")
    src_result = validate_src(SRC_DIR)
    report["sections"]["src"] = src_result
    if src_result["status"] == "ok":
        print(f"   ✅ All required src modules present")
    else:
        for issue in src_result["issues"]:
            print(f"   ❌ {issue}")

    # Overall status
    statuses = [s["status"] for s in report["sections"].values()]
    if "error" in statuses:
        overall = "error"
    elif "warning" in statuses or "incomplete" in statuses:
        overall = "warning"
    else:
        overall = "ok"

    report["overall_status"] = overall

    # Save report
    report_path = os.path.join(OUTPUT_DIR, "pipeline_validation_report.json")
    with open(report_path, "w") as f:
        json.dump(report, f, indent=2)

    print("\n" + "=" * 60)
    status_icon = {"ok": "✅", "warning": "⚠️", "error": "❌"}.get(overall, "?")
    print(f"{status_icon} OVERALL STATUS: {overall.upper()}")
    print(f"📄 Full report: {report_path}")
    print("=" * 60)

    return 0 if overall != "error" else 1


if __name__ == "__main__":
    sys.exit(main())
