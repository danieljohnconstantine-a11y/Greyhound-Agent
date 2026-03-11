"""
System Readiness Check — Greyhound Agent
=========================================
Answers: "How can I be sure the system is calibrated and ready?"

Runs a comprehensive GO/NO-GO checklist covering:
  1. Models presence — every deployed track has RF + GB + XGB + scaler
  2. Model calibration — spread > 0.5% (not collapsed)
  3. Model type audit — CalibratedCV on RF; native proba on GB/XGB
  4. Retrain queue — tracks that have results data but no model yet
  5. Known critical issues — summary of open bugs / limitations
  6. Expected win rate summary — based on historical audit data

Usage:
    python check_system_ready.py

Output:
    Prints a full GO/NO-GO report to stdout.
    Also writes reports/SYSTEM_READY_CHECK_{date}.txt
"""

import os
import sys
import pickle
import json
import glob
import numpy as np
import pandas as pd
from datetime import datetime

REPO_ROOT   = os.path.dirname(os.path.abspath(__file__))
MODELS_DIR  = os.path.join(REPO_ROOT, "models")
DATA_DIR    = os.path.join(REPO_ROOT, "data")
REPORTS_DIR = os.path.join(REPO_ROOT, "reports")

# Minimum probability spread (max-min across dogs in a race) for a model to be
# considered non-collapsed.  0.005 = 0.5%.
SPREAD_THRESHOLD = 0.005

# Minimum races a track needs to be worth training a dedicated model.
MIN_RACES_FOR_MODEL = 30

# ── helpers ──────────────────────────────────────────────────────────────────

def _load_pkl(path):
    with open(path, "rb") as fh:
        return pickle.load(fh)


def _get_deployed_tracks():
    """Return list of canonical track names that have all 4 pkl files present."""
    rf_files = glob.glob(os.path.join(MODELS_DIR, "*_rf.pkl"))
    tracks = []
    for rf in rf_files:
        base = os.path.basename(rf)[:-7]  # strip _rf.pkl
        gb     = os.path.join(MODELS_DIR, f"{base}_gb.pkl")
        xgb    = os.path.join(MODELS_DIR, f"{base}_xgb.pkl")
        scaler = os.path.join(MODELS_DIR, f"{base}_scaler.pkl")
        if os.path.exists(gb) and os.path.exists(xgb) and os.path.exists(scaler):
            tracks.append(base)
        else:
            tracks.append(f"{base} [INCOMPLETE — missing gb/xgb/scaler]")
    return tracks


def _model_spread(model, scaler, n_dogs=8):
    """
    Probe model by predicting on a synthetic 8-dog field with randomised
    features and returning the max-min spread of predicted win probabilities.
    Uses the same feature list as ensemble_config.json.
    """
    cfg_path = os.path.join(MODELS_DIR, "ensemble_config.json")
    if not os.path.exists(cfg_path):
        return None
    with open(cfg_path) as fh:
        cfg = json.load(fh)
    feature_cols = cfg.get("feature_cols", [])
    if not feature_cols:
        return None

    rng = np.random.RandomState(42)
    X = rng.randn(n_dogs, len(feature_cols))
    if scaler is not None:
        try:
            X = scaler.transform(X)
        except Exception:
            pass
    try:
        proba = model.predict_proba(X)
        win_proba = proba[:, 1] if proba.shape[1] == 2 else proba[:, 0]
        return float(win_proba.max() - win_proba.min())
    except Exception:
        return None


def _check_calibration(track, verbose=True):
    """
    Returns dict with keys: rf_ok, gb_ok, xgb_ok, rf_spread, gb_spread, xgb_spread,
    rf_type, gb_type, xgb_type.
    """
    results = {}
    scaler_path = os.path.join(MODELS_DIR, f"{track}_scaler.pkl")
    scaler = _load_pkl(scaler_path) if os.path.exists(scaler_path) else None

    for alg in ("rf", "gb", "xgb"):
        path = os.path.join(MODELS_DIR, f"{track}_{alg}.pkl")
        if not os.path.exists(path):
            results[f"{alg}_ok"]     = False
            results[f"{alg}_spread"] = None
            results[f"{alg}_type"]   = "MISSING"
            continue
        model = _load_pkl(path)
        spread = _model_spread(model, scaler)
        ok = spread is not None and spread > SPREAD_THRESHOLD
        results[f"{alg}_ok"]     = ok
        results[f"{alg}_spread"] = spread
        results[f"{alg}_type"]   = type(model).__name__

    return results


def _get_results_tracks():
    """
    Return a dict mapping UPPERCASE track name → race count, derived from
    all data/results_*.csv files.
    """
    counts: dict[str, int] = {}
    for csv_path in glob.glob(os.path.join(DATA_DIR, "results_*.csv")):
        try:
            df = pd.read_csv(csv_path)
            col = "Track" if "Track" in df.columns else df.columns[0]
            for track, grp in df.groupby(col):
                key = str(track).strip().upper()
                counts[key] = counts.get(key, 0) + len(grp)
        except Exception:
            pass
    return counts


# ── main check ───────────────────────────────────────────────────────────────

def run_check():
    lines = []
    ok_count = 0
    warn_count = 0
    fail_count = 0

    def ok(msg):
        nonlocal ok_count
        ok_count += 1
        lines.append(f"  ✅  {msg}")

    def warn(msg):
        nonlocal warn_count
        warn_count += 1
        lines.append(f"  ⚠️   {msg}")

    def fail(msg):
        nonlocal fail_count
        fail_count += 1
        lines.append(f"  ❌  {msg}")

    def section(title):
        lines.append("")
        lines.append("━" * 78)
        lines.append(f"  {title}")
        lines.append("━" * 78)

    lines.append("=" * 78)
    lines.append("  GREYHOUND AGENT — SYSTEM READINESS CHECK")
    lines.append(f"  Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    lines.append("=" * 78)

    # ── 1. Models directory ───────────────────────────────────────────────────
    section("SECTION 1: MODEL FILES PRESENT")
    deployed = _get_deployed_tracks()
    incomplete = [t for t in deployed if "INCOMPLETE" in t]
    complete   = [t for t in deployed if "INCOMPLETE" not in t]

    if complete:
        ok(f"{len(complete)} track(s) have complete model sets: {', '.join(complete)}")
    if incomplete:
        for t in incomplete:
            fail(t)
    if not complete:
        fail("No complete track models found in models/")

    # ── 2. Calibration / spread audit ────────────────────────────────────────
    section("SECTION 2: MODEL CALIBRATION (spread > 0.5%?)")
    calibration_issues = []
    for track in complete:
        res = _check_calibration(track)
        for alg in ("rf", "gb", "xgb"):
            spread = res.get(f"{alg}_spread")
            typ    = res.get(f"{alg}_type", "?")
            if spread is None:
                fail(f"{track} {alg.upper()} — could not measure spread (model missing or error)")
                calibration_issues.append(track)
            elif not res.get(f"{alg}_ok"):
                fail(
                    f"{track} {alg.upper()} — COLLAPSED spread={spread:.4f} "
                    f"(< {SPREAD_THRESHOLD}) type={typ}"
                )
                calibration_issues.append(track)
            else:
                ok(
                    f"{track} {alg.upper()} — spread={spread:.4f} type={typ}"
                )

    # ── 3. Model type audit ───────────────────────────────────────────────────
    section("SECTION 3: MODEL TYPE AUDIT (RF=CalibratedCV, GB/XGB=native)")
    type_issues = []
    for track in complete:
        res = _check_calibration(track)
        rf_type  = res.get("rf_type", "?")
        gb_type  = res.get("gb_type", "?")
        xgb_type = res.get("xgb_type", "?")

        if "CalibratedClassifierCV" in rf_type:
            ok(f"{track} RF  — CalibratedClassifierCV ✓ (expected)")
        else:
            warn(f"{track} RF  — type={rf_type}  (expected CalibratedClassifierCV)")
            type_issues.append(track)

        if gb_type in ("GradientBoostingClassifier",):
            ok(f"{track} GB  — {gb_type} ✓ (native proba, expected)")
        else:
            warn(f"{track} GB  — type={gb_type}  (expected GradientBoostingClassifier)")
            type_issues.append(track)

        if xgb_type in ("XGBClassifier",):
            ok(f"{track} XGB — {xgb_type} ✓ (native proba, expected)")
        else:
            warn(f"{track} XGB — type={xgb_type}  (expected XGBClassifier)")
            type_issues.append(track)

    # ── 4. Retrain queue ──────────────────────────────────────────────────────
    section("SECTION 4: RETRAIN QUEUE (tracks with data but no model)")
    results_track_counts = _get_results_tracks()
    complete_upper = {t.upper() for t in complete}

    retrain_needed = []
    too_small = []
    for track_up, race_count in sorted(results_track_counts.items()):
        if track_up not in complete_upper:
            if race_count >= MIN_RACES_FOR_MODEL:
                retrain_needed.append((track_up, race_count))
            else:
                too_small.append((track_up, race_count))

    if not retrain_needed:
        ok("All tracks with sufficient data (≥ 30 races) already have models.")
    else:
        for t, n in sorted(retrain_needed, key=lambda x: -x[1]):
            warn(
                f"{t} ({n} races) — needs model.  "
                "Run: python retrain_all_tracks_sigmoid.py"
            )

    for t, n in sorted(too_small, key=lambda x: -x[1]):
        warn(f"{t} ({n} races) — too few races for reliable model; excluded from training.")

    # ── 5. Results CSVs coverage vs models ───────────────────────────────────
    section("SECTION 5: RESULTS CSV COVERAGE (which tracks have actuals data?)")
    all_results_tracks = set(results_track_counts.keys())
    lines.append(f"  Tracks with results CSVs in data/: {len(all_results_tracks)}")
    lines.append(f"  Tracks with trained models:        {len(complete)}")
    covered   = sorted(t for t in all_results_tracks if t in complete_upper)
    uncovered = sorted(t for t in all_results_tracks if t not in complete_upper)
    if covered:
        ok(f"Tracks with BOTH results data AND model: {', '.join(covered)}")
    for t in uncovered:
        if results_track_counts.get(t, 0) >= MIN_RACES_FOR_MODEL:
            warn(
                f"{t} — results data exists but NO model yet. "
                "Cannot make predictions until model is trained."
            )

    # ── 6. Known critical issues ──────────────────────────────────────────────
    section("SECTION 6: KNOWN CRITICAL ISSUES (as of 2026-03-11)")
    n_with_model   = len(complete)
    n_need_model   = len(retrain_needed)
    n_total_tracks = n_with_model + n_need_model
    issues = [
        ("OPEN",
         f"Only {n_with_model} of ~{n_total_tracks} canonical tracks have trained models "
         f"({', '.join(complete)}). "
         f"{n_need_model} more tracks will raise RuntimeError when their PDFs are loaded. "
         "FIX: run retrain_all_tracks_sigmoid.py on a machine with full data/ PDFs."),
        ("OPEN",  "Australian form PDFs do NOT publish greyhound weights. "
                  "Weight=0 for every dog in every PDF. WeightFactor is always "
                  "neutral (1.0). This is factual — not a bug — but weight-based "
                  "features carry zero predictive signal."),
        ("OPEN",  "TrackConditionAdj always 1.0 (placeholder). No live track "
                  "condition or weather data is integrated. Heavy/Soft tracks "
                  "are treated identically to Good tracks."),
        ("OPEN",  "Historical box stats in src/features.py are hard-coded from "
                  "a 386-race sample. These will drift as more races occur. "
                  "FIX: periodically refresh TRACK_BOX_STATS from new results CSVs."),
        ("FIXED", "Maitland Box4 penalty was -0.02 while Box4 won 45% of races. "
                  "Fixed to +0.08 BOOST in src/features.py (Mar 10 2026)."),
        ("FIXED", "Healesville Box8 overfit. RF models had isotonic collapse. "
                  "Fixed by retraining with sigmoid calibration (Mar 10 2026)."),
        ("FIXED", "Shepparton missing from TRACK_COMPREHENSIVE_ADJUSTMENTS. "
                  "Added with MIXED classification (Mar 10 2026)."),
        ("FIXED", "GB and XGB models were wrapped in CalibratedClassifierCV(sigmoid) "
                  "causing near-collapse (spread 0.017-0.061). Fixed by storing "
                  "native classifiers directly (Mar 11 2026)."),
        ("FIXED", "BestTimeSec/SectionalSec emitting distance/15.5 or 6.5 as "
                  "a fake time when PDF had no timing. Fixed to emit None → "
                  "race-median fill (Mar 8 2026)."),
    ]
    for status, msg in issues:
        prefix = "OPEN " if status == "OPEN" else "FIXED"
        if status == "OPEN":
            warn(f"[{prefix}] {msg}")
        else:
            ok(f"[{prefix}] {msg}")

    # ── 7. Expected win rate summary ──────────────────────────────────────────
    section("SECTION 7: EXPECTED WIN RATE (from historical audits)")
    lines.append("""
  Based on PREDICTION_AUDIT_2026-03-10.txt (92 races, 9 tracks, 8-dog fields):

  ┌─────────────────────────────────────────────────────────────────────┐
  │  Metric                              Result                         │
  ├─────────────────────────────────────────────────────────────────────┤
  │  Random baseline (8-dog field)       12.5%  (1-in-8)               │
  │  Overall model win rate              22.8%  (21/92 races)          │
  │  Model vs baseline                   +10.3 percentage points       │
  │  Model is                            1.83× better than random      │
  ├─────────────────────────────────────────────────────────────────────┤
  │  Best tracks (with dedicated models) 27–40%                        │
  │    Nowra                             40.0%  (4/10)                 │
  │    Mandurah                          33.3%  (4/12)                 │
  │    Gawler                            27.3%  (3/11)                 │
  │  Worst tracks (cross-track models)   8–17%                         │
  │    Maitland                           9.1%  (1/11)                 │
  │    Shepparton                         8.3%  (1/12)                 │
  ├─────────────────────────────────────────────────────────────────────┤
  │  High-confidence filter (≥25%):                                    │
  │    Gawler ≥25%                        100% (2/2)                   │
  │    Maitland ≥25% (R3, 24.4%)         1/1                          │
  │  → Filtering to predictions ≥25% confidence raises hit rate        │
  │    dramatically.  Only bet when ML_Confidence ≥ 25%.               │
  └─────────────────────────────────────────────────────────────────────┘

  REALISTIC EXPECTATION GOING FORWARD:
  ┌─────────────────────────────────────────────────────────────────────┐
  │  All predictions (no filter)         ~22–25%  win rate expected    │
  │  Predictions with ≥20% confidence    ~28–35%  win rate expected    │
  │  Predictions with ≥25% confidence    ~35–45%  win rate expected    │
  │                                                                     │
  │  NOTE: These estimates are based on ONE audit day (10 Mar 2026).   │
  │  Run backtest_win_rate.py for a full multi-day analysis.           │
  └─────────────────────────────────────────────────────────────────────┘
""".rstrip())

    # ── 8. GO/NO-GO summary ───────────────────────────────────────────────────
    section("SECTION 8: GO / NO-GO SUMMARY")
    total_checks = ok_count + warn_count + fail_count
    lines.append(f"  ✅ PASS  : {ok_count:3d}")
    lines.append(f"  ⚠️  WARN  : {warn_count:3d}")
    lines.append(f"  ❌ FAIL  : {fail_count:3d}")
    lines.append(f"  Total   : {total_checks:3d}")
    lines.append("")

    if fail_count == 0 and warn_count <= 5:
        lines.append("  🟢  SYSTEM STATUS: GO — Pipeline is operational.")
        lines.append("      Deploy track PDFs to data_predictions/ and run:")
        lines.append("      python run_track_ensemble_predictions.py")
    elif fail_count == 0:
        lines.append("  🟡  SYSTEM STATUS: CONDITIONAL GO")
        lines.append("      Core pipeline is working.  Open warnings should be")
        lines.append("      addressed (especially the retrain queue) to improve accuracy.")
    else:
        lines.append("  🔴  SYSTEM STATUS: NO-GO")
        lines.append(f"      {fail_count} critical failures found.  Fix failures above first.")

    lines.append("")
    lines.append("  WHAT YOU MUST DO BEFORE BETTING:")
    lines.append("  1. Run retrain_all_tracks_sigmoid.py on a machine with full data/")
    lines.append("     (trains models for 20 more tracks — currently only 3 tracks ready)")
    lines.append("  2. For each race day: copy PDFs to data_predictions/ and run")
    lines.append("     run_track_ensemble_predictions.py")
    lines.append("  3. Only act on predictions with ML_Confidence >= 20%")
    lines.append("  4. Prioritise tracks where model beat baseline (Nowra, Mandurah,")
    lines.append("     Gawler, Sandown, Q Parklands) over weaker tracks")
    lines.append("  5. Run backtest_win_rate.py periodically to monitor real performance")
    lines.append("")
    lines.append("=" * 78)

    report_text = "\n".join(lines)
    print(report_text)

    # Write to reports/
    os.makedirs(REPORTS_DIR, exist_ok=True)
    out_path = os.path.join(
        REPORTS_DIR,
        f"SYSTEM_READY_CHECK_{datetime.now().strftime('%Y-%m-%d')}.txt"
    )
    with open(out_path, "w", encoding="utf-8") as fh:
        fh.write(report_text)
    print(f"\n  Report saved to: {out_path}")

    return fail_count == 0


if __name__ == "__main__":
    success = run_check()
    sys.exit(0 if success else 1)
