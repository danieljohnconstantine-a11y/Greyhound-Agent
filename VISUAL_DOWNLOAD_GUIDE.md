# 🎯 Visual Download Guide - Step by Step

## ❌ PROBLEM: "Invalid File" Error

When you click "Download ZIP" on GitHub:
```
[Download ZIP] → ⏬ Downloading... → ❌ Invalid File Error
```

**Why?** Repository is too large (353 MB) with big model files.

---

## ✅ SOLUTION: Use Git Clone Instead

### Visual Step-by-Step Guide

#### Step 1: Install Git (if not installed)

**Windows:**
```
1. Go to: https://git-scm.com/download/win
2. Download installer
3. Run installer
4. Click "Next" through all options (defaults are fine)
5. Click "Install"
```

**Mac:**
```
1. Open Terminal
2. Type: brew install git
   OR
   Download from: https://git-scm.com/download/mac
```

**Linux:**
```
Ubuntu/Debian: sudo apt-get install git
CentOS/RHEL: sudo yum install git
```

---

#### Step 2: Open Terminal/Command Prompt

**Windows:**
```
Press: Windows Key + R
Type: cmd
Press: Enter

You'll see: C:\Users\YourName>
```

**Mac:**
```
Press: Command + Space
Type: Terminal
Press: Enter

You'll see: user@computer ~ %
```

**Linux:**
```
Press: Ctrl + Alt + T

You'll see: user@computer:~$
```

---

#### Step 3: Navigate to Where You Want the Files

```bash
# Go to your desired location
# Examples:

# Windows - Desktop:
cd Desktop

# Windows - Documents:
cd Documents

# Mac/Linux - Desktop:
cd ~/Desktop

# Mac/Linux - Documents:
cd ~/Documents
```

---

#### Step 4: Clone the Repository

**Copy and paste this EXACT command:**

```bash
git clone -b copilot/copy-ml-training-prediction-files https://github.com/danieljohnconstantine-a11y/Greyhound-Agent.git
```

**What you'll see:**
```
Cloning into 'Greyhound-Agent'...
remote: Enumerating objects: 1234, done.
remote: Counting objects: 100% (1234/1234), done.
remote: Compressing objects: 100% (890/890), done.
remote: Total 1234 (delta 567), reused 1000 (delta 400)
Receiving objects: 100% (1234/1234), 353.00 MiB | 5.00 MiB/s, done.
Resolving deltas: 100% (567/567), done.
```

**Progress bar will show:**
```
Receiving objects:  50% (617/1234), 176.50 MiB | 5.00 MiB/s
Receiving objects:  75% (926/1234), 264.75 MiB | 5.00 MiB/s
Receiving objects: 100% (1234/1234), 353.00 MiB | 5.00 MiB/s, done.
```

**Time estimate:**
- Fast internet (50 Mbps): ~1 minute
- Medium internet (10 Mbps): ~5 minutes
- Slow internet (2 Mbps): ~20 minutes

---

#### Step 5: Verify Download

```bash
# Enter the folder
cd Greyhound-Agent

# List contents (Windows)
dir

# List contents (Mac/Linux)
ls -la
```

**You should see:**
```
data/
data_predictions/
models/
src/
outputs/
README.md
train_ml_track_ensemble.py
run_track_ensemble_predictions.py
... (more files)
```

---

## 🎉 SUCCESS!

You now have all 353 MB of files correctly downloaded!

### Quick Verification Checklist:

- [ ] `data/` folder exists (719 files, 159 MB)
- [ ] `models/` folder exists (15 files, 31 MB)
- [ ] `src/` folder exists (12 Python files)
- [ ] `data_predictions/` folder exists (13 PDFs)
- [ ] `train_ml_track_ensemble.py` file exists
- [ ] `run_track_ensemble_predictions.py` file exists

---

## 🚀 Next Steps

### Run Predictions:
```bash
# Install dependencies
pip install pdfplumber pandas numpy scikit-learn xgboost openpyxl

# Run predictions
python run_track_ensemble_predictions.py
```

### Train Models:
```bash
python train_ml_track_ensemble.py
```

---

## 🆘 Still Having Issues?

### Error: "git is not recognized"
**Fix:** Git not installed. Go back to Step 1.

### Error: "Permission denied"
**Fix (Windows):** Run Command Prompt as Administrator
**Fix (Mac/Linux):** Add `sudo` before command

### Error: "Repository not found"
**Fix:** Copy the exact command from Step 4. Check for typos.

### Slow download?
**Normal:** 353 MB takes time. Wait for it to complete. You'll see progress.

### Want only specific files?
**Solution:** See [DOWNLOAD_INSTRUCTIONS.md](DOWNLOAD_INSTRUCTIONS.md) - Method 3 (Sparse Checkout)

---

## 📱 Alternative: GitHub Desktop (No Command Line)

Don't like command line? Use GitHub Desktop:

1. **Download GitHub Desktop**
   - Go to: https://desktop.github.com/
   - Click "Download for [Your OS]"
   - Install it

2. **Clone Repository**
   - Open GitHub Desktop
   - Click: File → Clone Repository
   - Click: URL tab
   - Paste: `https://github.com/danieljohnconstantine-a11y/Greyhound-Agent`
   - Click: Clone

3. **Select Branch**
   - Click: Current Branch dropdown (top)
   - Select: `copilot/copy-ml-training-prediction-files`
   - Wait for download

4. **Open in Folder**
   - Right-click repository in sidebar
   - Click: "Show in Finder" (Mac) or "Show in Explorer" (Windows)

**Done!** All files downloaded.

---

## 📊 What Gets Downloaded?

```
Greyhound-Agent/           (Total: 353 MB, ~790 files)
│
├── 📁 data/               (159 MB) ← Race PDFs and CSVs
├── 📁 models/             (31 MB)  ← ML models
├── 📁 data_predictions/   (5 MB)   ← Input PDFs
├── 📁 src/                (500 KB) ← Python code
├── 📁 outputs/            (300 KB) ← Results
└── 📄 scripts/            (100 KB) ← Training & prediction
```

---

## 💡 Pro Tips

### Tip 1: Check Download Size
```bash
# After download, check folder size
du -sh Greyhound-Agent

# Should show: ~353M
```

### Tip 2: Update Repository Later
```bash
cd Greyhound-Agent
git pull
```
This gets any new changes without re-downloading everything.

### Tip 3: Save Disk Space
Only need code? Use sparse checkout:
```bash
git sparse-checkout set src models
```
Downloads only ~32 MB instead of 353 MB!

---

## 📞 Need More Help?

- **Full documentation:** [DOWNLOAD_INSTRUCTIONS.md](DOWNLOAD_INSTRUCTIONS.md)
- **Quick fix:** [ZIP_DOWNLOAD_FIX.md](ZIP_DOWNLOAD_FIX.md)
- **Git help:** https://git-scm.com/doc
- **GitHub Desktop help:** https://docs.github.com/en/desktop

---

**Remember: Don't use the ZIP download button!**

Use `git clone` or GitHub Desktop for repositories over 100 MB.
