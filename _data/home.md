**This app will NOT `perform` any ingest or import, but it should be used to prep digital assets and metadata (identifiers, Handles, filenames, etc.) for subsequent operations.**

**This is the Alma Edition - configured specifically for Alma Digital workflows.**
  
## Features of this Alma app include:  
  
  - **⚙️ Settings** - app is pre-configured for Alma Digital ingest,  
  - **📂 File Selector** - object file selection via...  
    - a system file picker pop-up, or  
    - ability to read a list of digital object filenames from a `CSV` file,  
      - coupled with a "fuzzy" network file search utility with numeric-only difference penalty, and
      - automatic update of the `CSV` with unique IDs, collection IDs, compound object handling, and revised file names/paths,
  - **📊 CSV Generator** - create initial CSV rows from selected files using Alma-D structure, with optional metadata merge from existing CSV files,
  - **✨ Create Derivatives** - Alma derivative creation utility (200x200 thumbnails with .clientThumb extension),
  - **📋 Update CSV** - metadata update utility with compound object (parent/child) relationship management and automatic TOC generation,
  - **📖 Final Instructions** - AWS S3 upload script generator for Alma Digital ingest and follow-up instructions to assist in Alma ingest operations.

