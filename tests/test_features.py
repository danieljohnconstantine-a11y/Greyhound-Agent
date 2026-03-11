"""
tests/test_features.py
======================
Validates that all 75 ML features are:
  1. Present in FEATURE_COLS (with expected count)
  2. Computed by compute_features() for every dog
  3. Dog-specific features produce unique per-dog values
  4. Track-specific adjustments differ between tracks

Run: python tests/test_features.py
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

import numpy as np
import pandas as pd

# ---------------------------------------------------------------------------
FEATURE_COLS = [
    'Box','Draw','CareerWins','CareerPlaces','CareerStarts','PrizeMoney',
    'RTC','DLR','DLW','Distance','BestTimeSec','SectionalSec',
    'RestFactor','Speed_kmh','EarlySpeedIndex',
    'FinishConsistency','MarginAvg','FormMomentum','ConsistencyIndex',
    'RecentFormBoost','DistanceSuit','TrainerStrikeRate','OverexposedPenalty',
    'PlaceRate','DLWFactor','DrawFactor','FormMomentumNorm',
    'MarginFactor','RTCFactor','BoxPositionBias','BoxPlaceRate','BoxTop3Rate',
    'TrackBox1Adjustment','TrackBox4Adjustment','TrackComprehensiveAdjustment',
    'TrackBoxWinRatePct','TrackBoxRank','BoxWinAdvantage',
    'AgeMonths','AgeFactor','RailPreference','BoxPenaltyFactor','SpeedAtDistance',
    'SpeedClassification','ExperienceTier','WinStreakFactor','FreshnessFactor',
    'ClassRating','GradeFactor','Last3AvgFinish','Last3FinishFactor',
    'DistanceChangeFactor','PaceBoxFactor','TrainerTier','FreshnessFactorV2',
    'AgeFactorV2','SurfacePreferenceFactor','WinPlaceRate','EarlySpeedPercentile',
    'BestTimePercentile','FieldSpeedStd','FieldTimeStd','TimeVsField',
    'SpeedVsField','FieldSimilarityIndex','TrackUpsetFactor','CompetitorDensity',
    'CompetitorAdjustment','FieldSize','FieldSizeAdjustment','WinStreakFactorV2',
    'RecentPlaceStreak','CloserBonus','TrainerMomentum','FinalScore',
]

# Features that ARE EXPECTED to be constant within a single race (by design):
#   - Race-level: same distance/field for all dogs in one race
#   - Track-level: same track signal for all dogs at one venue
EXPECTED_CONSTANT_FEATURES = {
    'Distance', 'DistanceSuit', 'FieldSpeedStd', 'FieldTimeStd',
    'FieldSimilarityIndex', 'FieldSize',
    'TrackBox1Adjustment', 'TrackBox4Adjustment', 'TrackUpsetFactor',
}

# Dog-specific features that MUST vary between dogs (unique per dog)
# These are the most critical to verify — if they're constant, predictions are broken.
MUST_VARY_FEATURES = [
    'Box', 'Draw', 'CareerWins', 'CareerPlaces', 'CareerStarts',
    'BestTimeSec', 'SectionalSec', 'DLR', 'DLW', 'PrizeMoney',
    'ConsistencyIndex', 'PlaceRate', 'WinPlaceRate',
    'TrackComprehensiveAdjustment', 'TrackBoxWinRatePct', 'TrackBoxRank',
    'BoxPositionBias', 'BoxPlaceRate', 'BoxTop3Rate',
    'DLWFactor', 'WinStreakFactor', 'FreshnessFactor',
    'AgeFactor', 'ExperienceTier', 'BoxPenaltyFactor',
    'EarlySpeedPercentile', 'BestTimePercentile',
    'CompetitorDensity', 'FinalScore',
]


def build_diverse_race(track='Cannington', distance=530):
    """Build an 8-dog race with deliberately diverse statistics."""
    rows = []
    configs = [
        # name,         box, wins, places, starts, prize,  rtc, dlr, dlw,    bt,    sec,  age,  trainer
        ('TopDog',        1,  12,    6,     40,   35000,  75,   7,    4,   30.22,  5.75,  '3d', 'Smith'),
        ('GoodForm',      2,   7,    9,     30,   18000,  68,  14,   15,   30.55,  5.90,  '2d', 'Brown'),
        ('Novice',        3,   0,    1,      5,     800,  48,   9,  999,   31.10,  6.20,  '1d', 'Jones'),
        ('MidPacker',     4,   4,    5,     22,   11500,  62,   6,   25,   30.70,  6.05,  '3b', 'Smith'),
        ('Backmarker',    5,   1,    3,     18,    3200,  54,  21,  90,    30.95,  6.15,  '2b', 'Brown'),
        ('LateCloser',    6,   3,    7,     25,    9800,  60,  12,   30,   30.80,  6.10,  '4d', 'Davis'),
        ('VetDog',        7,   6,    4,     85,   22000,  65,   8,   18,   30.60,  5.95,  '5b', 'Jones'),
        ('Outsider',      8,   2,    4,     15,    6500,  58,   5,   10,   30.48,  5.85,  '2d', 'Davis'),
    ]
    for cfg in configs:
        name, box, cw, cp, cs, pm, rtc, dlr, dlw, bt, sec, age, trainer = cfg
        dlw_val = dlw if dlw < 500 else 'Mdn'
        rows.append({
            'DogName': name, 'Box': box, 'Draw': box, 'Track': track,
            'RaceNumber': 1, 'RaceDate': '2026-03-11', 'Distance': distance,
            'CareerWins': cw, 'CareerPlaces': cp, 'CareerStarts': cs,
            'PrizeMoney': pm, 'RTC': rtc, 'DLR': dlr, 'DLW': dlw_val,
            'BestTimeSec': bt, 'SectionalSec': sec, 'SexAge': age,
            'Trainer': trainer,
            'Last3TimesSec': [bt + i * 0.12 for i in range(3)],
            'Margins': [1.5 - i * 0.8 for i in range(3)] if cw > 0 else [-2.0 - i for i in range(3)],
            'BoxBiasFactor': 0.0,
        })
    return pd.DataFrame(rows)


def test_feature_count():
    """Test 1: Exactly 75 features in FEATURE_COLS."""
    assert len(FEATURE_COLS) == 75, f"Expected 75, got {len(FEATURE_COLS)}"
    print(f"✅ TEST 1 PASS: FEATURE_COLS has exactly 75 features")


def test_all_features_computed():
    """Test 2: All 75 features are present in compute_features() output."""
    from src.features import compute_features
    df = build_diverse_race(track='Cannington', distance=530)
    result = compute_features(df)
    missing = [f for f in FEATURE_COLS if f not in result.columns]
    assert not missing, f"MISSING features: {missing}"
    print(f"✅ TEST 2 PASS: All 75 features computed by compute_features()")


def test_must_vary_features_are_unique():
    """Test 3: All MUST_VARY_FEATURES produce at least 2 distinct values across 8 dogs."""
    from src.features import compute_features
    df = build_diverse_race(track='Cannington', distance=530)
    result = compute_features(df)
    failures = []
    for feat in MUST_VARY_FEATURES:
        if feat not in result.columns:
            failures.append(f"{feat}: NOT COMPUTED")
            continue
        n_unique = result[feat].nunique()
        if n_unique < 2:
            failures.append(f"{feat}: only {n_unique} unique value(s) — all dogs identical!")
    assert not failures, "FAILED features (should vary per dog):\n  " + "\n  ".join(failures)
    print(f"✅ TEST 3 PASS: All {len(MUST_VARY_FEATURES)} must-vary features produce unique per-dog values")


def test_track_comprehensive_adjustments_differ_between_tracks():
    """Test 4: TrackComprehensiveAdjustment differs between Cannington and Darwin."""
    from src.features import compute_features
    df_c = build_diverse_race(track='Cannington', distance=530)
    df_d = build_diverse_race(track='Darwin', distance=515)
    r_c = compute_features(df_c)
    r_d = compute_features(df_d)
    # The comprehensive adjustment should reflect different box biases
    adj_c = r_c['TrackComprehensiveAdjustment'].values
    adj_d = r_d['TrackComprehensiveAdjustment'].values
    assert not np.allclose(adj_c, adj_d), (
        "TrackComprehensiveAdjustment identical between Cannington and Darwin — "
        "track-specific tuning is NOT working!"
    )
    print(f"✅ TEST 4 PASS: TrackComprehensiveAdjustment differs between tracks")
    print(f"   Cannington Box1-8: {adj_c.round(4).tolist()}")
    print(f"   Darwin     Box1-8: {adj_d.round(4).tolist()}")


def test_track_box_win_rate_differs_by_box_and_track():
    """Test 5: TrackBoxWinRatePct is unique per (track, box) combination."""
    from src.features import compute_features
    df_c = build_diverse_race(track='Cannington', distance=530)
    df_d = build_diverse_race(track='Darwin', distance=515)
    r_c = compute_features(df_c)
    r_d = compute_features(df_d)
    # Each box should have a different win-rate pct
    assert r_c['TrackBoxWinRatePct'].nunique() > 1, "Cannington: TrackBoxWinRatePct all same!"
    assert r_d['TrackBoxWinRatePct'].nunique() > 1, "Darwin: TrackBoxWinRatePct all same!"
    # The two tracks should have different values for the same box
    box1_cannington = r_c.loc[r_c['Box'] == 1, 'TrackBoxWinRatePct'].values[0]
    box1_darwin     = r_d.loc[r_d['Box'] == 1, 'TrackBoxWinRatePct'].values[0]
    assert box1_cannington != box1_darwin, "Box 1 win rate same at Cannington and Darwin!"
    print(f"✅ TEST 5 PASS: TrackBoxWinRatePct is unique per box AND per track")
    print(f"   Cannington Box1 win rate: {box1_cannington:.2f}%  |  Darwin Box1: {box1_darwin:.2f}%")


def test_no_feature_missing_from_metadata():
    """Test 6: All 75 features have a defined category (DOG/DERIVED_DOG/RACE/TRACK)."""
    from audit_all_features import FEATURE_META
    missing_meta = [f for f in FEATURE_COLS if f not in FEATURE_META]
    assert not missing_meta, f"Features with no metadata: {missing_meta}"
    print(f"✅ TEST 6 PASS: All 75 features have documented category/source/description")


def test_final_scores_are_unique_per_dog():
    """Test 7: FinalScore is unique per dog (ML model input — must differentiate)."""
    from src.features import compute_features
    df = build_diverse_race(track='Cannington', distance=530)
    result = compute_features(df)
    scores = result['FinalScore'].values
    n_unique = len(set(scores))
    assert n_unique == len(result), (
        f"FinalScore is not unique for all dogs! "
        f"Got {n_unique} unique scores for {len(result)} dogs."
    )
    print(f"✅ TEST 7 PASS: FinalScore is unique for all {n_unique} dogs")
    for _, row in result[['DogName','Box','FinalScore']].iterrows():
        print(f"   Box {int(row['Box'])} {row['DogName']:15s}: FinalScore = {row['FinalScore']:.4f}")


def test_best_time_percentile_is_unique_per_dog():
    """Test 8: BestTimePercentile ranks dogs correctly within the race."""
    from src.features import compute_features
    df = build_diverse_race(track='Cannington', distance=530)
    result = compute_features(df)
    percs = result['BestTimePercentile'].values
    assert len(set(percs)) > 1, "BestTimePercentile identical for all dogs!"
    # Dog with lowest BestTimeSec should have highest percentile (closest to 1.0)
    fastest_box = result.loc[result['BestTimeSec'].idxmin(), 'Box']
    fastest_pctile = result.loc[result['BestTimeSec'].idxmin(), 'BestTimePercentile']
    slowest_pctile = result.loc[result['BestTimeSec'].idxmax(), 'BestTimePercentile']
    assert fastest_pctile > slowest_pctile, (
        f"Fastest dog (Box {fastest_box}) has LOWER BestTimePercentile than slowest dog! "
        f"Ranking direction is wrong."
    )
    print(f"✅ TEST 8 PASS: BestTimePercentile correctly ranks dogs (fastest=highest)")


if __name__ == '__main__':
    tests = [
        test_feature_count,
        test_all_features_computed,
        test_must_vary_features_are_unique,
        test_track_comprehensive_adjustments_differ_between_tracks,
        test_track_box_win_rate_differs_by_box_and_track,
        test_no_feature_missing_from_metadata,
        test_final_scores_are_unique_per_dog,
        test_best_time_percentile_is_unique_per_dog,
    ]
    passed = 0
    failed = 0
    for t in tests:
        try:
            t()
            passed += 1
        except AssertionError as e:
            print(f"❌ FAIL: {t.__name__}: {e}")
            failed += 1
        except Exception as e:
            import traceback
            print(f"❌ ERROR: {t.__name__}: {e}")
            traceback.print_exc()
            failed += 1

    print()
    print(f"Results: {passed}/{len(tests)} passed, {failed} failed")
    sys.exit(0 if failed == 0 else 1)
