# WAV File Handling in Manage Digital Ingest

## Overview

This document describes how the Manage Digital Ingest application processes `.wav` audio files for Alma Digital ingestion. The application implements a **dual-representation model** where the original WAV file serves as the preservation copy and a high-quality MP3 conversion serves as the access copy.

## Workflow Summary

When a `.wav` file is imported, the application:

1. Creates a symbolic link with a sanitized filename in the temporary `OBJS/` directory
2. Converts the WAV to high-quality MP3 for web access
3. Generates a standard audio thumbnail
4. Prepares metadata with dual file references
5. Outputs both files with consistent naming for Alma upload

## Detailed Process

### 1. File Selection

**Location**: `views/file_selector_view.py`

- User selects `.wav` files through the file picker (WAV is an allowed extension)
- Filename is sanitized:
  - Spaces replaced with underscores
  - Space-dash patterns (` - `, `- `, ` -`) converted to double dashes (`--`)
  - Trailing spaces before extension are removed
- Symbolic link created in temporary `storage/temp/file_selector_YYYYMMDD_HHMMSS_xxxxxxxx/OBJS/` directory
- Original file remains untouched at source location

**Example**:
```
Original: /Users/john/Audio Files/Interview - Part 1.wav
Symlink:  storage/temp/.../OBJS/Interview--Part_1.wav
```

### 2. Derivative Creation

**Location**: `views/derivatives_view.py` → `create_audio_derivatives()`

When the user clicks "Create Derivatives", the application:

#### A. MP3 Conversion
- Uses **FFmpeg** to convert WAV to high-quality VBR MP3
- Command: `ffmpeg -i input.wav -q:a 0 -map a -y output.mp3`
- Quality setting `-q:a 0` provides highest quality VBR encoding
- Output saved in `OBJS/` directory with same base name: `{root}.mp3`
- Logs file sizes before and after conversion

#### B. Thumbnail Creation
- Copies the `assets/gc_media_TN.jpeg` template
- Resizes to 200×200 pixels (Alma requirement)
- Converts to RGB JPEG format
- Saves as `{root}.jpg.clientThumb` in `TN/` directory

**Example**:
```
Input:  OBJS/Interview--Part_1.wav
Output: OBJS/Interview--Part_1.mp3  (converted audio)
        TN/Interview--Part_1.jpg.clientThumb  (thumbnail)
```

### 3. Storage & Metadata Preparation

**Location**: `views/storage_view.py`

When preparing files for Alma upload, the application:

#### Unique ID Assignment
- Generates a unique identifier (e.g., `dg_20260127_142857_a1b2c3d4`)
- Renames both WAV and MP3 files with this ID
- Maintains file extension association

#### Dual Representation Model
The CSV metadata is configured with:

| Field | Value | Purpose |
|-------|-------|---------|
| `file_name_1` | `dg_xxxxx.mp3` | Primary/Access representation |
| `file_name_2` | `dg_xxxxx.wav` | Preservation representation |
| `dc:type` | `Sound` | Dublin Core type classification |
| `originating_system_id` | `dg_xxxxx` | Unique identifier |
| `dc:identifier` | `http://hdl.handle.net/11084/xxxxx` | Handle URL |

#### File Renaming Logic
The application handles two scenarios:

1. **Already Renamed by File Selector**:
   - Uses existing `dg_*` filename from file selector
   - Extracts base ID and applies to MP3
   
2. **Not Yet Renamed**:
   - Generates new unique ID
   - Renames `.wav` → `dg_xxxxx.wav` (preservation)
   - Renames `.mp3` → `dg_xxxxx.mp3` (access)

**Code Reference**: Lines 144-230 in `storage_view.py`

### 4. Final Output Structure

After processing, the temporary directory contains:

```
storage/temp/file_selector_YYYYMMDD_HHMMSS_xxxxxxxx/
├── OBJS/
│   ├── dg_20260127_142857_a1b2c3d4.wav  (symlink to original)
│   └── dg_20260127_142857_a1b2c3d4.mp3  (converted access copy)
├── TN/
│   └── dg_20260127_142857_a1b2c3d4.jpg.clientThumb  (thumbnail)
└── generated_metadata_YYYYMMDD_HHMMSS.csv  (metadata with dual references)
```

### 5. CSV Update Process

**Location**: `views/update_csv_view.py`

When updating CSV metadata (Step 1.5 in the update process):

- Locates rows with `.wav` filenames in `file_name_1`
- Replaces with corresponding `.mp3` filename
- Sets `file_name_2` to the `.wav` filename
- Sets `dc:type` to "Sound"
- Logs each update: `"Updated row {n} for .wav audio: file_name_1={mp3}, file_name_2={wav}, dc:type=Sound"`

## Technical Requirements

### Dependencies
- **FFmpeg**: Required for audio conversion
  - Must be installed and available in system PATH
  - Used for high-quality MP3 encoding
  
### File Format Specifications
- **Input**: WAV audio files (any valid WAV format)
- **Output MP3**: Variable Bitrate (VBR), highest quality setting
- **Thumbnail**: JPEG, 200×200 pixels, 85% quality, RGB color mode

### Alma Digital Specifications
- Primary representation: MP3 (web-accessible format)
- Preservation representation: WAV (archival quality)
- Thumbnail naming: `{base}.jpg.clientThumb`
- Dublin Core type: "Sound"

## Error Handling

The application handles several error scenarios:

1. **FFmpeg Not Found**:
   - Returns error: "FFmpeg not found. Please install FFmpeg to process audio files."
   - Processing halts for that file
   
2. **Missing Thumbnail Template**:
   - Returns error if `assets/gc_media_TN.jpeg` doesn't exist
   - Processing halts for that file
   
3. **Conversion Failures**:
   - Logs FFmpeg stderr output
   - Reports failure with specific error message

## Benefits of This Approach

1. **Preservation**: Original WAV quality retained for archival purposes
2. **Access**: MP3 provides universal playback in web browsers
3. **Efficiency**: Symbolic links avoid duplicating large audio files
4. **Consistency**: Standardized naming ensures proper Alma ingestion
5. **Metadata**: Dual file references maintain relationship between formats
6. **Quality**: VBR MP3 at highest quality provides excellent audio fidelity

## Related Documentation

- [ALMA-COMPOUND-HANDLING.md](ALMA-COMPOUND-HANDLING.md) - Multi-part object handling
- [USER-GUIDE.md](USER-GUIDE.md) - General application usage
- [DEPLOYMENT-SETUP.md](DEPLOYMENT-SETUP.md) - Installation and setup

---

*Last Updated: January 27, 2026*
