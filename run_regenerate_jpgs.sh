#!/bin/bash
# Regenerate JPG files from TIFFs in For-Import directory

cd "$(dirname "$0")"

# Activate virtual environment
source .venv/bin/activate

# Run the regeneration
python regenerate_jpgs.py

# Deactivate virtual environment
deactivate
