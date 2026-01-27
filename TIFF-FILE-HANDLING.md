# TIFF File Handling in Manage Digital Ingest

## Overview

This document describes how the Manage Digital Ingest application processes `.tif` and `.tiff` image files for Alma Digital ingestion. The application implements a **dual-representation model** where the original TIFF file serves as the preservation copy and a high-quality JPG conversion serves as the access copy.

## Workflow Summary

When a `.tif` or `.tiff` file is imported, the application:

1. Creates a symbolic link with a sanitized filename in the temporary `OBJS/` directory
2. Converts the TIFF to high-quality JPG for web access
3. Generates a standard thumbnail for display
4. Prepares metadata with dual file references
5. Outputs both files with consistent naming for Alma upload

## Detailed Process

### 1. File Selection

**Location**: `views/file_selector_view.py`

- User selects `.tif` or `.tiff` files through the file picker (both extensions are allowed)
- Filename is sanitized:
  - Spaces replaced with underscores
  - Space-dash patterns (` - `, `- `, ` -`) converted to double dashes (`--`)
  - Trailing spaces before extension are removed
- Symbolic link created in temporary `storage/temp/file_selector_YYYYMMDD_HHMMSS_xxxxxxxx/OBJS/` directory
- Original file remains untouched at source location

**Example**:
```
Original: /Users/john/Images/Historic Photo - Page 1.tiff
Symlink:  storage/temp/.../OBJS/Historic_Photo--Page_1.tiff
```

### 2. Derivative Creation

**Location**: `views/derivatives_view.py` → `create_image_derivatives()`

When the user clicks "Create Derivatives", the application:

#### A. JPG Conversion
- Uses **Pillow (PIL)** to convert TIFF to high-quality JPG
- Handles color space conversions:
  - **CMYK to RGB**: Uses ICC profiles when available, fallback to direct conversion
  - **RGBA to RGB**: Removes alpha channel
  - **Grayscale**: Preserved as-is
- Quality setting: **95%** (high quality for archival access)
- Optimization enabled for better compression without quality loss
- Output saved in `OBJS/` directory with same base name: `{root}.jpg`
- Logs file sizes before and after conversion

#### B. Thumbnail Creation
- Uses the `generate_thumbnail()` function with the original TIFF as source
- Resizes to 200×200 pixels (Alma requirement)
- Maintains aspect ratio with appropriate cropping/padding
- Saves as `{root}.jpg.clientThumb` in `TN/` directory
- JPEG format, 85% quality

**Example**:
```
Input:  OBJS/Historic_Photo--Page_1.tiff
Output: OBJS/Historic_Photo--Page_1.jpg  (converted image)
        TN/Historic_Photo--Page_1.jpg.clientThumb  (thumbnail)
```

### 3. Storage & Metadata Preparation

**Location**: `views/storage_view.py`

When preparing files for Alma upload, the application:

#### Unique ID Assignment
- Generates a unique identifier (e.g., `dg_20260127_142857_a1b2c3d4`)
- Renames both TIFF and JPG files with this ID
- Maintains file extension association

#### Dual Representation Model
The CSV metadata is configured with:

| Field | Value | Purpose |
|-------|-------|---------|
| `file_name_1` | `dg_xxxxx.jpg` | Primary/Access representation |
| `file_name_2` | `dg_xxxxx.tif` (or `.tiff`) | Preservation representation |
| `dc:type` | `Image` | Dublin Core type classification |
| `originating_system_id` | `dg_xxxxx` | Unique identifier |
| `dc:identifier` | `http://hdl.handle.net/11084/xxxxx` | Handle URL |

#### File Renaming Logic
The application handles two scenarios:

1. **Already Renamed by File Selector**:
   - Uses existing `dg_*` filename from file selector
   - Extracts base ID and applies to JPG
   
2. **Not Yet Renamed**:
   - Generates new unique ID
   - Renames `.tiff` → `dg_xxxxx.tiff` (preservation)
   - Renames `.jpg` → `dg_xxxxx.jpg` (access)

**Code Reference**: Lines 284-420 in `storage_view.py`

### 4. Final Output Structure

After processing, the temporary directory contains:

```
storage/temp/file_selector_YYYYMMDD_HHMMSS_xxxxxxxx/
├── OBJS/
│   ├── dg_20260127_142857_a1b2c3d4.tiff  (symlink to original)
│   └── dg_20260127_142857_a1b2c3d4.jpg   (converted access copy)
├── TN/
│   └── dg_20260127_142857_a1b2c3d4.jpg.clientThumb  (thumbnail)
└── generated_metadata_YYYYMMDD_HHMMSS.csv  (metadata with dual references)
```

### 5. CSV Update Process

**Location**: `views/update_csv_view.py`

When updating CSV metadata (Step 1.6 in the update process):

- Locates rows with `.tif` or `.tiff` filenames in `file_name_1`
- Replaces with corresponding `.jpg` filename
- Sets `file_name_2` to the `.tif`/`.tiff` filename
- Sets `dc:type` to "Image"
- Logs each update: `"Updated row {n} for .tiff image: file_name_1={jpg}, file_name_2={tiff}, dc:type=Image"`

## Technical Requirements

### Dependencies
- **Pillow (PIL)**: Required for image conversion
  - Must be installed via pip: `pip install Pillow`
  - Handles all major image formats
  - Built-in ICC profile support for color management
  
### File Format Specifications
- **Input**: TIFF/TIF image files (any valid TIFF format, including CMYK, RGB, RGBA, Grayscale)
- **Output JPG**: RGB color space, 95% quality, optimized
- **Thumbnail**: JPEG, 200×200 pixels, 85% quality, RGB color mode

### Supported TIFF Variants
- **Uncompressed TIFF**
- **LZW Compressed TIFF**
- **JPEG Compressed TIFF**
- **Packbits Compressed TIFF**
- **Multi-page TIFF** (first page only)
- **CMYK TIFF** (converted to RGB)
- **Grayscale TIFF** (preserved)

### Alma Digital Specifications
- Primary representation: JPG (web-accessible format)
- Preservation representation: TIFF (archival quality)
- Thumbnail naming: `{base}.jpg.clientThumb`
- Dublin Core type: "Image"

## Color Space Conversion Details

### CMYK to RGB Conversion
The application uses a two-tier approach for CMYK TIFF files:

1. **ICC Profile Method** (preferred):
   - Attempts to use embedded ICC profiles
   - Provides accurate color conversion
   - Preserves color fidelity
   
2. **Direct Conversion** (fallback):
   - Used if ICC profile conversion fails
   - Simple mathematical conversion
   - Adequate for most use cases

### Other Color Space Handling
- **RGBA**: Alpha channel removed, converted to RGB
- **Grayscale (L)**: Preserved without conversion
- **Palette/Indexed**: Converted to RGB
- **Lab**: Converted to RGB

## Error Handling

The application handles several error scenarios:

1. **Pillow/PIL Not Found**:
   - Returns error indicating missing dependency
   - Processing halts for that file
   
2. **Invalid TIFF Format**:
   - Logs specific error from Pillow
   - Processing halts for that file
   
3. **Color Space Conversion Failures**:
   - Falls back to simpler conversion method
   - Logs warning about fallback usage
   
4. **Thumbnail Creation Failures**:
   - Reports specific error from generate_thumbnail function
   - Processing halts for that file

## Benefits of This Approach

1. **Preservation**: Original TIFF quality retained for archival purposes
2. **Access**: JPG provides universal viewing in web browsers
3. **Efficiency**: Symbolic links avoid duplicating large image files
4. **Consistency**: Standardized naming ensures proper Alma ingestion
5. **Metadata**: Dual file references maintain relationship between formats
6. **Quality**: 95% JPG quality provides excellent image fidelity
7. **Color Accuracy**: ICC profile support ensures proper color conversion
8. **Compatibility**: Handles various TIFF formats including CMYK

## Comparison with WAV Audio Handling

The TIFF → JPG conversion follows the same architectural pattern as WAV → MP3:

| Aspect | TIFF Files | WAV Files |
|--------|-----------|-----------|
| **Input Format** | .tif, .tiff | .wav |
| **Access Copy** | .jpg (95% quality) | .mp3 (VBR highest quality) |
| **Preservation Copy** | Original TIFF | Original WAV |
| **Conversion Tool** | Pillow (PIL) | FFmpeg |
| **dc:type** | Image | Sound |
| **file_name_1** | JPG filename | MP3 filename |
| **file_name_2** | TIFF filename | WAV filename |
| **Thumbnail Source** | Original TIFF | Template asset |

## File Size Considerations

### Expected Size Reductions
- **Uncompressed TIFF**: 80-95% reduction (JPG is much smaller)
- **LZW Compressed TIFF**: 40-70% reduction (varies by content)
- **CMYK TIFF**: Additional reduction from color space conversion

### Example File Sizes
```
Original TIFF (uncompressed, 8.5x11", 300 DPI):
  CMYK: ~35 MB → JPG: ~2-4 MB (88-94% reduction)
  RGB:  ~25 MB → JPG: ~2-4 MB (84-92% reduction)
```

## Related Documentation

- [WAV-FILE-HANDLING.md](WAV-FILE-HANDLING.md) - Audio file handling (similar pattern)
- [ALMA-COMPOUND-HANDLING.md](ALMA-COMPOUND-HANDLING.md) - Multi-part object handling
- [USER-GUIDE.md](USER-GUIDE.md) - General application usage
- [DEPLOYMENT-SETUP.md](DEPLOYMENT-SETUP.md) - Installation and setup

## Troubleshooting

### Common Issues

**Problem**: "Error creating image derivatives: cannot identify image file"
- **Cause**: Invalid or corrupted TIFF file
- **Solution**: Verify TIFF file integrity, try opening in image viewer

**Problem**: Color shifts in converted JPG
- **Cause**: CMYK to RGB conversion without ICC profiles
- **Solution**: Ensure Pillow is up-to-date; consider manual color correction

**Problem**: Very large JPG files
- **Cause**: Extremely high resolution source images
- **Solution**: Normal; JPG at 95% quality preserves detail for archival access

**Problem**: Thumbnail appears blank or corrupted
- **Cause**: Incompatible TIFF compression or multi-page TIFF
- **Solution**: Convert TIFF to uncompressed format or ensure single-page

---

*Last Updated: January 27, 2026*
