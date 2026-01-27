#!/bin/bash

# run_tiff_converter.sh - Launch script for TIFF to JPG Batch Converter
# This script activates the virtual environment and runs the converter

set -e  # Exit on error

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${BLUE}=== TIFF to JPG Batch Converter ===${NC}"

# Get the directory where the script is located
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

# Check if virtual environment exists
if [ ! -d ".venv" ]; then
    echo -e "${RED}Error: Virtual environment not found at .venv${NC}"
    echo -e "${YELLOW}Please create it first:${NC}"
    echo -e "  python3 -m venv .venv"
    echo -e "  source .venv/bin/activate"
    echo -e "  pip install -r python-requirements.txt"
    exit 1
fi

# Activate virtual environment
echo -e "${GREEN}Activating virtual environment...${NC}"
source .venv/bin/activate

# Check for required dependencies
echo -e "${GREEN}Checking dependencies...${NC}"
python3 -c "import PIL" 2>/dev/null || {
    echo -e "${YELLOW}Installing Pillow...${NC}"
    pip install Pillow
}

python3 -c "import boto3" 2>/dev/null || {
    echo -e "${YELLOW}Installing boto3...${NC}"
    pip install boto3
}

# Check AWS credentials
echo -e "${GREEN}Checking AWS credentials...${NC}"
if ! aws sts get-caller-identity &>/dev/null; then
    echo -e "${YELLOW}Warning: AWS credentials not configured or invalid${NC}"
    echo -e "${YELLOW}Configure with: aws configure${NC}"
    echo -e "${YELLOW}Or set environment variables: AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY${NC}"
    echo ""
    read -p "Continue anyway? (y/N) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

echo ""
echo -e "${GREEN}Starting TIFF to JPG conversion...${NC}"
echo ""

# Run the converter script
python3 tiff_to_jpg_batch_converter.py

# Deactivate virtual environment
deactivate

echo ""
echo -e "${GREEN}Done!${NC}"
