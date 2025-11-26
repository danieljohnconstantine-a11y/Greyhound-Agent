"""
Bet-Worthy Race Detection Module

This module defines the criteria for determining which races are "bet-worthy"
and should receive color highlighting in the output Excel file.

Bet-worthy races are those where:
1. The top pick's score margin vs. the next highest is above a threshold (default: 7%)
   - Margin is calculated as: (top_score - second_score) / top_score * 100
   - This represents how much smaller the second score is relative to the top score
2. OR the model confidence for the top pick is above a threshold (default: 35%)

Thresholds can be adjusted via the configuration constants below.
"""

import pandas as pd

# ===== CONFIGURABLE THRESHOLDS =====
# Adjust these values to tune bet-worthy detection sensitivity

# Minimum score margin percentage between top pick and second pick (as percentage of top pick's score)
# Example: If top pick has score 50 and second pick has 45, margin is 10%
MIN_SCORE_MARGIN_PERCENT = 7.0

# Minimum absolute confidence/score for the top pick to be considered bet-worthy
MIN_TOP_PICK_CONFIDENCE = 35.0

# Alternative: Minimum absolute score difference (not percentage-based)
# Set to None to disable, or specify a value like 3.0
MIN_SCORE_MARGIN_ABSOLUTE = 3.0


def calculate_score_margin_percent(top_score, second_score):
    """
    Calculate the percentage margin between top and second scores.
    
    This calculates how much smaller the second score is relative to the top score:
    margin = (top_score - second_score) / top_score * 100
    
    For example:
    - If top_score=50 and second_score=45, margin is 10% (second is 10% behind first)
    - If top_score=40 and second_score=40, margin is 0%
    
    Args:
        top_score: Score of the top pick
        second_score: Score of the second pick
        
    Returns:
        Percentage margin (0-100) representing how much second_score lags behind top_score
    """
    if top_score <= 0:
        return 0.0
    margin = ((top_score - second_score) / top_score) * 100
    return max(0.0, margin)


def is_race_bet_worthy(race_dogs_df):
    """
    Determine if a race meets bet-worthy criteria.
    
    A race is bet-worthy if ANY of the following conditions are met:
    1. Top pick score margin vs. next highest >= MIN_SCORE_MARGIN_PERCENT
    2. Top pick score >= MIN_TOP_PICK_CONFIDENCE
    3. Absolute score difference >= MIN_SCORE_MARGIN_ABSOLUTE (if enabled)
    
    Args:
        race_dogs_df: DataFrame containing all dogs for a single race, 
                      must have 'FinalScore' column
        
    Returns:
        tuple: (is_worthy: bool, reason: str, margin_percent: float, top_score: float)
    """
    # Sort by FinalScore descending to get top picks
    sorted_dogs = race_dogs_df.sort_values('FinalScore', ascending=False)
    
    if len(sorted_dogs) < 1:
        return False, "No dogs in race", 0.0, 0.0
    
    top_score = sorted_dogs.iloc[0]['FinalScore']
    
    # Check condition 2: Top pick confidence threshold
    if top_score >= MIN_TOP_PICK_CONFIDENCE:
        return True, f"Top pick confidence {top_score:.2f} >= {MIN_TOP_PICK_CONFIDENCE}", 0.0, top_score
    
    # Need at least 2 dogs for margin calculations
    if len(sorted_dogs) < 2:
        return False, "Only one dog in race", 0.0, top_score
    
    second_score = sorted_dogs.iloc[1]['FinalScore']
    
    # Check condition 3: Absolute margin threshold (if enabled)
    if MIN_SCORE_MARGIN_ABSOLUTE is not None:
        absolute_margin = top_score - second_score
        if absolute_margin >= MIN_SCORE_MARGIN_ABSOLUTE:
            return True, f"Absolute margin {absolute_margin:.2f} >= {MIN_SCORE_MARGIN_ABSOLUTE}", 0.0, top_score
    
    # Check condition 1: Percentage margin threshold
    margin_percent = calculate_score_margin_percent(top_score, second_score)
    
    if margin_percent >= MIN_SCORE_MARGIN_PERCENT:
        return True, f"Score margin {margin_percent:.1f}% >= {MIN_SCORE_MARGIN_PERCENT}%", margin_percent, top_score
    
    return False, f"Margin {margin_percent:.1f}% < {MIN_SCORE_MARGIN_PERCENT}%, confidence {top_score:.2f} < {MIN_TOP_PICK_CONFIDENCE}", margin_percent, top_score


def identify_bet_worthy_races(df):
    """
    Identify all bet-worthy races in the dataset.
    
    Args:
        df: DataFrame with race data, must have 'Track', 'RaceNumber', and 'FinalScore' columns
        
    Returns:
        dict: Maps (Track, RaceNumber) tuples to bet-worthy info
              {(track, race_num): {'worthy': bool, 'reason': str, 'margin': float, 'top_score': float}}
    """
    bet_worthy_races = {}
    
    # Group by Track and RaceNumber
    for (track, race_num), group in df.groupby(['Track', 'RaceNumber']):
        is_worthy, reason, margin, top_score = is_race_bet_worthy(group)
        bet_worthy_races[(track, race_num)] = {
            'worthy': is_worthy,
            'reason': reason,
            'margin': margin,
            'top_score': top_score
        }
    
    return bet_worthy_races


def print_bet_worthy_summary(bet_worthy_races):
    """
    Print a summary of bet-worthy races.
    
    Args:
        bet_worthy_races: Output from identify_bet_worthy_races()
    """
    worthy_count = sum(1 for info in bet_worthy_races.values() if info['worthy'])
    total_count = len(bet_worthy_races)
    
    print(f"\n{'='*70}")
    print(f"BET-WORTHY RACES ANALYSIS")
    print(f"{'='*70}")
    print(f"Total races: {total_count}")
    print(f"Bet-worthy races: {worthy_count} ({worthy_count/total_count*100:.1f}%)")
    print(f"Non-bet-worthy races: {total_count - worthy_count}")
    print(f"\nThresholds:")
    print(f"  - Score margin percentage: {MIN_SCORE_MARGIN_PERCENT}%")
    print(f"  - Top pick confidence: {MIN_TOP_PICK_CONFIDENCE}")
    if MIN_SCORE_MARGIN_ABSOLUTE is not None:
        print(f"  - Absolute score margin: {MIN_SCORE_MARGIN_ABSOLUTE}")
    print(f"{'='*70}\n")
    
    if worthy_count > 0:
        print("Bet-worthy races:")
        for (track, race_num), info in sorted(bet_worthy_races.items()):
            if info['worthy']:
                print(f"  {track} Race {race_num}: {info['reason']}")
