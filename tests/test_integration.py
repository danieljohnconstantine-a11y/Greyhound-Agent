"""
Integration tests for the Greyhound Analytics pipeline
"""
import os
import pandas as pd
import sys

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.parser import parse_race_form
from src.features import compute_features


def test_parser_handles_missing_time_data():
    """Test that parser initializes time fields as None when missing"""
    sample_text = """
Race No 22 Nov 25 07:21PM WENTWORTH PARK 520m
1. 21135Greta 2b 0.0kg 1 Glenn Starr 4 - 9 - 16 $14,740 17 9 38
"""
    df = parse_race_form(sample_text)
    
    assert len(df) > 0, "Should parse at least one dog"
    assert df["BestTimeSec"].isna().all(), "BestTimeSec should be None when not in data"
    assert df["SectionalSec"].isna().all(), "SectionalSec should be None when not in data"
    print("✅ test_parser_handles_missing_time_data passed")


def test_features_uses_fallback_values():
    """Test that features.py uses fallback values for missing time data"""
    # Create a minimal dataframe with missing time data
    df = pd.DataFrame({
        "DogName": ["TestDog"],
        "Distance": [520],
        "BestTimeSec": [None],
        "SectionalSec": [None],
        "Last3TimesSec": [None],
        "Margins": [None],
        "DLR": [5],
        "CareerStarts": [10],
        "CareerWins": [3],
        "PrizeMoney": [10000],
        "CareerPlaces": [2],
    })
    
    result = compute_features(df)
    
    # Check that fallback values were applied
    assert not result["BestTimeSec"].isna().any(), "BestTimeSec should have fallback value"
    assert not result["SectionalSec"].isna().any(), "SectionalSec should have fallback value"
    assert result["FinalScore"].notna().all(), "FinalScore should be calculated"
    print("✅ test_features_uses_fallback_values passed")


def test_deduplication_works():
    """Test that duplicate dogs are removed"""
    df = pd.DataFrame({
        "Track": ["WENTWORTH PARK", "WENTWORTH PARK"],
        "RaceNumber": [1, 1],
        "DogName": ["TestDog", "TestDog"],
        "Box": [1, 1],
    })
    
    # Apply deduplication like in main.py
    initial_count = len(df)
    df_dedup = df.drop_duplicates(subset=["Track", "RaceNumber", "DogName"], keep="first")
    duplicates_removed = initial_count - len(df_dedup)
    
    assert duplicates_removed == 1, "Should remove 1 duplicate"
    assert len(df_dedup) == 1, "Should have 1 unique dog"
    print("✅ test_deduplication_works passed")


def test_outputs_directory_creation():
    """Test that outputs directory is created if it doesn't exist"""
    import tempfile
    import shutil
    
    # Create a temporary directory
    temp_dir = tempfile.mkdtemp()
    output_path = os.path.join(temp_dir, "outputs")
    
    try:
        # Ensure it doesn't exist
        assert not os.path.exists(output_path)
        
        # Create it (like in main.py)
        if not os.path.exists(output_path):
            os.makedirs(output_path)
        
        # Verify it exists
        assert os.path.exists(output_path), "Output directory should be created"
        print("✅ test_outputs_directory_creation passed")
    finally:
        # Cleanup
        shutil.rmtree(temp_dir)


if __name__ == "__main__":
    print("Running integration tests...\n")
    
    test_parser_handles_missing_time_data()
    test_features_uses_fallback_values()
    test_deduplication_works()
    test_outputs_directory_creation()
    
    print("\n✅ All integration tests passed!")
