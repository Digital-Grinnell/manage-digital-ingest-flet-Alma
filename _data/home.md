**This app will NOT `perform` any ingest or import, but it should be used to prep digital assets and metadata (identifiers, Handles, filenames, etc.) for subsequent operations.**

**This is the Alma Edition - configured specifically for Alma Digital workflows.**
  
## Features of this Alma app include:  
  
  - **Alma workflow only** - app is pre-configured for Alma Digital ingest,  
  - object file selection via...  
    - a system file picker pop-up, or  
    - ability to read a list of digital object filenames from a `CSV` file,  
      - coupled with a "fuzzy" network file search utility, and
      - automatic update of the `CSV` with unique IDs, collection IDs, compound object handling, and revised file names/paths,
  - Alma derivative creation utility (200x200 thumbnails with .clientThumb extension),
  - AWS S3 upload script generator for Alma Digital ingest,   
  - compound object (parent/child) relationship management with automatic TOC generation, and
  - follow-up instructions/scripts generator to assist in Alma ingest operations.

