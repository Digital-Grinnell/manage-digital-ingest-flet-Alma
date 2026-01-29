#!/usr/bin/env python3
"""
Regenerate JPG files from TIFF files in For-Import directory.
Only replaces existing JPG if the new one is larger (indicating better quality).
"""
from pathlib import Path
from PIL import Image
import shutil

def convert_tiff_to_jpg(tiff_path, jpg_path, quality=95):
    """
    Convert a TIFF file to JPG.
    
    Args:
        tiff_path: Path to source TIFF file
        jpg_path: Path to output JPG file
        quality: JPG quality (1-100, default 95)
    
    Returns:
        int: Size of generated JPG in bytes, or None if failed
    """
    try:
        with Image.open(tiff_path) as img:
            # Convert to RGB if necessary
            if img.mode not in ('RGB', 'L'):
                img = img.convert('RGB')
            
            # Save as JPG to temporary location first
            temp_jpg = jpg_path.parent / f"{jpg_path.stem}_temp.jpg"
            img.save(temp_jpg, 'JPEG', quality=quality, optimize=True)
            
            # Get size of generated file
            new_size = temp_jpg.stat().st_size
            
            # Return temp path and size
            return temp_jpg, new_size
    except Exception as e:
        print(f"  ❌ Error converting {tiff_path.name}: {e}")
        return None, None

def main():
    base_dir = Path(__file__).parent
    for_import_dir = base_dir / "For-Import"
    
    # Find all TIFF files
    tiff_files = list(for_import_dir.glob("*.tiff")) + list(for_import_dir.glob("*.tif"))
    tiff_files = sorted(set(tiff_files))  # Remove duplicates
    
    print("=" * 80)
    print("JPG REGENERATION FROM TIFF FILES")
    print("=" * 80)
    print(f"For-Import directory: {for_import_dir}")
    print(f"Found {len(tiff_files)} TIFF files")
    print("\nProcessing...")
    print("=" * 80)
    
    replaced = 0
    skipped_smaller = 0
    skipped_no_existing = 0
    errors = 0
    
    for i, tiff_path in enumerate(tiff_files, 1):
        # Determine JPG filename
        jpg_filename = tiff_path.stem + ".jpg"
        jpg_path = for_import_dir / jpg_filename
        
        print(f"[{i}/{len(tiff_files)}] {tiff_path.name}")
        
        # Convert TIFF to JPG
        temp_jpg, new_size = convert_tiff_to_jpg(tiff_path, jpg_path)
        
        if temp_jpg is None:
            errors += 1
            continue
        
        # Check if existing JPG exists
        if not jpg_path.exists():
            # No existing JPG, just move the new one
            temp_jpg.rename(jpg_path)
            print(f"  ✓ Created new JPG: {new_size:,} bytes")
            skipped_no_existing += 1
            continue
        
        # Compare sizes
        old_size = jpg_path.stat().st_size
        
        if new_size > old_size:
            # New file is larger, replace it
            jpg_path.unlink()
            temp_jpg.rename(jpg_path)
            print(f"  ✓ REPLACED: {old_size:,} bytes → {new_size:,} bytes (Δ +{new_size - old_size:,})")
            replaced += 1
        else:
            # Keep old file
            temp_jpg.unlink()
            print(f"  - Kept existing: {old_size:,} bytes (new would be {new_size:,} bytes)")
            skipped_smaller += 1
    
    print("\n" + "=" * 80)
    print("SUMMARY")
    print("=" * 80)
    print(f"Total TIFF files:          {len(tiff_files)}")
    print(f"JPGs replaced (larger):    {replaced}")
    print(f"JPGs kept (old was larger): {skipped_smaller}")
    print(f"New JPGs created:          {skipped_no_existing}")
    print(f"Errors:                    {errors}")
    print("=" * 80)

if __name__ == '__main__':
    main()
