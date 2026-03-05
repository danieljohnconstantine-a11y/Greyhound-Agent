# FIX: Prediction Error - AttributeError: 'NoneType' object has no attribute 'transform'

## Your Error

```
AttributeError: 'NoneType' object has no attribute 'transform'
   X_scaled = scaler.transform(X)
               ^^^^^^^^^^^^^^^^
```

## What This Means

❌ **YOU HAVEN'T TRAINED THE MODELS YET!**

The prediction script can't find the trained models and scalers for your tracks.

---

## The Problem

### What You're Trying to Do
Run predictions for these tracks:
- BENDIGO
- DUBBO  
- The Gardens
- Mandurah
- Meadows
- Q LAKESIDE
- WENTWORTH PARK

### What Models Actually Exist
Only 2 tracks have trained models:
- SALE ✅
- WENTWORTH PARK ✅

### Missing Models
- BENDIGO ❌
- DUBBO ❌
- The Gardens ❌
- Mandurah ❌
- Meadows ❌
- Q LAKESIDE ❌

**Result:** Scaler is `None` for missing tracks → Error!

---

## The Solution

### You MUST Train Models First!

```bash
# Step 1: Navigate to repository
cd C:\Users\danie\OneDrive\Desktop\Greyhound-Agent

# Step 2: Activate virtual environment
venv\Scripts\activate

# Step 3: Run training (takes 45-90 minutes)
python train_ml_track_ensemble.py

# Step 4: Wait for training to complete
# This creates models for ALL tracks in data/ directory

# Step 5: Now run predictions
python run_track_ensemble_predictions.py
```

---

## Why This Happens

### The Prediction Workflow

```
┌─────────────────────────────────────┐
│  1. TRAIN MODELS (REQUIRED FIRST)  │
│                                     │
│  python train_ml_track_ensemble.py │
│                                     │
│  Creates:                           │
│  - models/BENDIGO/rf.pkl            │
│  - models/BENDIGO/gb.pkl            │
│  - models/BENDIGO/xgb.pkl           │
│  - models/BENDIGO/scaler.pkl  ◄─────┼─ THIS IS WHAT'S MISSING!
│  - ... (repeat for all tracks)     │
└─────────────────────────────────────┘
              ↓
┌─────────────────────────────────────┐
│  2. RUN PREDICTIONS                 │
│                                     │
│  python run_track_ensemble_predictions.py │
│                                     │
│  Loads:                             │
│  - models/BENDIGO/scaler.pkl        │
│  - Uses scaler to transform data    │
│  - Makes predictions                │
└─────────────────────────────────────┘
```

**You tried step 2 without doing step 1!**

---

## How to Check If Models Exist

### Check Models Directory

```bash
# Windows
dir models

# Linux/Mac
ls models/
```

**Should see:**
```
models/
├── BENDIGO/
│   ├── rf.pkl
│   ├── gb.pkl
│   ├── xgb.pkl
│   └── scaler.pkl
├── DUBBO/
│   ├── rf.pkl
│   ├── gb.pkl
│   ├── xgb.pkl
│   └── scaler.pkl
├── The Gardens/
│   └── ... (same files)
... (one directory per track)
```

**If directories are missing → You need to train!**

### Check Specific Track

```bash
# Windows
dir "models\BENDIGO"

# Linux/Mac
ls "models/BENDIGO/"
```

**Should see 4 files:**
- `rf.pkl` (RandomForest model)
- `gb.pkl` (GradientBoosting model)
- `xgb.pkl` (XGBoost model)
- `scaler.pkl` (Feature scaler) ← THIS ONE CAUSES YOUR ERROR

---

## The Complete Workflow

### First Time Setup

```bash
# 1. Clone repository (done)
git clone --depth 1 -b copilot/copy-ml-training-prediction-files \
  https://github.com/danieljohnconstantine-a11y/Greyhound-Agent.git

# 2. Install packages (done)
cd Greyhound-Agent
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt

# 3. TRAIN MODELS (YOU ARE HERE - DO THIS!)
python train_ml_track_ensemble.py
# Takes 45-90 minutes
# Creates models for all tracks

# 4. Run predictions
python run_track_ensemble_predictions.py
# Now works!
```

### Regular Usage

```bash
# Every time you want predictions:

# 1. Activate venv
cd C:\Users\danie\OneDrive\Desktop\Greyhound-Agent
venv\Scripts\activate

# 2. Put PDFs in data_predictions/
# (You already did this)

# 3. Run predictions
python run_track_ensemble_predictions.py

# NOTE: You only need to train once!
# Models stay on disk and can be reused.
```

---

## Training Requirements

### What Training Needs

1. **Historical data PDFs** in `data/` directory
   - Need 400-700 historical race PDFs
   - Used to train the models
   - These teach the models how to predict

2. **Time** 
   - 45-90 minutes depending on data size
   - Don't interrupt!

3. **RAM**
   - 4-8 GB recommended
   - Close other programs if needed

4. **Patience**
   - Training shows progress
   - Wait for completion
   - Creates models for all tracks

### What Training Creates

```
models/
├── config.pkl
├── ensemble_config.json
├── BENDIGO/
│   ├── rf.pkl          (15 MB)
│   ├── gb.pkl          (900 KB)
│   ├── xgb.pkl         (600 KB)
│   └── scaler.pkl      (4 KB) ◄─ FIXES YOUR ERROR
├── DUBBO/
│   └── ... (same structure)
... (one per track)
```

---

## Verification After Training

### Check Training Succeeded

```bash
# Check models were created
dir models /AD

# Should see many track directories
# Each with 4 .pkl files
```

### Test One Track

```bash
# Check specific track
dir "models\BENDIGO"

# Should see:
# rf.pkl
# gb.pkl  
# xgb.pkl
# scaler.pkl ◄─ This file is what you need!
```

### Now Try Predictions

```bash
python run_track_ensemble_predictions.py
```

**Should work now!**

---

## Common Questions

### Q: Do I have to train for every prediction?
**A:** ❌ NO! Train once, predict many times.

Models stay on disk and can be reused forever (unless you want to retrain with new data).

### Q: How long does training take?
**A:** ⏱️ 45-90 minutes (one-time investment).

### Q: How long do predictions take?
**A:** ⚡ 2-5 minutes (fast once models exist).

### Q: What if I add new historical data?
**A:** 🔄 Retrain to incorporate new data into models.

### Q: Can I train for just one track?
**A:** ❌ NO - training processes all tracks at once.

### Q: What if training fails?
**A:** See TRAINING_TROUBLESHOOTING.md

---

## The Error Explained

### Code That's Failing

```python
# Line 170 in run_track_ensemble_predictions.py
X_scaled = scaler.transform(X)
```

### What Happens

1. Script tries to load scaler: `models/BENDIGO/scaler.pkl`
2. File doesn't exist → scaler = None
3. Tries to call: `None.transform(X)`
4. Python error: NoneType has no attribute 'transform'

### The Fix

Create the scaler file by running training!

---

## Summary

### Your Error
```
AttributeError: 'NoneType' object has no attribute 'transform'
```

### Root Cause
Models not trained for your tracks.

### Solution
```bash
python train_ml_track_ensemble.py
```

### After Training
```bash
python run_track_ensemble_predictions.py  # Will work!
```

### Status
✅ Error identified
✅ Solution provided
✅ Training required before predictions

**Run training first, then predictions work!** 🎯

---

## Quick Reference

```bash
# THE FIX (what you need to do):
cd C:\Users\danie\OneDrive\Desktop\Greyhound-Agent
venv\Scripts\activate
python train_ml_track_ensemble.py    # Wait 45-90 minutes
python run_track_ensemble_predictions.py  # Now works!
```

**You can't skip training - it's required!**
