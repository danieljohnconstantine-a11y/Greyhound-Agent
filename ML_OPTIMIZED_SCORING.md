# ML-Optimized Scoring Matrix - November 27, 2025

## Overview

Used machine learning (logistic regression) to analyze **2,467 dogs** across **386 races** to determine optimal feature weights for predicting winners.

## Key Finding: Box Position is THE Dominant Factor

The ML analysis revealed that **box position (DrawFactor + BoxPositionBias) accounts for ~41%** of winner prediction signal - far more than previously thought.

### Winner Prediction Importance Ranking

| Rank | Feature | Weight | Category |
|------|---------|--------|----------|
| 1 | **DrawFactor** | 41.0% | Box Position |
| 2 | CareerPlaces | 11.5% | Career |
| 3 | CareerStarts | 8.8% | Career |
| 4 | SectionalSec | 6.9% | Timing |
| 5 | EarlySpeedIndex | 5.1% | Timing |
| 6 | ConsistencyIndex | 5.1% | Career |
| 7 | TrainerStrikeRate | 5.0% | Other |
| 8 | DLWFactor | 4.3% | Form |
| 9 | Speed_kmh | 3.9% | Timing |
| 10 | BoxBiasFactor | 2.0% | Box Position |

## Weight Distribution by Category

| Category | Old Weight | New Weight | Change |
|----------|------------|------------|--------|
| Box Position | 9% | **42%** | +33% ↑↑↑ |
| Career | 12% | **27.5%** | +15.5% ↑↑ |
| Timing | 34% | **17.6%** | -16.4% ↓ |
| Form | 11% | **5.1%** | -5.9% ↓ |
| Other | 34% | **7.8%** | -26.2% ↓ |

## What This Means

### Previously Overweighted:
- Early speed and raw speed (timing) - was 34%, now 17.6%
- Form indicators (margins, momentum) - was 11%, now 5.1%
- Track conditions, weight factors - minimal impact

### Previously Underweighted:
- **Box position (draw)** - was 9%, should be 42% (!!)
- Career places - consistency in placing is #2 predictor
- Experience (career starts) - more starts = better predictor

## New Scoring Strategy

### For Sprints (<400m):
Focus heavily on box position (42% weight) since there's less time to overcome poor positioning:
- DrawFactor: 22%
- BoxPositionBias: 20%
- Career experience: 19%
- Timing: 19%

### For Middle Distances (400-500m):
Box still dominant but career matters more:
- DrawFactor: 18%
- BoxPositionBias: 16%
- Career/Experience: 29%
- Timing: 17%

### For Long Distances (>500m):
Career and experience become most important - dogs need stamina and consistency:
- DrawFactor: 14%
- BoxPositionBias: 12%
- Career/Experience: 35%
- Timing: 15%

## Technical Details

### Methodology:
1. Parsed all 30 PDF form guides (2,467 dogs)
2. Computed all features for each dog
3. Used box position win rates as target variable (from 386 race results)
4. Applied logistic regression with L2 regularization
5. Extracted feature coefficients as importance weights

### Box Position Win Rates (386 races):
- Box 1: 18.1% (BEST)
- Box 2: 15.3% (2nd)
- Box 8: 14.2% (3rd)
- Box 4: 12.7% (average)
- Box 6: 11.9%
- Box 5: 9.8%
- Box 7: 9.6% (2nd worst)
- Box 3: 8.0% (WORST)

## Expected Impact

With these ML-optimized weights:
1. **Predictions will favor dogs in boxes 1, 2, and 8** - the statistical winners
2. **Career placers will rank higher** - consistency matters
3. **Experienced dogs will score better** - more starts = predictable performance
4. **Speed alone won't dominate** - fast dogs in bad boxes will rank lower

## Files Changed

- `src/features.py` - Updated `get_weights()` function with ML-derived weights

## Validation

The weights have been validated to sum to 1.0 for each distance category and the module loads correctly.
