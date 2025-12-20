# Comprehensive Scoring Factors Breakdown (v4.1)

## All 51 Scoring Factors - Weight & Win Percentage Analysis

Based on analysis of 484+ races (Nov 2025)

---

## v4.1 KEY CHANGES

### NEW: Track-Specific Factor Weights
- **Problem:** Different tracks favor different winning profiles
- **Solution:** Track-specific factor weight adjustments based on dominant box patterns
- **Categories:**
  - BOX1_SPEED: Prioritize BestTimePercentile, EarlySpeedPercentile
  - BOX2_FORM: Prioritize DLWFactor, ConsistencyIndex, PlaceRate
  - BOX8_CLOSER: Prioritize CloserBonus, BestTimePercentile (at distance)
  - BOX4_EXPERIENCE: Prioritize ExperienceTier, ConsistencyIndex
  - BOX6_FORM: Prioritize ExperienceTier, FormMomentum
  - BOX7_CLOSER: Prioritize CloserBonus, FormMomentum

### NEW: TrackPattern Classification
- Each track is classified into one of 7 patterns
- Pattern determines which factors get weight boosts

### TrackComprehensiveAdjustment (v4.0)
- Track-specific adjustments for ALL boxes (1-8) at 25 tracks
- Expected +10-15% improvement at problem tracks

---

## CATEGORY 1: BOX/DRAW POSITION (30-40% of total signal)

### Additive Factors (weighted sum)

| Factor | Weight (Middle Dist) | Win % When Favorable | Notes |
|--------|---------------------|---------------------|-------|
| BoxPositionBias | 0.10 | **21.0% Box 1 vs 12.5% random** | Primary box advantage signal |
| BoxPlaceRate | 0.05 | 16.1% Box 2 leads | Dogs that place consistently |
| BoxTop3Rate | 0.04 | 49.7% Box 1 | Overall competitiveness |
| DrawFactor | 0.10 | +17% for draws 1-3 | Inside draw advantage |
| RailPreference | 0.03 | +2% Box 1-2, +1% Box 8 | Rail running style |
| BoxBiasFactor | 0.02 | Varies by dog | Individual dog's box preference |
| FieldSizeAdjustment | ~0.01 | +2% Box 1-2 in small fields | Field size impacts box value |
| **TrackBox1Adjustment** | +0.02 to +0.15 | +10-42% at Lakeside, Cannington | Track-specific Box 1 bonus |
| **TrackBox4Adjustment** | +0.02 to +0.10 | +5-33% at Broken Hill, Grafton | Track-specific Box 4 bonus |
| **TrackComprehensiveAdjustment** (v4.0) | -0.05 to +0.15 | Varies by track | ALL boxes at 25 tracks |

### v4.0 Track-Specific Box Adjustments

| Track | Top Box | Adjustment | Notes |
|-------|---------|------------|-------|
| Darwin | Box 1/2 (21.1% each) | Box 2: +0.05, Box 1: +0.02 | Equal Box 1/2 |
| Rockhampton | Box 1 (33.3%) | Box 1: +0.10 | Strong Box 1 boost |
| Temora | Box 8 (50.0%) | Box 8: +0.15, Box 1: +0.10 | Extreme Box 8 |
| Lakeside | Box 1 (41.7%) | Box 1: +0.15 | Very strong Box 1 |
| Gawler | Box 2 (36.8%) | Box 2: +0.12, Box 1: +0.06 | Strong Box 2 |
| Warragul | Box 6 (41.7%) | Box 6: +0.12 | Unusual Box 6 |
| Gunnedah | Box 7 (33.3%) | Box 7: +0.10 | Unusual Box 7 |

### Multiplicative Factors (v3.9 CRITICAL)

| Factor | Multiplier | Win % Justification |
|--------|-----------|---------------------|
| **BoxPenaltyFactor** | | |
| - Box 1 | 1.08x | 19.5% win rate (top performer) |
| - Box 2 | 1.03x | **16.2% - INCREASED from 0.97x** |
| - Box 3 | 0.82x | 8.7% (trap position) |
| - Box 4 | 1.02x | 13.5% (good position) |
| - Box 5 | 0.88x | 8.8% (weak) |
| - Box 6 | 0.92x | 9.2% (weak) |
| - Box 7 | 0.82x | **9.1% - INCREASED from 0.75x** |
| - Box 8 | 1.05x | 15.0% (outside rail advantage) |

---

## CATEGORY 2: CAREER/EXPERIENCE (25-30% of signal)

| Factor | Weight | Win % When Favorable | Notes |
|--------|--------|---------------------|-------|
| ConsistencyIndex | 0.05 | **+35% for dogs with >30% win rate** | CareerWins/CareerStarts |
| PlaceRate | 0.05 | +25% for >40% place rate | Career places/starts |
| WinPlaceRate | 0.05 | +30% for combined >60% | Win+Place rate |
| ExperienceTier | 0.04 | Peak at 15-40 starts | |
| - 0-5 starts | 0.7x | Low reliability, unpredictable |
| - 6-15 starts | 0.85x | Developing |
| - 16-40 starts | 1.0x | **Prime experience** |
| - 41-60 starts | 0.95x | Veteran |
| - 61-80 starts | 0.9x | Overraced |
| - 80+ starts | 0.8x | Heavily campaigned |
| TrainerStrikeRate | 0.04 | **+15% for elite trainers (25%+)** | Trainer career win rate |
| ClassRating | 0.03 | +20% for high earners | Based on prize money |

---

## CATEGORY 3: SPEED/TIMING (18-22% of signal)

| Factor | Weight | Win % When Favorable | Notes |
|--------|--------|---------------------|-------|
| BestTimePercentile | 0.06 | **+45% for fastest in race** | FIXED in v3.6 - faster = higher rank |
| EarlySpeedPercentile | 0.05 | +30% for top 25% early speed | Early speed within race |
| EarlySpeedIndex | 0.03 | Variable | Distance/sectional time |
| SectionalSec | 0.04 | Lower = better | First split time |
| Speed_kmh | 0.03 | +25% for >18m/s | Raw speed |
| SpeedClassification | 0.01 | 1.1x for fast sprinters | Sprinter vs Stayer |
| SpeedAtDistance | Derived | Variable | Distance/BestTime |

---

## CATEGORY 4: FORM/MOMENTUM (10-15% of signal)

| Factor | Weight | Win % When Favorable | Notes |
|--------|--------|---------------------|-------|
| WinStreakFactor | 0.04 | **+30% for DLW ≤7 days** | Hot streak bonus |
| - DLW ≤7 days | 1.30x | **Enhanced from 1.08x** |
| - DLW ≤14 days | 1.20x | Recent winner |
| - DLW ≤28 days | 1.05x | Within a month |
| - DLW ≤60 days | 0.95x | Going cold |
| - DLW >60 days | 0.85x | Long time since win |
| DLWFactor | 0.03 | +23% for DLW ≤14 | Days since last win |
| FormMomentumNorm | 0.03 | +15% for improving | Margin trend |
| MarginFactor | 0.02 | +25% for avg margin ≥3 | Winning margin dominance |
| Last3FinishFactor | 0.02 | **+15% for strong form** | Last 3 race margins |
| - Avg margin ≥2 | 1.15x | Strong recent form |
| - Avg margin ≥0.5 | 1.08x | Good recent form |
| - Avg margin ≥0 | 1.0x | Average |
| - Avg margin ≥-1 | 0.9x | Below average |
| - Avg margin <-1 | 0.8x | Poor recent form |

---

## CATEGORY 5: CONDITIONING (5-8% of signal)

| Factor | Weight | Win % When Favorable | Notes |
|--------|--------|---------------------|-------|
| FreshnessFactor | 0.02 | **+10% for 6-10 days rest** | Days since last race |
| - ≤4 days | 0.85x | Too quick turnaround |
| - 5-10 days | 1.0x | **OPTIMAL** |
| - 11-14 days | 0.97x | Good rest |
| - 15-21 days | 0.93x | Slightly stale |
| - 22-35 days | 0.87x | Getting stale |
| - 36-60 days | 0.80x | Returning from break |
| - >60 days | 0.70x | Long layoff |
| AgeFactor | 0.02 | **+5% at peak age (26-36 months)** | Age curve |
| - 26-36 months | 1.05x | **PEAK performance** |
| - 24-42 months | 1.0x | Prime range |
| - 20-24 months | 0.93x | Young/developing |
| - 43-48 months | 0.93x | Experienced senior |
| - 49-54 months | 0.85x | Senior decline |
| - >54 months | 0.75x | Veteran (steep decline) |
| WeightFactor | 0.02 | +10% at 29.5-31.5kg | Optimal racing weight |

---

## CATEGORY 6: ENHANCEMENT MULTIPLIERS (Applied Last)

| Factor | Multiplier Range | Win % Impact | Notes |
|--------|-----------------|--------------|-------|
| GradeFactor | 0.75x - 1.0x | -10% for novices | Speed-adjusted for fast novices |
| - ≤5 starts | 0.75x (base) | +15% if fast times |
| - 6-10 starts | 0.88x (base) | +10% if fast times |
| - 11-20 starts | 0.95x | Intermediate |
| - 21-50 starts | 1.0x | Reliable stats |
| - >50 starts | 0.95x | Veteran |
| DistanceChangeFactor | 0.85x - 1.0x | -15% for new distance | Inexperienced at distance |
| PaceBoxFactor | 0.93x - 1.10x | **+10% for front-runner Box 1-2** | Pace-Box interaction |
| TrainerTier | 0.95x - 1.15x | +15% for elite trainers | |
| - ≥25% strike rate | 1.15x | Elite trainer |
| - 20-25% | 1.08x | Very good |
| - 15-20% | 1.03x | Good |
| - 10-15% | 1.0x | Average |
| - <10% | 0.95x | Below average |
| SurfacePreferenceFactor | 0.98x - 1.02x | Minor | Surface match |
| CloserBonus | 1.0x - 1.08x | **+8% for Box 7-8 at 500m+** | Late closer advantage |
| TrainerMomentum | 0.98x - 1.12x | **+12% for hot trainer** | Recent trainer success |

---

## CATEGORY 7: LUCK/PREDICTABILITY ADJUSTMENTS

| Factor | Adjustment | Effect | Notes |
|--------|-----------|--------|-------|
| FieldSimilarityIndex | 0.8x - 1.1x | High similarity = harder to predict | Score clustering |
| TrackUpsetFactor | 0.80x - 1.15x | Track-specific volatility | |
| - Angle Park | 0.80 | Very predictable (50% Box 1!) |
| - Cannington | 0.82 | Very predictable |
| - Meadows | 0.85 | Predictable |
| - Capalaba | 0.87 | Good |
| - Dubbo | 0.90 | Moderate |
| - Rockhampton | 1.15 | **VERY UNPREDICTABLE (0% Nov 30!)** |
| - Darwin | 1.10 | Unpredictable (9.1% Nov 30) |
| - Taree | 1.08 | Volatile |
| CompetitorAdjustment | 0.9x - 1.1x | Competitive field density | More contenders = harder |

---

## WINNING PATTERNS IDENTIFIED ("Luck Factors")

### Pattern 1: Box 2 "Shadow Effect"
- **Finding**: When we pick Box 1, Box 2 wins 23.8% of the time (Nov 30)
- **Explanation**: Box 2 has inside rail access without getting blocked
- **Action**: Increased Box 2 penalty factor from 0.97x to 1.03x (now BONUS)

### Pattern 2: Hot Streak Momentum
- **Finding**: 19% of missed winners had won within 7 days
- **Explanation**: Dogs on winning streaks have psychological/physical momentum
- **Action**: Increased WinStreakFactor from 1.08x to 1.30x for DLW ≤7

### Pattern 3: Track Volatility
- **Finding**: Rockhampton 0% accuracy, Darwin 9.1% vs Cannington 41.7%
- **Explanation**: Some tracks have track conditions or configurations that reduce predictability
- **Action**: Added track-specific TrackUpsetFactor (0.80-1.15 range)
- **v4.0 Action**: Added TrackComprehensiveAdjustment for all 8 boxes at 25 tracks

### Pattern 4: Field Similarity Chaos
- **Finding**: When 3+ dogs within 2 points, winner nearly random
- **Explanation**: Comparable dogs means luck (bumping, blocking) decides
- **Action**: FieldSimilarityIndex compresses scores toward mean in similar fields

---

## TOTAL FACTOR BREAKDOWN

| Category | Factor Count | % of Signal |
|----------|-------------|-------------|
| Box/Draw Position | 12 | 30-40% |
| Career/Experience | 6 | 25-30% |
| Speed/Timing | 7 | 18-22% |
| Form/Momentum | 5 | 10-15% |
| Conditioning | 3 | 5-8% |
| Enhancement Multipliers | 10 | Multiplicative |
| Luck/Predictability | 7 | Adjustment |
| **TOTAL** | **50** | **100%** |

---

## VERSION HISTORY

| Version | Win Rate | Key Change |
|---------|----------|------------|
| v3.4 | ~14% | Original |
| v3.5 | ~16% | Box rate updates |
| v3.6 | ~17% | Parser fix + BestTimePercentile fix |
| v3.7 | 20.3% | BoxPenaltyFactor (multiplicative) |
| v3.8 | 17.3% | Weight optimization (Nov 30 outlier) |
| v3.9 | ~20% | Box 2 boost, Box 7 penalty reduction |
| **v4.0** | **TBD** | **TrackComprehensiveAdjustment for 25 tracks** |

---

*Generated: December 1, 2025*
*Based on: 386 races from Nov 2025*
