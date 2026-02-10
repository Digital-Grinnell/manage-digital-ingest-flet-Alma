# Storage View - CSV Generation Buttons

This document describes the functionality of each button in the "Generate CSV Metadata Rows" view.

---

## Generate CSV Rows (Blue)

**Purpose:** Creates CSV metadata rows for all selected files from File Selector

**What it does:**
- Creates CSV metadata rows using the Alma Digital CSV structure
- Generates unique `dg_*` filenames with sequential IDs
- Creates Handle URLs (`http://hdl.handle.net/11084/XXXXXXXX`)
- Detects compound objects (files with `_2`, `_3`, etc. suffixes)
- Renames files in OBJS/TN/SMALL directories to match new `dg_*` naming convention
- Saves `generated_metadata_YYYYMMDD_HHMMSS.csv` to temp directory
- Creates `values.csv` (expanded format with pipe-delimited values split into separate columns)
- Adds self-referential row for the CSV file itself (required by Alma Digital)

**Requirements:**
- Files must be selected via File Selector first

**Output Location:**
- `storage/temp/file_selector_TIMESTAMP/generated_metadata_YYYYMMDD_HHMMSS.csv`
- `storage/temp/file_selector_TIMESTAMP/values.csv`

---

## Upload Metadata CSV (Purple)

**Purpose:** Load additional metadata from an external CSV file

**What it does:**
- Opens file picker to select a CSV file containing metadata
- Loads the CSV into memory for merging with generated rows
- Validates that the CSV contains required identifier fields
- Enables the "Merge Metadata" button once successfully loaded

**Requirements:**
- CSV must contain at least one of these columns for matching:
  - `file_name_1` (recommended)
  - `dc:identifier`
  - `dc:title`
  - `Title`

**Use Case:**
- When you have existing metadata in a spreadsheet that you want to merge with generated rows
- Allows you to avoid manually entering metadata for each file

---

## Merge Metadata (Deep Purple)

**Purpose:** Merge uploaded metadata into generated rows

**What it does:**
- Matches rows from uploaded CSV with generated rows using identifier fields
- Copies metadata values from uploaded CSV into corresponding generated rows
- Supports normalized matching (handles spaces, special characters, etc.)
- Preserves compound object relationships (parent/child structure)
- Updates display to show merged data
- Saves merged result to temp directory

**Requirements:**
- Must have generated CSV rows first (via "Generate CSV Rows")
- Must have uploaded metadata CSV (via "Upload Metadata CSV")

**Matching Logic:**
1. First tries exact match on identifier field
2. Falls back to normalized matching (case-insensitive, special character handling)
3. Logs all matches and merges to the application log

**Button State:**
- Disabled until both generated rows AND metadata CSV are loaded

---

## Export to CSV File (Green)

**Purpose:** Save generated CSV metadata to a file

**What it does:**
- Opens directory picker to select save location
- Exports current generated metadata rows to a CSV file
- Can be used after generation or after merging metadata

**Use Case:**
- Save your work for later use
- Share CSV with others
- Import into Alma Digital or other systems

**Button State:**
- Disabled until CSV rows are generated

---

## Clear Data (Orange)

**Purpose:** Reset the CSV generation view

**What it does:**
- Clears all generated CSV data from memory
- Clears session storage
- Resets the display to empty state
- Disables Export and Clear buttons

**Warning:**
- This only clears the in-memory data
- Files in the temp directory remain unchanged
- You can regenerate rows from the same files

**Button State:**
- Disabled until CSV rows are generated

---

## Typical Workflow

### Basic Workflow (No External Metadata)
1. Select files using File Selector
2. Click **Generate CSV Rows**
3. Click **Export to CSV File** (optional - already saved to temp directory)

### Advanced Workflow (With External Metadata)
1. Select files using File Selector
2. Click **Generate CSV Rows**
3. Click **Upload Metadata CSV** and select your metadata file
4. Click **Merge Metadata** to combine the data
5. Click **Export to CSV File** (optional - already saved to temp directory)

---

## File Naming Conventions

### Generated Filenames

**Audio Files (.wav):**
- `file_name_1`: `dg_XXXXXXXX.mp3` (access copy)
- `file_name_2`: `dg_XXXXXXXX.wav` (preservation copy)

**Image Files (.tiff):**
- `file_name_1`: `dg_XXXXXXXX.jpg` (access copy)
- `file_name_2`: `dg_XXXXXXXX.tiff` (preservation copy)

**Other Files:**
- `file_name_1`: `dg_XXXXXXXX.ext` (original extension)

### Derivative Naming

**Thumbnails (TN directory):**
- `dg_XXXXXXXX.jpg.clientThumb`

**Small Derivatives (SMALL directory):**
- `dg_XXXXXXXX.jpg.clientViewFullSize`

---

## Compound Object Handling

Files are grouped as compound objects when they follow these patterns:

- `basename_2`, `basename_3`, etc. (with underscore)
- `basename 2`, `basename 3`, etc. (with space)
- Implicit part 1: `basename` (no number) becomes part 1 if `basename_2` exists

**Example:**
```
Interview.wav          → Part 1 (implicit)
Interview_2.wav        → Part 2
Interview_3.wav        → Part 3
```

**CSV Output:**
- Parent row with `compoundrelationship: compound-object:parent`
- Child rows with `compoundrelationship: child:part1`, `child:part2`, etc.

---

## Troubleshooting

**Merge button stays disabled:**
- Ensure you've generated CSV rows first
- Ensure you've uploaded a metadata CSV
- Check the log view for error messages

**Metadata not merging:**
- Verify your metadata CSV has a matching column (`file_name_1`, `dc:identifier`, etc.)
- Check that the values in the matching column correspond to your filenames
- View the log for details about which rows matched

**Files not renamed:**
- Check the temp directory permissions
- Verify files exist in OBJS/TN/SMALL directories
- Check logs for rename errors
