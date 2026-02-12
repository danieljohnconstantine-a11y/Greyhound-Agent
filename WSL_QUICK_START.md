# WSL Quick Start Guide

## Answer to Your Question

**Q: "dont i need to cd /mnt/c/Users/danie/OneDrive/Desktop ... git clone ... .gi"**

**A: YES! But you have a TYPO - it should be `.git` not `.gi`**

---

## Your Command Had a Typo:

```bash
# ❌ WRONG (what you typed):
git clone -b copilot/copy-ml-training-prediction-files https://github.com/danieljohnconstantine-a11y/Greyhound-Agent.gi

# ✅ CORRECT (what you should type):
git clone -b copilot/copy-ml-training-prediction-files https://github.com/danieljohnconstantine-a11y/Greyhound-Agent.git
```

**Note the ending: `.git` NOT `.gi`**

---

## Complete Command Sequence (Copy-Paste):

### Option 1: Automated Setup (Recommended)

```bash
# 1. Navigate to Desktop
cd /mnt/c/Users/danie/OneDrive/Desktop

# 2. Remove old version (if exists)
rm -rf Greyhound-Agent

# 3. Run automated setup (clones repo + creates venv + installs deps)
curl -sSL https://raw.githubusercontent.com/danieljohnconstantine-a11y/Greyhound-Agent/copilot/copy-ml-training-prediction-files/setup_ubuntu.sh | bash

# 4. Enter directory
cd Greyhound-Agent

# 5. Activate virtual environment
source venv/bin/activate

# 6. Run training
python train_ml_track_ensemble.py
```

**Time:** 10-15 minutes  
**Result:** Trained models ready!

---

### Option 2: Manual Setup (Step-by-Step)

```bash
# 1. Navigate to Desktop
cd /mnt/c/Users/danie/OneDrive/Desktop

# 2. Remove old version (if exists)
rm -rf Greyhound-Agent

# 3. Clone repository (FIXED TYPO: .git not .gi)
git clone -b copilot/copy-ml-training-prediction-files https://github.com/danieljohnconstantine-a11y/Greyhound-Agent.git

# 4. Enter directory
cd Greyhound-Agent

# 5. Create virtual environment
python3 -m venv venv

# 6. Activate virtual environment
source venv/bin/activate

# 7. Upgrade pip
pip install --upgrade pip

# 8. Install dependencies
pip install pandas numpy scikit-learn xgboost pdfplumber openpyxl

# 9. Run training
python train_ml_track_ensemble.py
```

**Time:** 15-20 minutes  
**Result:** Trained models ready!

---

## What Each Command Does:

1. **`cd /mnt/c/Users/danie/OneDrive/Desktop`**
   - Changes to your Windows Desktop folder
   - In WSL, Windows C: drive is at `/mnt/c`

2. **`rm -rf Greyhound-Agent`**
   - Removes old version if it exists
   - `-rf` = recursive force (no confirmation)

3. **`git clone -b ... .git`**
   - Downloads the repository from GitHub
   - `-b copilot/copy-ml-training-prediction-files` = specific branch
   - Ends with `.git` (your typo was `.gi`)

4. **`cd Greyhound-Agent`**
   - Enters the downloaded folder

5. **`python3 -m venv venv`**
   - Creates isolated Python environment
   - Prevents package conflicts

6. **`source venv/bin/activate`**
   - Activates the virtual environment
   - Your prompt changes to show `(venv)`

7. **`pip install ...`**
   - Installs required Python packages
   - 6 packages total

8. **`python train_ml_track_ensemble.py`**
   - Runs the training script
   - Creates 12 model files
   - Takes 2-5 minutes

---

## Verification:

After cloning, check it worked:

```bash
cd /mnt/c/Users/danie/OneDrive/Desktop/Greyhound-Agent
ls -la
```

You should see:
- `data/` folder
- `models/` folder
- `src/` folder
- `train_ml_track_ensemble.py`
- `run_track_ensemble_predictions.py`

---

## Common Issues:

### Issue 1: Still says `.gi`
**Solution:** Make sure you copy the CORRECT command with `.git` at the end

### Issue 2: "command not found: git"
**Solution:** 
```bash
sudo apt update
sudo apt install git -y
```

### Issue 3: "command not found: python3"
**Solution:**
```bash
sudo apt install python3 python3-pip python3-venv -y
```

### Issue 4: Permission denied on /mnt/c
**Solution:** This is normal for OneDrive folders, script should still work

### Issue 5: Clone is slow
**Solution:** Repository is 353 MB, takes 2-5 minutes. Be patient!

---

## Next Steps After Training:

```bash
# View trained models
ls -lh models/SALE/
ls -lh models/WENTWORTH\ PARK/

# Run predictions on new data
python run_track_ensemble_predictions.py

# Deactivate virtual environment when done
deactivate
```

---

## Quick Reference Card:

```bash
# Navigate + Clone
cd /mnt/c/Users/danie/OneDrive/Desktop
rm -rf Greyhound-Agent
git clone -b copilot/copy-ml-training-prediction-files https://github.com/danieljohnconstantine-a11y/Greyhound-Agent.git

# Setup venv
cd Greyhound-Agent
python3 -m venv venv
source venv/bin/activate

# Install + Train
pip install pandas numpy scikit-learn xgboost pdfplumber openpyxl
python train_ml_track_ensemble.py
```

**Copy-paste these commands one by one!**

---

## Summary:

✅ **YES**, you need to `cd` to Desktop  
✅ **YES**, you need to `rm -rf` old version  
✅ **YES**, you need to `git clone`  
❌ **BUT** fix the typo: `.git` NOT `.gi`  

**Your complete workflow is now ready to copy-paste!**
