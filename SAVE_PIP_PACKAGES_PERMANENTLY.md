# How to Save Pip Packages Permanently

## Question

"is there away i can save pip install pandas numpy scikit-learn xgboost pdfplumber openpyxl permanently to local pc, so i dont have to down load each time?"

## Answer

✅ **YES - Multiple ways to save packages permanently!**

---

## Quick Summary

**3 Main Methods:**

1. **Keep Same Virtual Environment** ⭐ EASIEST
   - Don't delete `venv/` directory
   - Packages stay installed forever
   - Just activate when needed

2. **Pip Cache** ⭐ ALREADY WORKING
   - Pip automatically caches packages
   - Second install much faster
   - No setup needed

3. **Local Package Repository** ⭐ ADVANCED
   - Download packages to folder
   - Install from folder anytime
   - Complete offline capability

---

## Method 1: Keep Same Virtual Environment (EASIEST) ⭐⭐⭐⭐⭐

### The Problem You Might Be Having

**Are you doing this?**
```bash
cd ~/Desktop
rm -rf Greyhound-Agent          # ❌ Delete everything
git clone ...                    # Clone again
cd Greyhound-Agent
python3 -m venv venv            # Create new venv
pip install [packages]           # Download 179 MB again ❌
```

**This makes you re-download packages every time!**

### The Solution: Just Keep the Directory!

```bash
# Setup ONCE:
cd /mnt/c/Users/danie/OneDrive/Desktop/Greyhound-Agent
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt  # Download once (10-30 minutes)

# Use ANYTIME (forever):
cd /mnt/c/Users/danie/OneDrive/Desktop/Greyhound-Agent
source venv/bin/activate         # Just activate! (1 second)
python train_ml_track_ensemble.py  # Works immediately!

# Important: DON'T delete the Greyhound-Agent directory!
```

### Why This Works

**Virtual environment is just a folder:**
```
Greyhound-Agent/
├── venv/                      ← This is just a folder!
│   ├── bin/
│   │   └── python            ← Python executable
│   ├── lib/
│   │   └── python3.12/
│   │       └── site-packages/  ← YOUR PACKAGES HERE!
│   │           ├── pandas/      (~200 MB)
│   │           ├── numpy/       (~80 MB)
│   │           ├── sklearn/     (~35 MB)
│   │           ├── xgboost/     (~50 MB)
│   │           ├── pdfplumber/  (~2 MB)
│   │           └── openpyxl/    (~1 MB)
├── data/
└── train_ml_track_ensemble.py
```

**Keep the folder = packages stay installed!**

### Benefits

✅ Simplest solution (no extra setup)
✅ Packages installed once, use forever
✅ No re-downloading needed
✅ Works immediately when activated
✅ Takes ~400 MB disk space (one-time)

---

## Method 2: Pip Cache (ALREADY WORKING!) ⭐⭐⭐⭐⭐

### Good News: Pip Automatically Caches Packages!

When you install packages, pip saves them automatically:

**Cache locations:**
- Linux/WSL: `~/.cache/pip/`
- Windows: `%LocalAppData%\pip\Cache`
- Mac: `~/Library/Caches/pip/`

### How It Helps

**First install (downloads from internet):**
```bash
pip install pandas numpy scikit-learn xgboost pdfplumber openpyxl
# Downloads 179 MB from PyPI
# Saves to cache automatically ✅
# Time: 10-30 minutes
```

**Second install (uses cache):**
```bash
# Create new venv
python3 -m venv new_venv
source new_venv/bin/activate

# Install again
pip install pandas numpy scikit-learn xgboost pdfplumber openpyxl
# Finds packages in cache! ✅
# Installs from cache (much faster)
# NO internet download needed!
# Time: 2-5 minutes
```

### Check Your Cache

```bash
# See cache location
pip cache dir

# See cache size
pip cache info

# List cached packages
pip cache list

# Clear cache (if needed)
pip cache purge
```

### Benefits

✅ Automatic (no setup needed)
✅ Second install 5-10× faster
✅ Works across all virtual environments
✅ Saves ~200 MB disk space
✅ Already helping you now!

---

## Method 3: Local Package Repository (ADVANCED) ⭐⭐⭐

### Create Permanent Package Store

```bash
# 1. Create directory for packages
mkdir -p ~/pip-packages

# 2. Download all packages once (WITH internet)
pip download pandas numpy scikit-learn xgboost pdfplumber openpyxl \
  -d ~/pip-packages/

# 3. Later: Install from local directory (NO internet needed!)
pip install pandas numpy scikit-learn xgboost pdfplumber openpyxl \
  --no-index --find-links ~/pip-packages/
```

### Download All Dependencies

```bash
# Download packages WITH all dependencies
pip download -r requirements.txt -d ~/pip-packages/
```

### Install from Local Repository

```bash
# Create new venv
python3 -m venv new_venv
source new_venv/bin/activate

# Install from local packages
pip install -r requirements.txt \
  --no-index --find-links ~/pip-packages/
```

### Benefits

✅ Download once, use forever
✅ Works completely offline
✅ Reuse across multiple virtual environments
✅ Can copy to USB/external drive
✅ Full control over package versions
✅ Takes ~200 MB disk space

---

## Method 4: Offline Wheelhouse (ADVANCED)

### Create Complete Offline Package Set

```bash
# 1. Create directory
mkdir -p ~/greyhound-offline-packages

# 2. Download everything (with internet)
cd /path/to/Greyhound-Agent
pip download -r requirements.txt -d ~/greyhound-offline-packages/

# 3. Later: Install completely offline
cd new-project
python3 -m venv venv
source venv/bin/activate
pip install --no-index \
  --find-links ~/greyhound-offline-packages/ \
  -r requirements.txt
```

### Use Cases

- ✈️ Airplane travel
- 🏔️ Remote locations without internet
- 🔒 Restricted/secure networks
- 💾 Creating installer packages
- 🌍 Multiple computers

### Benefits

✅ Complete offline capability
✅ Includes all dependencies
✅ Portable (copy to USB)
✅ No internet needed after download
✅ Can share with others

---

## Method 5: System-Wide Installation (NOT RECOMMENDED)

### Install Globally

```bash
# Install to system Python (no venv)
pip install pandas numpy scikit-learn xgboost pdfplumber openpyxl
```

### Why NOT Recommended

❌ No isolation between projects
❌ Version conflicts with other projects
❌ Hard to manage dependencies
❌ Can break system tools
❌ Difficult to clean up

**Only use if you:**
- Have a single Python project
- Don't care about isolation
- Understand the risks

---

## Method Comparison

| Method | Simplicity | Speed | Disk Space | Internet | Isolation | Best For |
|--------|------------|-------|------------|----------|-----------|----------|
| **Keep venv** | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | 400 MB (one) | Once | ✅ Yes | Everyone |
| **Pip cache** | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ | 200 MB | Once/pkg | ✅ Yes | Auto |
| **Local repo** | ⭐⭐⭐ | ⭐⭐⭐⭐⭐ | 200 MB | Once | ✅ Yes | Advanced |
| **Wheelhouse** | ⭐⭐ | ⭐⭐⭐⭐⭐ | 200 MB | Once | ✅ Yes | Offline |
| **System-wide** | ⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | 400 MB | Once | ❌ No | Single project |

---

## What You Should Do

### Recommended: Method 1 (Keep Same Venv)

**If you've been doing this (WRONG):**
```bash
cd ~/Desktop
rm -rf Greyhound-Agent  # ❌ STOP DOING THIS
```

**Do this instead (CORRECT):**
```bash
# Setup once:
cd /mnt/c/Users/danie/OneDrive/Desktop
# Keep Greyhound-Agent directory! Don't delete it!

# Use anytime:
cd Greyhound-Agent
source venv/bin/activate
python train_ml_track_ensemble.py
```

**Key change:** Stop deleting the `Greyhound-Agent` directory!

---

## Common Mistakes

### Mistake 1: Deleting Virtual Environment

```bash
rm -rf venv  # ❌ DON'T DO THIS
rm -rf Greyhound-Agent  # ❌ DON'T DO THIS
```

**Result:** All packages deleted, must re-download

**Fix:** Never delete `venv/` or `Greyhound-Agent/` directory

### Mistake 2: Creating New Venv Each Time

```bash
python3 -m venv venv  # ❌ DON'T REPEAT if venv exists
```

**Result:** Overwrites existing venv, deletes all packages

**Fix:** Create venv once, activate when needed

### Mistake 3: Not Activating Venv

```bash
python train_ml_track_ensemble.py  # ❌ Uses system Python
```

**Result:** Packages not found error

**Fix:** Always activate first:
```bash
source venv/bin/activate  # Linux/Mac/WSL
venv\Scripts\activate     # Windows
```

---

## Disk Space Requirements

### Virtual Environment (~400 MB)

```
venv/
├── bin/                      2 MB
├── include/                  1 KB
└── lib/
    └── python3.12/
        └── site-packages/
            ├── pandas/      200 MB
            ├── numpy/        80 MB
            ├── scipy/        35 MB
            ├── sklearn/      35 MB
            ├── xgboost/      50 MB
            └── others/       30 MB
            Total:          ~400 MB
```

### Pip Cache (~200 MB)

```
~/.cache/pip/
├── wheels/                 150 MB
└── http/                    50 MB
Total:                      ~200 MB
```

### Local Repository (~200 MB)

```
~/pip-packages/
├── pandas-3.0.1.whl         11 MB
├── numpy-2.4.2.whl          17 MB
├── xgboost-3.2.0.whl       132 MB
├── scikit_learn-1.8.0.whl    9 MB
├── pdfplumber-0.11.9.whl     1 MB
└── others/                  30 MB
Total:                      ~200 MB
```

---

## Advanced Tips

### Share Packages Across Projects

```bash
# Create central package repository
mkdir -p ~/central-pip-packages

# Download packages
pip download pandas numpy scikit-learn xgboost pdfplumber openpyxl \
  -d ~/central-pip-packages/

# Use in any project
pip install --no-index --find-links ~/central-pip-packages/ \
  pandas numpy scikit-learn xgboost pdfplumber openpyxl
```

### Create Portable Package Bundle

```bash
# Download packages
pip download -r requirements.txt -d /path/to/usb/packages/

# On another computer (offline)
pip install --no-index --find-links /path/to/usb/packages/ \
  -r requirements.txt
```

### Verify Cache Usage

```bash
# Install with verbose output
pip install -v pandas

# Look for: "Using cached" messages
# This confirms cache is being used
```

---

## Troubleshooting

### Problem: Cache Not Being Used

**Check cache location:**
```bash
pip cache dir
ls -lh $(pip cache dir)
```

**Enable cache if disabled:**
```bash
pip config set global.no-cache-file false
```

### Problem: Running Out of Disk Space

**Clear pip cache:**
```bash
pip cache purge
```

**Remove old virtual environments:**
```bash
# List venv directories
du -sh */venv/

# Remove ones you don't need
rm -rf old-project/venv/
```

---

## Summary

### Question

"is there away i can save pip install pandas numpy scikit-learn xgboost pdfplumber openpyxl permanently to local pc, so i dont have to down load each time?"

### Answer

✅ **YES - Multiple ways!**

### Best Method: Keep Same Virtual Environment

1. Create venv once: `python3 -m venv venv`
2. Install packages: `pip install -r requirements.txt`
3. **Never delete the directory**
4. Use anytime: `source venv/bin/activate`

### Alternative: Pip Cache (Already Working)

- Pip automatically caches packages
- Second install much faster
- No setup needed

### Advanced: Local Repository

- Download packages to folder
- Install from folder anytime
- Works completely offline

### The Key Insight

**Virtual environment is just a folder on your disk.**

**Keep the folder = packages stay installed forever!**

### What to Do

```bash
# Once:
cd /mnt/c/Users/danie/OneDrive/Desktop/Greyhound-Agent
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Forever:
cd /mnt/c/Users/danie/OneDrive/Desktop/Greyhound-Agent
source venv/bin/activate
# Packages already installed!
```

**Stop deleting your Greyhound-Agent directory!** 💾

---

**Total disk space:** 200-400 MB (one-time cost)
**Time saved:** Hours of re-downloading
**Simplicity:** Just keep the directory! 🎯
