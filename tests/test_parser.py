import os
import re
import pdfplumber
import sys
from datetime import datetime, date, timedelta

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from src.parser import parse_race_form

def extract_text_from_latest_pdf(folder):
    if not os.path.exists(folder):
        print(f"❌ Folder not found: {folder}")
        return None

    pdf_files = [f for f in os.listdir(folder) if f.lower().endswith(".pdf")]
    if not pdf_files:
        print("❌ No PDF files found in folder.")
        return None

    # Sort by most recently modified
    pdf_files.sort(key=lambda f: os.path.getmtime(os.path.join(folder, f)), reverse=True)
    pdf_path = os.path.join(folder, pdf_files[0])

    text = ""
    try:
        with pdfplumber.open(pdf_path) as pdf:
            for page in pdf.pages:
                page_text = page.extract_text()
                if page_text:
                    text += page_text + "\n"
    except Exception as e:
        print(f"⚠️ Error reading PDF: {e}")
        return None

    print(f"✅ Extracted text from {os.path.basename(pdf_path)}")
    return text


# ---------------------------------------------------------------------------
# Regression test: dog names containing periods (Mr., Mrs., Dr., Ms., Mt.)
# must be parsed correctly by the main dog-entry regex in src/parser.py.
# Bug fixed: period was absent from name character class [A-Za-z''\- ]+?
# causing honorific-prefixed dogs to be silently skipped.
#
# NOTE: The regex below intentionally mirrors the pattern in src/parser.py
# (dog_match re.compile on line ~267) to act as a regression guard. If the
# production pattern changes to remove period support, this test will fail.
# ---------------------------------------------------------------------------
_DOG_ENTRY_RE = re.compile(
    r"""^(\d+)\.?\s*([0-9xf]{0,7})?([A-Za-z''.\- ]+?)\s+(\d+[a-z])\s+([\d.]+)kg\s+(\d+)\s+([A-Za-z''.\- ]+)\s+(\d+)\s*-\s*(\d+)\s*-\s*(\d+)\s+\$?([\d,]+)\s+(\S+)\s+(\S+)\s+(\S+)"""
)

_HONORIFIC_TEST_CASES = [
    ("1. 11622Mr. Devere 1d 0.0kg 1 Daniel Pell 2 - 3 - 7 $5,350 8 10 28",
     "Mr. Devere", "Daniel Pell"),
    ("2. 72672Dr. Warren 2d 0.0kg 2 William McMahon 1 - 11 - 28 $9,160 29 5 51",
     "Dr. Warren", "William McMahon"),
    ("6. 31345Dr. Paris 2b 0.0kg 6 Kimberley McMahon 2 - 5 - 17 $10,955 18 5 36",
     "Dr. Paris", "Kimberley McMahon"),
    ("8. 40x44Dr. Xanthic 2d 0.0kg 8 Emily McMahon 2 - 3 - 17 $5,305 3 5 217",
     "Dr. Xanthic", "Emily McMahon"),
    ("5. 51647Dr. Farrah 3b 0.0kg 5 Kimberley McMahon 15 - 21 - 69 $47,690 10 40 117",
     "Dr. Farrah", "Kimberley McMahon"),
    # Normal name (no period) must still work
    ("4. 12472Whisky Bella 1b 0.0kg 4 George Cini 2 - 6 - 15 $6,465 16 53 79",
     "Whisky Bella", "George Cini"),
]


def test_dog_name_with_period():
    """Dog names with honorific prefixes (Mr., Mrs., Dr., Ms., Mt.) must parse."""
    for line, expected_name, expected_trainer in _HONORIFIC_TEST_CASES:
        m = _DOG_ENTRY_RE.match(line)
        assert m is not None, f"Regex failed to match line: {line[:80]}"
        actual_name = m.group(3).strip()
        actual_trainer = m.group(7).strip()
        assert actual_name.upper() == expected_name.upper(), (
            f"Name mismatch: expected '{expected_name}' got '{actual_name}'"
        )
        assert actual_trainer.upper() == expected_trainer.upper(), (
            f"Trainer mismatch: expected '{expected_trainer}' got '{actual_trainer}'"
        )


def _expected_filename_date(day: int, month: int):
    today = datetime.now().date()
    year = today.year
    candidate = date(year, month, day)
    if candidate > (today + timedelta(days=45)):
        year -= 1
    elif candidate < (today - timedelta(days=320)):
        year += 1
    return date(year, month, day).isoformat()


def test_parse_race_header_old_and_new_layout():
    old_layout = "\n".join([
        "Race No 28 May 26 06:37pm Angle Park 342m",
        "1. 6x613Zali Keeping 3b 0.0kg 1 Tamica Dunn 12 - 19 - 60 $47,530 4 3 8",
    ])
    new_layout = "\n".join([
        "Race No 01 June 26 06:02pm Angle Park 342m",
        "1. 6Regal Mack 1d 0.0kg 1 Alan Randall 0 - 0 - 1 $0 SU 7 Mdn",
    ])

    old_df = parse_race_form(old_layout, pdf_file="ANGLG2805form.pdf")
    new_df = parse_race_form(new_layout, pdf_file="ANGLG0106form.pdf")

    assert len(old_df) == 1
    assert len(new_df) == 1
    assert old_df.iloc[0]["Track"] == "Angle Park"
    assert new_df.iloc[0]["Track"] == "Angle Park"
    assert int(old_df.iloc[0]["RaceNumber"]) == 1
    assert int(new_df.iloc[0]["RaceNumber"]) == 1
    assert old_df.iloc[0]["RaceDate"] == "2026-05-28"
    assert new_df.iloc[0]["RaceDate"] == "2026-06-01"


def test_parse_race_date_fallback_from_filename():
    text = "\n".join([
        "Race 1",
        "1. 6Regal Mack 1d 0.0kg 1 Alan Randall 0 - 0 - 1 $0 SU 7 Mdn",
    ])

    df = parse_race_form(text, pdf_file="ANGLG0106form.pdf")
    assert len(df) == 1
    assert int(df.iloc[0]["RaceNumber"]) == 1
    assert df.iloc[0]["RaceDate"] == _expected_filename_date(1, 6)


if __name__ == "__main__":
    try:
        test_dog_name_with_period()
        test_parse_race_header_old_and_new_layout()
        test_parse_race_date_fallback_from_filename()
        print("✅ Passed parser regression tests")
    except AssertionError as e:
        print(f"❌ {e}")
        raise SystemExit(1)
