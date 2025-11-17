# Deployment and Setup Guide

This document provides instructions for deploying and setting up the Manage Digital Ingest application for Alma Digital workflows.

## Overview

The **Manage Digital Ingest for Alma** application is a standalone Python/Flet application designed specifically for preparing and uploading digital objects to Alma Digital via AWS S3.

## System Requirements

### Operating Systems
- macOS 10.14 or later
- Linux (Ubuntu 20.04+, Fedora 35+, or equivalent)
- Windows 10/11 (with some limitations)

### Software Requirements
- **Python**: 3.9 or later (3.13.3 recommended)
- **pip**: Latest version
- **Git**: For version control and deployment
- **AWS CLI**: For S3 uploads (optional but recommended)

### Hardware Requirements
- **RAM**: 4GB minimum, 8GB recommended
- **Disk Space**: 10GB minimum for application and temp files
- **Display**: 1280x800 minimum resolution

---

## Installation

### 1. Clone the Repository

```bash
git clone https://github.com/Digital-Grinnell/manage-digital-ingest-flet-Alma.git
cd manage-digital-ingest-flet-Alma
```

### 2. Create Virtual Environment

```bash
python3 -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
```

### 3. Install Dependencies

```bash
pip install -r python-requirements.txt
```

### 4. Verify Installation

```bash
python --version  # Should show Python 3.9+
pip list | grep flet  # Should show flet 0.28.2
```

---

## Configuration

### Application Configuration Files

The application uses several configuration files in the `_data/` directory:

#### `_data/config.json`
General application configuration:
```json
{
  "app_name": "Manage Digital Ingest",
  "version": "2.0",
  "mode": "Alma"
}
```

#### `_data/modes.json`
Mode configuration (Alma-specific):
```json
{
  "current_mode": "Alma",
  "available_modes": ["Alma"]
}
```

#### `_data/persistent.json`
User preferences (automatically managed):
```json
{
  "theme_mode": "light",
  "window_height": 900
}
```

### AWS Configuration

For S3 uploads, configure AWS CLI:

```bash
aws configure
```

Provide:
- **AWS Access Key ID**: Your AWS access key
- **AWS Secret Access Key**: Your AWS secret
- **Default region name**: us-east-1 (or your region)
- **Default output format**: json

Test AWS configuration:
```bash
aws s3 ls s3://na-st01.ext.exlibrisgroup.com/01GCL_INST/upload/
```

---

## Running the Application

### Desktop Mode (Recommended)

```bash
./run.sh
```

Or manually:
```bash
source .venv/bin/activate
flet run app.py
```

### Web Mode

```bash
flet run --web app.py
```

Then open browser to: `http://localhost:8550`

### Development Mode (with hot reload)

```bash
flet run --dev app.py
```

---

## Directory Structure

```
manage-digital-ingest-flet-Alma/
├── app.py                         # Main application entry point
├── logger.py                      # Logging configuration
├── utils.py                       # Utility functions
├── thumbnail.py                   # Thumbnail generation
├── python-requirements.txt        # Python dependencies
├── run.sh                         # Startup script
├── README.md                      # Quick start guide
├── USER-GUIDE.md                  # Comprehensive user documentation
├── ALMA-COMPOUND-HANDLING.md      # Compound object documentation
├── DEPLOYMENT-SETUP.md            # This file
├── .gitignore                     # Git ignore rules
├── views/                         # View modules
│   ├── __init__.py
│   ├── base_view.py               # Abstract base class
│   ├── home_view.py               # Home page
│   ├── about_view.py              # About page with session preservation
│   ├── settings_view.py           # Settings page
│   ├── exit_view.py               # Exit page
│   ├── file_selector_view.py      # File selection and fuzzy matching
│   ├── derivatives_view.py        # Derivative generation
│   ├── storage_view.py            # Storage status
│   ├── instructions_view.py       # Upload instructions and script generation
│   ├── update_csv_view.py         # CSV update logic
│   ├── log_view.py                # Log viewer
│   └── log_overlay.py             # Log overlay component
├── _data/                         # Configuration and reference data
│   ├── config.json                # Application configuration
│   ├── modes.json                 # Mode settings
│   ├── persistent.json            # User preferences
│   ├── file_sources.json          # File source configuration
│   ├── home.md                    # Home page content
│   ├── alma_aws_s3.md             # Instructions content
│   ├── alma_aws_s3.sh             # Upload script template
│   └── verified_CSV_headings_for_Alma-D.csv  # Valid CSV columns
├── assets/                        # Application assets
│   ├── Primary_Libraries.png      # Logo
│   └── update-csv-icon.png        # Icons
└── storage/                       # Runtime storage (git-ignored)
    ├── data/                      # Persistent data
    │   └── persistent_session.json  # Saved sessions
    └── temp/                      # Temporary files
        └── file_selector_*/       # Working directories
```

---

## Deployment to Production

### Option 1: Git-Based Deployment

Recommended for institutional deployment:

```bash
# On production server
git clone https://github.com/Digital-Grinnell/manage-digital-ingest-flet-Alma.git
cd manage-digital-ingest-flet-Alma
python3 -m venv .venv
source .venv/bin/activate
pip install -r python-requirements.txt
```

### Option 2: Package as Executable (PyInstaller)

Create standalone executable:

```bash
# Install PyInstaller
pip install pyinstaller

# Create executable
pyinstaller --onefile --windowed --name="ManageDigitalIngest" app.py

# Executable will be in dist/ directory
```

**Note**: Include `_data/` and `assets/` directories with the executable.

### Option 3: Docker Container

Create `Dockerfile`:

```dockerfile
FROM python:3.13-slim

WORKDIR /app

COPY python-requirements.txt .
RUN pip install --no-cache-dir -r python-requirements.txt

COPY . .

EXPOSE 8550

CMD ["flet", "run", "--web", "--port", "8550", "app.py"]
```

Build and run:

```bash
docker build -t manage-digital-ingest-alma .
docker run -p 8550:8550 manage-digital-ingest-alma
```

---

## Initial Setup Checklist

After installation, complete these setup steps:

### For Administrators

- [ ] Install Python 3.9+ and dependencies
- [ ] Configure AWS CLI with appropriate credentials
- [ ] Test S3 bucket access
- [ ] Create storage directories (`storage/data/`, `storage/temp/`)
- [ ] Set appropriate file permissions
- [ ] Configure backup strategy for `storage/data/`
- [ ] Test application launch
- [ ] Verify CSV validation with sample file

### For Users

- [ ] Launch application and verify it opens
- [ ] Review Home page instructions
- [ ] Check Settings (theme, window size)
- [ ] Prepare sample CSV with verified headings
- [ ] Test fuzzy search with small file set
- [ ] Generate test derivatives
- [ ] Review upload script generation
- [ ] Preserve a test session
- [ ] Restore session and verify

---

## Updating the Application

### From Git Repository

```bash
cd manage-digital-ingest-flet-Alma
git pull origin main
source .venv/bin/activate
pip install --upgrade -r python-requirements.txt
```

### Preserving User Data

User data is stored in:
- `storage/data/persistent_session.json` (saved sessions)
- `_data/persistent.json` (user preferences)
- `storage/temp/` (working files - if session preserved)

**Before updating**: Back up these files if needed.

---

## Versioning

This application follows semantic versioning (MAJOR.MINOR.PATCH):

- **MAJOR**: Incompatible API/workflow changes
- **MINOR**: New features (backward-compatible)
- **PATCH**: Bug fixes (backward-compatible)

**Current Version**: 2.0+

---

## Testing After Deployment

Run through this test workflow to verify installation:

### Test 1: Basic Launch
```bash
./run.sh
```
- ✅ Application opens without errors
- ✅ Home page displays correctly
- ✅ Navigation works

### Test 2: CSV Validation
- ✅ Load sample CSV from `_data/verified_CSV_headings_for_Alma-D.csv`
- ✅ CSV validates successfully
- ✅ Data displays in table

### Test 3: File Selection
- ✅ Browse for image files
- ✅ Fuzzy search executes
- ✅ Files match correctly
- ✅ Copy to temp succeeds

### Test 4: Derivative Generation
- ✅ TN derivatives generate
- ✅ Files appear in TN/ subdirectory
- ✅ Correct dimensions (200px max)

### Test 5: CSV Update
- ✅ Apply all updates executes
- ✅ Before/after comparison shows changes
- ✅ CSV saves successfully
- ✅ values.csv created

### Test 6: Upload Script
- ✅ Script generates successfully
- ✅ AWS commands are correct
- ✅ Copy buttons work
- ✅ Script is executable

### Test 7: Session Preservation
- ✅ Preserve session button works
- ✅ Session file created
- ✅ Restart application
- ✅ Session restores correctly

---

## Troubleshooting Deployment

### Python Version Issues

**Problem**: Application won't run, Python version error

**Solution**:
```bash
# Check Python version
python3 --version

# If too old, install Python 3.13
# On macOS with Homebrew:
brew install python@3.13

# On Ubuntu:
sudo apt install python3.13
```

### Dependency Installation Failures

**Problem**: pip install fails for certain packages

**Solution**:
```bash
# Update pip
pip install --upgrade pip

# Install build tools
# On macOS:
xcode-select --install

# On Ubuntu:
sudo apt install python3-dev build-essential

# Retry installation
pip install -r python-requirements.txt
```

### Flet Import Errors

**Problem**: `ModuleNotFoundError: No module named 'flet'`

**Solution**:
```bash
# Ensure virtual environment is activated
source .venv/bin/activate  # or .venv\Scripts\activate on Windows

# Install flet specifically
pip install flet==0.28.2

# Verify
python -c "import flet; print(flet.__version__)"
```

### AWS CLI Not Found

**Problem**: Upload script fails, AWS CLI not available

**Solution**:
```bash
# Install AWS CLI
# On macOS:
brew install awscli

# On Ubuntu:
sudo apt install awscli

# Or via pip:
pip install awscli

# Verify
aws --version
```

### Permission Denied Errors

**Problem**: Cannot write to storage/ directory

**Solution**:
```bash
# Set appropriate permissions
chmod 755 storage/
chmod 755 storage/data/
chmod 755 storage/temp/

# Or create directories if missing
mkdir -p storage/data storage/temp
```

### macOS Gatekeeper Issues

**Problem**: macOS blocks application from running

**Solution**:
```bash
# Run from terminal initially
./run.sh

# If Python blocked:
# System Preferences → Security & Privacy → Allow

# Or bypass Gatekeeper for development:
xattr -cr /path/to/manage-digital-ingest-flet-Alma
```

---

## Security Considerations

### AWS Credentials

- **Never** commit AWS credentials to Git
- Use AWS CLI configuration or environment variables
- Rotate credentials regularly
- Use IAM roles with minimal required permissions

### File Permissions

- Restrict access to `storage/` directory
- Set appropriate file permissions (644 for files, 755 for directories)
- Be cautious with uploaded CSV files (may contain sensitive metadata)

### Network Security

- When running in web mode, restrict access to localhost or trusted networks
- Use HTTPS if exposing web interface
- Consider firewall rules for production deployment

---

## Backup and Recovery

### What to Back Up

1. **User Data**:
   - `storage/data/persistent_session.json`
   - `_data/persistent.json`

2. **Configuration** (if customized):
   - `_data/config.json`

3. **Working Files** (if session preserved):
   - `storage/temp/file_selector_*/`

### Backup Strategy

```bash
# Create backup
tar -czf mdi-backup-$(date +%Y%m%d).tar.gz storage/data/ _data/persistent.json

# Restore backup
tar -xzf mdi-backup-YYYYMMDD.tar.gz
```

### Recovery Procedure

1. Reinstall application from Git
2. Restore `storage/data/` directory
3. Restore `_data/persistent.json`
4. Launch application
5. Verify session restoration

---

## Performance Tuning

### For Large Batches

- Process in batches of 50-100 files
- Increase system swap space if needed
- Use SSD for `storage/temp/`
- Close unnecessary applications

### Memory Optimization

- Monitor with: `ps aux | grep flet`
- Large CSV files (>1000 rows) may need more RAM
- Consider web mode for better resource management

### Disk Space Management

```bash
# Check disk usage
du -sh storage/temp/*

# Clean old temp directories (preserve protected ones)
# Protected directories have persistent_session.json reference

# Manual cleanup (careful!)
rm -rf storage/temp/file_selector_OLD_TIMESTAMP_*/
```

---

## Support and Maintenance

### Log Files

Application logs are written to `mdi.log`:

```bash
# View recent log entries
tail -f mdi.log

# Search for errors
grep ERROR mdi.log

# Export log for support
cp mdi.log mdi-backup-$(date +%Y%m%d).log
```

### Version Information

Check application version:
- Navigate to **About** page in application
- Or check: `_data/config.json`

### Getting Help

- **Documentation**: [USER-GUIDE.md](USER-GUIDE.md)
- **Repository**: [GitHub Issues](https://github.com/Digital-Grinnell/manage-digital-ingest-flet-Alma/issues)
- **Logs**: Include `mdi.log` when reporting issues

---

## Related Documentation

- **[README.md](README.md)**: Quick start and feature overview
- **[USER-GUIDE.md](USER-GUIDE.md)**: Comprehensive usage instructions
- **[ALMA-COMPOUND-HANDLING.md](ALMA-COMPOUND-HANDLING.md)**: Compound object documentation

---

**Last Updated**: November 2025  
**Application Version**: 2.0+  
**Target Deployment**: Grinnell College Libraries Digital Collections
