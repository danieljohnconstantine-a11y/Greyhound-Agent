# November 28, 2025 Analysis Report

## Executive Summary

**Total Races Analyzed:** 135 across 12 tracks

### Overall Box Position Results

| Box | Wins | Win Rate | vs Historical | Status |
|-----|------|----------|---------------|--------|
| 1 | 28 | 20.7% | +2.6% | ⬆️ Dominant |
| 2 | 17 | 12.6% | -2.7% | ⬇️ Underperformed |
| 3 | 13 | 9.6% | +1.6% | Near average |
| 4 | 19 | 14.1% | +1.4% | ⬆️ Above average |
| 5 | 12 | 8.9% | -0.9% | Below average |
| 6 | 11 | 8.1% | -3.8% | ⬇️ Underperformed |
| 7 | 16 | 11.9% | +2.3% | Above average |
| 8 | 19 | 14.1% | -0.1% | On track |

### Key Findings

1. **Box 1 Continues to Dominate**: 20.7% win rate (vs 18.1% historical average)
2. **Box 4 Overperformed**: 14.1% win rate (vs 12.7% historical) - worth watching
3. **Box 6 Significantly Underperformed**: Only 8.1% (vs 11.9% historical)

---

## Track-Specific Box 1 Performance

| Track | Box 1 Wins | Total Races | Win Rate | Action |
|-------|------------|-------------|----------|--------|
| Goulburn | 5 | 12 | **41.7%** 🔥 | Strong Box 1 boost applied |
| Bendigo | 4 | 12 | **33.3%** 🔥 | Strong Box 1 boost applied |
| Gawler | 3 | 9 | **33.3%** 🔥 | Strong Box 1 boost applied |
| Ladbrokes Gardens | 3 | 11 | 27.3% | Moderate boost |
| Wagga | 3 | 11 | 27.3% | Moderate boost |
| Warragul | 3 | 12 | 25.0% | Moderate boost |
| Bet Nation Townsville | 2 | 11 | 18.2% | Near average |
| Lakeside | 2 | 12 | 16.7% | Near average |
| Meadows | 2 | 12 | 16.7% | Near average |
| Mandurah | 1 | 11 | 9.1% | Penalty applied |
| Healesville | 0 | 12 | 0.0% ⚠️ | Strong penalty applied |
| Richmond | 0 | 10 | 0.0% ⚠️ | Penalty applied |

---

## Scoring Matrix Updates Applied

### Track-Specific Box 1 Adjustments (NEW)

```python
TRACK_BOX1_ADJUSTMENT = {
    # Strong Box 1 tracks (>30% win rate)
    "Goulburn": +0.08,    # 41.7% Box 1 wins
    "Angle Park": +0.08,  # 50% Box 1 wins (Nov 27)
    "Meadows": +0.06,     # 42% Box 1 wins (Nov 27)
    "Bendigo": +0.05,     # 33% Box 1 wins
    "Gawler": +0.05,      # 33% Box 1 wins
    
    # Weak Box 1 tracks (<15% win rate)
    "Healesville": -0.03, # 0% Box 1 (Nov 28)
    "Richmond": -0.02,    # 0% Box 1 (Nov 28)
    "Mandurah": -0.02,    # 9% Box 1 wins
}
```

### Track Upset Probability Updates

- **Healesville**: Moved from Low (0.90) → High (1.02)
- **Richmond**: Moved from Medium (0.95) → High (1.02)
- **Bendigo**: Moved from Medium (0.95) → Low (0.88)
- **Goulburn**: Added as Low upset (0.85)

---

## Ideas to Improve Success Rate

### 1. Track-Specific Scoring Matrices ✅ IMPLEMENTED

Different tracks favor different boxes. Applied track-specific Box 1 adjustments:
- Goulburn, Bendigo, Gawler: +5-8% Box 1 bonus
- Healesville, Richmond: -2-3% Box 1 penalty

### 2. Day-of-Week Analysis (TO BE IMPLEMENTED)

Track if Box 1 performance varies by weekday vs weekend.

### 3. Race Grade/Class Analysis (TO BE IMPLEMENTED)

Higher grade races may have different box bias patterns due to faster/more experienced dogs.

### 4. Field Size Factor (TO BE IMPLEMENTED)

- 5-6 dog fields: Inside boxes may have even stronger advantage
- Full 8 dog fields: More competitive, Box 8 rail advantage matters more

### 5. "Lock of the Day" Enhancement

Current criteria for TIER0 picks:
- Score ≥ 50
- Margin ≥ 15%
- Box 1 or 8 only
- 30+ career starts
- **NEW**: Track must be in LOW upset category

### 6. Confidence Score Threshold

Only bet when prediction confidence > 60% based on:
- Field similarity (lower = better)
- Track predictability (lower upset = better)
- Competitor density (lower = better)

---

## Cumulative Data Update

Added November 28 results to training data:
- Total races in dataset: 530+ (Nov 26-28)
- Box position statistics updated
- Track-specific biases refined

---

## Expected Impact

| Metric | Before | After Improvements |
|--------|--------|-------------------|
| Overall Win Rate | ~18% | ~20-22% |
| TIER0 (Lock) Win Rate | ~37% | ~42% |
| Track-adjusted accuracy | N/A | +5-8% for strong Box 1 tracks |

---

*Report generated: November 28, 2025*
*Data source: 12 tracks, 135 races*
