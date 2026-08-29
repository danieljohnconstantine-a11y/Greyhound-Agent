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
from datetime import datetime, date, timedelta
from pathlib import Path
from typing import Dict, List, Set, Tuple

try:
    import pdfplumber  # type: ignore
except Exception:  # pragma: no cover - optional dependency at runtime
    pdfplumber = None


REPO_ROOT = Path(__file__).resolve().parent
REPORTS_DIR = REPO_ROOT / "reports"
DATA_DIRS = [REPO_ROOT / "data", REPO_ROOT / "data2", REPO_ROOT / "data3", REPO_ROOT / "data4"]
REQUIRED_COLUMNS = ["Track", "Date", "Race", "Winner", "2nd", "3rd", "4th"]
ALT_REQUIRED_COLUMNS = ["Track", "RaceDate", "RaceNumber", "WinnerBox", "SecondBox", "ThirdBox", "FourthBox"]

FORM_RE_6 = re.compile(r"^(?P<prefix>[A-Z]+)(?P<dd>\d{2})(?P<mm>\d{2})(?P<yy>\d{2})form\.pdf$")
FORM_RE_4 = re.compile(r"^(?P<prefix>[A-Z]+)(?P<dd>\d{2})(?P<mm>\d{2})form\.pdf$")
# Keep this in sync with src/parser.py legacy fallback:
# month >= 10 -> 2025, otherwise 2026.
LEGACY_YEAR_SWITCH_MONTH = 10

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
    # ELWKG files are Elwick (Hobart) meetings in this dataset.
    "ELWKG": "Hobart",
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
    # MOWBG files correspond to Mowbray (Launceston) meetings.
    "MOWBG": "Launceston",
    "MTGG": "Mount Gambier",
    "NOWRG": "Nowra",
    "NTHMG": "Northam",
    "QLAKG": "Q Lakeside",
    "QPRKG": "Q Parklands",
    "QSTRG": "Q Straight",
    "RICHG": "Richmond",
    # Keep consistent with src/results_loader._TRACK_ALIASES where
    # "RICHMOND STRAIGHT" normalizes to "Richmond" for training merges.
    "RISTG": "Richmond",
    "ROCKG": "Rockhampton",
    "SALEG": "Sale",
    "SANDG": "Sandown",
    "SHEP": "Shepparton",
    "SHEPG": "Shepparton",
    # TASTG files map to Tasmania/Hobart meetings.
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
    "LADBROKES Q LAKESIDE": "Q Lakeside",
    "LADBROKES Q2 PARKLANDS": "Q Parklands",
    "LADBROKES Q STRAIGHT": "Q Straight",
    "MOUNT GAMBIER": "Mount Gambier",
    "MT GAMBIER": "Mount Gambier",
    # Keep consistent with src/results_loader normalization.
    "RICHMOND STRAIGHT": "Richmond",
    "SANDOWN PARK": "Sandown",
    "TASMANIA": "Hobart",
    "THE GARDENS": "Gardens",
    "LAKESIDE": "Q Lakeside",
    "Q1 LAKESIDE": "Q Lakeside",
    "Q2 PARKLANDS": "Q Parklands",
    "TAREE SUPER TRACK": "Taree",
    "THE MEADOWS": "Meadows",
}

CANONICAL_TRACKS: Dict[str, str] = {name.upper(): name for name in sorted(set(TRACK_CODE_MAP.values()))}
for _alias_target in TRACK_ALIASES.values():
    CANONICAL_TRACKS.setdefault(_alias_target.upper(), _alias_target)
# Values are stored uppercase because checks use track.upper().
INVALID_TRACK_NAMES: Set[str] = {"ABD"}
KNOWN_CANCELLED_FORM_MEETINGS: Set[Tuple[str, str]] = {
    ("2025-11-23", "Darwin"),
}
TRACK_DRIFT_DAY_WINDOW: Dict[str, int] = {
    "Hobart": 3,
}
TRACK_NEARBY_RESULTS_WINDOW: Dict[str, int] = {
    "Hobart": 5,
}


@dataclass
class AuditIssue:
    level: str  # ERROR / WARN / INFO
    message: str


def normalize_track(name: str) -> str:
    cleaned = re.sub(r"\s+", " ", (name or "").strip())
    if not cleaned:
        return ""
    aliased = TRACK_ALIASES.get(cleaned.upper(), cleaned)
    return CANONICAL_TRACKS.get(aliased.upper(), aliased)


def _build_day_offsets(window: int) -> List[int]:
    offsets: List[int] = []
    for day in range(1, window + 1):
        offsets.extend([day, -day])
    return offsets


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
        # Legacy inference used by parser.py (_extract_date_from_pdf_filename).
        yyyy = 2025 if mm >= LEGACY_YEAR_SWITCH_MONTH else 2026
        d = date(yyyy, mm, dd).isoformat()
        prefix = m4.group("prefix")
        return prefix, d, True

    raise ValueError(f"Unrecognized form filename: {filename}")


def infer_track_from_pdf_header(pdf_path: Path, fallback_track: str) -> str:
    """
    For ambiguous legacy codes, read the first-page header and extract track name.
    Falls back to the provided mapped track if extraction fails.
    Uses the first matching "Race No ... <track> ... <distance>m" line.
    """
    if pdfplumber is None:
        return fallback_track
    text = ""
    try:
        with pdfplumber.open(str(pdf_path)) as pdf:
            if not pdf.pages:
                return fallback_track
            text = pdf.pages[0].extract_text() or ""
    except Exception:
        return fallback_track

    for line in text.splitlines():
        if "Race No" not in line:
            continue
        m = re.search(r"\d{1,2}:\d{2}[ap]m\s+(.+?)\s+\d{3,4}m\b", line, flags=re.IGNORECASE)
        if not m:
            continue
        extracted = normalize_track(m.group(1))
        return extracted or fallback_track
    return fallback_track


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
        header_set = set(reader.fieldnames)
        required_set = set(REQUIRED_COLUMNS)
        alt_required_set = set(ALT_REQUIRED_COLUMNS)
        is_standard_schema = required_set.issubset(header_set)
        is_alt_schema = alt_required_set.issubset(header_set)
        if not is_standard_schema and not is_alt_schema:
            missing = sorted(required_set - header_set)
            alt_missing = sorted(alt_required_set - header_set)
            issues.append(
                AuditIssue(
                    "ERROR",
                    f"{path}: unsupported results schema, missing standard={missing}, missing alt={alt_missing}",
                )
            )
            return tracks_by_date

        for line_num, row in enumerate(reader, start=2):
            if not any((v or "").strip() for v in row.values()):
                blank_row_count += 1
                continue

            track = normalize_track((row.get("Track") or "").strip())
            if is_standard_schema:
                date_str = (row.get("Date") or "").strip()
                race = (row.get("Race") or "").strip()
                winner_col, second_col, third_col, fourth_col = "Winner", "2nd", "3rd", "4th"
            else:
                date_str = (row.get("RaceDate") or "").strip()
                race = (row.get("RaceNumber") or "").strip()
                winner_col, second_col, third_col, fourth_col = "WinnerBox", "SecondBox", "ThirdBox", "FourthBox"

            if not track:
                issues.append(AuditIssue("ERROR", f"{path}: empty Track at line {line_num}"))
                continue
            if track.upper() in INVALID_TRACK_NAMES:
                issues.append(AuditIssue("WARN", f"{path}: ignored invalid Track '{track}' at line {line_num}"))
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

            for col in [winner_col, second_col, third_col, fourth_col]:
                val = (row.get(col) or "").strip()
                if not val:
                    continue
                if col == winner_col and val.upper() == "ABD":
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
            # TASTG files in the dataset can refer to different TAS/NSW meetings.
            if prefix == "TASTG":
                track = infer_track_from_pdf_header(pdf, fallback_track=track)
            forms_by_date[date_str].add(normalize_track(track))
            if is_legacy:
                issues.append(AuditIssue("WARN", f"{pdf}: legacy DDMM filename missing yy"))
        except Exception:
            issues.append(AuditIssue("ERROR", f"{pdf}: malformed form filename"))

    result_files = sorted(set(data_dir.glob("results_*.csv")) | set(data_dir.glob("race_results*.csv")))
    if not result_files:
        issues.append(AuditIssue("INFO", f"{data_dir}: no results_*.csv or race_results*.csv files found"))

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
    missing_forms_rows: List[Tuple[str, str]] = []
    missing_results_rows: List[Tuple[str, str]] = []
    total_missing_forms = 0
    total_missing_results = 0
    auto_matched_rows: List[Tuple[str, str, str, str]] = []
    all_dates = sorted(set(global_forms) | set(global_results))

    forms_without_results_by_date: Dict[str, Set[str]] = {}
    results_without_forms_by_date: Dict[str, Set[str]] = {}
    for dt in all_dates:
        form_tracks = global_forms.get(dt, set())
        result_tracks = global_results.get(dt, set())
        forms_without_results_by_date[dt] = set(form_tracks - result_tracks)
        results_without_forms_by_date[dt] = set(result_tracks - form_tracks)

    # Explicitly suppress known cancelled meetings with no official results.
    for dt, track in KNOWN_CANCELLED_FORM_MEETINGS:
        forms_set = forms_without_results_by_date.get(dt)
        if forms_set and track in forms_set:
            forms_set.remove(track)
            auto_matched_rows.append((dt, track, dt, "CANCELLED"))

    # Auto-reconcile well-known same-day alias mismatches.
    alias_pair_rules = [
        ("Murray Bridge Straight", "Murray Bridge"),
    ]
    for dt in all_dates:
        for forms_track, results_track in alias_pair_rules:
            forms_set = forms_without_results_by_date.get(dt, set())
            results_set = results_without_forms_by_date.get(dt, set())
            if forms_track in forms_set and results_track in results_set:
                forms_set.remove(forms_track)
                results_set.remove(results_track)
                auto_matched_rows.append((dt, forms_track, dt, results_track))

    # Auto-reconcile same-track date drift (track-specific day windows).
    consumed_result_pairs: Set[Tuple[str, str]] = set()
    for dt in sorted(all_dates):
        forms_set = forms_without_results_by_date.get(dt, set())
        if not forms_set:
            continue
        dt_obj = datetime.strptime(dt, "%Y-%m-%d").date()

        for track in sorted(list(forms_set)):
            window = TRACK_DRIFT_DAY_WINDOW.get(track, 1)
            for offset in _build_day_offsets(window):
                candidate_dt = (dt_obj + timedelta(days=offset)).isoformat()
                candidate_key = (candidate_dt, track)
                if candidate_key in consumed_result_pairs:
                    continue
                if track not in results_without_forms_by_date.get(candidate_dt, set()):
                    continue
                forms_set.remove(track)
                results_without_forms_by_date[candidate_dt].remove(track)
                consumed_result_pairs.add(candidate_key)
                auto_matched_rows.append((dt, track, candidate_dt, track))
                break

    # If configured, allow forms dates to reconcile to nearby results dates
    # even when the nearby results date also has forms (no surplus row to consume).
    for dt in sorted(all_dates):
        forms_set = forms_without_results_by_date.get(dt, set())
        if not forms_set:
            continue
        dt_obj = datetime.strptime(dt, "%Y-%m-%d").date()
        for track in sorted(list(forms_set)):
            window = TRACK_NEARBY_RESULTS_WINDOW.get(track, 0)
            if window <= 0:
                continue
            for offset in _build_day_offsets(window):
                candidate_dt = (dt_obj + timedelta(days=offset)).isoformat()
                if track not in global_results.get(candidate_dt, set()):
                    continue
                forms_set.remove(track)
                auto_matched_rows.append((dt, track, candidate_dt, f"{track} (nearby)"))
                break

    for dt in all_dates:
        missing_results = sorted(forms_without_results_by_date.get(dt, set()))
        missing_forms = sorted(results_without_forms_by_date.get(dt, set()))
        if missing_results:
            total_missing_results += len(missing_results)
            for track in missing_results:
                missing_results_rows.append((dt, track))
            if len(missing_results_examples) < 10:
                missing_results_examples.append((dt, missing_results))
        if missing_forms:
            total_missing_forms += len(missing_forms)
            for track in missing_forms:
                missing_forms_rows.append((dt, track))
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
    if auto_matched_rows:
        pairing_issues.append(
            AuditIssue("INFO", f"Auto-matched {len(auto_matched_rows)} likely mis-saved pair(s) by alias/day-drift rules")
        )
        for form_dt, form_track, result_dt, result_track in sorted(auto_matched_rows)[:10]:
            pairing_issues.append(
                AuditIssue(
                    "INFO",
                    f"Auto-match {form_dt} {form_track} -> {result_dt} {result_track}",
                )
            )
        if len(auto_matched_rows) > 10:
            pairing_issues.append(AuditIssue("INFO", "Auto-match details truncated to 10 rows in this text report; see CSV for full list"))
    issues_by_dir["global_pairing"] = pairing_issues

    # Write full missing-pair exports for remediation planning.
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    generated_at = datetime.now()
    stamp = generated_at.strftime("%Y-%m-%d_%H%M%S")
    forms_without_results_csv = REPORTS_DIR / f"FORMS_WITHOUT_RESULTS_{stamp}.csv"
    results_without_forms_csv = REPORTS_DIR / f"RESULTS_WITHOUT_FORMS_{stamp}.csv"
    auto_matched_csv = REPORTS_DIR / f"AUTO_MATCHED_TRACK_DATE_PAIRS_{stamp}.csv"
    wrote_forms_without_results_csv = False
    wrote_results_without_forms_csv = False
    wrote_auto_matched_csv = False
    # missing_results_rows = forms exist but results are missing
    if missing_results_rows:
        with forms_without_results_csv.open("w", newline="", encoding="utf-8") as f:
            w = csv.writer(f)
            w.writerow(["Date", "Track"])
            w.writerows(sorted(missing_results_rows))
        wrote_forms_without_results_csv = True
    # missing_forms_rows = results exist but forms are missing
    if missing_forms_rows:
        with results_without_forms_csv.open("w", newline="", encoding="utf-8") as f:
            w = csv.writer(f)
            w.writerow(["Date", "Track"])
            w.writerows(sorted(missing_forms_rows))
        wrote_results_without_forms_csv = True
    if auto_matched_rows:
        with auto_matched_csv.open("w", newline="", encoding="utf-8") as f:
            w = csv.writer(f)
            w.writerow(["FormsDate", "FormsTrack", "ResultsDate", "ResultsTrack"])
            w.writerows(sorted(auto_matched_rows))
        wrote_auto_matched_csv = True

    report = write_report(issues_by_dir, generated_at=generated_at)
    print(f"Report written: {report}")
    if wrote_forms_without_results_csv:
        print(f"Forms-without-results list: {forms_without_results_csv}")
    else:
        print("Forms-without-results list: none")
    if wrote_results_without_forms_csv:
        print(f"Results-without-forms list: {results_without_forms_csv}")
    else:
        print("Results-without-forms list: none")
    if wrote_auto_matched_csv:
        print(f"Auto-matched pairs list: {auto_matched_csv}")
    else:
        print("Auto-matched pairs list: none")

    errors = sum(1 for issues in issues_by_dir.values() for issue in issues if issue.level == "ERROR")
    warnings = sum(1 for issues in issues_by_dir.values() for issue in issues if issue.level == "WARN")
    print(f"Errors: {errors}  Warnings: {warnings}")
    print("GO" if errors == 0 and warnings == 0 else "NO-GO")
    return 0 if (errors == 0 and warnings == 0) else 1


if __name__ == "__main__":
    raise SystemExit(main())
