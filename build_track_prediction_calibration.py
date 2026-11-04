#!/usr/bin/env python3
"""Build per-track calibration profiles from historical track_ensemble_predictions Excel files.

Outputs (in --output-dir):
- track_calibration_profiles_candidate.json
- track_calibration_profiles.json (active, only updated when gate passes)
- TRACK_CALIBRATION_REPORT.md

This script does NOT change Excel prediction format or daily runtime flow.
"""

from __future__ import annotations

import argparse
import json
import math
import re
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Tuple

import pandas as pd

from src.results_loader import load_results_dataframe

PRED_FILE_RE = re.compile(r"track_ensemble_predictions(\d{2})(\d{2})(\d{4})\.xlsx$", re.IGNORECASE)

TRACK_MAP = {
    "mt gambier": "mount gambier",
    "q parklands": "ladbrokes q2 parklands",
    "q lakeside": "ladbrokes q1 lakeside",
    "q straight": "ladbrokes q straight",
    "capalaba": "betdeluxe capalaba",
    "gardens": "ladbrokes gardens",
    "hobart": "launceston",
    "tasmania": "launceston",
    "bet nation townsville": "bet nation townsville",
    "betdeluxe rockhampton": "betdeluxe rockhampton",
    "rockhampton": "betdeluxe rockhampton",
    "murray bridge": "murray bridge straight",
}


def norm_track(name: str) -> str:
    key = re.sub(r"\s+", " ", str(name).strip().lower())
    return TRACK_MAP.get(key, key)


def parse_date_from_filename(path: Path) -> str | None:
    m = PRED_FILE_RE.search(path.name)
    if not m:
        return None
    dd, mm, yyyy = m.group(1), m.group(2), m.group(3)
    return f"{yyyy}-{mm}-{dd}"


def safe_int(v) -> int:
    s = str(v).strip().upper()
    if s.startswith("R"):
        s = s[1:]
    return int(float(s))


def safe_float(v) -> float:
    return float(str(v).strip())


def load_results(results_root: Path) -> Dict[Tuple[str, str, int], dict]:
    df = load_results_dataframe(data_dir=str(results_root / "data"), extra_dirs=None)
    if df.empty:
        # fallback manually from data* structure via results_loader in case data/ is sparse
        dfs = []
        for d in sorted(results_root.glob("data*")):
            try:
                part = load_results_dataframe(data_dir=str(d), extra_dirs=None)
                if not part.empty:
                    dfs.append(part)
            except Exception:
                continue
        df = pd.concat(dfs, ignore_index=True) if dfs else pd.DataFrame()

    rows: Dict[Tuple[str, str, int], Tuple[int, dict]] = {}
    for _, row in df.iterrows():
        date = str(row.get("Date", "")).strip()
        track = norm_track(row.get("Track", ""))
        try:
            race = safe_int(row.get("Race", row.get("RaceNumber", 0)))
        except Exception:
            continue

        winner = str(row.get("Winner", "")).strip().upper()
        second = str(row.get("2nd", "")).strip().upper()
        third = str(row.get("3rd", "")).strip().upper()

        if not (date and track and race):
            continue

        src = str(row.get("_source_file", ""))
        m = re.search(r"data(\d+)", src)
        data_num = int(m.group(1)) if m else 0

        k = (date, track, race)
        payload = {"winner": winner, "2nd": second, "3rd": third}
        prev = rows.get(k)
        if prev is None or data_num >= prev[0]:
            rows[k] = (data_num, payload)

    return {k: v[1] for k, v in rows.items()}


@dataclass
class TrackStats:
    track: str
    races: int = 0
    top_pick_wins: int = 0
    top_pick_top3: int = 0
    brier_sum: float = 0.0
    ece_sum: float = 0.0


def brier_for_race(preds: List[Tuple[int, float]], winner_box: str) -> float:
    total = 0.0
    n = 0
    for box, p in preds:
        y = 1.0 if str(box) == str(winner_box) else 0.0
        total += (p - y) ** 2
        n += 1
    return total / n if n else 0.0


def ece_for_race(preds: List[Tuple[int, float]], winner_box: str, bins: int = 10) -> float:
    # Dog-level ECE approximation for a single race
    bucket_sum = [0.0] * bins
    bucket_cnt = [0] * bins
    bucket_hit = [0.0] * bins

    for box, p in preds:
        b = min(int(p * bins), bins - 1)
        bucket_sum[b] += p
        bucket_cnt[b] += 1
        bucket_hit[b] += 1.0 if str(box) == str(winner_box) else 0.0

    total = sum(bucket_cnt)
    if total == 0:
        return 0.0

    ece = 0.0
    for i in range(bins):
        if bucket_cnt[i] == 0:
            continue
        conf = bucket_sum[i] / bucket_cnt[i]
        acc = bucket_hit[i] / bucket_cnt[i]
        ece += (bucket_cnt[i] / total) * abs(acc - conf)
    return ece


def choose_profile(top_pick_win_rate: float, top3_rate: float, brier: float, ece: float, races: int) -> str:
    if races < 20:
        return "conservative"
    if top_pick_win_rate >= 0.30 and top3_rate >= 0.58 and ece <= 0.10:
        return "aggressive"
    if top_pick_win_rate >= 0.25 and top3_rate >= 0.50 and ece <= 0.14:
        return "balanced"
    return "conservative"


def make_profile_params(profile: str) -> dict:
    if profile == "aggressive":
        return {
            "rf": {"n_estimators": 120, "max_depth": 10, "min_samples_split": 4},
            "gb": {"learning_rate": 0.11, "min_samples_leaf": 3, "subsample": 0.85},
            "xgb": {"n_estimators": 170, "learning_rate": 0.11, "max_depth": 4, "subsample": 0.85, "colsample_bytree": 0.85},
        }
    if profile == "balanced":
        return {
            "rf": {"n_estimators": 100, "max_depth": 10, "min_samples_split": 5},
            "gb": {"learning_rate": 0.10, "min_samples_leaf": 3, "subsample": 0.80},
            "xgb": {"n_estimators": 150, "learning_rate": 0.10, "max_depth": 4, "subsample": 0.80, "colsample_bytree": 0.80},
        }
    return {
        "rf": {"n_estimators": 90, "max_depth": 8, "min_samples_split": 8},
        "gb": {"learning_rate": 0.08, "min_samples_leaf": 5, "subsample": 0.75},
        "xgb": {"n_estimators": 120, "learning_rate": 0.08, "max_depth": 3, "subsample": 0.75, "colsample_bytree": 0.75},
    }


def weighted_summary(profiles: dict) -> dict:
    rows = profiles.get("per_track", {})
    total_races = sum(v.get("races", 0) for v in rows.values())
    if total_races == 0:
        return {"races": 0, "top_pick_win_rate": 0.0, "top3_rate": 0.0, "ece": 0.0}

    w_win = sum(v.get("top_pick_win_rate", 0.0) * v.get("races", 0) for v in rows.values()) / total_races
    w_top3 = sum(v.get("top3_rate", 0.0) * v.get("races", 0) for v in rows.values()) / total_races
    w_ece = sum(v.get("ece", 0.0) * v.get("races", 0) for v in rows.values()) / total_races
    return {"races": total_races, "top_pick_win_rate": w_win, "top3_rate": w_top3, "ece": w_ece}


def gate_decision(candidate: dict, active: dict | None) -> Tuple[bool, str, dict, dict]:
    cand = weighted_summary(candidate)
    prev = weighted_summary(active or {"per_track": {}})

    if prev["races"] == 0:
        return True, "PASS (no previous baseline)", cand, prev

    not_worse = (
        cand["top_pick_win_rate"] >= prev["top_pick_win_rate"] - 0.002
        and cand["top3_rate"] >= prev["top3_rate"] - 0.003
        and cand["ece"] <= prev["ece"] + 0.010
    )
    improved = (
        cand["top_pick_win_rate"] >= prev["top_pick_win_rate"] + 0.001
        or cand["top3_rate"] >= prev["top3_rate"] + 0.001
        or cand["ece"] <= prev["ece"] - 0.002
    )
    ok = bool(not_worse and improved)
    reason = "PASS (candidate improves/maintains walk-forward guardrails)" if ok else "FAIL (candidate did not beat promotion guardrails; keep previous calibration)"
    return ok, reason, cand, prev


def build_candidate(predictions_dir: Path, results: Dict[Tuple[str, str, int], dict]) -> dict:
    track_stats: Dict[str, TrackStats] = {}

    files = sorted(predictions_dir.glob("track_ensemble_predictions*.xlsx"))
    for p in files:
        date = parse_date_from_filename(p)
        if not date:
            continue

        try:
            df = pd.read_excel(p, sheet_name="Predictions")
        except Exception:
            df = pd.read_excel(p)

        required = {"Track", "RaceNumber", "Box", "ML_Confidence"}
        if not required.issubset(set(df.columns)):
            continue

        df = df.copy()
        df["TrackNorm"] = df["Track"].map(norm_track)

        for (track_norm, race_num), grp in df.groupby(["TrackNorm", "RaceNumber"]):
            try:
                race = safe_int(race_num)
            except Exception:
                continue

            result = results.get((date, track_norm, race))
            if not result:
                continue
            winner = str(result.get("winner", "")).strip().upper()
            p2 = str(result.get("2nd", "")).strip().upper()
            p3 = str(result.get("3rd", "")).strip().upper()

            race_preds = []
            for _, row in grp.iterrows():
                try:
                    box = safe_int(row["Box"])
                    prob = max(0.0, min(safe_float(row["ML_Confidence"]) / 100.0, 1.0))
                except Exception:
                    continue
                race_preds.append((box, prob))

            if not race_preds or not winner or winner == "ABD":
                continue

            race_preds_sorted = sorted(race_preds, key=lambda x: x[1], reverse=True)
            top_box = str(race_preds_sorted[0][0])

            st = track_stats.setdefault(track_norm, TrackStats(track=track_norm))
            st.races += 1
            if top_box == winner:
                st.top_pick_wins += 1
            if top_box in {winner, p2, p3}:
                st.top_pick_top3 += 1
            st.brier_sum += brier_for_race(race_preds, winner)
            st.ece_sum += ece_for_race(race_preds, winner)

    per_track = {}
    for track, st in sorted(track_stats.items()):
        if st.races == 0:
            continue
        top_win = st.top_pick_wins / st.races
        top3 = st.top_pick_top3 / st.races
        brier = st.brier_sum / st.races
        ece = st.ece_sum / st.races
        profile = choose_profile(top_win, top3, brier, ece, st.races)
        params = make_profile_params(profile)
        per_track[track] = {
            "races": st.races,
            "top_pick_win_rate": round(top_win, 4),
            "top3_rate": round(top3, 4),
            "brier": round(brier, 4),
            "ece": round(ece, 4),
            "recommended_profile": profile,
            **params,
        }

    return {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "source_predictions_dir": str(predictions_dir),
        "matched_tracks": len(per_track),
        "per_track": per_track,
    }


def write_report(out_path: Path, gate_ok: bool, gate_reason: str, cand_sum: dict, prev_sum: dict, active: dict):
    lines = [
        "# Track Calibration Promotion Report",
        "",
        f"- Gate result: **{'PASS' if gate_ok else 'FAIL'}**",
        f"- Reason: {gate_reason}",
        "",
        "## Weighted summary (race-weighted across tracks)",
        f"- Candidate races: {cand_sum.get('races',0)}",
        f"- Candidate top-pick win rate: {cand_sum.get('top_pick_win_rate',0.0)*100:.2f}%",
        f"- Candidate top-3 strike rate: {cand_sum.get('top3_rate',0.0)*100:.2f}%",
        f"- Candidate ECE: {cand_sum.get('ece',0.0):.4f}",
        "",
        f"- Previous races: {prev_sum.get('races',0)}",
        f"- Previous top-pick win rate: {prev_sum.get('top_pick_win_rate',0.0)*100:.2f}%",
        f"- Previous top-3 strike rate: {prev_sum.get('top3_rate',0.0)*100:.2f}%",
        f"- Previous ECE: {prev_sum.get('ece',0.0):.4f}",
        "",
        "## Active per-track profiles",
    ]
    for track, v in sorted(active.get("per_track", {}).items()):
        lines.append(
            f"- {track}: profile={v.get('recommended_profile')} | races={v.get('races')} | win={v.get('top_pick_win_rate',0)*100:.2f}% | top3={v.get('top3_rate',0)*100:.2f}% | ece={v.get('ece',0):.4f}"
        )
    out_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--predictions-dir", default="track_ensemble_predictions")
    ap.add_argument("--results-root", default=".")
    ap.add_argument("--output-dir", default="best_bets_reports")
    args = ap.parse_args()

    predictions_dir = Path(args.predictions_dir)
    results_root = Path(args.results_root)
    out_dir = Path(args.output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    results = load_results(results_root)
    candidate = build_candidate(predictions_dir, results)

    candidate_path = out_dir / "track_calibration_profiles_candidate.json"
    active_path = out_dir / "track_calibration_profiles.json"
    report_path = out_dir / "TRACK_CALIBRATION_REPORT.md"

    candidate_path.write_text(json.dumps(candidate, indent=2), encoding="utf-8")

    active = None
    if active_path.exists():
        try:
            active = json.loads(active_path.read_text(encoding="utf-8"))
        except Exception:
            active = None

    gate_ok, gate_reason, cand_sum, prev_sum = gate_decision(candidate, active)

    if gate_ok:
        active = candidate
        active_path.write_text(json.dumps(candidate, indent=2), encoding="utf-8")

    write_report(report_path, gate_ok, gate_reason, cand_sum, prev_sum, active or {"per_track": {}})

    print(f"Wrote candidate: {candidate_path}")
    print(f"Active profile: {active_path} ({'updated' if gate_ok else 'unchanged'})")
    print(f"Wrote report: {report_path}")
    print(f"Gate: {'PASS' if gate_ok else 'FAIL'} - {gate_reason}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
