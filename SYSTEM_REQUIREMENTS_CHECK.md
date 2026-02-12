# System Requirements Check

## Overview

Before downloading Greyhound-Agent (353 MB), verify your system meets these requirements.

---

## Minimum Requirements

### Software

| Requirement | Minimum | Recommended | Check Command |
|-------------|---------|-------------|---------------|
| **Python** | 3.8 | 3.9+ | `python3 --version` |
| **Git** | 2.0 | 2.30+ | `git --version` |
| **pip** | 20.0 | Latest | `pip --version` |
| **Virtual Environment** | venv | venv | `python3 -m venv --help` |

### Hardware

| Resource | Minimum | Recommended | Why |
|----------|---------|-------------|-----|
| **RAM** | 4 GB | 8+ GB | ML model training |
| **Disk Space** | 500 MB | 1+ GB | Repository + models |
| **CPU** | 2 cores | 4+ cores | Training speed |
| **Internet** | 5 Mbps | 10+ Mbps | Download speed |

### Python Packages

| Package | Version | Purpose |
|---------|---------|---------|
| **pandas** | 1.3+ | Data manipulation |
| **numpy** | 1.20+ | Numerical operations |
| **scikit-learn** | 1.0+ | ML algorithms (RF, GB) |
| **xgboost** | 1.5+ | XGBoost algorithm |
| **pdfplumber** | 0.7+ | PDF text extraction |
| **openpyxl** | 3.0+ | Excel file generation |

---

## Quick Check Commands

### Check Python Version:
```bash
python3 --version
# Output should be: Python 3.8.x or higher
```

### Check All Packages:
```bash
pip list | grep -E "pandas|numpy|scikit-learn|xgboost|pdfplumber|openpyxl"
# Should show all 6 packages
```

### Test Package Imports:
```bash
python3 -c "import pandas, numpy, sklearn, xgboost, pdfplumber, openpyxl; print('✅ All packages work')"
# Should print: ✅ All packages work
```

### Check RAM (Linux/Mac):
```bash
free -h | grep Mem
# Or
sysctl hw.memsize
```

### Check Disk Space:
```bash
df -h ~
# Should show at least 500 MB free
```

### Check Git:
```bash
git --version
# Should show: git version 2.x.x
```

### Check Virtual Environment:
```bash
python3 -m venv --help
# Should show help text (not error)
```

---

## Automated Check

**Run this script to check everything automatically:**

### Download and Run:
```bash
curl -O https://raw.githubusercontent.com/danieljohnconstantine-a11y/Greyhound-Agent/copilot/copy-ml-training-prediction-files/test_system.py
python3 test_system.py
```

### Or Run Directly (No Download):
```bash
curl -sSL https://raw.githubusercontent.com/danieljohnconstantine-a11y/Greyhound-Agent/copilot/copy-ml-training-prediction-files/test_system.py | python3
```

### What It Checks:
- ✅ Python version (3.8+)
- ✅ All 6 required packages
- ✅ Package import capability
- ✅ RAM (4+ GB)
- ✅ Disk space (500+ MB)
- ✅ Git installation
- ✅ Virtual environment support

---

## Expected Output

### If Everything Passes:
```
🔍 GREYHOUND-AGENT SYSTEM REQUIREMENTS CHECK

✅ Python 3.11.5 (Minimum: 3.8)
✅ pandas 2.1.0 installed and importable
✅ numpy 1.24.3 installed and importable
✅ scikit-learn 1.3.0 installed and importable
✅ xgboost 1.7.6 installed and importable
✅ pdfplumber 0.10.2 installed and importable
✅ openpyxl 3.1.2 installed and importable
✅ RAM: 16.0 GB (Recommended: 4+ GB)
✅ Disk: 2.5 TB free (Need: 500 MB)
✅ Git 2.39.0 installed
✅ Virtual environment supported

✅ ALL CHECKS PASSED!
🎉 Your system is ready to run Greyhound-Agent!
```

### If Something Fails:
```
❌ pandas: NOT INSTALLED
   💡 Install: pip install pandas

⚠️  Some checks failed
💡 Fix the issues above before downloading.
```

---

## What Each Requirement Is For

### Python 3.8+
- **Purpose:** Core programming language
- **Why this version:** Uses modern syntax and features
- **If missing:** Download from https://www.python.org/downloads/

### Git 2.0+
- **Purpose:** Download repository
- **Why this version:** Supports large file cloning
- **If missing:** Download from https://git-scm.com/downloads

### pandas
- **Purpose:** DataFrame operations, CSV handling
- **Used in:** Data loading, result exports
- **Install:** `pip install pandas`

### numpy
- **Purpose:** Numerical arrays, mathematical operations
- **Used in:** Feature calculations, ML inputs
- **Install:** `pip install numpy`

### scikit-learn
- **Purpose:** RandomForest, GradientBoosting algorithms
- **Used in:** ML model training and prediction
- **Install:** `pip install scikit-learn`

### xgboost
- **Purpose:** XGBoost algorithm
- **Used in:** Third ensemble algorithm
- **Install:** `pip install xgboost`

### pdfplumber
- **Purpose:** Extract text from PDF files
- **Used in:** Parse race form PDFs
- **Install:** `pip install pdfplumber`

### openpyxl
- **Purpose:** Create Excel files
- **Used in:** Export predictions to .xlsx
- **Install:** `pip install openpyxl`

### 4+ GB RAM
- **Purpose:** Load large datasets and ML models
- **Why needed:** Training requires memory for data + models
- **If less:** Training will be slower, may fail

### 500 MB Disk
- **Purpose:** Store repository (353 MB) + some workspace
- **Why needed:** Code, data, models, outputs
- **Recommended:** 1+ GB for comfortable working

---

## Installation Commands

### Install All Packages at Once:
```bash
pip install pandas numpy scikit-learn xgboost pdfplumber openpyxl
```

### Or Install One by One:
```bash
pip install pandas
pip install numpy
pip install scikit-learn
pip install xgboost
pip install pdfplumber
pip install openpyxl
```

### Ubuntu/Debian:
```bash
sudo apt update
sudo apt install python3 python3-pip python3-venv git
pip install pandas numpy scikit-learn xgboost pdfplumber openpyxl
```

---

## Troubleshooting

### "Python not found"
**Solution:** Install Python 3.8+ from https://www.python.org/downloads/

### "pip not found"
**Solution:** 
```bash
python3 -m ensurepip --upgrade
# Or
sudo apt install python3-pip
```

### "Package install fails"
**Solution:** 
```bash
pip install --upgrade pip
pip install <package_name>
```

### "Not enough RAM"
**Issue:** System has less than 4 GB  
**Impact:** Training may be slow or fail  
**Solution:** Close other applications, or upgrade RAM

### "Not enough disk space"
**Solution:** Free up space or choose different directory

### "venv not found"
**Solution:**
```bash
sudo apt install python3-venv
```

---

## After Passing All Checks

✅ **System is ready!**

**Next Steps:**
1. Download repository (see DOWNLOAD_INSTRUCTIONS.md)
2. Follow setup guide:
   - Ubuntu: UBUNTU_VENV_GUIDE.md
   - WSL: WSL_QUICK_START.md
   - Quick: SUPER_BASIC_UBUNTU_GUIDE.md
3. Run training: `python train_ml_track_ensemble.py`

---

## Support

**Still have issues?**
- Read PRE_DOWNLOAD_TEST_GUIDE.md for alternative testing methods
- Check GIT_CLONE_TIMEOUT_FIX.md for download issues
- Review troubleshooting sections in setup guides

**Need help?**
- Open GitHub issue
- Check documentation

---

## Summary

✅ **Run automated check:** `test_system.py`  
✅ **Time:** < 1 minute  
✅ **Download:** 4 KB  
✅ **Confidence:** Know before downloading  

**If all checks pass → Proceed with confidence!**
