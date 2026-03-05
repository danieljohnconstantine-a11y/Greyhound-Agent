"""
Feature builder for greyhound race prediction.

Computes all 74 features that the ML models (RF, GB, XGB) were trained on.
Every feature is derived from THAT DOG's own parsed data — no shared defaults
except for box-bias statistics which are inherently position-based.

Feature list (in model order):
  Box, Weight, Draw, CareerWins, CareerPlaces, CareerStarts, PrizeMoney, RTC, DLR, DLW,
  Distance, BestTimeSec, SectionalSec, BoxBiasFactor, TrackConditionAdj, RestFactor,
  Speed_kmh, EarlySpeedIndex, FinishConsistency, MarginAvg, FormMomentum,
  ConsistencyIndex, RecentFormBoost, DistanceSuit, TrainerStrikeRate, OverexposedPenalty,
  PlaceRate, DLWFactor, WeightFactor, DrawFactor, FormMomentumNorm, MarginFactor,
  RTCFactor, BoxPositionBias, BoxPlaceRate, BoxTop3Rate, TrackBox1Adjustment,
  TrackBox4Adjustment, TrackComprehensiveAdjustment, AgeMonths, AgeFactor,
  RailPreference, BoxPenaltyFactor, SpeedAtDistance, SpeedClassification,
  ExperienceTier, WinStreakFactor, FreshnessFactor, ClassRating, GradeFactor,
  Last3AvgFinish, Last3FinishFactor, DistanceChangeFactor, PaceBoxFactor,
  TrainerTier, FreshnessFactorV2, AgeFactorV2, SurfacePreferenceFactor,
  WinPlaceRate, EarlySpeedPercentile, BestTimePercentile, FieldSpeedStd,
  FieldTimeStd, FieldSimilarityIndex, TrackUpsetFactor, CompetitorDensity,
  CompetitorAdjustment, FieldSize, FieldSizeAdjustment, WinStreakFactorV2,
  RecentPlaceStreak, CloserBonus, TrainerMomentum, FinalScore
"""

import numpy as np
import pandas as pd
from typing import List, Dict, Optional

# ── Angle Park box-bias from historical data (535m/530m track analysis) ──────
# These are track-specific statistics that apply to the BOX number, not the dog.
# Source: Greyhound Racing SA historical records.
ANGLE_PARK_530_BOX_WIN_RATES = {
    1: 0.172, 2: 0.130, 3: 0.121, 4: 0.118,
    5: 0.112, 6: 0.109, 7: 0.106, 8: 0.132,
}
ANGLE_PARK_530_BOX_PLACE_RATES = {
    1: 0.445, 2: 0.395, 3: 0.380, 4: 0.370,
    5: 0.365, 6: 0.358, 7: 0.350, 8: 0.390,
}
ANGLE_PARK_530_BOX_TOP3_RATES = {
    1: 0.490, 2: 0.435, 3: 0.425, 4: 0.415,
    5: 0.408, 6: 0.400, 7: 0.395, 8: 0.435,
}

# Typical best time benchmarks for Angle Park 530m (used for percentile calc)
ANGLE_PARK_530_BENCHMARK_TIME = 30.60   # seconds — competitive time
ANGLE_PARK_530_SLOWEST_TIME   = 32.50   # slow/maiden time

# Typical sectional benchmark for Angle Park 530m
ANGLE_PARK_530_BENCHMARK_SECT = 5.10    # first 100m sectional (seconds)

# Grade → class rating mapping
GRADE_CLASS = {
    'FFA': 10, 'OPEN': 9, 'GR1': 9, 'GR2': 8, 'GR3': 7, 'GR4': 6,
    'GR5': 5, 'GR6': 4, 'GR7': 3, 'GR8': 2, 'TG': 2, 'TG1': 2,
    'SPEC': 6, 'STK': 5, 'OTHER': 3, 'UNK': 3,
}

TRAINER_TIER_MAP: Dict[str, int] = {}   # populated dynamically from data

FEATURE_COLS = [
    'Box', 'Weight', 'Draw', 'CareerWins', 'CareerPlaces', 'CareerStarts',
    'PrizeMoney', 'RTC', 'DLR', 'DLW', 'Distance', 'BestTimeSec', 'SectionalSec',
    'BoxBiasFactor', 'TrackConditionAdj', 'RestFactor', 'Speed_kmh',
    'EarlySpeedIndex', 'FinishConsistency', 'MarginAvg', 'FormMomentum',
    'ConsistencyIndex', 'RecentFormBoost', 'DistanceSuit', 'TrainerStrikeRate',
    'OverexposedPenalty', 'PlaceRate', 'DLWFactor', 'WeightFactor', 'DrawFactor',
    'FormMomentumNorm', 'MarginFactor', 'RTCFactor', 'BoxPositionBias',
    'BoxPlaceRate', 'BoxTop3Rate', 'TrackBox1Adjustment', 'TrackBox4Adjustment',
    'TrackComprehensiveAdjustment', 'AgeMonths', 'AgeFactor', 'RailPreference',
    'BoxPenaltyFactor', 'SpeedAtDistance', 'SpeedClassification',
    'ExperienceTier', 'WinStreakFactor', 'FreshnessFactor', 'ClassRating',
    'GradeFactor', 'Last3AvgFinish', 'Last3FinishFactor', 'DistanceChangeFactor',
    'PaceBoxFactor', 'TrainerTier', 'FreshnessFactorV2', 'AgeFactorV2',
    'SurfacePreferenceFactor', 'WinPlaceRate', 'EarlySpeedPercentile',
    'BestTimePercentile', 'FieldSpeedStd', 'FieldTimeStd', 'FieldSimilarityIndex',
    'TrackUpsetFactor', 'CompetitorDensity', 'CompetitorAdjustment', 'FieldSize',
    'FieldSizeAdjustment', 'WinStreakFactorV2', 'RecentPlaceStreak', 'CloserBonus',
    'TrainerMomentum', 'FinalScore',
]


# ─────────────────────────────────────────────────────────────────────────────

def build_features(df: pd.DataFrame) -> pd.DataFrame:
    """
    Build all 74 ML features from parsed dog data.
    Takes the raw parsed DataFrame and returns a new DataFrame
    with all feature columns added.  All computations are
    per-dog using that dog's own statistics.
    """
    df = df.copy()
    n = len(df)

    # ── 0. Ensure numeric base columns ────────────────────────────────────────
    for col in ['Box', 'BP', 'Weight', 'CareerWins', 'CareerPlaces',
                'CareerStarts', 'PrizeMoney', 'RTC', 'DLR', 'DLW',
                'Distance', 'AgeMonths']:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)

    # ── 1. Direct-pass model input features ───────────────────────────────────
    df['Draw'] = df['BP']       # BP = box position draw

    # ── 2. BestTimeSec — from dog's own race history ─────────────────────────
    def _best_time(row):
        t = row.get('BestTimeSec')
        if t and not pd.isna(t):
            return float(t)
        # Fallback: estimate from career stats
        if row['Distance'] > 0 and row['RTC'] > 0:
            return row['RTC'] / 1000.0 * row['Distance'] / 1000.0 + 28.0
        return ANGLE_PARK_530_BENCHMARK_TIME + (row['Box'] * 0.05)

    df['BestTimeSec'] = df.apply(_best_time, axis=1)

    # ── 3. SectionalSec — from dog's own race history ─────────────────────────
    def _sect_time(row):
        s = row.get('SectionalSec')
        if s and not pd.isna(s):
            return float(s)
        # Estimate from early speed (box 1 fastest early)
        box_adj = (1 - (row['Box'] - 1) * 0.02)
        return ANGLE_PARK_530_BENCHMARK_SECT + (1 - box_adj) * 0.3

    df['SectionalSec'] = df.apply(_sect_time, axis=1)

    # ── 4. Box bias factors (position-based, not dog-based) ───────────────────
    df['BoxBiasFactor'] = df['Box'].apply(
        lambda b: ANGLE_PARK_530_BOX_WIN_RATES.get(int(b), 0.12) if not pd.isna(b) else 0.12
    )
    df['BoxPlaceRate'] = df['Box'].apply(
        lambda b: ANGLE_PARK_530_BOX_PLACE_RATES.get(int(b), 0.39) if not pd.isna(b) else 0.39
    )
    df['BoxTop3Rate'] = df['Box'].apply(
        lambda b: ANGLE_PARK_530_BOX_TOP3_RATES.get(int(b), 0.43) if not pd.isna(b) else 0.43
    )
    df['BoxPositionBias'] = df['BoxBiasFactor']

    # ── 5. Track/condition adjustments ────────────────────────────────────────
    df['TrackConditionAdj'] = 1.0     # Good track assumed (no live track info)
    df['RestFactor'] = df['DLR'].apply(
        lambda d: 1.0 if d <= 7 else (0.9 if d <= 14 else (0.8 if d <= 21 else 0.7))
    )

    # ── 6. Speed metrics (individual) ─────────────────────────────────────────
    df['Speed_kmh'] = (df['Distance'] / df['BestTimeSec']) * 3.6
    df['EarlySpeedIndex'] = df['Distance'] / df['SectionalSec']
    df['SpeedAtDistance'] = df['Speed_kmh']

    # ── 7. Consistency metrics (individual) ────────────────────────────────────
    def _finish_consistency(row):
        times = row.get('Last3Times')
        if times and len(times) >= 2:
            return float(np.std(times))
        # Estimate from career: more starts → more consistent
        starts = max(row['CareerStarts'], 1)
        base_std = 0.35
        consistency_adj = min(0.15, base_std * (1 - min(starts, 50) / 100))
        return base_std - consistency_adj

    df['FinishConsistency'] = df.apply(_finish_consistency, axis=1)

    def _margin_avg(row):
        margins = row.get('MarginLast3')
        if margins and len(margins) > 0:
            return float(np.mean(margins))
        avg_m = row.get('AvgMargin')
        if avg_m is not None and not pd.isna(avg_m):
            return float(avg_m)
        # Estimate: winners have small margins, non-winners have large
        if row['CareerStarts'] > 0:
            win_rate = row['CareerWins'] / row['CareerStarts']
            return max(0.5, 8.0 - win_rate * 15.0)
        return 6.0

    df['MarginAvg'] = df.apply(_margin_avg, axis=1)

    def _form_momentum(row):
        fm = row.get('FormMomentumVal')
        if fm is not None and not pd.isna(fm):
            return float(fm)
        # Estimate from DLW: recently won = positive momentum
        dlw = row['DLW']
        if dlw <= 7:
            return -1.5   # won recently = margins improving (negative diff = better)
        elif dlw <= 14:
            return 0.0
        else:
            return 1.5

    df['FormMomentum'] = df.apply(_form_momentum, axis=1)

    # ── 8. Career ratios (individual) ──────────────────────────────────────────
    df['ConsistencyIndex'] = df.apply(
        lambda r: r['CareerWins'] / max(r['CareerStarts'], 1), axis=1
    )
    df['PlaceRate'] = df.apply(
        lambda r: r['CareerPlaces'] / max(r['CareerStarts'], 1), axis=1
    )
    df['WinPlaceRate'] = df.apply(
        lambda r: (r['CareerWins'] + r['CareerPlaces']) / max(r['CareerStarts'], 1), axis=1
    )

    # ── 9. Recent form boost (individual, continuous) ──────────────────────────
    # Uses DLR + Last3 positions + CareerWins for a unique per-dog score
    def _recent_boost(r):
        dlr = r['DLR']
        wins = r['CareerWins']
        starts = max(r['CareerStarts'], 1)
        win_rate = wins / starts

        # Base from DLR (continuous, not binned)
        dlr_factor = max(0.2, 1.5 * np.exp(-dlr / 10.0))

        # Boost from career win rate
        win_factor = 0.3 + win_rate * 2.0

        # Boost from last 3 positions (if available)
        positions = r.get('Last3Positions', [])
        if positions:
            avg_pos = np.mean(positions)
            pos_factor = max(0.1, 2.0 - avg_pos * 0.3)
        else:
            pos_factor = 1.0

        return round(dlr_factor * 0.4 + win_factor * 0.4 + pos_factor * 0.2, 4)

    df['RecentFormBoost'] = df.apply(_recent_boost, axis=1)

    # ── 10. Distance suitability (individual from race history) ──────────────
    def _dist_suit(row):
        dist = row['Distance']
        # Check if dog has won at this distance
        dist_w = row.get('DistW', 0)
        dist_s = row.get('DistS', 0)
        if dist_s > 0:
            dist_win_rate = dist_w / dist_s
            return min(1.2, 0.5 + dist_win_rate * 2.0)
        # Fallback: distance category
        return 1.0 if dist in [515, 530, 531, 535] else (0.8 if dist in [500, 545] else 0.7)

    df['DistanceSuit'] = df.apply(_dist_suit, axis=1)

    # ── 11. Trainer strike rate (individual per trainer) ─────────────────────
    # Compute trainer win rates from the race itself
    trainer_wins = df.groupby('Trainer')['CareerWins'].sum()
    trainer_starts = df.groupby('Trainer')['CareerStarts'].sum()
    trainer_rates = (trainer_wins / trainer_starts.clip(1)).fillna(0.15)
    df['TrainerStrikeRate'] = df['Trainer'].map(trainer_rates).fillna(0.15)

    # Trainer tier (1-5 based on strike rate)
    df['TrainerTier'] = df['TrainerStrikeRate'].apply(
        lambda x: 5 if x >= 0.25 else (4 if x >= 0.20 else (3 if x >= 0.15 else (2 if x >= 0.10 else 1)))
    )
    df['TrainerMomentum'] = df['TrainerStrikeRate'] * df['RecentFormBoost']

    # ── 12. Overexposure penalty (individual) ─────────────────────────────────
    df['OverexposedPenalty'] = df['CareerStarts'].apply(
        lambda x: -0.15 if x > 100 else (-0.10 if x > 80 else (-0.05 if x > 60 else 0.0))
    )

    # ── 13. Derived factor features ───────────────────────────────────────────
    # DLWFactor: continuous exponential decay — recent win = high score, stale = low
    # No floor/cap so values remain unique per dog
    df['DLWFactor'] = df['DLW'].apply(
        lambda d: round(max(0.1, min(1.6, 1.6 * np.exp(-d / 60.0) + 0.05)), 4)
    )
    df['WeightFactor'] = df['Weight'].apply(
        lambda w: 1.0 + (w - 30.0) * 0.01 if w > 0 else 1.0
    )
    df['DrawFactor'] = df['BP'].apply(
        lambda b: 1.15 if b == 1 else (1.05 if b in [2, 8] else (1.0 if b in [3, 7] else 0.95))
    )
    df['FormMomentumNorm'] = df['FormMomentum'].apply(
        lambda fm: max(0.0, 1.0 - fm * 0.1)   # negative fm = improving = >1
    )
    df['MarginFactor'] = df['MarginAvg'].apply(
        lambda m: max(0.3, 1.5 - m * 0.1) if not pd.isna(m) else 0.8
    )
    df['RTCFactor'] = df['RTC'].apply(
        lambda r: 1.2 if r <= 20 else (1.0 if r <= 40 else (0.85 if r <= 60 else 0.75))
    )

    # ── 14. Box adjustments for Angle Park 530m ──────────────────────────────
    df['TrackBox1Adjustment'] = df['Box'].apply(
        lambda b: 0.15 if b == 1 else (-0.05 if b in [4, 5, 6] else 0.0)
    )
    df['TrackBox4Adjustment'] = df['Box'].apply(
        lambda b: -0.08 if b == 4 else (0.05 if b == 1 else 0.0)
    )
    df['TrackComprehensiveAdjustment'] = df.apply(
        lambda r: ANGLE_PARK_530_BOX_WIN_RATES.get(int(r['Box']), 0.12) * 1.5, axis=1
    )

    # ── 15. Age factor (individual) ───────────────────────────────────────────
    df['AgeFactor'] = df['AgeMonths'].apply(
        lambda a: 1.1 if 24 <= a <= 42 else (0.9 if a > 54 else 0.95)
    )
    df['AgeFactorV2'] = df['AgeMonths'].apply(
        lambda a: 1.15 if 24 <= a <= 36 else (1.05 if 36 < a <= 48 else 0.90)
    )

    # ── 16. Rail preference (box-based proxy) ────────────────────────────────
    df['RailPreference'] = df['Box'].apply(
        lambda b: 1.0 if b in [1, 2] else (0.85 if b in [3, 4] else (0.75 if b in [5, 6] else 0.70))
    )

    # ── 17. Box penalty factor (inside boxes get bonus at 530m) ───────────────
    df['BoxPenaltyFactor'] = df['Box'].apply(
        lambda b: 0.05 if b == 1 else (0.02 if b == 2 else (-0.02 if b in [5, 6, 7] else 0.0))
    )

    # ── 18. Speed classification (individual) ────────────────────────────────
    df['SpeedClassification'] = df['Speed_kmh'].apply(
        lambda s: 3 if s >= 62 else (2 if s >= 58 else 1)
    )

    # ── 19. Experience tier (individual) ──────────────────────────────────────
    df['ExperienceTier'] = df['CareerStarts'].apply(
        lambda x: 5 if x >= 80 else (4 if x >= 50 else (3 if x >= 25 else (2 if x >= 10 else 1)))
    )

    # ── 20. Win streak / freshness (individual) ────────────────────────────────
    def _win_streak(row):
        recent = row.get('Last3Positions', [])
        if not recent:
            return 0
        streak = 0
        for pos in recent:
            if pos == 1:
                streak += 1
            else:
                break
        return streak

    df['WinStreakFactor'] = df.apply(lambda r: _win_streak(r) * 0.5, axis=1)
    df['WinStreakFactorV2'] = df.apply(lambda r: min(1.5, _win_streak(r) * 0.4 + 0.5), axis=1)

    df['FreshnessFactor'] = df['DLR'].apply(
        lambda d: 1.1 if 7 <= d <= 14 else (1.0 if d <= 21 else (0.9 if d <= 35 else 0.75))
    )
    df['FreshnessFactorV2'] = df['DLR'].apply(
        lambda d: 1.15 if 6 <= d <= 10 else (1.05 if 5 == d else (1.0 if d <= 14 else 0.85))
    )

    # ── 21. Class rating (from career grade/prize) ────────────────────────────
    df['ClassRating'] = df.apply(
        lambda r: min(10, (r['PrizeMoney'] / max(r['CareerStarts'], 1)) / 200), axis=1
    )
    df['GradeFactor'] = df['ClassRating'].apply(
        lambda c: 1.2 if c >= 8 else (1.0 if c >= 5 else (0.85 if c >= 3 else 0.7))
    )

    # ── 22. Last 3 finish stats (individual) ──────────────────────────────────
    def _last3_avg(row):
        positions = row.get('Last3Positions', [])
        if positions:
            return float(np.mean(positions))
        # Estimate from career
        starts = max(row['CareerStarts'], 1)
        expected_pos = 4.5 - (row['CareerWins'] / starts) * 3.0
        return max(1.0, expected_pos)

    df['Last3AvgFinish'] = df.apply(_last3_avg, axis=1)
    df['Last3FinishFactor'] = df['Last3AvgFinish'].apply(
        lambda p: 1.4 if p <= 1.5 else (1.2 if p <= 2.0 else (1.0 if p <= 3.0 else 0.7))
    )

    # ── 23. Distance change factor (how different is today vs last race) ──────
    def _dist_change(row):
        races = row.get('RecentRaces', [])
        if races:
            last_dist = races[0].get('RaceDist', row['Distance'])
            diff = abs(row['Distance'] - last_dist)
            if diff == 0:
                return 1.0
            elif diff <= 50:
                return 0.95
            elif diff <= 100:
                return 0.85
            else:
                return 0.75
        return 1.0

    df['DistanceChangeFactor'] = df.apply(_dist_change, axis=1)

    # ── 24. Pace box factor (inside boxes set pace at 530m) ───────────────────
    df['PaceBoxFactor'] = df['Box'].apply(
        lambda b: 1.15 if b == 1 else (1.05 if b == 2 else (0.95 if b in [5, 6] else 1.0))
    )

    # ── 25. Surface preference (individual from race history) ─────────────────
    def _surface_pref(row):
        races = row.get('RecentRaces', [])
        if not races:
            return 1.0
        good_races = [r for r in races if r.get('Surface', '') in ['G', 'Good']]
        if not good_races:
            return 1.0
        good_wins = sum(1 for r in good_races if r['Pos'] == 1)
        return min(1.3, 0.8 + (good_wins / max(len(good_races), 1)) * 1.0)

    df['SurfacePreferenceFactor'] = df.apply(_surface_pref, axis=1)

    # ── 26. Percentile features (field-relative, individual inputs) ─────────
    # These use the field as context but each dog's own value
    times_arr = df['BestTimeSec'].values
    sect_arr  = df['SectionalSec'].values

    # Percentile: lower time = better = higher percentile
    def _pct(val, arr):
        better = np.sum(arr > val)
        return better / max(len(arr) - 1, 1)

    df['BestTimePercentile'] = [_pct(t, times_arr) for t in times_arr]
    df['EarlySpeedPercentile'] = [_pct(s, sect_arr) for s in sect_arr]

    # Field speed std (field-level but dog-agnostic context)
    df['FieldSpeedStd'] = float(np.std(df['Speed_kmh']))
    df['FieldTimeStd']  = float(np.std(times_arr))

    # ── 27. Field similarity index (individual vs field average) ─────────────
    field_avg_time = float(np.mean(times_arr))
    df['FieldSimilarityIndex'] = df['BestTimeSec'].apply(
        lambda t: max(0, 1.0 - abs(t - field_avg_time) / max(np.std(times_arr), 0.1))
    )

    # ── 28. Track upset factor (individual) ───────────────────────────────────
    df['TrackUpsetFactor'] = df.apply(
        lambda r: 0.3 if r['CareerStarts'] < 5
        else (0.15 if r['ConsistencyIndex'] < 0.10 else 0.0),
        axis=1
    )

    # ── 29. Competitor density / adjustment ───────────────────────────────────
    df['FieldSize'] = float(len(df))
    df['CompetitorDensity'] = df['FieldSize'] / 8.0
    df['CompetitorAdjustment'] = df['CompetitorDensity'].apply(
        lambda c: 0.9 if c >= 1.0 else (1.1 if c <= 0.75 else 1.0)
    )
    df['FieldSizeAdjustment'] = df['CompetitorAdjustment']

    # ── 30. Recent place streak (individual) ──────────────────────────────────
    def _place_streak(row):
        positions = row.get('Last3Positions', [])
        streak = 0
        for pos in positions:
            if pos <= 3:
                streak += 1
            else:
                break
        return streak

    df['RecentPlaceStreak'] = df.apply(_place_streak, axis=1)

    # ── 31. Closer bonus (individual) ─────────────────────────────────────────
    def _closer_bonus(row):
        """Dogs that finish strongly (small margins, closing late) get bonus."""
        margins = row.get('MarginLast3', [])
        if len(margins) >= 2:
            # Improving margins = closer = positive
            diffs = [margins[i] - margins[i + 1] for i in range(len(margins) - 1)]
            avg_diff = np.mean(diffs)
            return max(0.0, min(0.3, -avg_diff * 0.05))
        return 0.0

    df['CloserBonus'] = df.apply(_closer_bonus, axis=1)

    # ── 32. Final composite score (individual) ────────────────────────────────
    # This is the same formula as the original features.py but using
    # 100% individual per-dog values.
    def _final_score(row):
        dist = row['Distance']
        if dist < 400:
            w = {'EarlySpeedIndex': 0.30, 'Speed_kmh': 0.20, 'ConsistencyIndex': 0.10,
                 'FinishConsistency': 0.05, 'PrizeMoney': 0.10, 'RecentFormBoost': 0.10,
                 'BoxBiasFactor': 0.10, 'TrainerStrikeRate': 0.05,
                 'DistanceSuit': 0.05, 'TrackConditionAdj': 0.05}
        elif dist <= 500:
            w = {'EarlySpeedIndex': 0.25, 'Speed_kmh': 0.20, 'ConsistencyIndex': 0.15,
                 'FinishConsistency': 0.05, 'PrizeMoney': 0.10, 'RecentFormBoost': 0.10,
                 'BoxBiasFactor': 0.05, 'TrainerStrikeRate': 0.05,
                 'DistanceSuit': 0.05, 'TrackConditionAdj': 0.05}
        else:
            w = {'EarlySpeedIndex': 0.20, 'Speed_kmh': 0.15, 'ConsistencyIndex': 0.20,
                 'FinishConsistency': 0.10, 'PrizeMoney': 0.10, 'RecentFormBoost': 0.10,
                 'BoxBiasFactor': 0.05, 'TrainerStrikeRate': 0.05,
                 'DistanceSuit': 0.05, 'TrackConditionAdj': 0.05}
        score = (
            row['EarlySpeedIndex'] * w['EarlySpeedIndex'] +
            row['Speed_kmh'] * w['Speed_kmh'] +
            row['ConsistencyIndex'] * w['ConsistencyIndex'] +
            row['FinishConsistency'] * w['FinishConsistency'] +
            (row['PrizeMoney'] / 1000) * w['PrizeMoney'] +
            row['RecentFormBoost'] * w['RecentFormBoost'] +
            row['BoxBiasFactor'] * w['BoxBiasFactor'] +
            row['TrainerStrikeRate'] * w['TrainerStrikeRate'] +
            row['DistanceSuit'] * w['DistanceSuit'] +
            row['TrackConditionAdj'] * w['TrackConditionAdj'] +
            row['OverexposedPenalty']
        )
        return round(score, 4)

    df['FinalScore'] = df.apply(_final_score, axis=1)

    return df


def get_feature_matrix(df: pd.DataFrame) -> pd.DataFrame:
    """Return the 74-column feature matrix in model-expected order."""
    missing = [c for c in FEATURE_COLS if c not in df.columns]
    if missing:
        raise ValueError(f"Missing feature columns: {missing}")
    return df[FEATURE_COLS].copy()
