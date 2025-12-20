#!/usr/bin/env python3
"""Check PDF-to-CSV coverage for December 17, 2025"""

import os
import csv

# Track name mappings from PDF codes to CSV names
TRACK_MAPPINGS = {
    'TEMOG1712': 'Temora',
    'TASTG1712': 'Taree',
    'GUNNG1712': 'Gunnedah',
    'RICHG1712': 'Richmond',
    'GAWLG1712': 'Gawler',
    'HEALG1712': 'Healesville',
    'CAPAG1712': 'BetDeluxe Capalaba',
    'BDGOG1712': 'Bendigo',
    'QLAKG1712': 'Ladbrokes Q1 Lakeside',
    'BRATG1712': 'Ballarat',
    'MEADG1712': 'Meadows',
    'ROCKG1712': 'BetDeluxe Rockhampton',
    'CANNG1712': 'Cannington'
}

def main():
    # Find PDFs for December 17, 2025
    pdfs = []
    for filename in os.listdir('data'):
        if filename.endswith('1712form.pdf'):
            pdfs.append(filename)
    
    pdfs.sort()
    
    # Load CSV results for December 17, 2025
    csv_tracks = {}
    with open('data/results_2025-12-17.csv', 'r') as f:
        reader = csv.DictReader(f)
        for row in reader:
            track = row['Track']
            if track not in csv_tracks:
                csv_tracks[track] = []
            csv_tracks[track].append(int(row['Race']))
    
    print("=" * 80)
    print("DECEMBER 17, 2025 COVERAGE ANALYSIS")
    print("=" * 80)
    
    # Check coverage
    all_match = True
    total_races = 0
    
    for pdf in pdfs:
        pdf_code = pdf.replace('form.pdf', '')
        track_name = TRACK_MAPPINGS.get(pdf_code, f"Unknown ({pdf_code})")
        
        if track_name in csv_tracks:
            race_count = len(csv_tracks[track_name])
            total_races += race_count
            print(f"✓ {track_name:30s} {race_count:2d} races -> PDF: {pdf}")
        else:
            print(f"✗ {track_name:30s} ?? races -> PDF: {pdf} [NO RESULTS!]")
            all_match = False
    
    print("\n" + "=" * 80)
    
    # Check for CSVs without PDFs
    csv_only = []
    for track in csv_tracks:
        found = False
        for pdf_code, pdf_track in TRACK_MAPPINGS.items():
            if pdf_track == track:
                found = True
                break
        if not found:
            csv_only.append(track)
    
    if csv_only:
        print("\nTRACKS WITH RESULTS BUT NO PDF:")
        for track in csv_only:
            print(f"  - {track}: {len(csv_tracks[track])} races")
        all_match = False
    
    print("\n" + "=" * 80)
    print("SUMMARY")
    print("=" * 80)
    print(f"PDFs found:        {len(pdfs)}")
    print(f"Tracks in CSV:     {len(csv_tracks)}")
    print(f"Total races:       {total_races}")
    
    if all_match and len(pdfs) == len(csv_tracks):
        print(f"\n🎉 PERFECT MATCH! All {len(pdfs)} tracks have both PDFs and results!")
    elif all_match:
        print(f"\n✓ All PDFs have matching results")
    else:
        print(f"\n⚠ Some mismatches found - check above")
    
    print("=" * 80)

if __name__ == '__main__':
    main()
