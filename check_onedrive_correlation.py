#!/usr/bin/env python3
import csv
from pathlib import Path

csv_file = Path('all_single_tiffs_with_local_paths.csv')
rows = []
with open(csv_file, 'r') as f:
    reader = csv.DictReader(f)
    for row in reader:
        rows.append(row)

# Get the 11 problematic files
very_small = [r for r in rows if r['JPG Size (bytes)'] != 'N/A' and int(r['JPG Size (bytes)']) < 10000]

print('Checking if problematic JPGs came from OneDrive TIFFs:')
print('=' * 80)

onedrive_count = 0
volumes_count = 0

for row in very_small:
    local_path = row['Local Path']
    is_onedrive = 'OneDrive' in local_path if local_path else False
    is_volumes = '/Volumes/' in local_path if local_path else False
    
    if is_onedrive:
        onedrive_count += 1
    if is_volumes:
        volumes_count += 1
    
    filename = Path(local_path).name if local_path else 'N/A'
    source = 'OneDrive' if is_onedrive else ('/Volumes' if is_volumes else 'Other')
    print(f'{filename:<40} Source: {source:<12} | {row["JPG Size (bytes)"]:>6} bytes')

print('=' * 80)
print(f'Total problematic files: {len(very_small)}')
print(f'From OneDrive: {onedrive_count}')
print(f'From /Volumes: {volumes_count}')
print(f'\nConclusion: {"ALL" if volumes_count == 0 else "NONE"} of the problematic files are from OneDrive.')
print(f'            {"ALL" if volumes_count == len(very_small) else str(volumes_count)} of the problematic files are from /Volumes.')
