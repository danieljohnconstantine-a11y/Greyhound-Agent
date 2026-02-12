# 🐧 SUPER BASIC Ubuntu Guide - Download the Code

**For Complete Beginners - Just 3 Steps!**

---

## What You Need
- A computer running Ubuntu (any version)
- Internet connection
- 5 minutes

---

## Step 1: Open Terminal

**What is Terminal?**
Terminal is where you type commands. It's a black window with text.

**How to Open It:**
1. Press `Ctrl` + `Alt` + `T` on your keyboard at the same time
2. OR: Click the grid icon (bottom left) → Type "terminal" → Click Terminal

**What You'll See:**
A window with text like this:
```
username@computer:~$
```

✅ **You're ready for Step 2!**

---

## Step 2: Install Git (The Download Tool)

**What is Git?**
Git is a tool that downloads code from the internet.

**What to Type:**
Copy and paste this into Terminal, then press Enter:

```bash
sudo apt install git -y
```

**What Happens:**
- You might see: `[sudo] password for username:`
- Type your computer password (you won't see it as you type - that's normal!)
- Press Enter
- You'll see lots of text scrolling - this is normal!
- Wait 1-2 minutes

**How to Know It Worked:**
When you see `username@computer:~$` again, it's done!

✅ **Git is installed!**

---

## Step 3: Download the Code

**What to Type:**
Copy and paste this into Terminal, then press Enter:

```bash
git clone -b copilot/copy-ml-training-prediction-files https://github.com/danieljohnconstantine-a11y/Greyhound-Agent.git
```

**What Happens:**
- You'll see: `Cloning into 'Greyhound-Agent'...`
- Then a progress bar showing download
- This takes 2-5 minutes (353 MB downloading)
- You'll see percentages: 10%, 20%, 30%...

**How to Know It Worked:**
You'll see this at the end:
```
Receiving objects: 100% 
Resolving deltas: 100%
done.
```

✅ **Code downloaded!**

---

## 🎉 YOU'RE DONE!

### Where Is the Code?

Type this to see it:
```bash
cd Greyhound-Agent
ls
```

You'll see all the files listed!

### What You Downloaded:

- 📁 **data/** - Race information
- 📁 **models/** - Trained AI models  
- 📁 **src/** - Python code
- 📄 **train_ml_track_ensemble.py** - Training script
- 📄 **run_track_ensemble_predictions.py** - Prediction script

---

## What's Next?

### Want to Run the Predictions?

1. Make sure you're in the Greyhound-Agent folder:
   ```bash
   cd Greyhound-Agent
   ```

2. Install Python tools:
   ```bash
   sudo apt install python3 python3-pip -y
   pip3 install pandas numpy scikit-learn
   ```

3. Run predictions:
   ```bash
   python3 run_track_ensemble_predictions.py
   ```

### Want More Help?

See these guides:
- **UBUNTU_TRAINING_GUIDE.md** - Complete training guide
- **README.md** - Full documentation

---

## Troubleshooting

### "Command not found"
**Problem:** Terminal says `git: command not found`  
**Solution:** Repeat Step 2 (install git)

### "Permission denied"
**Problem:** Terminal says `Permission denied`  
**Solution:** Type your password when asked (you won't see it as you type)

### Download is Slow
**Problem:** Taking forever to download  
**Solution:** This is normal! File is 353 MB. Be patient. Could take 5-10 minutes on slow internet.

### Still Stuck?
Type this to see if Git is installed:
```bash
git --version
```

You should see something like: `git version 2.25.1`

---

## Quick Summary

**The 3 Commands:**
```bash
# 1. Install Git
sudo apt install git -y

# 2. Download Code  
git clone -b copilot/copy-ml-training-prediction-files https://github.com/danieljohnconstantine-a11y/Greyhound-Agent.git

# 3. Check It Worked
cd Greyhound-Agent
ls
```

**Total Time:** 5-10 minutes

**What You Get:** 353 MB of code, data, and AI models ready to use!

---

## 🎯 Success Checklist

- ✅ Terminal opened
- ✅ Git installed (saw `[sudo] password`)
- ✅ Code downloaded (saw `Receiving objects: 100%`)
- ✅ Folder exists (can `cd Greyhound-Agent`)

**You did it!** 🎉

---

**Need Even More Help?** Open an issue on GitHub and we'll help you!
