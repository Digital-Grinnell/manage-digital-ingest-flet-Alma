#!/usr/bin/env .venv/bin/python3
"""
TIFF to JPG Batch Converter Utility

This standalone script reads MMS IDs and AWS S3 paths from a CSV file,
downloads TIFF files from S3, converts them to high-quality JPG derivatives,
and appends the JPG paths to the CSV.

Usage:
    python tiff_to_jpg_batch_converter.py

Input:
    - CSV file: /Users/mcfatem/GitHub/CABB/all_single_tiffs.csv
    - Columns: MMS ID, S3 Path

Output:
    - JPG derivatives stored in: ~/TIF-to-JPG-Derivatives/
    - Updated CSV with JPG paths appended as a new column
    - Log file: tiff_to_jpg_conversion.log

Dependencies:
    - Pillow (PIL): pip install Pillow
    - boto3: pip install boto3 (for AWS S3 access)
"""

import os
import sys
import csv
import logging
from pathlib import Path
from datetime import datetime
from PIL import Image, ImageCms
import tempfile
import shutil
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Setup logging
log_file = 'tiff_to_jpg_conversion.log'
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.FileHandler(log_file),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)


def convert_tiff_to_jpg(tiff_path, output_dir, base_name):
    """
    Convert a TIFF file to high-quality JPG.
    
    Args:
        tiff_path: Path to the source TIFF file
        output_dir: Directory where JPG should be saved
        base_name: Base name for the output JPG file
        
    Returns:
        str: Path to the created JPG file, or None if conversion failed
    """
    try:
        # Create output directory if it doesn't exist
        os.makedirs(output_dir, exist_ok=True)
        
        # Define output JPG path
        jpg_filename = f"{base_name}.jpg"
        jpg_path = os.path.join(output_dir, jpg_filename)
        
        # Get file size for logging
        tiff_size_mb = os.path.getsize(tiff_path) / (1024 * 1024)
        logger.info(f"  Converting: {os.path.basename(tiff_path)} ({tiff_size_mb:.2f} MB)")
        
        # Open and convert TIFF to JPG
        with Image.open(tiff_path) as img:
            # Convert to RGB if needed (TIFF might be CMYK, RGBA, etc.)
            if img.mode not in ('RGB', 'L'):
                # Convert CMYK or other modes to RGB
                if img.mode == 'CMYK':
                    # For CMYK images, use a more careful conversion
                    try:
                        # Try to use ICC profile if available
                        img = ImageCms.profileToProfile(img, 
                                                       ImageCms.createProfile('sRGB'), 
                                                       ImageCms.createProfile('sRGB'),
                                                       outputMode='RGB')
                        logger.debug(f"  Converted CMYK to RGB using ICC profile")
                    except Exception as e:
                        # Fall back to simple conversion
                        logger.debug(f"  ICC profile conversion failed, using fallback: {e}")
                        img = img.convert('RGB')
                else:
                    logger.debug(f"  Converting {img.mode} to RGB")
                    img = img.convert('RGB')
            
            # Save as high-quality JPG (95% quality for archival access copy)
            img.save(jpg_path, 'JPEG', quality=95, optimize=True)
        
        # Log success with file size
        jpg_size_mb = os.path.getsize(jpg_path) / (1024 * 1024)
        logger.info(f"  ✓ JPG created: {jpg_filename} ({jpg_size_mb:.2f} MB)")
        
        return jpg_path
        
    except Exception as e:
        logger.error(f"  ✗ Error converting {tiff_path}: {str(e)}")
        return None


def download_from_s3(s3_path, local_path, bucket_name='grinnell-edu-backup'):
    """
    Download a file from AWS S3.
    
    Args:
        s3_path: S3 object key/path
        local_path: Local path where file should be saved
        bucket_name: S3 bucket name
        
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        import boto3
        from botocore.exceptions import ClientError
        
        # Get AWS credentials from environment variables (loaded from .env)
        aws_access_key = os.getenv('AWS_ACCESS_KEY_ID')
        aws_secret_key = os.getenv('AWS_SECRET_ACCESS_KEY')
        aws_region = os.getenv('AWS_REGION', 'us-east-1')
        
        if not aws_access_key or not aws_secret_key:
            logger.error("  ✗ AWS credentials not found in .env file")
            logger.error("  Required: AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY")
            return False
        
        # Initialize S3 client with credentials from .env
        s3_client = boto3.client(
            's3',
            aws_access_key_id=aws_access_key,
            aws_secret_access_key=aws_secret_key,
            region_name=aws_region
        )
        
        # Download file
        logger.debug(f"  Downloading from S3: s3://{bucket_name}/{s3_path}")
        s3_client.download_file(bucket_name, s3_path, local_path)
        logger.debug(f"  Downloaded to: {local_path}")
        
        return True
        
    except ClientError as e:
        logger.error(f"  ✗ S3 download error: {e}")
        return False
    except ImportError:
        logger.error("  ✗ boto3 not installed. Install with: pip install boto3")
        return False
    except Exception as e:
        logger.error(f"  ✗ Error downloading from S3: {str(e)}")
        return False


def process_csv(input_csv_path, output_dir, bucket_name='grinnell-edu-backup', use_s3=True):
    """
    Process the CSV file, converting TIFF files to JPG and updating the CSV.
    
    Args:
        input_csv_path: Path to the input CSV file
        output_dir: Directory where JPG derivatives should be stored
        bucket_name: S3 bucket name (if using S3)
        use_s3: Whether to download from S3 (True) or use local paths (False)
        
    Returns:
        tuple: (total_rows, successful_conversions, failed_conversions)
    """
    # Expand home directory
    output_dir = os.path.expanduser(output_dir)
    
    # Create output directory
    os.makedirs(output_dir, exist_ok=True)
    logger.info(f"Output directory: {output_dir}")
    
    # Read the CSV file
    rows = []
    with open(input_csv_path, 'r', encoding='utf-8') as f:
        reader = csv.reader(f)
        rows = list(reader)
    
    if len(rows) == 0:
        logger.error("CSV file is empty")
        return 0, 0, 0
    
    # Check if header exists
    header = rows[0]
    logger.info(f"CSV columns: {header}")
    
    # Add new column for JPG path if not already present
    if len(header) < 3:
        header.append('JPG Path')
    
    # Process each row
    total_rows = len(rows) - 1  # Exclude header
    successful = 0
    failed = 0
    
    logger.info(f"Processing {total_rows} TIFF files...")
    
    for idx, row in enumerate(rows[1:], start=1):  # Skip header
        if len(row) < 2:
            logger.warning(f"Row {idx}: Incomplete data, skipping")
            row.append('')  # Add empty JPG path
            failed += 1
            continue
        
        mms_id = row[0].strip()
        s3_path = row[1].strip()
        
        # Extract filename from S3 path
        tiff_filename = os.path.basename(s3_path)
        base_name = os.path.splitext(tiff_filename)[0]
        
        logger.info(f"[{idx}/{total_rows}] Processing MMS ID: {mms_id}")
        logger.info(f"  TIFF: {tiff_filename}")
        
        # Determine the TIFF file path
        if use_s3:
            # Create temporary directory for downloads
            with tempfile.TemporaryDirectory() as temp_dir:
                local_tiff_path = os.path.join(temp_dir, tiff_filename)
                
                # Download from S3
                if not download_from_s3(s3_path, local_tiff_path, bucket_name):
                    logger.error(f"  Failed to download from S3")
                    row.append('')  # Add empty JPG path
                    failed += 1
                    continue
                
                # Convert to JPG
                jpg_path = convert_tiff_to_jpg(local_tiff_path, output_dir, base_name)
        else:
            # Use local path (for testing or local files)
            local_tiff_path = s3_path
            if not os.path.exists(local_tiff_path):
                logger.error(f"  TIFF file not found: {local_tiff_path}")
                row.append('')  # Add empty JPG path
                failed += 1
                continue
            
            # Convert to JPG
            jpg_path = convert_tiff_to_jpg(local_tiff_path, output_dir, base_name)
        
        # Update row with JPG path
        if jpg_path:
            # Ensure row has at least 3 columns
            while len(row) < 3:
                row.append('')
            row[2] = jpg_path
            successful += 1
            logger.info(f"  ✓ Success ({successful}/{total_rows})")
        else:
            # Ensure row has at least 3 columns
            while len(row) < 3:
                row.append('')
            row[2] = ''
            failed += 1
            logger.error(f"  ✗ Failed ({failed}/{total_rows})")
        
        # Log progress every 10 files
        if idx % 10 == 0:
            logger.info(f"Progress: {idx}/{total_rows} processed ({successful} successful, {failed} failed)")
    
    # Write updated CSV
    output_csv_path = input_csv_path.replace('.csv', '_with_jpg_paths.csv')
    with open(output_csv_path, 'w', encoding='utf-8', newline='') as f:
        writer = csv.writer(f)
        writer.writerows(rows)
    
    logger.info(f"Updated CSV saved to: {output_csv_path}")
    
    return total_rows, successful, failed


def main():
    """Main execution function."""
    logger.info("=" * 80)
    logger.info("TIFF to JPG Batch Converter")
    logger.info("=" * 80)
    logger.info(f"Start time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Configuration
    input_csv = '/Users/mcfatem/GitHub/CABB/all_single_tiffs.csv'
    output_directory = '~/TIF-to-JPG-Derivatives/'
    s3_bucket = 'grinnell-edu-backup'
    use_s3_download = True  # Set to False for local file testing
    
    # Verify input file exists
    if not os.path.exists(input_csv):
        logger.error(f"Input CSV not found: {input_csv}")
        sys.exit(1)
    
    logger.info(f"Input CSV: {input_csv}")
    logger.info(f"Output directory: {output_directory}")
    logger.info(f"S3 bucket: {s3_bucket}")
    logger.info(f"Use S3 download: {use_s3_download}")
    logger.info("")
    
    # Check dependencies
    try:
        import PIL
        logger.info(f"✓ Pillow version: {PIL.__version__}")
    except ImportError:
        logger.error("✗ Pillow not installed. Install with: pip install Pillow")
        sys.exit(1)
    
    if use_s3_download:
        try:
            import boto3
            logger.info(f"✓ boto3 installed")
            
            # Verify AWS credentials are in .env
            aws_access_key = os.getenv('AWS_ACCESS_KEY_ID')
            aws_secret_key = os.getenv('AWS_SECRET_ACCESS_KEY')
            
            if aws_access_key and aws_secret_key:
                logger.info(f"✓ AWS credentials loaded from .env")
                logger.info(f"  Region: {os.getenv('AWS_REGION', 'us-east-1')}")
            else:
                logger.error("✗ AWS credentials not found in .env file")
                logger.error("  Required: AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY")
                sys.exit(1)
                
        except ImportError:
            logger.error("✗ boto3 not installed. Install with: pip install boto3")
            logger.error("  Or set use_s3_download = False to use local files")
            sys.exit(1)
    
    logger.info("")
    logger.info("Starting conversion process...")
    logger.info("")
    
    # Process the CSV
    try:
        total, successful, failed = process_csv(
            input_csv, 
            output_directory, 
            s3_bucket, 
            use_s3_download
        )
        
        logger.info("")
        logger.info("=" * 80)
        logger.info("CONVERSION SUMMARY")
        logger.info("=" * 80)
        logger.info(f"Total files:       {total}")
        logger.info(f"Successful:        {successful}")
        logger.info(f"Failed:            {failed}")
        logger.info(f"Success rate:      {(successful/total*100) if total > 0 else 0:.1f}%")
        logger.info(f"End time:          {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        logger.info(f"Log file:          {os.path.abspath(log_file)}")
        logger.info("=" * 80)
        
    except KeyboardInterrupt:
        logger.warning("\n\nProcess interrupted by user (Ctrl+C)")
        logger.info("Partial results may have been saved")
        sys.exit(1)
    except Exception as e:
        logger.error(f"\n\nUnexpected error: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        sys.exit(1)


if __name__ == '__main__':
    main()
