#!/usr/bin/env python3
"""
Comprehensive analysis of yesterday's (26/11/2025) predictions vs actual results.

This script:
1. Parses actual results from the user's input
2. Regenerates predictions from the Nov 26 PDFs only
3. Compares predictions vs actuals
4. Identifies issues in parsing, data transfer, and scoring
5. Provides recommendations for improvements
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

# Track name mappings (PDF codes to full names and vice versa)
TRACK_MAPPINGS = {
    # PDF code -> normalized name
    'TEMO': 'Temora',
    'TAST': 'Taree', 
    'GUNN': 'Gunnedah',
    'RICH': 'Richmond',
    'HEAL': 'Healesville',
    'GAWL': 'Gawler',
    'CAPA': 'Capalaba',  # BetDeluxe Capalaba
    'BDGO': 'Bendigo',
    'QLAK': 'Lakeside',  # Ladbrokes Q1 Lakeside
    'DRWN': 'Darwin',
    'BRAT': 'Ballarat',
    'SALE': 'Sale',
    'TEMOG': 'Temora',
    'TASTG': 'Taree',
    'GUNNG': 'Gunnedah', 
    'RICHG': 'Richmond',
    'HEALG': 'Healesville',
    'GAWLG': 'Gawler',
    'CAPAG': 'Capalaba',
    'BDGOG': 'Bendigo',
    'QLAKG': 'Lakeside',
    'DRWNG': 'Darwin',
    'BRATG': 'Ballarat',
    'SALEG': 'Sale',
    'CANNG': 'Gunnedah',  # Alternate code
    'ROCKG': 'Rockhampton',
}

# Actual results from user (26/11/25)
# Format: Track -> {Race#: [1st, 2nd, 3rd, 4th box numbers]}
ACTUAL_RESULTS_NOV_26 = {
    'Temora': {
        1: [1,7,4,6], 2: [1,4,3,6], 3: [8,3,5,7], 4: [8,1,6,2], 5: [1,8,7,5],
        6: [8,7,2,1], 7: [8,7,5,4], 8: [1,7,8,2], 9: [5,1,8,2], 10: [8,2,1,6]
    },
    'Taree': {
        1: [3,8,4,1], 2: [1,8,2,4]
        # R3-R12 are ABD (abandoned)
    },
    'Gunnedah': {
        1: [7,2,5,4], 2: [4,2,8,1], 3: [2,6,3,5], 4: [3,5,9,7], 5: [7,2,3,4],
        6: [7,4,6,5], 7: [7,4,1,8], 8: [6,1,8,2], 9: [5,2,1,3], 10: [5,7,3,4],
        11: [6,2,3,8], 12: [2,6,1,7]
    },
    'Richmond': {
        1: [1,6,4,8], 2: [7,8,4,1], 3: [8,7,3,1], 4: [8,6,7,1], 5: [8,6,2,1],
        6: [2,3,1,8], 7: [8,7,1,6], 8: [6,4,3,8], 9: [6,5,7,8], 10: [1,2,6,3],
        11: [1,2,8,3], 12: [5,2,6,1]
    },
    'Healesville': {
        1: [7,8,1,6], 2: [2,4,6,3], 3: [6,4,1,2], 4: [1,4,7,6], 5: [4,6,7,3],
        6: [2,8,5,6], 7: [1,7,2,8], 8: [3,2,5,4], 9: [8,2,4,3], 10: [6,1,8,4],
        11: [1,2,8,7], 12: [8,4,2,7]
    },
    'Gawler': {
        1: [1,6,4,8], 2: [7,5,2,8], 3: [2,4,1,8], 4: [2,5,8,4], 5: [1,5,2,9],
        6: [9,8,4,2], 7: [7,4,1,8], 8: [2,5,8,7], 9: [2,9,8,5], 10: [1,6,8,2]
    },
    'Capalaba': {  # BetDeluxe Capalaba
        1: [4,8,7,5], 2: [3,6,7,1], 3: [6,5,4,1], 4: [6,4,7,3], 5: [8,5,7,3],
        6: [7,4,6,5], 7: [1,4,7,8], 8: [2,8,3,7], 9: [2,7,4,6], 10: [1,2,8,6],
        11: [7,4,1,2], 12: [8,1,5,4]
    },
    'Bendigo': {
        1: [2,3,4,1], 2: [3,2,4,5], 3: [5,6,8,2], 4: [5,1,2,4], 5: [6,7,3,5],
        6: [2,8,6,3], 7: [3,6,1,8], 8: [4,8,1,7], 9: [2,4,3,7], 10: [2,3,7,1],
        11: [7,1,6,5], 12: [3,6,4,8]
    },
    'Lakeside': {  # Ladbrokes Q1 Lakeside
        1: [6,3,4,2], 2: [5,2,7,6], 3: [8,2,7,3], 4: [1,8,5,7], 5: [8,2,3,1],
        6: [1,7,4,8], 7: [1,6,7,9], 8: [2,1,8,3], 9: [1,2,8,4], 10: [8,3,2,1],
        11: [1,8,5,7], 12: [3,4,8,1]
    },
    'Darwin': {
        1: [6,4,5,3], 2: [1,7,2,8], 3: [8,4,5,2], 4: [2,1,5,4], 5: [6,8,3,5],
        6: [4,8,1,2], 7: [8,4,7,5], 8: [7,2,1,8], 9: [2,3,4,8], 10: [2,4,1,7],
        11: [2,1,5,8]
    },
    'Ballarat': {
        1: [4,7,2,1], 2: [2,8,4,5], 3: [3,8,1,6], 4: [5,7,4,6], 5: [2,1,8,4],
        6: [1,6,4,8], 7: [6,3,4,2], 8: [6,4,1,7], 9: [1,5,6,8], 10: [6,1,2,7],
        11: [1,2,7,8], 12: [2,7,8,5]
    },
    'Sale': {
        1: [5,6,8,4], 2: [8,1,0,1,6], 3: [8,4,1,5], 4: [2,1,7,5], 5: [8,4,3,1],
        6: [8,2,4,1], 7: [2,8,3,6], 8: [7,4,5,6], 9: [5,7,8,4], 10: [7,2,8,5],
        11: [4,7,1,6], 12: [7,8,1,6]
    }
}

# Rockhampton results appear to be missing from user input - check if PDF exists
# Also check for any track name mismatches


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
    # Remove .pdf extension and date part
    base = filename.replace('.pdf', '')
    # Extract track code (usually first 4-5 chars before date)
    for code in TRACK_MAPPINGS:
        if base.upper().startswith(code):
            return TRACK_MAPPINGS[code]
    # Try to extract from filename pattern
    match = re.match(r'^([A-Za-z]+)G?\d+', base)
    if match:
        code = match.group(1).upper()
        if code in TRACK_MAPPINGS:
            return TRACK_MAPPINGS[code]
    return base[:4]  # Fallback to first 4 chars


def run_analysis():
    """Run comprehensive analysis."""
    print("=" * 80)
    print("COMPREHENSIVE ANALYSIS: Nov 26, 2025 Predictions vs Actuals")
    print("=" * 80)
    
    # Step 1: Find all Nov 26 PDFs
    data_dir = Path("data")
    nov26_pdfs = list(data_dir.glob("*2611*.pdf"))
    
    print(f"\n📂 Found {len(nov26_pdfs)} PDFs for Nov 26, 2025:")
    for pdf in nov26_pdfs:
        track = get_track_from_filename(pdf.name)
        print(f"   - {pdf.name} -> {track}")
    
    # Step 2: Parse all Nov 26 PDFs and generate fresh predictions
    print("\n" + "=" * 80)
    print("STEP 1: Parsing Nov 26 PDFs and generating predictions...")
    print("=" * 80)
    
    all_predictions = []
    parsing_issues = []
    
    for pdf_path in nov26_pdfs:
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
            
            # Apply feature computation
            df = compute_features(df)
            
            # Store track info from filename for matching
            df['SourceTrack'] = track_name
            df['SourceFile'] = pdf_path.name
            
            print(f"   Parsed {len(df)} dogs across {df['RaceNumber'].nunique()} races")
            print(f"   Track in data: {df['Track'].unique()}")
            
            all_predictions.append(df)
            
        except Exception as e:
            parsing_issues.append(f"{pdf_path.name}: {str(e)}")
            print(f"   ❌ Error: {e}")
    
    if not all_predictions:
        print("\n❌ No predictions could be generated!")
        return
    
    combined_df = pd.concat(all_predictions, ignore_index=True)
    print(f"\n✅ Total: {len(combined_df)} dogs parsed from {len(nov26_pdfs)} PDFs")
    
    # Step 3: Get top picks per race
    print("\n" + "=" * 80)
    print("STEP 2: Extracting top picks per race...")
    print("=" * 80)
    
    picks = combined_df.sort_values(
        ['SourceTrack', 'RaceNumber', 'FinalScore'], 
        ascending=[True, True, False]
    ).groupby(['SourceTrack', 'RaceNumber']).first().reset_index()
    
    print(f"Generated {len(picks)} top picks")
    
    # Step 4: Compare with actual results
    print("\n" + "=" * 80)
    print("STEP 3: Comparing predictions with actual results...")
    print("=" * 80)
    
    total_races = 0
    correct_1st = 0
    correct_top3 = 0
    box_1_wins = 0
    our_box_1_picks = 0
    
    comparison_results = []
    
    for track, races in ACTUAL_RESULTS_NOV_26.items():
        track_picks = picks[picks['SourceTrack'].str.lower() == track.lower()]
        
        if track_picks.empty:
            # Try alternate matching
            track_picks = picks[picks['Track'].str.lower().str.contains(track.lower()[:4])]
        
        if track_picks.empty:
            print(f"\n⚠️  No predictions found for {track}")
            continue
            
        print(f"\n📍 {track}:")
        
        for race_num, results in races.items():
            if len(results) < 4:
                continue  # Skip incomplete results
                
            race_pick = track_picks[track_picks['RaceNumber'] == race_num]
            
            if race_pick.empty:
                continue
            
            total_races += 1
            our_pick_box = int(race_pick.iloc[0]['Box'])
            actual_winner = results[0]
            actual_top3 = results[:3]
            
            # Track box 1 stats
            if actual_winner == 1:
                box_1_wins += 1
            if our_pick_box == 1:
                our_box_1_picks += 1
            
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
    
    # Step 5: Calculate and display metrics
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
        
        print(f"\n📊 BOX 1 ANALYSIS:")
        print(f"   Box 1 actual wins: {box_1_wins} ({box_1_wins/total_races*100:.1f}%)")
        print(f"   Our Box 1 picks: {our_box_1_picks} ({our_box_1_picks/total_races*100:.1f}%)")
        
        # Baseline: Random selection would be ~12.5% (1/8 boxes)
        random_expected = total_races * 0.125
        print(f"\n📊 COMPARISON TO RANDOM:")
        print(f"   Random expected wins: {random_expected:.1f} ({12.5}%)")
        print(f"   Our wins: {correct_1st} ({win_rate:.1f}%)")
        if win_rate > 12.5:
            print(f"   ✅ {win_rate - 12.5:.1f}% better than random")
        else:
            print(f"   ❌ {12.5 - win_rate:.1f}% worse than random")
    
    # Step 6: Analyze issues
    print("\n" + "=" * 80)
    print("STEP 5: ISSUE ANALYSIS")
    print("=" * 80)
    
    if parsing_issues:
        print("\n⚠️  PARSING ISSUES:")
        for issue in parsing_issues:
            print(f"   - {issue}")
    
    # Analyze which box positions are winning vs what we're picking
    if comparison_results:
        df_results = pd.DataFrame(comparison_results)
        
        print("\n📊 BOX POSITION ANALYSIS:")
        print("\nActual Winner Box Distribution:")
        winner_dist = df_results['ActualWinner'].value_counts().sort_index()
        for box, count in winner_dist.items():
            pct = count / len(df_results) * 100
            print(f"   Box {box}: {count} wins ({pct:.1f}%)")
        
        print("\nOur Pick Box Distribution:")
        pick_dist = df_results['OurPick'].value_counts().sort_index()
        for box, count in pick_dist.items():
            pct = count / len(df_results) * 100
            win_count = len(df_results[(df_results['OurPick'] == box) & (df_results['IsWinner'])])
            print(f"   Box {box}: {count} picks, {win_count} wins ({win_count/count*100:.1f}% success)")
    
    # Step 7: Save detailed results
    print("\n" + "=" * 80)
    print("STEP 6: SAVING ANALYSIS RESULTS")
    print("=" * 80)
    
    if comparison_results:
        df_results = pd.DataFrame(comparison_results)
        output_path = "outputs/nov26_analysis_results.csv"
        df_results.to_csv(output_path, index=False)
        print(f"✅ Detailed results saved to: {output_path}")
    
    # Save the predictions we generated
    combined_df.to_csv("outputs/nov26_predictions.csv", index=False)
    print(f"✅ Full predictions saved to: outputs/nov26_predictions.csv")
    
    return comparison_results, combined_df


if __name__ == "__main__":
    results, predictions = run_analysis()
