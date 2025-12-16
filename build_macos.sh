#!/bin/bash

# build_macos.sh - Build macOS app bundle for Manage Digital Ingest
# This script creates a standalone .app that can be installed in Applications

set -e  # Exit on error

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${BLUE}=== Building Manage Digital Ingest for macOS ===${NC}"

# Get the directory where the script is located
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

VENV_DIR=".venv"

# Check if virtual environment exists
if [ ! -d "$VENV_DIR" ]; then
    echo -e "${YELLOW}Virtual environment not found. Creating .venv...${NC}"
    python3 -m venv "$VENV_DIR"
    echo -e "${GREEN}✓ Virtual environment created${NC}"
fi

# Activate virtual environment
echo -e "${BLUE}Activating virtual environment...${NC}"
source "$VENV_DIR/bin/activate"

# Ensure flet is installed
echo -e "${BLUE}Checking Flet installation...${NC}"
if ! pip show flet > /dev/null 2>&1; then
    echo -e "${YELLOW}Installing Flet...${NC}"
    pip install flet
fi

# Build the app
echo -e "${BLUE}Building macOS application bundle...${NC}"
echo -e "${YELLOW}This may take several minutes...${NC}"

flet pack app.py \
    --name "Manage Digital Ingest" \
    --icon assets/favicon-256x256.png

echo ""
echo -e "${GREEN}✓ Build complete!${NC}"
echo -e "${BLUE}App bundle location: ${YELLOW}build/macos/Manage Digital Ingest.app${NC}"
echo ""
echo -e "${BLUE}To install:${NC}"
echo -e "  cp -r 'build/macos/Manage Digital Ingest.app' /Applications/"
echo ""
echo -e "${BLUE}To run:${NC}"
echo -e "  open 'build/macos/Manage Digital Ingest.app'"
echo ""

# Deactivate virtual environment
deactivate
