#!/usr/bin/env python3
"""Generate RF/GB/XGB tuning overrides from historical best-bets reports."""

from __future__ import annotations

import argparse
import csv
import json
import re
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional, Tuple

REPORT_RE = re.compile(r"best_bets_report(\d{2})(\d{2})(\d{4})\.txt$")
ROW_RE = re.compile(
    r"^\s*\d+\s+(.+?)\s+R(\d{1,2})\s+([0-9]+(?:\.[0-9]+)?)%\s+Box\s+(\d{1,2})\b",
    re.IGNORECASE,
)

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
    key = re.sub(r"\s+", " ", name.strip().lower())
    return TRACK_MAP.get(key, key)


def load_results(results_root: Path) -> Dict[Tuple[str, str, int], str]:
    rows: Dict[Tuple[str, str, int], Tuple[int, str]] = {}
    for p in results_root.glob("data*/results_*.csv"):
        m = re.search(r"data(\d+)", str(p))
        data_num = int(m.group(1)) if m else 0
        with p.open(newline="", encoding="utf-8") as f:
            for row in csv.DictReader(f):
                date = str(row.get("Date", "")).strip()
                track = norm_track(str(row.get("Track", "")))
                race_raw = str(row.get("Race", row.get("RaceNumber", 0)) or 0).strip().upper()
                race = int(re.sub(r"^R", "", race_raw)) if race_raw else 0
                winner = str(row.get("Winner", "")).strip().upper()
                if not (date and track and race and winner and winner != "ABD"):
                    continue
                k = (date, track, race)
                prev = rows.get(k)
                if prev is None or data_num >= prev[0]:
                    rows[k] = (data_num, winner)
    return {k: v[1] for k, v in rows.items()}


def parse_reports(reports_dir: Path) -> List[dict]:
    parsed: List[dict] = []
    for p in sorted(reports_dir.glob("best_bets_report*.txt")):
        m = REPORT_RE.search(p.name)
        if not m:
            continue
        date = f"{m.group(3)}-{m.group(2)}-{m.group(1)}"
        for line in p.read_text(encoding="utf-8", errors="ignore").splitlines():
            mm = ROW_RE.match(line)
            if not mm:
                continue
            parsed.append(
                {
                    "date": date,
                    "track_raw": mm.group(1).strip(),
                    "track": norm_track(mm.group(1)),
                    "race": int(mm.group(2)),
                    "gap_pct": float(mm.group(3)),
                    "top_box": mm.group(4),
                    "source_report": p.name,
                }
            )
    return parsed


def choose_profile(overall_win: float, high_gap_win: float, matched: int) -> Tuple[str, dict]:
    # Conservative if high-confidence edge is weak, aggressive if very strong.
    if matched < 500 or high_gap_win < 0.34:
        profile = "conservative"
        params = {
            "rf": {"n_estimators": 100, "max_depth": 8, "min_samples_split": 8},
            "gb": {"learning_rate": 0.08, "min_samples_leaf": 5, "subsample": 0.75},
            "xgb": {"n_estimators": 120, "learning_rate": 0.08, "max_depth": 3, "subsample": 0.75, "colsample_bytree": 0.75},
        }
    elif high_gap_win > 0.42 and overall_win > 0.29:
        profile = "aggressive"
        params = {
            "rf": {"n_estimators": 120, "max_depth": 10, "min_samples_split": 4},
            "gb": {"learning_rate": 0.12, "min_samples_leaf": 3, "subsample": 0.85},
            "xgb": {"n_estimators": 180, "learning_rate": 0.12, "max_depth": 4, "subsample": 0.85, "colsample_bytree": 0.85},
        }
    else:
        profile = "balanced"
        params = {
            "rf": {"n_estimators": 100, "max_depth": 10, "min_samples_split": 5},
            "gb": {"learning_rate": 0.10, "min_samples_leaf": 3, "subsample": 0.80},
            "xgb": {"n_estimators": 150, "learning_rate": 0.10, "max_depth": 4, "subsample": 0.80, "colsample_bytree": 0.80},
        }
    return profile, params


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--reports-dir", default="best_bets_reports")
    ap.add_argument("--results-root", default=".")
    ap.add_argument("--output-dir", default="best_bets_reports")
    args = ap.parse_args()

    reports_dir = Path(args.reports_dir)
    results_root = Path(args.results_root)
    out_dir = Path(args.output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    results = load_results(results_root)
    reports = parse_reports(reports_dir)

    matched = 0
    wins = 0
    high_gap_matched = 0
    high_gap_wins = 0
    gap_bins = defaultdict(lambda: [0, 0])

    for r in reports:
        key = (r["date"], r["track"], r["race"])
        winner = results.get(key)
        if not winner:
            continue
        matched += 1
        won = winner == r["top_box"]
        if won:
            wins += 1

        if r["gap_pct"] >= 10.0:
            high_gap_matched += 1
            if won:
                high_gap_wins += 1

        bin_key = int(r["gap_pct"])
        gap_bins[bin_key][0] += 1
        if won:
            gap_bins[bin_key][1] += 1

        r["winner_box"] = winner
        r["top_pick_won"] = int(won)

    overall_win = wins / matched if matched else 0.0
    high_gap_win = high_gap_wins / high_gap_matched if high_gap_matched else 0.0

    profile, params = choose_profile(overall_win, high_gap_win, matched)

    overrides = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "source_reports_dir": str(reports_dir),
        "results_root": str(results_root),
        "matched_predictions": matched,
        "overall_top_pick_win_rate": round(overall_win, 4),
        "high_gap_sample_size": high_gap_matched,
        "high_gap_win_rate": round(high_gap_win, 4),
        "applied_profile": profile,
        **params,
    }

    (out_dir / "model_tuning_overrides.json").write_text(json.dumps(overrides, indent=2), encoding="utf-8")

    with (out_dir / "best_bets_report_index.csv").open("w", newline="", encoding="utf-8") as f:
        fieldnames = [
            "date",
            "track_raw",
            "track",
            "race",
            "gap_pct",
            "top_box",
            "winner_box",
            "top_pick_won",
            "source_report",
        ]
        w = csv.DictWriter(f, fieldnames=fieldnames)
        w.writeheader()
        for r in reports:
            w.writerow({k: r.get(k, "") for k in fieldnames})

    gap_lines = []
    for b in sorted(gap_bins):
        n, w = gap_bins[b]
        rate = (w / n * 100.0) if n else 0.0
        gap_lines.append(f"- {b:02d}.00%–{b:02d}.99%: {w}/{n} ({rate:.2f}%)")

    summary = (
        "# Best-Bets Driven Tuning Summary\n\n"
        f"- Matched predictions: **{matched}**\n"
        f"- Overall top-pick win rate: **{overall_win*100:.2f}%**\n"
        f"- High-gap (>=10%) win rate: **{high_gap_win*100:.2f}%** from **{high_gap_matched}** races\n"
        f"- Applied profile: **{profile}**\n\n"
        "## Gap-bin win rates\n"
        + ("\n".join(gap_lines) if gap_lines else "- No matched rows")
        + "\n"
    )
    (out_dir / "tuning_summary.md").write_text(summary, encoding="utf-8")

    print(f"Wrote: {out_dir / 'model_tuning_overrides.json'}")
    print(f"Wrote: {out_dir / 'best_bets_report_index.csv'}")
    print(f"Wrote: {out_dir / 'tuning_summary.md'}")
    print(f"Profile: {profile} | matched={matched} | overall={overall_win*100:.2f}% | high_gap={high_gap_win*100:.2f}%")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
