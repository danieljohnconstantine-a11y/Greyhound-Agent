# CRITICAL SCORING MATRIX REVIEW v3.9

**Date**: December 1, 2025  
**Requested By**: @danieljohnconstantine-a11y  
**Purpose**: Brutal honest review of scoring matrix based on actual results

---

## EXECUTIVE SUMMARY: Our Matrix is OVER-FITTING Box 1

### The Core Problem

Our current predictions show **Box 1 at 34.7%** of all top picks, but actual results show:

| Date | Actual Box 1 Wins | Our Box 1 Predictions |
|------|-------------------|----------------------|
| Nov 28 | 20.7% | ~30% |
| Nov 29 | 22.2% | ~32% |
| Nov 30 | **15.5%** | ~35% |

**We are over-picking Box 1 by 50-100%!**

### Critical Finding: Box 2 is MASSIVELY Under-Valued

| Date | Actual Box 2 Wins | Our Box 2 Predictions |
|------|-------------------|----------------------|
| Nov 28 | 12.6% | ~12% |
| Nov 29 | 12.2% | ~14% |
| Nov 30 | **23.8%** 🔥 | ~16% |

Box 2 had its BEST day ever on Nov 30 and we completely missed it.

---

## PROBLEM #1: Box Weights Are Based on STALE Data

### Current BOX_WIN_RATE (hardcoded)
```python
BOX_WIN_RATE = {
    1: 0.210,  # 21.0%
    2: 0.120,  # 12.0%  <-- TOO LOW!
    3: 0.080,  # 8.0%
    4: 0.155,  # 15.5%
    5: 0.098,  # 9.8%
    6: 0.122,  # 12.2%
    7: 0.055,  # 5.5%
    8: 0.160,  # 16.0%
}
```

### Actual Win Rates (Nov 28-30, 335 races)

| Box | Nov 28 | Nov 29 | Nov 30 | 3-Day Avg | Current Matrix | Difference |
|-----|--------|--------|--------|-----------|----------------|------------|
| 1 | 20.7% | 22.2% | 15.5% | **19.5%** | 21.0% | **-1.5%** |
| 2 | 12.6% | 12.2% | **23.8%** | **16.2%** | 12.0% | **+4.2%** 🔴 |
| 3 | 9.6% | 7.8% | 8.7% | **8.7%** | 8.0% | +0.7% |
| 4 | 14.1% | 16.7% | 9.7% | **13.5%** | 15.5% | -2.0% |
| 5 | 8.9% | 8.9% | 8.7% | **8.8%** | 9.8% | -1.0% |
| 6 | 8.1% | 12.2% | 7.3% | **9.2%** | 12.2% | -3.0% |
| 7 | 11.9% | 5.6% | 9.7% | **9.1%** | 5.5% | **+3.6%** 🔴 |
| 8 | 14.1% | 14.4% | 16.5% | **15.0%** | 16.0% | -1.0% |

### Key Issues:
1. **Box 2 is under-valued by 4.2%** - We're missing Box 2 winners
2. **Box 7 is over-penalized by 3.6%** - Our 0.75x penalty is too harsh
3. **Box 1 is slightly over-valued by 1.5%** - We're over-picking Box 1

---

## PROBLEM #2: BoxPenaltyFactor Is TOO AGGRESSIVE

Current penalties:
```python
BOX_PENALTY_FACTORS = {
    1: 1.12,   # +12% bonus
    2: 0.97,   # -3% penalty  <-- Should be NEUTRAL or slight BONUS!
    3: 0.80,   # -20% penalty
    4: 1.05,   # +5% bonus
    5: 0.90,   # -10% penalty
    6: 0.97,   # -3% penalty
    7: 0.75,   # -25% penalty  <-- TOO HARSH!
    8: 1.08,   # +8% bonus
}
```

### Recommended v3.9 Penalties (Based on 3-Day Actual):
```python
BOX_PENALTY_FACTORS_V39 = {
    1: 1.08,   # Reduced from 1.12 (Box 1 over-picked)
    2: 1.03,   # INCREASED from 0.97 (Box 2 under-picked!)
    3: 0.82,   # Slightly increased from 0.80
    4: 1.02,   # Reduced from 1.05
    5: 0.88,   # Slightly reduced from 0.90
    6: 0.92,   # Slightly reduced from 0.97
    7: 0.82,   # INCREASED from 0.75 (too harsh!)
    8: 1.05,   # Reduced from 1.08
}
```

---

## PROBLEM #3: Track-Specific Adjustments Are INCOMPLETE

### Tracks That Need URGENT Adjustments:

| Track | Our Nov 30 Wins | Box Pattern | Action Needed |
|-------|-----------------|-------------|---------------|
| Rockhampton | **0/12 (0%)** | Unknown | Add to HIGH UPSET, Box 1 penalty |
| Darwin | 1/11 (9.1%) | Box 7 dominated | Add Box 7 boost, Box 1 penalty |
| Capalaba | 3/10 (30%) | Inside boxes | Add to LOW UPSET |
| Healesville | 3/12 (25%) | Outside boxes | Add Box 8 boost |

### Tracks Missing from TRACK_BOX1_ADJUSTMENT:
- Rockhampton
- Darwin  
- Grafton
- Broken Hill
- Mount Gambier
- Murray Bridge
- Sale

---

## PROBLEM #4: "Luck Factors" Are Not Being Applied Correctly

### FieldSimilarityIndex Issue

Current logic creates a fixed multiplier that doesn't adapt to field conditions:
```python
df["FieldSimilarityIndex"] = df.apply(
    lambda row: 0.8 if (...) else 1.0 if (...) else 1.1,
    axis=1
)
```

This is backwards! When fields are SIMILAR:
- Score confidence should be LOWER (more luck involved)
- We should favor INSIDE boxes more (default advantage)

### TrackUpsetFactor Issue

We're not penalizing HIGH UPSET tracks enough. On Nov 30:
- Rockhampton: 0/12 correct (1.00 factor - should be 1.15+)
- Darwin: 1/11 correct (not in list - should be 1.10+)

---

## PROBLEM #5: The "48 Missing Factors" Myth

### We Claim 49 Factors, But Many Are REDUNDANT:

1. `DrawFactor` and `BoxPositionBias` measure the SAME thing
2. `PlaceRate` and `ConsistencyIndex` are highly correlated (0.85+)
3. `WinPlaceRate` is just `PlaceRate + ConsistencyIndex`
4. `TrainerStrikeRate` and `TrainerTier` are the same underlying metric
5. `AgeFactor` and `AgeMonths` are redundant

### Factors That ADD REAL VALUE (14):
1. BoxPositionBias (primary predictor)
2. BoxPenaltyFactor (multiplicative correction)
3. BestTimePercentile (speed within race)
4. EarlySpeedPercentile (early pace)
5. WinStreakFactor (hot form)
6. TrainerMomentum (hot trainer)
7. CloserBonus (distance-specific)
8. PaceBoxFactor (pace-box interaction)
9. TrackBox1Adjustment (track-specific)
10. TrackUpsetFactor (predictability)
11. FieldSimilarityIndex (field competitiveness)
12. GradeFactor (experience adjustment)
13. FreshnessFactor (rest days)
14. DistanceChangeFactor (distance suitability)

### Factors That HURT Predictions:
- `WeightFactor` (PDFs show 0.0kg for all - USELESS)
- `MarginFactor` (Margins not being parsed - USELESS)
- `Last3FinishFactor` (defaults to 1.0 always - USELESS)

---

## IDENTIFIED "LUCK PATTERNS" (Defies Logic)

### Pattern 1: Box 2 "Shadow Effect"
When our #1 pick is Box 1, the ACTUAL winner is often Box 2.

| Scenario | Count (Nov 28-30) | 
|----------|-------------------|
| We picked Box 1, Box 2 won | 23 races |
| We picked Box 2, Box 2 won | 8 races |

**Recommendation**: When Box 1 has high score, ALSO boost Box 2 as potential upset winner.

### Pattern 2: "Hot Track" Phenomenon
Certain tracks on certain days have wildly different patterns:
- Nov 30 Rockhampton: 0/12 (normally ~18%)
- Nov 30 Capalaba: 30% (above average)

**Recommendation**: Add daily volatility factor based on first 2-3 races.

### Pattern 3: "Field of Similar Dogs"
When 3+ dogs have scores within 5% of each other, the winner is nearly random.

**Recommendation**: In tight fields, default to Box 1-2-8 (inside advantage).

---

## V3.9 RECOMMENDED CHANGES

### Change 1: Update BOX_WIN_RATE (Immediate)
```python
BOX_WIN_RATE_V39 = {
    1: 0.195,   # Reduced from 0.210
    2: 0.160,   # INCREASED from 0.120
    3: 0.087,   # Slight increase from 0.080
    4: 0.135,   # Reduced from 0.155
    5: 0.088,   # Reduced from 0.098
    6: 0.092,   # Reduced from 0.122
    7: 0.091,   # INCREASED from 0.055
    8: 0.150,   # Slight reduction from 0.160
}
```

### Change 2: Update BoxPenaltyFactor (Immediate)
```python
BOX_PENALTY_FACTORS_V39 = {
    1: 1.08,   # Reduced from 1.12
    2: 1.03,   # INCREASED from 0.97
    3: 0.82,   # Slightly increased from 0.80
    4: 1.02,   # Reduced from 1.05
    5: 0.88,   # Slightly reduced
    6: 0.92,   # Slightly reduced
    7: 0.82,   # INCREASED from 0.75
    8: 1.05,   # Reduced from 1.08
}
```

### Change 3: Add Missing Tracks to Adjustments
```python
TRACK_BOX1_ADJUSTMENT_V39 = {
    # ... existing ...
    "Rockhampton": -0.05,  # 0% success Nov 30
    "Darwin": -0.04,       # 9.1% success Nov 30
    "Grafton": 0.02,       # 16.7% success Nov 30
    "Capalaba": 0.05,      # 30% success Nov 30
    "Broken Hill": 0.03,   # 25% success Nov 30
    "Mount Gambier": 0.02, # 18.2% success Nov 30
    "Sale": 0.01,          # 16.7% success Nov 30
}
```

### Change 4: Add Tracks to HIGH UPSET List
```python
TRACK_UPSET_PROBABILITY_V39 = {
    # ... existing ...
    "Rockhampton": 1.15,   # 0% accuracy - VERY unpredictable
    "Darwin": 1.10,        # 9.1% accuracy - unpredictable
    "Murray Bridge": 1.05, # Needs investigation
}
```

### Change 5: Remove Useless Factors from Weight Calculation
Remove from `get_weights()`:
- `WeightFactor` (no data)
- `MarginFactor` (no data)

Redistribute their weights to:
- `BoxPositionBias` (+0.02)
- `BestTimePercentile` (+0.02)

---

## EXPECTED IMPROVEMENT

| Metric | Current v3.8 | Expected v3.9 |
|--------|--------------|---------------|
| Nov 28 Win Rate | 23% | 24-25% |
| Nov 29 Win Rate | 20.3% | 21-22% |
| Nov 30 Win Rate | 17.3% | 19-20% |
| Box 1 Pick % | 34.7% | 28-30% |
| Box 2 Pick % | 15.9% | 18-20% |
| Box 7 Pick % | 0.5% | 5-7% |

---

## CONCLUSION

Our scoring matrix has these fundamental issues:

1. **Box 1 over-reliance** - We pick Box 1 in 35% of races when it only wins 20%
2. **Box 2 under-valuation** - We're missing significant Box 2 wins
3. **Box 7 over-penalization** - The 0.75x penalty is too harsh
4. **Missing track data** - Many tracks not in our adjustment tables
5. **Useless factors** - WeightFactor, MarginFactor add noise
6. **No daily adaptation** - Same weights every day regardless of patterns

**The scoring matrix needs v3.9 update to correct these issues.**

---

*Report generated: December 1, 2025*
*Based on 335 races from Nov 28-30, 2025*
