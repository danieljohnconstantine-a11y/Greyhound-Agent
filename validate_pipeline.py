#!/usr/bin/env python3
"""
validate_pipeline.py

Model integrity check: ensure every configured track has RF/GB/XGB + scaler
and that each model can produce a probability from a dummy feature vector.
"""

from __future__ import annotations

import json
import pickle
import sys
from datetime import datetime
from pathlib import Path

import numpy as np
import pandas as pd


REPO_ROOT = Path(__file__).resolve().parent
MODELS_DIR = REPO_ROOT / "models"
OUTPUTS_DIR = REPO_ROOT / "outputs"


def _find_model_path(track: str, alg: str) -> Path | None:
    sub = MODELS_DIR / track / f"{alg}.pkl"
    if sub.exists():
        return sub
    flat = MODELS_DIR / f"{track}_{alg}.pkl"
    if flat.exists():
        return flat
    return None


def _find_scaler_path(track: str) -> Path | None:
    sub = MODELS_DIR / track / "scaler.pkl"
    if sub.exists():
        return sub
    flat = MODELS_DIR / f"{track}_scaler.pkl"
    if flat.exists():
        return flat
    return None


def main() -> int:
    config_path = MODELS_DIR / "config.pkl"
    if not config_path.exists():
        print(f"ERROR: Missing {config_path}")
        return 1

    with config_path.open("rb") as f:
        config = pickle.load(f)

    tracks = config.get("tracks", [])
    if isinstance(tracks, dict):
        tracks = list(tracks.keys())
    tracks = list(tracks)
    algorithms = list(config.get("algorithms", []))
    feature_cols = list(config.get("feature_cols", []))

    failures = []
    checked = []

    for track in tracks:
        scaler_path = _find_scaler_path(track)
        if scaler_path is None:
            failures.append({"track": track, "type": "missing_scaler"})
            continue

        try:
            with scaler_path.open("rb") as f:
                scaler = pickle.load(f)
        except Exception as exc:
            failures.append({"track": track, "type": "unloadable_scaler", "error": str(exc)})
            continue

        model_paths = {}
        missing_algs = []
        for alg in algorithms:
            model_path = _find_model_path(track, alg)
            if model_path is None:
                missing_algs.append(alg)
            else:
                model_paths[alg] = model_path
        if missing_algs:
            failures.append({"track": track, "type": "missing_models", "algorithms": missing_algs})
            continue

        cols = list(getattr(scaler, "feature_names_in_", feature_cols))
        if not cols:
            failures.append({"track": track, "type": "missing_feature_columns"})
            continue

        try:
            X = pd.DataFrame([np.zeros(len(cols), dtype=float)], columns=cols)
            X_scaled = scaler.transform(X)
        except Exception as exc:
            failures.append({"track": track, "type": "scaler_transform_failed", "error": str(exc)})
            continue

        track_ok = True
        for alg, path in model_paths.items():
            try:
                with path.open("rb") as f:
                    model = pickle.load(f)
                if not hasattr(model, "predict_proba"):
                    raise AttributeError("model has no predict_proba")
                probs = model.predict_proba(X_scaled)
                shape = getattr(probs, "shape", None)
                if not (shape and len(shape) == 2 and shape[0] == 1 and shape[1] >= 2):
                    raise ValueError(f"unexpected predict_proba shape: {shape}")
            except Exception as exc:
                track_ok = False
                failures.append(
                    {"track": track, "type": "model_inference_failed", "algorithm": alg, "path": str(path), "error": str(exc)}
                )
        if track_ok:
            checked.append(track)

    report = {
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "config_path": str(config_path),
        "tracks_in_config": len(tracks),
        "tracks_validated": len(checked),
        "failures": failures,
        "status": "PASS" if not failures else "FAIL",
    }

    OUTPUTS_DIR.mkdir(parents=True, exist_ok=True)
    out_path = OUTPUTS_DIR / "pipeline_validation_report.json"
    out_path.write_text(json.dumps(report, indent=2), encoding="utf-8")

    print(f"Validation report written: {out_path}")
    print(f"Tracks in config: {len(tracks)}")
    print(f"Tracks validated: {len(checked)}")
    print(f"Failures: {len(failures)}")
    print("PASS" if not failures else "FAIL")
    return 0 if not failures else 1


if __name__ == "__main__":
    raise SystemExit(main())
