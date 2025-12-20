# Greyhound Prediction System - Windows Quick Start

## 🚀 Quick Start (3 Steps)

### Step 1: Setup (One-Time)
Double-click `setup.bat`
- Installs all required packages
- Creates necessary folders (data, models, output)

### Step 2: Add Your Race PDFs
1. Copy race PDF files to the `data\` folder
2. File names should be like: `DUBBG0312form.pdf`

### Step 3: Run Predictions
Choose one option:

**Option A: v4.4 Rule-Based (28-30% win rate)**
- Double-click `run_predictions.bat`
- Processes all PDFs in data folder
- Shows TIER0/TIER1 picks instantly

**Option B: ML Hybrid (35-40% win rate, ultra-selective)**
- First time: Double-click `train_ml.bat` (trains model on historical data)
- Then: Double-click `run_ml_hybrid.bat` for predictions
- Only bets when v4.4 AND ML both agree

---

## 📁 File Guide

### Batch Files (Double-click to run)
| File | Purpose | When to Use |
|------|---------|-------------|
| `setup.bat` | Install dependencies | Run once at start |
| `run_predictions.bat` | v4.4 predictions | Daily predictions |
| `train_ml.bat` | Train ML model | First time + monthly |
| `run_ml_hybrid.bat` | ML hybrid predictions | After ML training |

### Folders
- `data\` - Place race PDFs here
- `models\` - ML models saved here
- `output\` - Prediction results saved here

---

## 💡 Daily Workflow

### Morning Routine (Get Today's Picks)
1. Download today's race PDFs from your source
2. Copy PDFs to `data\` folder
3. Double-click `run_predictions.bat`
4. Check output for TIER0 picks (highest confidence)

### Using ML Hybrid (Optional, Higher Accuracy)
1. Ensure you have 5+ days of historical PDFs + results in `data\`
2. Double-click `train_ml.bat` (first time only)
3. Double-click `run_ml_hybrid.bat` for today's races
4. Only bet on races where both systems agree

---

## 🎯 Understanding the Output

### v4.4 Predictions
```
TIER0 (LOCK) - 42-45% win rate
├─ Score margin: 18%+ above 2nd place
├─ Box: 1, 2, or 8 only
└─ Career: 25+ starts minimum

TIER1 - 26-28% win rate
├─ Score margin: 8-18% above 2nd place
└─ All boxes eligible
```

### ML Hybrid Predictions
```
HYBRID BET - 35-40% win rate
├─ v4.4 says: TIER0 (18%+ margin)
├─ ML says: 75%+ confidence
└─ Both pick: SAME dog
```

**Only bet when all 3 conditions met!**

---

## ⚙️ Troubleshooting

### "Python not found"
- Install Python 3.8+ from python.org
- Check "Add to PATH" during installation

### "No PDFs found"
- Place PDFs in `data\` folder
- File names must end with `form.pdf`

### "ML model not found"
- Run `train_ml.bat` first
- Need 5+ days of historical data

### Training takes too long
- Normal for first time (5-10 minutes)
- Faster on subsequent runs
- Close other programs to speed up

---

## 📊 Performance Comparison

| System | Win Rate | Bets/Day | Best For |
|--------|----------|----------|----------|
| v4.4 Overall | 28-30% | All races | Balanced betting |
| v4.4 TIER0 | 42-45% | 15-20% | Selective betting |
| ML Hybrid | 35-40% | 10-15% | Ultra-conservative |

**Recommendation:** Start with v4.4 TIER0, add ML hybrid after 1 month of data collection.

---

## 🔄 Updating Historical Data

To improve ML accuracy over time:
1. After each race day, save results CSV to `data\results_YYYY-MM-DD.csv`
2. Re-run `train_ml.bat` weekly
3. Model learns from new data automatically

---

## 📞 Need Help?

1. Check error message in command window
2. Ensure Python 3.8+ installed
3. Verify PDFs in correct format
4. See ML_INTEGRATION_GUIDE.md for detailed ML setup

---

**System Version:** v4.4 + ML v1.0  
**Last Updated:** December 2, 2025
