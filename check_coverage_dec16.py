#!/usr/bin/env python3
"""
Check coverage between PDFs and CSV results for December 16, 2025
"""
import os
import csv
from collections import defaultdict

# Track name normalizations for matching
TRACK_NORMALIZATIONS = {
    "ANGLE PARK": "Angle Park",
    "ANGLG": "Angle Park",
    "BULLI": "Bulli",
    "BULIG": "Bulli",
    "GOSFORD": "Gosford",
    "GOSFG": "Gosford",
    "GRAFTON": "Grafton",
    "GRAFG": "Grafton",
    "MURRAY BRIDGE STRAIGHT": "Murray Bridge Straight",
    "MBRSG": "Murray Bridge Straight",
    "HOBART": "Hobart",
    "ELWKG": "Hobart",
    "HORSHAM": "Horsham",
    "HSHMG": "Horsham",
    "LADBROKES Q1 LAKESIDE": "Ladbrokes Q1 Lakeside",
    "QLAKG": "Ladbrokes Q1 Lakeside",
    "GEELONG": "Geelong",
    "GEELG": "Geelong",
    "WARRAGUL": "Warragul",
    "WARGG": "Warragul",
    "BET NATION TOWNSVILLE": "Bet Nation Townsville",
    "TOWNSVILLE": "Bet Nation Townsville",
    "TOWNG": "Bet Nation Townsville",
    "MANDURAH": "Mandurah",
    "MANDG": "Mandurah",
}

def normalize_track_name(track):
    """Normalize track name for matching"""
    track_upper = track.upper().strip()
    
    # Try direct mapping first
    if track_upper in TRACK_NORMALIZATIONS:
        return TRACK_NORMALIZATIONS[track_upper]
    
    # Try partial matches
    for key, value in TRACK_NORMALIZATIONS.items():
        if key in track_upper or track_upper in key:
            return value
    
    return track

def extract_track_from_pdf(filename):
    """Extract track code from PDF filename"""
    # Format: TRACKCODE##form.pdf (e.g., ANGLG1612form.pdf)
    basename = os.path.basename(filename)
    if 'form.pdf' in basename:
        # Remove form.pdf and date (1612)
        track_code = basename.replace('form.pdf', '').replace('1612', '')
        return track_code
    return None

# Read December 16 PDFs
print("=" * 80)
print("DECEMBER 16, 2025 - PDF AND RESULTS COVERAGE ANALYSIS")
print("=" * 80)

pdf_dir = "data"
dec16_pdfs = []
for filename in os.listdir(pdf_dir):
    if filename.endswith('.pdf') and '1612' in filename:
        dec16_pdfs.append(filename)

print(f"\n📁 PDFS FOUND FOR DECEMBER 16: {len(dec16_pdfs)}")
pdf_tracks = set()
for pdf in sorted(dec16_pdfs):
    track_code = extract_track_from_pdf(pdf)
    track_name = normalize_track_name(track_code) if track_code else "Unknown"
    pdf_tracks.add(track_name)
    print(f"  ✓ {pdf:<30} → {track_name}")

# Read December 16 results
results_file = "data/results_2025-12-16.csv"
csv_tracks = defaultdict(int)
total_races = 0

if os.path.exists(results_file):
    with open(results_file, 'r') as f:
        reader = csv.DictReader(f)
        for row in reader:
            track = row['Track']
            normalized = normalize_track_name(track)
            csv_tracks[normalized] += 1
            total_races += 1

print(f"\n📊 RESULTS FOUND FOR DECEMBER 16: {total_races} races across {len(csv_tracks)} tracks")
for track, count in sorted(csv_tracks.items()):
    print(f"  ✓ {track:<35} → {count:2d} races")

# Find mismatches
print("\n" + "=" * 80)
print("COVERAGE ANALYSIS")
print("=" * 80)

pdfs_without_results = pdf_tracks - set(csv_tracks.keys())
results_without_pdfs = set(csv_tracks.keys()) - pdf_tracks

if not pdfs_without_results and not results_without_pdfs:
    print("\n✅ PERFECT MATCH! All PDFs have results and all results have PDFs")
else:
    if pdfs_without_results:
        print(f"\n⚠️  PDFS WITHOUT RESULTS ({len(pdfs_without_results)}):")
        for track in sorted(pdfs_without_results):
            print(f"  ❌ {track}")
    
    if results_without_pdfs:
        print(f"\n⚠️  RESULTS WITHOUT PDFS ({len(results_without_pdfs)}):")
        for track in sorted(results_without_pdfs):
            races = csv_tracks[track]
            print(f"  ❌ {track:<35} → {races} races missing PDF")

# Summary
print("\n" + "=" * 80)
print("SUMMARY")
print("=" * 80)
print(f"Total PDFs for Dec 16:        {len(dec16_pdfs)}")
print(f"Total Results for Dec 16:     {total_races} races")
print(f"Tracks with PDFs:             {len(pdf_tracks)}")
print(f"Tracks with Results:          {len(csv_tracks)}")
print(f"PDFs without Results:         {len(pdfs_without_results)}")
print(f"Results without PDFs:         {len(results_without_pdfs)}")
print(f"Coverage Rate:                {len(pdf_tracks & set(csv_tracks.keys()))} / {max(len(pdf_tracks), len(csv_tracks))} tracks matched")
print("=" * 80)
