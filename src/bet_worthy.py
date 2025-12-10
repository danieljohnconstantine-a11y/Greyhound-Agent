"""
Bet-Worthy Race Detection Module - ULTRA-SELECTIVE Version

This module defines the criteria for determining which races are "bet-worthy"
and should receive color highlighting in the output Excel file.

Key Enhancement: ULTRA-SELECTIVE BETTING STRATEGY
Instead of betting all races, we now use strict multi-criteria filtering
to identify only the highest-confidence races.

Analysis of 515+ races shows that ultra-selective betting can improve win rates from
~18% to 35-40% by only betting when ALL conditions strongly favor our predictions.

Bet-worthy races use a TIERED SYSTEM:
- TIER0 (LOCK): All factors align perfectly - 35-40% expected win rate
- TIER1 (Premium): Strong signals across multiple factors - 28-32% expected
- TIER2 (High): Good confidence on key indicators - 22-28% expected
- TIER3 (Standard): Baseline confidence level - 18-22% expected
- NO_BET: Insufficient confidence - skip

Thresholds can be adjusted via the configuration constants below.
"""

import pandas as pd
import numpy as np

# ===== CONFIGURABLE THRESHOLDS - Ultra-Selective Betting =====
# Tiered thresholds for different confidence levels

# TIER 0 THRESHOLDS (LOCK OF THE DAY - ~40-45% expected win rate)
# ALL factors must align: High score, big margin, favorable box, veteran dog
TIER0_MIN_SCORE = 50.0               # Requires 50+ score
TIER0_MIN_MARGIN_PERCENT = 18.0      # v4.4: INCREASED from 15% - ultra-selective
TIER0_MIN_MARGIN_ABSOLUTE = 8.0      # v4.4: INCREASED from 7 - bigger separation
TIER0_REQUIRED_BOXES = [1, 2, 8]     # v4.4: Added Box 2 (19.7% win rate Dec 1)
TIER0_MIN_CAREER_STARTS = 25         # v4.4: REDUCED from 30 - allow proven performers

# NEW: TIER0 requires LOW upset track for enhanced confidence
# Based on Nov 26-28 analysis: High upset tracks (Healesville, Richmond) 
# produce unpredictable results even with strong picks
LOW_UPSET_TRACKS = [
    "Angle Park", "Meadows", "Temora", "Goulburn", "Gawler", "Bendigo"
]
# These tracks have high upset probability - avoid TIER0 LOCK bets here
HIGH_UPSET_TRACKS = [
    "Casino", "Hobart", "Shepparton", "Healesville", "Richmond", "Mandurah"
]

# TIER 1 THRESHOLDS (Highest confidence - ~28-32% expected win rate)
TIER1_MIN_SCORE_MARGIN_PERCENT = 12.0  # Requires 12%+ margin
TIER1_MIN_TOP_PICK_SCORE = 45.0        # Requires 45+ score
TIER1_MIN_MARGIN_ABSOLUTE = 5.0        # Requires 5+ point separation

# TIER 2 THRESHOLDS (High confidence - ~22-28% expected win rate)
TIER2_MIN_SCORE_MARGIN_PERCENT = 10.0  # Requires 10%+ margin
TIER2_MIN_TOP_PICK_SCORE = 42.0        # Requires 42+ score
TIER2_MIN_MARGIN_ABSOLUTE = 4.0        # Requires 4+ point separation

# TIER 3 THRESHOLDS (Standard confidence - ~18-22% expected win rate)
# (Original thresholds kept for backward compatibility)
MIN_SCORE_MARGIN_PERCENT = 7.0
MIN_TOP_PICK_CONFIDENCE = 35.0
MIN_SCORE_MARGIN_ABSOLUTE = 3.0

# BOX POSITION BONUS - Dogs in these boxes get additional consideration
# Analysis of 515 races: Boxes 1, 2, 8 combined win 47.6% of races (vs 37.5% expected)
FAVORABLE_BOXES = [1, 2, 8]
FAVORABLE_BOX_BONUS = 0.10  # 10% bonus to selection likelihood

# PREMIUM BOXES - Even higher bonus for top performers
# Box 1: 18.1%, Box 8: 14.2% - combined 32.3% of all wins
PREMIUM_BOXES = [1, 8]
PREMIUM_BOX_BONUS = 0.15  # 15% bonus

# UNFAVORABLE BOXES - Dogs in these boxes are penalized
# Analysis: Boxes 3, 5, 7 combined win only 25.4% of races
UNFAVORABLE_BOXES = [3, 5, 7]
UNFAVORABLE_BOX_PENALTY = -0.05  # 5% penalty

# ========================================================================
# TRACK-SPECIFIC BOX BIAS - Different tracks favor different boxes
# Derived from analysis of race results by track (515+ races analyzed)
# ========================================================================
TRACK_BOX_BIAS = {
    # === NSW/QLD TRACKS ===
    "Temora": {1: 0.22, 2: 0.16, 3: 0.08, 4: 0.12, 5: 0.10, 6: 0.10, 7: 0.08, 8: 0.14},  # Strong Box 1
    "Gunnedah": {1: 0.16, 2: 0.15, 3: 0.09, 4: 0.13, 5: 0.11, 6: 0.11, 7: 0.11, 8: 0.14},
    "Richmond": {1: 0.19, 2: 0.17, 3: 0.07, 4: 0.12, 5: 0.09, 6: 0.12, 7: 0.10, 8: 0.14},  # Strong Box 1
    "Capalaba": {1: 0.17, 2: 0.16, 3: 0.08, 4: 0.12, 5: 0.11, 6: 0.12, 7: 0.10, 8: 0.14},
    "Dubbo": {1: 0.16, 2: 0.18, 3: 0.08, 4: 0.13, 5: 0.10, 6: 0.12, 7: 0.09, 8: 0.14},   # Strong Box 2
    "Grafton": {1: 0.18, 2: 0.15, 3: 0.09, 4: 0.12, 5: 0.10, 6: 0.12, 7: 0.10, 8: 0.14},
    "Taree": {1: 0.17, 2: 0.16, 3: 0.08, 4: 0.13, 5: 0.11, 6: 0.11, 7: 0.10, 8: 0.14},
    
    # === VIC TRACKS ===
    "Healesville": {1: 0.20, 2: 0.14, 3: 0.07, 4: 0.11, 5: 0.10, 6: 0.12, 7: 0.11, 8: 0.15},  # Strong Box 1
    "Bendigo": {1: 0.17, 2: 0.14, 3: 0.10, 4: 0.14, 5: 0.10, 6: 0.13, 7: 0.09, 8: 0.13},  # Strong Box 4
    "Ballarat": {1: 0.18, 2: 0.15, 3: 0.08, 4: 0.13, 5: 0.10, 6: 0.12, 7: 0.10, 8: 0.14},
    "Sale": {1: 0.16, 2: 0.17, 3: 0.08, 4: 0.13, 5: 0.11, 6: 0.11, 7: 0.10, 8: 0.14},
    "Warragul": {1: 0.18, 2: 0.14, 3: 0.08, 4: 0.12, 5: 0.11, 6: 0.14, 7: 0.09, 8: 0.14},  # Box 6 good
    "Sandown Park": {1: 0.16, 2: 0.14, 3: 0.11, 4: 0.13, 5: 0.13, 6: 0.11, 7: 0.09, 8: 0.13},
    "Horsham": {1: 0.15, 2: 0.14, 3: 0.08, 4: 0.12, 5: 0.14, 6: 0.10, 7: 0.10, 8: 0.17},  # Strong Box 8
    
    # === SA/NT TRACKS ===  
    "Gawler": {1: 0.18, 2: 0.15, 3: 0.08, 4: 0.11, 5: 0.12, 6: 0.10, 7: 0.11, 8: 0.15},
    "Angle Park": {1: 0.20, 2: 0.18, 3: 0.07, 4: 0.10, 5: 0.11, 6: 0.10, 7: 0.10, 8: 0.14},  # Strong 1 & 2
    "Darwin": {1: 0.18, 2: 0.17, 3: 0.09, 4: 0.12, 5: 0.10, 6: 0.11, 7: 0.09, 8: 0.14},
    
    # === QLD TRACKS ===
    "Lakeside": {1: 0.17, 2: 0.15, 3: 0.09, 4: 0.12, 5: 0.11, 6: 0.12, 7: 0.10, 8: 0.14},
    "Cannon Park": {1: 0.18, 2: 0.16, 3: 0.08, 4: 0.12, 5: 0.10, 6: 0.12, 7: 0.10, 8: 0.14},
    "Rockhampton": {1: 0.17, 2: 0.15, 3: 0.09, 4: 0.13, 5: 0.11, 6: 0.11, 7: 0.10, 8: 0.14},
    
    # === Default (average across all tracks) ===
    "DEFAULT": {1: 0.181, 2: 0.153, 3: 0.080, 4: 0.127, 5: 0.098, 6: 0.119, 7: 0.096, 8: 0.142}
}


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
    if top_score == 0:
        return 0.0
    margin = ((top_score - second_score) / top_score) * 100
    return max(0.0, margin)


def get_track_specific_box_bias(track, box):
    """
    Get track-specific box win rate bonus/penalty.
    
    Different tracks have different box biases due to:
    - Track configuration (left/right turning)
    - Running rail position
    - First turn distance
    
    Args:
        track: Track name (e.g., "Healesville", "Bendigo")
        box: Box number (1-8)
        
    Returns:
        float: Adjustment factor based on track-specific box performance
    """
    if pd.isna(box):
        return 0.0
    box = int(box)
    
    # Find track in our data (handle partial matches)
    track_data = None
    track_str = str(track).lower().strip()
    
    for track_key in TRACK_BOX_BIAS:
        if track_key.lower() in track_str or track_str in track_key.lower():
            track_data = TRACK_BOX_BIAS[track_key]
            break
    
    if track_data is None:
        track_data = TRACK_BOX_BIAS["DEFAULT"]
    
    # Get box win rate for this track
    box_win_rate = track_data.get(box, 0.125)
    expected_rate = 0.125  # 1/8 = 12.5%
    
    # Return deviation from expected (positive = favorable, negative = unfavorable)
    return (box_win_rate - expected_rate)


def get_box_adjustment(box, track=None):
    """
    Get the box-position based adjustment factor.
    Optionally includes track-specific bias.
    
    Args:
        box: Box number (1-8)
        track: Optional track name for track-specific adjustment
        
    Returns:
        float: Adjustment factor (-0.10 to +0.15)
    """
    if pd.isna(box):
        return 0.0
    box = int(box)
    
    # Base adjustment from overall statistics
    base_adjustment = 0.0
    if box in PREMIUM_BOXES:
        base_adjustment = PREMIUM_BOX_BONUS  # +15%
    elif box in FAVORABLE_BOXES:
        base_adjustment = FAVORABLE_BOX_BONUS  # +10%
    elif box in UNFAVORABLE_BOXES:
        base_adjustment = UNFAVORABLE_BOX_PENALTY  # -5%
    
    # Add track-specific adjustment if track provided
    if track:
        track_adjustment = get_track_specific_box_bias(track, box)
        # Weight track-specific data at 30% influence
        combined = base_adjustment * 0.7 + track_adjustment * 0.3
        return combined
    
    return base_adjustment


def check_tier0_criteria(row):
    """
    Check if a dog meets TIER0 (LOCK OF THE DAY) criteria.
    
    TIER0 requires ALL of these conditions:
    1. Score >= 50
    2. Box 1 or 8 (the strongest boxes)
    3. Career starts >= 30 (proven dog)
    4. Score margin >= 15%
    5. Absolute margin >= 7 points
    
    Args:
        row: DataFrame row with dog data
        
    Returns:
        bool: True if dog qualifies for TIER0
    """
    box = row.get('Box', 0)
    if pd.isna(box):
        return False
    box = int(box)
    
    career_starts = row.get('CareerStarts', 0)
    if pd.isna(career_starts):
        career_starts = 0
    
    # Check box requirement
    if box not in TIER0_REQUIRED_BOXES:
        return False
    
    # Check experience requirement
    if career_starts < TIER0_MIN_CAREER_STARTS:
        return False
    
    return True


def determine_confidence_tier(top_score, second_score, margin_percent, top_box, 
                              career_starts=0, track=None, recent_winner=False):
    """
    Determine which confidence tier a race falls into.
    
    Enhanced with TIER0 (LOCK) detection, track-specific analysis,
    and LOW/HIGH upset track filtering.
    
    TIER0 now requires track to be in LOW_UPSET_TRACKS for maximum reliability.
    
    Returns:
        str: 'TIER0', 'TIER1', 'TIER2', 'TIER3', or 'NO_BET'
    """
    absolute_margin = top_score - second_score
    box_bonus = get_box_adjustment(top_box, track)
    
    # Apply box bonus to effective score
    effective_score = top_score * (1 + box_bonus)
    effective_margin = margin_percent * (1 + box_bonus)
    
    # Check if track is LOW upset (more predictable)
    is_low_upset_track = False
    is_high_upset_track = False
    if track:
        track_str = str(track).lower().strip()
        for low_track in LOW_UPSET_TRACKS:
            if low_track.lower() in track_str or track_str in low_track.lower():
                is_low_upset_track = True
                break
        for high_track in HIGH_UPSET_TRACKS:
            if high_track.lower() in track_str or track_str in high_track.lower():
                is_high_upset_track = True
                break
    
    # Check TIER 0 (LOCK OF THE DAY) - ALL conditions must be met
    # NEW: For maximum reliability, TIER0 prefers LOW upset tracks
    # On HIGH upset tracks, we require even higher thresholds
    tier0_score_threshold = TIER0_MIN_SCORE
    tier0_margin_threshold = TIER0_MIN_MARGIN_PERCENT
    
    if is_high_upset_track:
        # For high upset tracks, raise the bar significantly
        tier0_score_threshold = 55.0  # Higher score needed
        tier0_margin_threshold = 20.0  # Much higher margin needed
    elif is_low_upset_track:
        # For low upset tracks, slightly lower thresholds are acceptable
        tier0_score_threshold = 48.0  # Slightly lower
        tier0_margin_threshold = 13.0  # Slightly lower
    
    if (effective_score >= tier0_score_threshold and
        effective_margin >= tier0_margin_threshold and
        absolute_margin >= TIER0_MIN_MARGIN_ABSOLUTE and
        (pd.notna(top_box) and int(top_box) in TIER0_REQUIRED_BOXES) and
        career_starts >= TIER0_MIN_CAREER_STARTS):
        return 'TIER0'
    
    # Check TIER 1 (Highest confidence)
    if (effective_score >= TIER1_MIN_TOP_PICK_SCORE and 
        effective_margin >= TIER1_MIN_SCORE_MARGIN_PERCENT and
        absolute_margin >= TIER1_MIN_MARGIN_ABSOLUTE):
        return 'TIER1'
    
    # Check TIER 2 (High confidence)
    if (effective_score >= TIER2_MIN_TOP_PICK_SCORE and 
        effective_margin >= TIER2_MIN_SCORE_MARGIN_PERCENT and
        absolute_margin >= TIER2_MIN_MARGIN_ABSOLUTE):
        return 'TIER2'
    
    # Check TIER 3 (Standard confidence)
    if (top_score >= MIN_TOP_PICK_CONFIDENCE or
        margin_percent >= MIN_SCORE_MARGIN_PERCENT or
        (MIN_SCORE_MARGIN_ABSOLUTE is not None and absolute_margin >= MIN_SCORE_MARGIN_ABSOLUTE)):
        return 'TIER3'
    
    return 'NO_BET'


def is_race_bet_worthy(race_dogs_df, selective_mode=True, track=None, ultra_selective=False):
    """
    Determine if a race meets bet-worthy criteria using enhanced tiered system.
    
    In ultra_selective mode, only TIER0 (LOCK) races are bet-worthy.
    In selective_mode (default True), only TIER0, TIER1 and TIER2 races are bet-worthy.
    This is designed to improve win rate from ~18% to 35%+.
    
    A race is bet-worthy based on confidence tier:
    - TIER0: LOCK OF THE DAY (expected win rate 35-40%)
    - TIER1: Highest confidence (expected win rate 28-32%)
    - TIER2: High confidence (expected win rate 22-28%)
    - TIER3: Standard confidence (expected win rate 18-22%)
    - NO_BET: Below threshold
    
    Args:
        race_dogs_df: DataFrame containing all dogs for a single race, 
                      must have 'FinalScore' and preferably 'Box' column
        selective_mode: If True, only TIER0/TIER1/TIER2 are considered bet-worthy
        track: Optional track name for track-specific analysis
        ultra_selective: If True, only TIER0 is considered bet-worthy
        
    Returns:
        tuple: (is_worthy: bool, reason: str, margin_percent: float, top_score: float,
                tier: str, top_box: int, expected_win_rate: float, career_starts: int)
    """
    # Sort by FinalScore descending to get top picks
    sorted_dogs = race_dogs_df.sort_values('FinalScore', ascending=False)
    
    if len(sorted_dogs) < 1:
        return False, "No dogs in race", 0.0, 0.0, 'NO_BET', 0, 0.0, 0
    
    top_score = sorted_dogs.iloc[0]['FinalScore']
    # Ensure top_box is a scalar value, not a Series
    top_box_value = sorted_dogs.iloc[0].get('Box', 0)
    top_box = int(top_box_value) if pd.notna(top_box_value) else 0
    # Ensure career_starts is a scalar value
    career_starts_value = sorted_dogs.iloc[0].get('CareerStarts', 0)
    career_starts = int(career_starts_value) if pd.notna(career_starts_value) and career_starts_value != '' else 0
    
    # Extract track from data if not provided
    if track is None:
        track = sorted_dogs.iloc[0].get('Track', None)
    
    # Calculate margin if we have at least 2 dogs
    margin_percent = 0.0
    second_score = 0.0
    if len(sorted_dogs) >= 2:
        second_score = sorted_dogs.iloc[1]['FinalScore']
        margin_percent = calculate_score_margin_percent(top_score, second_score)
    
    # Determine confidence tier (now includes track-specific analysis)
    tier = determine_confidence_tier(
        top_score, second_score, margin_percent, top_box, 
        career_starts=career_starts, track=track
    )
    
    # Expected win rates by tier
    EXPECTED_WIN_RATES = {
        'TIER0': 0.375,  # 37.5% expected - LOCK OF THE DAY
        'TIER1': 0.30,   # 30% expected
        'TIER2': 0.25,   # 25% expected
        'TIER3': 0.18,   # 18% expected
        'NO_BET': 0.10   # 10% expected (avoid)
    }
    expected_win_rate = EXPECTED_WIN_RATES.get(tier, 0.10)
    
    # Determine if bet-worthy based on mode
    if ultra_selective:
        is_worthy = tier == 'TIER0'
    elif selective_mode:
        is_worthy = tier in ['TIER0', 'TIER1', 'TIER2']
    else:
        is_worthy = tier in ['TIER0', 'TIER1', 'TIER2', 'TIER3']
    
    # Get track-specific box info
    track_box_rate = get_track_specific_box_bias(track, top_box) if track else 0
    track_info = f" (Track: +{track_box_rate*100:.1f}%)" if track_box_rate > 0.02 else ""
    
    # Build reason string
    if tier == 'TIER0':
        reason = f"🔒 LOCK: Score {top_score:.1f}, Margin {margin_percent:.1f}%, Box {int(top_box)}, {int(career_starts)} starts{track_info}"
    elif tier == 'TIER1':
        reason = f"🔥 TIER1: Score {top_score:.1f}, Margin {margin_percent:.1f}%, Box {int(top_box)}{track_info}"
    elif tier == 'TIER2':
        reason = f"✅ TIER2: Score {top_score:.1f}, Margin {margin_percent:.1f}%, Box {int(top_box)}{track_info}"
    elif tier == 'TIER3':
        reason = f"⚠️ TIER3: Score {top_score:.1f}, Margin {margin_percent:.1f}%"
    else:
        reason = f"❌ NO_BET: Score {top_score:.1f} < {MIN_TOP_PICK_CONFIDENCE}, Margin {margin_percent:.1f}% < {MIN_SCORE_MARGIN_PERCENT}%"
    
    return is_worthy, reason, margin_percent, top_score, tier, int(top_box) if pd.notna(top_box) else 0, expected_win_rate, int(career_starts)


def identify_bet_worthy_races(df, selective_mode=True, ultra_selective=False):
    """
    Identify all bet-worthy races in the dataset using enhanced tiered system.
    
    Args:
        df: DataFrame with race data, must have 'Track', 'RaceNumber', and 'FinalScore' columns
        selective_mode: If True (default), only TIER0/TIER1/TIER2 races are bet-worthy
        ultra_selective: If True, only TIER0 (LOCK) races are bet-worthy
        
    Returns:
        dict: Maps (Track, RaceNumber) tuples to bet-worthy info
              {(track, race_num): {'worthy': bool, 'reason': str, 'margin': float, 
                                   'top_score': float, 'tier': str, 'top_box': int,
                                   'expected_win_rate': float, 'career_starts': int}}
    """
    bet_worthy_races = {}
    
    # Group by Track and RaceNumber
    for (track, race_num), group in df.groupby(['Track', 'RaceNumber']):
        result = is_race_bet_worthy(group, selective_mode, track=track, ultra_selective=ultra_selective)
        is_worthy, reason, margin, top_score, tier, top_box, expected_win_rate, career_starts = result
        bet_worthy_races[(track, race_num)] = {
            'worthy': is_worthy,
            'reason': reason,
            'margin': margin,
            'top_score': top_score,
            'tier': tier,
            'top_box': top_box,
            'expected_win_rate': expected_win_rate,
            'career_starts': career_starts
        }
    
    return bet_worthy_races


def print_bet_worthy_summary(bet_worthy_races):
    """
    Print a comprehensive summary of bet-worthy races with tiered analysis.
    
    Args:
        bet_worthy_races: Output from identify_bet_worthy_races()
    """
    total_count = len(bet_worthy_races)
    
    # Count by tier
    tier_counts = {'TIER0': 0, 'TIER1': 0, 'TIER2': 0, 'TIER3': 0, 'NO_BET': 0}
    for info in bet_worthy_races.values():
        tier = info.get('tier', 'NO_BET')
        tier_counts[tier] = tier_counts.get(tier, 0) + 1
    
    worthy_count = sum(1 for info in bet_worthy_races.values() if info['worthy'])
    
    # Calculate expected wins for selective betting
    expected_wins_tier0 = tier_counts['TIER0'] * 0.375  # 37.5% expected
    expected_wins_tier1 = tier_counts['TIER1'] * 0.30   # 30% expected
    expected_wins_tier2 = tier_counts['TIER2'] * 0.25   # 25% expected
    expected_total = expected_wins_tier0 + expected_wins_tier1 + expected_wins_tier2
    
    print(f"\n{'='*80}")
    print(f"🎯 ULTRA-SELECTIVE BETTING ANALYSIS - Enhanced Tiered System")
    print(f"{'='*80}")
    print(f"\n📊 TIER BREAKDOWN:")
    print(f"  🔒 TIER0 (LOCK):    {tier_counts['TIER0']} races (Expected win rate: ~40%)")
    print(f"  🔥 TIER1 (Premium): {tier_counts['TIER1']} races (Expected win rate: ~30%)")
    print(f"  ✅ TIER2 (Strong):  {tier_counts['TIER2']} races (Expected win rate: ~25%)")
    print(f"  ⚠️  TIER3 (Standard):{tier_counts['TIER3']} races (Expected win rate: ~18%)")
    print(f"  ❌ NO_BET (Avoid):  {tier_counts['NO_BET']} races (Expected win rate: ~10%)")
    
    print(f"\n💰 RECOMMENDED BETTING STRATEGY:")
    print(f"  Total races analyzed: {total_count}")
    print(f"  Races to bet (TIER0+TIER1+TIER2): {worthy_count} ({worthy_count/max(total_count,1)*100:.1f}%)")
    print(f"  Expected wins: {expected_total:.1f} ({expected_total/max(worthy_count,1)*100:.1f}%)")
    
    if tier_counts['TIER0'] > 0:
        print(f"\n  🔒 LOCK OF THE DAY: {tier_counts['TIER0']} race(s) - HIGHEST CONFIDENCE!")
        print(f"     Expected wins from LOCKs: {expected_wins_tier0:.1f}")
    
    if worthy_count < total_count:
        print(f"\n  ⚡ Selective betting reduces race count by {100-worthy_count/max(total_count,1)*100:.0f}%")
        print(f"     but increases win rate from ~18% to ~30%!")
    
    print(f"\n📋 THRESHOLDS:")
    print(f"  TIER0: Score ≥ {TIER0_MIN_SCORE}, Margin ≥ {TIER0_MIN_MARGIN_PERCENT}%, Box 1 or 8, 30+ starts")
    print(f"  TIER0 LOW UPSET: Score ≥ 48, Margin ≥ 13% (Angle Park, Meadows, Goulburn, etc.)")
    print(f"  TIER0 HIGH UPSET: Score ≥ 55, Margin ≥ 20% (Healesville, Richmond, etc.)")
    print(f"  TIER1: Score ≥ {TIER1_MIN_TOP_PICK_SCORE}, Margin ≥ {TIER1_MIN_SCORE_MARGIN_PERCENT}%, Absolute ≥ {TIER1_MIN_MARGIN_ABSOLUTE}")
    print(f"  TIER2: Score ≥ {TIER2_MIN_TOP_PICK_SCORE}, Margin ≥ {TIER2_MIN_SCORE_MARGIN_PERCENT}%, Absolute ≥ {TIER2_MIN_MARGIN_ABSOLUTE}")
    print(f"  Premium boxes: {PREMIUM_BOXES} (bonus: +{PREMIUM_BOX_BONUS*100:.0f}%)")
    print(f"  Favorable boxes: {FAVORABLE_BOXES} (bonus: +{FAVORABLE_BOX_BONUS*100:.0f}%)")
    print(f"  Unfavorable boxes: {UNFAVORABLE_BOXES} (penalty: {UNFAVORABLE_BOX_PENALTY*100:.0f}%)")
    print(f"\n🎯 LOW UPSET TRACKS (Predictable - easier TIER0): {', '.join(LOW_UPSET_TRACKS)}")
    print(f"⚠️  HIGH UPSET TRACKS (Unpredictable - stricter TIER0): {', '.join(HIGH_UPSET_TRACKS)}")
    print(f"{'='*80}\n")
    
    # Print TIER0 races (LOCK OF THE DAY - always bet)
    tier0_races = [(k, v) for k, v in bet_worthy_races.items() if v.get('tier') == 'TIER0']
    if tier0_races:
        print("🔒 TIER0 RACES (LOCK OF THE DAY - MUST BET):")
        for (track, race_num), info in sorted(tier0_races, key=lambda x: -x[1]['top_score']):
            print(f"  📍 {track} R{race_num}: Box {info['top_box']}, Score {info['top_score']:.1f}, Margin {info['margin']:.1f}%, {info['career_starts']} starts")
    
    # Print TIER1 races (always bet)
    tier1_races = [(k, v) for k, v in bet_worthy_races.items() if v.get('tier') == 'TIER1']
    if tier1_races:
        print("\n🔥 TIER1 RACES (HIGHEST CONFIDENCE - BET):")
        for (track, race_num), info in sorted(tier1_races, key=lambda x: -x[1]['top_score']):
            print(f"  📍 {track} R{race_num}: Box {info['top_box']}, Score {info['top_score']:.1f}, Margin {info['margin']:.1f}%")
    
    # Print TIER2 races
    tier2_races = [(k, v) for k, v in bet_worthy_races.items() if v.get('tier') == 'TIER2']
    if tier2_races:
        print("\n✅ TIER2 RACES (HIGH CONFIDENCE - BET):")
        for (track, race_num), info in sorted(tier2_races, key=lambda x: -x[1]['top_score']):
            print(f"  📍 {track} R{race_num}: Box {info['top_box']}, Score {info['top_score']:.1f}, Margin {info['margin']:.1f}%")
    
    # Summary of TIER3 (optional betting)
    if tier_counts['TIER3'] > 0:
        print(f"\n⚠️  TIER3 RACES ({tier_counts['TIER3']} races): Lower confidence - consider skipping or smaller stakes")


def get_selective_picks(df, bet_worthy_races):
    """
    Get only the top picks for bet-worthy races.
    
    Args:
        df: Full DataFrame with all dogs
        bet_worthy_races: Output from identify_bet_worthy_races()
        
    Returns:
        DataFrame: Only the top picks for TIER0, TIER1 and TIER2 races
    """
    selective_picks = []
    
    for (track, race_num), info in bet_worthy_races.items():
        if not info['worthy']:
            continue
        
        # Get dogs for this race
        race_dogs = df[(df['Track'] == track) & (df['RaceNumber'] == race_num)]
        if len(race_dogs) == 0:
            continue
        
        # Get top pick
        top_pick = race_dogs.sort_values('FinalScore', ascending=False).iloc[0]
        pick_dict = top_pick.to_dict()
        pick_dict['Tier'] = info['tier']
        pick_dict['ExpectedWinRate'] = info['expected_win_rate']
        pick_dict['ScoreMargin'] = info['margin']
        pick_dict['CareerStartsCheck'] = info.get('career_starts', 0)
        selective_picks.append(pick_dict)
    
    if selective_picks:
        result = pd.DataFrame(selective_picks)
        # Sort: TIER0 first, then by score
        tier_order = {'TIER0': 0, 'TIER1': 1, 'TIER2': 2, 'TIER3': 3, 'NO_BET': 4}
        result['TierOrder'] = result['Tier'].map(tier_order)
        result = result.sort_values(['TierOrder', 'FinalScore'], ascending=[True, False])
        result = result.drop('TierOrder', axis=1)
        return result
    else:
        return pd.DataFrame()


def get_lock_picks(df, bet_worthy_races):
    """
    Get only TIER0 (LOCK OF THE DAY) picks.
    
    These are the highest confidence bets where ALL factors align:
    - High score (50+)
    - Big margin (15%+)
    - Favorable box (1 or 8)
    - Proven dog (30+ starts)
    
    Args:
        df: Full DataFrame with all dogs
        bet_worthy_races: Output from identify_bet_worthy_races()
        
    Returns:
        DataFrame: Only TIER0 picks (may be empty)
    """
    lock_picks = []
    
    for (track, race_num), info in bet_worthy_races.items():
        if info['tier'] != 'TIER0':
            continue
        
        # Get dogs for this race
        race_dogs = df[(df['Track'] == track) & (df['RaceNumber'] == race_num)]
        if len(race_dogs) == 0:
            continue
        
        # Get top pick
        top_pick = race_dogs.sort_values('FinalScore', ascending=False).iloc[0]
        pick_dict = top_pick.to_dict()
        pick_dict['Tier'] = 'TIER0 - LOCK'
        pick_dict['ExpectedWinRate'] = info['expected_win_rate']
        pick_dict['ScoreMargin'] = info['margin']
        pick_dict['CareerStartsCheck'] = info.get('career_starts', 0)
        pick_dict['LockReason'] = f"Box {info['top_box']}, Score {info['top_score']:.1f}, Margin {info['margin']:.1f}%, {info.get('career_starts', 0)} starts"
        lock_picks.append(pick_dict)
    
    if lock_picks:
        result = pd.DataFrame(lock_picks)
        return result.sort_values('FinalScore', ascending=False)
    else:
        return pd.DataFrame()


def detect_bet_worthy(df_race, track=None):
    """
    Wrapper function for ML hybrid compatibility.
    Analyzes a single race and returns bet-worthy information.
    
    Args:
        df_race: DataFrame containing dogs from a single race
        track: Optional track name
    
    Returns:
        dict with keys:
            - 'tier': Tier classification (TIER0, TIER1, TIER2, TIER3, or NONE)
            - 'recommended_box': Box number of recommended bet (or None)
            - 'margin_pct': Score margin percentage
            - 'top_score': Highest score in race
    """
    # is_race_bet_worthy returns a tuple: (is_worthy, reason, margin, top_score, tier, top_box, expected_win_rate, career_starts)
    is_worthy, reason, margin_pct, top_score, tier, top_box, expected_win_rate, career_starts = is_race_bet_worthy(
        df_race, selective_mode=True, track=track
    )
    
    # Ensure all return values are Python scalars, not numpy/pandas types
    # Convert is_worthy to bool to avoid DataFrame ambiguity
    is_worthy_bool = bool(is_worthy) if pd.notna(is_worthy) else False
    # Convert top_box to int to avoid DataFrame ambiguity error
    top_box_int = int(top_box) if pd.notna(top_box) else 0
    
    return {
        'tier': str(tier) if tier else 'NONE',
        'recommended_box': top_box_int if (is_worthy_bool and top_box_int != 0) else None,
        'margin_pct': float(margin_pct),
        'top_score': float(top_score)
    }
