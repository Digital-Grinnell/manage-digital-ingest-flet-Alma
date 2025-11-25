# User Guide: Manage Digital Ingest for Alma

A comprehensive guide for using the Manage Digital Ingest application to prepare and upload digital objects to Alma Digital.

## Table of Contents

- [Overview](#overview)
- [Getting Started](#getting-started)
- [Alma Workflow](#alma-workflow)
- [View Descriptions](#view-descriptions)
- [Session Preservation](#session-preservation)
- [Troubleshooting](#troubleshooting)

---

## Overview

**Manage Digital Ingest for Alma** is a desktop application built with Flet and Python that helps you:

- Prepare digital image collections for ingest into Alma Digital
- Match CSV metadata with corresponding image files using fuzzy search
- Generate derivative images (thumbnails and small versions)
- Update CSV files with sanitized filenames and unique identifiers
- Upload files to Alma AWS S3 storage
- Maintain session state across multiple work sessions

### Key Features

- **Fuzzy Filename Matching**: Automatically matches images to CSV metadata entries with configurable similarity threshold
- **Derivative Generation**: Creates TN (thumbnails) and SMALL versions of images
- **CSV Management**: Updates metadata with sanitized filenames and unique IDs
- **Compound Object Support**: Handles parent/child relationships for multi-page documents and collections
- **Session Preservation**: Save your work and resume later
- **AWS S3 Integration**: Generate upload scripts for Alma ingest
- **Comment Row Support**: CSV rows starting with # are preserved but ignored in processing

---

## Getting Started

### Launch the Application

```bash
flet run app.py
```

Or for web mode:
```bash
flet run --web app.py
```

### Initial Setup

1. **Review Settings** (Settings page)
   - Application is configured for Alma mode by default
   - File selection method is set to CSV
   - Optionally adjust theme (Light/Dark)
   - Optionally adjust window height

2. **Prepare Your Files**
   - CSV file with Alma Digital metadata
   - Digital object files (images, PDFs, etc.)
   - Ensure CSV headings match verified format (see `_data/verified_CSV_headings_for_Alma-D.csv`)

---

## Alma Workflow

This workflow prepares digital objects for upload to Alma Digital via AWS S3.

### Step 1: Home - Review Instructions

1. Navigate to **Home** page
2. Read the Alma-specific instructions
3. Note the CSV heading requirements
4. Review workflow overview

### Step 2: Settings - Verify Configuration

1. Go to **Settings** page
2. Verify **Mode** is set to `Alma` (fixed, cannot be changed)
3. Verify **File Selector** is `CSV`
4. Optionally adjust theme and window height
5. Settings are automatically saved

### Step 3: File Selector - Choose Files

#### Method 1: Direct File Selection (FilePicker)
1. Navigate to **File Selector** page
2. Click **"Select Files"** to open system file picker
3. Select all files you want to process
4. Files are automatically copied to temporary directory with symbolic links
5. Temp directory structure: `storage/temp/file_selector_YYYYMMDD_HHMMSS_UUID/OBJS/`
6. Status display shows temporary file count

#### Method 2: CSV-Based Selection with Fuzzy Matching

##### 3.1 Select CSV File
1. Navigate to **File Selector** page
2. Click **"Select CSV File"** and choose your metadata CSV
   - CSV must have verified headings for Alma mode
   - See `_data/verified_CSV_headings_for_Alma-D.csv` for valid columns
   - Comment rows (starting with #) are automatically filtered from processing
3. Review the CSV validation status
4. CSV is loaded and displayed in the table

##### 3.2 Browse for Image Files
1. Click **"Browse for Image Files"**
2. Select all image files that correspond to CSV entries
3. Multiple files can be selected at once
4. File count is displayed

##### 3.3 Run Fuzzy Search
1. Click **"Run Fuzzy Search"**
   - Application matches image filenames to CSV metadata using sequence-based similarity
   - 10-point penalty applied for numeric-only differences (e.g., file_52.pdf vs file_25.pdf)
   - Each CSV entry is matched to the best available file
   - Exhaustive search ensures true best match is found
2. Review matched files and their similarity scores
3. Adjust similarity threshold if needed:
   - Default: 90%
   - Lower threshold (70-80%) for more lenient matching
   - Higher threshold (95-100%) for stricter matching

##### 3.4 Handle Unmatched Files
- Files not matching any CSV entry are noted
- Placeholder files (400x400 pixels) are created for missing files
- CSV is updated with "ATTENTION! file-not-found" markers
- Review log for details on unmatched/missing files

##### 3.5 Copy Matched Files to Temp
1. Click **"Copy Matched Files to Temp"**
   - Creates temporary directory structure
   - Copies images with sanitized filenames
   - Structure: `storage/temp/file_selector_YYYYMMDD_HHMMSS_UUID/OBJS/`
   - Original CSV is copied to temp directory with timestamp
2. Review copy status and file count
3. Temp directory path is displayed and saved to session

### Step 3a: CSV Generator (Optional) - Create Initial Metadata

If you don't have a CSV file yet, you can generate one from your selected files:

1. Navigate to **CSV Generator** page
2. Verify selected files count is shown
3. Click **"Generate CSV Rows"**
   - Creates one CSV row per selected file
   - Populates `file_name_1` with filename
   - Populates `dc:title` with filename (without extension)
   - All other fields remain blank for manual editing
   - Uses Alma-D CSV structure (66+ columns)
4. Review generated data in the table view
5. **Optional: Merge Existing Metadata**
   - If you have an existing CSV with descriptive metadata:
     - Click **"Upload Metadata CSV"**
     - Select your CSV file with metadata
     - Click **"Merge Metadata"**
     - Matching rows are merged based on `file_name_1`
     - Only empty fields are populated (existing data preserved)
     - Review merge statistics in snack bar
6. Click **"Export to CSV File"**
   - Choose destination directory
   - CSV file is saved with timestamp: `generated_metadata_YYYYMMDD_HHMMSS.csv`
7. Edit the exported CSV to add/refine metadata before proceeding with workflow

**Note**: Generated CSV rows are stored in session storage and cleared when app restarts.

**Tip**: The merge feature is useful when you have partial metadata (descriptions, subjects, dates) in one CSV and want to combine it with newly generated file information.

### Step 4: Derivatives - Generate Thumbnails

#### 4.1 Generate TN Derivatives
1. Navigate to **Derivatives** page
2. Click **"Generate TN Derivatives"**
   - Creates thumbnails (200px max dimension) in `/TN` subdirectory
   - Uses Pillow for image processing
   - Uses PyMuPDF for PDF processing
   - Maintains aspect ratio
   - Preserves image quality
3. Review generation statistics
4. Check log for any errors

#### 4.2 Generate SMALL Derivatives (Optional)
1. Optionally click **"Generate SMALL Derivatives"**
   - Creates small versions (800px max dimension) in `/SMALL` subdirectory
   - Same processing as TN but larger size
   - Useful for preview images
2. Review generation statistics

#### 4.3 Review Generated Files
- File counts are displayed for each derivative type
- List of generated files is shown
- Check temp directory structure: `OBJS/`, `TN/`, `SMALL/`

### Step 5: Update CSV - Apply All Updates

#### 5.1 Review Current CSV
1. Navigate to **Update CSV** page
2. Review the "Before" CSV data display
3. Check existing metadata values

#### 5.2 Apply All Updates
1. Click **"Apply All Updates"** button
   - The following operations are performed automatically:
   
   **Step 1**: Update existing rows with sanitized filenames
   - Matches CSV filenames to sanitized temp filenames
   - Updates filename columns with new values
   
   **Step 2**: Append new row for CSV file itself
   - Creates metadata record for the CSV file
   - Sets `dc:type` to "Dataset"
   - Uses sanitized CSV filename
   
   **Step 3**: Generate unique IDs for empty cells
   - Fills empty `originating_system_id` cells with `dg_<epoch>` format
   - Ensures each record has unique identifier
   
   **Step 4**: Set dc:identifier to Handle URL format
   - Converts IDs to Handle URL format: `http://hdl.handle.net/11084/{id}`
   
   **Step 5**: Populate dginfo field
   - Sets dginfo to temp CSV filename for all rows
   - Links records to their source CSV
   
   **Step 6**: Process Alma compound parent/child relationships (if applicable)
   - Identifies parent/child records via `compoundrelationship` column
   - Links families through `group_id`
   - Builds Table of Contents from child titles
   - Sets parent `dc:type` to "compound"
   - Validates minimum 2 children per parent
   - See [ALMA-COMPOUND-HANDLING.md](ALMA-COMPOUND-HANDLING.md) for details

2. Review processing log messages
3. Check for any validation errors or warnings

#### 5.3 Review Changes
1. View "Before/After" comparison tables
2. Check the change count summary
3. Verify metadata updates are correct
4. Review compound object relationships if present

#### 5.4 Save Changes
1. Changes are automatically saved to the working CSV
2. Two CSV files are created:
   - **Main CSV**: Preserves comment rows, saved with minimal quoting
   - **values.csv**: Comment rows removed, collection_id cells blanked, ready for upload
3. Both files saved to temp directory
4. Click **"Save CSV"** button if manual save needed

### Step 6: Instructions - Generate Upload Script

#### 6.1 Navigate to Instructions
1. Navigate to **Instructions** page
2. Review follow-up instructions for Alma Digital upload

#### 6.2 Enter Alma Information
1. **Profile ID**: Pre-filled with `6496776180004641` (verify or update)
2. **Import ID**: Leave blank unless you have a specific import ID
   - Script will help you find available import IDs

#### 6.3 Generate Upload Script
1. Click **"Generate Upload Script"**
2. Script is saved to: `{temp_directory}/upload_to_alma.sh`
3. Review the displayed AWS S3 commands:
   - Upload CSV and values.csv
   - Upload OBJS directory
   - Upload TN directory

#### 6.4 Copy Commands
- Use **"Copy All 3 cp Commands"** button to copy all upload commands at once
- Or use individual copy buttons for each command
- Commands are formatted for direct terminal use

### Step 7: Execute Upload

#### 7.1 Prepare Terminal
1. Open terminal application
2. Navigate to temp directory:
   ```bash
   cd storage/temp/file_selector_YYYYMMDD_HHMMSS_UUID/
   ```
3. Make script executable:
   ```bash
   chmod +x upload_to_alma.sh
   ```

#### 7.2 Run Upload Script
1. Execute script:
   ```bash
   ./upload_to_alma.sh
   ```
2. Follow interactive prompts:

   **Step 1 - List S3 Bucket Contents**
   - Lists available profile and import directories
   - Find your profile ID if not already known
   - Note the import ID structure
   
   **Step 2 - Upload Files**
   - Copies entire temp directory to S3
   - Uploads: OBJS/, TN/, CSV files
   - Shows progress for each file
   
   **Step 3 - Verify Upload**
   - Lists uploaded files in S3 bucket
   - Confirms successful transfer
   - Shows file count and paths

#### 7.3 Complete Alma Ingest
1. Return to Alma Digital Uploader interface
2. Navigate to your profile and import ID
3. Verify files are visible in Alma
4. Complete the ingest process in Alma Digital
5. Review and publish digital objects

---

## View Descriptions

### Home
- Welcome page with Alma-specific instructions
- Quick overview of the 7-step ingest process
- Links to relevant documentation
- Application branding and logo

### Settings
- **Mode**: Fixed to "Alma" (cannot be changed)
- **File Selector**: Fixed to "CSV" (CSV-based workflow)
- **Theme**: Light or Dark mode (user preference)
- **Window Height**: Adjust application window size
- Settings automatically persist across sessions

### File Selector
- **CSV Selection**: Choose and validate CSV metadata file
- **File Browsing**: Select image files to match with CSV
- **Fuzzy Search**: Automatic filename matching with configurable threshold and numeric-only difference penalty
- **Temp Copy**: Create working directory with sanitized filenames
- **Status Display**: Shows validation, match results, file counts
- **Comment Filtering**: Rows starting with # are automatically excluded from processing
- **Direct File Selection**: Use FilePicker to select files without CSV (creates symbolic links)

### CSV Generator
- **Generate Metadata**: Create initial CSV rows from selected files
- **Alma-D Structure**: Uses verified 66+ column Alma Digital CSV format
- **Auto-populate**: Fills `file_name_1` and `dc:title` fields automatically
- **Upload Metadata CSV**: Load existing CSV file with descriptive metadata
- **Merge Metadata**: Combine uploaded metadata with generated rows by matching `file_name_1`
- **Preview Table**: View generated data before export
- **Export to CSV**: Save generated metadata to any directory
- **Session Storage**: Temporarily stores generated rows (cleared on app restart)
- **Timestamp Filenames**: Exported files include timestamp for version tracking
- **Smart Merge**: Only populates empty fields, preserves existing data

### Derivatives
- **TN Generation**: Create thumbnail images (200px max)
- **SMALL Generation**: Create preview images (800px max)
- **Progress Display**: Shows generation status and file counts
- **File Listing**: Lists all generated derivative files
- **Error Reporting**: Displays any generation failures
- **Format Support**: Handles images (JPG, PNG, TIF) and PDFs

### Update CSV
- **Before View**: Display current CSV data
- **Apply Updates**: Execute all metadata transformations
- **After View**: Display updated CSV data
- **Comparison**: Side-by-side before/after tables
- **Change Summary**: Count of modifications made
- **Manual Save**: Option to save changes manually
- **Processing Steps**: Detailed log of each transformation
- **Compound Handling**: Automatic parent/child relationship processing

### Storage
- Displays temp directory status
- Shows available files (OBJS, TN, SMALL, CSV)
- Link to temp directory location
- File count and size information

### Instructions
- Alma-specific follow-up instructions
- AWS S3 upload script generator
- Profile ID and Import ID input fields
- Individual command copy buttons
- **Copy All 3 cp Commands**: Bulk copy button for all upload commands
- Script preview and explanation
- Next steps guidance

### Log
- Real-time application log viewer
- Filter by log level (INFO, WARNING, ERROR)
- Search functionality
- Auto-scroll option
- Export log to file
- Clear log display
- Timestamp for each entry

### About
- Application information
- Version details
- Current session data viewer
- **Session preservation** functionality
- Logging test buttons
- License and credits

---

## Session Preservation

Save your work and resume later without losing progress.

### Saving a Session

1. Navigate to **About** page
2. Click **"Preserve Session & Protect Temp Directory"**
3. Confirmation message shows number of keys saved
4. Session data saved to: `storage/data/persistent_session.json`
5. Temporary directory marked as protected (won't be auto-deleted)

### What Gets Preserved

- All session keys and values
- Temp directory path and protection status
- File selection data (`temp_file_info`, `csv_filenames_for_matched`)
- CSV file paths and metadata
- Theme and window settings
- Processing status and results
- Any other session state

### Restoring a Session

- **Automatic**: Session restores on next application launch
- Temp directory remains intact (not deleted)
- All files (CSV, OBJS, TN, SMALL, values.csv) remain available
- Continue work from where you left off
- No need to re-run file selection or fuzzy search

### When to Use Session Preservation

- **End of work day**: Save progress on large batch
- **Multi-day projects**: Resume work tomorrow
- **Testing**: Preserve test scenarios
- **Before app updates**: Protect work in progress
- **Interrupted workflows**: Safe recovery point
- **After successful upload**: Keep backup of processed files

### Managing Preserved Sessions

- Session persists until manually deleted or overwritten
- To clear: Delete `storage/data/persistent_session.json`
- To update: Click preserve button again (overwrites previous)
- Temp directory cleanup respects protection flag
- Can have only one preserved session at a time

---

## Troubleshooting

### CSV Not Validating

**Problem**: CSV file rejected with heading validation error

**Solutions**:
- Check CSV against verified headings file: `_data/verified_CSV_headings_for_Alma-D.csv`
- Remove any unrecognized column headers
- Ensure column names match exactly (case-sensitive)
- Verify CSV uses UTF-8 encoding
- Check for hidden characters or BOM markers
- Comment rows (starting with #) are OK and will be filtered

### Fuzzy Search Not Finding Matches

**Problem**: Images not matching to CSV entries

**Solutions**:
- Lower similarity threshold (try 80% or 70%)
- Check that CSV column contains filenames (not full paths)
- Verify image filenames somewhat resemble CSV entries
- The algorithm uses sequence matching (not character counting)
- Filenames `012` and `021` are 95% similar (high score)
- Remove special characters from filenames
- Check for encoding issues in CSV
- Ensure CSV has filename column populated

### Wrong Files Being Matched

**Problem**: Fuzzy search matches incorrect files

**Solutions**:
- Increase similarity threshold (try 95% or higher)
- Check that CSV filenames are unique enough
- The search now examines ALL files before selecting best match
- No early termination - ensures true best match
- Review match scores in log
- Consider renaming similar files to be more distinct

### Derivatives Not Generating

**Problem**: TN or SMALL images not created

**Solutions**:
- Ensure temp directory exists and has files in OBJS/
- Check file permissions on temp directory
- Verify image files are valid (not corrupted)
- Check log for specific error messages
- Try generating one derivative type at a time
- Ensure sufficient disk space
- For PDFs, verify PyMuPDF is installed correctly
- Check that Pillow is installed and up to date

### Compound Object Errors

**Problem**: Parent/child relationships not processing correctly

**Solutions**:
- Verify `compoundrelationship` column exists in CSV
- Ensure parent rows have values starting with "parent"
- Ensure child rows have values starting with "child"
- Check that at least 2 children follow each parent
- Verify children immediately follow parent (no gaps)
- Check log for specific validation errors
- See [ALMA-COMPOUND-HANDLING.md](ALMA-COMPOUND-HANDLING.md) for details

### Upload Script Not Working

**Problem**: AWS S3 upload fails or script errors

**Solutions**:
- Verify AWS credentials are configured: `aws configure`
- Test AWS connection: `aws s3 ls`
- Check profile ID is correct (default: `6496776180004641`)
- Ensure script has execute permissions: `chmod +x upload_to_alma.sh`
- Review AWS S3 bucket permissions
- Check network connectivity
- Verify bucket name: `na-st01.ext.exlibrisgroup.com/01GCL_INST/upload/`
- Check that import ID exists or leave blank to find one

### Session Not Restoring

**Problem**: Preserved session not loading on restart

**Solutions**:
- Verify file exists: `storage/data/persistent_session.json`
- Check file is valid JSON (not corrupted)
- Review application log for restore errors
- Temp directory must still exist at saved path
- Check temp directory wasn't manually deleted
- Try preserving session again
- Restart application after preserving

### Collection_id Being Modified

**Problem**: collection_id values are being changed or populated automatically

**Current Behavior** (as of latest update):
- collection_id cells are now left as-is in main CSV
- values.csv has all collection_id cells blanked out
- No automatic population of collection_id
- Users manage collection_id values themselves

**Solutions**:
- Update to latest version if seeing old behavior
- Check that values.csv (not main CSV) is being uploaded
- Manually set collection_id values in your CSV if needed

### Application Crashes or Freezes

**Problem**: App becomes unresponsive

**Solutions**:
- Check `mdi.log` for error messages
- Verify Python version compatibility (3.9+)
- Update Flet: `pip install --upgrade flet==0.28.2`
- Clear temp directories manually: `rm -rf storage/temp/*`
- Delete `persistent_session.json` and restart fresh
- Run in web mode: `flet run --web app.py`
- Check system resources (memory, disk space)
- Try processing smaller batches

### macOS FilePicker Not Opening

**Problem**: File browser dialog doesn't appear on macOS

**Solutions**:
- Application uses CSV mode which doesn't require FilePicker
- Run in web mode: `flet run --web app.py`
- Grant appropriate macOS permissions in System Preferences
- Check for entitlement issues in console logs
- Use terminal to verify file paths if needed

---

## File Locations

### Application Files
- Main application: `app.py`
- Configuration: `_data/config.json`
- Persistent settings: `_data/persistent.json`
- Preserved sessions: `storage/data/persistent_session.json`
- Log file: `mdi.log`

### Temporary Files
- Temp directories: `storage/temp/file_selector_YYYYMMDD_HHMMSS_UUID/`
- Subdirectories: `OBJS/`, `TN/`, `SMALL/`
- Working CSV copy: `{temp_dir}/csv_filename_YYYYMMDD_HHMMSS.csv`
- Values CSV: `{temp_dir}/values.csv` (no comments, blank collection_id)
- Upload script: `{temp_dir}/upload_to_alma.sh`

### Reference Data
- Alma CSV headings: `_data/verified_CSV_headings_for_Alma-D.csv`
- File sources: `_data/file_sources.json`
- Home page content: `_data/home.md`
- Instructions content: `_data/alma_aws_s3.md`

---

## Tips and Best Practices

### CSV Preparation
- ✅ Use consistent, descriptive filenames in CSV
- ✅ Avoid special characters in filename column
- ✅ Test with small subset before full batch
- ✅ Keep backup copy of original CSV
- ✅ Comment rows (starting with #) are OK and will be preserved
- ✅ Use verified column headings from reference file
- ✅ Leave collection_id blank unless you need specific collection

### File Naming
- ✅ Use underscores instead of spaces
- ✅ Keep filenames under 200 characters
- ✅ Avoid special characters: `< > : " / \ | ? *`
- ✅ Use consistent naming pattern across all files
- ✅ Make filenames distinct enough for fuzzy matching

### Compound Objects
- ✅ Use `compoundrelationship` column for parent/child
- ✅ Ensure at least 2 children per parent
- ✅ Keep children immediately after parent in CSV
- ✅ Provide meaningful `dc:title` for children (used in TOC)
- ✅ Set `dc:type` for children (appears in TOC)

### Workflow Efficiency
- ✅ Generate all derivatives before uploading
- ✅ Review CSV changes before proceeding
- ✅ Preserve session before long operations
- ✅ Test upload with small batch first
- ✅ Keep log view open for monitoring
- ✅ Use "Copy All 3 cp Commands" for faster workflow

### Performance
- ✅ Process files in batches of 50-100 for large collections
- ✅ Close unnecessary applications during processing
- ✅ Use SSD for temp directory when possible
- ✅ Ensure adequate disk space (3x total image size)
- ✅ Monitor log for warnings about large files

---

## Getting Help

### Log Files
Check `mdi.log` for detailed error messages and operation history. All operations are logged with timestamps and severity levels.

### Session Data
View current session state in **About** page to verify data integrity and see what's preserved.

### Documentation
- This User Guide: Comprehensive workflow and troubleshooting
- [ALMA-COMPOUND-HANDLING.md](ALMA-COMPOUND-HANDLING.md): Detailed compound object documentation
- [README.md](README.md): Quick start and feature overview

### Support Resources
- Application repository: [GitHub](https://github.com/Digital-Grinnell/manage-digital-ingest-flet-Alma)
- Grinnell College Libraries: [Digital Collections](https://digital.grinnell.edu)
- Alma Documentation: Ex Libris knowledge center
- AWS S3 Documentation: Amazon AWS documentation

---

**Last Updated**: November 2025  
**Application Version**: 2.0+  
**Flet Version**: 0.28.2  
**Python Version**: 3.9+
