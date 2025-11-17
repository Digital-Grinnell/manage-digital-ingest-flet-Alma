# Development History: Manage Digital Ingest for Alma

A record of key development milestones and feature implementations for the Alma Digital workflow application.

## Overview

This document chronicles the development of the Manage Digital Ingest application for Alma Digital, focusing on features specific to institutional repository workflows, AWS S3 integration, and compound object handling.

**Development Period**: October 2025 - Present  
**Primary Focus**: Alma Digital workflows, CSV management, and AWS S3 upload automation  
**Development Approach**: Incremental improvements with user feedback

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
