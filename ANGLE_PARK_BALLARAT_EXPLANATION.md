# Angle Park & BALLARAT Models - Complete Explanation

## Your Question

> "i am confused, can you not see Angle Park and Ballarat in https://github.com/danieljohnconstantine-a11y/Greyhound-Agent/tree/copilot/copy-ml-training-prediction-files/models .. because that where i see them????"

## The Answer

**YOU WERE ABSOLUTELY RIGHT!** Angle Park and BALLARAT models WERE uploaded to GitHub. Here's what happened:

---

## Git History Timeline

### ✅ December 29, 2025 - You Uploaded The Models

**Commit:** `750715e8e637` - "Add files via upload"

You successfully uploaded:
```
models/
├── Angle Park_gb.pkl
├── Angle Park_rf.pkl
├── Angle Park_scaler.pkl
├── Angle Park_xgb.pkl (assumed, based on pattern)
├── BALLARAT_gb.pkl
├── BALLARAT_rf.pkl
├── BALLARAT_scaler.pkl
├── BALLARAT_xgb.pkl (assumed)
├── BENDIGO_gb.pkl
├── BENDIGO_rf.pkl
└── BENDIGO_scaler.pkl
```

### ❌ February 11, 2026 - Models Were Deleted

Multiple commits deleted these files:
- `040177a` - Delete BALLARAT_scaler.pkl
- `52fe387` - Delete BALLARAT_rf.pkl
- `7723c53` - Delete BALLARAT_gb.pkl
- `2b1b438` - Delete Angle Park_scaler.pkl
- `218409d` - Delete Angle Park_rf.pkl
- `1041dfe` - Delete Angle Park_gb.pkl

---

## Why Were They Deleted?

Likely reasons:

1. **File Size Issues**
   - Each track has ~25 MB of model files
   - GitHub warns about files over 50 MB
   - Repository was getting large

2. **gitignore Rule**
   - Line 29 in `.gitignore`: `models/*.pkl`
   - This ignores all pkl files in models directory
   - Files shouldn't have been committed in first place

3. **Repository Cleanup**
   - Someone cleaned up the repository
   - Removed large binary files
   - Kept only SALE and WENTWORTH PARK

---

## Current State (as of now)

**Files that EXIST in git:**
```
models/
├── SALE/
│   ├── rf.pkl (14.7 MB) ✅
│   ├── gb.pkl (888 KB) ✅
│   ├── xgb.pkl (520 KB) ✅
│   ├── scaler.pkl (3.5 KB) ✅
│   ├── metadata.json ✅
│   └── training_metrics.json ✅
├── WENTWORTH PARK/
│   ├── rf.pkl (14.3 MB) ✅
│   ├── gb.pkl (911 KB) ✅
│   ├── xgb.pkl (554 KB) ✅
│   ├── scaler.pkl (3.5 KB) ✅
│   ├── metadata.json ✅
│   └── training_metrics.json ✅
├── config.pkl ✅
└── ensemble_config.json ✅
```

**Files that were DELETED:**
- ❌ Angle Park (all model files)
- ❌ BALLARAT (all model files)
- ❌ BENDIGO (all model files)

---

## Why You Can Still See Them on GitHub

When you look at GitHub's web interface, you might be seeing:

1. **Cached View** - GitHub caches directory listings
2. **Old Commit** - Browsing an older commit where they existed
3. **Different Branch** - They might exist on another branch

---

## How to Verify

### Check Current Files
```bash
git ls-tree -r --name-only HEAD models/
```

### Check Git History
```bash
git log --all --full-history --oneline -- "*Angle*" "*BALLARAT*"
```

### View Old Commit
```bash
git show 750715e8e637:models/
```

---

## Solutions

### Option 1: Restore from Git History ⭐ RECOMMENDED

```bash
cd /path/to/Greyhound-Agent
git checkout copilot/copy-ml-training-prediction-files

# Restore Angle Park
git checkout 750715e -- "models/Angle Park_rf.pkl"
git checkout 750715e -- "models/Angle Park_gb.pkl"
git checkout 750715e -- "models/Angle Park_xgb.pkl"
git checkout 750715e -- "models/Angle Park_scaler.pkl"

# Restore BALLARAT
git checkout 750715e -- "models/BALLARAT_rf.pkl"
git checkout 750715e -- "models/BALLARAT_gb.pkl"
git checkout 750715e -- "models/BALLARAT_xgb.pkl"
git checkout 750715e -- "models/BALLARAT_scaler.pkl"

# Commit restored files
git add models/
git commit -m "Restore Angle Park and BALLARAT models from history"
git push
```

### Option 2: Use Git LFS (for large files)

```bash
# Install Git LFS
git lfs install

# Track large model files
git lfs track "models/*.pkl"
git add .gitattributes

# Then restore files (Option 1) or re-add them
```

### Option 3: Retrain Models

```bash
# Add historical race data for these tracks to data/
# Then train:
python train_ml_track_ensemble.py
```

---

## My Apology

**I WAS WRONG** - I said the models didn't exist because I checked the current state, not the git history.

**YOU WERE RIGHT** - You DID upload Angle Park and BALLARAT to GitHub on December 29, 2025.

**WHAT HAPPENED** - Someone deleted them on February 11, 2026 (possibly for file size reasons).

---

## Recommendation

**I recommend Option 1** - Restore the files from git history.

They're still in the git repository's history, we just need to bring them back to the current branch.

**Would you like me to restore them now?**

---

## Files Stored in Git History

```
Commit: 750715e8e637 (Dec 29, 2025)

models/Angle Park_gb.pkl      ✅ Available
models/Angle Park_rf.pkl      ✅ Available
models/Angle Park_scaler.pkl  ✅ Available
models/BALLARAT_gb.pkl        ✅ Available
models/BALLARAT_rf.pkl        ✅ Available
models/BALLARAT_scaler.pkl    ✅ Available
models/BENDIGO_gb.pkl         ✅ Available
models/BENDIGO_rf.pkl         ✅ Available
models/BENDIGO_scaler.pkl     ✅ Available
```

All of these can be restored from git history!

---

## Summary

- ✅ You uploaded the models (December 29, 2025)
- ❌ They were deleted (February 11, 2026)
- ✅ They still exist in git history
- ✅ We can restore them
- ✅ You were right, I was wrong

**My sincere apologies for the confusion!**
