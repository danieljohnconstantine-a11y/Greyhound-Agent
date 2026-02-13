#!/bin/bash
# Quick Clone Script for Linux/WSL Users
# This script downloads the repository using shallow clone to avoid timeout issues

echo "==============================================="
echo " Greyhound-Agent Quick Clone Script"
echo " Fixes: 'Connection timed out' errors"
echo "==============================================="
echo ""

# Check if running in correct directory
echo "Current directory: $(pwd)"
echo ""
echo "This will clone the repository to the current directory."
read -p "Press Enter to continue or Ctrl+C to cancel..."

echo ""
echo "[1/4] Cleaning up any previous failed clones..."
if [ -d "Greyhound-Agent" ]; then
    echo "Removing existing Greyhound-Agent directory..."
    rm -rf Greyhound-Agent
fi

echo ""
echo "[2/4] Configuring git for large downloads..."
git config --global http.postBuffer 524288000
git config --global core.compression 0
git config --global http.lowSpeedLimit 0
git config --global http.lowSpeedTime 999999

echo ""
echo "[3/4] Cloning repository (shallow clone - much faster!)..."
echo "This downloads only the latest version without full history."
echo "Expected download: ~50-100MB instead of ~353MB"
git clone --depth 1 -b copilot/copy-ml-training-prediction-files https://github.com/danieljohnconstantine-a11y/Greyhound-Agent.git

if [ $? -ne 0 ]; then
    echo ""
    echo "==============================================="
    echo "ERROR: Clone failed!"
    echo "==============================================="
    echo ""
    echo "Try these alternatives:"
    echo "1. Check your internet connection"
    echo "2. Try again during off-peak hours"
    echo "3. Download as ZIP from GitHub:"
    echo "   https://github.com/danieljohnconstantine-a11y/Greyhound-Agent"
    echo "   (Switch to branch: copilot/copy-ml-training-prediction-files)"
    echo "   Click Code -> Download ZIP"
    echo ""
    exit 1
fi

echo ""
echo "[4/4] Verifying clone..."
cd Greyhound-Agent
if [ ! -f "train_ml_track_ensemble.py" ]; then
    echo "WARNING: Some files may be missing!"
    cd ..
    exit 1
fi

echo ""
echo "==============================================="
echo " SUCCESS! Repository cloned successfully"
echo "==============================================="
echo ""
echo "Location: $(pwd)"
echo ""
echo "Next steps:"
echo "1. Install dependencies: pip install -r requirements.txt"
echo "2. Run validation: python test_complete_pipeline.py"
echo "3. Generate predictions: python run_track_ensemble_predictions.py"
echo ""
echo "See README_100_PERCENT_CONFIDENCE.txt for more information."
echo ""
