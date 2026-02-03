# Track Organization Guide - Simple Steps

## What This Does

Organizes all 49 greyhound tracks from messy flat files into clean subdirectories.

---

## Current Problem

After training, you have 196+ model files scattered in one directory:

```
models/
├── Bulli_rf.pkl
├── Bulli_gb.pkl
├── Bulli_xgb.pkl
├── Bulli_scaler.pkl
├── DARWIN_rf.pkl
├── DARWIN_gb.pkl
├── Murray_Bridge_rf.pkl
├── ... (190 more files)
```

**Problem:** Hard to find specific track models, difficult to manage 50+ tracks.

---

## Solution - Clean Organization

Each track gets its own folder with all files organized:

```
models/
├── Bulli/
│   ├── rf.pkl
│   ├── gb.pkl
│   ├── xgb.pkl
│   ├── scaler.pkl
│   ├── metadata.json
│   └── training_metrics.json
├── DARWIN/
│   ├── rf.pkl
│   ├── gb.pkl
│   ├── xgb.pkl
│   ├── scaler.pkl
│   ├── metadata.json
│   └── training_metrics.json
└── ... (47 more tracks)
```

**Benefits:**
- ✅ Easy to find specific track
- ✅ Clean separation
- ✅ Scales to 100+ tracks
- ✅ Includes performance metrics

---

## STEP 1: One-Click Organization (Windows)

### Method A: Batch File (Easiest)

1. **Download latest code** from GitHub
2. **Double-click** `ORGANIZE_ALL_TRACKS.bat`
3. **Wait 5 minutes** for organization to complete
4. **Done!** All 49 tracks now organized

### What It Does:
- Scans all model files in models/ directory
- Creates subdirectory for each track
- Moves files into correct locations
- Generates metadata and metrics
- Validates organization

### Output:
- `models/TRACK_NAME/` - 49 subdirectories created
- `outputs/pipeline_validation_report.json` - Validation results

---

## STEP 2: Verify Organization

Check the validation report:

```bash
python validate_pipeline.py
```

**Expected Result:**
```
✅ Tests Passed: 5/5 (100%)
✅ Status: PRODUCTION READY
```

---

## What If Something Goes Wrong?

### Issue: "Python not found"
**Solution:** Install Python 3.8+ from python.org

### Issue: "Script failed"
**Solution:** Check error message in console, share with support

### Issue: "Not all tracks organized"
**Solution:** Check `outputs/pipeline_validation_report.json` for details

---

## Manual Method (If Batch File Doesn't Work)

Run commands one at a time:

```bash
# Step 1: Organize models
python reorganize_models_by_track.py

# Step 2: Add metrics
python add_training_metrics.py

# Step 3: Validate
python validate_pipeline.py
```

---

## After Organization

### Regular Operations

**After training new tracks:**
```bash
python reorganize_models_by_track.py
python add_training_metrics.py
python validate_pipeline.py
```

**To make predictions:**
Models load automatically from organized subdirectories - no changes needed!

---

## Summary

**Before:** 196 flat files, hard to manage  
**After:** 49 organized subdirectories, easy to find and scale  
**Time:** 5 minutes one-time setup  
**Method:** One click - `ORGANIZE_ALL_TRACKS.bat`

---

## Questions?

- Check `outputs/pipeline_validation_report.json` for detailed status
- Run `python validate_pipeline.py` anytime to verify organization
- All scripts are automated - no manual file moving required
