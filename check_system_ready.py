#!/usr/bin/env python3
"""
check_system_ready.py

GO / NO-GO readiness audit for retraining and track/result data quality.
"""

from __future__ import annotations

import csv
import re
import sys
from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime, date
from pathlib import Path
from typing import Dict, List, Set, Tuple


REPO_ROOT = Path(__file__).resolve().parent
REPORTS_DIR = REPO_ROOT / "reports"
DATA_DIRS = [REPO_ROOT / "data", REPO_ROOT / "data2", REPO_ROOT / "data3", REPO_ROOT / "data4"]
REQUIRED_COLUMNS = ["Track", "Date", "Race", "Winner", "2nd", "3rd", "4th"]

FORM_RE_6 = re.compile(r"^(?P<prefix>[A-Z]+)(?P<dd>\d{2})(?P<mm>\d{2})(?P<yy>\d{2})form\.pdf$")
FORM_RE_4 = re.compile(r"^(?P<prefix>[A-Z]+)(?P<dd>\d{2})(?P<mm>\d{2})form\.pdf$")

TRACK_CODE_MAP: Dict[str, str] = {
    "ANGLG": "Angle Park",
    "ANGNG": "Angle Park",
    "BDGOG": "Bendigo",
    "BRATG": "Ballarat",
    "BRHG": "Broken Hill",
    "BULIG": "Bulli",
    "CANNG": "Cannington",
    "CAPAG": "Capalaba",
    "CSNOG": "Casino",
    "DRWNG": "Darwin",
    "DUBBG": "Dubbo",
    "ELWKG": "Healesville",
    "GARDG": "Gardens",
    "GAWLG": "Gawler",
    "GEELG": "Geelong",
    "GOSFG": "Gosford",
    "GOULG": "Goulburn",
    "GRAFG": "Grafton",
    "GUNNG": "Gunnedah",
    "HEALG": "Healesville",
    "HSHMG": "Horsham",
    "MAITG": "Maitland",
    "MANDG": "Mandurah",
    "MBRGG": "Murray Bridge",
    "MBRSG": "Murray Bridge Straight",
    "MEADG": "Meadows",
    "MOWBG": "Wentworth Park",
    "MTGG": "Mount Gambier",
    "NOWRG": "Nowra",
    "NTHMG": "Northam",
    "QLAKG": "Q Lakeside",
    "QPRKG": "Q Parklands",
    "QSTRG": "Q Straight",
    "RICHG": "Richmond",
    "RISTG": "Richmond Straight",
    "ROCKG": "Rockhampton",
    "SALEG": "Sale",
    "SANDG": "Sandown",
    "SHEP": "Shepparton",
    "SHEPG": "Shepparton",
    "TASTG": "Hobart",
    "TEMOG": "Temora",
    "TOWNG": "Townsville",
    "TRARG": "Traralgon",
    "WAGGG": "Wagga",
    "WARGG": "Warragul",
    "WENPG": "Wentworth Park",
    "WNBLG": "Warrnambool",
}

TRACK_ALIASES: Dict[str, str] = {
    "BET NATION TOWNSVILLE": "Townsville",
    "BETDELUXE CAPALABA": "Capalaba",
    "BETDELUXE ROCKHAMPTON": "Rockhampton",
    "LADBROKES GARDENS": "Gardens",
    "LADBROKES Q1 LAKESIDE": "Q Lakeside",
    "LADBROKES Q2 PARKLANDS": "Q Parklands",
    "LADBROKES Q STRAIGHT": "Q Straight",
    "MOUNT GAMBIER": "Mount Gambier",
    "MT GAMBIER": "Mount Gambier",
    "RICHMOND STRAIGHT": "Richmond Straight",
    "SANDOWN PARK": "Sandown",
    "THE MEADOWS": "Meadows",
}


@dataclass
class AuditIssue:
    level: str  # ERROR / WARN / INFO
    message: str


def normalize_track(name: str) -> str:
    cleaned = re.sub(r"\s+", " ", (name or "").strip())
    if not cleaned:
        return ""
    return TRACK_ALIASES.get(cleaned.upper(), cleaned)


def parse_form_filename(filename: str) -> Tuple[str, str, bool]:
    m6 = FORM_RE_6.match(filename)
    if m6:
        dd, mm, yy = int(m6.group("dd")), int(m6.group("mm")), int(m6.group("yy"))
        d = date(2000 + yy, mm, dd).isoformat()
        prefix = m6.group("prefix")
        return prefix, d, False

    m4 = FORM_RE_4.match(filename)
    if m4:
        dd, mm = int(m4.group("dd")), int(m4.group("mm"))
        # Legacy inference used by parser.py
        yyyy = 2025 if mm >= 10 else 2026
        d = date(yyyy, mm, dd).isoformat()
        prefix = m4.group("prefix")
        return prefix, d, True

    raise ValueError(f"Unrecognized form filename: {filename}")


def validate_results_file(path: Path, issues: List[AuditIssue]) -> Dict[str, Set[str]]:
    tracks_by_date: Dict[str, Set[str]] = defaultdict(set)
    seen_keys: Set[Tuple[str, str, str]] = set()
    duplicate_count = 0
    non_numeric_count = 0
    blank_row_count = 0
    with path.open(newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        if reader.fieldnames is None:
            issues.append(AuditIssue("ERROR", f"{path}: empty CSV (no header row)"))
            return tracks_by_date
        if reader.fieldnames != REQUIRED_COLUMNS:
            issues.append(AuditIssue("ERROR", f"{path}: invalid header {reader.fieldnames}, expected {REQUIRED_COLUMNS}"))
            return tracks_by_date

        for line_num, row in enumerate(reader, start=2):
            if not any((v or "").strip() for v in row.values()):
                blank_row_count += 1
                continue

            track = normalize_track((row.get("Track") or "").strip())
            date_str = (row.get("Date") or "").strip()
            race = (row.get("Race") or "").strip()

            if not track:
                issues.append(AuditIssue("ERROR", f"{path}: empty Track at line {line_num}"))
                continue
            try:
                datetime.strptime(date_str, "%Y-%m-%d")
            except ValueError:
                issues.append(AuditIssue("ERROR", f"{path}: invalid Date '{date_str}' at line {line_num}"))
                continue
            race_num = race[1:] if race.upper().startswith("R") else race
            if not race_num.isdigit():
                issues.append(AuditIssue("ERROR", f"{path}: invalid Race '{race}' at line {line_num}"))
                continue

            key = (date_str, track, race_num)
            if key in seen_keys:
                duplicate_count += 1
            seen_keys.add(key)

            for col in ["Winner", "2nd", "3rd", "4th"]:
                val = (row.get(col) or "").strip()
                if not val:
                    continue
                if col == "Winner" and val.upper() == "ABD":
                    continue
                if not val.isdigit():
                    non_numeric_count += 1

            tracks_by_date[date_str].add(track)

    if blank_row_count:
        issues.append(AuditIssue("WARN", f"{path}: {blank_row_count} blank row(s)"))
    if duplicate_count:
        issues.append(AuditIssue("WARN", f"{path}: {duplicate_count} duplicate Date+Track+Race row(s)"))
    if non_numeric_count:
        issues.append(AuditIssue("WARN", f"{path}: {non_numeric_count} non-numeric placing value(s)"))
    return tracks_by_date


def audit_data_dir(data_dir: Path) -> Tuple[List[AuditIssue], Dict[str, Set[str]], Dict[str, Set[str]]]:
    issues: List[AuditIssue] = []
    forms_by_date: Dict[str, Set[str]] = defaultdict(set)
    results_by_date: Dict[str, Set[str]] = defaultdict(set)

    if not data_dir.exists():
        issues.append(AuditIssue("WARN", f"{data_dir}: directory not found"))
        return issues, forms_by_date, results_by_date

    for pdf in sorted(data_dir.glob("*form.pdf")):
        try:
            prefix, date_str, is_legacy = parse_form_filename(pdf.name)
            track = TRACK_CODE_MAP.get(prefix, prefix)
            forms_by_date[date_str].add(normalize_track(track))
            if is_legacy:
                issues.append(AuditIssue("WARN", f"{pdf}: legacy DDMM filename missing yy"))
        except Exception:
            issues.append(AuditIssue("ERROR", f"{pdf}: malformed form filename"))

    result_files = sorted(data_dir.glob("results_*.csv"))
    if not result_files:
        issues.append(AuditIssue("INFO", f"{data_dir}: no results_*.csv files found"))

    for csv_file in result_files:
        tracks = validate_results_file(csv_file, issues)
        for d, tset in tracks.items():
            results_by_date[d].update(tset)

    return issues, forms_by_date, results_by_date


def write_report(issues_by_dir: Dict[str, List[AuditIssue]], generated_at: datetime) -> Path:
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    report_path = REPORTS_DIR / f"SYSTEM_READY_CHECK_{generated_at.strftime('%Y-%m-%d_%H%M%S')}.txt"
    lines: List[str] = []
    lines.append("SYSTEM READY CHECK")
    lines.append(f"Generated: {generated_at.isoformat(timespec='seconds')}")
    lines.append("")
    total_errors = total_warnings = 0
    for dir_name, issues in issues_by_dir.items():
        lines.append(f"[{dir_name}]")
        if not issues:
            lines.append("  ✅ No issues found")
            lines.append("")
            continue
        for issue in issues:
            lines.append(f"  {issue.level}: {issue.message}")
            if issue.level == "ERROR":
                total_errors += 1
            elif issue.level == "WARN":
                total_warnings += 1
        lines.append("")
    lines.append("SUMMARY")
    lines.append(f"  Errors  : {total_errors}")
    lines.append(f"  Warnings: {total_warnings}")
    lines.append("  Status  : GO" if (total_errors == 0 and total_warnings == 0) else "  Status  : NO-GO")
    report_path.write_text("\n".join(lines), encoding="utf-8")
    return report_path


def main() -> int:
    issues_by_dir: Dict[str, List[AuditIssue]] = {}
    global_forms: Dict[str, Set[str]] = defaultdict(set)
    global_results: Dict[str, Set[str]] = defaultdict(set)
    for d in DATA_DIRS:
        issues, forms_by_date, results_by_date = audit_data_dir(d)
        issues_by_dir[d.name] = issues
        for dt, tracks in forms_by_date.items():
            global_forms[dt].update(tracks)
        for dt, tracks in results_by_date.items():
            global_results[dt].update(tracks)

    # Global track/date pairing audit across all data folders.
    missing_forms_examples = []
    missing_results_examples = []
    total_missing_forms = 0
    total_missing_results = 0
    all_dates = sorted(set(global_forms) | set(global_results))
    for dt in all_dates:
        form_tracks = global_forms.get(dt, set())
        result_tracks = global_results.get(dt, set())
        missing_results = sorted(form_tracks - result_tracks)
        missing_forms = sorted(result_tracks - form_tracks)
        if missing_results:
            total_missing_results += len(missing_results)
            if len(missing_results_examples) < 10:
                missing_results_examples.append((dt, missing_results))
        if missing_forms:
            total_missing_forms += len(missing_forms)
            if len(missing_forms_examples) < 10:
                missing_forms_examples.append((dt, missing_forms))

    pairing_issues: List[AuditIssue] = []
    if total_missing_results:
        pairing_issues.append(
            AuditIssue(
                "WARN",
                f"Global pairing: {total_missing_results} form track/date entries missing results across {len(all_dates)} dates",
            )
        )
        for dt, tracks in missing_results_examples:
            pairing_issues.append(AuditIssue("WARN", f"Example {dt} forms-without-results: {tracks}"))
    if total_missing_forms:
        pairing_issues.append(
            AuditIssue(
                "WARN",
                f"Global pairing: {total_missing_forms} result track/date entries missing forms across {len(all_dates)} dates",
            )
        )
        for dt, tracks in missing_forms_examples:
            pairing_issues.append(AuditIssue("WARN", f"Example {dt} results-without-forms: {tracks}"))
    issues_by_dir["global_pairing"] = pairing_issues

    generated_at = datetime.now()
    report = write_report(issues_by_dir, generated_at=generated_at)
    print(f"Report written: {report}")

    errors = sum(1 for issues in issues_by_dir.values() for issue in issues if issue.level == "ERROR")
    warnings = sum(1 for issues in issues_by_dir.values() for issue in issues if issue.level == "WARN")
    print(f"Errors: {errors}  Warnings: {warnings}")
    print("GO" if errors == 0 and warnings == 0 else "NO-GO")
    return 0 if (errors == 0 and warnings == 0) else 1


if __name__ == "__main__":
    raise SystemExit(main())
