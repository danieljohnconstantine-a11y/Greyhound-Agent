#!/bin/bash

###############################################################################
# Package Installation Script for Unstable Internet Connections
# 
# This script installs Python packages with extended timeouts and retry logic
# Designed for users with slow or unstable internet connections
#
# Usage: chmod +x install_packages.sh && ./install_packages.sh
###############################################################################

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
TIMEOUT=300  # 5 minutes per read
RETRIES=10   # Number of retry attempts
MAX_ATTEMPTS=5  # Max attempts per package

# Packages to install
PACKAGES=(
    "pandas"
    "numpy"
    "scikit-learn"
    "xgboost"
    "pdfplumber"
    "openpyxl"
)

# Print header
echo -e "${BLUE}═══════════════════════════════════════════════════════════${NC}"
echo -e "${BLUE}  Package Installation Script for Unstable Connections${NC}"
echo -e "${BLUE}═══════════════════════════════════════════════════════════${NC}"
echo ""

# Check if we're in a virtual environment
if [ -z "$VIRTUAL_ENV" ]; then
    echo -e "${YELLOW}⚠ Warning: No virtual environment detected${NC}"
    echo -e "${YELLOW}  It's recommended to use a virtual environment${NC}"
    echo ""
    read -p "Continue anyway? (y/n): " -n 1 -r
    echo ""
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo "Installation cancelled."
        exit 1
    fi
fi

# Configure pip with extended timeouts
echo -e "${BLUE}Configuring pip with extended timeouts ($TIMEOUT seconds)...${NC}"
pip config set --user global.timeout $TIMEOUT 2>/dev/null || true

echo -e "${BLUE}Configuring pip with increased retry attempts ($RETRIES retries)...${NC}"
pip config set --user global.retries $RETRIES 2>/dev/null || true

echo -e "${GREEN}✓ Configuration complete!${NC}"
echo ""

# Install packages one by one with retry logic
echo -e "${BLUE}Installing packages one-by-one with retry logic...${NC}"
echo ""

FAILED_PACKAGES=()
INSTALLED_COUNT=0
TOTAL_PACKAGES=${#PACKAGES[@]}

for i in "${!PACKAGES[@]}"; do
    PACKAGE="${PACKAGES[$i]}"
    INDEX=$((i + 1))
    
    echo -e "${BLUE}─────────────────────────────────────────────────────────${NC}"
    echo -e "${BLUE}Installing package $INDEX/$TOTAL_PACKAGES: $PACKAGE${NC}"
    echo -e "${BLUE}─────────────────────────────────────────────────────────${NC}"
    
    SUCCESS=0
    for ATTEMPT in $(seq 1 $MAX_ATTEMPTS); do
        echo -e "Attempt $ATTEMPT/$MAX_ATTEMPTS: pip install --timeout $TIMEOUT $PACKAGE"
        
        if pip install --timeout $TIMEOUT --retries $RETRIES "$PACKAGE" 2>&1 | tee /tmp/pip_install_$PACKAGE.log; then
            echo -e "${GREEN}✓ Successfully installed $PACKAGE${NC}"
            SUCCESS=1
            INSTALLED_COUNT=$((INSTALLED_COUNT + 1))
            break
        else
            echo -e "${RED}✗ Attempt $ATTEMPT failed${NC}"
            if [ $ATTEMPT -lt $MAX_ATTEMPTS ]; then
                echo -e "${YELLOW}Waiting 5 seconds before retry...${NC}"
                sleep 5
            fi
        fi
    done
    
    if [ $SUCCESS -eq 0 ]; then
        echo -e "${RED}✗ Failed to install $PACKAGE after $MAX_ATTEMPTS attempts${NC}"
        FAILED_PACKAGES+=("$PACKAGE")
    fi
    
    echo ""
done

# Print summary
echo -e "${BLUE}═══════════════════════════════════════════════════════════${NC}"
echo -e "${BLUE}  Installation Summary${NC}"
echo -e "${BLUE}═══════════════════════════════════════════════════════════${NC}"

for PACKAGE in "${PACKAGES[@]}"; do
    if [[ " ${FAILED_PACKAGES[@]} " =~ " ${PACKAGE} " ]]; then
        echo -e "${RED}✗ $PACKAGE - Failed to install${NC}"
    else
        echo -e "${GREEN}✓ $PACKAGE - Installed successfully${NC}"
    fi
done

echo ""

if [ ${#FAILED_PACKAGES[@]} -eq 0 ]; then
    echo -e "${GREEN}Success: All $TOTAL_PACKAGES packages installed!${NC}"
    echo ""
    echo -e "${BLUE}Next steps:${NC}"
    echo "1. Verify installation:"
    echo "   python -c \"import pandas, numpy, sklearn, xgboost, pdfplumber, openpyxl; print('All packages work!')\""
    echo ""
    echo "2. Run the prediction system:"
    echo "   python run_track_ensemble_predictions.py"
    echo ""
    exit 0
else
    echo -e "${RED}Warning: ${#FAILED_PACKAGES[@]} package(s) failed to install${NC}"
    echo -e "${YELLOW}Failed packages: ${FAILED_PACKAGES[*]}${NC}"
    echo ""
    echo -e "${YELLOW}Troubleshooting:${NC}"
    echo "1. Check your internet connection"
    echo "2. Try again later (different time of day)"
    echo "3. Install failed packages individually:"
    for PACKAGE in "${FAILED_PACKAGES[@]}"; do
        echo "   pip install --timeout 600 --retries 20 $PACKAGE"
    done
    echo ""
    echo "4. See PIP_INSTALL_TIMEOUT_SOLUTION.md for more options"
    echo ""
    exit 1
fi
