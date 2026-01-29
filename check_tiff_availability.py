#!/usr/bin/env python3
import csv
from pathlib import Path

# Read problematic files
prob_csv = Path('problematic_jpgs.csv')
with open(prob_csv, 'r') as f:
    reader = csv.DictReader(f)
    prob_files = list(reader)

print('Checking For-Import directory for problematic TIFF files:')
print('=' * 80)

for_import = Path('For-Import')
found = 0
not_found = 0

tiffs_found = []

for row in prob_files:
    filename = row['TIFF Filename']
    # Check both .tiff and .tif extensions
    tiff_path = for_import / filename
    tif_path = for_import / filename.replace('.tiff', '.tif')
    
    if tiff_path.exists():
        size = tiff_path.stat().st_size
        print(f'✓ {filename:<40} {size:>12,} bytes')
        tiffs_found.append(str(tiff_path))
        found += 1
    elif tif_path.exists():
        size = tif_path.stat().st_size
        print(f'✓ {tif_path.name:<40} {size:>12,} bytes')
        tiffs_found.append(str(tif_path))
        found += 1
    else:
        print(f'✗ {filename:<40} NOT FOUND')
        not_found += 1

print('=' * 80)
print(f'Found in For-Import: {found}')
print(f'Not Found: {not_found}')

if tiffs_found:
    print(f'\n{"=" * 80}')
    print('SOLUTION: Re-generate JPG files from these TIFFs')
    print('=' * 80)
    print('\nThese TIFF files are available and can be re-converted:')
    for tiff in tiffs_found:
        print(f'  {tiff}')
