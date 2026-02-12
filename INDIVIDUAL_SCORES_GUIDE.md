# Individual Algorithm Scores Guide

## Overview

The track_ensemble_predictions.xlsx now includes **3 new columns** showing individual machine learning algorithm scores for each dog:

- **RF_Score** - RandomForest prediction (0-100%)
- **GB_Score** - GradientBoosting prediction (0-100%)
- **XGB_Score** - XGBoost prediction (0-100%)

These columns appear immediately after **ML_Confidence** for easy comparison.

## What These Scores Mean

### ML_Confidence (Ensemble Average)
The main prediction score - a weighted average of all three algorithms:
```
ML_Confidence = (RF_Score × weight_RF + GB_Score × weight_GB + XGB_Score × weight_XGB) / total_weight
```

### Individual Scores
Each algorithm independently predicts the probability that a dog will win:
- **RF_Score**: RandomForest's prediction
- **GB_Score**: GradientBoosting's prediction
- **XGB_Score**: XGBoost's prediction

## Example Output

### Excel Columns:
```
Track | RaceNumber | Box | DogName         | ML_Confidence | RF_Score | GB_Score | XGB_Score
SALE  | 1          | 3   | Paw Ezra        | 15.0          | 14.6     | 15.2     | 15.3
SALE  | 1          | 5   | Greyscale       | 14.6          | 14.6     | 15.2     | 13.9
SALE  | 1          | 7   | Flywheel Vixen  | 13.7          | 12.8     | 15.2     | 13.0
SALE  | 1          | 2   | Paw Elodee      | 6.5           | 14.6     | 3.8      | 1.2
```

### Console Output:
```
✅ Top pick: Box 3 - Paw Ezra (15.0% (RF=14.6, GB=15.2, XGB=15.3))
```

### Summary File:
```
SALE:
  Race 1: Box 3 - Paw Ezra (15.0% (RF=14.6, GB=15.2, XGB=15.3))
```

## Why This Is Useful

### 1. Verification of ML Processing
You can verify that machine learning was actually performed for each dog:
- If all three scores are identical (e.g., RF=14.6, GB=14.6, XGB=14.6), this suggests a potential issue
- Different scores confirm each algorithm independently analyzed the dog

### 2. Algorithm Performance Tracking
Identify which algorithms work better for specific tracks:
- **High RF, Low GB/XGB**: RandomForest sees patterns others don't
- **High GB, Low RF/XGB**: GradientBoosting dominant for this track
- **Consensus (all high)**: Strong favorite across all algorithms
- **Split decision**: Algorithms disagree - less confidence

### 3. Pattern Detection
Track patterns over time:
- Does RandomForest consistently outperform for sprint races?
- Does XGBoost excel at longer distances?
- Are there track-specific algorithm preferences?

### 4. Transparency
Full visibility into how the ensemble score is calculated:
```
Example: Paw Ezra
RF_Score: 14.6%
GB_Score: 15.2%
XGB_Score: 15.3%
Average: (14.6 + 15.2 + 15.3) / 3 = 15.0% → ML_Confidence
```

## Interpreting Score Variations

### Tight Agreement (Low Variance)
```
Paw Ezra: 15.0% (RF=14.6, GB=15.2, XGB=15.3)
Range: 0.7%
```
- All algorithms agree strongly
- High confidence prediction
- More reliable pick

### Moderate Disagreement
```
Greyscale: 14.6% (RF=14.6, GB=15.2, XGB=13.9)
Range: 1.3%
```
- Some algorithm disagreement
- Moderate confidence
- Still reasonable pick

### Strong Disagreement (High Variance)
```
Paw Elodee: 6.5% (RF=14.6, GB=3.8, XGB=1.2)
Range: 13.4%
```
- Algorithms strongly disagree
- Low confidence - AVOID
- RF sees something others don't (investigate why)
- Ensemble averaging protects against outliers

## Track-Specific Analysis

You can now analyze which algorithms perform best for each track:

### Example Analysis:
1. Export predictions to CSV/Excel
2. Group by Track
3. Compare RF/GB/XGB scores for winners vs. non-winners
4. Identify patterns:
   - "SALE track: XGBoost +2% more accurate than RF"
   - "WENTWORTH PARK: GradientBoosting dominant"
   - "Sprint races: RandomForest best"

### Sample Query (in Excel/Python):
```python
# Find races where algorithms disagreed significantly
df['score_variance'] = df[['RF_Score', 'GB_Score', 'XGB_Score']].std(axis=1)
high_variance = df[df['score_variance'] > 5.0]

# Find track-specific algorithm strength
by_track = df.groupby('Track')[['RF_Score', 'GB_Score', 'XGB_Score']].mean()
```

## Usage

### Running Predictions:
```bash
python run_track_ensemble_predictions.py
# OR
run_track_ensemble_predictions.bat
```

### Output Files:
- **track_ensemble_predictions.xlsx** - Full predictions with individual scores
- **track_ensemble_summary.txt** - Quick summary with individual scores

### Column Order:
The output prioritizes these columns first:
1. Track
2. RaceNumber
3. Box
4. DogName
5. **ML_Confidence** (ensemble average)
6. **RF_Score** (RandomForest)
7. **GB_Score** (GradientBoosting)
8. **XGB_Score** (XGBoost)
9. ... (other features)

## Technical Details

### How Scores Are Calculated:

1. **Feature Extraction**: 76+ features extracted from race form
2. **Scaling**: Features scaled using track-specific StandardScaler
3. **Individual Predictions**:
   - RandomForest: `rf_model.predict_proba(X_scaled)[:, 1]`
   - GradientBoosting: `gb_model.predict_proba(X_scaled)[:, 1]`
   - XGBoost: `xgb_model.predict_proba(X_scaled)[:, 1]`
4. **Calibration**: All models use Isotonic Regression calibration
5. **Ensemble**: Weighted average of three predictions
6. **Output**: All scores multiplied by 100 and rounded to 1 decimal

### Model Training:
Models are trained per track using `train_ml_track_ensemble.py`:
- Each track has separate RF/GB/XGB models
- Models calibrated on historical data
- Track-specific scalers ensure proper normalization

## Troubleshooting

### All Scores Identical
```
Dog: 14.6% (RF=14.6, GB=14.6, XGB=14.6)
```
**Issue**: Features aren't varying between dogs  
**Solution**: Check feature engineering - dog-specific features may be missing

### One Algorithm Very Different
```
Dog: 10.0% (RF=14.6, GB=8.5, XGB=7.0)
```
**Issue**: RandomForest seeing pattern others miss  
**Action**: Investigate why - could be valid signal or overfitting

### All Scores Near 0% or 100%
```
Dog: 0.1% (RF=0.0, GB=0.1, XGB=0.2)
```
**Issue**: Dog has very poor features or calibration issue  
**Action**: Review dog's career stats and recent form

## Summary

The individual RF/GB/XGB scores provide:

✅ **Verification** - Confirm ML processing occurred  
✅ **Transparency** - See how ensemble score is calculated  
✅ **Analysis** - Track algorithm performance by track  
✅ **Patterns** - Identify algorithm strengths/weaknesses  
✅ **Confidence** - Score agreement indicates prediction reliability  

**Use these scores to:**
- Verify predictions
- Build trust in the system
- Improve track-specific strategies
- Understand algorithm behavior
- Make more informed betting decisions

---

**Questions or Issues?**
- Check PIPELINE_TEST_REPORT.md for sample outputs
- Review train_ml_track_ensemble.py for model training details
- See run_track_ensemble_predictions.py for prediction code
