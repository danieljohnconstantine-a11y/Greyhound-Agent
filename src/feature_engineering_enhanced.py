"""
Enhanced Feature Engineering Module - Phase 1 (Complete)

Automatically computes advanced features during ML training:

Phase 1A (High Impact):
1. Days since last race (freshness/rest impact)
2. Track-specific win rate (performance at specific venues)
3. Distance-specific win rate (performance at specific distances)

Phase 1B (Medium Impact):
4. Box win percentage (performance from specific starting positions)
5. Recent speed ratings (last 3 races average speed vs field)
6. Head-to-head win rate (performance against today's competitors)

Phase 1C (Quality Indicators):
7. Prize money earned (career earnings as quality metric)
8. Handler/trainer performance rating (trainer strike rate enhancements)

These features are computed from historical race data during training.
No manual aggregation required - the training script processes all races.
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from collections import defaultdict
import logging

logger = logging.getLogger(__name__)


class HistoricalFeatureBuilder:
    """
    Builds advanced features from historical race data.
    Processes data incrementally to maintain temporal consistency.
    """
    
    def __init__(self):
        """Initialize feature tracking dictionaries"""
        # Phase 1A: Track historical performance by dog
        self.dog_race_history = defaultdict(list)  # {dog_name: [(date, track, distance, position, time), ...]}
        self.dog_track_stats = defaultdict(lambda: defaultdict(lambda: {'wins': 0, 'starts': 0}))  # {dog: {track: stats}}
        self.dog_distance_stats = defaultdict(lambda: defaultdict(lambda: {'wins': 0, 'starts': 0}))  # {dog: {distance: stats}}
        self.dog_last_race_date = {}  # {dog_name: last_race_date}
        
        # Phase 1B: Box, speed, and head-to-head tracking
        self.dog_box_stats = defaultdict(lambda: defaultdict(lambda: {'wins': 0, 'starts': 0}))  # {dog: {box: stats}}
        self.dog_recent_times = defaultdict(list)  # {dog_name: [(race_time, field_avg_time), ...]} - last 3 races
        self.dog_opponents = defaultdict(set)  # {dog_name: {opponent_names}}
        self.head_to_head_wins = defaultdict(lambda: defaultdict(int))  # {dog1: {dog2: wins}}
        self.head_to_head_races = defaultdict(lambda: defaultdict(int))  # {dog1: {dog2: total_races}}
        
        # Phase 1C: Quality metrics
        self.dog_prize_money = defaultdict(float)  # {dog_name: total_prize_money}
        self.trainer_stats = defaultdict(lambda: {'wins': 0, 'starts': 0})  # {trainer_name: stats}
        self.dog_trainer = {}  # {dog_name: trainer_name}
        
        logger.info("HistoricalFeatureBuilder initialized with Phase 1A+1B+1C features")
    
    def update_dog_history(self, dog_name, race_date, track, distance, position, box_number=None, race_time=None, field_avg_time=None, trainer=None, prize_money=0, opponents=None):
        """
        Update historical records for a dog after a race.
        
        Args:
            dog_name: Name of the dog
            race_date: Date of the race (datetime or string)
            track: Track name
            distance: Race distance in meters
            position: Finishing position (1 = winner)
            box_number: Starting box number (1-8)
            race_time: Dog's race time in seconds
            field_avg_time: Average time of all dogs in race
            trainer: Trainer name
            prize_money: Prize money earned
            opponents: List of opponent dog names in this race
        """
        if not dog_name:
            return
        
        # Convert race_date to datetime if it's a string
        if isinstance(race_date, str):
            try:
                race_date = pd.to_datetime(race_date)
            except:
                logger.warning(f"Could not parse race date: {race_date}")
                return
        
        # Normalize distance to bracket (300m, 400m, 500m, 600m+)
        distance_bracket = self._get_distance_bracket(distance)
        
        # Phase 1A: Add to race history
        self.dog_race_history[dog_name].append({
            'date': race_date,
            'track': track,
            'distance': distance_bracket,
            'position': position,
            'time': race_time
        })
        
        # Phase 1A: Update track stats
        self.dog_track_stats[dog_name][track]['starts'] += 1
        if position == 1:
            self.dog_track_stats[dog_name][track]['wins'] += 1
        
        # Phase 1A: Update distance stats
        self.dog_distance_stats[dog_name][distance_bracket]['starts'] += 1
        if position == 1:
            self.dog_distance_stats[dog_name][distance_bracket]['wins'] += 1
        
        # Phase 1A: Update last race date
        if dog_name not in self.dog_last_race_date or race_date > self.dog_last_race_date[dog_name]:
            self.dog_last_race_date[dog_name] = race_date
        
        # Phase 1B: Update box stats
        if box_number is not None:
            self.dog_box_stats[dog_name][box_number]['starts'] += 1
            if position == 1:
                self.dog_box_stats[dog_name][box_number]['wins'] += 1
        
        # Phase 1B: Update recent race times (keep last 3)
        if race_time is not None and field_avg_time is not None:
            self.dog_recent_times[dog_name].append((race_time, field_avg_time))
            if len(self.dog_recent_times[dog_name]) > 3:
                self.dog_recent_times[dog_name].pop(0)  # Keep only last 3
        
        # Phase 1B: Update head-to-head records
        if opponents:
            for opponent in opponents:
                if opponent and opponent != dog_name:
                    self.dog_opponents[dog_name].add(opponent)
                    self.head_to_head_races[dog_name][opponent] += 1
                    if position == 1:
                        self.head_to_head_wins[dog_name][opponent] += 1
        
        # Phase 1C: Update prize money
        self.dog_prize_money[dog_name] += prize_money
        
        # Phase 1C: Update trainer stats
        if trainer:
            self.dog_trainer[dog_name] = trainer
            self.trainer_stats[trainer]['starts'] += 1
            if position == 1:
                self.trainer_stats[trainer]['wins'] += 1
    
    def _get_distance_bracket(self, distance):
        """
        Convert actual distance to standardized bracket.
        
        Args:
            distance: Race distance in meters
            
        Returns:
            Standardized distance bracket (300, 400, 500, or 600)
        """
        if pd.isna(distance):
            return 500  # Default to 500m if unknown
        
        distance = float(distance)
        
        if distance < 350:
            return 300
        elif distance < 450:
            return 400
        elif distance < 550:
            return 500
        else:
            return 600
    
    def compute_days_since_last_race(self, dog_name, current_date):
        """
        Calculate days since dog's last race.
        
        Args:
            dog_name: Name of the dog
            current_date: Current race date
            
        Returns:
            Days since last race (float), or NaN if no history
        """
        if dog_name not in self.dog_last_race_date:
            return np.nan
        
        last_race = self.dog_last_race_date[dog_name]
        
        # Convert current_date to datetime if needed
        if isinstance(current_date, str):
            try:
                current_date = pd.to_datetime(current_date)
            except:
                return np.nan
        
        days_gap = (current_date - last_race).total_seconds() / 86400  # Convert to days
        
        # Negative values shouldn't happen (race before history), but return 0 if so
        return max(0, days_gap)
    
    def compute_track_specific_win_rate(self, dog_name, track):
        """
        Calculate dog's win rate at specific track.
        
        Args:
            dog_name: Name of the dog
            track: Track name
            
        Returns:
            Win rate at this track (0-1), or NaN if no history
        """
        if dog_name not in self.dog_track_stats:
            return np.nan
        
        if track not in self.dog_track_stats[dog_name]:
            return np.nan
        
        stats = self.dog_track_stats[dog_name][track]
        
        if stats['starts'] == 0:
            return np.nan
        
        return stats['wins'] / stats['starts']
    
    def compute_distance_specific_win_rate(self, dog_name, distance):
        """
        Calculate dog's win rate at specific distance bracket.
        
        Args:
            dog_name: Name of the dog
            distance: Race distance in meters
            
        Returns:
            Win rate at this distance (0-1), or NaN if no history
        """
        distance_bracket = self._get_distance_bracket(distance)
        
        if dog_name not in self.dog_distance_stats:
            return np.nan
        
        if distance_bracket not in self.dog_distance_stats[dog_name]:
            return np.nan
        
        stats = self.dog_distance_stats[dog_name][distance_bracket]
        
        if stats['starts'] == 0:
            return np.nan
        
        return stats['wins'] / stats['starts']
    
    def compute_box_win_percentage(self, dog_name, box_number):
        """
        Calculate dog's win rate from specific starting box.
        
        Args:
            dog_name: Name of the dog
            box_number: Box number (1-8)
            
        Returns:
            Win percentage from this box (0-1), or NaN if no history
        """
        if dog_name not in self.dog_box_stats:
            return np.nan
        
        if box_number not in self.dog_box_stats[dog_name]:
            return np.nan
        
        stats = self.dog_box_stats[dog_name][box_number]
        
        if stats['starts'] == 0:
            return np.nan
        
        return stats['wins'] / stats['starts']
    
    def compute_recent_speed_rating(self, dog_name):
        """
        Calculate dog's recent speed rating (last 3 races).
        Speed rating = average(dog_time / field_avg_time) over last 3 races.
        Lower is better (< 1.0 means faster than average).
        
        Args:
            dog_name: Name of the dog
            
        Returns:
            Speed rating (typically 0.9-1.1), or NaN if insufficient history
        """
        if dog_name not in self.dog_recent_times:
            return np.nan
        
        recent_times = self.dog_recent_times[dog_name]
        
        if len(recent_times) == 0:
            return np.nan
        
        # Calculate average relative speed (dog_time / field_avg)
        speed_ratios = []
        for dog_time, field_avg in recent_times:
            if dog_time > 0 and field_avg > 0:
                speed_ratios.append(dog_time / field_avg)
        
        if not speed_ratios:
            return np.nan
        
        return np.mean(speed_ratios)
    
    def compute_head_to_head_win_rate(self, dog_name, opponents):
        """
        Calculate dog's win rate against today's specific opponents.
        
        Args:
            dog_name: Name of the dog
            opponents: List of opponent dog names in today's race
            
        Returns:
            Win rate against these opponents (0-1), or NaN if no history
        """
        if not opponents:
            return np.nan
        
        if dog_name not in self.head_to_head_races:
            return np.nan
        
        total_races_vs_opponents = 0
        total_wins_vs_opponents = 0
        
        for opponent in opponents:
            if opponent == dog_name:
                continue
            
            if opponent in self.head_to_head_races[dog_name]:
                races = self.head_to_head_races[dog_name][opponent]
                wins = self.head_to_head_wins[dog_name].get(opponent, 0)
                
                total_races_vs_opponents += races
                total_wins_vs_opponents += wins
        
        if total_races_vs_opponents == 0:
            return np.nan
        
        return total_wins_vs_opponents / total_races_vs_opponents
    
    def compute_prize_money_earned(self, dog_name):
        """
        Get total prize money earned by dog (quality indicator).
        
        Args:
            dog_name: Name of the dog
            
        Returns:
            Total prize money earned, or 0 if no history
        """
        return self.dog_prize_money.get(dog_name, 0.0)
    
    def compute_trainer_performance_rating(self, dog_name):
        """
        Calculate trainer's overall win rate (handler effect).
        
        Args:
            dog_name: Name of the dog
            
        Returns:
            Trainer's win rate (0-1), or NaN if no history
        """
        if dog_name not in self.dog_trainer:
            return np.nan
        
        trainer = self.dog_trainer[dog_name]
        
        if trainer not in self.trainer_stats:
            return np.nan
        
        stats = self.trainer_stats[trainer]
        
        if stats['starts'] == 0:
            return np.nan
        
        return stats['wins'] / stats['starts']
    
    def add_enhanced_features_to_race(self, race_df, race_date, track):
        """
        Add enhanced features to a race DataFrame before training.
        
        This should be called BEFORE updating history with race results,
        so features reflect only past information.
        
        Args:
            race_df: DataFrame with race data (one row per dog)
            race_date: Date of this race
            track: Track name for this race
            
        Returns:
            DataFrame with 8 new Phase 1 feature columns added
        """
        result_df = race_df.copy()
        
        # Initialize new feature columns
        # Phase 1A
        result_df['DaysSinceLastRace'] = np.nan
        result_df['TrackSpecificWinRate'] = np.nan
        result_df['DistanceSpecificWinRate'] = np.nan
        
        # Phase 1B
        result_df['BoxWinPercentage'] = np.nan
        result_df['RecentSpeedRating'] = np.nan
        result_df['HeadToHeadWinRate'] = np.nan
        
        # Phase 1C
        result_df['PrizeMoneyEarned'] = 0.0
        result_df['TrainerPerformanceRating'] = np.nan
        
        # Get all dog names in this race for head-to-head
        all_dogs_in_race = [row.get('DogName', '') for _, row in result_df.iterrows() if row.get('DogName')]
        
        # Compute features for each dog in the race
        for idx, row in result_df.iterrows():
            dog_name = row.get('DogName', '')
            distance = row.get('Distance', 500)
            box_number = row.get('Box', 0)
            
            if not dog_name:
                continue
            
            # Phase 1A: Compute days since last race
            days_since = self.compute_days_since_last_race(dog_name, race_date)
            result_df.at[idx, 'DaysSinceLastRace'] = days_since
            
            # Phase 1A: Compute track-specific win rate
            track_win_rate = self.compute_track_specific_win_rate(dog_name, track)
            result_df.at[idx, 'TrackSpecificWinRate'] = track_win_rate
            
            # Phase 1A: Compute distance-specific win rate
            distance_win_rate = self.compute_distance_specific_win_rate(dog_name, distance)
            result_df.at[idx, 'DistanceSpecificWinRate'] = distance_win_rate
            
            # Phase 1B: Compute box win percentage
            box_win_pct = self.compute_box_win_percentage(dog_name, box_number)
            result_df.at[idx, 'BoxWinPercentage'] = box_win_pct
            
            # Phase 1B: Compute recent speed rating
            speed_rating = self.compute_recent_speed_rating(dog_name)
            result_df.at[idx, 'RecentSpeedRating'] = speed_rating
            
            # Phase 1B: Compute head-to-head win rate
            opponents = [opp for opp in all_dogs_in_race if opp != dog_name]
            h2h_win_rate = self.compute_head_to_head_win_rate(dog_name, opponents)
            result_df.at[idx, 'HeadToHeadWinRate'] = h2h_win_rate
            
            # Phase 1C: Get prize money earned
            prize_money = self.compute_prize_money_earned(dog_name)
            result_df.at[idx, 'PrizeMoneyEarned'] = prize_money
            
            # Phase 1C: Compute trainer performance rating
            trainer_rating = self.compute_trainer_performance_rating(dog_name)
            result_df.at[idx, 'TrainerPerformanceRating'] = trainer_rating
        
        return result_df
    
    def get_feature_summary(self):
        """
        Get summary statistics about features computed.
        
        Returns:
            Dictionary with summary info
        """
        total_dogs = len(self.dog_race_history)
        total_races = sum(len(races) for races in self.dog_race_history.values())
        
        # Count dogs with track-specific history
        dogs_with_track_history = sum(
            1 for dog in self.dog_track_stats
            if any(stats['starts'] > 0 for stats in self.dog_track_stats[dog].values())
        )
        
        # Count dogs with distance-specific history
        dogs_with_distance_history = sum(
            1 for dog in self.dog_distance_stats
            if any(stats['starts'] > 0 for stats in self.dog_distance_stats[dog].values())
        )
        
        return {
            'total_dogs_tracked': total_dogs,
            'total_races_processed': total_races,
            'dogs_with_track_history': dogs_with_track_history,
            'dogs_with_distance_history': dogs_with_distance_history,
            'unique_tracks': sum(len(tracks) for tracks in self.dog_track_stats.values()),
            'unique_distances': sum(len(distances) for distances in self.dog_distance_stats.values())
        }


def add_enhanced_features(race_data_list, winners_list):
    """
    Process all historical races and add enhanced features.
    
    This function processes races in chronological order to build up
    historical statistics, then adds features to each race based on
    past data only (no data leakage).
    
    Args:
        race_data_list: List of DataFrames, one per race
        winners_list: List of winner box numbers (parallel to race_data_list)
        
    Returns:
        Tuple of (enhanced_race_data_list, winners_list, feature_summary)
    """
    logger.info("Starting enhanced feature computation...")
    logger.info(f"Processing {len(race_data_list)} races")
    
    # Initialize feature builder
    builder = HistoricalFeatureBuilder()
    
    # We need to sort races by date to process in chronological order
    # Extract dates and create index mapping
    race_dates = []
    for race_df in race_data_list:
        # Try to get date from DataFrame
        if 'Date' in race_df.columns:
            race_date = race_df['Date'].iloc[0] if len(race_df) > 0 else None
        else:
            race_date = None
        race_dates.append(race_date)
    
    # Create sorted indices
    valid_indices = [i for i, date in enumerate(race_dates) if date is not None]
    if len(valid_indices) < len(race_data_list):
        logger.warning(f"Found {len(race_data_list) - len(valid_indices)} races without dates - these will be processed last")
    
    # Sort by date
    try:
        sorted_indices = sorted(valid_indices, key=lambda i: pd.to_datetime(race_dates[i]))
        # Add races without dates at the end
        sorted_indices.extend([i for i in range(len(race_data_list)) if i not in valid_indices])
    except:
        logger.warning("Could not sort races by date - processing in original order")
        sorted_indices = list(range(len(race_data_list)))
    
    # Process races in chronological order
    enhanced_race_data_list = []
    enhanced_winners_list = []
    
    for idx in sorted_indices:
        race_df = race_data_list[idx]
        winner_box = winners_list[idx]
        
        # Get race metadata
        race_date = race_dates[idx]
        track = race_df['Track'].iloc[0] if 'Track' in race_df.columns and len(race_df) > 0 else 'Unknown'
        
        # Add enhanced features (based on history up to this point)
        enhanced_df = builder.add_enhanced_features_to_race(race_df, race_date, track)
        enhanced_race_data_list.append(enhanced_df)
        enhanced_winners_list.append(winner_box)
        
        # Update history with this race's results
        if race_date is not None:
            # Get all dogs in this race for head-to-head tracking
            all_dogs_in_race = [dog_row.get('DogName', '') for _, dog_row in race_df.iterrows() if dog_row.get('DogName')]
            
            # Calculate average race time for speed ratings
            race_times = [dog_row.get('Time', 0) for _, dog_row in race_df.iterrows() if pd.notna(dog_row.get('Time', 0)) and dog_row.get('Time', 0) > 0]
            field_avg_time = np.mean(race_times) if race_times else None
            
            for _, dog_row in race_df.iterrows():
                dog_name = dog_row.get('DogName', '')
                box_number = dog_row.get('Box', 0)
                distance = dog_row.get('Distance', 500)
                race_time = dog_row.get('Time', None)
                trainer = dog_row.get('Trainer', '')
                prize_money = dog_row.get('PrizeMoney', 0)
                
                # Position is 1 if this dog won, otherwise approximate from form
                position = 1 if box_number == winner_box else 2
                
                # Opponents are all other dogs in this race
                opponents = [opp for opp in all_dogs_in_race if opp != dog_name]
                
                builder.update_dog_history(
                    dog_name=dog_name,
                    race_date=race_date,
                    track=track,
                    distance=distance,
                    position=position,
                    box_number=box_number,
                    race_time=race_time,
                    field_avg_time=field_avg_time,
                    trainer=trainer,
                    prize_money=prize_money,
                    opponents=opponents
                )
    
    # Get summary statistics
    summary = builder.get_feature_summary()
    
    logger.info("Enhanced feature computation complete")
    logger.info(f"Summary: {summary}")
    
    return enhanced_race_data_list, enhanced_winners_list, summary
