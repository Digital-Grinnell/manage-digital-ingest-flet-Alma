# WAV File Handling in Manage Digital Ingest

## Overview

This document describes how the Manage Digital Ingest application processes `.wav` and `.mp3` audio files for Alma Digital ingestion. The application implements a **dual-representation model** where the original WAV file serves as the preservation copy and a high-quality MP3 conversion serves as the access copy. Additionally, the application offers a **semi-automated transcript creation workflow** using Microsoft Word Office 365's transcription feature.

## Workflow Summary

When a `.wav` or `.mp3` file is imported, the application:

1. Creates a symbolic link with a sanitized filename in the temporary `OBJS/` directory
2. Converts WAV to high-quality MP3 for web access (or uses provided MP3)
3. Generates a standard audio thumbnail
4. **Offers semi-automated transcript creation using Microsoft Word**
5. Prepares metadata with dual file references (for WAV inputs)
6. Outputs files with consistent naming for Alma upload

## Detailed Process

### 1. File Selection

**Location**: `views/file_selector_view.py`

- User selects `.wav` or `.mp3` files through the file picker
- Both WAV and MP3 are now allowed extensions
- Filename is sanitized:
  - Spaces replaced with underscores
  - Space-dash patterns (` - `, `- `, ` -`) converted to double dashes (`--`)
  - Trailing spaces before extension are removed
- Symbolic link created in temporary `storage/temp/file_selector_YYYYMMDD_HHMMSS_xxxxxxxx/OBJS/` directory
- Original file remains untouched at source location

**Examples**:
```
Original WAV: /Users/john/Audio Files/Interview - Part 1.wav
Symlink:      storage/temp/.../OBJS/Interview--Part_1.wav

Original MP3: /Users/jane/Recordings/Oral History.mp3
Symlink:      storage/temp/.../OBJS/Oral_History.mp3
```

### 2. Derivative Creation

**Location**: `views/derivatives_view.py` → `create_audio_derivatives()`

When the user clicks "Create Derivatives", the application processes audio files as follows:

#### A. MP3 Handling

**For WAV Input Files:**
- Uses **FFmpeg** to convert WAV to high-quality VBR MP3
- Command: `ffmpeg -i input.wav -q:a 0 -map a -y output.mp3`
- Quality setting `-q:a 0` provides highest quality VBR encoding
- Output saved in `OBJS/` directory with same base name: `{root}.mp3`
- Logs file sizes before and after conversion

**For MP3 Input Files:**
- MP3 file is copied directly to the `OBJS/` directory
- No conversion necessary
- Original MP3 quality is preserved

#### B. Thumbnail Creation
- Copies the `assets/gc_media_TN.jpeg` template
- Resizes to 200×200 pixels (Alma requirement)
- Converts to RGB JPEG format
- Saves as `{root}.jpg.clientThumb` in `TN/` directory

#### C. Transcript Workflow Initiation

After derivatives are created, the application automatically offers a **semi-automated transcript creation workflow**:

1. **Checks for Existing Transcript**: 
   - Looks for a CSV file with the same base name as the audio file
   - If found, notifies user and skips workflow

2. **Displays Transcript Option**:
   - Shows a prominent "📝 TRANSCRIPT AVAILABLE" message in the processing log
   - Provides a "📖 View Transcription Instructions" button

3. **When User Clicks Instructions**:
   - Opens MP3 file location in macOS Finder for easy access
   - Displays detailed step-by-step instructions in a dialog
   - Instructions cover the complete Microsoft Word transcription process

**Examples**:
```
WAV Input:  OBJS/Interview--Part_1.wav
Output:     OBJS/Interview--Part_1.mp3  (converted audio)
            TN/Interview--Part_1.jpg.clientThumb  (thumbnail)
            Transcript option displayed

MP3 Input:  OBJS/Oral_History.mp3
Output:     OBJS/Oral_History.mp3  (copied, no conversion)
            TN/Oral_History.jpg.clientThumb  (thumbnail)
            Transcript option displayed
```

### 3. Semi-Automated Transcript Creation Workflow

**Location**: `transcript_helper.py` and `views/derivatives_view.py`

The application provides a semi-automated workflow for creating transcripts from audio files using **Microsoft Word Office 365's built-in transcription feature**. This workflow is triggered automatically after MP3 derivatives are created.

#### A. Transcript Workflow Overview

The workflow consists of three main components:

1. **Automatic Detection**: After creating audio derivatives, the app checks if a transcript already exists
2. **User Instructions**: If no transcript exists, provides detailed instructions for using Word
3. **Automatic Processing**: When the user saves their Word transcript, the app can detect and process it

#### B. Using the Transcript Feature

**Step 1: View Instructions**

After derivatives are created, look for the transcript notification in the processing log:
```
📝 TRANSCRIPT AVAILABLE for Interview--Part_1.mp3
[📖 View Transcription Instructions] (button)
```

Click the "View Transcription Instructions" button to:
- Open the MP3 file location in Finder
- See detailed step-by-step instructions

**Step 2: Create Transcript in Microsoft Word**

The instructions guide you through Microsoft Word's transcription process:

1. Open Microsoft Word (Office 365)
2. Go to Home tab → Dictate dropdown → Transcribe
3. Upload your MP3 audio file
4. Wait for transcription to complete (Word automatically identifies speakers and timestamps)
5. Click "Add to document" to insert the transcript
6. **Important**: Save the document with the **same base name** as the MP3 file:
   - MP3 file: `Interview--Part_1.mp3`
   - Save as: `Interview--Part_1.docx`
7. Save in the **same directory** as the MP3 file

**Step 3: Process the Transcript**

After saving your Word document:

1. Click "Check for Completed Transcript" in the instructions dialog
2. The app automatically:
   - Locates the `.docx` file
   - Parses the Word transcript format
   - Extracts speaker names, timestamps, and text
   - Creates a structured CSV file: `Interview--Part_1.csv`

#### C. Transcript Output Format

The generated CSV file contains three columns:

| Column | Description | Example |
|--------|-------------|---------|
| `Speaker` | Speaker identifier | "Speaker 1", "Jane Smith" |
| `Timestamp` | Time marker | "0:00:05", "1:23:45" |
| `Text` | Transcribed content | "This is what was said..." |

**Example CSV Output**:
```csv
Speaker,Timestamp,Text
Speaker 1,0:00:05,This is the first thing that was said in the recording.
Speaker 2,0:00:15,This is a response from another speaker.
Speaker 1,0:00:28,Continuation of the conversation...
```

#### D. Technical Implementation

**Module**: `transcript_helper.py`

Key functions:
- `get_word_transcription_instructions()`: Generates formatted instructions
- `reveal_in_finder()`: Opens file location in macOS Finder
- `parse_docx_transcript()`: Converts Word .docx to structured CSV
- `check_for_existing_transcript()`: Detects previously created transcripts

**Word Document Format**:
The parser expects Microsoft Word's standard transcription output format:
```
Speaker 1 0:00:05
This is the text that was said.

Speaker 2 0:00:15
This is a response.
```

**Speaker Name Editing**:
You can edit speaker names in Word before saving:
- Replace "Speaker 1" with actual names (e.g., "John Smith")
- Replace "Speaker 2" with actual names (e.g., "Jane Doe")
- The parser will preserve your custom speaker names

#### E. Workflow Benefits

1. **Semi-Automated**: Minimal manual steps, automatic file detection and processing
2. **Quality**: Uses Microsoft's professional-grade transcription engine
3. **Flexibility**: Edit transcripts in Word before processing
4. **Structured Output**: CSV format for easy data management and analysis
5. **Integration**: Works seamlessly with Alma digital ingest workflow

#### F. Requirements

- **Microsoft 365 Subscription**: Required for Word's transcription feature
- **Internet Connection**: Transcription is cloud-based
- **Python Package**: `python-docx` (installed via `pip install python-docx`)

#### G. Limitations

- Transcription quality depends on audio clarity
- Speaker identification is automatic but may need manual correction
- Word's transcription requires user interaction (not fully automated)
- Works best with clear speech and minimal background noise

### 4. Storage & Metadata Preparation

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

### 5. Final Output Structure

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

### 6. CSV Update Process

**Location**: `views/update_csv_view.py`

When updating CSV metadata (Step 1.5 in the update process):

- Locates rows with `.wav` filenames in `file_name_1`
- Replaces with corresponding `.mp3` filename
- Sets `file_name_2` to the `.wav` filename
- Sets `dc:type` to "Sound"
- Logs each update: `"Updated row {n} for .wav audio: file_name_1={mp3}, file_name_2={wav}, dc:type=Sound"`

## Technical Requirements

### Dependencies
- **FFmpeg**: Required for WAV to MP3 audio conversion
  - Must be installed and available in system PATH
  - Used for high-quality MP3 encoding
  - Not required if only processing MP3 files directly
  
- **python-docx**: Required for transcript processing
  - Install: `pip install python-docx`
  - Used to parse Microsoft Word .docx files
  - Included in `python-requirements.txt`
  
- **Microsoft Office 365**: Required for transcript creation
  - Active subscription needed for Word's transcription feature
  - Internet connection required
  - macOS, Windows, or Web version supported
  
### File Format Specifications
- **Input**: WAV or MP3 audio files
  - WAV: Any valid WAV format
  - MP3: Any valid MP3 format
- **Output MP3**: Variable Bitrate (VBR), highest quality setting (from WAV conversion)
- **Thumbnail**: JPEG, 200×200 pixels, 85% quality, RGB color mode
- **Transcript**: CSV with Speaker, Timestamp, and Text columns

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

1. **Preservation**: Original WAV quality retained for archival purposes (when using WAV input)
2. **Flexibility**: Direct MP3 input supported for files already in web format
3. **Access**: MP3 provides universal playback in web browsers
4. **Efficiency**: Symbolic links avoid duplicating large audio files
5. **Consistency**: Standardized naming ensures proper Alma ingestion
6. **Metadata**: Dual file references maintain relationship between formats
7. **Quality**: VBR MP3 at highest quality provides excellent audio fidelity
8. **Transcription**: Semi-automated workflow makes transcript creation efficient
9. **Structured Data**: CSV transcript output enables easy data management and analysis
10. **Professional Quality**: Leverages Microsoft's transcription engine for accurate results

## Related Documentation

- [Oral-History-Workflow](https://github.com/Digital-Grinnell/Oral-History-Workflow) - Original transcript workflow repository
- [ALMA-COMPOUND-HANDLING.md](ALMA-COMPOUND-HANDLING.md) - Multi-part object handling
- [USER-GUIDE.md](USER-GUIDE.md) - General application usage
- [DEPLOYMENT-SETUP.md](DEPLOYMENT-SETUP.md) - Installation and setup

## Quick Start: Transcript Workflow

1. **Select Audio File**: Choose .wav or .mp3 files in File Selector
2. **Create Derivatives**: Click "Create Derivatives" button
3. **View Instructions**: Click "📖 View Transcription Instructions" when prompted
4. **Transcribe in Word**: Follow the displayed instructions to use Word's transcription
5. **Save .docx**: Save transcript with same name as MP3 in same directory
6. **Process**: Click "Check for Completed Transcript" to generate CSV

---

*Last Updated: February 2, 2026*
