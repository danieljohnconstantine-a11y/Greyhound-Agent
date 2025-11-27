# 🏁 Greyhound Prediction Accuracy Analysis - 25/11/2024

## 📊 Overall Performance

- **Total Races Analyzed**: 137
- **Correct Predictions**: 55
- **Incorrect Predictions**: 82
- **Prediction Accuracy**: **40.15%**

## 🎯 Detailed Results by Track

| Track | Correct | Total | Accuracy |
|-------|---------|-------|----------|
| MURRAY BDGE STRAIGHT | 6 | 10 | 60.0% |
| BALLARAT | 8 | 14 | 57.1% |
| Q LAKESIDE | 8 | 14 | 57.1% |
| Angle Park | 5 | 10 | 50.0% |
| Mandurah | 5 | 10 | 50.0% |
| GRAFTON | 4 | 10 | 40.0% |
| GOSFORD | 4 | 11 | 36.4% |
| Bulli | 4 | 12 | 33.3% |
| HORSHAM | 4 | 12 | 33.3% |
| LAUNCESTON | 3 | 10 | 30.0% |
| TOWNSVILLE | 2 | 12 | 16.7% |
| Warragul | 2 | 12 | 16.7% |

## 🔍 Scoring Variable Analysis

**Top Variables Correlated with Correct Predictions:**

| Variable | Correct Mean | Incorrect Mean | Difference | Effect Size (Cohen's d) | Significant |
|----------|--------------|----------------|------------|------------------------|-------------|
| RecentFormBoost | 0.564 | 0.457 | +0.106 | 0.360 | ✅ |
| ConsistencyIndex | 0.153 | 0.193 | -0.040 | -0.278 | ❌ |
| FinishConsistency | 0.109 | 0.188 | -0.079 | -0.276 | ❌ |
| PrizeMoney | 19368.709 | 26995.195 | -7626.486 | -0.251 | ❌ |
| DLWFactor | 0.505 | 0.437 | +0.069 | 0.208 | ❌ |
| EarlySpeedIndex | 79.799 | 73.547 | +6.252 | 0.191 | ❌ |
| Speed_kmh | 63.819 | 64.288 | -0.469 | -0.160 | ❌ |
| TrainerStrikeRate | 0.155 | 0.173 | -0.018 | -0.158 | ❌ |
| DrawFactor | 0.853 | 0.830 | +0.022 | 0.158 | ❌ |
| PlaceRate | 0.310 | 0.291 | +0.019 | 0.127 | ❌ |

### 📈 Interpretation:
- **Positive difference**: Variable is higher in correct predictions (should increase weight)
- **Negative difference**: Variable is lower in correct predictions (should decrease weight)
- **Effect Size > 0.3**: Meaningful difference
- **Significance**: p-value < 0.05 indicates statistical significance

## 💡 Recommendations

### 1. 🔴 Increase Weight (Priority: HIGH)

**Variables**: RecentFormBoost

**Reason**: These variables are significantly higher in correct predictions with strong effect

  - `RecentFormBoost`: Mean difference = +0.106, Effect size = 0.360

**Action**: Increase the weights for these variables in the scoring algorithm (in `src/features.py`, function `get_weights()`). These have the strongest correlation with winning picks.

### 2. 🟡 Increase Weight (Priority: MEDIUM)

**Variables**: DLWFactor, EarlySpeedIndex, DrawFactor

**Reason**: These variables show moderate positive correlation with correct predictions

  - `DLWFactor`: Mean difference = +0.069, Effect size = 0.208
  - `EarlySpeedIndex`: Mean difference = +6.252, Effect size = 0.191
  - `DrawFactor`: Mean difference = +0.022, Effect size = 0.158

**Action**: Increase the weights for these variables in the scoring algorithm (in `src/features.py`, function `get_weights()`). These show moderate positive correlation.

### 3. 🟡 Decrease Weight (Priority: MEDIUM)

**Variables**: ConsistencyIndex, FinishConsistency, PrizeMoney, Speed_kmh, TrainerStrikeRate

**Reason**: These variables show moderate negative correlation - higher values may hurt predictions

  - `ConsistencyIndex`: Mean difference = -0.040, Effect size = -0.278
  - `FinishConsistency`: Mean difference = -0.079, Effect size = -0.276
  - `PrizeMoney`: Mean difference = -7626.486, Effect size = -0.251

**Action**: Decrease the weights for these variables or investigate why high values correlate with incorrect predictions. Moderate negative correlation suggests caution.

### 4. 🟢 Remove Or Revise (Priority: LOW)

**Variables**: PlaceRate, DistanceSuit, BoxBiasFactor, BoxPositionBias, OverexposedPenalty

**Reason**: These variables show weak correlation with winning picks

  - `PlaceRate`: Mean difference = +0.019, Effect size = 0.127
  - `DistanceSuit`: Mean difference = -0.006, Effect size = -0.112
  - `BoxBiasFactor`: Mean difference = -0.018, Effect size = -0.077

**Action**: Consider removing these variables or collecting better data for them, as they don't seem to contribute meaningfully to prediction accuracy.


## ⚙️ Suggested Weight Adjustments

Based on the analysis above, here are concrete weight adjustments for `src/features.py`:

### Variables to INCREASE:

- **RecentFormBoost**: strong increase (effect size: 0.360)
- **DLWFactor**: moderate increase (effect size: 0.208)
- **EarlySpeedIndex**: moderate increase (effect size: 0.191)
- **DrawFactor**: moderate increase (effect size: 0.158)

### Variables to DECREASE:

- **ConsistencyIndex**: moderate decrease (effect size: -0.278)
- **FinishConsistency**: moderate decrease (effect size: -0.276)
- **PrizeMoney**: moderate decrease (effect size: -0.251)

**Note**: Adjust weights proportionally while maintaining total weight = 1.0 for each distance category.


## 🎲 Sample Predictions vs Actuals

| Track | Race | Predicted (Box) | Predicted Dog | Actual Box | Result |
|-------|------|----------------|---------------|------------|--------|
| Angle Park | R1 | Box 7 | Lady Turbine | Box 4 | ❌ Wrong |
| Angle Park | R2 | Box 5 | Exultant McLaren | Box 5 | ✅ Correct |
| Angle Park | R3 | Box 1 | Miss Rubble | Box 7 | ❌ Wrong |
| Angle Park | R4 | Box 4 | Destini Fresco | Box 4 | ✅ Correct |
| Angle Park | R5 | Box 5 | Archer Nine | Box 5 | ✅ Correct |
| Angle Park | R6 | Box 7 | Russo | Box 7 | ✅ Correct |
| Angle Park | R7 | Box 1 | Pippa's Hero | Box 7 | ❌ Wrong |
| Angle Park | R8 | Box 4 | Fantastic Tommy | Box 4 | ✅ Correct |
| Angle Park | R9 | Box 7 | Footrot Fan | Box 8 | ❌ Wrong |
| Angle Park | R10 | Box 7 | Kicker Dusty | Box 8 | ❌ Wrong |

*... and 127 more races*

## 📈 Key Insights

### Distance Analysis

| Distance Category | Correct | Total | Accuracy |
|-------------------|---------|-------|----------|
| Sprint (<400m) | 39 | 94 | 41.5% |
| Middle (400-500m) | 14 | 37 | 37.8% |
| Long (>500m) | 2 | 6 | 33.3% |

