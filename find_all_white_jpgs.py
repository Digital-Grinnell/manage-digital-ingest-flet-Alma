#!/usr/bin/env python3
"""
Find all potentially problematic (white/small) JPG files with expanded criteria
"""
import csv
from pathlib import Path
from collections import defaultdict

csv_file = Path(__file__).parent / "all_single_tiffs_with_local_paths.csv"

# Read the CSV
rows = []
with open(csv_file, 'r', encoding='utf-8') as f:
    reader = csv.DictReader(f)
    for row in reader:
        rows.append(row)

# Categorize by size with expanded thresholds
not_found = [r for r in rows if r['JPG Size (bytes)'] == 'N/A']
very_small = [r for r in rows if r['JPG Size (bytes)'] != 'N/A' and int(r['JPG Size (bytes)']) < 10000]
small = [r for r in rows if r['JPG Size (bytes)'] != 'N/A' and 10000 <= int(r['JPG Size (bytes)']) < 50000]
questionable = [r for r in rows if r['JPG Size (bytes)'] != 'N/A' and 50000 <= int(r['JPG Size (bytes)']) < 100000]
medium = [r for r in rows if r['JPG Size (bytes)'] != 'N/A' and 100000 <= int(r['JPG Size (bytes)']) < 200000]
large = [r for r in rows if r['JPG Size (bytes)'] != 'N/A' and int(r['JPG Size (bytes)']) >= 200000]

# All potentially problematic (expand threshold)
all_problematic = very_small + small

print("=" * 80)
print("EXPANDED JPG FILE SIZE ANALYSIS")
print("=" * 80)
print(f"\nTotal TIFF records: {len(rows)}")
print(f"\nDetailed Size Distribution:")
print(f"  Not found:              {len(not_found):4d} ({len(not_found)/len(rows)*100:5.1f}%)")
print(f"  Very small (<10KB):     {len(very_small):4d} ({len(very_small)/len(rows)*100:5.1f}%) 🔴 DEFINITELY PROBLEMATIC")
print(f"  Small (10-50KB):        {len(small):4d} ({len(small)/len(rows)*100:5.1f}%) 🟠 LIKELY PROBLEMATIC")
print(f"  Questionable (50-100KB): {len(questionable):4d} ({len(questionable)/len(rows)*100:5.1f}%) 🟡 POSSIBLY PROBLEMATIC")
print(f"  Medium (100-200KB):     {len(medium):4d} ({len(medium)/len(rows)*100:5.1f}%)")
print(f"  Large (≥200KB):         {len(large):4d} ({len(large)/len(rows)*100:5.1f}%)")

print(f"\n{'=' * 80}")
print(f"COMBINED PROBLEMATIC FILES (<50KB): {len(all_problematic)}")
print(f"{'=' * 80}")

# Check source distribution for all problematic files
onedrive_count = 0
volumes_count = 0
other_count = 0

for row in all_problematic:
    local_path = row['Local Path']
    if 'OneDrive' in local_path:
        onedrive_count += 1
    elif '/Volumes/' in local_path:
        volumes_count += 1
    else:
        other_count += 1

print(f"\nSource Distribution for Problematic Files:")
print(f"  From OneDrive:  {onedrive_count:4d} ({onedrive_count/len(all_problematic)*100 if all_problematic else 0:5.1f}%)")
print(f"  From /Volumes:  {volumes_count:4d} ({volumes_count/len(all_problematic)*100 if all_problematic else 0:5.1f}%)")
print(f"  From Other:     {other_count:4d} ({other_count/len(all_problematic)*100 if all_problematic else 0:5.1f}%)")

# Save expanded list to CSV
output_csv = Path(__file__).parent / "all_problematic_jpgs.csv"
with open(output_csv, 'w', encoding='utf-8', newline='') as f:
    writer = csv.DictWriter(f, fieldnames=['MMS ID', 'TIFF Filename', 'JPG Size (bytes)', 'Source Type', 'Local Path'])
    writer.writeheader()
    for row in all_problematic:
        local_path = row['Local Path']
        if 'OneDrive' in local_path:
            source = 'OneDrive'
        elif '/Volumes/' in local_path:
            source = '/Volumes'
        else:
            source = 'Other'
        
        writer.writerow({
            'MMS ID': row['MMS ID'],
            'TIFF Filename': Path(local_path).name if local_path else 'N/A',
            'JPG Size (bytes)': row['JPG Size (bytes)'],
            'Source Type': source,
            'Local Path': local_path
        })

print(f"\n{'=' * 80}")
print(f"All {len(all_problematic)} problematic files saved to: {output_csv}")
print("=" * 80)

# Show first 20
if all_problematic:
    print(f"\nFirst 20 Problematic Files:")
    print(f"{'MMS ID':<25} {'Filename':<35} {'Size':>10} {'Source':<10}")
    print("-" * 80)
    for row in all_problematic[:20]:
        mms_id = row['MMS ID']
        filename = Path(row['Local Path']).name if row['Local Path'] else 'N/A'
        size = row['JPG Size (bytes)']
        local_path = row['Local Path']
        source = 'OneDrive' if 'OneDrive' in local_path else ('/Volumes' if '/Volumes/' in local_path else 'Other')
        print(f"{mms_id:<25} {filename:<35} {size:>10} {source:<10}")
