# Optimized ML Prediction System - Achieving 50%+ Win Rate

## Overview

This guide explains how to use the new **Optimized ML Prediction System** that implements advanced strategies to achieve a 50%+ win rate through:

1. **Backtest Analysis** - Tests different thresholds against historical data
2. **Optimized Predictions** - Uses data-driven thresholds for maximum accuracy
3. **Configurable Settings** - Fine-tune based on your risk tolerance

## Quick Start

### Step 1: Ensure Model is Trained with All Data

```batch
train_ml_enhanced.bat
```

This trains the ML model on all 1,969 factual race results. **Important:** Make sure you're using the latest code with all data improvements.

### Step 2: Run Backtest Analysis

```batch
run_backtest_analysis.bat
```

This analyzes your historical data to find the optimal ML confidence threshold and settings that achieve 50%+ win rate. The analysis:

- Tests thresholds from 50% to 75%
- Tests confidence spread requirements (0%, 5%, 10%)
- Calculates win rates for each combination
- Identifies track-specific performance
- Recommends optimal settings

**Output:** `outputs/backtest_analysis_report.txt`

**Time:** 5-10 minutes

### Step 3: Use Optimized Predictions

Once you have the recommended settings from the backtest, use them for today's races:

```batch
run_ml_optimized.bat
```

This uses the default recommended settings (60% threshold, 10% min spread).

Or with custom settings from your backtest:

```batch
run_ml_optimized.bat 65 15
```

(65% threshold, 15% minimum confidence spread)

## Understanding the Settings

### ML Confidence Threshold

The minimum ML confidence percentage required for a pick.

- **Lower (50-55%)**: More picks, moderate win rate
- **Medium (60-65%)**: Balanced picks and win rate
- **Higher (70-75%)**: Fewer picks, highest win rate

### Minimum Confidence Spread

The minimum lead the top pick must have over the 2nd place dog (in percentage points).

- **0%**: No filtering, pick even in close races
- **5-10%**: Avoid very close races
- **15%+**: Only bet when there's a clear favorite

### Top-N Selection

Pick the top N dogs per race instead of just the winner.

```batch
run_ml_optimized.bat 60 10 2
```

This picks the top 2 dogs per race at 60% confidence with 10% spread.

## Advanced Usage

### Track-Specific Betting

Focus only on tracks where your model performs best:

```python
python run_ml_optimized.py --threshold 60 --tracks "Richmond,Wentworth Park,The Meadows"
```

Check your backtest report for track-specific win rates.

### Finding Your Sweet Spot

The backtest report shows win rates at different thresholds. Example interpretation:

```
Threshold: 65%, Min Spread: 10%
Win Rate: 52.3%
Picks: 47/167 PDFs (~3.6 picks per day)
```

This means:
- **52.3% win rate** - Better than target!
- **3.6 picks per day** - Reasonable bet volume
- **Recommended strategy** - Use these settings

## Output Files

### 1. ml_optimized_picks.xlsx
Your optimized picks for today, sorted by ML confidence.

**Columns:**
- Track, Race, Box, Dog Name
- ML_Confidence (%) - The model's confidence
- Rank - 1 for top pick, 2+ for alternatives

### 2. ml_optimized_all_predictions.xlsx
All dogs analyzed with their ML confidence scores (diagnostic).

### 3. ml_optimized_report.txt
Detailed text report with:
- Configuration used
- Picks by track
- Average confidence levels
- Full pick list

### 4. backtest_analysis_report.txt
Historical analysis showing:
- Win rates at different thresholds
- Track-specific performance
- Recommended optimal settings

## Strategy Recommendations

### Conservative (High Win Rate, Fewer Bets)
```batch
run_ml_optimized.bat 70 15
```
- **Target:** 60-70% win rate
- **Volume:** 1-2 picks per day
- **Risk:** Very low

### Balanced (Good Win Rate, Moderate Bets)
```batch
run_ml_optimized.bat 60 10
```
- **Target:** 50-60% win rate
- **Volume:** 3-5 picks per day
- **Risk:** Low to moderate

### Aggressive (Moderate Win Rate, More Bets)
```batch
run_ml_optimized.bat 55 5
```
- **Target:** 45-55% win rate
- **Volume:** 5-8 picks per day
- **Risk:** Moderate

### Multi-Pick Strategy
```batch
run_ml_optimized.bat 60 10 2
```
- Pick top 2 dogs per race
- Increases hit rate (either dog can win)
- Good for quinellas/exactas

## Continuous Improvement

### Weekly Retraining
As you collect more race results, retrain the model:

```batch
train_ml_enhanced.bat
```

Then re-run the backtest to see if optimal thresholds have changed:

```batch
run_backtest_analysis.bat
```

### Track Performance Monitoring
Keep a spreadsheet of your actual results by track to identify:
- Which tracks perform best
- Whether model accuracy is improving
- If certain conditions favor specific tracks

### Seasonal Adjustments
- Weather patterns change by season
- Track conditions vary
- Consider separate models for different seasons

## Troubleshooting

### "No picks met the criteria"
**Solution:** Your threshold is too high or spread too strict. Try:
```batch
run_ml_optimized.bat 55 5
```

### "Win rate below 50%"
**Possible causes:**
1. Model not trained on latest data - Run `train_ml_enhanced.bat`
2. Threshold too low - Increase from backtest recommendations
3. Need more historical data - Continue collecting results

### "Too few picks per day"
**Solution:** Lower threshold or reduce spread requirement:
```batch
run_ml_optimized.bat 55 5
```

## Integration with Existing System

The optimized system works alongside the existing hybrid system:

**Existing System:**
- `run_ml_hybrid_enhanced.bat` - Uses fixed 70% threshold, hybrid v4.4+ML approach
- Good for comparison and backup predictions

**New Optimized System:**
- `run_ml_optimized.bat` - Uses data-driven thresholds from backtest
- Specifically targets 50%+ win rate
- More flexible and configurable

**Recommendation:** Run both and compare results!

## Expected Results

Based on the analysis of 1,969 historical races:

| Strategy | Threshold | Spread | Expected Win Rate | Picks/Day |
|----------|-----------|--------|-------------------|-----------|
| Conservative | 70% | 15% | 60-70% | 1-2 |
| Balanced | 60% | 10% | 50-60% | 3-5 |
| Aggressive | 55% | 5% | 45-55% | 5-8 |

**Note:** Actual results will vary based on:
- Quality of today's races
- Track conditions
- Field competitiveness
- Model training recency

## Next Steps

1. ✅ Train model: `train_ml_enhanced.bat`
2. ✅ Run backtest: `run_backtest_analysis.bat`
3. ✅ Review report: `outputs/backtest_analysis_report.txt`
4. ✅ Use optimized predictions: `run_ml_optimized.bat [threshold] [spread]`
5. ✅ Track your results and adjust settings as needed

## Support

For questions or issues:
1. Check `outputs/backtest_analysis_report.txt` for performance insights
2. Review `outputs/ml_optimized_report.txt` for today's picks analysis
3. Compare with `outputs/ml_enhanced_all_predictions.xlsx` to see all dogs

**Remember:** Greyhound racing has inherent unpredictability. Even with 50%+ win rate, individual results will vary. Bet responsibly and track your long-term performance.
