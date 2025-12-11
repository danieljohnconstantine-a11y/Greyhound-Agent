# Quick Start: Prediction Accuracy Analysis

## Running the Analysis

1. **Prepare actual winners data** in a text file (e.g., `actual_winners.txt`):
   ```
   Angle Park, R1, 3
   Angle Park, R2, 5
   BALLARAT, R1, 7
   ...
   ```

2. **Run the analysis**:
   ```bash
   python analyze_predictions.py actual_winners.txt
   ```

3. **View results**:
   - Console output shows the complete analysis
   - Saved to `outputs/prediction_analysis_YYYYMMDD.md`
   - Detailed comparison in `outputs/prediction_comparison_YYYYMMDD.csv`

## Example with Sample Data

```bash
python analyze_predictions.py example_winners.txt
```

This demonstrates the analysis with simulated race results (~40% accuracy).

## What You'll Get

- **Overall accuracy** percentage
- **Track-by-track** performance breakdown
- **Statistical analysis** of each scoring variable
- **Prioritized recommendations** for weight adjustments
- **Specific action items** to improve predictions

## Key Findings (from sample data)

**Best Performing Tracks:**
- MURRAY BDGE STRAIGHT: 60.0%
- BALLARAT: 57.1%
- Q LAKESIDE: 57.1%

**Top Variables to Increase:**
- RecentFormBoost (effect size: 0.360) ⭐ HIGH PRIORITY
- DLWFactor (effect size: 0.208)
- EarlySpeedIndex (effect size: 0.191)

**Variables to Decrease:**
- ConsistencyIndex (effect size: -0.278)
- FinishConsistency (effect size: -0.276)
- PrizeMoney (effect size: -0.251)

These recommendations are based on statistical analysis comparing the scoring variables of correct predictions vs incorrect predictions.
