"""
Tests for features.py - specifically for BestTimeSec and SectionalSec handling
"""
import pandas as pd
import numpy as np
import sys
import os

# Add src to path
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
        assert "All 3 dogs have the same BestTimeSec value" in str(e)
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
        assert "All 3 dogs have the same SectionalSec value" in str(e)
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


if __name__ == '__main__':
    print("Running features.py tests...\n")
    
    test_missing_timing_columns()
    test_unique_timing_values()
    test_identical_timing_values_raises_error()
    test_identical_sectional_values_raises_error()
    test_single_dog_no_error()
    test_partial_nan_values()
    test_final_score_with_nan_timing()
    
    print("\n✅ All tests passed!")
