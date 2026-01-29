#!/usr/bin/env python3
"""
Analyze JPG images in For-Import directory to identify all-white or nearly white images.
Uses PIL/Pillow to examine pixel data rather than just file size.
"""
import csv
from pathlib import Path
from PIL import Image
import statistics

def analyze_image_whiteness(image_path):
    """
    Analyze an image to determine if it's all white or nearly white.
    
    Returns:
        dict with keys:
        - is_white: bool (True if image is all/nearly white)
        - mean_value: float (average pixel value 0-255)
        - std_dev: float (standard deviation of pixel values)
        - unique_colors: int (number of unique colors)
        - error: str or None (error message if image couldn't be analyzed)
    """
    try:
        with Image.open(image_path) as img:
            # Convert to RGB if necessary
            if img.mode != 'RGB':
                img = img.convert('RGB')
            
            # Get pixel data
            pixels = list(img.getdata())
            
            # Flatten RGB tuples to single list
            all_values = []
            for pixel in pixels:
                all_values.extend(pixel)
            
            # Calculate statistics
            mean_value = statistics.mean(all_values)
            std_dev = statistics.stdev(all_values) if len(all_values) > 1 else 0
            
            # Count unique colors
            unique_colors = len(set(pixels))
            
            # An image is "white" if:
            # 1. Mean value is very high (>250 out of 255)
            # 2. Standard deviation is very low (<5)
            # 3. Very few unique colors (<10)
            is_white = (mean_value > 250 and std_dev < 5 and unique_colors < 10)
            
            return {
                'is_white': is_white,
                'mean_value': round(mean_value, 2),
                'std_dev': round(std_dev, 2),
                'unique_colors': unique_colors,
                'error': None
            }
    except Exception as e:
        return {
            'is_white': None,
            'mean_value': None,
            'std_dev': None,
            'unique_colors': None,
            'error': str(e)
        }

def main():
    base_dir = Path(__file__).parent
    csv_file = base_dir / "all_single_tiffs_with_local_paths.csv"
    for_import_dir = base_dir / "For-Import"
    
    # Read CSV
    print("Reading CSV file...")
    rows = []
    with open(csv_file, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            rows.append(row)
    
    print(f"Found {len(rows)} TIFF records")
    print(f"\nAnalyzing JPG images in {for_import_dir}...")
    print("=" * 100)
    
    # Analyze JPG files
    results = []
    white_images = []
    errors = []
    not_found = 0
    analyzed = 0
    
    for i, row in enumerate(rows, 1):
        if i % 100 == 0:
            print(f"Progress: {i}/{len(rows)} ({i/len(rows)*100:.1f}%)")
        
        local_path = row['Local Path']
        if not local_path:
            not_found += 1
            continue
        
        # Get JPG filename
        tiff_filename = Path(local_path).name
        jpg_filename = tiff_filename.replace('.tiff', '.jpg').replace('.tif', '.jpg')
        jpg_path = for_import_dir / jpg_filename
        
        if not jpg_path.exists():
            not_found += 1
            continue
        
        # Analyze the image
        analysis = analyze_image_whiteness(jpg_path)
        analyzed += 1
        
        result = {
            'MMS ID': row['MMS ID'],
            'TIFF Filename': tiff_filename,
            'JPG Filename': jpg_filename,
            'JPG Size': row.get('JPG Size (bytes)', 'N/A'),
            'Is White': analysis['is_white'],
            'Mean Pixel Value': analysis['mean_value'],
            'Std Dev': analysis['std_dev'],
            'Unique Colors': analysis['unique_colors'],
            'Error': analysis['error'],
            'Local Path': local_path
        }
        results.append(result)
        
        if analysis['is_white']:
            white_images.append(result)
        
        if analysis['error']:
            errors.append(result)
    
    print(f"\n{'=' * 100}")
    print("ANALYSIS COMPLETE")
    print("=" * 100)
    print(f"Total records:           {len(rows)}")
    print(f"JPG files analyzed:      {analyzed}")
    print(f"JPG files not found:     {not_found}")
    print(f"Analysis errors:         {len(errors)}")
    print(f"\n🔴 ALL-WHITE IMAGES DETECTED: {len(white_images)}")
    
    # Save all results
    output_file = base_dir / "jpg_whiteness_analysis.csv"
    with open(output_file, 'w', encoding='utf-8', newline='') as f:
        if results:
            writer = csv.DictWriter(f, fieldnames=results[0].keys())
            writer.writeheader()
            writer.writerows(results)
    
    print(f"\nAll analysis results saved to: {output_file}")
    
    # Save white images list
    if white_images:
        white_output = base_dir / "confirmed_white_jpgs.csv"
        with open(white_output, 'w', encoding='utf-8', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=white_images[0].keys())
            writer.writeheader()
            writer.writerows(white_images)
        
        print(f"White images list saved to: {white_output}")
        
        print(f"\n{'=' * 100}")
        print("CONFIRMED WHITE IMAGES")
        print("=" * 100)
        print(f"{'MMS ID':<25} {'JPG Filename':<40} {'Size':>10} {'Mean':>6} {'StdDev':>7}")
        print("-" * 100)
        for img in white_images[:30]:  # Show first 30
            print(f"{img['MMS ID']:<25} {img['JPG Filename']:<40} {img['JPG Size']:>10} "
                  f"{img['Mean Pixel Value']:>6} {img['Std Dev']:>7}")
        
        if len(white_images) > 30:
            print(f"\n... and {len(white_images) - 30} more (see {white_output})")
    
    # Show errors if any
    if errors:
        print(f"\n{'=' * 100}")
        print(f"ERRORS ENCOUNTERED: {len(errors)}")
        print("=" * 100)
        for err in errors[:10]:
            print(f"{err['JPG Filename']}: {err['Error']}")

if __name__ == '__main__':
    main()
