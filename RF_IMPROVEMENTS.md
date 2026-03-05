# Random Forest (RF) Accuracy Improvements

## Overview

This document describes the improvements made to the Random Forest classifier to enhance prediction accuracy for greyhound racing.

## What Was Changed

### 1. Hyperparameter Optimizations

#### Increased Number of Trees (n_estimators)
- **Large datasets (>600 samples)**: 100 → **150 trees** (+50%)
- **Medium datasets (400-600)**: 150 → **200 trees** (+33%)
- **Small datasets (<400)**: 200 → **250 trees** (+25%)

**Why**: More trees lead to better accuracy through ensemble diversity. The model can capture more complex patterns.

#### Enhanced Tree Depth (max_depth)
- **Large datasets**: 15 → **18 levels** (+20%)
- **Medium datasets**: 18 → **20 levels** (+11%)
- **Small datasets**: 20 → **22 levels** (+10%)

**Why**: Deeper trees can model more complex interactions between features. Balanced against overfitting risk.

#### Added min_samples_leaf = 2
**New parameter** that requires at least 2 samples in each leaf node.

**Why**: Prevents overfitting by stopping the tree from creating leaves with just 1 sample. Improves generalization.

#### Added max_features = 'sqrt'
**New parameter** that samples √n features for each tree split (e.g., √76 ≈ 9 features).

**Why**: 
- Reduces correlation between trees (improves ensemble diversity)
- Proven optimal for classification tasks
- Prevents individual trees from dominating with same top features

#### Added class_weight = 'balanced'
**New parameter** that automatically adjusts weights inversely proportional to class frequencies.

**Why**: Handles the natural imbalance in greyhound racing (few winners, many non-winners). Prevents the model from just predicting "no win" all the time.

### 2. Metrics & Tracking

#### Feature Importance
- Extracts and saves top 10 most important features per track
- Helps identify which racing metrics are most predictive
- Saved in `training_metrics.json`

#### Comprehensive Metrics Recording
Now saves to `models/{TRACK}/training_metrics.json`:
```json
{
  "ensemble_performance": {
    "accuracy": 0.XX,
    "accuracy_uncalibrated": 0.XX,
    "calibration_improvement": 0.XX
  },
  "models": {
    "rf": {
      "accuracy_calibrated": 0.XX,
      "accuracy_uncalibrated": 0.XX,
      "n_estimators": 250,
      "max_depth": 22
    }
  },
  "feature_importance": [
    "Feature1: 0.0543",
    "Feature2: 0.0421",
    ...
  ]
}
```

### 3. Enhanced Reporting

During training, you'll now see:
```
✅ Ensemble accuracy: 65.3%
✅ RF accuracy: 63.1%
✅ Calibration gain: +2.2%
📝 Saved metrics to models/SALE/training_metrics.json
```

## Expected Improvements

### Conservative Estimate
- **RF accuracy alone**: +3-6% improvement
- **Ensemble with RF, GB, XGB**: +5-8% improvement

### Optimistic Estimate
- **RF accuracy alone**: +6-10% improvement
- **Ensemble with RF, GB, XGB**: +10-15% improvement

### Factors Affecting Improvement
1. **Dataset size**: Larger tracks benefit more from increased tree count
2. **Feature quality**: Better features → better predictions
3. **Class balance**: Tracks with more balanced win rates may see larger gains
4. **Existing accuracy**: Lower baseline accuracy → more room for improvement

## How to Use

### Run Full Training

```bash
# Windows
train_ml_track_ensemble.bat

# Linux/Mac
python train_ml_track_ensemble.py
```

This will:
1. Load historical data from `data/` directory
2. Train improved RF models for each track
3. Save models to `models/{TRACK}/` directories
4. Save metrics to `models/{TRACK}/training_metrics.json`

### Check Results

After training, compare the metrics:

```bash
# View SALE track metrics
cat models/SALE/training_metrics.json

# Look for:
# - "accuracy" under "ensemble_performance"
# - "accuracy_calibrated" under "models.rf"
# - "feature_importance" to see top predictive features
```

### Compare Before/After

If you saved old metrics, compare:
- **Old ensemble accuracy**: Check old `training_metrics.json`
- **New ensemble accuracy**: Check new `training_metrics.json`
- **Improvement**: New - Old

## Technical Details

### Why These Specific Hyperparameters?

#### max_features = 'sqrt'
Research shows that for classification:
- `sqrt(n)` features per split is optimal
- Reduces tree correlation (key to Random Forest success)
- Better than 'log2' or 'auto' for most datasets

#### min_samples_leaf = 2
- Prevents creating leaves with 1 sample (overfitting)
- Still allows flexibility (not too restrictive)
- Good balance for datasets of 300-1000 samples

#### class_weight = 'balanced'
- Automatically calculates: `n_samples / (n_classes * bincount(y))`
- For 20% winners: weights ≈ {0: 0.625, 1: 2.5}
- Ensures model pays attention to minority class

### Memory Considerations

The improvements add minimal memory overhead:
- More trees: Linear increase (250 vs 200 = +25% memory)
- Deeper trees: Minimal impact (already have depth limit)
- New parameters: No additional memory

Adaptive complexity still active:
- Large datasets automatically use fewer trees/depth to prevent OOM

## Validation

### Test Script

Run the test to verify improvements work:
```bash
python test_rf_improvements.py
```

This creates synthetic data and compares old vs new hyperparameters.

### Real-World Validation

The true test is on actual greyhound data:
1. Run full training with new hyperparameters
2. Compare accuracy in `training_metrics.json`
3. Generate predictions and compare to actual race results
4. Calculate win rate improvement

## Next Steps

### After This Improvement

1. **Feature Engineering**: Use feature importance to guide new feature creation
2. **Ensemble Weights**: Optimize RF vs GB vs XGB weights based on accuracy
3. **Cross-Validation**: Add k-fold CV for more robust accuracy estimates
4. **Hyperparameter Tuning**: Consider GridSearch or RandomSearch for optimal params

### Monitoring

Track these metrics over time:
- `ensemble_accuracy` - overall system performance
- `rf_accuracy` - RF-specific performance
- `calibration_improvement` - how much calibration helps
- Feature importance changes - which features matter most

## Troubleshooting

### If Accuracy Decreases

Possible causes:
1. **Overfitting**: Try reducing max_depth or increasing min_samples_leaf
2. **Data quality**: Check if recent data has more noise
3. **Class imbalance changed**: Verify class_weight='balanced' is active

### If Training is Slow

The increased n_estimators will make training ~25% slower. Options:
1. Reduce n_estimators slightly (e.g., 225 instead of 250)
2. Use fewer tracks for quick testing
3. Ensure `n_jobs=-1` to use all CPU cores

### Memory Issues

If OOM errors occur:
- Adaptive complexity should handle this automatically
- Manually reduce n_estimators in code if needed
- Train tracks separately instead of all at once

## References

- Sklearn RandomForest: https://scikit-learn.org/stable/modules/generated/sklearn.ensemble.RandomForestClassifier.html
- RF Hyperparameters: https://scikit-learn.org/stable/modules/ensemble.html#parameters
- Feature Importance: https://scikit-learn.org/stable/auto_examples/ensemble/plot_forest_importances.html

## Summary

✅ **Increased n_estimators**: More trees = better accuracy  
✅ **Increased max_depth**: Deeper trees = capture complex patterns  
✅ **Added min_samples_leaf**: Prevent overfitting  
✅ **Added max_features='sqrt'**: Optimal for classification  
✅ **Added class_weight='balanced'**: Handle winner/non-winner imbalance  
✅ **Feature importance tracking**: Identify key predictive features  
✅ **Comprehensive metrics**: Track improvements over time  

**Expected Result**: 5-15% accuracy improvement in greyhound race predictions.
