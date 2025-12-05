# Comprehensive 25+ Variable Scoring Matrix

## Overview

This document describes the comprehensive scoring matrix used for greyhound race predictions. The matrix uses **25+ variables** derived from machine learning analysis of 2,467 dogs across 386 race results (September-November 2025).

## Variable Categories

The scoring system groups variables into 5 major categories:

| Category | Sprint (<400m) | Middle (400-500m) | Long (>500m) |
|----------|----------------|-------------------|--------------|
| Box Position | 38% | 32% | 26% |
| Career/Experience | 26% | 28% | 32% |
| Speed/Timing | 18% | 20% | 20% |
| Form/Momentum | 10% | 12% | 14% |
| Conditioning | 8% | 8% | 8% |

## All 25+ Variables

### 1. Box Position Variables (30-40%)

| Variable | Description | Source |
|----------|-------------|--------|
| `DrawFactor` | Raw draw/box position advantage | Parsed from PDF |
| `BoxPositionBias` | Win rate by box (386 races) | Calculated from results |
| `BoxPlaceRate` | 2nd place rate by box | Calculated from results |
| `BoxTop3Rate` | Top 3 finish rate by box | Calculated from results |
| `RailPreference` | Inside/outside rail bonus | Derived from box |
| `BoxBiasFactor` | Individual dog's box preference | Parsed from race history |

**Box Statistics (386 races analyzed):**

| Box | Win Rate | Place Rate | Top 3 Rate |
|-----|----------|------------|------------|
| 1 | 18.1% ⬆️ | 14.2% | 49.7% ⬆️ |
| 2 | 15.3% | 16.1% ⬆️ | 41.7% |
| 3 | 8.0% ⬇️ | 8.3% ⬇️ | 25.6% ⬇️ |
| 4 | 12.7% | 14.5% | 39.1% |
| 5 | 9.8% | 9.6% | 28.8% |
| 6 | 11.9% | 10.1% | 34.5% |
| 7 | 9.6% | 11.7% | 33.4% |
| 8 | 14.2% | 14.2% | 44.6% |

### 2. Career/Experience Variables (25-32%)

| Variable | Description | Formula/Source |
|----------|-------------|----------------|
| `PlaceRate` | Career place percentage | CareerPlaces / CareerStarts |
| `ConsistencyIndex` | Career win percentage | CareerWins / CareerStarts |
| `WinPlaceRate` | Combined win+place rate | (Wins + Places) / Starts |
| `ExperienceTier` | Career starts tier (0.7-1.0) | Based on CareerStarts |
| `TrainerStrikeRate` | Trainer's overall success | Aggregated from all dogs |
| `ClassRating` | Prize money class (0-1) | Normalized PrizeMoney |

**Experience Tiers:**
- Novice (0-5 starts): 0.7 (unpredictable)
- Developing (6-15): 0.85
- Prime (16-40): 1.0 ⬆️
- Veteran (41-60): 0.95
- Overraced (61-80): 0.9
- Heavily Campaigned (80+): 0.8

### 3. Speed/Timing Variables (15-20%)

| Variable | Description | Source |
|----------|-------------|--------|
| `EarlySpeedPercentile` | Early speed rank in race | Calculated per-race |
| `BestTimePercentile` | Best time rank in race | Calculated per-race |
| `SectionalSec` | Raw sectional time | Parsed from PDF |
| `EarlySpeedIndex` | Early speed index | Distance / SectionalSec |
| `Speed_kmh` | Raw speed | Distance / BestTimeSec |
| `SpeedClassification` | Sprinter vs stayer (0.9-1.1) | Speed categorization |

### 4. Form/Momentum Variables (10-14%)

| Variable | Description | Formula |
|----------|-------------|---------|
| `DLWFactor` | Days since last win factor | 0.8-1.2 based on DLW |
| `WinStreakFactor` | Winning streak bonus | 0.8-1.2 based on DLW |
| `FormMomentumNorm` | Form trend direction | Normalized margin trend |
| `MarginFactor` | Average winning margin | 0.4-1.0 based on margins |

**DLW (Days Last Win) Factors:**
- ≤7 days: 1.2 (hot streak)
- 8-14 days: 1.1 (recent winner)
- 15-28 days: 1.0 (normal)
- 29-60 days: 0.9 (cooling)
- >60 days: 0.8 (cold)

### 5. Conditioning Variables (8%)

| Variable | Description | Optimal Range |
|----------|-------------|---------------|
| `FreshnessFactor` | Days since last race | 6-14 days optimal |
| `AgeFactor` | Age in optimal range | 24-42 months peak |
| `WeightFactor` | Racing weight | 29.5-31.5 kg optimal |

**Age Factors:**
- Very Young (<18 months): 0.7
- Young (18-23): 0.9
- Peak (24-42): 1.0 ⬆️
- Experienced (43-48): 0.9
- Senior (49-54): 0.8
- Veteran (55+): 0.6

## Weight Distribution by Distance

### Sprint (<400m)
Box position is CRITICAL for short races:
- DrawFactor: 12%
- BoxPositionBias: 10%
- BoxPlaceRate: 6%
- BoxTop3Rate: 5%
- RailPreference: 3%
- BoxBiasFactor: 2%
**Total Box: 38%**

### Middle (400-500m)
More balanced approach:
- Box Position: 32%
- Career: 28%
- Speed: 20%
- Form: 12%
- Conditioning: 8%

### Long (>500m)
Stamina and consistency dominate:
- Box Position: 26%
- Career: 32% ⬆️
- Speed: 20%
- Form: 14%
- Conditioning: 8%

## Missing Data Handling

When timing data is unavailable, the system redistributes weight:

| Scenario | Adjustment |
|----------|------------|
| Both speed + early timing missing | 1.4x boost to career indicators |
| One timing metric missing | 1.2x boost to career indicators |
| Box position weight | 1.5x boost when timing missing |

## Score Calculation

The final score is calculated as:

```
FinalScore = (BoxScore + CareerScore + SpeedScore + FormScore + ConditioningScore) × 100

Where each category is the sum of:
  variable_value × variable_weight × any_adjustments
```

## Expected Outcomes

Based on the 386-race analysis:

| Prediction | Expected Rate |
|------------|---------------|
| Correct Winner | 15-18% |
| In Top 3 | 40-45% |
| Exacta (top 2) | 8-12% |
| Trifecta | 3-5% |

## Data Sources

- Race results: `data/race_results_nov_2025.csv` (386 races)
- Dog data: 30 PDF form guides (2,467 dogs)
- Timing coverage: 90.3% of dogs have timing data

## Version History

- v1.0: Initial 18-variable scoring matrix
- v2.0: ML-optimized weights (41% box position)
- v3.0: **Current** - 25+ variable comprehensive matrix

---
*Last updated: November 27, 2025*
*Analysis period: September - November 2025*
