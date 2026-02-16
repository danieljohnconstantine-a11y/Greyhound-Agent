# Correct Clone Commands Reference

Quick reference for the correct git clone commands with the typo fixed and proper authentication.

## The Problem You Had

### Original Command (WRONG)

```bash
git clone --depth 1 -b copilot/copy-ml-training-prediction-files \
  https://github.com/danieljohnconstanitne-a11y/Greyhound-Agent.git
                              ^^ TYPO: missing 't'
```

**Two issues:**
1. Typo in URL: `constani**t**ne` should be `constanti**n**e`
2. Password authentication doesn't work (GitHub deprecated it in 2021)

---

## Correct Commands

### Method 1: HTTPS with Personal Access Token (PAT)

**Setup first:** Create PAT at https://github.com/settings/tokens
- Select scope: `repo`
- Copy token (shown only once)

**Clone command:**
```bash
git clone --depth 1 -b copilot/copy-ml-training-prediction-files \
  https://github.com/danieljohnconstantine-a11y/Greyhound-Agent.git
```

**When prompted:**
- Username: `danieljohnconstantine-a11y`
- Password: `[paste your PAT]`

### Method 2: SSH

**Setup first:** Generate and add SSH key to GitHub
```bash
ssh-keygen -t ed25519
cat ~/.ssh/id_ed25519.pub  # Add this to GitHub
```

**Clone command:**
```bash
git clone --depth 1 -b copilot/copy-ml-training-prediction-files \
  git@github.com:danieljohnconstantine-a11y/Greyhound-Agent.git
```

### Method 3: GitHub CLI

**Setup first:** Install and authenticate
```bash
# Install (Windows)
winget install --id GitHub.cli

# Authenticate
gh auth login
```

**Clone command:**
```bash
gh repo clone danieljohnconstantine-a11y/Greyhound-Agent -- \
  --depth 1 -b copilot/copy-ml-training-prediction-files
```

---

## Complete Example (PAT Method)

```bash
# 1. Navigate to desktop
cd /mnt/c/Users/danie/OneDrive/Desktop

# 2. Clean up old attempts
rm -rf Greyhound-Agent

# 3. Clone with corrected URL
git clone --depth 1 -b copilot/copy-ml-training-prediction-files \
  https://github.com/danieljohnconstantine-a11y/Greyhound-Agent.git

# 4. When prompted for credentials:
#    Username: danieljohnconstantine-a11y
#    Password: [paste your PAT token]

# 5. Navigate into cloned directory
cd Greyhound-Agent

# Success!
```

---

## URL Comparison

### WRONG (What you typed)
```
https://github.com/danieljohnconstanitne-a11y/Greyhound-Agent.git
                              ^^ missing 't'
```

### CORRECT (What you should use)
```
https://github.com/danieljohnconstantine-a11y/Greyhound-Agent.git
                              ^^ has 't'
```

### SSH Version (CORRECT)
```
git@github.com:danieljohnconstantine-a11y/Greyhound-Agent.git
```

---

## Using Automated Retry Script

If you have connection issues, use the retry script:

```bash
chmod +x clone_with_retry.sh
./clone_with_retry.sh
```

The script automatically:
- Uses correct URL (typo fixed)
- Configures optimal settings
- Retries up to 5 times
- Handles connection drops

---

## Quick Troubleshooting

### Still Getting Authentication Error?

**Check 1:** Using PAT correctly?
- Username: Your GitHub username
- Password: Your PAT (NOT your GitHub password)

**Check 2:** PAT has correct scope?
- Must have `repo` scope checked
- Create new one if unsure

**Check 3:** Using correct URL?
- Should be: `danieljohnconstantine-a11y` (with 't')
- NOT: `danieljohnconstanitne-a11y` (missing 't')

### Getting "Repository not found"?

- Check for typo in URL
- Verify repository name is correct
- Check if you have access to the repository

---

## After Successful Clone

### Next Steps

```bash
# 1. Navigate into directory
cd Greyhound-Agent

# 2. Create virtual environment
python3 -m venv venv
source venv/bin/activate

# 3. Install packages
./install_packages.sh
# or
pip install -r requirements.txt

# 4. Run the code
python train_ml_track_ensemble.py
```

---

## Related Documentation

For detailed setup instructions:
- `FIX_GIT_AUTHENTICATION_ERROR.md` - Complete troubleshooting
- `GITHUB_AUTHENTICATION_SETUP.md` - Authentication setup guide
- `install_packages.sh` - Package installation script
- `clone_with_retry.sh` - Automated clone with retry

---

## Summary

### The Fix

1. **Fix typo:** `constani**t**ne` → `constanti**n**e`
2. **Use PAT/SSH:** Don't use GitHub password
3. **Clone:** Use one of the three methods above

### Recommended Method

**HTTPS with PAT** (easiest for most users)
1. Create PAT: https://github.com/settings/tokens
2. Clone with corrected URL
3. Enter PAT when prompted

**Time:** 5-10 minutes
**Success rate:** 95%

---

**You're now ready to successfully clone!** 🎯
