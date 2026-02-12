# Quick Reference: Individual RF/GB/XGB Scores

## What You Get

**3 New Columns in Every Prediction:**
- **RF_Score** - RandomForest prediction
- **GB_Score** - GradientBoosting prediction
- **XGB_Score** - XGBoost prediction

## Example
```
Dog: Paw Ezra
ML_Confidence: 15.0%
  ├─ RF_Score:  14.6%
  ├─ GB_Score:  15.2%
  └─ XGB_Score: 15.3%
```

## Quick Interpretation

### ✅ Good Prediction (Tight Agreement)
```
15.0% (RF=14.6, GB=15.2, XGB=15.3)
Range: 0.7%
```
**Meaning:** All algorithms agree → High confidence

### ⚠️ Moderate Prediction (Some Disagreement)
```
14.6% (RF=14.6, GB=15.2, XGB=13.9)
Range: 1.3%
```
**Meaning:** Slight disagreement → Medium confidence

### ❌ Risky Prediction (Strong Disagreement)
```
6.5% (RF=14.6, GB=3.8, XGB=1.2)
Range: 13.4%
```
**Meaning:** Algorithms clash → Low confidence, AVOID

## Why This Matters

1. **Verify ML Worked** - Different scores = ML actually ran
2. **Track Patterns** - See which algorithm works best per track
3. **Assess Confidence** - Agreement = reliability
4. **Understand Scoring** - See how ML_Confidence is calculated

## Column Order in Excel
```
Track → RaceNumber → Box → DogName → ML_Confidence → RF_Score → GB_Score → XGB_Score → ...
```

## No Action Required

Run predictions as normal:
```bash
python run_track_ensemble_predictions.py
```

Output automatically includes all 3 scores!

## Full Documentation

See **[INDIVIDUAL_SCORES_GUIDE.md](INDIVIDUAL_SCORES_GUIDE.md)** for complete details.
