"""
audit_all_features.py
======================
Metadata catalogue for all 75 ML feature columns used in the greyhound
ensemble models (RF + GB + XGB).

Each entry in FEATURE_META maps a column name to a dict with:
    category  — one of DOG / DERIVED_DOG / RACE / TRACK
    source    — 'PDF' (raw form guide) or 'DERIVED' (computed by features.py)
    description — short human-readable description
"""

FEATURE_META = {
    # ── Raw dog stats (directly from PDF form guide) ──────────────────────────
    'Box':                      {'category': 'DOG',         'source': 'PDF',     'description': 'Starting box number (1-8)'},
    'Draw':                     {'category': 'DOG',         'source': 'PDF',     'description': 'Draw position (may differ from box on some tracks)'},
    'CareerWins':               {'category': 'DOG',         'source': 'PDF',     'description': 'Total career wins'},
    'CareerPlaces':             {'category': 'DOG',         'source': 'PDF',     'description': 'Total career places (2nd or 3rd)'},
    'CareerStarts':             {'category': 'DOG',         'source': 'PDF',     'description': 'Total career starts'},
    'PrizeMoney':               {'category': 'DOG',         'source': 'PDF',     'description': 'Total career prize money (AUD)'},
    'RTC':                      {'category': 'DOG',         'source': 'PDF',     'description': 'Racing Times Category code (speed class)'},
    'DLR':                      {'category': 'DOG',         'source': 'PDF',     'description': 'Days since last race'},
    'DLW':                      {'category': 'DOG',         'source': 'PDF',     'description': 'Days since last win'},
    'Distance':                 {'category': 'RACE',        'source': 'PDF',     'description': 'Race distance in metres'},
    'BestTimeSec':              {'category': 'DOG',         'source': 'PDF',     'description': 'Best recorded race time in seconds at this distance'},
    'SectionalSec':             {'category': 'DOG',         'source': 'PDF',     'description': 'Best sectional (early split) time in seconds'},
    'AgeMonths':                {'category': 'DOG',         'source': 'PDF',     'description': 'Dog age in months'},

    # ── Derived dog features (computed by src/features.py) ────────────────────
    'RestFactor':               {'category': 'DERIVED_DOG', 'source': 'DERIVED', 'description': 'Rest quality score based on DLR (optimal 6-10 days = 1.0)'},
    'Speed_kmh':                {'category': 'DERIVED_DOG', 'source': 'DERIVED', 'description': 'Estimated speed in km/h derived from BestTimeSec and Distance'},
    'EarlySpeedIndex':          {'category': 'DERIVED_DOG', 'source': 'DERIVED', 'description': 'Early burst speed index from SectionalSec'},
    'FinishConsistency':        {'category': 'DERIVED_DOG', 'source': 'DERIVED', 'description': 'Standard deviation of recent finishing positions (lower = more consistent)'},
    'MarginAvg':                {'category': 'DERIVED_DOG', 'source': 'DERIVED', 'description': 'Average winning/losing margin across recent races'},
    'FormMomentum':             {'category': 'DERIVED_DOG', 'source': 'DERIVED', 'description': 'Trend in recent finishing positions (improving vs declining)'},
    'ConsistencyIndex':         {'category': 'DERIVED_DOG', 'source': 'DERIVED', 'description': 'Ratio of places to starts (higher = more consistent placer)'},
    'RecentFormBoost':          {'category': 'DERIVED_DOG', 'source': 'DERIVED', 'description': 'Boost for dogs with strong recent form (last 3 races)'},
    'DistanceSuit':             {'category': 'DERIVED_DOG', 'source': 'DERIVED', 'description': 'Suitability score for current race distance (1.0 for 300-700m)'},
    'TrainerStrikeRate':        {'category': 'DERIVED_DOG', 'source': 'DERIVED', 'description': 'Trainer win strike rate (wins/starts across card)'},
    'OverexposedPenalty':       {'category': 'DERIVED_DOG', 'source': 'DERIVED', 'description': 'Penalty for dogs racing too frequently (over-exposed)'},
    'PlaceRate':                {'category': 'DERIVED_DOG', 'source': 'DERIVED', 'description': 'Career place rate (places / starts)'},
    'DLWFactor':                {'category': 'DERIVED_DOG', 'source': 'DERIVED', 'description': 'Factor based on days since last win (recency bonus)'},
    'DrawFactor':               {'category': 'DERIVED_DOG', 'source': 'DERIVED', 'description': 'Adjustment for draw position vs box position'},
    'FormMomentumNorm':         {'category': 'DERIVED_DOG', 'source': 'DERIVED', 'description': 'Normalised FormMomentum (0-1 scale)'},
    'MarginFactor':             {'category': 'DERIVED_DOG', 'source': 'DERIVED', 'description': 'Winning margin factor (large wins = positive signal)'},
    'RTCFactor':                {'category': 'DERIVED_DOG', 'source': 'DERIVED', 'description': 'Racing Times Category factor (speed class adjustment)'},
    'AgeFactor':                {'category': 'DERIVED_DOG', 'source': 'DERIVED', 'description': 'Age-based performance factor (peak: 26-36 months)'},
    'RailPreference':           {'category': 'DERIVED_DOG', 'source': 'DERIVED', 'description': 'Inside vs outside box preference score'},
    'BoxPenaltyFactor':         {'category': 'DERIVED_DOG', 'source': 'DERIVED', 'description': 'Box-specific penalty/boost (Box 1=1.05, Box 2=1.08, Box 8=1.08)'},
    'SpeedAtDistance':          {'category': 'DERIVED_DOG', 'source': 'DERIVED', 'description': 'Speed score adjusted for current race distance'},
    'SpeedClassification':      {'category': 'DERIVED_DOG', 'source': 'DERIVED', 'description': 'Ordinal speed class (0=slow, 1=average, 2=fast, 3=elite)'},
    'ExperienceTier':           {'category': 'DERIVED_DOG', 'source': 'DERIVED', 'description': 'Experience tier based on total starts (0=novice .. 3=veteran)'},
    'WinStreakFactor':          {'category': 'DERIVED_DOG', 'source': 'DERIVED', 'description': 'Hot streak multiplier (1.50x for back-to-back wins)'},
    'FreshnessFactor':          {'category': 'DERIVED_DOG', 'source': 'DERIVED', 'description': 'Freshness score based on DLR (optimal rest window)'},
    'ClassRating':              {'category': 'DERIVED_DOG', 'source': 'DERIVED', 'description': 'Class rating derived from grade and prize money history'},
    'GradeFactor':              {'category': 'DERIVED_DOG', 'source': 'DERIVED', 'description': 'Race grade adjustment factor (v3.6 speed-adjusted)'},
    'Last3AvgFinish':           {'category': 'DERIVED_DOG', 'source': 'DERIVED', 'description': 'Average finishing position across last 3 races'},
    'Last3FinishFactor':        {'category': 'DERIVED_DOG', 'source': 'DERIVED', 'description': 'Factor from last 3 finishes (1.8x weight for recent winners)'},
    'DistanceChangeFactor':     {'category': 'DERIVED_DOG', 'source': 'DERIVED', 'description': 'Penalty/boost for distance change vs dog best distance'},
    'PaceBoxFactor':            {'category': 'DERIVED_DOG', 'source': 'DERIVED', 'description': 'Front-runner advantage factor from box position'},
    'TrainerTier':              {'category': 'DERIVED_DOG', 'source': 'DERIVED', 'description': 'Trainer quality tier (0=below avg, 1=avg, 2=good, 3=elite)'},
    'FreshnessFactorV2':        {'category': 'DERIVED_DOG', 'source': 'DERIVED', 'description': 'Refined freshness v2 (optimal 6-10 days window)'},
    'AgeFactorV2':              {'category': 'DERIVED_DOG', 'source': 'DERIVED', 'description': 'Refined age factor v2 (peak 26-36 months)'},
    'SurfacePreferenceFactor':  {'category': 'DERIVED_DOG', 'source': 'DERIVED', 'description': 'Surface type preference factor (sand vs grass)'},
    'WinPlaceRate':             {'category': 'DERIVED_DOG', 'source': 'DERIVED', 'description': 'Combined win + place rate (wins + places) / starts'},
    'EarlySpeedPercentile':     {'category': 'DERIVED_DOG', 'source': 'DERIVED', 'description': 'Percentile rank of early speed vs field (1=fastest in race)'},
    'BestTimePercentile':       {'category': 'DERIVED_DOG', 'source': 'DERIVED', 'description': 'Percentile rank of best time vs field (1=fastest time)'},
    'WinStreakFactorV2':        {'category': 'DERIVED_DOG', 'source': 'DERIVED', 'description': 'Enhanced win streak v2 (1.50x hot streak, 1.32x recent win)'},
    'RecentPlaceStreak':        {'category': 'DERIVED_DOG', 'source': 'DERIVED', 'description': 'Recent placing streak factor (v5.3 margin-derived)'},
    'CloserBonus':              {'category': 'DERIVED_DOG', 'source': 'DERIVED', 'description': 'Bonus for strong closers (dogs that finish well)'},
    'TrainerMomentum':          {'category': 'DERIVED_DOG', 'source': 'DERIVED', 'description': 'Trainer hot streak factor (recent trainer form)'},
    'FinalScore':               {'category': 'DERIVED_DOG', 'source': 'DERIVED', 'description': 'Heuristic composite score (weighted sum of all factors)'},

    # ── Box / position features (derived from track history) ─────────────────
    'BoxPositionBias':          {'category': 'TRACK',       'source': 'DERIVED', 'description': 'Box position historical win bias from 386-race analysis'},
    'BoxPlaceRate':             {'category': 'TRACK',       'source': 'DERIVED', 'description': 'Historical place rate for this box at this track'},
    'BoxTop3Rate':              {'category': 'TRACK',       'source': 'DERIVED', 'description': 'Historical top-3 rate for this box at this track'},
    'TrackBox1Adjustment':      {'category': 'TRACK',       'source': 'DERIVED', 'description': 'Track-specific Box 1 win rate adjustment'},
    'TrackBox4Adjustment':      {'category': 'TRACK',       'source': 'DERIVED', 'description': 'Track-specific Box 4 win rate adjustment'},
    'TrackComprehensiveAdjustment': {'category': 'TRACK',   'source': 'DERIVED', 'description': 'Combined track-specific adjustment for all boxes (v5.2)'},
    'TrackBoxWinRatePct':       {'category': 'TRACK',       'source': 'DERIVED', 'description': 'Box win rate percentage at this specific track'},
    'TrackBoxRank':             {'category': 'TRACK',       'source': 'DERIVED', 'description': 'Rank of box by historical win rate at this track (1=best)'},
    'BoxWinAdvantage':          {'category': 'TRACK',       'source': 'DERIVED', 'description': 'Win rate advantage of this box vs field average at this track'},
    'TrackUpsetFactor':         {'category': 'TRACK',       'source': 'DERIVED', 'description': 'Track-specific upset/luck factor (variance in outcomes)'},

    # ── Field / race context features ─────────────────────────────────────────
    'FieldSpeedStd':            {'category': 'RACE',        'source': 'DERIVED', 'description': 'Standard deviation of Speed_kmh across the field'},
    'FieldTimeStd':             {'category': 'RACE',        'source': 'DERIVED', 'description': 'Standard deviation of BestTimeSec across the field'},
    'TimeVsField':              {'category': 'RACE',        'source': 'DERIVED', 'description': "Dog's best time relative to field average (z-score)"},
    'SpeedVsField':             {'category': 'RACE',        'source': 'DERIVED', 'description': "Dog's speed relative to field average (z-score)"},
    'FieldSimilarityIndex':     {'category': 'RACE',        'source': 'DERIVED', 'description': 'How similar this dog is to the rest of the field (0=unique, 1=average)'},
    'CompetitorDensity':        {'category': 'RACE',        'source': 'DERIVED', 'description': 'Density of similar-speed competitors (v5.3 EarlySpeedIndex primary)'},
    'CompetitorAdjustment':     {'category': 'RACE',        'source': 'DERIVED', 'description': 'Adjustment based on number and quality of direct competitors'},
    'FieldSize':                {'category': 'RACE',        'source': 'PDF',     'description': 'Number of dogs in the race (typically 5-8)'},
    'FieldSizeAdjustment':      {'category': 'RACE',        'source': 'DERIVED', 'description': 'Probability adjustment for field size (smaller field = higher base prob)'},
}

assert len(FEATURE_META) == 75, (
    f"FEATURE_META has {len(FEATURE_META)} entries, expected 75. "
    "Update this dict when adding/removing features."
)
