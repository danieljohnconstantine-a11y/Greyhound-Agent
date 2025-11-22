"""
Tests for features.py - specifically for timing and margin data handling
"""
import pandas as pd
import numpy as np

# Use relative import
try:
    from src.features import compute_features
except ImportError:
    # If run from tests directory
    import sys
    import os
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
    from src.features import compute_features


def test_missing_timing_columns():
    """Test that missing BestTimeSec and SectionalSec columns are handled with NaN and warnings"""
    df = pd.DataFrame({
        'Box': [1, 2, 3],
        'DogName': ['Dog1', 'Dog2', 'Dog3'],
        'Distance': [435, 435, 435],
        'CareerStarts': [10, 20, 30],
        'CareerWins': [2, 5, 8],
        'PrizeMoney': [1000, 2000, 3000],
        'DLR': [5, 7, 10]
    })
    
    result = compute_features(df)
    
    # Should create columns with NaN
    assert 'BestTimeSec' in result.columns
    assert 'SectionalSec' in result.columns
    assert result['BestTimeSec'].isna().all()
    assert result['SectionalSec'].isna().all()
    
    # Speed_kmh and EarlySpeedIndex should also be NaN
    assert result['Speed_kmh'].isna().all()
    assert result['EarlySpeedIndex'].isna().all()
    
    print("✅ test_missing_timing_columns passed")


def test_unique_timing_values():
    """Test that unique BestTimeSec and SectionalSec values are preserved"""
    df = pd.DataFrame({
        'Box': [1, 2, 3],
        'DogName': ['Dog1', 'Dog2', 'Dog3'],
        'Distance': [435, 435, 435],
        'CareerStarts': [10, 20, 30],
        'CareerWins': [2, 5, 8],
        'PrizeMoney': [1000, 2000, 3000],
        'DLR': [5, 7, 10],
        'BestTimeSec': [22.5, 22.8, 23.1],
        'SectionalSec': [8.1, 8.2, 8.3]
    })
    
    result = compute_features(df)
    
    # Values should be preserved
    assert result['BestTimeSec'].tolist() == [22.5, 22.8, 23.1]
    assert result['SectionalSec'].tolist() == [8.1, 8.2, 8.3]
    
    # Speed_kmh and EarlySpeedIndex should be calculated
    assert result['Speed_kmh'].notna().all()
    assert result['EarlySpeedIndex'].notna().all()
    
    # Verify Speed_kmh calculation for first dog
    expected_speed = (435 / 22.5) * 3.6
    assert abs(result['Speed_kmh'].iloc[0] - expected_speed) < 0.01
    
    # Verify EarlySpeedIndex calculation for first dog
    expected_esi = 435 / 8.1
    assert abs(result['EarlySpeedIndex'].iloc[0] - expected_esi) < 0.01
    
    print("✅ test_unique_timing_values passed")


def test_identical_timing_values_raises_error():
    """Test that identical BestTimeSec values across all dogs raises ValueError"""
    df = pd.DataFrame({
        'Box': [1, 2, 3],
        'DogName': ['Dog1', 'Dog2', 'Dog3'],
        'Distance': [435, 435, 435],
        'CareerStarts': [10, 20, 30],
        'CareerWins': [2, 5, 8],
        'PrizeMoney': [1000, 2000, 3000],
        'DLR': [5, 7, 10],
        'BestTimeSec': [22.5, 22.5, 22.5],  # All the same!
        'SectionalSec': [8.1, 8.2, 8.3]
    })
    
    try:
        compute_features(df)
        assert False, "Should have raised ValueError"
    except ValueError as e:
        assert "All 3 dogs with BestTimeSec values have the same value" in str(e)
        print("✅ test_identical_timing_values_raises_error passed")


def test_identical_sectional_values_raises_error():
    """Test that identical SectionalSec values across all dogs raises ValueError"""
    df = pd.DataFrame({
        'Box': [1, 2, 3],
        'DogName': ['Dog1', 'Dog2', 'Dog3'],
        'Distance': [435, 435, 435],
        'CareerStarts': [10, 20, 30],
        'CareerWins': [2, 5, 8],
        'PrizeMoney': [1000, 2000, 3000],
        'DLR': [5, 7, 10],
        'BestTimeSec': [22.5, 22.8, 23.1],
        'SectionalSec': [8.5, 8.5, 8.5]  # All the same!
    })
    
    try:
        compute_features(df)
        assert False, "Should have raised ValueError"
    except ValueError as e:
        assert "All 3 dogs with SectionalSec values have the same value" in str(e)
        print("✅ test_identical_sectional_values_raises_error passed")


def test_single_dog_no_error():
    """Test that a single dog doesn't trigger the identical values error"""
    df = pd.DataFrame({
        'Box': [1],
        'DogName': ['OnlyDog'],
        'Distance': [435],
        'CareerStarts': [10],
        'CareerWins': [2],
        'PrizeMoney': [1000],
        'DLR': [5],
        'BestTimeSec': [22.5],
        'SectionalSec': [8.1]
    })
    
    result = compute_features(df)
    
    # Should complete without error
    assert len(result) == 1
    assert result['BestTimeSec'].iloc[0] == 22.5
    assert result['SectionalSec'].iloc[0] == 8.1
    
    print("✅ test_single_dog_no_error passed")


def test_partial_nan_values():
    """Test that some dogs can have NaN timing values"""
    df = pd.DataFrame({
        'Box': [1, 2, 3],
        'DogName': ['Dog1', 'Dog2', 'Dog3'],
        'Distance': [435, 435, 435],
        'CareerStarts': [10, 20, 30],
        'CareerWins': [2, 5, 8],
        'PrizeMoney': [1000, 2000, 3000],
        'DLR': [5, 7, 10],
        'BestTimeSec': [22.5, np.nan, 23.1],
        'SectionalSec': [8.1, 8.2, np.nan]
    })
    
    result = compute_features(df)
    
    # Dog1 should have both Speed_kmh and EarlySpeedIndex
    assert pd.notna(result['Speed_kmh'].iloc[0])
    assert pd.notna(result['EarlySpeedIndex'].iloc[0])
    
    # Dog2 should have EarlySpeedIndex but not Speed_kmh
    assert pd.isna(result['Speed_kmh'].iloc[1])
    assert pd.notna(result['EarlySpeedIndex'].iloc[1])
    
    # Dog3 should have Speed_kmh but not EarlySpeedIndex
    assert pd.notna(result['Speed_kmh'].iloc[2])
    assert pd.isna(result['EarlySpeedIndex'].iloc[2])
    
    print("✅ test_partial_nan_values passed")


def test_final_score_with_nan_timing():
    """Test that FinalScore is calculated even with NaN timing values"""
    df = pd.DataFrame({
        'Box': [1, 2],
        'DogName': ['Dog1', 'Dog2'],
        'Distance': [435, 435],
        'CareerStarts': [10, 20],
        'CareerWins': [2, 5],
        'PrizeMoney': [1000, 2000],
        'DLR': [5, 7],
        'BestTimeSec': [22.5, np.nan],
        'SectionalSec': [8.1, np.nan]
    })
    
    result = compute_features(df)
    
    # Both dogs should have FinalScore calculated
    assert 'FinalScore' in result.columns
    assert pd.notna(result['FinalScore'].iloc[0])
    assert pd.notna(result['FinalScore'].iloc[1])
    
    # Dog1 should have higher score due to timing data
    # (assuming timing contributes positively to score)
    # Note: This may not always be true depending on other factors
    
    print("✅ test_final_score_with_nan_timing passed")


def test_missing_last3_and_margins():
    """Test that missing Last3TimesSec and Margins columns are handled with empty lists"""
    df = pd.DataFrame({
        'Box': [1, 2, 3],
        'DogName': ['Dog1', 'Dog2', 'Dog3'],
        'Distance': [435, 435, 435],
        'CareerStarts': [10, 20, 30],
        'CareerWins': [2, 5, 8],
        'PrizeMoney': [1000, 2000, 3000],
        'DLR': [5, 7, 10]
    })
    
    result = compute_features(df)
    
    # Should create columns with empty lists
    assert 'Last3TimesSec' in result.columns
    assert 'Margins' in result.columns
    assert all(isinstance(x, list) and len(x) == 0 for x in result['Last3TimesSec'])
    assert all(isinstance(x, list) and len(x) == 0 for x in result['Margins'])
    
    # Derived metrics should be 0
    assert all(x == 0 for x in result['FinishConsistency'])
    assert all(x == 0 for x in result['MarginAvg'])
    assert all(x == 0 for x in result['FormMomentum'])
    
    print("✅ test_missing_last3_and_margins passed")


def test_unique_last3_and_margins():
    """Test that unique Last3TimesSec and Margins values are preserved"""
    df = pd.DataFrame({
        'Box': [1, 2, 3],
        'DogName': ['Dog1', 'Dog2', 'Dog3'],
        'Distance': [435, 435, 435],
        'CareerStarts': [10, 20, 30],
        'CareerWins': [2, 5, 8],
        'PrizeMoney': [1000, 2000, 3000],
        'DLR': [5, 7, 10],
        'Last3TimesSec': [[22.5, 22.6, 22.7], [23.1, 23.2], [24.0, 24.1, 24.2]],
        'Margins': [[1.0, 2.0, 3.0], [4.0, 5.0], [6.0, 7.0, 8.0]]
    })
    
    result = compute_features(df)
    
    # Values should be preserved
    assert result['Last3TimesSec'].iloc[0] == [22.5, 22.6, 22.7]
    assert result['Margins'].iloc[0] == [1.0, 2.0, 3.0]
    
    # Derived metrics should be calculated
    assert result['FinishConsistency'].iloc[0] > 0  # Should have std dev
    assert result['MarginAvg'].iloc[0] == 2.0
    assert result['FormMomentum'].iloc[0] == 1.0  # (2-1 + 3-2)/2 = 1
    
    print("✅ test_unique_last3_and_margins passed")


def test_identical_last3_raises_error():
    """Test that identical Last3TimesSec values across all dogs raises ValueError"""
    df = pd.DataFrame({
        'Box': [1, 2, 3],
        'DogName': ['Dog1', 'Dog2', 'Dog3'],
        'Distance': [435, 435, 435],
        'CareerStarts': [10, 20, 30],
        'CareerWins': [2, 5, 8],
        'PrizeMoney': [1000, 2000, 3000],
        'DLR': [5, 7, 10],
        'Last3TimesSec': [[22.5, 22.6, 22.7], [22.5, 22.6, 22.7], [22.5, 22.6, 22.7]]  # All the same!
    })
    
    try:
        compute_features(df)
        assert False, "Should have raised ValueError"
    except ValueError as e:
        assert "All 3 dogs with Last3TimesSec values have the same value" in str(e)
        print("✅ test_identical_last3_raises_error passed")


def test_identical_margins_raises_error():
    """Test that identical Margins values across all dogs raises ValueError"""
    df = pd.DataFrame({
        'Box': [1, 2, 3],
        'DogName': ['Dog1', 'Dog2', 'Dog3'],
        'Distance': [435, 435, 435],
        'CareerStarts': [10, 20, 30],
        'CareerWins': [2, 5, 8],
        'PrizeMoney': [1000, 2000, 3000],
        'DLR': [5, 7, 10],
        'Margins': [[5.0, 6.3, 10.3], [5.0, 6.3, 10.3], [5.0, 6.3, 10.3]]  # All the same!
    })
    
    try:
        compute_features(df)
        assert False, "Should have raised ValueError"
    except ValueError as e:
        assert "All 3 dogs with Margins values have the same value" in str(e)
        print("✅ test_identical_margins_raises_error passed")


def test_partial_empty_last3_and_margins():
    """Test that some dogs can have empty Last3TimesSec and Margins"""
    df = pd.DataFrame({
        'Box': [1, 2, 3],
        'DogName': ['Dog1', 'Dog2', 'Dog3'],
        'Distance': [435, 435, 435],
        'CareerStarts': [10, 20, 30],
        'CareerWins': [2, 5, 8],
        'PrizeMoney': [1000, 2000, 3000],
        'DLR': [5, 7, 10],
        'Last3TimesSec': [[22.5, 22.6, 22.7], [], [24.0, 24.1, 24.2]],
        'Margins': [[1.0, 2.0, 3.0], [4.0, 5.0], []]
    })
    
    result = compute_features(df)
    
    # Dog1 should have all derived metrics
    assert result['FinishConsistency'].iloc[0] > 0
    assert result['MarginAvg'].iloc[0] > 0
    
    # Dog2 should have empty Last3 metrics but valid Margins metrics
    assert result['FinishConsistency'].iloc[1] == 0
    assert result['MarginAvg'].iloc[1] > 0
    
    # Dog3 should have valid Last3 metrics but empty Margins metrics
    assert result['FinishConsistency'].iloc[2] > 0
    assert result['MarginAvg'].iloc[2] == 0
    
    print("✅ test_partial_empty_last3_and_margins passed")


if __name__ == '__main__':
    print("Running features.py tests...\n")
    
    test_missing_timing_columns()
    test_unique_timing_values()
    test_identical_timing_values_raises_error()
    test_identical_sectional_values_raises_error()
    test_single_dog_no_error()
    test_partial_nan_values()
    test_final_score_with_nan_timing()
    test_missing_last3_and_margins()
    test_unique_last3_and_margins()
    test_identical_last3_raises_error()
    test_identical_margins_raises_error()
    test_partial_empty_last3_and_margins()
    
    print("\n✅ All tests passed!")
