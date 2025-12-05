#!/usr/bin/env python3
"""
Helper script to input actual winner data for speed matrix analysis
"""

import pandas as pd
from pathlib import Path
import sys

OUTPUTS_DIR = Path("outputs")
DATA_FILE = OUTPUTS_DIR / "todays_form_color.xlsx"
WINNER_OUTPUT = OUTPUTS_DIR / "actual_winners_25_11_25.csv"


def display_races(df):
    """Display all races for data entry"""
    races = df.groupby(['Track', 'RaceNumber']).first().reset_index()
    races = races.sort_values(['Track', 'RaceNumber'])
    
    print("\n" + "=" * 80)
    print("RACES ON 25/11/2025")
    print("=" * 80)
    print(f"\nTotal Races: {len(races)}\n")
    
    for i, row in races.iterrows():
        print(f"{i+1:3d}. {row['Track']:15s} Race {row['RaceNumber']:2.0f} - {row['RaceTime']}")
    
    return races


def show_race_details(df, track, race_num):
    """Show details of a specific race"""
    race_data = df[(df['Track'] == track) & (df['RaceNumber'] == race_num)].copy()
    race_data = race_data.sort_values('Box')
    
    print(f"\n{'Box':<5} {'Dog Name':<25} {'Trainer':<20} {'FinalScore':<12}")
    print("-" * 65)
    
    for _, dog in race_data.iterrows():
        print(f"{dog['Box']:<5.0f} {dog['DogName']:<25} {dog['Trainer']:<20} {dog['FinalScore']:<12.2f}")
    
    return race_data


def manual_entry_mode(df):
    """Interactive mode for manual winner entry"""
    races = display_races(df)
    winners = []
    
    print("\n" + "=" * 80)
    print("MANUAL WINNER ENTRY MODE")
    print("=" * 80)
    print("\nEnter winners for each race. Type 'q' to quit.\n")
    
    for i, race in races.iterrows():
        track = race['Track']
        race_num = race['RaceNumber']
        
        print(f"\n--- Race {i+1}/{len(races)}: {track} Race {race_num} ---")
        show_race_details(df, track, race_num)
        
        while True:
            box = input(f"\nEnter winning box number (or 's' to skip, 'q' to quit): ").strip()
            
            if box.lower() == 'q':
                print("\nQuitting entry mode...")
                return winners if len(winners) > 0 else None
            
            if box.lower() == 's':
                print("Skipping this race...")
                break
            
            try:
                box_num = int(box)
                race_data = df[(df['Track'] == track) & (df['RaceNumber'] == race_num)]
                winner = race_data[race_data['Box'] == box_num]
                
                if len(winner) == 0:
                    print(f"Box {box_num} not found in this race. Please try again.")
                    continue
                
                winner = winner.iloc[0]
                print(f"Winner: Box {box_num} - {winner['DogName']} (Trainer: {winner['Trainer']})")
                
                winners.append({
                    'Track': track,
                    'RaceNumber': race_num,
                    'RaceDate': winner['RaceDate'],
                    'WinningBox': box_num,
                    'WinningDog': winner['DogName']
                })
                break
                
            except ValueError:
                print("Invalid input. Please enter a box number.")
    
    return winners


def paste_mode():
    """Mode for pasting winner data from clipboard/text"""
    print("\n" + "=" * 80)
    print("PASTE MODE - Winner Data Entry")
    print("=" * 80)
    print("\nPaste your winner data in one of these formats:")
    print("\nFormat 1 (CSV):")
    print("Track,RaceNumber,WinningBox,WinningDog")
    print("SALE,11,4,Akina Jack")
    print("\nFormat 2 (Simple):")
    print("SALE 11 4")
    print("HEALESVILLE 8 7")
    print("\nPaste your data below, then press Ctrl+D (Unix) or Ctrl+Z (Windows) when done:")
    print("-" * 80)
    
    lines = []
    try:
        while True:
            line = input()
            lines.append(line)
    except EOFError:
        pass
    
    if not lines:
        print("No data entered.")
        return None
    
    # Try to parse the data
    winners = []
    
    # Check if it's CSV format
    if 'Track' in lines[0] or ',' in lines[0]:
        # CSV format
        for line in lines[1:] if 'Track' in lines[0] else lines:
            parts = [p.strip() for p in line.split(',')]
            if len(parts) >= 3:
                winners.append({
                    'Track': parts[0],
                    'RaceNumber': int(parts[1]),
                    'RaceDate': '2024-11-25',
                    'WinningBox': int(parts[2]),
                    'WinningDog': parts[3] if len(parts) > 3 else ''
                })
    else:
        # Simple format
        for line in lines:
            parts = line.split()
            if len(parts) >= 3:
                winners.append({
                    'Track': parts[0],
                    'RaceNumber': int(parts[1]),
                    'RaceDate': '2024-11-25',
                    'WinningBox': int(parts[2]),
                    'WinningDog': parts[3] if len(parts) > 3 else ''
                })
    
    print(f"\nParsed {len(winners)} winners")
    return winners


def main():
    """Main entry point"""
    print("=" * 80)
    print("GREYHOUND WINNER DATA ENTRY TOOL")
    print("=" * 80)
    
    # Load race data
    print(f"\nLoading race data from {DATA_FILE}...")
    df = pd.read_excel(DATA_FILE)
    total_races = len(df.groupby(['Track', 'RaceNumber']))
    print(f"Loaded {len(df)} runners across {total_races} races")
    
    # Choose mode
    print("\nSelect data entry mode:")
    print("  1. Manual entry (interactive)")
    print("  2. Paste mode (bulk entry)")
    print("  3. Load from file")
    
    choice = input("\nEnter choice (1-3): ").strip()
    
    winners = None
    
    if choice == '1':
        winners = manual_entry_mode(df)
    elif choice == '2':
        winners = paste_mode()
    elif choice == '3':
        filename = input("Enter filename: ").strip()
        try:
            winner_df = pd.read_csv(filename)
            winners = winner_df.to_dict('records')
            print(f"Loaded {len(winners)} winners from {filename}")
        except Exception as e:
            print(f"Error loading file: {e}")
            return
    else:
        print("Invalid choice")
        return
    
    if winners is None or len(winners) == 0:
        print("\nNo winner data to save. Exiting.")
        return
    
    # Save winners
    winner_df = pd.DataFrame(winners)
    winner_df.to_csv(WINNER_OUTPUT, index=False)
    
    print("\n" + "=" * 80)
    print(f"SUCCESS! Saved {len(winners)} winners to {WINNER_OUTPUT}")
    print("=" * 80)
    print("\nNext step: Run 'python analyze_speed_matrix.py' to perform analysis")
    

if __name__ == "__main__":
    main()
