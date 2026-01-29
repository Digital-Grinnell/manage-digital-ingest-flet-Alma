#!/usr/bin/env python3
"""
Add JPG file size column to all_single_tiffs_with_local_paths.csv
"""
import csv
import os
from pathlib import Path

# Paths
csv_file = Path(__file__).parent / "all_single_tiffs_with_local_paths.csv"
output_file = Path(__file__).parent / "all_single_tiffs_with_local_paths_updated.csv"
for_import_dir = Path(__file__).parent / "For-Import"

# Read the CSV and add JPG size column
rows = []
with open(csv_file, 'r', encoding='utf-8') as f:
    reader = csv.DictReader(f)
    fieldnames = reader.fieldnames + ['JPG Size (bytes)']
    
    for row in reader:
        # Extract the TIFF filename from the Local Path column
        local_path = row['Local Path']
        if local_path:
            tiff_filename = Path(local_path).name
            # Convert .tiff to .jpg
            jpg_filename = tiff_filename.replace('.tiff', '.jpg').replace('.tif', '.jpg')
            
            # Look for the JPG file in For-Import directory
            jpg_path = for_import_dir / jpg_filename
            
            if jpg_path.exists():
                file_size = jpg_path.stat().st_size
                row['JPG Size (bytes)'] = str(file_size)
            else:
                row['JPG Size (bytes)'] = 'N/A'
        else:
            row['JPG Size (bytes)'] = 'N/A'
        
        rows.append(row)

# Write the updated CSV
with open(output_file, 'w', encoding='utf-8', newline='') as f:
    writer = csv.DictWriter(f, fieldnames=fieldnames)
    writer.writeheader()
    writer.writerows(rows)

print(f"Updated CSV written to: {output_file}")
print(f"Total rows processed: {len(rows)}")

# Count how many have JPG files
with_jpg = sum(1 for r in rows if r['JPG Size (bytes)'] != 'N/A')
print(f"Rows with JPG files found: {with_jpg}")
print(f"Rows without JPG files: {len(rows) - with_jpg}")

# Show stats on small JPG files (likely problematic)
small_threshold = 10000  # 10KB
small_jpgs = [r for r in rows if r['JPG Size (bytes)'] != 'N/A' and int(r['JPG Size (bytes)']) < small_threshold]
print(f"\nPotentially problematic JPGs (< {small_threshold} bytes): {len(small_jpgs)}")

if small_jpgs:
    print("\nFirst 10 small JPG files:")
    for row in small_jpgs[:10]:
        mms_id = row['MMS ID']
        size = row['JPG Size (bytes)']
        local_path = Path(row['Local Path']).name if row['Local Path'] else 'N/A'
        print(f"  {mms_id} | {local_path} | {size} bytes")
