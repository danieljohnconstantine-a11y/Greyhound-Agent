# Ubuntu Training Guide: Run ML Model Training

Complete step-by-step guide to download, clone, and run `train_ml_track_ensemble.py` on Ubuntu.

## ⏱️ Time Required
- **Installation:** 5-10 minutes
- **Training:** 2-5 minutes
- **Total:** 7-15 minutes

## 📋 Prerequisites

### System Requirements:
- **OS:** Ubuntu 20.04+ (or Debian-based Linux)
- **CPU:** 2+ cores recommended
- **RAM:** 4GB minimum, 8GB recommended
- **Disk:** 500MB free space
- **Internet:** Required for downloading

### Check Your System:
```bash
# Check Ubuntu version
lsb_release -a

# Check Python version (need 3.8+)
python3 --version

# Check disk space
df -h
```

---

## 🚀 Step-by-Step Guide

### Step 1: Install Git and Python

```bash
# Update package list
sudo apt update

# Install Git
sudo apt install git -y

# Install Python 3 and pip
sudo apt install python3 python3-pip -y

# Verify installations
git --version
python3 --version
pip3 --version
```

**Expected Output:**
```
git version 2.34.1
Python 3.10.12
pip 22.0.2
```

---

### Step 2: Clone the Repository

```bash
# Navigate to your preferred directory
cd ~

# Clone the repository (this branch)
git clone -b copilot/copy-ml-training-prediction-files https://github.com/danieljohnconstantine-a11y/Greyhound-Agent.git

# Navigate into the repository
cd Greyhound-Agent
```

**What happens:**
- Downloads ~353 MB
- Takes 2-5 minutes depending on connection
- Creates `Greyhound-Agent` folder

**Verify:**
```bash
# Check you're in the right place
pwd
ls -la
```

You should see files like:
- `train_ml_track_ensemble.py`
- `data/` folder
- `models/` folder
- `src/` folder

---

### Step 3: Install Python Dependencies

```bash
# Install required packages
pip3 install pandas numpy scikit-learn xgboost pdfplumber openpyxl

# OR install with specific versions for stability
pip3 install pandas==2.0.3 numpy==1.24.3 scikit-learn==1.3.0 xgboost==2.0.0 pdfplumber==0.10.2 openpyxl==3.1.2
```

**What gets installed:**
- `pandas` - Data manipulation
- `numpy` - Numerical operations
- `scikit-learn` - ML algorithms (RandomForest, GradientBoosting)
- `xgboost` - XGBoost algorithm
- `pdfplumber` - PDF parsing
- `openpyxl` - Excel file handling

**Installation time:** 2-5 minutes

**Verify installation:**
```bash
python3 -c "import pandas, numpy, sklearn, xgboost, pdfplumber, openpyxl; print('✓ All packages installed')"
```

---

### Step 4: Verify Data Files

```bash
# Check data folder exists
ls -lh data/ | head -20

# Check race results exist
ls data/results*.csv | wc -l
```

**Expected:**
- 30+ CSV result files
- 700+ PDF form files
- Total ~220 MB in data folder

---

### Step 5: Run the Training Script

```bash
# Run the training script
python3 train_ml_track_ensemble.py
```

**What happens:**

1. **Loading data** (30 seconds):
   ```
   Loading historical race data...
   Found 30 result files
   Loaded 450+ races
   ```

2. **Training models** (1-3 minutes):
   ```
   Training track: SALE
     - RandomForest: 91 samples, 76 features
     - GradientBoosting: 91 samples
     - XGBoost: 91 samples
   
   Training track: WENTWORTH PARK
     - RandomForest: 72 samples, 76 features
     - GradientBoosting: 72 samples
     - XGBoost: 72 samples
   ```

3. **Saving models** (10 seconds):
   ```
   Saved: models/SALE/rf.pkl (14.6 MB)
   Saved: models/SALE/gb.pkl (888 KB)
   Saved: models/SALE/xgb.pkl (520 KB)
   Saved: models/WENTWORTH PARK/rf.pkl (14.3 MB)
   Saved: models/WENTWORTH PARK/gb.pkl (911 KB)
   Saved: models/WENTWORTH PARK/xgb.pkl (554 KB)
   ```

4. **Summary**:
   ```
   ✓ Training complete!
   ✓ Models saved to models/ directory
   ✓ Training log: logs/train_track_ensemble.log
   ```

**Total time:** 2-5 minutes

---

## 📊 Output & Results

### Model Files Created:

```bash
# Check models were created
ls -lh models/SALE/
ls -lh models/WENTWORTH\ PARK/
```

**Expected files per track:**
- `rf.pkl` - RandomForest model (~14 MB)
- `gb.pkl` - GradientBoosting model (~900 KB)
- `xgb.pkl` - XGBoost model (~550 KB)
- `scaler.pkl` - Feature scaler (~10 KB)
- `metadata.json` - Model info
- `training_metrics.json` - Performance metrics

### Training Logs:

```bash
# View training log
cat logs/train_track_ensemble.log
```

### Success Indicators:

✅ No error messages  
✅ Models saved for each track  
✅ Log file created  
✅ Training metrics show accuracy > 60%

---

## 🔧 Troubleshooting

### Issue: "Permission denied"

**Solution:**
```bash
# Add execute permission
chmod +x train_ml_track_ensemble.py

# Or use sudo if needed
sudo python3 train_ml_track_ensemble.py
```

### Issue: "ModuleNotFoundError: No module named 'pandas'"

**Solution:**
```bash
# Reinstall dependencies
pip3 install --user pandas numpy scikit-learn xgboost pdfplumber openpyxl

# Or try with sudo
sudo pip3 install pandas numpy scikit-learn xgboost pdfplumber openpyxl
```

### Issue: "No such file or directory: 'data/results*.csv'"

**Solution:**
```bash
# Make sure you're in the correct directory
cd ~/Greyhound-Agent
pwd

# Check if data folder exists
ls -la data/
```

### Issue: Training is slow

**Normal behavior:**
- First run takes 2-5 minutes
- RandomForest models are large and take time
- Progress is logged to console

**Speed it up:**
- Close other applications
- Use a machine with more RAM
- Training cannot be significantly faster due to ML algorithms

### Issue: Out of memory

**Solution:**
```bash
# Check available memory
free -h

# If low on RAM, close other apps or use a machine with more RAM
# Minimum 4GB RAM required, 8GB recommended
```

---

## ✅ What You Get

After successful training:

1. **ML Models** - Ready to use for predictions
   - SALE track: 6 files (3 models + scaler + 2 JSON)
   - WENTWORTH PARK track: 6 files (3 models + scaler + 2 JSON)

2. **Training Metrics** - Performance data
   - Accuracy scores
   - Training time
   - Feature counts
   - Sample sizes

3. **Logs** - Complete training history
   - What was trained
   - Any warnings
   - Performance metrics

---

## 🎯 Next Steps

### 1. Make Predictions

```bash
# Run predictions on new race data
python3 run_track_ensemble_predictions.py
```

### 2. View Results

```bash
# Check prediction outputs
ls outputs/
cat outputs/track_ensemble_summary.txt
```

### 3. Retrain Models (when you have new data)

```bash
# Add new result files to data/
# Then rerun training
python3 train_ml_track_ensemble.py
```

---

## 📚 Quick Reference

### All Commands in Order:

```bash
# 1. Install prerequisites
sudo apt update
sudo apt install git python3 python3-pip -y

# 2. Clone repository
cd ~
git clone -b copilot/copy-ml-training-prediction-files https://github.com/danieljohnconstantine-a11y/Greyhound-Agent.git
cd Greyhound-Agent

# 3. Install dependencies
pip3 install pandas numpy scikit-learn xgboost pdfplumber openpyxl

# 4. Run training
python3 train_ml_track_ensemble.py

# 5. Check results
ls -lh models/SALE/
cat logs/train_track_ensemble.log
```

---

## 💡 Tips

- **Use virtual environment** (optional but recommended):
  ```bash
  python3 -m venv venv
  source venv/bin/activate
  pip install pandas numpy scikit-learn xgboost pdfplumber openpyxl
  ```

- **Update models regularly** - Retrain when you add new race data

- **Backup models** - Copy `models/` folder before retraining

- **Check logs** - Always review `logs/train_track_ensemble.log` after training

---

## ❓ Need Help?

- **Check the log:** `cat logs/train_track_ensemble.log`
- **View documentation:** [README.md](README.md)
- **Report issues:** [GitHub Issues](https://github.com/danieljohnconstantine-a11y/Greyhound-Agent/issues)

---

**Last Updated:** 2026-02-12  
**Tested On:** Ubuntu 22.04 LTS, Python 3.10

✅ **You're ready to train ML models on Ubuntu!**
