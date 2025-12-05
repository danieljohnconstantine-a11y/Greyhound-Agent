#!/usr/bin/env python3
"""
Analysis of Nov 29, 2025 race predictions vs actual results.
"""

import pandas as pd
import numpy as np
import pdfplumber
import os
import sys
import re
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

from src.parser import parse_race_form
from src.features import compute_features

# Track name mappings
TRACK_MAPPINGS = {
    'TAST': 'Taree',
    'TASTG': 'Taree',
    'DUBB': 'Dubbo',
    'DUBBG': 'Dubbo',
    'WENP': 'Wentworth Park',
    'WENPG': 'Wentworth Park',
    'GARD': 'Gardens',
    'GARDG': 'Gardens',
    'BRAT': 'Ballarat',
    'BRATG': 'Ballarat',
    'QLAK': 'Lakeside',
    'QLAKG': 'Lakeside',
    'SAND': 'Sandown',
    'SANDG': 'Sandown',
    'CANN': 'Cannington',
    'CANNG': 'Cannington',
}

# Actual results for Nov 29 - 8 tracks (from user input)
ACTUAL_RESULTS_NOV_29 = {
    'Taree': {
        1: [2,3,4,5], 2: [6,7,1,8], 3: [1,6,4,2], 4: [3,4,1,2], 5: [6,1,3,8],
        6: [6,7,2,4], 7: [6,7,4,3], 8: [8,2,1,7], 9: [2,8,1,3], 10: [8,6,2,3],
        11: [4,1,7,6]
    },
    'Dubbo': {
        1: [7,6,3,8], 2: [7,1,3,2], 3: [3,4,5,8], 4: [1,5,3,2], 5: [1,4,2,3],
        6: [8,5,1,4], 7: [5,8,1,4], 8: [1,8,2,7], 9: [8,1,3,6], 10: [8,2,6,3],
        11: [4,3,1,7]
    },
    'Wentworth Park': {
        1: [2,4,6,3], 2: [1,7,4,5], 3: [8,2,6,1], 4: [1,2,5,4], 5: [1,2,7,8],
        6: [4,2,6,1], 7: [4,5,2,3], 8: [1,6,5,4], 9: [3,5,2,7], 10: [6,2,1,9]
    },
    'Gardens': {  # Ladbrokes Gardens
        1: [5,6,7,1], 2: [6,5,2,1], 3: [2,8,4,5], 4: [5,8,7,2], 5: [5,8,2,3],
        6: [2,7,8,5], 7: [5,8,7,4], 8: [5,4,8,2], 9: [1,9,10,5], 10: [4,7,8,2],
        11: [6,5,2,1], 12: [4,6,5,1]
    },
    'Ballarat': {
        1: [2,1,7,5], 2: [4,8,3,5], 3: [4,5,8,3], 4: [4,8,2,3], 5: [6,4,8,7],
        6: [1,4,5,8], 7: [7,1,6,3], 8: [7,6,4,8], 9: [4,7,3,6], 10: [8,7,3,6],
        11: [4,8,3,10], 12: [8,6,7,2]
    },
    'Lakeside': {  # Ladbrokes Q1 Lakeside
        1: [4,1,7,5], 2: [5,8,2,4], 3: [8,6,2,1], 4: [1,8,2,7], 5: [4,2,9,5],
        6: [6,3,1,8], 7: [1,6,3,4], 8: [3,7,8,6], 9: [5,8,4,2], 10: [8,4,2,5]
    },
    'Sandown': {
        1: [1,7,2,3], 2: [3,2,6,8], 3: [1,2,4,7], 4: [1,2,10,4], 5: [1,8,2,6],
        6: [4,5,6,3], 7: [2,7,3,1], 8: [8,4,3,2], 9: [7,1,2,4], 10: [2,5,1,6],
        11: [3,4,8,2], 12: [8,3,2,1]
    },
    'Cannington': {
        1: [6,2,1,4], 2: [6,1,8,4], 3: [2,10,3,5], 4: [2,1,4,5], 5: [4,5,3,1],
        6: [1,5,3,4], 7: [1,4,7,8], 8: [1,2,3,7], 9: [2,1,8,3], 10: [3,6,5,2],
        11: [8,4,2,1], 12: [1,3,6,4]
    }
}


def extract_text_from_pdf(pdf_path):
    """Extract text from PDF file."""
    text = ""
    try:
        with pdfplumber.open(pdf_path) as pdf:
            for page in pdf.pages:
                page_text = page.extract_text()
                if page_text:
                    text += page_text + "\n"
    except Exception as e:
        print(f"Error reading {pdf_path}: {e}")
    return text


def get_track_from_filename(filename):
    """Extract track name from PDF filename."""
    base = filename.replace('.pdf', '')
    for code in TRACK_MAPPINGS:
        if base.upper().startswith(code):
            return TRACK_MAPPINGS[code]
    match = re.match(r'^([A-Za-z]+)G?\d+', base)
    if match:
        code = match.group(1).upper()
        if code in TRACK_MAPPINGS:
            return TRACK_MAPPINGS[code]
    return base[:4]


def run_analysis():
    """Run comprehensive analysis for Nov 29."""
    print("=" * 80)
    print("COMPREHENSIVE ANALYSIS: Nov 29, 2025 Predictions vs Actuals")
    print("=" * 80)
    
    # Find all Nov 29 PDFs
    data_dir = Path("data")
    nov29_pdfs = list(data_dir.glob("*2911*.pdf"))
    
    print(f"\n📂 Found {len(nov29_pdfs)} PDFs for Nov 29, 2025:")
    for pdf in nov29_pdfs:
        track = get_track_from_filename(pdf.name)
        print(f"   - {pdf.name} -> {track}")
    
    # Parse all Nov 29 PDFs and generate predictions
    print("\n" + "=" * 80)
    print("STEP 1: Parsing Nov 29 PDFs and generating predictions...")
    print("=" * 80)
    
    all_predictions = []
    parsing_issues = []
    
    for pdf_path in nov29_pdfs:
        track_name = get_track_from_filename(pdf_path.name)
        print(f"\n📄 Processing: {pdf_path.name} ({track_name})")
        
        try:
            raw_text = extract_text_from_pdf(pdf_path)
            if not raw_text.strip():
                parsing_issues.append(f"{pdf_path.name}: Empty text extracted")
                continue
                
            df = parse_race_form(raw_text)
            if df.empty:
                parsing_issues.append(f"{pdf_path.name}: No dogs parsed")
                continue
            
            df = compute_features(df)
            df['SourceTrack'] = track_name
            df['SourceFile'] = pdf_path.name
            
            print(f"   Parsed {len(df)} dogs across {df['RaceNumber'].nunique()} races")
            all_predictions.append(df)
            
        except Exception as e:
            parsing_issues.append(f"{pdf_path.name}: {str(e)}")
            print(f"   ❌ Error: {e}")
    
    if not all_predictions:
        print("\n❌ No predictions could be generated!")
        return
    
    combined_df = pd.concat(all_predictions, ignore_index=True)
    print(f"\n✅ Total: {len(combined_df)} dogs parsed from {len(nov29_pdfs)} PDFs")
    
    # Get top picks per race
    print("\n" + "=" * 80)
    print("STEP 2: Extracting top picks per race...")
    print("=" * 80)
    
    picks = combined_df.sort_values(
        ['SourceTrack', 'RaceNumber', 'FinalScore'], 
        ascending=[True, True, False]
    ).groupby(['SourceTrack', 'RaceNumber']).first().reset_index()
    
    print(f"Generated {len(picks)} top picks")
    
    # Compare with actual results
    print("\n" + "=" * 80)
    print("STEP 3: Comparing predictions with actual results...")
    print("=" * 80)
    
    total_races = 0
    correct_1st = 0
    correct_top3 = 0
    box_wins = {1: 0, 2: 0, 3: 0, 4: 0, 5: 0, 6: 0, 7: 0, 8: 0}
    our_picks = {1: 0, 2: 0, 3: 0, 4: 0, 5: 0, 6: 0, 7: 0, 8: 0}
    
    comparison_results = []
    missed_winners = []
    
    for track, races in ACTUAL_RESULTS_NOV_29.items():
        track_picks = picks[picks['SourceTrack'].str.lower() == track.lower()]
        
        if track_picks.empty:
            track_picks = picks[picks['Track'].str.lower().str.contains(track.lower()[:4])]
        
        if track_picks.empty:
            print(f"\n⚠️  No predictions found for {track}")
            continue
            
        print(f"\n📍 {track}:")
        
        for race_num, results in races.items():
            if len(results) < 4:
                continue
                
            race_pick = track_picks[track_picks['RaceNumber'] == race_num]
            
            if race_pick.empty:
                continue
            
            total_races += 1
            our_pick_box = int(race_pick.iloc[0]['Box'])
            actual_winner = results[0]
            actual_top3 = results[:3]
            
            # Track box stats
            if actual_winner <= 8:
                box_wins[actual_winner] += 1
            if our_pick_box <= 8:
                our_picks[our_pick_box] += 1
            
            is_winner = our_pick_box == actual_winner
            is_top3 = our_pick_box in actual_top3
            
            if is_winner:
                correct_1st += 1
                status = "✅ WIN"
            elif is_top3:
                correct_top3 += 1
                status = "🟡 TOP3"
            else:
                status = "❌ MISS"
                # Track missed winner details
                missed_winners.append({
                    'Track': track,
                    'Race': race_num,
                    'OurPick': our_pick_box,
                    'ActualWinner': actual_winner,
                    'OurScore': race_pick.iloc[0]['FinalScore'],
                    'OurDog': race_pick.iloc[0]['DogName']
                })
            
            dog_name = race_pick.iloc[0]['DogName']
            score = race_pick.iloc[0]['FinalScore']
            
            comparison_results.append({
                'Track': track,
                'Race': race_num,
                'OurPick': our_pick_box,
                'OurDog': dog_name,
                'OurScore': score,
                'ActualWinner': actual_winner,
                'ActualTop3': actual_top3,
                'IsWinner': is_winner,
                'IsTop3': is_top3
            })
            
            print(f"   R{race_num}: Pick Box {our_pick_box} ({dog_name[:20]}) | Actual: {results[0]}-{results[1]}-{results[2]}-{results[3]} | {status}")
    
    # Calculate and display metrics
    print("\n" + "=" * 80)
    print("STEP 4: PERFORMANCE METRICS")
    print("=" * 80)
    
    if total_races > 0:
        win_rate = correct_1st / total_races * 100
        top3_rate = (correct_1st + correct_top3) / total_races * 100
        
        print(f"\n📊 OVERALL RESULTS:")
        print(f"   Total Races Analyzed: {total_races}")
        print(f"   Correct Winners (1st): {correct_1st} ({win_rate:.1f}%)")
        print(f"   In Top 3: {correct_1st + correct_top3} ({top3_rate:.1f}%)")
        print(f"   Missed: {total_races - correct_1st - correct_top3}")
        
        print(f"\n📊 BOX WIN DISTRIBUTION (Nov 29):")
        for box in sorted(box_wins.keys()):
            pct = box_wins[box] / total_races * 100 if total_races > 0 else 0
            print(f"   Box {box}: {box_wins[box]} wins ({pct:.1f}%)")
        
        print(f"\n📊 OUR PICK DISTRIBUTION:")
        for box in sorted(our_picks.keys()):
            pct = our_picks[box] / total_races * 100 if total_races > 0 else 0
            print(f"   Box {box}: {our_picks[box]} picks ({pct:.1f}%)")
        
        # Analyze missed winners patterns
        print("\n" + "=" * 80)
        print("STEP 5: MISSED WINNERS ANALYSIS")
        print("=" * 80)
        
        if missed_winners:
            missed_df = pd.DataFrame(missed_winners)
            print(f"\nTotal missed: {len(missed_df)}")
            
            print("\nMissed winner box distribution:")
            for box in sorted(missed_df['ActualWinner'].unique()):
                count = len(missed_df[missed_df['ActualWinner'] == box])
                pct = count / len(missed_df) * 100
                print(f"   Box {box}: {count} ({pct:.1f}%)")
            
            print("\nOur pick box when we missed:")
            for box in sorted(missed_df['OurPick'].unique()):
                count = len(missed_df[missed_df['OurPick'] == box])
                pct = count / len(missed_df) * 100
                print(f"   Box {box}: {count} picks ({pct:.1f}%)")
        
        # vs Random comparison
        random_expected = total_races * 0.125
        print(f"\n📊 COMPARISON TO RANDOM:")
        print(f"   Random expected wins: {random_expected:.1f} ({12.5}%)")
        print(f"   Our wins: {correct_1st} ({win_rate:.1f}%)")
        if win_rate > 12.5:
            print(f"   ✅ {win_rate - 12.5:.1f}% better than random")
        else:
            print(f"   ❌ {12.5 - win_rate:.1f}% worse than random")
    
    # Save results
    if comparison_results:
        df_results = pd.DataFrame(comparison_results)
        output_path = "outputs/nov29_analysis_results.csv"
        df_results.to_csv(output_path, index=False)
        print(f"\n✅ Detailed results saved to: {output_path}")
        
        # Save Nov 29 results data
        results_output = "data/results_2025-11-29.csv"
        df_results.to_csv(results_output, index=False)
        print(f"✅ Results data saved to: {results_output}")
    
    return comparison_results, combined_df, missed_winners


if __name__ == "__main__":
    results, predictions, missed = run_analysis()
