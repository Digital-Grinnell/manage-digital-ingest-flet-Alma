# Manage Digital Ingest: Alma Edition

A Flet-based Python application for managing Grinnell College ingest of digital objects to Alma Digital.

> **📖 New to this application?** Start with the [USER-GUIDE.md](USER-GUIDE.md) for comprehensive workflow instructions and troubleshooting.

## 🚀 Quick Start

### Running the Application

The easiest way to run the application is using the provided `run.sh` script:

```bash
./run.sh
```

**What it does:**
1. Checks if a Python virtual environment (`.venv`) exists
2. Creates the virtual environment if it doesn't exist
3. Activates the virtual environment
4. Installs/upgrades required dependencies from `python-requirements.txt`
5. Launches the Flet application

**First-time setup:**
```bash
chmod +x run.sh  # Make the script executable (only needed once)
./run.sh         # Run the application
```

**Requirements:**
- Python 3.7 or higher
- Bash shell (macOS, Linux, or Windows with Git Bash/WSL)

## 📖 Overview

This Alma-specific version of Manage Digital Ingest helps you:

- Prepare digital image collections for ingest into Alma Digital
- Match CSV metadata with corresponding image files using fuzzy search
- Generate derivative images (thumbnails for Alma)
- Update CSV files with Alma-specific metadata (compound objects, collection IDs)
- Generate AWS S3 upload scripts for Alma ingest
- Maintain session state across multiple work sessions

## 🎯 Key Features for Alma

- **Alma Workflow Only**: Configured specifically for Alma Digital workflows
- **Fuzzy Filename Matching**: Automatically matches images to CSV metadata entries with numeric-only difference penalty
- **CSV Metadata Generator**: Create initial CSV rows from selected files with Alma-D structure
- **CSV Metadata Merge**: Upload existing metadata CSV and merge it into generated rows
- **Alma Derivative Generation**: Creates thumbnails (200x200) with `.jpg.clientThumb` extension
- **Compound Object Support**: Handles parent/child relationships with automatic TOC generation
- **Collection ID Management**: Populates collection_id fields for Alma
- **AWS S3 Integration**: Generates upload scripts for Alma S3 buckets
- **Session Preservation**: Save your work and resume later

## 📋 Alma Workflow

1. **Settings**: App is pre-configured for Alma mode
2. **File Selector**: Choose files using FilePicker or load CSV with metadata and match files
3. **CSV Generator** (Optional): Generate initial CSV metadata rows from selected files, or upload existing metadata and merge
4. **Create Derivatives**: Generate Alma thumbnails (TN directory with .clientThumb extension)
5. **Update CSV**: Apply Alma-specific metadata updates (compound objects, collection IDs)
6. **Instructions**: View final workflow instructions with AWS S3 upload details

## 📄 Required CSV Columns for Alma

See `_data/verified_CSV_headings_for_Alma-D.csv` for the complete list of valid column headings for Alma workflows.

## 🔧 Configuration

The app automatically sets the mode to "Alma" - no mode selection needed. Configure:
- File selection method (FilePicker or CSV)
- Azure storage settings
- Theme (Light/Dark)

## 📚 Documentation

### Comprehensive Guides

- **[USER-GUIDE.md](USER-GUIDE.md)** - Complete user guide with step-by-step Alma workflow, troubleshooting, and best practices
- **[ALMA-COMPOUND-HANDLING.md](ALMA-COMPOUND-HANDLING.md)** - Detailed documentation on parent/child compound object processing
- **[DEPLOYMENT-SETUP.md](DEPLOYMENT-SETUP.md)** - Installation, deployment, configuration, and maintenance guide
- **[DEVELOPMENT-HISTORY.md](DEVELOPMENT-HISTORY.md)** - Feature development timeline and technical architecture

### Quick Reference

- `_data/verified_CSV_headings_for_Alma-D.csv` - Valid CSV column headings
- `_data/alma_aws_s3.md` - AWS S3 upload instructions
- `mdi.log` - Application log file (auto-generated)

## 🏢 About

Developed for Grinnell College Libraries to streamline the digital object ingest process for Alma Digital.
