#!/bin/bash

################################################################################
# Ubuntu Virtual Environment Setup Script
# For Greyhound ML Training - Handles Large Files
################################################################################

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
REPO_URL="https://github.com/danieljohnconstantine-a11y/Greyhound-Agent.git"
BRANCH="copilot/copy-ml-training-prediction-files-again"
REPO_DIR="Greyhound-Agent"
VENV_DIR="venv"

################################################################################
# Helper Functions
################################################################################

print_step() {
    echo -e "${BLUE}==>${NC} ${GREEN}$1${NC}"
}

print_info() {
    echo -e "${YELLOW}ℹ${NC}  $1"
}

print_success() {
    echo -e "${GREEN}✓${NC}  $1"
}

print_error() {
    echo -e "${RED}✗${NC}  $1"
}

################################################################################
# Main Setup
################################################################################

echo -e "${GREEN}"
echo "╔════════════════════════════════════════════════════════════╗"
echo "║   Greyhound ML Training - Ubuntu Virtual Environment Setup  ║"
echo "╚════════════════════════════════════════════════════════════╝"
echo -e "${NC}"

# Step 1: Check and install prerequisites
print_step "Step 1/5: Installing prerequisites..."
print_info "This will install git, python3, python3-pip, and python3-venv"

sudo apt update -qq
sudo apt install -y git python3 python3-pip python3-venv > /dev/null 2>&1

# Verify installations
if command -v git &> /dev/null && command -v python3 &> /dev/null; then
    print_success "Prerequisites installed: git $(git --version | awk '{print $3}'), python $(python3 --version | awk '{print $2}')"
else
    print_error "Failed to install prerequisites"
    exit 1
fi

# Step 2: Clone repository
print_step "Step 2/5: Cloning repository (shallow clone for speed)..."
print_info "This may take 2-5 minutes depending on your connection"

# Remove existing directory if present
if [ -d "$REPO_DIR" ]; then
    print_info "Removing existing $REPO_DIR directory..."
    rm -rf "$REPO_DIR"
fi

# Clone with depth 1 (shallow clone - faster for large repos)
if git clone --depth 1 -b "$BRANCH" "$REPO_URL" "$REPO_DIR"; then
    print_success "Repository cloned successfully (~200 MB downloaded)"
else
    print_error "Failed to clone repository"
    print_info "Try running: git config --global http.postBuffer 524288000"
    exit 1
fi

cd "$REPO_DIR"

# Step 3: Create virtual environment
print_step "Step 3/5: Creating Python virtual environment..."
print_info "This isolates dependencies and helps manage memory for large files"

if python3 -m venv "$VENV_DIR"; then
    print_success "Virtual environment created at $REPO_DIR/$VENV_DIR"
else
    print_error "Failed to create virtual environment"
    exit 1
fi

# Step 4: Activate virtual environment and install dependencies
print_step "Step 4/5: Installing Python dependencies in virtual environment..."
print_info "Installing: pandas, numpy, scikit-learn, xgboost, pdfplumber, openpyxl"

# Activate venv
source "$VENV_DIR/bin/activate"

# Upgrade pip
pip install --upgrade pip --quiet

# Install dependencies
if pip install pandas numpy scikit-learn xgboost pdfplumber openpyxl --quiet; then
    print_success "Dependencies installed successfully"
else
    print_error "Failed to install dependencies"
    exit 1
fi

# Step 5: Verify setup
print_step "Step 5/5: Verifying setup..."

# Check venv is active
if [[ "$VIRTUAL_ENV" != "" ]]; then
    print_success "Virtual environment active: $VIRTUAL_ENV"
else
    print_error "Virtual environment not active"
    exit 1
fi

# Check key directories exist
if [ -d "data" ] && [ -d "models" ] && [ -d "src" ]; then
    print_success "Repository structure verified (data/, models/, src/)"
else
    print_error "Repository structure incomplete"
    exit 1
fi

# Check Python packages
if python -c "import pandas, numpy, sklearn, xgboost" 2>/dev/null; then
    print_success "Python packages verified"
else
    print_error "Some Python packages missing"
    exit 1
fi

echo ""
echo -e "${GREEN}╔════════════════════════════════════════════════════════════╗"
echo -e "║                    SETUP COMPLETE! ✓                        ║"
echo -e "╚════════════════════════════════════════════════════════════╝${NC}"
echo ""

# Print next steps
echo -e "${YELLOW}📝 NEXT STEPS:${NC}"
echo ""
echo "1. Navigate to repository:"
echo -e "   ${BLUE}cd $(pwd)${NC}"
echo ""
echo "2. Activate virtual environment (if not already active):"
echo -e "   ${BLUE}source venv/bin/activate${NC}"
echo ""
echo "3. Train ALL models (sigmoid calibration — required for predictions):"
echo -e "   ${BLUE}bash train_ubuntu.sh${NC}"
echo "   (Trains RF + GB + XGB for every track. Duration: ~20 minutes.)"
echo ""
echo "4. After training completes, push models to GitHub:"
echo -e "   ${BLUE}git add models/*.pkl${NC}"
echo -e "   ${BLUE}git commit -m 'retrain all tracks: sigmoid calibration'${NC}"
echo -e "   ${BLUE}git push${NC}"
echo "   (Then on Windows: git pull, and double-click run_track_ensemble_predictions.bat)"
echo ""
echo "5. When done, deactivate virtual environment:"
echo -e "   ${BLUE}deactivate${NC}"
echo ""
echo -e "${YELLOW}📊 WHAT YOU HAVE:${NC}"
echo "  • Repository: $(pwd)"
echo "  • Virtual environment: $(pwd)/venv"
echo "  • Data: 700+ race PDFs and CSV files"
echo "  • Source code: Python modules in src/"
echo ""
echo -e "${YELLOW}💡 UBUNTU → WINDOWS WORKFLOW:${NC}"
echo "  1. Train on Ubuntu:   bash train_ubuntu.sh"
echo "  2. Push to GitHub:    git add models/*.pkl && git commit -m 'retrain' && git push"
echo "  3. Pull on Windows:   git pull"
echo "  4. Run predictions:   double-click run_track_ensemble_predictions.bat"
echo ""
echo "  Models (.pkl files) are fully cross-platform between Ubuntu and Windows."
echo ""
echo -e "${GREEN}Happy training! 🏁🐕${NC}"
echo ""
