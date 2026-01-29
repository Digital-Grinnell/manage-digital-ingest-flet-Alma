#!/usr/bin/env python3
"""
Generate a report of JPG files by size to identify problematic conversions
"""
import csv
from pathlib import Path
from collections import defaultdict

csv_file = Path(__file__).parent / "all_single_tiffs_with_local_paths.csv"

# Read the CSV and categorize files by size
rows = []
with open(csv_file, 'r', encoding='utf-8') as f:
    reader = csv.DictReader(f)
    for row in reader:
        rows.append(row)

# Categorize by size
not_found = [r for r in rows if r['JPG Size (bytes)'] == 'N/A']
very_small = [r for r in rows if r['JPG Size (bytes)'] != 'N/A' and int(r['JPG Size (bytes)']) < 10000]
small = [r for r in rows if r['JPG Size (bytes)'] != 'N/A' and 10000 <= int(r['JPG Size (bytes)']) < 50000]
medium = [r for r in rows if r['JPG Size (bytes)'] != 'N/A' and 50000 <= int(r['JPG Size (bytes)']) < 200000]
large = [r for r in rows if r['JPG Size (bytes)'] != 'N/A' and int(r['JPG Size (bytes)']) >= 200000]

print("=" * 80)
print("JPG FILE SIZE ANALYSIS REPORT")
print("=" * 80)
print(f"\nTotal TIFF records in CSV: {len(rows)}")
print(f"\nJPG File Distribution:")
print(f"  Not found in For-Import: {len(not_found):4d} ({len(not_found)/len(rows)*100:5.1f}%)")
print(f"  Very small (<10KB):      {len(very_small):4d} ({len(very_small)/len(rows)*100:5.1f}%) ⚠️  LIKELY PROBLEMATIC")
print(f"  Small (10-50KB):         {len(small):4d} ({len(small)/len(rows)*100:5.1f}%)")
print(f"  Medium (50-200KB):       {len(medium):4d} ({len(medium)/len(rows)*100:5.1f}%)")
print(f"  Large (≥200KB):          {len(large):4d} ({len(large)/len(rows)*100:5.1f}%)")

print(f"\n{'=' * 80}")
print("POTENTIALLY PROBLEMATIC FILES (Very Small JPGs < 10KB)")
print(f"{'=' * 80}")
print(f"Total: {len(very_small)} files")
print(f"\n{'MMS ID':<25} {'Filename':<35} {'Size (bytes)':>12}")
print("-" * 80)
for row in very_small:
    mms_id = row['MMS ID']
    filename = Path(row['Local Path']).name if row['Local Path'] else 'N/A'
    size = row['JPG Size (bytes)']
    print(f"{mms_id:<25} {filename:<35} {size:>12}")

# Create a CSV with just the problematic files
output_csv = Path(__file__).parent / "problematic_jpgs.csv"
with open(output_csv, 'w', encoding='utf-8', newline='') as f:
    writer = csv.DictWriter(f, fieldnames=['MMS ID', 'TIFF Filename', 'JPG Size (bytes)', 'Local Path'])
    writer.writeheader()
    for row in very_small:
        writer.writerow({
            'MMS ID': row['MMS ID'],
            'TIFF Filename': Path(row['Local Path']).name if row['Local Path'] else 'N/A',
            'JPG Size (bytes)': row['JPG Size (bytes)'],
            'Local Path': row['Local Path']
        })

print(f"\n{'=' * 80}")
print(f"Problematic files also saved to: {output_csv}")
print("=" * 80)
