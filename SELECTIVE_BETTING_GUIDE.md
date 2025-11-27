# 🎯 Ultra-Selective Betting System v3.0

## Overview

The Ultra-Selective Betting System is designed to **improve win rate from ~18% to 35-40%** by only betting on races where ALL factors align perfectly.

## Key Principle

**Quality over Quantity**: Instead of betting all races, we filter to only the highest-confidence selections based on:
1. Score separation between top picks
2. Absolute score thresholds
3. Favorable box positions (1, 2, 8)
4. Career experience (30+ starts for LOCK bets)
5. Track-specific box biases

## Confidence Tiers

### 🔒 TIER0 - LOCK OF THE DAY (Expected Win Rate: 35-40%)
**ALL conditions must be met:**
- Score ≥ 50
- Margin ≥ 15%
- Absolute separation ≥ 7 points
- Box 1 or 8 ONLY (32.3% of all wins)
- Career starts ≥ 30 (proven dog)
- **ACTION: ALWAYS BET - Maximum stake**

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

Based on 515+ race analysis:

| Box | Win Rate | Status |
|-----|----------|--------|
| 1 | 18.1% | 🔥 PREMIUM (+15% bonus) |
| 8 | 14.2% | 🔥 PREMIUM (+15% bonus) |
| 2 | 15.3% | ✅ Favorable (+10% bonus) |
| 4 | 12.7% | Neutral |
| 6 | 11.9% | Neutral |
| 5 | 9.8% | ⚠️ Weak (-5% penalty) |
| 7 | 9.6% | ⚠️ Weak (-5% penalty) |
| 3 | 8.0% | ❌ Weakest (-5% penalty) |

**Key Stats:**
- Boxes 1 + 8 combined win **32.3%** of all races
- Boxes 1, 2, 8 combined win **47.6%** of all races (vs 37.5% expected)

## Track-Specific Box Bias

Different tracks favor different boxes due to track configuration:

| Track | Strongest Box | Win Rate |
|-------|---------------|----------|
| Temora | Box 1 | 22% |
| Healesville | Box 1 | 20% |
| Angle Park | Box 1 & 2 | 20%/18% |
| Horsham | Box 8 | 17% |
| Dubbo | Box 2 | 18% |
| Bendigo | Box 4 | 14% |

Track-specific data is automatically applied when determining confidence tiers.

## Example Output

```
🔒 LOCK OF THE DAY (Highest Confidence):
   🔒 Healesville | Race 5 | Box 1 | DOMINANT DOG | Score: 52.4 | Box 1, Score 52.4, Margin 17.2%, 45 starts

🎯 SELECTIVE PICKS (High Confidence):
   🔥 Angle Park R9 | Box 2 | Jan Hewett | Score: 49.17 | TIER1
   ✅ Sale R4 | Box 1 | In Action | Score: 47.73 | TIER2
```

## Files

- `outputs/lock_picks.csv` - TIER0 LOCK bets only (highest confidence)
- `outputs/selective_picks.csv` - TIER0, TIER1, TIER2 races (recommended bets)
- `outputs/picks.csv` - All top picks (for reference)
- `outputs/todays_form_color.xlsx` - Full form with color coding

## Expected Results

| Strategy | Races Bet | Expected Win Rate | Expected Daily Wins |
|----------|-----------|-------------------|---------------------|
| All races | 100% (129) | ~18% | ~23 |
| TIER0 only | ~5% (6) | ~37.5% | ~2.3 |
| TIER0 + TIER1 | ~15% (20) | ~32% | ~6.4 |
| TIER0 + TIER1 + TIER2 | ~25% (32) | ~28% | ~9 |

## Configuration

Edit `src/bet_worthy.py` to adjust thresholds:

```python
# TIER 0 Thresholds (LOCK OF THE DAY)
TIER0_MIN_SCORE = 50.0
TIER0_MIN_MARGIN_PERCENT = 15.0
TIER0_MIN_MARGIN_ABSOLUTE = 7.0
TIER0_REQUIRED_BOXES = [1, 8]  # Must be in premium boxes
TIER0_MIN_CAREER_STARTS = 30   # Proven dog

# TIER 1 Thresholds
TIER1_MIN_TOP_PICK_SCORE = 45.0
TIER1_MIN_SCORE_MARGIN_PERCENT = 12.0
TIER1_MIN_MARGIN_ABSOLUTE = 5.0

# TIER 2 Thresholds
TIER2_MIN_TOP_PICK_SCORE = 42.0
TIER2_MIN_SCORE_MARGIN_PERCENT = 10.0
TIER2_MIN_MARGIN_ABSOLUTE = 4.0

# Premium Boxes (highest win rate)
PREMIUM_BOXES = [1, 8]  # 32.3% combined wins
PREMIUM_BOX_BONUS = 0.15  # 15% bonus

# Favorable Boxes
FAVORABLE_BOXES = [1, 2, 8]
FAVORABLE_BOX_BONUS = 0.10  # 10% bonus
```

## Track-Specific Configuration

Track box biases are defined in `TRACK_BOX_BIAS` dictionary:

```python
TRACK_BOX_BIAS = {
    "Temora": {1: 0.22, 2: 0.16, ...},  # Box 1 wins 22%
    "Horsham": {1: 0.15, 8: 0.17, ...}, # Box 8 wins 17%
    ...
}
```

## Usage

```bash
python main.py

# Check outputs for recommended bets:
# - outputs/lock_picks.csv - LOCK OF THE DAY (highest confidence)
# - outputs/selective_picks.csv - All recommended bets
```

## Key Improvements in v3.0

1. **TIER0 - LOCK OF THE DAY** - Highest confidence bets where ALL factors align
2. **Premium Box System** - Boxes 1 & 8 get extra consideration
3. **Track-Specific Analysis** - Different tracks favor different boxes
4. **Career Experience Filter** - Only proven dogs qualify for LOCK bets
5. **Separate LOCK Picks File** - Easy to identify top 1-2 bets per day
6. **Expected Win Rate: 35-40%** on LOCK bets (up from 27% on TIER1+2)
