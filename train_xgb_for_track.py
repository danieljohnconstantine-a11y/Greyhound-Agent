#!/usr/bin/env python3
"""
train_xgb_for_track.py
=======================
Helper script called by ORGANIZE_ALL_TRACKS.bat to train an XGB model
for a given track if one is not already present.

Usage:
    python train_xgb_for_track.py "Angle Park"
    python train_xgb_for_track.py BALLARAT
"""

import sys
import os
import warnings

warnings.filterwarnings('ignore')

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from predict_race import train_or_load_xgb, _track_to_prefix
from src.pdf_parser import parse_form_pdf
from src.race_features import build_features


def main():
    if len(sys.argv) < 2:
        print("Usage: python train_xgb_for_track.py <track_name>")
        sys.exit(1)

    track = ' '.join(sys.argv[1:])    # allow multi-word names like "Angle Park"
    xgb_path = f'{track}_xgb.pkl'

    if os.path.exists(xgb_path):
        print(f"  [SKIP] {xgb_path} already exists")
        sys.exit(0)

    prefix = _track_to_prefix(track)
    data_dir = 'data'

    if not os.path.isdir(data_dir):
        print(f"  [ERROR] data/ directory not found")
        sys.exit(1)

    pdfs = sorted([
        f for f in os.listdir(data_dir)
        if f.upper().startswith(prefix) and f.lower().endswith('.pdf')
    ])

    if not pdfs:
        print(f"  [WARN] No PDFs found for track prefix '{prefix}' — cannot train XGB for {track}")
        sys.exit(0)

    # Use the most recent PDF available
    pdf_path = os.path.join(data_dir, pdfs[-1])
    print(f"  Using PDF: {pdf_path}")

    try:
        df = parse_form_pdf(pdf_path)
    except Exception as e:
        print(f"  [ERROR] Could not parse {pdf_path}: {e}")
        sys.exit(1)

    if df.empty:
        print(f"  [WARN] No dogs found in {pdf_path}")
        sys.exit(0)

    try:
        feat = build_features(df)
    except Exception as e:
        print(f"  [ERROR] Feature build failed: {e}")
        sys.exit(1)

    model = train_or_load_xgb(track, feat, '.')
    if model:
        print(f"  [OK] XGB model trained and saved → {xgb_path}")
    else:
        print(f"  [WARN] XGB training failed for {track}")
        sys.exit(1)


if __name__ == '__main__':
    main()
