# Scoring Matrix Update - November 27, 2025

## Analysis Summary

After fixing PDF parsing issues (fuzzy matching + distance conversion), a comprehensive re-analysis was performed using:
- **386 race results** from `data/race_results_nov_2025.csv`
- **2,467 dogs** from 30 PDF form guides
- **90.3% timing data coverage** (up from ~63%)

## Key Changes

### 1. Box Position Bias (Updated)

Based on 386 races, the box position biases have been recalibrated:

| Box | Old Bias | New Bias | Win Rate | Change |
|-----|----------|----------|----------|--------|
| 1 | +0.075 | **+0.045** | 18.1% (70 wins) | ↓ reduced |
| 2 | +0.075 | **+0.022** | 15.3% (59 wins) | ↓ reduced |
| 3 | -0.055 | **-0.036** | 8.0% (31 wins) | ↑ less penalty |
| 4 | +0.015 | **+0.002** | 12.7% (49 wins) | ≈ similar |
| 5 | -0.020 | **-0.021** | 9.8% (38 wins) | ≈ similar |
| 6 | 0.000 | **-0.005** | 11.9% (46 wins) | ↓ slight penalty |
| 7 | 0.000 | **-0.023** | 9.6% (37 wins) | ↓ now penalized |
| 8 | +0.050 | **+0.014** | 14.2% (55 wins) | ↓ reduced |

**Key Insight**: Box 7 was previously neutral (0.000) but data shows it only wins 9.6% - now correctly penalized.

### 2. Timing Data Extraction Improvements

| Stage | Coverage | Dogs with Timing |
|-------|----------|------------------|
| Before fixes | 62.8% | 1,549 |
| After fuzzy matching | 76.6% | 1,890 |
| After distance conversion | **90.3%** | **2,228** |

**Distance conversion** added 290 additional dogs with timing data by converting race times from other distances.

### 3. Strongest/Weakest Boxes

**Favor these boxes** (pick more often):
- Box 1: 18.1% wins - STRONGEST
- Box 2: 15.3% wins
- Box 8: 14.2% wins

**Avoid these boxes** (penalize in scoring):
- Box 3: 8.0% wins - WEAKEST
- Box 7: 9.6% wins
- Box 5: 9.8% wins

## Expected Impact

With these updates:
1. More accurate box position scoring based on larger dataset
2. Better predictions for dogs racing at new distances
3. Improved handling of dogs without timing at exact race distance

## Files Changed

- `src/features.py` - Updated BOX_POSITION_BIAS values
- `src/parser.py` - Added fuzzy matching and distance conversion

## Data Sources

- Race results: `data/race_results_nov_2025.csv` (386 races)
- PDF forms: 30 form guide PDFs from Sep-Nov 2025
