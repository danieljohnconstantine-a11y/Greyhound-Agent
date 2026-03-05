# GitHub Authentication Setup Guide

Complete guide for setting up GitHub authentication for git operations.

## Table of Contents

1. [Personal Access Token (PAT)](#personal-access-token-pat)
2. [SSH Keys](#ssh-keys)
3. [GitHub CLI](#github-cli)
4. [Credential Storage](#credential-storage)
5. [Troubleshooting](#troubleshooting)

---

## Personal Access Token (PAT)

### What is a PAT?

A Personal Access Token is like a password but more secure:
- Can be scoped (limited permissions)
- Can be revoked easily
- Can have expiration dates
- Required for HTTPS authentication since August 2021

### Creating a PAT

#### Step 1: Navigate to Token Settings

1. Go to https://github.com
2. Log in to your account
3. Click your profile picture (top right corner)
4. Click **Settings**
5. Scroll down to **Developer settings** (bottom of left sidebar)
6. Click **Personal access tokens**
7. Click **Tokens (classic)**

#### Step 2: Generate New Token

1. Click **"Generate new token (classic)"**
2. If prompted, re-enter your GitHub password
3. Fill in the form:
   - **Note:** Give it a descriptive name (e.g., "Greyhound-Agent Access")
   - **Expiration:** Choose duration (90 days recommended, or "No expiration" if you prefer)
   - **Scopes:** Select what this token can access

#### Step 3: Select Scopes

For cloning/pushing repositories, you need:

- ☑️ **repo** (Full control of private repositories)
  - This automatically selects all sub-scopes

Optional additional scopes:
- ☑️ **workflow** (if working with GitHub Actions)
- ☑️ **admin:org** (if managing organizations)

**For most users, just select "repo"**

#### Step 4: Generate and Save Token

1. Scroll down and click **"Generate token"**
2. **IMPORTANT:** Copy the token immediately!
   - Format: `ghp_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx`
   - It's shown only ONCE
   - If you lose it, you must generate a new one

3. **Save it securely:**
   - Password manager (recommended)
   - Secure note
   - Environment variable

### Using Your PAT

When git prompts for credentials:
```
Username: your-github-username
Password: [paste your PAT token]
```

**Important:** Use the PAT as the password, not your GitHub account password!

---

## SSH Keys

### What are SSH Keys?

SSH keys provide secure, passwordless authentication:
- More secure than passwords
- No need to enter credentials
- Preferred by developers
- Works across all systems

### Generating SSH Keys

#### For Linux/WSL/Mac:

```bash
# Generate new SSH key
ssh-keygen -t ed25519 -C "your_email@example.com"

# When prompted:
# - File location: Press Enter (default is fine)
# - Passphrase: Enter one (optional but recommended)
```

#### For Windows (without WSL):

```bash
# In PowerShell or Git Bash
ssh-keygen -t ed25519 -C "your_email@example.com"
```

#### Understanding the Output

```
Generating public/private ed25519 key pair.
Enter file in which to save the key (/home/user/.ssh/id_ed25519):
```

- Default location is fine (press Enter)
- Creates two files:
  - `id_ed25519` - Private key (keep secret!)
  - `id_ed25519.pub` - Public key (safe to share)

### Adding SSH Key to GitHub

#### Step 1: Copy Your Public Key

**Linux/WSL/Mac:**
```bash
cat ~/.ssh/id_ed25519.pub
```

**Windows (PowerShell):**
```powershell
Get-Content ~/.ssh/id_ed25519.pub
```

Copy the entire output (starts with `ssh-ed25519...`)

#### Step 2: Add to GitHub

1. Go to https://github.com
2. Click profile picture → **Settings**
3. **SSH and GPG keys** (left sidebar)
4. Click **"New SSH key"**
5. Fill in:
   - **Title:** Descriptive name (e.g., "My Laptop")
   - **Key type:** Authentication Key
   - **Key:** Paste your public key
6. Click **"Add SSH key"**
7. Confirm with your GitHub password if prompted

### Testing SSH Connection

```bash
ssh -T git@github.com
```

Expected output:
```
Hi username! You've successfully authenticated, but GitHub does not provide shell access.
```

If successful, you're ready to use SSH URLs!

### Using SSH for Cloning

```bash
# SSH URL format
git clone git@github.com:username/repository.git

# Example
git clone git@github.com:danieljohnconstantine-a11y/Greyhound-Agent.git
```

---

## GitHub CLI

### What is GitHub CLI?

Official command-line tool from GitHub:
- Handles authentication automatically
- Simplifies git operations
- Modern and recommended
- Easiest setup

### Installation

#### Windows

**Option 1: Using winget**
```bash
winget install --id GitHub.cli
```

**Option 2: Using scoop**
```bash
scoop install gh
```

**Option 3: Download installer**
- Visit https://cli.github.com/
- Download Windows installer
- Run and follow prompts

#### Mac

```bash
brew install gh
```

#### Linux (Ubuntu/Debian)

```bash
# Add repository
curl -fsSL https://cli.github.com/packages/githubcli-archive-keyring.gpg | sudo dd of=/usr/share/keyrings/githubcli-archive-keyring.gpg

# Add to sources
echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/githubcli-archive-keyring.gpg] https://cli.github.com/packages stable main" | sudo tee /etc/apt/sources.list.d/github-cli.list > /dev/null

# Install
sudo apt update
sudo apt install gh
```

#### Linux (Fedora/RHEL)

```bash
sudo dnf install gh
```

### Authentication

```bash
gh auth login
```

Follow the interactive prompts:
1. **What account?** → GitHub.com
2. **Protocol?** → HTTPS (recommended) or SSH
3. **Authenticate?** → Login with a web browser
4. Copy the one-time code shown
5. Press Enter to open browser
6. Paste code in browser
7. Authorize GitHub CLI

### Using GitHub CLI

#### Clone Repository

```bash
gh repo clone username/repository

# With branch and depth
gh repo clone danieljohnconstantine-a11y/Greyhound-Agent -- --depth 1 -b branch-name
```

#### Other Useful Commands

```bash
# Check authentication status
gh auth status

# View repositories
gh repo list

# Create pull request
gh pr create

# View issues
gh issue list
```

---

## Credential Storage

### Why Cache Credentials?

Avoid re-entering PAT or SSH passphrase every time.

### For HTTPS (PAT)

#### Linux/WSL

**Option 1: Store permanently (less secure)**
```bash
git config --global credential.helper store
```

Credentials stored in plain text at `~/.git-credentials`

**Option 2: Cache for session (more secure)**
```bash
git config --global credential.helper cache
# Default: 15 minutes

# Or specify timeout (in seconds)
git config --global credential.helper 'cache --timeout=3600'  # 1 hour
```

#### Windows

```bash
git config --global credential.helper wincred
```

Uses Windows Credential Manager (secure)

#### Mac

```bash
git config --global credential.helper osxkeychain
```

Uses macOS Keychain (secure)

### For SSH Keys

#### Using ssh-agent (Automatic Loading)

**Linux/WSL:**

Add to `~/.bashrc` or `~/.zshrc`:
```bash
# Start ssh-agent
eval "$(ssh-agent -s)"

# Add key
ssh-add ~/.ssh/id_ed25519
```

**Windows (Git Bash):**

Add to `~/.bash_profile`:
```bash
env=~/.ssh/agent.env

agent_load_env () { test -f "$env" && . "$env" >| /dev/null ; }

agent_start () {
    (umask 077; ssh-agent >| "$env")
    . "$env" >| /dev/null ; }

agent_load_env

# agent_run_state: 0=agent running w/ key; 1=agent w/o key; 2=agent not running
agent_run_state=$(ssh-add -l >| /dev/null 2>&1; echo $?)

if [ ! "$SSH_AUTH_SOCK" ] || [ $agent_run_state = 2 ]; then
    agent_start
    ssh-add ~/.ssh/id_ed25519
elif [ "$SSH_AUTH_SOCK" ] && [ $agent_run_state = 1 ]; then
    ssh-add ~/.ssh/id_ed25519
fi

unset env
```

---

## Troubleshooting

### PAT Issues

#### "Invalid username or token"

**Problem:** PAT is incorrect or expired

**Solutions:**
1. Check if PAT is copied correctly (no extra spaces)
2. Verify PAT hasn't expired
3. Confirm PAT has `repo` scope
4. Generate new PAT if needed

#### Test PAT validity

```bash
curl -H "Authorization: token YOUR_PAT_HERE" https://api.github.com/user
```

Should return your user information.

### SSH Issues

#### "Permission denied (publickey)"

**Problem:** SSH key not recognized

**Solutions:**
1. Check if key is added to GitHub:
   ```bash
   ssh -T git@github.com
   ```

2. Check if key is loaded:
   ```bash
   ssh-add -l
   ```

3. Add key manually:
   ```bash
   ssh-add ~/.ssh/id_ed25519
   ```

4. Check SSH config:
   ```bash
   cat ~/.ssh/config
   ```

   Should include:
   ```
   Host github.com
       HostName github.com
       User git
       IdentityFile ~/.ssh/id_ed25519
   ```

#### "Could not open a connection to your authentication agent"

**Problem:** ssh-agent not running

**Solution:**
```bash
eval "$(ssh-agent -s)"
ssh-add ~/.ssh/id_ed25519
```

### GitHub CLI Issues

#### "Not logged in"

**Solution:**
```bash
gh auth logout
gh auth login
```

Follow prompts to re-authenticate.

#### "Command not found"

**Solution:**
- Reinstall GitHub CLI
- Check if in PATH
- Restart terminal

---

## Security Best Practices

### For PATs

1. **Use minimal scopes** - Only select what you need
2. **Set expiration** - Use 90 days or less
3. **Rotate regularly** - Generate new tokens periodically
4. **Revoke unused tokens** - Clean up old tokens
5. **Never commit tokens** - Don't put in code or configs
6. **Use secure storage** - Password manager recommended

### For SSH Keys

1. **Use passphrase** - Protects private key if stolen
2. **Use ed25519** - Modern, more secure than RSA
3. **Keep private key private** - Never share `id_ed25519`
4. **Use different keys** - Different key per device
5. **Remove old keys** - Delete from GitHub when device retired

---

## Summary

### Quick Recommendations

**For beginners:**
- Use Personal Access Token (PAT)
- Easy to understand
- Works everywhere

**For developers:**
- Use SSH keys
- Better security
- No password prompts
- Industry standard

**For convenience:**
- Use GitHub CLI
- Easiest setup
- Handles everything

---

## Related Documentation

- `FIX_GIT_AUTHENTICATION_ERROR.md` - Troubleshooting guide
- `CORRECT_CLONE_COMMANDS.md` - Quick command reference
- `clone_with_retry.sh` - Automated clone script

---

**You're now ready to authenticate with GitHub!** 🎯
