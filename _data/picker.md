# File Selection Options

The application provides three methods for selecting files to process:

## 1. FilePicker (Direct Selection)

Click the '+' button to open the file picker dialog and select multiple images and/or PDF files directly from your file system.

The selected file paths will be stored in `page.session['selected_file_paths']` for later processing.

**Note:** In macOS, this app must be run as a browser app to use the file picker due to OS security restrictions.

## 2. CSV Selector (Search Workflow)

Load a CSV file containing filenames, then use fuzzy search to locate the actual files on your system.

This method is useful when:
- You have a list of filenames in a spreadsheet
- Files are scattered across multiple directories
- You need to match filenames with metadata

## 3. Complete Directory (Resume Previous Work)

Select a previously saved complete directory containing OBJS, TN, and SMALL subdirectories from a prior session.

This method allows you to:
- Resume work from a previous session
- Load preserved temporary directories with completed processing
- Skip file selection, derivatives creation, and CSV generation
- Go directly to the final Alma import step (Instructions view)

**Requirements:**
- Directory must contain `OBJS/` subdirectory with files
- Should contain `TN/` and `SMALL/` subdirectories with derivatives
- Should contain `generated_metadata_*.csv` and `values.csv` files

**Use Case:** Load a backup directory that was saved via the temp preservation feature. Since all processing is already complete (derivatives created, CSV generated), you can proceed directly to the Instructions view to generate the Alma upload script.

---

## Changing File Selection Method

To change which method is active:
1. Go to Settings
2. Select your preferred option from the "File Selection Option" dropdown
3. Navigate to File Selector to use the selected method
