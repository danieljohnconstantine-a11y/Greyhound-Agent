# ⚠️ ZIP DOWNLOAD ISSUE - QUICK FIX

## Problem
GitHub ZIP download fails or shows "invalid file" error.

## Why?
- Repository is 353 MB (too large for GitHub ZIP)
- Contains large ML model files (14+ MB each)
- 700+ PDF files cause compression issues

## ✅ SOLUTION (Choose One)

### Option 1: Git Clone (Recommended)
```bash
git clone -b copilot/copy-ml-training-prediction-files https://github.com/danieljohnconstantine-a11y/Greyhound-Agent.git
```

### Option 2: GitHub Desktop
1. Download: https://desktop.github.com/
2. Clone this repository
3. Select branch: `copilot/copy-ml-training-prediction-files`

### Option 3: Download Specific Folders Only
Use sparse checkout:
```bash
git clone -b copilot/copy-ml-training-prediction-files --no-checkout https://github.com/danieljohnconstantine-a11y/Greyhound-Agent.git
cd Greyhound-Agent
git sparse-checkout init --cone
git sparse-checkout set models src data_predictions
git checkout
```

## 📖 Full Instructions
See [DOWNLOAD_INSTRUCTIONS.md](DOWNLOAD_INSTRUCTIONS.md) for detailed guide.

## Need Help?
- Install Git: https://git-scm.com/downloads
- Git Desktop: https://desktop.github.com/
- Contact repository owner

---

**Don't use "Download ZIP" button - it will fail!**
