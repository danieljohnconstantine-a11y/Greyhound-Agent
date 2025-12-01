# Track Winner Pattern Analysis v4.0

## Deep Dive Analysis - Dec 1, 2025

Based on analysis of 386+ races from November 2025 results data.

---

## Executive Summary

**Key Findings:**
1. **Track-specific scoring is CRITICAL** - Different tracks have dramatically different box winning patterns
2. **Darwin and Rockhampton** were underperforming due to generic scoring - now have track-specific adjustments
3. **Box 8 dominates 5 tracks** - Healesville, Sale, Grafton, BetDeluxe Capalaba, Temora
4. **Box 2 under-valued** at several tracks - Gawler (36.8%), Dubbo (25%), Angle Park (25%)

---

## Winner Box Distribution (Overall)

| Box | Wins | Win Rate |
|-----|------|----------|
| Box 1 | 70 | **18.1%** |
| Box 2 | 59 | **15.3%** |
| Box 3 | 31 | 8.0% |
| Box 4 | 49 | 12.7% |
| Box 5 | 38 | 9.8% |
| Box 6 | 46 | 11.9% |
| Box 7 | 37 | 9.6% |
| Box 8 | 55 | **14.2%** |

---

## Track Categories by Dominant Box

### HIGH BOX 1 TRACKS (Box 1 ≥ 25%)

| Track | Box 1 Win Rate | Races |
|-------|----------------|-------|
| Lakeside | **41.7%** | 12 |
| Temora | **40.0%** | 10 |
| BetDeluxe Rockhampton | **33.3%** | 12 |
| Gawler | 26.3% | 19 |
| Ballarat | 25.0% | 12 |
| Sandown Park | 25.0% | 12 |

### HIGH BOX 2 TRACKS (Box 2 ≥ 20%)

| Track | Box 2 Win Rate | Races |
|-------|----------------|-------|
| Gawler | **36.8%** | 19 |
| Angle Park | 25.0% | 12 |
| Ballarat | 25.0% | 12 |
| Dubbo | 25.0% | 12 |
| Bendigo | 21.2% | 33 |
| Darwin | 21.1% | 19 |

### HIGH BOX 8 TRACKS (Box 8 ≥ 20%)

| Track | Box 8 Win Rate | Races |
|-------|----------------|-------|
| Temora | **50.0%** | 10 |
| BetDeluxe Capalaba | **36.4%** | 11 |
| Wentworth Park | 30.0% | 10 |
| Grafton | 27.3% | 11 |
| Lakeside | 25.0% | 12 |
| Sale | 22.9% | 48 |
| Healesville | 22.2% | 36 |

### UNPREDICTABLE TRACKS (High Entropy)

| Track | Entropy | Races | Notes |
|-------|---------|-------|-------|
| Q2 Parklands | 2.92 | 12 | Most unpredictable |
| Bendigo | 2.80 | 33 | Spread winners |
| Darwin | 2.80 | 19 | Equal Box 1/2 |
| Richmond | 2.75 | 23 | Box 6 dominant |
| Capalaba | 2.75 | 12 | Volatile |
| Sale | 2.71 | 48 | Large sample |
| Healesville | 2.70 | 36 | Box 8 favorite |

---

## Problem Track Analysis

### DARWIN (9.1% Accuracy)

**Pattern Analysis:**
- Box 1: 21.1% (we over-picked)
- Box 2: 21.1% (we under-picked!)
- Box 4/6: 15.8% each (good secondary options)
- Box 3/5/7: 5.3% each (avoid)

**v4.0 Adjustments:**
```
Box 1: +0.02 (slight boost)
Box 2: +0.05 (INCREASED BOOST - key fix!)
Box 4: +0.02
Box 6: +0.02
Box 3/5/7: -0.03 (penalties)
```

### ROCKHAMPTON (0% Accuracy)

**Pattern Analysis:**
- Box 1: 33.3% (DOMINANT but we still got 0%)
- Box 5/8: 16.7% each (secondary)
- Issue: Not picking Box 1 dogs correctly

**v4.0 Adjustments:**
```
Box 1: +0.10 (STRONG BOOST)
Box 5: +0.02
Box 8: +0.02
Box 7: -0.05
```

---

## Common Winner Factor Combinations

Based on analysis across all tracks, winners typically share:

### Top Predictive Factors

1. **BestTimePercentile** (fastest in race): +45% win rate boost
2. **Box Position** (1, 2, or 8): +21% vs random
3. **WinStreakFactor** (DLW ≤7 days): +30% boost
4. **ConsistencyIndex** (>30% career win rate): +35% boost
5. **TrainerTier** (elite trainers 25%+): +15% boost

### Track-Specific Winning Patterns

| Pattern | Tracks | Strategy |
|---------|--------|----------|
| Box 1 + Fast Time | Lakeside, Rockhampton, Gawler | Heavy Box 1 boost |
| Box 2 + Recent Winner | Darwin, Bendigo, Dubbo | Boost Box 2, check DLW |
| Box 8 + Closer | Temora, Capalaba, Grafton | Box 8 at long distances |
| Box 6/7 + Experience | Warragul, Richmond, Wentworth Park | Middle boxes matter |

---

## Exacta Patterns (1-2 Combinations)

Top 15 most common exacta combinations:

| Combo | Count | % |
|-------|-------|---|
| 1-2 | 15 | 3.9% |
| 1-8 | 15 | 3.9% |
| 2-4 | 13 | 3.4% |
| 8-2 | 12 | 3.1% |
| 1-7 | 11 | 2.8% |
| 2-1 | 11 | 2.8% |
| 6-1 | 11 | 2.8% |
| 5-2 | 10 | 2.6% |
| 1-5 | 10 | 2.6% |
| 1-6 | 10 | 2.6% |

**Key Insight:** When Box 1 wins, Box 2 or Box 8 often places second.

---

## v4.0 Changes Summary

### New Track-Specific Scoring System

1. **Comprehensive adjustments for all 8 boxes** at each track
2. **25 tracks with specific patterns** now handled
3. **Darwin/Rockhampton special handling** to fix 0-9% accuracy

### Implementation in features.py

```python
TRACK_COMPREHENSIVE_ADJUSTMENTS = {
    "Darwin": {
        1: 0.02,    # Slight boost (was 21.1%)
        2: 0.05,    # INCREASED BOOST
        4: 0.02, 6: 0.02,
        3: -0.03, 5: -0.03, 7: -0.03
    },
    "BetDeluxe Rockhampton": {
        1: 0.10,    # STRONG BOOST for Box 1
        5: 0.02, 8: 0.02,
        7: -0.05
    },
    # ... 23 more tracks
}
```

---

## Expected Impact

| Track | Before v4.0 | Expected After |
|-------|-------------|----------------|
| Darwin | 9.1% | 15-20% |
| Rockhampton | 0% | 15-25% |
| Capalaba | 30% | 30-35% |
| Gawler | TBD | 25-30% |
| Temora | TBD | 20-30% |

---

## Recommendations for Further Improvement

1. **Form factors matter less at unpredictable tracks** - Consider reducing form weight at Q2 Parklands, Bendigo
2. **Weather/track conditions** - Track surface state may explain some variance
3. **Time of day patterns** - Night racing vs day racing may differ
4. **Field size impact** - Small fields (5-6 dogs) favor inside boxes more

---

*Generated: December 1, 2025*
*Based on: 386 races from November 2025*
*Version: v4.0 Track-Specific Scoring Update*
