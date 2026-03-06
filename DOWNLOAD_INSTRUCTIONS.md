# 📥 How to Download This Repository

## ⚠️ Important: ZIP Download Issues

**The GitHub "Download ZIP" button may fail** because this repository contains:
- 353 MB of data
- Large ML model files (14+ MB each)
- 700+ PDF files (159 MB)
- Binary files that don't compress well

**If the ZIP file shows "invalid file" error, use one of the methods below instead.**

---

## ✅ Recommended Download Methods

### Method 1: Git Clone (BEST - Works for Large Repos)

This is the **most reliable method** for large repositories:

```bash
# Clone the entire repository
git clone -b copilot/copy-ml-training-prediction-files https://github.com/danieljohnconstantine-a11y/Greyhound-Agent.git

# Navigate into the folder
cd Greyhound-Agent
```

**Advantages:**
- ✅ Handles large files properly
- ✅ No size limits
- ✅ All files downloaded correctly
- ✅ Can update with `git pull`

**Requirements:**
- Git installed ([Download Git](https://git-scm.com/downloads))
- Internet connection
- ~400 MB disk space

---

### Method 2: GitHub Desktop (Easy GUI Method)

If you prefer a graphical interface:

1. **Download GitHub Desktop**: https://desktop.github.com/
2. **Open GitHub Desktop**
3. **File → Clone Repository**
4. **URL tab**: Enter `https://github.com/danieljohnconstantine-a11y/Greyhound-Agent`
5. **Branch**: Select `copilot/copy-ml-training-prediction-files`
6. **Click "Clone"**

**Advantages:**
- ✅ User-friendly interface
- ✅ Handles large files
- ✅ Easy updates

---

### Method 3: Sparse Checkout (Download Specific Folders Only)

If you only need specific folders (e.g., just the models):

```bash
# Initialize sparse checkout
git clone -b copilot/copy-ml-training-prediction-files --no-checkout https://github.com/danieljohnconstantine-a11y/Greyhound-Agent.git
cd Greyhound-Agent

# Enable sparse checkout
git sparse-checkout init --cone

# Choose which folders to download
git sparse-checkout set models src data_predictions

# Get the files
git checkout
```

**Advantages:**
- ✅ Download only what you need
- ✅ Faster download
- ✅ Less disk space

**Popular folder combinations:**
- Models only: `models`
- Code only: `src`
- Complete ML pipeline: `models src data_predictions train_ml_track_ensemble.py run_track_ensemble_predictions.py`

---

### Method 4: Download Individual Folders (Browser Method)

For individual files or small folders:

1. **Navigate to the folder** on GitHub
2. **Use a browser extension** like:
   - [GitZip](https://gitzip.org/) - Paste the GitHub folder URL
   - [DownGit](https://minhaskamal.github.io/DownGit/) - Create download links

**Example:**
- For models folder: `https://github.com/danieljohnconstantine-a11y/Greyhound-Agent/tree/copilot/copy-ml-training-prediction-files/models`

**Advantages:**
- ✅ No Git installation needed
- ✅ Download specific folders only

**Disadvantages:**
- ⚠️ Still may fail for folders with large files
- ⚠️ Requires external tools

---

## 📊 Repository Contents Overview

| Folder | Size | Files | Description |
|--------|------|-------|-------------|
| `data/` | 159 MB | 719 | Race PDFs and CSV files |
| `models/` | 31 MB | 15 | Trained ML models (SALE, WENTWORTH PARK) |
| `data_predictions/` | ~5 MB | 13 | Prediction input PDFs |
| `src/` | ~500 KB | 12 | Python source code |
| `outputs/` | ~300 KB | 24 | Prediction results |
| **Total** | **353 MB** | **~790** | Complete ML pipeline |

---

## 🔧 Troubleshooting

### Problem: "The download is taking forever"
**Solution:** The repository is 353 MB. On slower connections, this can take 5-10 minutes. Use `git clone` which shows progress.

### Problem: "Invalid file" or "Corrupted ZIP"
**Solution:** This is a known GitHub limitation. Use Method 1 (Git Clone) instead.

### Problem: "I don't have Git installed"
**Solution:** 
- **Windows**: Download from https://git-scm.com/download/win
- **Mac**: Install via `brew install git` or download from https://git-scm.com/download/mac
- **Linux**: `sudo apt-get install git` (Ubuntu/Debian) or `sudo yum install git` (CentOS/RHEL)

### Problem: "Not enough disk space"
**Solution:** Use Method 3 (Sparse Checkout) to download only the folders you need.

### Problem: "I only need the code, not the data"
**Solution:** Use sparse checkout:
```bash
git sparse-checkout set src models train_ml_track_ensemble.py run_track_ensemble_predictions.py
```
This downloads only ~32 MB instead of 353 MB.

---

## 💡 Quick Start After Download

Once downloaded, you can:

1. **Train models:**
   ```bash
   python train_ml_track_ensemble.py
   ```

2. **Run predictions:**
   ```bash
   python run_track_ensemble_predictions.py
   ```

3. **Explore the code:**
   - `src/parser.py` - PDF parsing
   - `src/features.py` - Feature engineering
   - `src/ml_predictor_advanced.py` - ML predictions

---

## 📞 Still Having Issues?

If none of these methods work:

1. **Check your internet connection** - 353 MB requires stable connection
2. **Free up disk space** - Ensure you have at least 500 MB free
3. **Try a different network** - Some corporate networks block large downloads
4. **Use a download manager** - For git clone, use a tool that can resume interrupted downloads

---

## 📖 Additional Resources

- [Git Documentation](https://git-scm.com/doc)
- [GitHub Desktop Guide](https://docs.github.com/en/desktop)
- [Git Sparse Checkout Guide](https://git-scm.com/docs/git-sparse-checkout)

---

**Last Updated:** 2026-02-12  
**Repository Size:** 353 MB  
**Branch:** copilot/copy-ml-training-prediction-files
