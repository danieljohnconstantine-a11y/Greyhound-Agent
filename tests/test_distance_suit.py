import pandas as pd
import numpy as np
from src.features import compute_distance_suitability, compute_features


def test_distance_suitability_basic():
    """Test basic DistanceSuit calculation with simple data"""
    # Create test data with known win rates
    test_data = pd.DataFrame({
        'DogName': ['Dog A', 'Dog B', 'Dog C', 'Dog A', 'Dog B'],
        'Distance': [520, 520, 520, 400, 400],
        'CareerWins': [10, 5, 0, 8, 4],
        'CareerStarts': [20, 10, 10, 10, 10]
    })
    
    result = compute_distance_suitability(test_data)
    
    # Check that DistanceSuit column is created
    assert 'DistanceSuit' in result.columns
    
    # At 520m: Dog A has 0.5 win rate, Dog B has 0.5, Dog C has 0
    # Max is 0.5, so Dog A and B should be 1.0, Dog C should be 0
    # At 400m: Dog A has 0.8 win rate, Dog B has 0.4
    # Max is 0.8, so Dog A should be 1.0, Dog B should be 0.5
    
    print("\nTest results:")
    print(result[['DogName', 'Distance', 'CareerWins', 'CareerStarts', 'DistanceSuit']])
    
    # Verify normalization: max DistanceSuit per distance should be 1.0
    for distance in result['Distance'].unique():
        max_suit = result[result['Distance'] == distance]['DistanceSuit'].max()
        assert max_suit == 1.0, f"Max DistanceSuit at {distance}m should be 1.0, got {max_suit}"
    
    print("✅ Basic DistanceSuit test passed")


def test_distance_suitability_no_starts():
    """Test that dogs with no starts default to 0.5 win rate"""
    test_data = pd.DataFrame({
        'DogName': ['New Dog', 'Veteran Dog'],
        'Distance': [520, 520],
        'CareerWins': [0, 10],
        'CareerStarts': [0, 20]
    })
    
    result = compute_distance_suitability(test_data)
    
    print("\nNo starts test:")
    print(result[['DogName', 'Distance', 'CareerWins', 'CareerStarts', 'DistanceSuit']])
    
    # New Dog with no starts should have win rate of 0.5 (default)
    # Veteran Dog has 0.5 win rate (10/20)
    # Both should normalize to 1.0 since they have the same effective win rate
    new_dog_suit = result[result['DogName'] == 'New Dog']['DistanceSuit'].iloc[0]
    assert new_dog_suit == 1.0, f"New dog DistanceSuit should be 1.0, got {new_dog_suit}"
    
    print("✅ No starts test passed")


def test_distance_suitability_multiple_distances():
    """Test that normalization is done per distance"""
    test_data = pd.DataFrame({
        'DogName': ['Dog A', 'Dog B', 'Dog A', 'Dog B'],
        'Distance': [520, 520, 400, 400],
        'CareerWins': [10, 5, 5, 10],
        'CareerStarts': [20, 20, 20, 20]
    })
    
    result = compute_distance_suitability(test_data)
    
    print("\nMultiple distances test:")
    print(result[['DogName', 'Distance', 'CareerWins', 'CareerStarts', 'DistanceSuit']])
    
    # At 520m: Dog A has 0.5 win rate (best) -> 1.0, Dog B has 0.25 -> 0.5
    # At 400m: Dog B has 0.5 win rate (best) -> 1.0, Dog A has 0.25 -> 0.5
    
    dog_a_520 = result[(result['DogName'] == 'Dog A') & (result['Distance'] == 520)]['DistanceSuit'].iloc[0]
    dog_b_400 = result[(result['DogName'] == 'Dog B') & (result['Distance'] == 400)]['DistanceSuit'].iloc[0]
    
    assert dog_a_520 == 1.0, f"Dog A at 520m should be 1.0, got {dog_a_520}"
    assert dog_b_400 == 1.0, f"Dog B at 400m should be 1.0, got {dog_b_400}"
    
    print("✅ Multiple distances test passed")


def test_distance_suitability_missing_distance():
    """Test that missing Distance column is handled gracefully"""
    test_data = pd.DataFrame({
        'DogName': ['Dog A', 'Dog B'],
        'CareerWins': [10, 5],
        'CareerStarts': [20, 20]
    })
    
    result = compute_distance_suitability(test_data)
    
    print("\nMissing Distance test:")
    print(result[['DogName', 'CareerWins', 'CareerStarts', 'DistanceSuit']])
    
    # Should default all to 0.5
    assert all(result['DistanceSuit'] == 0.5), "All DistanceSuit values should be 0.5 when Distance is missing"
    
    print("✅ Missing Distance test passed")


def test_compute_features_integration():
    """Test that compute_features properly integrates DistanceSuit"""
    test_data = pd.DataFrame({
        'Box': [1, 2, 3],
        'DogName': ['Dog A', 'Dog B', 'Dog C'],
        'Distance': [520, 520, 520],
        'CareerWins': [10, 5, 2],
        'CareerStarts': [20, 20, 20],
        'PrizeMoney': [10000, 5000, 2000],
        'DLR': [5, 10, 15],
        'CareerPlaces': [5, 5, 5],
        'FormNumber': ['123', '456', '789'],
        'Trainer': ['T1', 'T2', 'T3'],
        'SexAge': ['2d', '3d', '4d'],
        'Weight': [30.5, 31.0, 29.5],
        'Draw': [1, 2, 3],
        'RTC': ['A', 'B', 'C'],
        'DLW': [10, 20, 30],
        'RaceNumber': [1, 1, 1],
        'RaceDate': ['2025-10-01', '2025-10-01', '2025-10-01'],
        'RaceTime': ['7:00PM', '7:00PM', '7:00PM'],
        'Track': ['Test Track', 'Test Track', 'Test Track']
    })
    
    result = compute_features(test_data)
    
    print("\nIntegration test:")
    print(result[['DogName', 'Distance', 'CareerWins', 'CareerStarts', 'DistanceSuit', 'FinalScore']])
    
    # Verify DistanceSuit is in result
    assert 'DistanceSuit' in result.columns
    
    # Verify FinalScore is calculated
    assert 'FinalScore' in result.columns
    
    # Best performer should have DistanceSuit of 1.0
    best_dog_suit = result[result['CareerWins'] == 10]['DistanceSuit'].iloc[0]
    assert best_dog_suit == 1.0, f"Best performer should have DistanceSuit of 1.0, got {best_dog_suit}"
    
    print("✅ Integration test passed")


if __name__ == "__main__":
    test_distance_suitability_basic()
    test_distance_suitability_no_starts()
    test_distance_suitability_multiple_distances()
    test_distance_suitability_missing_distance()
    test_compute_features_integration()
    print("\n🎉 All tests passed!")
