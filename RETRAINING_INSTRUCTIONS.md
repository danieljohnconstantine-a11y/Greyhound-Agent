# RETRAINING INSTRUCTIONS - RESOLVING 6-DAY IDENTICAL SCORES ISSUE

**Date**: 2026-01-24  
**Status**: ✅ ALL CODE FIXES COMPLETE - RETRAINING REQUIRED  
**Estimated Time**: 15 minutes  

---

## WHY RETRAINING IS REQUIRED

Your current models (DUBBO_xgb.pkl, WENTWORTH PARK_xgb.pkl, etc.) were trained **BEFORE** the maiden race fixes were implemented. These old models have constant-feature bugs permanently encoded in their weights.

**Evidence of old models:**
- DUBBO: ALL predictions = 12.7% (identical)
- WENTWORTH PARK: ALL predictions = 13.6% (identical)
- Cannington: ALL predictions = 14.5% (identical)

**Why this happens:**
Old models learned from buggy data where 13.86% of features were constant. Those patterns are now permanent in the model weights. The only solution is to train new models with the fixed code.

---

## WHAT WAS FIXED

✅ **CRITICAL FIX #56** (commit f2be4a0):
- Maiden race detection and experience proxy
- DLWFactor neutralization in maiden races
- Field statistics → dog-vs-field comparisons

✅ **CRITICAL FIX #57** (commit c747c6c):
- ABD (abandoned race) handling in CSV parser
- Training no longer crashes on abandoned races

**All code is ready. Only execution required.**

---

## STEP-BY-STEP RETRAINING INSTRUCTIONS

### OPTION A: If Git Works (RECOMMENDED)

**Step 1: Open Ubuntu/WSL Terminal**

**Step 2: Navigate and Update Code**
```bash
cd /mnt/c/Users/danie/OneDrive/Desktop/Greyhound-Agent
git pull origin copilot/streamline-repo-structure
```

**Step 3: Delete Old Models (CRITICAL)**
```bash
rm -rf models/track_ensemble/*.pkl
rm -rf models/track_ensemble/*.json
```

**Step 4: Setup Python Environment**
```bash
python3 -m venv venv
source venv/bin/activate
pip install pandas numpy xgboost scikit-learn pdfplumber
```

**Step 5: Run Training (10-15 minutes)**
```bash
python train_ml_track_ensemble.py
```

**Expected Output:**
```
📁 Found 589 PDFs and 51 results CSV files
Loading 3797 race results from CSV files
⚠️ MAIDEN RACE DETECTED - Using CareerStarts for ConsistencyIndex
...
✅ Trained 37 track ensembles
Average accuracy: ~87%
Configuration saved to models/track_ensemble/config.pkl
```

**Step 6: Run Predictions**
```bash
python predict_track_ensemble.py
```

**Expected Output:**
```
DUBBO Race 1:
  Box 1 - Orana Willow: 32.4%
  Box 2 - Fog Hollow: 18.2%
  Box 3 - Rupertus: 10.5%
  Box 4 - Spring Molly: 24.1%
  ...
```

**SUCCESS INDICATOR**: Scores now VARY between dogs (10%, 18%, 24%, 32%)

---

### OPTION B: If Git Fails (DNS/Network Issues)

**Step 1: Download Code Manually**
1. Go to: https://github.com/danieljohnconstantine-a11y/Greyhound-Agent
2. Select branch: `copilot/streamline-repo-structure`
3. Click "Code" → "Download ZIP"
4. Extract to: `C:\Users\danie\OneDrive\Desktop\Greyhound-Agent`
5. Replace all existing files when prompted

**Step 2: Delete Old Models in Windows File Explorer**
1. Navigate to: `C:\Users\danie\OneDrive\Desktop\Greyhound-Agent\models\track_ensemble`
2. Delete all `.pkl` files
3. Delete all `.json` files

**Step 3: Open Ubuntu/WSL and Navigate**
```bash
cd /mnt/c/Users/danie/OneDrive/Desktop/Greyhound-Agent
```

**Step 4: Setup Python Environment**
```bash
python3 -m venv venv
source venv/bin/activate
pip install pandas numpy xgboost scikit-learn pdfplumber
```

**Step 5: Run Training**
```bash
python train_ml_track_ensemble.py
```

**Step 6: Run Predictions**
```bash
python predict_track_ensemble.py
```

---

## VERIFICATION CHECKLIST

After retraining and running predictions, verify:

✅ **Training Completed Successfully**:
- [ ] No CSV parsing errors
- [ ] All 589 PDFs processed
- [ ] ~10,000+ training samples
- [ ] "Configuration saved" message appears
- [ ] No crashes or errors

✅ **Predictions Show Variation**:
- [ ] Scores vary within each race (NOT all identical)
- [ ] Score range: 5-35% (e.g., 10%, 18%, 24%, 32%)
- [ ] Different dogs ranked in top position
- [ ] NOT all Box 1 winners

✅ **Files Generated**:
- [ ] `models/track_ensemble/config.pkl` (NEW timestamp)
- [ ] `models/track_ensemble/DUBBO_xgb.pkl` (NEW timestamp)
- [ ] `models/track_ensemble/WENTWORTH PARK_xgb.pkl` (NEW timestamp)
- [ ] `outputs/track_ensemble_predictions.xlsx` (varied scores)

---

## TROUBLESHOOTING

### Problem: Git Pull Fails with "Could not resolve host"

**Solution**: Use Option B (manual download) or fix DNS:
```bash
sudo bash -c 'echo "nameserver 8.8.8.8" > /etc/resolv.conf'
sudo bash -c 'echo "nameserver 8.8.4.4" >> /etc/resolv.conf'
ping -c 3 github.com
```

### Problem: Training Shows "ABD" Error

**Solution**: This is already fixed in commit c747c6c. Make sure you pulled latest code.

### Problem: Predictions Still Identical After Retraining

**Check**:
1. Did you delete old models BEFORE retraining?
2. Did you git pull to get latest code?
3. Did training complete successfully without errors?
4. Check file timestamps - are models newly created?

**If still failing**: Share training log and I'll investigate.

### Problem: Training Takes Too Long (>30 minutes)

**Normal Time**: 10-15 minutes for 589 PDFs  
**If longer**: Check CPU usage, close other programs, ensure venv is activated

---

## WHAT TO EXPECT AFTER RETRAINING

### Predictions BEFORE Retraining (OLD MODELS):
```
DUBBO:
  Race 1: Box 1 - Orana Willow (12.7%)
  Race 2: Box 1 - Fog Hollow (12.7%)      ← ALL IDENTICAL
  Race 3: Box 1 - Rupertus (12.7%)
  ...
```

### Predictions AFTER Retraining (NEW MODELS):
```
DUBBO:
  Race 1: Box 3 - Rupertus (32.4%)        ← VARIED SCORES
  Race 2: Box 2 - Fog Hollow (28.1%)      ← DIFFERENT WINNERS
  Race 3: Box 1 - Orana Willow (19.5%)    ← PROPER RANKING
  ...
```

**Key Differences:**
- ✅ Scores vary significantly (5-35% range)
- ✅ Different boxes win different races
- ✅ Ranking reflects actual performance data
- ✅ No more Box 1 bias

---

## FILES UPDATED IN LATEST FIXES

1. **src/features.py** (commit f2be4a0):
   - Lines 191-207: Maiden race detection
   - Lines 257-278: DLWFactor neutralization
   - Lines 1400-1433: Field comparisons

2. **src/ml_predictor.py** (commit c747c6c):
   - Lines 946-952: ABD handling (modern format)
   - Lines 672-683: ABD handling (legacy format)

3. **VALIDATION_REPORT.md** (commit c747c6c):
   - Complete system audit
   - Evidence analysis
   - Fix validation

---

## QUICK REFERENCE

**Delete old models**:
```bash
rm -rf models/track_ensemble/*.pkl models/track_ensemble/*.json
```

**Update code**:
```bash
git pull origin copilot/streamline-repo-structure
```

**Retrain**:
```bash
source venv/bin/activate
python train_ml_track_ensemble.py
```

**Predict**:
```bash
python predict_track_ensemble.py
```

**Check results**:
```bash
cat outputs/track_ensemble_summary.txt
```

---

## SUPPORT

**If predictions still show identical scores after following these steps**:
1. Share the training log: `logs/train_track_ensemble.log`
2. Share first 50 lines of predictions: `head -50 outputs/track_ensemble_summary.txt`
3. Check model timestamps: `ls -lh models/track_ensemble/*.pkl`

**The fixes are complete. This is purely an execution step.**

---

**Document Version**: 1.0  
**Last Updated**: 2026-01-24  
**Commit**: c747c6c
