# 🎯 Selective Betting System - Enhanced Win Rate Strategy

## Overview

The Selective Betting System is designed to **improve win rate from ~18% to 25-32%** by only betting on races that meet strict, multi-criteria confidence thresholds.

## Key Principle

**Quality over Quantity**: Instead of betting all races, we filter to only the highest-confidence selections based on:
1. Score separation between top picks
2. Absolute score thresholds
3. Favorable box positions (1, 2, 8)

## Confidence Tiers

### 🔥 TIER1 - Premium Selections (Expected Win Rate: 28-32%)
- Score ≥ 45
- Margin ≥ 12%
- Absolute separation ≥ 5 points
- **ACTION: Always bet**

### ✅ TIER2 - Strong Selections (Expected Win Rate: 22-28%)
- Score ≥ 42
- Margin ≥ 10%
- Absolute separation ≥ 4 points
- **ACTION: Bet with confidence**

### ⚠️ TIER3 - Standard Selections (Expected Win Rate: ~18%)
- Score ≥ 35 OR Margin ≥ 7% OR Absolute ≥ 3
- **ACTION: Optional - smaller stakes**

### ❌ NO_BET - Below Threshold
- Does not meet any criteria
- **ACTION: Skip this race**

## Box Position Analysis

Based on 386+ race analysis:

| Box | Win Rate | Adjustment |
|-----|----------|------------|
| 1 | 18.1% | +10% bonus |
| 2 | 15.3% | +10% bonus |
| 8 | 14.2% | +10% bonus |
| 3 | 8.0% | -5% penalty |
| 5 | 9.8% | -5% penalty |
| 7 | 9.6% | -5% penalty |

Boxes 1, 2, and 8 combined win **47.6%** of all races (vs 37.5% expected).

## Example Output

```
🔥 Angle Park R9 | Box 2 | Jan Hewett | Score: 59.17 | TIER1
✅ SALE R4 | Box 1 | In Action | Score: 57.73 | TIER2
```

## Files

- `outputs/selective_picks.csv` - Only TIER1 and TIER2 races (recommended bets)
- `outputs/picks.csv` - All top picks (for reference)
- `outputs/todays_form_color.xlsx` - Full form with color coding

## Expected Results

| Strategy | Races Bet | Expected Win Rate |
|----------|-----------|-------------------|
| All races | 100% | ~18% |
| TIER1 only | ~15% | ~30% |
| TIER1 + TIER2 | ~25% | ~27% |

## Configuration

Edit `src/bet_worthy.py` to adjust thresholds:

```python
# TIER 1 Thresholds
TIER1_MIN_TOP_PICK_SCORE = 45.0
TIER1_MIN_SCORE_MARGIN_PERCENT = 12.0
TIER1_MIN_MARGIN_ABSOLUTE = 5.0

# TIER 2 Thresholds
TIER2_MIN_TOP_PICK_SCORE = 42.0
TIER2_MIN_SCORE_MARGIN_PERCENT = 10.0
TIER2_MIN_MARGIN_ABSOLUTE = 4.0

# Favorable Boxes
FAVORABLE_BOXES = [1, 2, 8]
FAVORABLE_BOX_BONUS = 0.10  # 10% bonus
```

## Usage

```bash
python main.py
# Check outputs/selective_picks.csv for recommended bets
```

## Key Improvements in v2.0

1. **Tiered Confidence System** - Clear categorization of races
2. **Box Position Integration** - Boxes 1, 2, 8 get bonus consideration
3. **Expected Win Rate Display** - Know your odds before betting
4. **Separate Selective Picks File** - Easy to identify recommended bets
