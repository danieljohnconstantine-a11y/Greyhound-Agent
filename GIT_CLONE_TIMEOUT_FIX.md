# Git Clone Timeout Fix

## Your Error:
```
error: RPC failed; curl 56 Recv failure: Connection timed out
error: 4990 bytes of body are still expected
fatal: early EOF
fatal: fetch-pack: invalid index-pack output
```

## You Did Nothing Wrong!

The repository is **353 MB** (very large) and your connection timed out. This is a common issue with large repositories, especially on:
- Slow internet connections
- WSL (Windows Subsystem for Linux)
- Corporate/restricted networks
- Long distance from GitHub servers

---

## ⭐ Solution 1: Increase Git Buffer (TRY THIS FIRST!)

This is the easiest and works for most people.

```bash
# Step 1: Increase git buffer (one-time configuration)
git config --global http.postBuffer 524288000

# Step 2: Clone normally
cd /mnt/c/Users/danie/OneDrive/Desktop
git clone -b copilot/copy-ml-training-prediction-files https://github.com/danieljohnconstantine-a11y/Greyhound-Agent.git
```

**What this does:** Tells git to wait longer before timing out (allows 500MB downloads)

**Time:** 5-10 minutes to download

---

## Solution 2: Shallow Clone (Faster)

If Solution 1 still times out, try downloading less data:

```bash
cd /mnt/c/Users/danie/OneDrive/Desktop
git clone --depth 1 -b copilot/copy-ml-training-prediction-files https://github.com/danieljohnconstantine-a11y/Greyhound-Agent.git
```

**What this does:** Downloads only the latest version (not full history)

**Advantage:** Much smaller (~200 MB instead of 353 MB), faster download

**Time:** 3-5 minutes to download

---

## Solution 3: Partial Clone (Smartest)

Download files on-demand (requires Git 2.27+):

```bash
cd /mnt/c/Users/danie/OneDrive/Desktop
git clone --filter=blob:none -b copilot/copy-ml-training-prediction-files https://github.com/danieljohnconstantine-a11y/Greyhound-Agent.git
```

**What this does:** Downloads structure first, files later as needed

**Advantage:** Even smaller initial download (~100 MB)

**Time:** 2-3 minutes initial, then files download as you use them

---

## Solution 4: Clone in Chunks (Most Resilient)

If everything keeps timing out, try this step-by-step approach:

```bash
cd /mnt/c/Users/danie/OneDrive/Desktop

# Step 1: Create folder and initialize
mkdir Greyhound-Agent
cd Greyhound-Agent
git init

# Step 2: Add remote
git remote add origin https://github.com/danieljohnconstantine-a11y/Greyhound-Agent.git

# Step 3: Fetch branch (this may take 5-10 minutes)
git fetch --depth 1 origin copilot/copy-ml-training-prediction-files

# Step 4: Checkout
git checkout copilot/copy-ml-training-prediction-files
```

**What this does:** Breaks download into smaller chunks

**Advantage:** If one step fails, you can retry just that step

**Time:** 5-15 minutes total

---

## Solution 5: GitHub Desktop (No Command Line!)

The most reliable option for large repositories:

### Steps:

1. **Download GitHub Desktop**
   - Go to: https://desktop.github.com/
   - Download and install (Windows version)

2. **Sign in to GitHub**
   - Open GitHub Desktop
   - Click "Sign in to GitHub.com"
   - Enter your credentials

3. **Clone Repository**
   - Click "Clone a repository from the Internet"
   - Go to "URL" tab
   - Repository URL: `https://github.com/danieljohnconstantine-a11y/Greyhound-Agent.git`
   - Branch: `copilot/copy-ml-training-prediction-files`
   - Local path: `C:\Users\danie\OneDrive\Desktop\Greyhound-Agent`
   - Click "Clone"

4. **Wait**
   - Progress bar will show download
   - Takes 5-10 minutes
   - Automatically resumes if connection drops!

**Advantage:** 
- Most reliable for large repos
- Better resume capability
- Visual progress bar
- Works better than WSL on Windows

---

## WSL-Specific Tips

If you're using WSL (Windows Subsystem for Linux):

1. **WSL networking can be slower** - Try Solution 2 (shallow clone) or Solution 5 (GitHub Desktop)

2. **Alternative: Use Windows Command Prompt instead**
   ```cmd
   # Open Windows Command Prompt (cmd.exe)
   cd C:\Users\danie\OneDrive\Desktop
   git clone -b copilot/copy-ml-training-prediction-files https://github.com/danieljohnconstantine-a11y/Greyhound-Agent.git
   ```

3. **Or use PowerShell**
   ```powershell
   cd C:\Users\danie\OneDrive\Desktop
   git clone -b copilot/copy-ml-training-prediction-files https://github.com/danieljohnconstantine-a11y/Greyhound-Agent.git
   ```

---

## Comparison Table

| Solution | Download Size | Speed | Reliability | Best For |
|----------|--------------|--------|-------------|----------|
| 1. Buffer Increase | Full (353MB) | Normal | High | Most users ⭐ |
| 2. Shallow Clone | Medium (~200MB) | Fast | High | Slow connections |
| 3. Partial Clone | Small (~100MB) | Very Fast | Medium | Modern git |
| 4. Clone in Chunks | Full (353MB) | Slow | Very High | Persistent failures |
| 5. GitHub Desktop | Full (353MB) | Normal | Very High | WSL users |

---

## Verification

After successful clone, verify everything downloaded:

```bash
cd Greyhound-Agent
ls -la

# You should see:
# data/               (719 files)
# data_predictions/   (13 files)
# models/             (15 files)
# src/                (12 files)
# outputs/            (24 files)
# train_ml_track_ensemble.py
# run_track_ensemble_predictions.py
# And more...
```

Check folder size:
```bash
du -sh .
# Should show: ~353M or 353MB
```

---

## Still Having Issues?

### Try These:

1. **Different Network**
   - Try a different WiFi network
   - Use mobile hotspot
   - Try at different time of day

2. **Check Internet Speed**
   ```bash
   # Test your download speed
   curl -s https://raw.githubusercontent.com/sivel/speedtest-cli/master/speedtest.py | python3 -
   ```

3. **Use VPN** (if on restricted network)
   - Corporate networks may limit large downloads
   - Try personal network instead

4. **Contact Your Network Admin** (if on corporate network)
   - They may need to whitelist GitHub

5. **GitHub Desktop** (Recommended)
   - Most reliable option
   - Better resume capability
   - Works around most network issues

---

## Quick Reference

**Easiest (try first):**
```bash
git config --global http.postBuffer 524288000
cd /mnt/c/Users/danie/OneDrive/Desktop
git clone -b copilot/copy-ml-training-prediction-files https://github.com/danieljohnconstantine-a11y/Greyhound-Agent.git
```

**Fastest:**
```bash
cd /mnt/c/Users/danie/OneDrive/Desktop
git clone --depth 1 -b copilot/copy-ml-training-prediction-files https://github.com/danieljohnconstantine-a11y/Greyhound-Agent.git
```

**Most Reliable:**
- Use GitHub Desktop (download from https://desktop.github.com/)

---

## What's Next?

After successful clone:

1. **Install dependencies:**
   ```bash
   cd Greyhound-Agent
   pip3 install pandas numpy scikit-learn xgboost pdfplumber openpyxl
   ```

2. **Run training:**
   ```bash
   python3 train_ml_track_ensemble.py
   ```

3. **See guides:**
   - `UBUNTU_TRAINING_GUIDE.md` - Complete training guide
   - `SUPER_BASIC_UBUNTU_GUIDE.md` - Simple 3-step guide
   - `README.md` - Main documentation

---

## Summary

**You did nothing wrong!** Large repositories often timeout on slow connections or WSL.

**Best solutions:**
1. Increase buffer (easiest)
2. Shallow clone (fastest)
3. GitHub Desktop (most reliable)

**All should work** - pick the one that fits your situation!
