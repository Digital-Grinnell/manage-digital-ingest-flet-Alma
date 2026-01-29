#!/bin/bash
# Run the white JPG analysis script with the project's virtual environment

cd "$(dirname "$0")"

# Activate virtual environment
source .venv/bin/activate

# Run the analysis
python analyze_white_jpgs.py

# Deactivate virtual environment
deactivate
