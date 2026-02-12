# Ubuntu Virtual Environment Guide
## Download, Clone, and Train ML Models with Virtual Environment

This guide shows you how to download the repository and run ML training in Ubuntu using a Python virtual environment. **Virtual environments help manage large files efficiently and keep your system clean.**

---

## 🎯 What You'll Do

1. Install prerequisites
2. Clone the repository
3. Create a virtual environment
4. Install dependencies
5. Run ML training

**Time:** 10-15 minutes  
**Skill Level:** Beginner-friendly

---

## ✨ Why Virtual Environment?

✅ **Isolated:** Doesn't mess with your system Python  
✅ **Memory-efficient:** Better handling of large files (353 MB repo)  
✅ **Clean:** Easy to delete and recreate  
✅ **Safe:** No conflicts with other projects  
✅ **Reproducible:** Same environment every time  

---

## 📋 Prerequisites

- Ubuntu 20.04 or newer (or WSL on Windows)
- Internet connection
- 500 MB free disk space
- 4 GB RAM minimum

---

## 🚀 Step 1: Install Prerequisites

Open Terminal and run:

```bash
sudo apt update
sudo apt install -y git python3 python3-pip python3-venv
```

**What this does:**
- `git` - Downloads code from GitHub
- `python3` - Python programming language
- `python3-pip` - Python package installer
- `python3-venv` - Virtual environment tool

**Verify installation:**
```bash
git --version
python3 --version
```

You should see version numbers (e.g., `git version 2.34.1`, `Python 3.10.12`).

---

## 📥 Step 2: Clone Repository

**Option A: Shallow Clone (Faster - Recommended)**
```bash
git clone --depth 1 -b copilot/copy-ml-training-prediction-files https://github.com/danieljohnconstantine-a11y/Greyhound-Agent.git
```

**Option B: Full Clone (If you need full history)**
```bash
# Increase git buffer first
git config --global http.postBuffer 524288000

# Then clone
git clone -b copilot/copy-ml-training-prediction-files https://github.com/danieljohnconstantine-a11y/Greyhound-Agent.git
```

**What happens:**
- Downloads ~200 MB (shallow) or ~353 MB (full)
- Takes 2-5 minutes depending on connection
- Creates `Greyhound-Agent` folder

**Navigate to folder:**
```bash
cd Greyhound-Agent
```

**Verify download:**
```bash
ls -la
```

You should see: `data/`, `models/`, `src/`, `README.md`, etc.

---

## 🔧 Step 3: Create Virtual Environment

Inside the `Greyhound-Agent` folder, run:

```bash
python3 -m venv venv
```

**What this does:**
- Creates a folder called `venv`
- Contains isolated Python environment
- About 20-30 MB in size

**Verify creation:**
```bash
ls -la venv/
```

You should see: `bin/`, `lib/`, `include/`, `pyvenv.cfg`

---

## 🎨 Step 4: Activate Virtual Environment

```bash
source venv/bin/activate
```

**How to know it worked:**
- Your prompt changes to show `(venv)` at the beginning
- Example: `(venv) user@computer:~/Greyhound-Agent$`

**Check you're using venv Python:**
```bash
which python
```

Should show: `/path/to/Greyhound-Agent/venv/bin/python` (NOT `/usr/bin/python3`)

---

## 📦 Step 5: Install Dependencies

With virtual environment activated:

```bash
# Upgrade pip first
pip install --upgrade pip

# Install all required packages
pip install pandas numpy scikit-learn xgboost pdfplumber openpyxl
```

**What this installs:**
- `pandas` - Data manipulation
- `numpy` - Numerical computing
- `scikit-learn` - Machine learning (RF, GB algorithms)
- `xgboost` - XGBoost algorithm
- `pdfplumber` - PDF text extraction
- `openpyxl` - Excel file handling

**Time:** 2-3 minutes

**Verify installation:**
```bash
pip list
```

You should see all the packages listed.

**Test imports:**
```bash
python -c "import pandas, numpy, sklearn, xgboost; print('All packages OK!')"
```

---

## 🏋️ Step 6: Run ML Training

Now you're ready to train the models!

```bash
python train_ml_track_ensemble.py
```

**What happens:**
1. **Loading data** (~30 seconds)
   - Reads 700+ race PDF files
   - Parses CSV results
   - Creates training dataset

2. **Training models** (~2-5 minutes)
   - Trains for 2 tracks (SALE, WENTWORTH PARK)
   - 3 algorithms per track (RF, GB, XGB)
   - Calibrates probabilities
   - Evaluates performance

3. **Saving models** (~10 seconds)
   - Saves 6 files per track (12 total)
   - RF models ~14 MB each
   - GB models ~900 KB each
   - XGB models ~550 KB each
   - Plus scalers and metadata

**Progress indicators:**
```
Loading historical data...
Processing 700+ race PDFs...
Training SALE track models...
  - Random Forest: 95.2% accuracy
  - Gradient Boosting: 94.8% accuracy  
  - XGBoost: 95.5% accuracy
Training WENTWORTH PARK models...
  - Random Forest: 93.7% accuracy
  - Gradient Boosting: 94.1% accuracy
  - XGBoost: 94.9% accuracy
Saving models...
Training complete!
```

**Success indicators:**
- ✅ No errors
- ✅ Models saved to `models/SALE/` and `models/WENTWORTH PARK/`
- ✅ Logs saved to `logs/train_track_ensemble.log`

---

## 🎯 Step 7: Run Predictions (Optional)

After training, you can run predictions:

```bash
python run_track_ensemble_predictions.py
```

**What it does:**
- Reads PDF files from `data_predictions/` folder
- Applies trained models
- Generates predictions with confidence scores
- Saves results to Excel files

**Output files:**
- `outputs/track_ensemble_predictions.xlsx`
- `outputs/track_ensemble_summary.txt`

---

## 🔄 Daily Usage

**Each time you want to work with the project:**

1. **Activate virtual environment:**
   ```bash
   cd Greyhound-Agent
   source venv/bin/activate
   ```

2. **Run your script:**
   ```bash
   python train_ml_track_ensemble.py
   # or
   python run_track_ensemble_predictions.py
   ```

3. **Deactivate when done:**
   ```bash
   deactivate
   ```

---

## 🧹 Maintenance

### Update Dependencies
```bash
source venv/bin/activate
pip install --upgrade pandas numpy scikit-learn xgboost pdfplumber openpyxl
```

### Recreate Virtual Environment
```bash
# Deactivate if active
deactivate

# Delete old venv
rm -rf venv

# Create new one
python3 -m venv venv
source venv/bin/activate
pip install pandas numpy scikit-learn xgboost pdfplumber openpyxl
```

### Clean Up Old Files
```bash
# Remove old model files
rm -rf models/SALE/* models/WENTWORTH\ PARK/*

# Remove old logs
rm -rf logs/*.log

# Retrain
python train_ml_track_ensemble.py
```

---

## ⚠️ Troubleshooting

### Issue 1: venv creation fails
**Error:** `Command 'python3 -m venv' failed`

**Solution:**
```bash
sudo apt install -y python3-venv
python3 -m venv venv
```

### Issue 2: pip not found in venv
**Error:** `pip: command not found`

**Solution:**
```bash
python -m pip install --upgrade pip
```

### Issue 3: Permission denied
**Error:** `Permission denied`

**Solution:**
```bash
# Don't use sudo with pip in venv!
# Just activate venv first:
source venv/bin/activate
pip install package_name
```

### Issue 4: Module not found during training
**Error:** `ModuleNotFoundError: No module named 'pandas'`

**Solution:**
```bash
# Make sure venv is activated
source venv/bin/activate

# Reinstall dependencies
pip install pandas numpy scikit-learn xgboost pdfplumber openpyxl
```

### Issue 5: Out of memory during training
**Error:** `MemoryError` or system freezes

**Solution:**
- Close other applications
- Minimum 4 GB RAM required
- Consider using shallow clone (saves ~150 MB)
- Train one track at a time (modify script)

### Issue 6: Git clone timeout
**Error:** `Connection timed out` or `early EOF`

**Solution:**
```bash
# Use shallow clone (faster)
git clone --depth 1 -b copilot/copy-ml-training-prediction-files https://github.com/danieljohnconstantine-a11y/Greyhound-Agent.git
```

Or see: [GIT_CLONE_TIMEOUT_FIX.md](GIT_CLONE_TIMEOUT_FIX.md)

### Issue 7: Training is slow
**Normal behavior:**
- Training takes 2-5 minutes
- Loading data takes 30 seconds
- This is expected for 700+ PDFs

**If longer than 10 minutes:**
- Check CPU usage: `top`
- Check disk space: `df -h`
- Check RAM: `free -h`

### Issue 8: Can't find venv after closing terminal
**Solution:**
```bash
# Always navigate to repo first
cd /path/to/Greyhound-Agent

# Then activate
source venv/bin/activate
```

---

## 📊 What You Get

After training:

```
Greyhound-Agent/
├── venv/                      # Virtual environment (20-30 MB)
├── data/                      # Race data (159 MB)
│   ├── 700+ PDF files
│   └── 51 CSV result files
├── models/                    # Trained models (~32 MB)
│   ├── SALE/
│   │   ├── rf.pkl            # Random Forest (14 MB)
│   │   ├── gb.pkl            # Gradient Boosting (888 KB)
│   │   ├── xgb.pkl           # XGBoost (520 KB)
│   │   ├── scaler.pkl        # Feature scaler
│   │   ├── metadata.json     # Model info
│   │   └── training_metrics.json
│   └── WENTWORTH PARK/
│       └── (same 6 files)
├── logs/
│   └── train_track_ensemble.log
└── outputs/
    └── (prediction results)
```

---

## 💡 Pro Tips

1. **Always activate venv before running scripts**
   ```bash
   source venv/bin/activate
   ```

2. **Check which Python you're using**
   ```bash
   which python  # Should be in venv/bin/
   ```

3. **List installed packages**
   ```bash
   pip list
   ```

4. **Save your installed packages**
   ```bash
   pip freeze > requirements.txt
   ```

5. **Install from requirements**
   ```bash
   pip install -r requirements.txt
   ```

6. **Update all packages**
   ```bash
   pip list --outdated
   pip install --upgrade package_name
   ```

---

## 🎉 Success Checklist

After completing this guide, you should have:

- [ ] Git and Python installed
- [ ] Repository cloned (~200-353 MB)
- [ ] Virtual environment created
- [ ] Dependencies installed (6 packages)
- [ ] Training script runs successfully
- [ ] Models saved to `models/` folder
- [ ] Can activate/deactivate venv

---

## 📚 Additional Resources

- **SUPER_BASIC_UBUNTU_GUIDE.md** - Simpler version (no venv)
- **UBUNTU_TRAINING_GUIDE.md** - Training without venv
- **GIT_CLONE_TIMEOUT_FIX.md** - Fix connection timeouts
- **README.md** - Project overview

---

## ❓ Need Help?

1. Check troubleshooting section above
2. Review logs: `cat logs/train_track_ensemble.log`
3. Verify setup: `pip list` and `ls -la models/`
4. Check GitHub issues

---

**You're all set! Happy training! 🏁🐕**
