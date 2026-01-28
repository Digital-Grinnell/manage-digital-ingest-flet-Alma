# Development History: Manage Digital Ingest for Alma

A record of key development milestones and feature implementations for the Alma Digital workflow application.

## Overview

This document chronicles the development of the Manage Digital Ingest application for Alma Digital, focusing on features specific to institutional repository workflows, AWS S3 integration, and compound object handling.

**Development Period**: October 2025 - Present  
**Primary Focus**: Alma Digital workflows, CSV management, and AWS S3 upload automation  
**Development Approach**: Incremental improvements with user feedback

---

## Recent Updates

### Audio Derivatives Generation

**Date**: January 2026

**Change**: Added audio file processing to the derivatives generation workflow.

**Details**:
- Modified `derivatives_view.py` to handle .wav audio files:
  - **MP3 Conversion**: Converts .wav files to high-quality .mp3 format
    - Uses FFmpeg with `-q:a 0` setting (highest quality VBR encoding)
    - Stores converted .mp3 files in OBJS directory
    - Preserves original filename with .mp3 extension
  - **Audio Thumbnail**: Creates visual thumbnail for audio files
    - Sources from `assets/gc_media_TN.jpeg` template
    - Resizes to 200x200 pixels for Alma compatibility
    - Saves with `.jpg.clientThumb` extension in TN directory
- Added `create_audio_derivatives()` method with FFmpeg integration
- Requires FFmpeg installation for audio conversion

**Files Modified**:
- `views/derivatives_view.py`: Added audio processing support

**Dependencies**:
- Requires FFmpeg to be installed and available in system PATH
- Uses Pillow (PIL) for thumbnail resizing

**Example**:
- Input: `interview.wav` in OBJS/
- Generated:
  - `OBJS/interview.mp3` (high-quality conversion)
  - `TN/interview.jpg.clientThumb` (200x200 audio thumbnail)

---

### CSV Generator Creates values.csv

**Date**: January 2026

**Change**: CSV Generator now automatically creates values.csv file in the temp directory.

**Details**:
- Modified `generate_csv_rows()` in `storage_view.py` to call `save_values_csv()` after generating CSV rows
- Added `save_values_csv()` method to StorageView class:
  - Creates values.csv in the temp directory (alongside OBJS/, TN/, SMALL/)
  - Blanks out `collection_id` column for all rows except the last one (self-referential CSV row)
  - Uses minimal quoting (quoting=0) for proper CSV formatting
  - No comment rows (CSV Generator doesn't create comment rows)
- Ensures values.csv is ready for Alma Digital upload without additional processing

**Files Modified**:
- `views/storage_view.py`: Added `save_values_csv()` method and integrated into CSV generation workflow

**Purpose**:
- values.csv is the file used for Alma Digital upload
- Main CSV file can contain comments and full collection_id values for reference
- values.csv is upload-ready with collection_id properly formatted

---

### Flexible Compound Object Separator

**Date**: January 2026

**Change**: Compound object detection now accepts both underscore and space as separators.

**Details**:
- Updated regex pattern from `r'^(.+)_(\d+)$'` to `r'^(.+)[_ ](\d+)$'`
- Now detects compound objects with either separator:
  - `album_1.jpg`, `album_2.jpg` (underscore)
  - `album 1.jpg`, `album 2.jpg` (space)
  - Can even mix: `album_1.jpg`, `album 2.jpg` (both recognized)

**Files Modified**:
- `views/storage_view.py`: Updated compound detection regex
- `DEVELOPMENT-HISTORY.md`: Updated documentation with examples

---

**Date**: January 2026

**Change**: Enhanced CSV generation to automatically create Handle URLs and detect compound objects.

**Details**:
- Modified `generate_csv_rows()` in `storage_view.py` to:
  - **Handle URL Generation**: Automatically generate `dc:identifier` Handle URLs from unique IDs
    - Format: `http://hdl.handle.net/11084/<numeric_part>`
    - Extracts numeric portion from dg_* ID (e.g., `dg_1737072345` → `1737072345`)
  - **Compound Object Detection**: Automatically detect and process compound objects
    - Detects files with pattern `basename_<integer>` or `basename <integer>` (space or underscore separator)
      - Examples: `album_1.jpg`, `album 2.jpg`, `album_3.jpg` (all valid)
    - **Handles implicit part 1**: If `basename` exists alongside `basename_2`, `basename 2`, etc., treats `basename` as part 1
      - Example: `Nick_Nonas.jpg` and `Nick_Nonas_2.jpg` → compound with 2 parts
      - Example: `Nick Nonas.jpg` and `Nick Nonas 2.jpg` → compound with 2 parts
    - Groups files by basename and sorts by part number
    - Requires minimum 2 parts to create compound object
  - **Compound Metadata Generation**:
    - Creates parent row with `compoundrelationship: "parent:<basename>"`
    - Sets parent `dc:type` to "compound"
    - Generates child rows with `compoundrelationship: "child:part<N>"`
    - Links all children to parent via `group_id`
    - Builds `dcterms:tableOfContents` from child titles
    - Sets child `rep_label` and `rep_public_note` fields
  - **Smart Naming**: Child titles formatted as "basename - Part N"
  
**Files Modified**:
- `views/storage_view.py`: Updated `generate_csv_rows()` method with compound detection and Handle URL generation

**Example - Standalone File**:
- Input: `photo.jpg`
- Generated `file_name_1`: `dg_1737072345.jpg`
- Generated `dc:identifier`: `http://hdl.handle.net/11084/1737072345`
- Generated `dc:title`: `photo`

**Example - Compound Object (Explicit Numbering)**:
- Input files: `album_1.jpg`, `album_2.jpg`, `album_3.jpg`
- Parent row created with 3 children
- TOC: `album - Part 1 | album - Part 2 | album - Part 3`

**Example - Compound Object (Implicit Part 1)**:
- Input files: `Nick_Nonas.jpg`, `Nick_Nonas_2.jpg`
- `Nick_Nonas.jpg` treated as part 1 (implicit)
- `Nick_Nonas_2.jpg` treated as part 2 (explicit)
- Parent row created with 2 children
- TOC: `Nick_Nonas - Part 1 | Nick_Nonas - Part 2`

**Full Compound Example**:
- Input files: `album_1.jpg`, `album_2.jpg`, `album_3.jpg`
- Parent row created:
  - `originating_system_id`: `dg_1737072350`
  - `group_id`: `dg_1737072350`
  - `dc:identifier`: `http://hdl.handle.net/11084/1737072350`
  - `dc:title`: `album`
  - `dc:type`: `compound`
  - `compoundrelationship`: `parent:album`
  - `dcterms:tableOfContents`: `album - Part 1 | album - Part 2 | album - Part 3`
- Child rows created (3):
  - Each with unique `originating_system_id` and `dc:identifier`
  - All share parent's `group_id`: `dg_1737072350`
  - `dc:title`: `album - Part 1`, `album - Part 2`, `album - Part 3`
  - `compoundrelationship`: `child:part1`, `child:part2`, `child:part3`
  - Files renamed: `dg_1737072351.jpg`, `dg_1737072352.jpg`, `dg_1737072353.jpg`

---

### CSV Generation with dg_* Naming Convention

**Date**: January 2026

**Change**: Updated CSV generation to use dg_* naming convention for file_name_1 field and temporary files.

**Details**:
- Modified `generate_csv_rows()` in `storage_view.py` to:
  - Generate unique IDs using `utils.generate_unique_id()` for each file
  - Set `file_name_1` field to `dg_<timestamp><extension>` format
  - Preserve original filename (without extension) in `dc:title` field
  - Automatically rename temporary files in OBJS/ directory to match dg_* convention
  - Update session temp_file_info with new filenames
- Ensures consistency between CSV metadata and actual file storage
- Maintains Handle URL generation compatibility with dg_* format

**Files Modified**:
- `views/storage_view.py`: Updated `generate_csv_rows()` method to implement dg_* naming

**Example**:
- Original file: `photo_001.jpg`
- Generated `file_name_1`: `dg_1737072345.jpg`
- Generated `dc:title`: `photo_001`
- Temp file renamed: `OBJS/dg_1737072345.jpg`

---

### Audio File Support (WAV)

**Date**: January 2026

**Change**: Added .wav file support to FilePicker allowed extensions.

**Details**:
- Updated `file_selector_view.py` to include "wav" in `allowed_extensions` list
- Modified dialog title to reflect support for "Image, PDF, or Audio Files"
- Allows users to select .wav audio files alongside existing image and PDF formats

**Files Modified**:
- `views/file_selector_view.py`: Added "wav" to allowed_extensions in FilePickerSelectorView

---

## Core Feature Development

### CSV Processing and Validation

**Date**: October 2025

**Features Implemented**:
- CSV heading validation against verified Alma Digital columns
- Comment row support (rows starting with #)
- Minimal quoting for CSV output
- Differential CSV saving (main preserves comments, values.csv strips them)
- Fuzzy filename matching using sequence-based similarity
- Exhaustive search algorithm (examines all files before choosing best match)

**Technical Details**:
- Uses Pandas for CSV manipulation with `quoting=0` for minimal quoting
- Comment filtering implemented in 8+ processing loops
- `difflib.SequenceMatcher` for proper sequence similarity (replaced character counting)
- Helper function `is_comment_row()` checks if first column starts with #

**Files Involved**:
- `views/update_csv_view.py`: CSV update logic
- `views/file_selector_view.py`: File selection and fuzzy matching
- `utils.py`: Fuzzy search algorithm

---

### Unique ID Generation

**Date**: October 2025

**Problem Statement**: Need automatic unique identifier generation for digital objects.

**Solution Implemented**:
- Epoch-based ID format: `dg_<timestamp>`
- Session-based duplicate prevention
- Auto-increment if collision detected
- Fills empty `originating_system_id` cells

**Technical Implementation**:
```python
def generate_unique_id(page):
    epoch = int(time.time())
    unique_id = f"dg_{epoch}"
    # Check session for duplicates, increment if needed
    while unique_id in page.session.get("generated_ids", set()):
        epoch += 1
        unique_id = f"dg_{epoch}"
    return unique_id
```

**Files Modified**:
- `utils.py`: Added `generate_unique_id()` function
- `views/update_csv_view.py`: Integrated into CSV update workflow

---

### Handle URL Format

**Date**: October 2025

**Requirement**: Convert unique IDs to Handle URL format for Alma Digital.

**Implementation**:
- Extracts numeric portion from `originating_system_id`
- Converts to Handle format: `http://hdl.handle.net/11084/{numeric_id}`
- Populates `dc:identifier` column
- Only processes non-empty IDs

**Example**:
```
originating_system_id: dg_1729123456
dc:identifier: http://hdl.handle.net/11084/1729123456
```

**Files Modified**:
- `views/update_csv_view.py`: Added Handle URL conversion in Step 3.5

---

### Compound Object Handling

**Date**: November 4, 2025

**Problem Statement**: Alma Digital requires special metadata for compound objects (parent/child relationships).

**Features Implemented**:
- Automatic parent/child detection via `compoundrelationship` column
- Group ID linking (parent ID becomes family identifier)
- Table of Contents generation from child titles and types
- Parent validation (minimum 2 children required)
- Representation field population for children

**Processing Steps**:
1. Detect parent rows (compoundrelationship starts with "parent")
2. Collect consecutive child rows
3. Validate minimum child count (2 required)
4. Link via `group_id` (set to parent's `originating_system_id`)
5. Build TOC from child metadata: `"Title (Type) | Title (Type) | ..."`
6. Set parent `dc:type` to "compound"
7. Populate child `rep_label` and `rep_public_note`

**Validation**:
- Parents with < 2 children: `mms_id` marked with "*ERROR* Too few children!"
- Comprehensive logging of all processing steps

**Documentation**: See [ALMA-COMPOUND-HANDLING.md](ALMA-COMPOUND-HANDLING.md) for complete details.

**Files Modified**:
- `views/update_csv_view.py`: Added Step 3.65 for compound processing

---

### AWS S3 Upload Integration

**Date**: October 2025

**Features Implemented**:
- Upload script generation with profile ID and import ID
- Three-step upload process (list, upload, verify)
- Interactive shell script with prompts
- Copy buttons for individual commands
- Bulk copy button for all three aws s3 cp commands

**Script Features**:
- Lists S3 bucket contents to find profile/import IDs
- Uploads entire temp directory structure (OBJS, TN, CSV)
- Verifies upload completion
- Supports custom profile ID (default: 6496776180004641)

**Technical Implementation**:
- Template stored in `_data/alma_aws_s3.sh`
- Runtime substitution of paths and IDs
- Extract aws s3 cp commands for bulk copy feature
- Executable script saved to temp directory

**Files Modified**:
- `utils.py`: `generate_alma_s3_script()` function
- `views/instructions_view.py`: Script generation UI with copy buttons

---

### Session Preservation

**Date**: October 2025

**Problem Statement**: Users need to save work and resume later without losing progress.

**Solution Implemented**:
- Save all session data to `storage/data/persistent_session.json`
- Protect temp directories from cleanup
- Automatic session restoration on app launch
- Preserve file selection, CSV data, temp directory paths

**What Gets Preserved**:
- Selected CSV file path and filename
- Temp directory path and protection status
- File matching information (`temp_file_info`, `csv_filenames_for_matched`)
- All session keys and values

**User Workflow**:
1. Navigate to About page
2. Click "Preserve Session & Protect Temp Directory"
3. Session saved with confirmation
4. On next launch, session automatically restores
5. All files remain available in temp directory

**Files Modified**:
- `views/about_view.py`: Session preservation UI
- `app.py`: Session restoration on startup

---

### Placeholder File Generation

**Date**: November 2025

**Problem Statement**: Handle missing files gracefully with visual placeholders.

**Solution Implemented**:
- Generate placeholder files for unmatched/missing CSV entries
- Support for multiple formats: PDF, JPG, TIF, PNG
- Standard size: 400x400 pixels
- Pure Python implementation (Pillow + PyMuPDF)
- "ATTENTION! file-not-found" markers in CSV

**Technical Details**:
- Uses Pillow for image placeholders (JPG, PNG, TIF)
- Uses PyMuPDF for PDF placeholders
- ReportLab for PDF generation
- Creates gray placeholder with "File Not Found" text
- Updates CSV with special marker for manual review

**Files Modified**:
- `views/file_selector_view.py`: Placeholder generation logic
- `python-requirements.txt`: Added Pillow, PyMuPDF, ReportLab
- Removed ImageMagick dependency for cross-platform compatibility

---

### Collection ID Handling

**Date**: November 2025

**Requirement**: Allow users to manage collection_id values themselves.

**Changes Implemented**:
- Removed automatic population of collection_id with Pending Review
- Removed collection_id assignment for CSV file records
- Left collection_id cells as-is in main CSV (preserves user values)
- Blanked collection_id column in values.csv (empty cells)

**Rationale**: Users need control over collection assignment, automatic population was overwriting manual entries.

**Files Modified**:
- `views/update_csv_view.py`: Removed Steps 3.6 (auto-fill), commented out line 355 and 713 assignments
- `views/update_csv_view.py`: Added collection_id blanking in `save_values_csv()`

---

## Bug Fixes and Improvements

### Fuzzy Matching Algorithm Fix

**Date**: November 2025

**Problem**: Wrong files being matched (e.g., `phpp_MathewsJack_012.jpg` matched to CSV entry `phpp_MathewsJack_021.jpg` at 100%).

**Root Cause**: Original algorithm counted matching characters regardless of position, giving 24/26 = 92% match for "012" vs "021".

**Solution**:
- Replaced character-counting with `difflib.SequenceMatcher`
- Properly accounts for character order and position
- Now "012" vs "021" = 95% (more accurate)
- Removed early termination (was returning first 100% match without checking remaining files)
- Exhaustive search ensures true best match found

**Files Modified**:
- `utils.py`: Rewrote `calculate_string_similarity()` and `perform_fuzzy_search()`

### MMS ID Overlay Protection

**Date**: January 2026

**Feature**: Records with non-blank `mms_id` values are now treated as overlay records, meaning they represent existing Alma records being updated. The system now preserves all existing metadata for these records.

**Implementation**:
- Added `mms_id` column check before any CSV modifications
- If `mms_id` has a value (non-blank), the row is skipped for:
  - `originating_system_id` generation
  - `dc:identifier` population/conversion
  - File format conversions (.wav to .mp3, .tiff to .jpg)
  - `dc:type` updates
  - Any other metadata modifications
- Self-referential CSV row is still added to values.csv regardless

**Behavior**:
- **New records** (blank `mms_id`): All processing applies (generate IDs, convert files, set metadata)
- **Overlay records** (non-blank `mms_id`): Preserve all existing metadata, only add self-referential CSV row

**Files Modified**:
- `views/update_csv_view.py`: Added mms_id checks in Steps 1.5, 1.6, 3, and 3.5

---

### Multi-Valued Field Expansion in values.csv

**Date**: January 2026

**Feature**: When creating values.csv, the system now automatically expands multi-valued metadata fields (those containing `|` separators) into multiple single-valued columns with the same column name, following Alma Digital import requirements.

**Implementation**:
- Based on expansion logic from `../migrate-MODS-to-dcterms/expand-csv.py`
- Analyzes all columns to find maximum number of `|` delimited values
- Creates duplicate column headings for fields needing expansion
- Splits cell values on `|` and distributes across expanded columns
- Escapes double quotes properly for CSV format
- Applied in both `update_csv_view.py` and `storage_view.py`

**Example**:
```
Before expansion:
dc:subject
"Dogs | Cats | Birds"

After expansion:
dc:subject, dc:subject, dc:subject
"Dogs", "Cats", "Birds"
```

**Behavior**:
1. Analyze CSV data to count max `|` occurrences per column
2. Generate expanded headings (duplicate column names)
3. For each data row, split values on `|`
4. Distribute split values across expanded columns
5. Empty columns for values that don't exist
6. Log expansion details (which columns expanded and to how many)

**Files Modified**:
- `views/update_csv_view.py`: Added expansion to `save_values_csv()`
- `views/storage_view.py`: Added expansion to `save_values_csv()`

---

### Automatic file_name_2 Matching and Copying

**Date**: January 2026

**Feature**: When file_name_1 matched files are copied to the temporary OBJS directory, the system now automatically searches for and copies corresponding file_name_2 files.

**Implementation**:
- Extracts both file_name_1 and file_name_2 column data from CSV during file selection
- After matching file_name_1 files, automatically searches for file_name_2 files for the same rows
- Only searches for file_name_2 when:
  - file_name_2 value is not empty
  - Corresponding file_name_1 was successfully matched
- Copies both file_name_1 and file_name_2 files to OBJS directory
- **Important**: file_name_2 files are copied for S3 upload purposes but are NOT included in derivative processing
- Only file_name_1 files have thumbnails and derivatives generated
- Reports counts separately in success messages

**Behavior**:
1. Extract file_name_1 and file_name_2 data from CSV
2. Perform fuzzy search for all file_name_1 files
3. For each successfully matched file_name_1, check if there's a file_name_2 value
4. Search for and copy file_name_2 files to OBJS (stored separately from derivative processing list)
5. Generate derivatives ONLY for file_name_1 files
6. Report: "Created X file_name_1, Y file_name_2 file(s)"

**Files Modified**:
- `views/file_selector_view.py`: Added file_name_2 extraction and matching logic

---

### Exact Match Priority in Fuzzy Search

**Date**: January 2026

**Problem**: When both `.jpg` and `.tiff` versions of a file exist (e.g., `grinnell_4941_OBJ.jpg` and `grinnell_4941_OBJ.tiff`), fuzzy matching was selecting the `.tiff` even when CSV specified `.jpg`, because extension was ignored during matching.

**Solution**:
- Modified `perform_fuzzy_search()` to first check for exact matches (including extension)
- Only proceeds with fuzzy matching if no exact match is found
- Ensures CSV-specified file extensions are respected when files exist

**Behavior**:
1. **Step 1**: Search for exact filename match (including extension) → return immediately if found
2. **Step 2**: If no exact match, perform fuzzy search (ignoring extension)

**Files Modified**:
- `utils.py`: Added exact match check before fuzzy matching logic

---

### PyMuPDF Deprecation Warning

**Date**: November 2025

**Problem**: SwigPyPacked deprecation warnings cluttering output.

**Solution**:
- Added warnings filter in `app.py`
- Suppresses deprecation warnings for SwigPyPacked
- Updated to PyMuPDF 1.26.6

**Files Modified**:
- `app.py`: Added `warnings.filterwarnings()` at import
- `python-requirements.txt`: Updated PyMuPDF version

---

## Technical Architecture

### Technology Stack

**Core Framework**:
- Python 3.13.3
- Flet 0.28.2 (UI framework)

**Data Processing**:
- Pandas 2.3.3 (CSV manipulation)
- difflib (string similarity)

**Image Processing**:
- Pillow 12.0.0 (image operations)
- PyMuPDF 1.26.6 (PDF processing)
- ReportLab 4.4.4 (PDF generation)

**External Integration**:
- AWS CLI (S3 uploads)
- AWS S3 bucket: `na-st01.ext.exlibrisgroup.com/01GCL_INST/upload/`

### Application Structure

**Object-Oriented Architecture**:
- `base_view.py`: Abstract base class for all views
- Individual view modules for each page
- Shared utilities in `utils.py`
- Centralized logging via `logger.py`

**Data Flow**:
1. File Selector: CSV load → file selection → fuzzy matching → temp copy
2. Derivatives: Image processing → thumbnail generation
3. Update CSV: Metadata transformation → compound processing → save
4. Instructions: Script generation → S3 upload

**Session Management**:
- Flet page.session for runtime state
- JSON persistence for long-term storage
- Temp directory protection for preserved sessions

---

## Key Achievements

### Workflow Automation
- ✅ End-to-end Alma Digital ingest pipeline
- ✅ Automatic filename sanitization
- ✅ Fuzzy matching with high accuracy
- ✅ Compound object metadata generation
- ✅ AWS S3 upload script generation

### Data Integrity
- ✅ Comment row preservation
- ✅ Minimal CSV quoting
- ✅ Unique ID generation with collision prevention
- ✅ Differential CSV saving (main vs values)
- ✅ Collection ID user control

### User Experience
- ✅ Session preservation
- ✅ Comprehensive logging
- ✅ Before/after comparison views
- ✅ Copy-paste friendly commands
- ✅ Placeholder generation for missing files

### Cross-Platform Compatibility
- ✅ Pure Python implementation
- ✅ No ImageMagick dependency
- ✅ Works on macOS, Linux, Windows
- ✅ Web mode support

---

## Technical Debt & Future Enhancements

### Known Limitations

**Performance**:
- Large CSV files (>1000 rows) may be slow
- No pagination in table views
- Memory usage grows with file count

**Features**:
- No dginfo JSON implementation yet
- No nested compound objects (grandparent/parent/child)
- No automatic AWS upload (script must be run manually)

**Error Handling**:
- No automatic retry for failed operations
- Limited validation of compound object structures
- No rollback on partial failures

### Future Enhancement Ideas

**Automation**:
- Direct AWS S3 upload from application
- Batch processing with progress tracking
- Automatic compound object detection

**Validation**:
- Pre-upload CSV validation
- Image quality checks
- Metadata completeness reports

**Performance**:
- CSV chunking for large files
- Parallel derivative generation
- Caching for fuzzy search results

**Features**:
- Multiple CSV file support
- Custom metadata templates
- Integration with Alma Digital API

---

## Documentation

**Comprehensive Guides**:
- [USER-GUIDE.md](USER-GUIDE.md): Complete workflow documentation
- [ALMA-COMPOUND-HANDLING.md](ALMA-COMPOUND-HANDLING.md): Compound object details
- [DEPLOYMENT-SETUP.md](DEPLOYMENT-SETUP.md): Installation and deployment
- [README.md](README.md): Quick start overview

---

**Last Updated**: November 2025  
**Application Version**: 2.0+  
**Primary Maintainer**: Grinnell College Libraries
