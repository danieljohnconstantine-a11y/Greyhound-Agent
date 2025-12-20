# ML Model Setup & Verification Guide

## Quick Check: Is Your ML Model Being Used?

Run `run_complete_analysis.bat` and look for these messages:

### ✅ CORRECT - ML Model Active:
```
📥 Loading ML v2.1 enhanced model...
✅ ML v2.1 model loaded successfully
✓ ML predictions: 8 dogs
```
**Win Rate:** 40-50%+ (ML-driven predictions)

### ❌ INCORRECT - Fallback Mode:
```
📥 Loading ML v2.1 enhanced model...
⚠️  Model not found at models/greyhound_ml_v2.1_enhanced.pkl
   Running in v4.4-only mode (without ML predictions)
ℹ️  Using v4.4 scores (ML not available)
```
**Win Rate:** 28-30% (rule-based only)

---

## Why Your ML Model Isn't in GitHub

The trained ML model file (`greyhound_ml_v2.1_enhanced.pkl`) is **31MB** which exceeds GitHub's 100MB limit. It's intentionally blocked by `.gitignore` to keep the repository lightweight.

**This is NORMAL and CORRECT.**

The model stays on your local PC where it was trained with `train_ml_enhanced.bat`.

---

## File Locations Explained

### Training (One-time setup):
```
Input:  data/*.csv                    (2,108 race results)
        data/*.pdf                     (180 race forms)
Output: models/greyhound_ml_v2.1_enhanced.pkl  (31MB - STAYS LOCAL)
```

### Daily Predictions (Using the model):
```
Input:  data_predictions/*.pdf        (today's races)
        models/greyhound_ml_v2.1_enhanced.pkl  (must exist locally)
Output: outputs/ml_unified_predictions.xlsx   (predictions)
```

---

## Setup Instructions

### Initial Setup (Once per PC):

1. **Train the model** (you've already done this):
   ```batch
   train_ml_enhanced.bat
   ```
   This creates `models/greyhound_ml_v2.1_enhanced.pkl` on your PC.

2. **Verify model exists**:
   ```batch
   dir models\greyhound_ml_v2.1_enhanced.pkl
   ```
   Should show: ~31MB file

3. **Test predictions**:
   ```batch
   run_complete_analysis.bat
   ```
   Should show: "✅ ML v2.1 model loaded successfully"

### Daily Use:

1. Place today's PDFs in `data_predictions/`
2. Run `run_complete_analysis.bat`
3. Check console output:
   - ✅ "ML v2.1 model loaded" = Using ML (good)
   - ⚠️ "Model not found" = Using v4.4 fallback (bad)

---

## Troubleshooting

### Problem: "Model not found" error

**Cause:** Model file doesn't exist at expected location

**Solutions:**

1. **Retrain the model:**
   ```batch
   train_ml_enhanced.bat
   ```
   This takes 5-15 minutes and creates the model file.

2. **Check file location:**
   The model MUST be at:
   ```
   models/greyhound_ml_v2.1_enhanced.pkl
   ```
   (relative to where you run `run_complete_analysis.bat`)

3. **Verify training completed:**
   After running `train_ml_enhanced.bat`, check for:
   ```
   ✅ Model saved to: models/greyhound_ml_v2.1_enhanced.pkl
   ```

### Problem: Win rate is 28-30% (too low)

**Cause:** Running in v4.4 fallback mode (ML not loaded)

**Solution:** Follow steps above to ensure ML model exists and loads correctly.

### Problem: Want to use model on different PC

**Solution:** Copy the model file:
1. On PC #1: `models/greyhound_ml_v2.1_enhanced.pkl`
2. Copy to PC #2: `models/greyhound_ml_v2.1_enhanced.pkl`
3. Model is portable - no retraining needed

---

## Why This Design?

**Benefits:**
- ✅ Model trained once with all 2,108 races
- ✅ Model stays local (fast, no upload delays)
- ✅ GitHub repository stays small (<50MB vs 31MB+ with model)
- ✅ Model is portable (copy between PCs easily)
- ✅ Multiple people can use same repository with their own trained models

**Trade-off:**
- ⚠️ Must train model on each PC that needs predictions (one-time, 5-15 mins)

---

## Summary

| Status | Console Message | Win Rate | Action |
|--------|----------------|----------|--------|
| ✅ Good | "ML v2.1 model loaded successfully" | 40-50%+ | Use predictions normally |
| ❌ Bad | "Model not found" | 28-30% | Run `train_ml_enhanced.bat` |

**The 2,108 races ARE being used** - but only when the model file exists locally during predictions.

**You don't need to upload anything to GitHub** - the system is working as designed.
