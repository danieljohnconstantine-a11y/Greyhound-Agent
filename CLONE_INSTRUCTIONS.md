# How to Clone This Repository Successfully

This repository contains ML models and data files (~353MB total) which may cause timeout issues on slow or unstable internet connections. Below are multiple methods to successfully clone the repository.

## Quick Solution (Recommended for Slow Connections)

### Method 1: Shallow Clone (Fastest - Downloads only latest version)

```bash
# Navigate to your desired directory
cd /mnt/c/Users/danie/OneDrive/Desktop

# Remove any failed clone attempts
rm -rf Greyhound-Agent

# Shallow clone with depth 1 (only latest commit)
git clone --depth 1 -b copilot/copy-ml-training-prediction-files https://github.com/danieljohnconstantine-a11y/Greyhound-Agent.git

cd Greyhound-Agent
```

**Advantages:**
- Much faster download (~50-100MB instead of 353MB)
- Works better on slow/unstable connections
- Gets you all the files you need to run the project

**Disadvantages:**
- No git history (but you can fetch it later if needed)

---

## Method 2: Clone with Reduced Depth

```bash
cd /mnt/c/Users/danie/OneDrive/Desktop
rm -rf Greyhound-Agent

# Clone with last 5 commits
git clone --depth 5 -b copilot/copy-ml-training-prediction-files https://github.com/danieljohnconstantine-a11y/Greyhound-Agent.git

cd Greyhound-Agent
```

---

## Method 3: Download as ZIP (No Git Required)

If git clone continues to fail, download directly from GitHub:

1. Go to: https://github.com/danieljohnconstantine-a11y/Greyhound-Agent
2. Switch to branch: `copilot/copy-ml-training-prediction-files`
3. Click the green "Code" button
4. Select "Download ZIP"
5. Extract to your desired location

**Note:** This method doesn't include git history, but all files will be present.

---

## Method 4: Clone in Steps (For Unstable Connections)

If you keep getting disconnected, try cloning without checking out files first:

```bash
cd /mnt/c/Users/danie/OneDrive/Desktop
rm -rf Greyhound-Agent

# Step 1: Clone without checkout
git clone --no-checkout -b copilot/copy-ml-training-prediction-files https://github.com/danieljohnconstantine-a11y/Greyhound-Agent.git

cd Greyhound-Agent

# Step 2: Checkout files in small batches
git config core.compression 0
git checkout HEAD
```

---

## Method 5: Increase Git Settings (Already Done)

You've already run these commands, which help:

```bash
git config --global http.postBuffer 524288000
git config --global core.compression 0
git config --global http.lowSpeedLimit 0
git config --global http.lowSpeedTime 999999
```

---

## Troubleshooting

### If Clone Still Fails:

1. **Check your internet connection:**
   ```bash
   ping github.com
   ```

2. **Try using SSH instead of HTTPS:**
   ```bash
   git clone --depth 1 -b copilot/copy-ml-training-prediction-files git@github.com:danieljohnconstantine-a11y/Greyhound-Agent.git
   ```

3. **Clone during off-peak hours:**
   - Try early morning or late night when internet is less congested

4. **Use a VPN or different network:**
   - Sometimes corporate/ISP networks have issues with large downloads

5. **Resume a failed clone:**
   If you have a partial clone:
   ```bash
   cd Greyhound-Agent
   git fetch --unshallow
   git checkout copilot/copy-ml-training-prediction-files
   ```

---

## Verify Successful Clone

After cloning, verify you have all the files:

```bash
cd Greyhound-Agent

# Check key directories exist
ls -la models/
ls -la data_predictions/
ls -la src/

# Check Python scripts
ls -la *.py

# Expected key files:
# - train_ml_track_ensemble.py
# - run_track_ensemble_predictions.py
# - requirements.txt
# - models/ directory with SALE and WENTWORTH PARK subdirectories
```

---

## What's in This Repository

- **Total Size:** ~353MB
- **Large Files:**
  - RF model files: 14MB each (2 files)
  - Training data PDFs: ~600 files in `data/`
  - Prediction PDFs: 11 files in `data_predictions/`
  
These large files are necessary for the ML prediction system to work.

---

## After Successful Clone

1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

2. Run validation tests:
   ```bash
   python test_complete_pipeline.py
   python PROOF_INDIVIDUAL_DOG_PREDICTIONS.py
   ```

3. Generate predictions:
   ```bash
   python run_track_ensemble_predictions.py
   ```

---

## Need Help?

If you continue to experience issues:

1. Check the GitHub Issues page
2. Ensure you're on a stable internet connection
3. Try Method 1 (Shallow Clone) - it's the most reliable
4. Consider Method 3 (ZIP Download) as a last resort

---

**Recommended:** Use Method 1 (Shallow Clone) for fastest and most reliable download!
