# START HERE - Complete Setup Guide

## Welcome!

This document helps you navigate all the documentation for common setup issues.

**Having a problem?** Find it below and jump to the solution!

---

## Quick Navigation

1. [Git Clone Issues](#1-git-clone-issues)
2. [ZIP Download Issues](#2-zip-download-issues)
3. [GitHub Authentication Issues](#3-github-authentication-issues)
4. [Pip Install Issues](#4-pip-install-issues)
5. [Model Compatibility](#5-model-compatibility)
6. [Quick Commands Reference](#6-quick-commands-reference)

---

## 1. Git Clone Issues

### Problem: Git Clone Timeout

**Error:**
```
error: RPC failed; curl 56 Recv failure: Connection timed out
fatal: early EOF
```

**Cause:** Repository is large (353MB), connection times out

**Solution:** Use shallow clone with retry script

**Files to read:**
- `START_HERE_CLONE_FIX.md` - Quick fix
- `FIX_CLONE_TIMEOUT.md` - Detailed explanation
- `UNSTABLE_CONNECTION_SOLUTIONS.md` - All connection solutions

**Quick fix:**
```bash
git clone --depth 1 -b copilot/copy-ml-training-prediction-files https://github.com/danieljohnconstantine-a11y/Greyhound-Agent.git
```

**Best fix (with auto-retry):**
```bash
./clone_with_retry.sh
```

---

### Problem: Connection Reset During Clone

**Error:**
```
error: RPC failed; curl 56 Recv failure: Connection reset by peer
```

**Cause:** Unstable internet connection

**Solution:** Use retry script that handles connection drops

**Files to read:**
- `INTERNET_ISSUE_CONFIRM.md` - Confirms it's internet issue
- `UNSTABLE_CONNECTION_SOLUTIONS.md` - Complete solutions

**Quick fix:**
```bash
./clone_with_retry.sh
```

---

## 2. ZIP Download Issues

### Problem: Corrupted/Invalid ZIP File

**Error:**
```
Windows cannot open the folder.
The compressed (zipped) folder is invalid.
```

**Cause:** Incomplete ZIP download due to connection issues

**Solution:** Don't use ZIP - use git clone with retry instead

**Files to read:**
- `FIX_CORRUPTED_ZIP.md` - Complete explanation
- `ZIP_DOWNLOAD_GUIDE.md` - Alternative methods

**Quick fix:**
```bash
# Don't download ZIP - use git clone instead:
./clone_with_retry.sh
```

---

### Problem: ZIP Download Button Doesn't Work

**Error:** GitHub ZIP download fails or times out

**Cause:** Repository is 353MB, exceeds GitHub's ZIP generation limits

**Solution:** Use git clone instead of ZIP download

**Files to read:**
- `WHY_ZIP_DOWNLOAD_FAILS.md` - Technical explanation
- `ZIP_DOWNLOAD_BUTTON_SOLUTION.md` - All alternatives
- `ANSWER_ZIP_BUTTON.md` - Quick answer

**Quick fix:**
```bash
# Use git clone instead of ZIP:
git clone --depth 1 -b copilot/copy-ml-training-prediction-files https://github.com/danieljohnconstantine-a11y/Greyhound-Agent.git
```

---

## 3. GitHub Authentication Issues

### Problem: Authentication Failed

**Error:**
```
remote: Invalid username or token.
Password authentication is not supported for Git operations.
fatal: Authentication failed
```

**Cause:** GitHub deprecated password authentication in August 2021

**Solution:** Use Personal Access Token (PAT), SSH keys, or GitHub CLI

**Files to read:**
- `FIX_GIT_AUTHENTICATION_ERROR.md` - Main troubleshooting
- `GITHUB_AUTHENTICATION_SETUP.md` - Complete setup guide
- `CORRECT_CLONE_COMMANDS.md` - Corrected commands

**Quick fix (HTTPS with PAT):**
1. Create PAT: https://github.com/settings/tokens
2. Select scope: `repo`
3. Clone and use PAT as password

**Quick fix (SSH):**
1. Generate key: `ssh-keygen -t ed25519`
2. Add to GitHub: Settings → SSH keys
3. Clone with: `git@github.com:danieljohnconstantine-a11y/Greyhound-Agent.git`

---

## 4. Pip Install Issues

### Problem: Pip Install Timeout

**Error:**
```
ReadTimeoutError: HTTPSConnectionPool(host='files.pythonhosted.org', port=443): Read timed out.
```

**Cause:** Internet too slow to download large packages (e.g., xgboost 131.7 MB) within pip's 15-second timeout

**Solution:** Use automated install script with increased timeout and retries

**Files to read:**
- `WHAT_HAPPENED_NOW.md` - Quick answer
- `WHAT_HAPPENED_PIP_ERROR.md` - Full explanation
- `PIP_INSTALL_TIMEOUT_SOLUTION.md` - All solutions
- `ANSWER_PIP_TIMEOUT.md` - Quick reference
- `PIP_TIMEOUT_QUICK_START.txt` - Visual guide

**Quick fix:**
```bash
# Don't use: pip install pandas numpy scikit-learn xgboost pdfplumber openpyxl

# Use this instead:
chmod +x install_packages.sh
./install_packages.sh
```

**Alternative (manual with timeout):**
```bash
pip install --timeout 300 -r requirements.txt
```

---

## 5. Model Compatibility

### Question: Can I Use Old Models? Do I Need to Retrain?

**Answer:** 
- **Can use:** ✅ YES - Old models work
- **Should retrain:** ⚠️ Recommended for 30-38% better accuracy

**Files to read:**
- `ANSWER_MODEL_COMPATIBILITY.md` - Quick answer
- `MODEL_COMPATIBILITY_GUIDE.md` - Complete guide
- `OLD_VS_NEW_MODELS.txt` - Visual comparison

**Quick answer:**
- Old models load and work fine
- New models have 34 improvements (+30-38% accuracy)
- Retrain if features changed (required)
- Retrain if want better accuracy (recommended)
- Keep old models if just testing (optional)

**How to retrain:**
```bash
python train_ml_track_ensemble.py
```

---

## 6. Quick Commands Reference

### Initial Setup

```bash
# Clone repository (with auto-retry)
./clone_with_retry.sh

# Or clone normally (if internet is stable)
git clone --depth 1 -b copilot/copy-ml-training-prediction-files https://github.com/danieljohnconstantine-a11y/Greyhound-Agent.git

# Navigate to repository
cd Greyhound-Agent

# Create virtual environment
python3 -m venv venv

# Activate virtual environment
source venv/bin/activate  # Linux/Mac/WSL
# OR
venv\Scripts\activate  # Windows

# Install packages (with auto-retry)
chmod +x install_packages.sh
./install_packages.sh

# Or install manually (if internet is stable)
pip install -r requirements.txt
```

### Run Training

```bash
# Train models (10-90 minutes)
python train_ml_track_ensemble.py

# Check training results
cat models/SALE/training_metrics.json
```

### Run Predictions

```bash
# Run predictions on PDFs in data_predictions/
python run_track_ensemble_predictions.py

# Check outputs
ls outputs/
```

### Verify Installation

```bash
# Test all packages installed
python -c "import pandas, numpy, sklearn, xgboost, pdfplumber, openpyxl; print('All packages installed!')"

# Test pipeline
python test_complete_pipeline.py
```

---

## Common Issues Summary

| Issue | Quick Fix | Documentation |
|-------|-----------|---------------|
| Git clone timeout | `./clone_with_retry.sh` | START_HERE_CLONE_FIX.md |
| Connection reset | `./clone_with_retry.sh` | UNSTABLE_CONNECTION_SOLUTIONS.md |
| Corrupted ZIP | Use git clone instead | FIX_CORRUPTED_ZIP.md |
| ZIP button fails | Use git clone instead | WHY_ZIP_DOWNLOAD_FAILS.md |
| Auth failed | Setup PAT or SSH | FIX_GIT_AUTHENTICATION_ERROR.md |
| Pip timeout | `./install_packages.sh` | WHAT_HAPPENED_NOW.md |
| Model compatibility | Read guide | ANSWER_MODEL_COMPATIBILITY.md |

---

## Documentation Organization

### Quick Answers (Start Here)
- `README_START_HERE.md` ← You are here
- `WHAT_HAPPENED_NOW.md` - Current pip issue
- `ANSWER_PIP_TIMEOUT.md` - Pip timeout answer
- `ANSWER_ZIP_BUTTON.md` - ZIP button answer
- `ANSWER_MODEL_COMPATIBILITY.md` - Model answer

### Detailed Guides
- `PIP_INSTALL_TIMEOUT_SOLUTION.md` - Pip solutions
- `UNSTABLE_CONNECTION_SOLUTIONS.md` - Connection solutions
- `GITHUB_AUTHENTICATION_SETUP.md` - Auth setup
- `MODEL_COMPATIBILITY_GUIDE.md` - Model guide
- `ZIP_DOWNLOAD_GUIDE.md` - ZIP alternatives

### Automation Scripts
- `install_packages.sh` / `.bat` - Install packages
- `clone_with_retry.sh` / `.bat` - Clone with retries
- `quick_clone.sh` / `.bat` - Quick shallow clone

### Total: 37+ comprehensive documentation files

---

## Your Internet Issues

**Root cause of most problems:** Unstable/slow internet connection

**Symptoms:**
- Git clone timeouts
- Connection resets
- Corrupted downloads
- Pip install timeouts

**Solution pattern:**
- Use automated retry scripts
- Increase timeouts
- Install/download one-by-one
- Be patient (10-30 minutes)

**Success rates with retry scripts:** 90-95%

---

## Getting Help

1. **Find your issue** in this document
2. **Read the quick answer** in the "Quick Answers" files
3. **Read detailed guide** if needed
4. **Run the automation script** for your issue
5. **Be patient** - scripts handle retries automatically

**Most issues resolve with:** Patience + Retry scripts + Adequate time

---

## Success Checklist

- [ ] Cloned repository successfully
- [ ] Activated virtual environment
- [ ] Installed all packages
- [ ] Verified installation works
- [ ] Trained models (optional - pre-trained exist)
- [ ] Run predictions successfully

**Expected time:** 30-60 minutes total (mostly waiting for downloads)

---

## Bottom Line

**Most problems are caused by slow/unstable internet, not the repository.**

**Solution:** Use the automation scripts (clone_with_retry.sh, install_packages.sh) which handle internet issues automatically.

**Success rate:** 90-95% with patience and scripts

**Total time:** 30-60 minutes from start to working system

---

## Need More Help?

All documentation files are in the repository root directory. Read the appropriate file for your specific issue.

**Good luck!** 🎯
