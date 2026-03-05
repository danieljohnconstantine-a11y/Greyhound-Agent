"""
Scorer Module - Wrapper for scoring functionality

This module provides the score_race function that wraps
the compute_features functionality for compatibility with
ML hybrid prediction scripts.
"""

from src.features import compute_features

def score_race(df_race, track=None):
    """
    Score a race using the v4.4 feature computation system.
    
    Args:
        df_race: DataFrame containing race data for multiple dogs
        track: Optional track name (not currently used but kept for API compatibility)
    
    Returns:
        DataFrame with FinalScore column added
    """
    # Apply v4.4 feature computation which adds FinalScore
    df_scored = compute_features(df_race)
    return df_scored
