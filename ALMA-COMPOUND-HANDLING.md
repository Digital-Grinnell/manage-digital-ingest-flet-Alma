# Alma Compound Object Handling in UpdateCSV

## Overview
This document describes the compound object (parent/child) relationship logic implemented in the UpdateCSV view for Alma mode workflows.

## Implementation Date
November 4, 2025

## Purpose
In Alma Digital workflows, compound objects represent collections of related digital items (e.g., multi-page documents, photo albums, multi-part works). These require special metadata handling to:
- Link parent and child records through a common `group_id`
- Build a Table of Contents (TOC) from child titles
- Set appropriate object types and representations
- Validate minimum child count requirements

## Functionality

### When It Runs
- **Mode**: Alma only
- **Timing**: Step 3.65 in the `apply_all_updates()` method
- **Location**: After Handle URL processing
- **Trigger**: Automatic when "Apply All Updates" button is clicked
- **Condition**: Only runs if `compoundrelationship` column exists in CSV

### Required CSV Columns

**Essential:**
- `compoundrelationship`: Identifies parent ("parent:...") and child ("child:...") records
- `originating_system_id`: Unique identifier for each record
- `group_id`: Links parent and children together (populated by this logic)

**Optional but recommended:**
- `dc:title`: Title of each object (used in TOC)
- `dc:type`: Type of each object (used in TOC)
- `dcterms:tableOfContents`: Where parent's TOC is stored
- `dcterms:type.dcterms:DCMIType`: Cleared for parent records
- `rep_label`: Set to child's title
- `rep_public_note`: Set to child's type
- `mms_id`: Marked with error if validation fails

### Detection Logic

The logic identifies compound objects by scanning the CSV sequentially:

1. **Parent Detection**: Finds rows where `compoundrelationship` starts with "parent"
2. **Child Detection**: Processes immediately following rows that start with "child"
3. **Grouping**: All consecutive children belong to the parent above them

### Processing Steps

#### For Each Parent Record:

1. **Group Identification**
   - Set parent's `group_id` = parent's `originating_system_id`
   - This creates the identifier that links the family together

2. **Child Discovery**
   - Scan forward through CSV rows
   - Collect all consecutive rows where `compoundrelationship` starts with "child"
   - Stop when encountering non-child row or end of CSV

3. **Child Validation**
   - Count total children found
   - **Requirement**: Minimum 2 children per parent
   - If < 2 children: Log error and mark parent's `mms_id` = "*ERROR* Too few children!"

4. **Table of Contents Construction**
   - For each valid child, build TOC entry:
     - Format with both title and type: `"Title (Type) | "`
     - Format with title only: `"Title | "`
   - Concatenate all entries with pipe separators
   - Store in parent's `dcterms:tableOfContents` field

5. **Parent Metadata Updates**
   - Set `dc:type` = "compound"
   - Clear `dcterms:type.dcterms:DCMIType` = ""
   - Store complete TOC string

#### For Each Child Record:

1. **Group Membership**
   - Set child's `group_id` = parent's `originating_system_id`
   - Links child to parent through common identifier

2. **Representation Fields**
   - Set `rep_label` = child's `dc:title`
   - Set `rep_public_note` = child's `dc:type`
   - These fields describe the digital representation

### Example Workflow

#### Input CSV:
| Row | compoundrelationship | originating_system_id | dc:title | dc:type | group_id |
|-----|---------------------|----------------------|----------|---------|----------|
| 1   | parent:album        | dg_1234567890       | Summer Album | Collection |  |
| 2   | child:page1         | dg_1234567891       | Page 1 | StillImage |  |
| 3   | child:page2         | dg_1234567892       | Page 2 | StillImage |  |
| 4   | child:page3         | dg_1234567893       | Page 3 | StillImage |  |

#### After Processing:
| Row | compoundrelationship | originating_system_id | dc:title | dc:type | group_id | dcterms:tableOfContents | rep_label | rep_public_note |
|-----|---------------------|----------------------|----------|---------|----------|------------------------|-----------|----------------|
| 1   | parent:album        | dg_1234567890       | Summer Album | compound | dg_1234567890 | Page 1 (StillImage) \| Page 2 (StillImage) \| Page 3 (StillImage) |  |  |
| 2   | child:page1         | dg_1234567891       | Page 1 | StillImage | dg_1234567890 |  | Page 1 | StillImage |
| 3   | child:page2         | dg_1234567892       | Page 2 | StillImage | dg_1234567890 |  | Page 2 | StillImage |
| 4   | child:page3         | dg_1234567893       | Page 3 | StillImage | dg_1234567890 |  | Page 3 | StillImage |

### Changes Made:
- ✅ Parent `group_id` set to its own `originating_system_id`
- ✅ All children `group_id` set to parent's `originating_system_id`
- ✅ Parent `dc:type` changed to "compound"
- ✅ Parent `dcterms:tableOfContents` populated with child information
- ✅ Each child's `rep_label` and `rep_public_note` set

## Logging

Comprehensive logging tracks all processing:

```
[INFO] Processing Alma compound parent/child relationships...
[INFO] Found parent at row 1 with originating_system_id: dg_1234567890
[INFO]   Set parent group_id to: dg_1234567890
[INFO]   Processed child at row 2: Page 1
[INFO]   Processed child at row 3: Page 2
[INFO]   Processed child at row 4: Page 3
[INFO]   Set parent TOC: Page 1 (StillImage) | Page 2 (StillImage) | Page 3 (StillImage)
[INFO]   Set parent dc:type to 'compound'
[INFO] Processed 1 compound parent/child group(s)
```

### Error Logging:
```
[ERROR] *ERROR* Parent at row 1 has only 1 child(ren), need at least 2!
```

## Edge Cases Handled

1. **Missing Columns**: Safely checks for column existence before updating
2. **Insufficient Children**: Validates minimum 2 children, logs error if not met
3. **Empty Values**: Handles empty/missing titles and types gracefully
4. **Non-String Values**: Converts all values to strings for comparison
5. **Sequential Processing**: Correctly handles multiple parent/child groups in one CSV
6. **Orphaned Children**: Only processes children immediately following a parent

## Validation Rules

### Parent Record Requirements:
- ✅ Must have `compoundrelationship` starting with "parent"
- ✅ Must have valid `originating_system_id`
- ✅ Must have at least 2 children immediately following
- ❌ Parent with 0-1 children = validation error

### Child Record Requirements:
- ✅ Must have `compoundrelationship` starting with "child"
- ✅ Must immediately follow parent or another child
- ✅ Should have `dc:title` for TOC (optional but recommended)

## Code Location

- **File**: `views/update_csv_view.py`
- **Method**: `apply_all_updates()`
- **Step**: 3.65 (Alma compound parent/child processing)
- **Lines**: Approximately 365-445 (may vary with updates)

## Reference Implementation

This logic is based on the reference implementation in:
- **Source**: `../migrate-MODS-to-dcterms/manage-collections.py`
- **Lines**: 312-373
- **Adaptation**: Converted from Polars DataFrames to Pandas DataFrames

Key differences from reference:
- Uses Pandas `.at[]` accessor instead of Polars
- Simplified dginfo handling (not yet fully implemented)
- Enhanced logging for debugging
- Added validation and error handling

## Integration with Alma Digital

After CSV processing, the resulting metadata structure works with Alma Digital's compound object model:

1. **Import Process**: Alma recognizes compound objects by matching `group_id` values
2. **Parent Display**: Shows TOC with clickable links to children
3. **Child Access**: Each child becomes a separate digital representation
4. **Navigation**: Users can browse between related items in the compound

## Future Enhancements

Potential improvements for consideration:

1. **dginfo Implementation**: Full JSON-based digital information tracking
2. **Flexible Validation**: Configurable minimum child count
3. **TOC Formatting**: Customizable TOC templates
4. **Nested Compounds**: Support for grandparent/parent/child hierarchies
5. **Post-Processing Report**: Summary of all compound groups created
6. **Error Recovery**: Attempt to fix common issues automatically

## Troubleshooting

### Common Issues:

**Problem**: "No compound parent/child relationships found"
- **Check**: Verify `compoundrelationship` column exists and has values
- **Check**: Ensure values start with "parent" or "child" (not "Parent" or "PARENT")

**Problem**: "Too few children" error
- **Check**: Confirm at least 2 child rows immediately follow parent
- **Check**: Verify child rows have `compoundrelationship` starting with "child"

**Problem**: Empty TOC in parent record
- **Check**: Ensure children have `dc:title` values
- **Check**: Verify `dcterms:tableOfContents` column exists

**Problem**: Children not linked to parent
- **Check**: Confirm `group_id` column exists in CSV
- **Check**: Verify children immediately follow parent (no gaps)

## Related Documentation

- **Alma Digital Documentation**: See Alma Digital help for compound object structure
- **CSV Column Verification**: See `utils.py` for column validation logic
- **General UpdateCSV**: See `USER.md` for overall UpdateCSV functionality

## Contact

For questions about Alma compound object handling in the Manage Digital Ingest application, refer to this document and the related application documentation.
