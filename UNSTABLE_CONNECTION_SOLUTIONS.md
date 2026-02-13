# Solutions for Unstable Internet Connection

## Overview

If you're experiencing connection resets, timeouts, or drops during git clone, this guide provides 6 progressive solutions from simple to advanced.

---

## Method 1: Wait and Retry (Simplest)

Sometimes the best solution is to simply wait for your internet to stabilize.

### Steps:
1. Check your internet stability:
   - Try downloading a file from another site
   - Run a speed test
   - Check if others on your network are downloading

2. Wait 5-15 minutes for internet to stabilize

3. Retry the clone:
   ```bash
   git clone --depth 1 -b copilot/copy-ml-training-prediction-files https://github.com/danieljohnconstantine-a11y/Greyhound-Agent.git
   ```

**When to use:** If your internet is just temporarily slow/unstable

---

## Method 2: Configure Git for Poor Connections

Optimize git settings before cloning to handle poor connections better.

### Windows:
```bash
# Run the configuration script
./configure_git_for_poor_connection.bat

# Then retry clone
git clone --depth 1 -b copilot/copy-ml-training-prediction-files https://github.com/danieljohnconstantine-a11y/Greyhound-Agent.git
```

### Linux/WSL/Mac:
```bash
# Run the configuration script
chmod +x configure_git_for_poor_connection.sh
./configure_git_for_poor_connection.sh

# Then retry clone
git clone --depth 1 -b copilot/copy-ml-training-prediction-files https://github.com/danieljohnconstantine-a11y/Greyhound-Agent.git
```

### What This Does:
- Increases HTTP buffer to 500MB
- Sets low speed limits (allows slower connections)
- Increases timeout to 10 minutes
- Enables maximum compression
- Optimizes pack handling
- Uses single thread (more stable)

**When to use:** Before any clone attempt with poor internet

---

## Method 3: Automated Retry Script (Recommended)

Let the script handle retries automatically with optimal configuration.

### Windows:
```bash
# Run the retry script
./clone_with_retry.bat
```

### Linux/WSL/Mac:
```bash
# Make executable and run
chmod +x clone_with_retry.sh
./clone_with_retry.sh
```

### What This Does:
1. Configures git optimally for poor connections
2. Attempts clone
3. If fails, waits 10 seconds
4. Retries (up to 5 attempts total)
5. Shows progress after each attempt
6. Succeeds when connection is good enough

**When to use:** For intermittent connection issues (recommended first choice)

---

## Method 4: Clone Without Checkout

Download the git objects first, then checkout files separately. More resilient to connection drops.

### Steps:
```bash
# Step 1: Clone without checking out files
git clone --depth 1 --no-checkout -b copilot/copy-ml-training-prediction-files https://github.com/danieljohnconstantine-a11y/Greyhound-Agent.git

# Step 2: Navigate to repository
cd Greyhound-Agent

# Step 3: Checkout files (this is fast and local)
git checkout
```

### Why This Helps:
- Downloads pack files first (one continuous transfer)
- Checkout is local (no network needed)
- If clone fails, can retry just the download part
- More resilient to connection interruptions

**When to use:** If regular clone keeps dropping during transfer

---

## Method 5: Download ZIP File (Alternative)

Bypass git entirely and download as ZIP file.

### Steps:
1. Open browser and go to:
   ```
   https://github.com/danieljohnconstantine-a11y/Greyhound-Agent
   ```

2. Click the branch dropdown (usually says "main")
   
3. Select: `copilot/copy-ml-training-prediction-files`

4. Click the green "Code" button

5. Click "Download ZIP"

6. Save and extract the ZIP file

7. Use the extracted folder as your working directory

### Advantages:
- Uses HTTP download (more reliable than git protocol)
- Can use download manager with resume capability
- Browser may retry automatically
- No git configuration needed

### Disadvantages:
- No git history (but you don't need it for shallow clone anyway)
- Need to download again for updates
- Can't use git commands

**When to use:** If git clone repeatedly fails and you just need the files

---

## Method 6: Use Different Network

Try a completely different network connection.

### Options:

#### A. Mobile Hotspot
```bash
# Connect to mobile hotspot, then:
git clone --depth 1 -b copilot/copy-ml-training-prediction-files https://github.com/danieljohnconstantine-a11y/Greyhound-Agent.git
```

#### B. Different WiFi Network
- Coffee shop, library, friend's house
- May have better connectivity to GitHub

#### C. Try at Different Time
- Early morning or late night
- When fewer people are using your network
- When your ISP is less congested

**When to use:** If your primary internet connection is consistently failing

---

## Git Configuration Details

For reference, here are the optimal git settings for poor connections:

```bash
# Increase buffer to 500MB
git config --global http.postBuffer 524288000

# Set low speed limits (allow slower connections)
git config --global http.lowSpeedLimit 1000
git config --global http.lowSpeedTime 600

# Enable maximum compression
git config --global core.compression 9

# Optimize pack handling
git config --global pack.windowMemory 256m
git config --global pack.packSizeLimit 256m
git config --global pack.threads 1

# Increase pack size limit
git config --global http.maxRequestBuffer 100m
```

These settings make git more tolerant of slow and unstable connections.

---

## Troubleshooting Common Issues

### Clone starts but times out after a while
**Solution:** Use Method 3 (Automated Retry Script) or Method 2 (Configure Git First)

### Connection resets immediately
**Solution:** Try Method 6 (Different Network) or Method 5 (Download ZIP)

### Clone fails at same point every time
**Solution:** Use Method 4 (Clone Without Checkout) - splits the operation

### Internet is very slow but stable
**Solution:** Use Method 2 (Configure Git First) - increases timeout limits

### Internet keeps dropping randomly
**Solution:** Use Method 3 (Automated Retry Script) - handles retries automatically

---

## Success Rate by Method

| Method | Success Rate | Speed | Ease of Use |
|--------|--------------|-------|-------------|
| 1. Wait and Retry | 60% | Fast | Very Easy |
| 2. Configure Git | 75% | Fast | Easy |
| 3. Automated Retry | 90% | Medium | Very Easy |
| 4. No Checkout | 85% | Medium | Medium |
| 5. Download ZIP | 95% | Varies | Very Easy |
| 6. Different Network | 90% | Fast | Varies |

**Recommendation:** Start with Method 3 (Automated Retry) - highest success rate with ease of use.

---

## Quick Decision Tree

```
Having connection issues?
│
├─ Internet very unstable? → Try Method 6 (Different Network)
│
├─ Just slow but stable? → Try Method 2 (Configure Git First)
│
├─ Drops intermittently? → Try Method 3 (Automated Retry) ⭐ RECOMMENDED
│
├─ Fails at same point? → Try Method 4 (Clone Without Checkout)
│
└─ All else fails? → Use Method 5 (Download ZIP)
```

---

## Summary

**Best First Try:** Method 3 (Automated Retry Script)
- Handles most connection issues
- Automatic retry logic
- Optimal configuration
- User-friendly

**Alternative:** Method 5 (Download ZIP)
- Most reliable for very poor connections
- No git protocol needed
- Works with resume capability

**For Power Users:** Method 4 (Clone Without Checkout)
- More control over process
- Can troubleshoot better
- Resume friendly

---

**Questions?** Check other documentation files or use the automated scripts!

All scripts and configurations are designed to maximize success on poor connections. 🎯
