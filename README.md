# 🐕 Greyhound ML Prediction Pipeline

Complete machine learning pipeline for greyhound racing predictions with track-specific ensemble models.

---

## ⚡ RECENT IMPROVEMENT: Score Discrimination +52%

**Problem Identified:** Many dogs had identical prediction scores (81-91% clustering)  
**Solution Delivered:** XGB-weighted ensemble + within-race normalization  
**Result Proven:** +52% more score spread, +56% more variation  

📄 **[DISCRIMINATION_IMPROVEMENT_PROOF.md](DISCRIMINATION_IMPROVEMENT_PROOF.md)** - Complete proof with test results

---

## 🚨 ZIP DOWNLOAD ISSUE - READ THIS FIRST! 🚨

### ❌ The "Download ZIP" button WILL FAIL
**If you downloaded a ZIP and got "invalid file" error, read this:**

**Problem:** Repository is 353 MB with large ML model files → ZIP download corrupts  
**Solution:** Use `git clone` instead (works perfectly)

### ✅ Quick Fix - Copy & Paste This:

```bash
git clone -b copilot/copy-ml-training-prediction-files https://github.com/danieljohnconstantine-a11y/Greyhound-Agent.git
```

**Don't have Git?** Download: https://git-scm.com/downloads

**Need help?** → **[ISSUE_RESOLVED.md](ISSUE_RESOLVED.md)** ← Start here!

### 📚 Full Documentation:
- **[ISSUE_RESOLVED.md](ISSUE_RESOLVED.md)** - Problem & solution explained
- **[VISUAL_DOWNLOAD_GUIDE.md](VISUAL_DOWNLOAD_GUIDE.md)** - Step-by-step with pictures
- **[DOWNLOAD_INSTRUCTIONS.md](DOWNLOAD_INSTRUCTIONS.md)** - Complete reference
- **[ZIP_DOWNLOAD_FIX.md](ZIP_DOWNLOAD_FIX.md)** - Quick reference

### 🪟 WSL (Windows Subsystem for Linux) Users:
- **[WSL_QUICK_START.md](WSL_QUICK_START.md)** - 🎯 **WSL USERS START HERE!** Complete command sequence (fixes common typos)

### 🐧 Ubuntu Users:
- **[setup_ubuntu.sh](setup_ubuntu.sh)** - 🚀 **ONE-COMMAND SETUP!** Automated script with virtual environment
- **[UBUNTU_VENV_GUIDE.md](UBUNTU_VENV_GUIDE.md)** - ⭐ **Virtual Environment Guide** - Best for large files & training
- **[SUPER_BASIC_UBUNTU_GUIDE.md](SUPER_BASIC_UBUNTU_GUIDE.md)** - Super simple 3-step guide (no venv)
- **[UBUNTU_TRAINING_GUIDE.md](UBUNTU_TRAINING_GUIDE.md)** - Complete guide: download → clone → train models


### 🚨 CONNECTION TIMEOUT ERROR?
- **[IMMEDIATE_FIX.md](IMMEDIATE_FIX.md)** - 🆘 **GOT TIMEOUT ERROR?** Direct answers + 4 working solutions
### ⚠️ Common Issues:
- **[GIT_CLONE_TIMEOUT_FIX.md](GIT_CLONE_TIMEOUT_FIX.md)** - Fix "Connection timed out" errors (5 solutions)

### 🧪 Test Before Download:
- **[PRE_DOWNLOAD_TEST_GUIDE.md](PRE_DOWNLOAD_TEST_GUIDE.md)** - 🎯 **TEST FIRST!** 8 ways to test pipeline before downloading (4 KB vs 353 MB)
- **[test_system.py](test_system.py)** - 🔍 **SYSTEM CHECK** - Run this script to verify your system is ready (1 minute test)
- **[SYSTEM_REQUIREMENTS_CHECK.md](SYSTEM_REQUIREMENTS_CHECK.md)** - Hardware & software requirements

**Quick System Test (4 KB download):**
```bash
curl -sSL https://raw.githubusercontent.com/danieljohnconstantine-a11y/Greyhound-Agent/copilot/copy-ml-training-prediction-files/test_system.py | python3
```

---

---

## 📊 Repository Contents

| Folder | Size | Description |
|--------|------|-------------|
| `data/` | 159 MB | 719 race PDFs and CSV files |
| `models/` | 31 MB | Trained ML models (SALE, WENTWORTH PARK) |
| `data_predictions/` | ~5 MB | Prediction input PDFs |
| `src/` | ~500 KB | Python source code (12 modules) |
| `outputs/` | ~300 KB | Prediction results |

**Total:** 353 MB (~790 files)

---

## 🚀 Features

### Machine Learning
- **3-Algorithm Ensemble**: Random Forest, Gradient Boosting, XGBoost
- **Track-Specific Models**: Separate models for each track
- **Individual Dog Predictions**: 76 features per dog
- **Calibrated Probabilities**: Isotonic regression for better confidence
- **Individual Algorithm Scores**: NEW! RF_Score, GB_Score, XGB_Score columns show each algorithm's prediction

### Data Processing
- **PDF Parsing**: Automated extraction of race forms
- **Feature Engineering**: 67 engineered features from raw data
- **Weather & Track Data**: Environmental factors included
- **Historical Performance**: Career stats and recent form

### Outputs
- **Excel Reports**: Detailed predictions with confidence scores + individual RF/GB/XGB scores
- **Summary Statistics**: Track-by-track analysis with algorithm breakdowns
- **JSON Validation**: Pipeline integrity checks
- **Algorithm Transparency**: See how each ML algorithm scored every dog

---

## 📖 Usage

### Training Models
```bash
# Train track-specific ensemble models
python train_ml_track_ensemble.py

# Or use batch file (Windows)
train_ml_track_ensemble.bat
```

### Making Predictions
```bash
# Run predictions on new race forms
python run_track_ensemble_predictions.py

# Or use batch file (Windows)
run_track_ensemble_predictions.bat
```

**Output includes:**
- `track_ensemble_predictions.xlsx` - Full predictions with **RF_Score, GB_Score, XGB_Score** columns
- `track_ensemble_summary.txt` - Quick summary with individual algorithm scores

**Example output:**
```
Track | RaceNumber | Box | DogName    | ML_Confidence | RF_Score | GB_Score | XGB_Score
SALE  | 1          | 3   | Paw Ezra   | 15.0          | 14.6     | 15.2     | 15.3
```

See **[INDIVIDUAL_SCORES_GUIDE.md](INDIVIDUAL_SCORES_GUIDE.md)** for detailed explanation of RF/GB/XGB scores.

### Organizing Data
```bash
# Organize race data by track
ORGANIZE_ALL_TRACKS.bat
```

---

## 🧪 Testing & Verification

Pipeline testing documentation available:
- **[PIPELINE_TEST_REPORT.md](PIPELINE_TEST_REPORT.md)** - Technical test results
- **[PDF_EXTRACTION_VERIFICATION_REPORT.md](PDF_EXTRACTION_VERIFICATION_REPORT.md)** - Data extraction proof
- **[EXECUTIVE_SUMMARY.md](EXECUTIVE_SUMMARY.md)** - Quick overview
- **[README_TEST_DOCS.md](README_TEST_DOCS.md)** - Testing documentation index

**Verified:** 163 dogs predicted with 100% data extraction

---

## 📁 Project Structure

```
Greyhound-Agent/
├── data/                      # 719 race PDFs and CSV files (159 MB)
├── data_predictions/          # 13 prediction input PDFs (~5 MB)
├── models/                    # Trained ML models (31 MB)
│   ├── SALE/                  # SALE track models
│   ├── WENTWORTH PARK/        # WENTWORTH PARK models
│   └── ensemble_config.json   # Ensemble configuration
├── src/                       # Python source code (~500 KB)
│   ├── parser.py              # PDF parsing
│   ├── features.py            # Feature engineering
│   ├── ml_predictor_advanced.py  # ML predictions
│   └── ... (9 more modules)
├── outputs/                   # Prediction results (~300 KB)
│   ├── by_track/              # Track-specific results
│   └── combined/              # Multi-track analysis
├── train_ml_track_ensemble.py    # Training script
├── run_track_ensemble_predictions.py  # Prediction script
├── ORGANIZE_ALL_TRACKS.bat    # Data organization utility
└── DOWNLOAD_INSTRUCTIONS.md   # How to download this repo
```

---

## 🔧 Requirements

- Python 3.8+
- pdfplumber
- pandas
- numpy
- scikit-learn
- xgboost
- openpyxl

Install dependencies:
```bash
pip install pdfplumber pandas numpy scikit-learn xgboost openpyxl
```

---

## 📊 Model Performance

**SALE Track:**
- Ensemble of RF (14.6 MB) + GB (888 KB) + XGB (520 KB)
- Trained on historical race data
- Individual dog predictions with confidence scores

**WENTWORTH PARK Track:**
- Ensemble of RF (14.3 MB) + GB (911 KB) + XGB (554 KB)
- Track-specific feature scaling
- Calibrated probability outputs

---

## 📄 Documentation Index

- **[DOWNLOAD_INSTRUCTIONS.md](DOWNLOAD_INSTRUCTIONS.md)** - How to download (IMPORTANT!)
- **[SHOWCASE.md](SHOWCASE.md)** - Project showcase and overview
- **[PIPELINE_TEST_REPORT.md](PIPELINE_TEST_REPORT.md)** - Testing results
- **[PDF_EXTRACTION_VERIFICATION_REPORT.md](PDF_EXTRACTION_VERIFICATION_REPORT.md)** - Data extraction proof
- **[MISSION_COMPLETE.md](MISSION_COMPLETE.md)** - Project completion summary

---

## ⚙️ Output Files

After running predictions:
- `outputs/track_ensemble_predictions.xlsx` - All predictions with confidence
- `outputs/track_ensemble_summary.txt` - Summary statistics
- `outputs/by_track/[TRACK]/predictions.xlsx` - Track-specific results
- `outputs/combined/all_tracks_predictions.xlsx` - Combined analysis

---

## 🐛 Troubleshooting

### Cannot download repository?
See **[DOWNLOAD_INSTRUCTIONS.md](DOWNLOAD_INSTRUCTIONS.md)** for solutions.

### Models not loading?
Ensure all `.pkl` files in `models/` directory are present and not corrupted.

### PDF parsing errors?
Check that PDF files are in the correct format and not password-protected.

---

## 📝 License

This project is for educational and research purposes.

---

**Last Updated:** 2026-02-12  
**Version:** 1.0  
**Repository Size:** 353 MB
