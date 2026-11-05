#!/usr/bin/env python3
"""Discover stable winner indicators and interaction combos from historical races.

Outputs (in --output-dir):
- winner_indicator_profiles_candidate.json
- winner_indicator_profiles.json (active, only updated when gate passes)
- WINNER_INDICATOR_REPORT.md

Purpose:
- Identify per-track indicators and combos that historically improve winner selection
- Validate stability with walk-forward tests
- Provide soft sample-weight boosts for training (not hard rules)
"""

from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List

import numpy as np
import pandas as pd

from src.ml_predictor import load_historical_data_hybrid


def distance_bucket(series: pd.Series) -> pd.Series:
    d = pd.to_numeric(series, errors="coerce").fillna(500)
    return pd.cut(d, bins=[-np.inf, 399.999, 550.0, np.inf], labels=["SPRINT", "MIDDLE", "LONG"]).astype(str)


def safe_norm_track(v) -> str:
    return str(v).strip().lower()


def build_study_df() -> pd.DataFrame:
    race_data_list, winners_list = load_historical_data_hybrid()

    rows: List[pd.DataFrame] = []
    for race_df, winner_info in zip(race_data_list, winners_list):
        if race_df is None or race_df.empty:
            continue

        # Keep only true winner-labeled races for this analysis
        if isinstance(winner_info, dict):
            if int(winner_info.get("position", 0)) != 1:
                continue
            winner_box = int(winner_info.get("box", 0))
        else:
            winner_box = int(winner_info)

        r = race_df.copy()
        if "RaceNumber" not in r.columns:
            continue

        r["WinnerLabel"] = (pd.to_numeric(r.get("Box"), errors="coerce") == winner_box).astype(int)
        rows.append(r)

    if not rows:
        return pd.DataFrame()

    df = pd.concat(rows, ignore_index=True)

    # Standard fields
    if "Date" not in df.columns and "RaceDate" in df.columns:
        df["Date"] = df["RaceDate"]
    if "Date" not in df.columns:
        df["Date"] = ""
    df["Date"] = pd.to_datetime(df["Date"], errors="coerce")
    df["TrackNorm"] = df["Track"].map(safe_norm_track)
    df["DistanceBucket"] = distance_bucket(df.get("Distance", pd.Series([500] * len(df))))
    df["FieldSize"] = df.groupby(["TrackNorm", "RaceNumber", "Date"], dropna=False)["DogName"].transform("count")
    df["FieldBucket"] = pd.cut(df["FieldSize"], bins=[0, 6, 7, 20], labels=["SMALL", "MEDIUM", "FULL"]).astype(str)

    # Per-race ranking indicators
    race_keys = ["TrackNorm", "RaceNumber", "Date"]
    desc_rank_features = [
        "BestTimePercentile",
        "EarlySpeedPercentile",
        "TrainerStrikeRate",
        "TrainerMomentum",
        "ConsistencyIndex",
        "TrackBoxWinRatePct",
    ]
    asc_rank_features = ["InterferenceRisk"]

    for col in desc_rank_features:
        if col in df.columns:
            df[f"rank_{col}"] = df.groupby(race_keys, dropna=False)[col].rank(ascending=False, method="min")
    for col in asc_rank_features:
        if col in df.columns:
            df[f"rank_{col}"] = df.groupby(race_keys, dropna=False)[col].rank(ascending=True, method="min")

    # Binary indicator conditions
    df["inside_box"] = pd.to_numeric(df.get("Box"), errors="coerce").fillna(99).astype(int) <= 2
    df["recent_win_form"] = (
        (pd.to_numeric(df.get("DLW"), errors="coerce") <= 14)
        | (pd.to_numeric(df.get("Last3FinishFactor"), errors="coerce") >= 1.08)
    ).fillna(False)
    df["strong_trainer"] = (
        (pd.to_numeric(df.get("TrainerStrikeRate"), errors="coerce") >= 0.20)
        | (pd.to_numeric(df.get("TrainerMomentum"), errors="coerce") >= 1.06)
    ).fillna(False)
    df["high_consistency"] = (pd.to_numeric(df.get("ConsistencyIndex"), errors="coerce") >= 0.20).fillna(False)
    df["low_interference"] = (pd.to_numeric(df.get("InterferenceRisk"), errors="coerce") <= 0.40).fillna(False)
    df["pace_edge"] = (pd.to_numeric(df.get("PaceBoxFactor"), errors="coerce") >= 1.02).fillna(False)
    df["strong_box_bias"] = (pd.to_numeric(df.get("TrackBoxWinRatePct"), errors="coerce") >= 15.0).fillna(False)

    # Top-rank flags
    def _has_rank(c: str) -> bool:
        return c in df.columns

    df["top_speed"] = (df["rank_BestTimePercentile"] == 1) if _has_rank("rank_BestTimePercentile") else False
    df["top_early"] = (df["rank_EarlySpeedPercentile"] == 1) if _has_rank("rank_EarlySpeedPercentile") else False
    df["top_trainer"] = (df["rank_TrainerStrikeRate"] == 1) if _has_rank("rank_TrainerStrikeRate") else False
    df["top_trainer_momentum"] = (df["rank_TrainerMomentum"] == 1) if _has_rank("rank_TrainerMomentum") else False
    df["top_box_bias"] = (df["rank_TrackBoxWinRatePct"] == 1) if _has_rank("rank_TrackBoxWinRatePct") else False
    df["low_risk_rank"] = (df["rank_InterferenceRisk"] == 1) if _has_rank("rank_InterferenceRisk") else False

    # Interaction combos
    df["combo_early_inside_recent"] = df["top_early"] & df["inside_box"] & df["recent_win_form"]
    df["combo_trainer_consistency_lowrisk"] = (
        (df["strong_trainer"] | df["top_trainer"] | df["top_trainer_momentum"])
        & df["high_consistency"]
        & (df["low_interference"] | df["low_risk_rank"])
    )
    df["combo_speed_boxbias_lowrisk"] = df["top_speed"] & (df["strong_box_bias"] | df["top_box_bias"]) & (df["low_interference"] | df["low_risk_rank"])

    return df


def eval_condition(df: pd.DataFrame, cond_col: str) -> Dict[str, float]:
    baseline = float(df["WinnerLabel"].mean()) if len(df) else 0.0
    active = df[df[cond_col] == True]  # noqa: E712
    support = int(len(active))
    if support == 0:
        return {"support": 0, "win_rate": 0.0, "baseline": baseline, "lift": 0.0}
    wr = float(active["WinnerLabel"].mean())
    return {
        "support": support,
        "win_rate": wr,
        "baseline": baseline,
        "lift": wr - baseline,
    }


def walk_forward_stability(track_df: pd.DataFrame, cond_col: str) -> Dict[str, float]:
    sdf = track_df.dropna(subset=["Date"]).sort_values("Date")
    if len(sdf) < 120:
        return {"folds": 0, "avg_lift": 0.0, "positive_folds": 0, "min_support": 0}

    dates = sorted(sdf["Date"].dropna().unique())
    if len(dates) < 12:
        return {"folds": 0, "avg_lift": 0.0, "positive_folds": 0, "min_support": 0}

    cuts = [0.50, 0.70, 0.85]
    lifts = []
    supports = []
    positives = 0
    for c in cuts:
        i = min(max(int(len(dates) * c), 2), len(dates) - 2)
        cut_date = dates[i]
        next_i = min(i + max(1, int(len(dates) * 0.10)), len(dates) - 1)
        end_date = dates[next_i]
        test = sdf[(sdf["Date"] > cut_date) & (sdf["Date"] <= end_date)]
        m = eval_condition(test, cond_col)
        if m["support"] > 0:
            lifts.append(m["lift"])
            supports.append(m["support"])
            if m["lift"] > 0:
                positives += 1

    if not lifts:
        return {"folds": 0, "avg_lift": 0.0, "positive_folds": 0, "min_support": 0}

    return {
        "folds": len(lifts),
        "avg_lift": float(np.mean(lifts)),
        "positive_folds": int(positives),
        "min_support": int(min(supports) if supports else 0),
    }


def choose_boost(lift: float, stable_avg_lift: float) -> float:
    score = 0.6 * lift + 0.4 * stable_avg_lift
    if score >= 0.06:
        return 1.16
    if score >= 0.04:
        return 1.12
    if score >= 0.025:
        return 1.08
    return 1.04


def build_candidate(df: pd.DataFrame) -> dict:
    condition_cols = [
        "top_speed",
        "top_early",
        "recent_win_form",
        "strong_trainer",
        "high_consistency",
        "strong_box_bias",
        "low_interference",
        "combo_early_inside_recent",
        "combo_trainer_consistency_lowrisk",
        "combo_speed_boxbias_lowrisk",
    ]

    per_track = {}
    for track, tdf in sorted(df.groupby("TrackNorm")):
        if len(tdf) < 160:
            continue

        race_count = int(tdf[["Date", "RaceNumber"]].drop_duplicates().shape[0])
        base = float(tdf["WinnerLabel"].mean())

        singles = {}
        boosts = {}
        stable_combo_names = []

        for cond in condition_cols:
            m = eval_condition(tdf, cond)
            wf = walk_forward_stability(tdf, cond)
            if m["support"] < 25 or wf["folds"] < 2:
                continue

            keep = (m["lift"] >= 0.015 and wf["avg_lift"] >= 0.006 and wf["positive_folds"] >= 2)
            if not keep:
                continue

            singles[cond] = {
                "support": m["support"],
                "win_rate": round(m["win_rate"], 4),
                "baseline": round(m["baseline"], 4),
                "lift": round(m["lift"], 4),
                "wf_avg_lift": round(wf["avg_lift"], 4),
                "wf_positive_folds": wf["positive_folds"],
                "wf_folds": wf["folds"],
            }

            boosts[cond] = choose_boost(m["lift"], wf["avg_lift"])
            if cond.startswith("combo_"):
                stable_combo_names.append(cond)

        if not singles:
            continue

        # quality score for promotion gate
        weighted_lift = np.mean([v["lift"] * np.log1p(v["support"]) for v in singles.values()])
        quality = float(weighted_lift)

        per_track[track] = {
            "races": race_count,
            "baseline_win_rate": round(base, 4),
            "quality_score": round(quality, 5),
            "top_indicators": dict(sorted(singles.items(), key=lambda kv: kv[1]["lift"], reverse=True)[:8]),
            "stable_combinations": sorted(stable_combo_names),
            "sample_weight_boosts": boosts,
        }

    # global summary
    all_qualities = [v.get("quality_score", 0.0) for v in per_track.values()]
    global_quality = float(np.mean(all_qualities)) if all_qualities else 0.0

    return {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "track_count": len(per_track),
        "global_quality_score": round(global_quality, 5),
        "per_track": per_track,
    }


def gate_decision(candidate: dict, active: dict | None):
    c_tracks = int(candidate.get("track_count", 0))
    c_quality = float(candidate.get("global_quality_score", 0.0))

    if not active:
        return True, "PASS (no previous indicator profile baseline)", c_tracks, c_quality, 0, 0.0

    p_tracks = int(active.get("track_count", 0))
    p_quality = float(active.get("global_quality_score", 0.0))

    not_worse = (c_tracks >= max(1, p_tracks - 2)) and (c_quality >= p_quality - 0.002)
    improved = (c_quality >= p_quality + 0.001) or (c_tracks >= p_tracks + 1)
    ok = bool(not_worse and improved)
    reason = "PASS (indicator profile improves/maintains stability)" if ok else "FAIL (candidate indicator profile not stable enough; keep previous)"
    return ok, reason, c_tracks, c_quality, p_tracks, p_quality


def write_report(path: Path, gate_ok: bool, reason: str, c_tracks: int, c_quality: float, p_tracks: int, p_quality: float, active: dict):
    lines = [
        "# Winner Indicator Stability Report",
        "",
        f"- Gate result: **{'PASS' if gate_ok else 'FAIL'}**",
        f"- Reason: {reason}",
        "",
        "## Candidate vs Previous",
        f"- Candidate tracks with stable profiles: {c_tracks}",
        f"- Candidate global quality score: {c_quality:.5f}",
        f"- Previous tracks with stable profiles: {p_tracks}",
        f"- Previous global quality score: {p_quality:.5f}",
        "",
        "## Active track profiles",
    ]

    for track, v in sorted((active or {}).get("per_track", {}).items()):
        lines.append(
            f"- {track}: quality={v.get('quality_score',0):.5f}, races={v.get('races',0)}, combos={len(v.get('stable_combinations',[]))}, indicators={len(v.get('top_indicators',{}))}"
        )

    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--output-dir", default="best_bets_reports")
    args = ap.parse_args()

    out = Path(args.output_dir)
    out.mkdir(parents=True, exist_ok=True)

    df = build_study_df()
    if df.empty:
        raise SystemExit("No study data available for winner-indicator profile generation.")

    candidate = build_candidate(df)

    candidate_path = out / "winner_indicator_profiles_candidate.json"
    active_path = out / "winner_indicator_profiles.json"
    report_path = out / "WINNER_INDICATOR_REPORT.md"

    candidate_path.write_text(json.dumps(candidate, indent=2), encoding="utf-8")

    active = None
    if active_path.exists():
        try:
            active = json.loads(active_path.read_text(encoding="utf-8"))
        except Exception:
            active = None

    gate_ok, reason, c_tracks, c_quality, p_tracks, p_quality = gate_decision(candidate, active)

    if gate_ok:
        active = candidate
        active_path.write_text(json.dumps(candidate, indent=2), encoding="utf-8")

    write_report(report_path, gate_ok, reason, c_tracks, c_quality, p_tracks, p_quality, active or {"per_track": {}})

    print(f"Wrote candidate: {candidate_path}")
    print(f"Active profile: {active_path} ({'updated' if gate_ok else 'unchanged'})")
    print(f"Wrote report: {report_path}")
    print(f"Gate: {'PASS' if gate_ok else 'FAIL'} - {reason}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
