# Download Verification Checklist

Use this checklist to verify your download is complete and valid before extracting.

---

## Pre-Download Checklist

Before starting your download:

- [ ] **Check internet connection**
  - Run speed test: https://www.speedtest.net/
  - Minimum recommended: 5 Mbps
  - Stable connection (no frequent drops)

- [ ] **Check disk space**
  - Need: ~500 MB free minimum
  - Check: Right-click drive → Properties
  - Free up space if needed

- [ ] **Prepare environment**
  - Close bandwidth-heavy programs
  - Disable sleep/hibernate
  - Keep browser open during download
  - Don't schedule other large downloads

- [ ] **Choose download method**
  - Stable internet: Browser ZIP download OK
  - Unstable internet: Use git clone with retry
  - Very unstable: Use download manager

---

## During Download Checklist

While downloading:

- [ ] **Monitor progress**
  - Watch percentage increase
  - Check speed is reasonable
  - Verify it doesn't stall

- [ ] **Keep system active**
  - Don't close browser
  - Don't sleep/hibernate computer
  - Don't disconnect internet

- [ ] **Watch for errors**
  - Network error messages
  - Download stopping unexpectedly
  - Browser crashes

---

## Post-Download Checklist

### Immediate Verification (Before Extracting!)

- [ ] **Check download completed**
  - Look for download completion notification
  - No `.crdownload` or `.part` extension
  - File shows in Downloads folder

- [ ] **Verify file size - CRITICAL!**
  ```
  Expected ZIP size: ~95-110 MB (100,000,000 bytes)
  
  How to check:
  1. Right-click ZIP file
  2. Click "Properties"
  3. Look at "Size" field
  4. Compare to expected
  ```
  
  **If size is LESS than 95 MB:**
  - ❌ Download incomplete
  - ❌ DO NOT EXTRACT
  - ❌ Delete file and download again

- [ ] **Check file name**
  - Should end in `.zip`
  - Full name: `Greyhound-Agent-copilot-copy-ml-training-prediction-files.zip`
  - No strange characters or corruption in name

- [ ] **Check modified date**
  - Should be today's date
  - Shows recent time
  - Confirms it's your fresh download

### Test Extraction

- [ ] **Test ZIP validity**
  ```
  1. Right-click ZIP file
  2. Click "Extract All..."
  3. If error immediately → ZIP corrupted
  4. If starts extracting → Continue
  5. Can cancel after it starts
  ```

- [ ] **Check extraction destination**
  - Choose location with enough space
  - Prefer local drive (not network)
  - Remember location for later

---

## Detailed File Size Guide

### Expected Sizes

```
ZIP file (compressed):    ~95-110 MB
Extracted (full repo):    ~353 MB
After extraction total:   ~450 MB (ZIP + extracted)
```

### What Different Sizes Mean

| Your File Size | Meaning | Action |
|---------------|---------|--------|
| 0 KB - 1 MB | Download just started or failed | Delete and retry |
| 1 MB - 50 MB | Download incomplete (interrupted) | Delete and retry |
| 50 MB - 94 MB | Partial download (connection dropped) | Delete and retry |
| 95 MB - 110 MB | ✅ Likely complete | Proceed to extraction |
| >150 MB | Something wrong (not a ZIP?) | Delete and retry |

---

## Extraction Verification

### After Extracting

- [ ] **Check folder created**
  - Name: `Greyhound-Agent-copilot-copy-ml-training-prediction-files`
  - Or: `Greyhound-Agent` (may be renamed)

- [ ] **Verify folder size**
  - Should be ~353 MB
  - Right-click folder → Properties → Size

- [ ] **Check folder contents**
  - [ ] `data/` folder exists (~310 MB)
  - [ ] `models/` folder exists (~31 MB)
  - [ ] `data_predictions/` folder exists (~9 MB)
  - [ ] `src/` folder exists (~100 KB)
  - [ ] `requirements.txt` file exists
  - [ ] `README.md` or similar documentation exists

- [ ] **Count files (optional)**
  - Should have 680+ files total
  - Mostly PDF files in data/ folder
  - At least 76 Python files in src/

### Integrity Checks

- [ ] **Check critical files exist**
  ```
  models/SALE/rf.pkl                    (~14 MB)
  models/SALE/gb.pkl                    (~900 KB)
  models/SALE/xgb.pkl                   (~500 KB)
  models/WENTWORTH PARK/rf.pkl          (~14 MB)
  requirements.txt
  train_ml_track_ensemble.py
  run_track_ensemble_predictions.py
  ```

- [ ] **Verify no error files**
  - No files named "Error" or "Corrupted"
  - No 0 KB files (except legitimate empty files)
  - No obvious missing sections

---

## Quick Decision Tree

### Is Your ZIP File Valid?

```
Check file size
│
├─ Size < 95 MB?
│  └─ NO → Download incomplete
│     └─ Action: Delete and re-download
│
├─ Size 95-110 MB?
│  └─ YES → Probably good
│     ├─ Try extracting
│     ├─ Extracts successfully?
│     │  ├─ YES → ✅ You're good!
│     │  └─ NO → Corrupted during transfer
│     │     └─ Action: Delete and re-download
│
└─ Size > 150 MB?
   └─ Wrong file or error
      └─ Action: Delete and re-download
```

---

## What to Do If Download Fails Verification

### If File Size is Wrong

**Don't waste time trying to extract!**

1. **Delete the file**
   ```
   Right-click → Delete
   Empty Recycle Bin
   ```

2. **Identify the cause**
   - Internet disconnected during download?
   - Computer went to sleep?
   - Browser crashed?
   - Disk space ran out?

3. **Fix the cause**
   - Wait for stable internet
   - Disable sleep mode
   - Free up disk space
   - Try different browser

4. **Choose better method**
   
   **For unstable internet:**
   ```bash
   # Use git clone with retry instead
   cd /mnt/c/Users/danie/OneDrive/Desktop
   ./clone_with_retry.sh
   ```
   
   **For stable internet:**
   - Re-download ZIP from GitHub
   - Or use download manager (can resume)

### If Extraction Fails

**ZIP file might be corrupted:**

1. **Try different extraction tool**
   - Windows built-in extractor
   - 7-Zip (free): https://www.7-zip.org/
   - WinRAR (trial): https://www.win-rar.com/

2. **If all tools fail**
   - ZIP is definitely corrupted
   - Delete and re-download
   - Consider using git clone instead

### If Extracted Files Are Wrong

**Partial or corrupted extraction:**

1. **Delete extracted folder**
2. **Verify ZIP file size again**
3. **Re-extract with different tool**
4. **If still wrong, re-download ZIP**

---

## Prevention Checklist

### To Prevent Future Issues

- [ ] **Use stable internet**
  - Test before large downloads
  - Avoid peak hours if possible
  - Use wired connection vs WiFi

- [ ] **Use appropriate method**
  - Stable internet → ZIP download OK
  - Unstable internet → Git clone with retry
  - Very poor → Download manager

- [ ] **Configure correctly**
  - Disable sleep during downloads
  - Ensure sufficient disk space
  - Close other programs

- [ ] **Verify immediately**
  - Check size right after download
  - Don't wait to verify later
  - Catch problems early

---

## Recommended Tools

### For Verification

- **File size:** Windows Explorer Properties (built-in)
- **ZIP test:** 7-Zip → Test Archive
- **Extraction:** 7-Zip or Windows built-in

### For Downloading

**If ZIP keeps failing:**
- Git with retry script (included in repo)
- Free Download Manager
- Internet Download Manager (paid)

### For Comparison

**File hashes (advanced users):**
```bash
# Get SHA256 of your download
certutil -hashfile Greyhound-Agent.zip SHA256

# Compare with successful download
# (Ask others who succeeded)
```

---

## Summary Checklist

### Before You Extract - The Critical Check

✅ **File size is 95-110 MB?**
   - If YES → Proceed to extraction
   - If NO → Delete and re-download

✅ **File ends in .zip (not .crdownload)?**
   - If YES → Download complete
   - If NO → Still downloading, wait

✅ **Modified date is recent?**
   - If YES → Fresh download
   - If NO → Old failed attempt, delete

### After Extraction - Verify Success

✅ **Folder size is ~353 MB?**
✅ **Has data/, models/, src/ folders?**
✅ **Has requirements.txt?**
✅ **Has Python files?**

**If all YES → Success! You're ready to use it.**

---

## Quick Commands for Your Situation

### If You Have Unstable Internet

**Skip ZIP, use this instead:**

```bash
cd /mnt/c/Users/danie/OneDrive/Desktop
rm -rf Greyhound-Agent Greyhound-Agent*.zip
./clone_with_retry.sh
```

**Why:**
- More reliable for poor connections
- Automatic retries
- Can resume from failures
- 90% success rate

### If You Must Use ZIP

**After downloading:**

```bash
# Check file size
ls -lh Greyhound-Agent*.zip

# Should show ~95-110M
# If less, delete and retry with better internet
```

---

## Need More Help?

**If verification fails:**
1. See `FIX_CORRUPTED_ZIP.md` for detailed solutions
2. See `ZIP_DOWNLOAD_GUIDE.md` for complete guide
3. See `UNSTABLE_CONNECTION_SOLUTIONS.md` for connection issues

**Quick answer:**
For unstable internet, abandon ZIP and use `./clone_with_retry.sh` instead!
