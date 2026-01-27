# TIFF to JPG Batch Converter Utility

## Overview

This standalone utility script processes TIFF files from AWS S3, converts them to high-quality JPG derivatives, and updates the source CSV with the JPG file paths. It uses the same TIFF-to-JPG conversion logic from the Manage Digital Ingest application.

## Purpose

Batch convert 3,500+ TIFF files stored in AWS S3 to JPG format for web access while maintaining high quality (95% JPEG quality).

## Features

- **AWS S3 Integration**: Downloads TIFF files directly from S3 buckets
- **High-Quality Conversion**: 95% JPEG quality with optimization
- **Color Space Handling**: Proper CMYK to RGB conversion using ICC profiles
- **CSV Updates**: Automatically appends JPG paths to the source CSV
- **Progress Tracking**: Real-time logging with success/failure counts
- **Error Handling**: Continues processing even if individual files fail
- **Resumable**: Can be interrupted and outputs partial results

## Requirements

### Python Dependencies

The script runs in the repository's `.venv` virtual environment and requires:

```bash
# Pillow is already installed (included in python-requirements.txt)
# boto3 needs to be installed:
source .venv/bin/activate
pip install boto3
deactivate
```

Or let the wrapper script install it automatically:
```bash
./run_tiff_converter.sh
# Will auto-install boto3 if not present
```

**Required packages**:
- **Pillow (PIL)**: Image processing library for TIFF to JPG conversion ✓ Already installed
- **boto3**: AWS SDK for Python (S3 file downloads) - Will be installed on first run

### AWS Credentials

Ensure AWS credentials are configured for S3 access:

```bash
aws configure
```

Or set environment variables:
```bash
export AWS_ACCESS_KEY_ID=your_access_key
export AWS_SECRET_ACCESS_KEY=your_secret_key
export AWS_DEFAULT_REGION=us-east-1
```

## Input

### CSV File Structure

**File**: `/Users/mcfatem/GitHub/CABB/all_single_tiffs.csv`

**Format**:
```csv
MMS ID,S3 Path
991011506419204641,01GCL_INST/storage/alma/44/D8/6D/.../grinnell_3482_OBJ.tiff
991011532686804641,01GCL_INST/storage/alma/8C/D1/57/.../grinnell_4952_OBJ.tiff
...
```

**Columns**:
1. **MMS ID**: Alma MMS identifier
2. **S3 Path**: Full S3 object path (relative to bucket)

## Output

### JPG Derivatives

**Location**: `~/TIF-to-JPG-Derivatives/`

**Naming**: Same as source TIFF but with `.jpg` extension
- Example: `grinnell_3482_OBJ.tiff` → `grinnell_3482_OBJ.jpg`

**Format**:
- JPEG quality: 95%
- Color space: RGB (converted from CMYK if needed)
- Optimization: Enabled

### Updated CSV

**File**: `/Users/mcfatem/GitHub/CABB/all_single_tiffs_with_jpg_paths.csv`

**Format**:
```csv
MMS ID,S3 Path,JPG Path
991011506419204641,01GCL_INST/storage/alma/.../grinnell_3482_OBJ.tiff,/Users/username/TIF-to-JPG-Derivatives/grinnell_3482_OBJ.jpg
991011532686804641,01GCL_INST/storage/alma/.../grinnell_4952_OBJ.tiff,/Users/username/TIF-to-JPG-Derivatives/grinnell_4952_OBJ.jpg
...
```

**New Column**:
3. **JPG Path**: Full local path to the created JPG derivative

### Log File

**File**: `tiff_to_jpg_conversion.log`

Contains detailed logging of:
- Conversion progress (file by file)
- File sizes (TIFF → JPG)
- Success/failure status
- Error messages
- Summary statistics

## Usage

### Quick Start

```bash
# 1. Ensure you're in the repository directory
cd /Users/mcfatem/GitHub/manage-digital-ingest-flet-Alma

# 2. Configure AWS credentials (one-time setup)
aws configure

# 3. Run the converter
./run_tiff_converter.sh
```

The wrapper script will:
- ✓ Activate the `.venv` virtual environment
- ✓ Check and install missing dependencies (boto3)
- ✓ Verify AWS credentials
- ✓ Run the conversion process
- ✓ Deactivate the environment when done

### Basic Execution

**Recommended** - Use the wrapper script (automatically activates .venv):
```bash
./run_tiff_converter.sh
```

Or activate the virtual environment manually:
```bash
source .venv/bin/activate
python3 tiff_to_jpg_batch_converter.py
deactivate
```

Or run directly (uses .venv automatically):
```bash
./tiff_to_jpg_batch_converter.py
```

### Configuration

Edit the configuration section in `main()` function:

```python
# Configuration
input_csv = '/Users/mcfatem/GitHub/CABB/all_single_tiffs.csv'
output_directory = '~/TIF-to-JPG-Derivatives/'
s3_bucket = 'grinnell-edu-backup'
use_s3_download = True  # Set to False for local file testing
```

**Parameters**:
- `input_csv`: Path to the source CSV file
- `output_directory`: Where JPG derivatives should be saved
- `s3_bucket`: AWS S3 bucket name
- `use_s3_download`: 
  - `True`: Download from S3 (requires boto3 and AWS credentials)
  - `False`: Use local file paths (for testing)

### Monitoring Progress

The script provides real-time progress updates:

```
[1/3500] Processing MMS ID: 991011506419204641
  TIFF: grinnell_3482_OBJ.tiff
  Converting: grinnell_3482_OBJ.tiff (12.45 MB)
  ✓ JPG created: grinnell_3482_OBJ.jpg (2.31 MB)
  ✓ Success (1/3500)

[2/3500] Processing MMS ID: 991011532686804641
  TIFF: grinnell_4952_OBJ.tiff
  Converting: grinnell_4952_OBJ.tiff (18.72 MB)
  ✓ JPG created: grinnell_4952_OBJ.jpg (3.15 MB)
  ✓ Success (2/3500)

Progress: 10/3500 processed (10 successful, 0 failed)
...
```

### Final Summary

```
================================================================================
CONVERSION SUMMARY
================================================================================
Total files:       3500
Successful:        3485
Failed:            15
Success rate:      99.6%
End time:          2026-01-27 15:30:45
Log file:          /path/to/tiff_to_jpg_conversion.log
================================================================================
```

## Performance Considerations

### Processing Time

Estimated based on file sizes and network speed:

- **Average TIFF size**: ~15 MB
- **Average download time**: 2-5 seconds (depends on network)
- **Average conversion time**: 1-3 seconds
- **Total per file**: ~3-8 seconds

**For 3,500 files**: Approximately 3-8 hours total processing time

### Interruption & Resume

The script can be interrupted (Ctrl+C) at any time:
- Partial results are saved to the output CSV
- Progress is logged to the log file
- Failed conversions have empty JPG paths in the CSV
- Can identify and retry failed files by checking for empty JPG paths

### Disk Space

Estimated disk requirements:

- **Source TIFFs**: ~52 GB (average 15 MB × 3,500 files)
- **JPG derivatives**: ~10-12 GB (estimated 80% size reduction)
- **Temporary storage**: Minimal (downloads one file at a time)

Ensure you have at least **15 GB free space** in `~/TIF-to-JPG-Derivatives/`

## Error Handling

### Common Errors

1. **AWS Credentials Not Found**
   ```
   ✗ boto3 not installed. Install with: pip install boto3
   ```
   **Solution**: Install boto3 and configure AWS credentials

2. **S3 Download Failed**
   ```
   ✗ S3 download error: An error occurred (403) when calling the GetObject operation: Forbidden
   ```
   **Solution**: Check AWS credentials and S3 bucket permissions

3. **Invalid TIFF File**
   ```
   ✗ Error converting /tmp/file.tiff: cannot identify image file
   ```
   **Solution**: TIFF file may be corrupted; marked as failed in CSV

4. **Out of Disk Space**
   ```
   ✗ Error converting: [Errno 28] No space left on device
   ```
   **Solution**: Free up disk space or change output directory

### Retry Failed Conversions

To retry only failed conversions, create a filtered CSV:

```bash
# Extract rows with empty JPG paths
grep ',$' all_single_tiffs_with_jpg_paths.csv > failed_conversions.csv

# Update script to use failed_conversions.csv
# Then re-run the script
```

## Conversion Logic

### Color Space Handling

The script handles various TIFF color spaces:

1. **CMYK → RGB**: 
   - Attempts ICC profile conversion (preferred)
   - Falls back to simple mathematical conversion
   
2. **RGBA → RGB**: 
   - Removes alpha channel
   
3. **Grayscale (L)**: 
   - Preserved as-is
   
4. **Other modes**: 
   - Converted to RGB

### Quality Settings

- **JPEG Quality**: 95% (high quality for archival access)
- **Optimization**: Enabled (better compression without quality loss)
- **Progressive**: Not enabled (for better compatibility)

## Testing

### Test with Local Files

To test without downloading from S3:

1. Copy a few TIFF files to a local directory
2. Update the CSV to use local paths
3. Set `use_s3_download = False` in the script
4. Run the script

### Test with Small Subset

Create a test CSV with 10-20 rows:

```bash
head -21 /Users/mcfatem/GitHub/CABB/all_single_tiffs.csv > test_subset.csv
```

Update `input_csv` in the script to use `test_subset.csv`

## Related Documentation

- [TIFF-FILE-HANDLING.md](TIFF-FILE-HANDLING.md) - TIFF conversion logic in main app
- [WAV-FILE-HANDLING.md](WAV-FILE-HANDLING.md) - Similar pattern for audio files

## Troubleshooting

### Script Hangs or Freezes

**Cause**: Large TIFF file download or conversion
**Solution**: Be patient; check log file for current status

### High Memory Usage

**Cause**: Very large TIFF files
**Solution**: Script processes one file at a time to minimize memory usage

### Inconsistent Color Conversion

**Cause**: CMYK TIFF without embedded ICC profile
**Solution**: Colors may shift slightly; this is expected for CMYK → RGB conversion

## Support & Maintenance

**Author**: Manage Digital Ingest Development Team  
**Created**: January 27, 2026  
**Script Location**: `/Users/mcfatem/GitHub/manage-digital-ingest-flet-Alma/tiff_to_jpg_batch_converter.py`

For issues or questions, check the log file first, then review the error handling section above.

---

*Last Updated: January 27, 2026*
