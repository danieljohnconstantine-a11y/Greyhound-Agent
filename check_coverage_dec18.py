#!/usr/bin/env python3
"""Check PDF coverage for December 18, 2025 race results."""

import os
import pandas as pd
from collections import defaultdict

# Read the December 18 results
results_file = 'data/results_2025-12-18.csv'
df = pd.read_csv(results_file)

# Count races per track
track_races = df.groupby('Track').size().to_dict()

print("=" * 80)
print("December 18, 2025 Race Results Coverage Analysis")
print("=" * 80)
print(f"\nTotal races added: {len(df)}")
print(f"Number of tracks: {len(track_races)}")
print("\nRaces per track:")
for track, count in sorted(track_races.items()):
    print(f"  {track}: {count} races")

# Check for corresponding PDFs
print("\n" + "=" * 80)
print("PDF Coverage Check")
print("=" * 80)

# List all PDFs for December 18
pdf_files = [f for f in os.listdir('data') if f.endswith('.pdf') and '1812' in f]

print(f"\nFound {len(pdf_files)} PDFs with date pattern '1812' (Dec 18, 2025)")

if pdf_files:
    print("\nPDF files found:")
    for pdf in sorted(pdf_files):
        print(f"  {pdf}")
    
    # Try to match PDFs to tracks
    print("\n" + "=" * 80)
    print("Track → PDF Mapping")
    print("=" * 80)
    
    track_mapping = {
        'Richmond Straight': 'RICHS',
        'Nowra': 'NOWR',
        'Wentworth Park': 'WENT',
        'Casino': 'CASI',
        'Shepparton': 'SHEP',
        'Mount Gambier': 'MTGA',
        'Ladbrokes Q Straight': 'QLAK',
        'Warrnambool': 'WARR',
        'Warragul': 'WARG',
        'Sandown': 'SAND',
        'Hobart': 'ELWK',
        'Ladbrokes Q2 Parklands': 'QLAK',
        'Mandurah': 'MAND'
    }
    
    matched = 0
    unmatched_tracks = []
    
    for track in sorted(track_races.keys()):
        races = track_races[track]
        # Try to find matching PDF
        track_code = track_mapping.get(track, track[:4].upper())
        matching_pdfs = [p for p in pdf_files if track_code in p.upper()]
        
        if matching_pdfs:
            print(f"✓ {track}: {races} races → PDF: {matching_pdfs[0]}")
            matched += 1
        else:
            print(f"✗ {track}: {races} races → NO PDF FOUND")
            unmatched_tracks.append(track)
    
    print(f"\n✓ Matched: {matched}/{len(track_races)} tracks")
    if unmatched_tracks:
        print(f"✗ Missing PDFs for: {', '.join(unmatched_tracks)}")
else:
    print("\n⚠ No PDFs found for December 18, 2025")
    print("   Please add PDFs to the data/ folder")

# Summary
print("\n" + "=" * 80)
print("Summary")
print("=" * 80)
print(f"Date: December 18, 2025")
print(f"Tracks: {len(track_races)}")
print(f"Total Races: {len(df)}")
print(f"PDFs Found: {len(pdf_files)}")

# Count total races across all CSV files
all_csvs = [f for f in os.listdir('data') if f.startswith('results_') and f.endswith('.csv')]
total_races = 0
for csv_file in all_csvs:
    try:
        df_temp = pd.read_csv(f'data/{csv_file}')
        total_races += len(df_temp)
    except:
        pass

print(f"\nTotal race results across all CSV files: {total_races}")
print(f"CSV files in database: {len(all_csvs)}")

# Count total PDFs
all_pdfs = [f for f in os.listdir('data') if f.endswith('.pdf')]
print(f"Total PDF files in database: {len(all_pdfs)}")

print("\n" + "=" * 80)
