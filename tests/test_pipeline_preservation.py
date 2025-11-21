"""
Test that the pipeline preserves unique dog variables from PDFs
"""
import pandas as pd
import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from parser import parse_race_form
from features import compute_features


# Test fixtures
# Note: Date format matches PDF structure but is generic for long-term test stability
SAMPLE_RACE_DATA = """
Race No 19 Oct 25 06:52PM BROKEN HILL 375m
1. 25243Visibility 2d 0.0kg 1 Kaylene Hatzi 0 - 4 - 13 $1,855 14 7 Mdn
2. 54825Vision 3d 0.0kg 3 Judith Hurley 1 - 3 - 9 $1,720 7 5 192
3. 34657Wings 3b 0.0kg 5 Clayton Trengove 1 - 3 - 11 $1,565 12 7 64
"""


def test_parser_preserves_unique_fields():
    """Test that parser extracts unique values for each dog"""
    df = parse_race_form(SAMPLE_RACE_DATA)
    
    # Verify we got all dogs
    assert len(df) == 3, f"Expected 3 dogs, got {len(df)}"
    
    # Verify unique names
    assert df['DogName'].nunique() == 3, "All dog names should be unique"
    
    # Verify unique trainers
    assert df['Trainer'].nunique() == 3, "All trainers should be unique"
    
    # Verify unique prize money
    assert df['PrizeMoney'].nunique() == 3, "All prize money should be unique"
    
    print("✅ Parser preserves unique fields")
    return True


def test_features_preserves_parsed_data():
    """Test that compute_features doesn't overwrite parsed unique values"""
    # Create sample data with varied distances
    df = pd.DataFrame({
        'DogName': ['Dog A', 'Dog B', 'Dog C'],
        'Distance': [375, 500, 595],
        'CareerWins': [5, 3, 7],
        'CareerStarts': [20, 15, 25],
        'DLR': [3, 5, 2],
        'PrizeMoney': [10000, 8000, 12000]
    })
    
    # Apply feature computation
    df_features = compute_features(df)
    
    # Verify original fields preserved
    assert list(df_features['DogName']) == ['Dog A', 'Dog B', 'Dog C'], "Dog names should be preserved"
    assert list(df_features['CareerWins']) == [5, 3, 7], "Career wins should be preserved"
    
    # Verify timing fields vary by distance (not all identical)
    assert df_features['BestTimeSec'].nunique() == 3, "BestTimeSec should vary by distance"
    assert df_features['SectionalSec'].nunique() == 3, "SectionalSec should vary by distance"
    
    # Verify timing data source is marked
    assert 'TimingDataSource' in df_features.columns, "Should have TimingDataSource field"
    assert df_features['TimingDataSource'].iloc[0] == 'Estimated', "Should be marked as Estimated"
    
    print("✅ Features preserve parsed data and create distance-based estimates")
    return True


def test_no_identical_default_values():
    """Test that we don't assign identical default values to all dogs"""
    df = pd.DataFrame({
        'DogName': ['Dog A', 'Dog B', 'Dog C'],
        'Distance': [375, 500, 375],  # Two dogs same distance
        'CareerWins': [5, 3, 7],
        'CareerStarts': [20, 15, 25],
        'DLR': [3, 5, 2],
        'PrizeMoney': [10000, 8000, 12000]
    })
    
    df_features = compute_features(df)
    
    # Dogs with same distance should have same timing, but not all dogs
    assert df_features['BestTimeSec'].nunique() > 1, "BestTimeSec should not be identical for all dogs"
    
    # Dogs with same distance should have same BestTimeSec
    dogs_375m = df_features[df_features['Distance'] == 375]
    assert dogs_375m['BestTimeSec'].nunique() == 1, "Dogs at same distance should have same BestTimeSec"
    
    print("✅ No identical defaults for all dogs")
    return True


if __name__ == '__main__':
    print("Running pipeline preservation tests...\n")
    
    try:
        test_parser_preserves_unique_fields()
        test_features_preserves_parsed_data()
        test_no_identical_default_values()
        
        print("\n" + "="*60)
        print("ALL TESTS PASSED ✅")
        print("="*60)
    except AssertionError as e:
        print(f"\n❌ TEST FAILED: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
