#!/bin/bash
# Train ML models on historical data

echo "====================================="
echo " TRAINING GREYHOUND PREDICTION MODELS"
echo "====================================="
echo

# Check Python
if ! command -v python3 &> /dev/null; then
    echo "ERROR: Python 3 not found"
    exit 1
fi

# Check data folder
if [ ! -d "data" ] || [ -z "$(ls -A data/*.pdf 2>/dev/null)" ]; then
    echo "ERROR: No training PDFs in data/ folder"
    exit 1
fi

echo "Installing dependencies..."
pip3 install -r requirements.txt

echo
echo "Training models (this may take 30-60 minutes)..."
python3 -c "from src.main import train_models; train_models('data')"

echo
echo "====================================="
echo " TRAINING COMPLETE!"
echo "====================================="
echo "Models saved to models/ directory"
