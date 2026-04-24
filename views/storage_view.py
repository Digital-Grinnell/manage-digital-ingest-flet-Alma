"""
CSV Generator view for creating CSV rows from selected files.
"""
import os
import json
import csv
import re
import flet as ft
import pandas as pd
from datetime import datetime

import utils
from .base_view import BaseView


class StorageView(BaseView):
    
    def __init__(self, page: ft.Page):
        """Initialize the CSV generator view."""
        super().__init__(page)
        self.csv_data_table = None
        self.generated_csv_data = []
        self.generated_rows_text = None
        self.export_button = None
        self.clear_button = None
        self.merge_button = None
        self.metadata_csv_path = None
        self.metadata_df = None
        self.compound_checkbox = None
    
    def load_csv_headings(self):
        """Load CSV headings from verified headings file."""
        try:
            headings_file = "_data/verified_CSV_headings_for_Alma-D.csv"
            with open(headings_file, 'r', encoding='utf-8') as f:
                reader = csv.reader(f)
                headings = next(reader)
                self.logger.info(f"Loaded {len(headings)} CSV headings from {headings_file}")
                return headings
        except Exception as e:
            self.logger.error(f"Failed to load CSV headings: {e}")
            return []
    
    def generate_csv_rows(self, e):
        """Generate CSV rows from selected file paths."""
        # Get selected file paths from session
        file_paths = self.page.session.get("selected_file_paths") or []
        temp_file_info = self.page.session.get("temp_file_info") or []
        temp_objs_dir = self.page.session.get("temp_objs_directory")
        temp_tn_dir = self.page.session.get("temp_tn_directory")
        temp_small_dir = self.page.session.get("temp_small_directory")
        
        if not file_paths:
            self.show_snack("No files selected. Please use File Selector first.", is_error=True)
            return
        
        # Load CSV headings
        headings = self.load_csv_headings()
        if not headings:
            self.show_snack("Failed to load CSV headings", is_error=True)
            return
        
        # Check if manual compound object processing is requested
        force_compound = self.compound_checkbox and self.compound_checkbox.value
        
        # First pass: Detect compound objects by grouping files with _<integer> or <space><integer> pattern
        compound_groups = {}
        standalone_files = []
        files_with_basename = {}  # Track files that might be implicit part 1
        
        # If manual compound processing is enabled and we have 2+ files, force all files into one compound
        if force_compound and len(file_paths) >= 2:
            self.logger.info(f"Manual compound object processing: forcing {len(file_paths)} files into a single compound")
            
            # Generate a base name from the first file or use a generic name
            first_filename = os.path.basename(file_paths[0])
            base_name = os.path.splitext(first_filename)[0]
            # Remove any trailing numbers and separators from base name
            base_name = re.sub(r'[_ ]\d+$', '', base_name)
            
            # Create compound group with all files numbered sequentially
            compound_groups[base_name] = [(i + 1, file_path) for i, file_path in enumerate(file_paths)]
        else:
            # Use automatic detection
            for file_path in file_paths:
                filename = os.path.basename(file_path)
                name_without_ext = os.path.splitext(filename)[0]
                
                # Check if filename ends with _<integer> or <space><integer>
                match = re.match(r'^(.+)[_ ](\d+)$', name_without_ext)
                if match:
                    base_name = match.group(1)
                    part_number = int(match.group(2))
                    
                    if base_name not in compound_groups:
                        compound_groups[base_name] = []
                    compound_groups[base_name].append((part_number, file_path))
                else:
                    # This might be a standalone file OR an implicit part 1
                    # Store it temporarily to check later
                    files_with_basename[name_without_ext] = file_path
            
            # Second pass: Check if any basename files have corresponding _2, _3, etc.
            # If so, treat the basename file as part 1 of a compound
            for basename, base_file_path in files_with_basename.items():
                if basename in compound_groups:
                    # This basename has numbered parts, so this is part 1
                    compound_groups[basename].insert(0, (1, base_file_path))
                    self.logger.info(f"Detected implicit part 1 for compound '{basename}': {os.path.basename(base_file_path)}")
                else:
                    # No numbered parts found, treat as standalone
                    standalone_files.append(base_file_path)
            
            # Third pass: Regroup files where a "part 1" with trailing number exists in compound_groups
            # E.g., "Silverman and Fardman 15" (part=15 of "Silverman and Fardman") should actually be
            # part 1 of "Silverman and Fardman 15" group (which has parts 2 and 3)
            regrouped = {}
            for base_name in list(compound_groups.keys()):
                parts = compound_groups[base_name]
                # Check if any part in this group could actually be part 1 of another group
                for part_num, file_path in parts[:]:  # Iterate over copy
                    filename_noext = os.path.splitext(os.path.basename(file_path))[0]
                    # Check if this filename (which is base_name + separator + part_num) exists as a basename in compound_groups
                    if filename_noext in compound_groups and filename_noext != base_name:
                        # This file should be part 1 of the filename_noext group, not part of base_name group
                        if filename_noext not in regrouped:
                            regrouped[filename_noext] = []
                        regrouped[filename_noext].append((1, file_path))  # It's part 1 of the other group
                        parts.remove((part_num, file_path))
                        self.logger.info(f"Regrouped '{os.path.basename(file_path)}' as part 1 of compound '{filename_noext}'")
            
            # Apply regrouping
            for new_base, new_parts in regrouped.items():
                if new_base in compound_groups:
                    # Prepend part 1 to the existing group
                    compound_groups[new_base] = new_parts + compound_groups[new_base]
        
        # Sort compound groups by part number
        for base_name in compound_groups:
            compound_groups[base_name].sort(key=lambda x: x[0])
        
        # Generate rows
        self.generated_csv_data = []
        updated_temp_file_info = []
        file_idx = 0
        
        # Process compound objects first
        for base_name, parts in compound_groups.items():
            if len(parts) >= 2:  # Valid compound object (minimum 2 children)
                self.logger.info(f"Detected compound object '{base_name}' with {len(parts)} parts")
                
                # Generate parent row
                parent_row = {heading: "" for heading in headings}
                parent_unique_id = utils.generate_unique_id(self.page)
                
                # Extract numeric portion for Handle URL
                numeric_part = parent_unique_id.split('_')[-1] if '_' in parent_unique_id else parent_unique_id
                
                if 'originating_system_id' in parent_row:
                    parent_row['originating_system_id'] = parent_unique_id
                if 'group_id' in parent_row:
                    parent_row['group_id'] = parent_unique_id
                if 'dc:identifier' in parent_row:
                    parent_row['dc:identifier'] = f"http://hdl.handle.net/11084/{numeric_part}"
                if 'dc:title' in parent_row:
                    parent_row['dc:title'] = base_name
                if 'dc:type' in parent_row:
                    parent_row['dc:type'] = "compound"
                if 'compoundrelationship' in parent_row:
                    parent_row['compoundrelationship'] = f"parent:{base_name}"
                
                # Build Table of Contents from children
                toc_entries = []
                
                # Process child rows
                for part_num, file_path in parts:
                    child_row = {heading: "" for heading in headings}
                    
                    filename = os.path.basename(file_path)
                    name_without_ext = os.path.splitext(filename)[0]
                    file_ext = os.path.splitext(filename)[1]
                    
                    # Check if this file already has temp_file_info (from file selector)
                    existing_info = None
                    if file_idx < len(temp_file_info):
                        existing_info = temp_file_info[file_idx]
                    
                    # Check if this is a .wav audio file
                    is_wav = file_ext.lower() == '.wav'
                    # Check if this is a .tif/.tiff image file
                    is_tiff = file_ext.lower() in ['.tif', '.tiff']
                    
                    # Check if this .wav file was already renamed by file selector
                    already_renamed_wav = is_wav and existing_info and existing_info.get('is_wav', False)
                    # Check if this .tiff file was already renamed by file selector
                    already_renamed_tiff = is_tiff and existing_info and existing_info.get('is_tiff', False)
                    
                    if already_renamed_wav:
                        # Use the existing dg_* filename from file selector
                        wav_filename = existing_info.get('sanitized_filename', filename)
                        # Extract the base name (without .wav extension) for the .mp3
                        base_id = os.path.splitext(wav_filename)[0]
                        dg_filename = f"{base_id}.mp3"
                        child_unique_id = base_id  # The unique ID is already in the filename
                    elif already_renamed_tiff:
                        # Use the existing dg_* filename from file selector
                        tiff_filename = existing_info.get('sanitized_filename', filename)
                        # Extract the base name (without .tif extension) for the .jpg
                        base_id = os.path.splitext(tiff_filename)[0]
                        dg_filename = f"{base_id}.jpg"
                        child_unique_id = base_id  # The unique ID is already in the filename
                    else:
                        # Generate unique ID for child
                        child_unique_id = utils.generate_unique_id(self.page)
                        
                        # Create new filename with dg_* convention
                        if is_wav:
                            # For .wav files, primary representation is .mp3
                            dg_filename = f"{child_unique_id}.mp3"
                            # Preservation copy is the .wav
                            wav_filename = f"{child_unique_id}.wav"
                        elif is_tiff:
                            # For .tiff files, primary representation is .jpg
                            dg_filename = f"{child_unique_id}.jpg"
                            # Preservation copy is the .tiff
                            tiff_filename = f"{child_unique_id}{file_ext}"
                        else:
                            dg_filename = f"{child_unique_id}{file_ext}"
                    
                    child_numeric_part = child_unique_id.split('_')[-1] if '_' in child_unique_id else child_unique_id
                    
                    # Set child fields
                    if 'file_name_1' in child_row:
                        child_row['file_name_1'] = dg_filename
                    
                    # For .wav files, set file_name_2 to the .wav preservation copy
                    if is_wav and 'file_name_2' in child_row:
                        child_row['file_name_2'] = wav_filename
                    
                    # For .tiff files, set file_name_2 to the .tiff preservation copy
                    if is_tiff and 'file_name_2' in child_row:
                        child_row['file_name_2'] = tiff_filename
                    
                    if 'originating_system_id' in child_row:
                        child_row['originating_system_id'] = child_unique_id
                    if 'group_id' in child_row:
                        child_row['group_id'] = parent_unique_id
                    if 'dc:identifier' in child_row:
                        child_row['dc:identifier'] = f"http://hdl.handle.net/11084/{child_numeric_part}"
                    if 'dc:title' in child_row:
                        child_title = f"{base_name} - Part {part_num}"
                        child_row['dc:title'] = child_title
                        toc_entries.append(child_title)
                    
                    # Set dc:type to "Sound" for audio files
                    if is_wav and 'dc:type' in child_row:
                        child_row['dc:type'] = 'Sound'
                    
                    # Set dc:type to "Image" for TIFF files
                    if is_tiff and 'dc:type' in child_row:
                        child_row['dc:type'] = 'Image'
                    
                    if 'compoundrelationship' in child_row:
                        child_row['compoundrelationship'] = f"child:part{part_num}"
                    if 'rep_label' in child_row:
                        child_row['rep_label'] = child_row.get('dc:title', '')
                    if 'rep_public_note' in child_row:
                        child_row['rep_public_note'] = child_row.get('dc:type', '')
                    
                    # Rename temp file
                    if temp_objs_dir and os.path.exists(temp_objs_dir):
                        try:
                            old_temp_path = file_path
                            
                            if is_wav and not already_renamed_wav:
                                # For .wav files not yet renamed, rename to .wav extension (preservation copy)
                                new_temp_path = os.path.join(temp_objs_dir, wav_filename)
                            elif is_tiff and not already_renamed_tiff:
                                # For .tiff files not yet renamed, rename to .tiff extension (preservation copy)
                                new_temp_path = os.path.join(temp_objs_dir, tiff_filename)
                            elif not is_wav and not is_tiff:
                                # For non-wav/non-tiff files, use the dg_filename
                                new_temp_path = os.path.join(temp_objs_dir, dg_filename)
                            else:
                                # File already renamed by file selector, no need to rename
                                new_temp_path = old_temp_path
                            
                            if os.path.exists(old_temp_path) and old_temp_path != new_temp_path:
                                os.rename(old_temp_path, new_temp_path)
                                self.logger.info(f"Renamed temp file: {os.path.basename(old_temp_path)} -> {os.path.basename(new_temp_path)}")
                                
                                # If this is a .wav file, also rename the corresponding .mp3 if it exists
                                if is_wav and not already_renamed_wav:
                                    old_mp3_name = os.path.splitext(os.path.basename(old_temp_path))[0] + '.mp3'
                                    old_mp3_path = os.path.join(temp_objs_dir, old_mp3_name)
                                    new_mp3_name = os.path.splitext(wav_filename)[0] + '.mp3'
                                    new_mp3_path = os.path.join(temp_objs_dir, new_mp3_name)
                                    
                                    if os.path.exists(old_mp3_path):
                                        os.rename(old_mp3_path, new_mp3_path)
                                        self.logger.info(f"Renamed corresponding MP3: {old_mp3_name} -> {new_mp3_name}")
                                
                                # If this is a .tiff file, also rename the corresponding .jpg if it exists
                                if is_tiff and not already_renamed_tiff:
                                    old_jpg_name = os.path.splitext(os.path.basename(old_temp_path))[0] + '.jpg'
                                    old_jpg_path = os.path.join(temp_objs_dir, old_jpg_name)
                                    new_jpg_name = os.path.splitext(tiff_filename)[0] + '.jpg'
                                    new_jpg_path = os.path.join(temp_objs_dir, new_jpg_name)
                                    
                                    if os.path.exists(old_jpg_path):
                                        os.rename(old_jpg_path, new_jpg_path)
                                        self.logger.info(f"Renamed corresponding JPG: {old_jpg_name} -> {new_jpg_name}")
                                
                                # Rename thumbnail in TN directory if it exists
                                if temp_tn_dir and os.path.exists(temp_tn_dir):
                                    old_basename = os.path.splitext(os.path.basename(old_temp_path))[0]
                                    old_thumb_name = f"{old_basename}.jpg.clientThumb"
                                    old_thumb_path = os.path.join(temp_tn_dir, old_thumb_name)
                                    
                                    # Determine new thumbnail name based on file type
                                    if is_wav and not already_renamed_wav:
                                        new_basename = os.path.splitext(wav_filename)[0]
                                    elif is_tiff and not already_renamed_tiff:
                                        new_basename = os.path.splitext(tiff_filename)[0]
                                    elif not is_wav and not is_tiff:
                                        new_basename = os.path.splitext(dg_filename)[0]
                                    else:
                                        new_basename = old_basename
                                    
                                    new_thumb_name = f"{new_basename}.jpg.clientThumb"
                                    new_thumb_path = os.path.join(temp_tn_dir, new_thumb_name)
                                    
                                    if os.path.exists(old_thumb_path) and old_thumb_path != new_thumb_path:
                                        os.rename(old_thumb_path, new_thumb_path)
                                        self.logger.info(f"Renamed TN thumbnail: {old_thumb_name} -> {new_thumb_name}")
                                
                                # Rename small derivative in SMALL directory if it exists
                                if temp_small_dir and os.path.exists(temp_small_dir):
                                    old_basename = os.path.splitext(os.path.basename(old_temp_path))[0]
                                    old_small_name = f"{old_basename}.jpg.clientViewFullSize"
                                    old_small_path = os.path.join(temp_small_dir, old_small_name)
                                    
                                    # Determine new small derivative name based on file type
                                    if is_wav and not already_renamed_wav:
                                        new_basename = os.path.splitext(wav_filename)[0]
                                    elif is_tiff and not already_renamed_tiff:
                                        new_basename = os.path.splitext(tiff_filename)[0]
                                    elif not is_wav and not is_tiff:
                                        new_basename = os.path.splitext(dg_filename)[0]
                                    else:
                                        new_basename = old_basename
                                    
                                    new_small_name = f"{new_basename}.jpg.clientViewFullSize"
                                    new_small_path = os.path.join(temp_small_dir, new_small_name)
                                    
                                    if os.path.exists(old_small_path) and old_small_path != new_small_path:
                                        os.rename(old_small_path, new_small_path)
                                        self.logger.info(f"Renamed SMALL derivative: {old_small_name} -> {new_small_name}")
                                
                                if file_idx < len(temp_file_info):
                                    info = temp_file_info[file_idx].copy()
                                    info['temp_path'] = new_temp_path
                                    if is_wav:
                                        info['sanitized_filename'] = wav_filename
                                        info['is_wav'] = True
                                    elif is_tiff:
                                        info['sanitized_filename'] = tiff_filename
                                        info['is_tiff'] = True
                                    else:
                                        info['sanitized_filename'] = dg_filename
                                    updated_temp_file_info.append(info)
                                else:
                                    new_info = {
                                        'original_path': file_path,
                                        'original_filename': filename,
                                        'temp_path': new_temp_path,
                                        'sanitized_filename': wav_filename if is_wav else (tiff_filename if is_tiff else dg_filename)
                                    }
                                    if is_wav:
                                        new_info['is_wav'] = True
                                    elif is_tiff:
                                        new_info['is_tiff'] = True
                                    updated_temp_file_info.append(new_info)
                        except Exception as rename_err:
                            self.logger.error(f"Failed to rename temp file {filename}: {rename_err}")
                    
                    file_idx += 1
                    self.generated_csv_data.append(child_row)
                
                # Set parent's Table of Contents
                if 'dcterms:tableOfContents' in parent_row and toc_entries:
                    parent_row['dcterms:tableOfContents'] = " | ".join(toc_entries)
                
                # Insert parent at the beginning of the compound group
                # Find the index where the first child was added
                insert_idx = len(self.generated_csv_data) - len(parts)
                self.generated_csv_data.insert(insert_idx, parent_row)
            else:
                # Treat single-part as standalone
                standalone_files.extend([part[1] for part in parts])
        
        # Process standalone files
        for file_path in standalone_files:
            # Create a row dictionary with all headings as keys
            row = {heading: "" for heading in headings}
            
            # Populate basic fields from filename
            filename = os.path.basename(file_path)
            name_without_ext = os.path.splitext(filename)[0]
            file_ext = os.path.splitext(filename)[1]
            
            # Check if this file already has temp_file_info (from file selector)
            existing_info = None
            if file_idx < len(temp_file_info):
                existing_info = temp_file_info[file_idx]
            
            # Check if this is a .wav audio file
            is_wav = file_ext.lower() == '.wav'
            # Check if this is a .tif/.tiff image file
            is_tiff = file_ext.lower() in ['.tif', '.tiff']
            
            # Check if this .wav file was already renamed by file selector
            already_renamed_wav = is_wav and existing_info and existing_info.get('is_wav', False)
            # Check if this .tiff file was already renamed by file selector
            already_renamed_tiff = is_tiff and existing_info and existing_info.get('is_tiff', False)
            
            if already_renamed_wav:
                # Use the existing dg_* filename from file selector
                wav_filename = existing_info.get('sanitized_filename', filename)
                # Extract the base name (without .wav extension) for the .mp3
                base_id = os.path.splitext(wav_filename)[0]
                dg_filename = f"{base_id}.mp3"
                unique_id = base_id  # The unique ID is already in the filename
            elif already_renamed_tiff:
                # Use the existing dg_* filename from file selector
                tiff_filename = existing_info.get('sanitized_filename', filename)
                # Extract the base name (without .tif extension) for the .jpg
                base_id = os.path.splitext(tiff_filename)[0]
                dg_filename = f"{base_id}.jpg"
                unique_id = base_id  # The unique ID is already in the filename
            else:
                # Generate unique ID for this file
                unique_id = utils.generate_unique_id(self.page)
                
                # Create new filename with dg_* convention
                if is_wav:
                    # For .wav files, primary representation is .mp3
                    dg_filename = f"{unique_id}.mp3"
                    # Preservation copy is the .wav
                    wav_filename = f"{unique_id}.wav"
                elif is_tiff:
                    # For .tiff files, primary representation is .jpg
                    dg_filename = f"{unique_id}.jpg"
                    # Preservation copy is the .tiff
                    tiff_filename = f"{unique_id}{file_ext}"
                else:
                    dg_filename = f"{unique_id}{file_ext}"
            
            # Extract numeric portion for Handle URL
            numeric_part = unique_id.split('_')[-1] if '_' in unique_id else unique_id
            
            # Set file_name_1 to the dg_* filename (primary representation)
            if 'file_name_1' in row:
                row['file_name_1'] = dg_filename
            
            # For .wav files, set file_name_2 to the .wav preservation copy
            if is_wav and 'file_name_2' in row:
                row['file_name_2'] = wav_filename
            
            # For .tiff files, set file_name_2 to the .tiff preservation copy
            if is_tiff and 'file_name_2' in row:
                row['file_name_2'] = tiff_filename
            
            # Set dc:identifier Handle URL
            if 'dc:identifier' in row:
                row['dc:identifier'] = f"http://hdl.handle.net/11084/{numeric_part}"
            
            # Set dc:title to original filename without extension
            if 'dc:title' in row:
                if existing_info:
                    # Use original filename from temp_file_info
                    orig_name = os.path.splitext(existing_info.get('original_filename', filename))[0]
                    row['dc:title'] = orig_name
                else:
                    row['dc:title'] = name_without_ext
            
            # Set dc:type to "Sound" for audio files
            if is_wav and 'dc:type' in row:
                row['dc:type'] = 'Sound'
            
            # Set dc:type to "Image" for TIFF files
            if is_tiff and 'dc:type' in row:
                row['dc:type'] = 'Image'
            
            # Rename temp file if we have temp directory info
            if temp_objs_dir and os.path.exists(temp_objs_dir):
                try:
                    old_temp_path = file_path
                    
                    if is_wav and not already_renamed_wav:
                        # For .wav files not yet renamed, rename to .wav extension (preservation copy)
                        new_temp_path = os.path.join(temp_objs_dir, wav_filename)
                    elif is_tiff and not already_renamed_tiff:
                        # For .tiff files not yet renamed, rename to .tiff extension (preservation copy)
                        new_temp_path = os.path.join(temp_objs_dir, tiff_filename)
                    elif not is_wav and not is_tiff:
                        # For non-wav/non-tiff files, use the dg_filename
                        new_temp_path = os.path.join(temp_objs_dir, dg_filename)
                    else:
                        # File already renamed by file selector, no need to rename
                        new_temp_path = old_temp_path
                    
                    # Only rename if the file exists and new name is different
                    if os.path.exists(old_temp_path) and old_temp_path != new_temp_path:
                        os.rename(old_temp_path, new_temp_path)
                        self.logger.info(f"Renamed temp file: {os.path.basename(old_temp_path)} -> {os.path.basename(new_temp_path)}")
                        
                        # If this is a .wav file, also rename the corresponding .mp3 if it exists
                        if is_wav and not already_renamed_wav:
                            old_mp3_name = os.path.splitext(os.path.basename(old_temp_path))[0] + '.mp3'
                            old_mp3_path = os.path.join(temp_objs_dir, old_mp3_name)
                            new_mp3_name = os.path.splitext(wav_filename)[0] + '.mp3'
                            new_mp3_path = os.path.join(temp_objs_dir, new_mp3_name)
                            
                            if os.path.exists(old_mp3_path):
                                os.rename(old_mp3_path, new_mp3_path)
                                self.logger.info(f"Renamed corresponding MP3: {old_mp3_name} -> {new_mp3_name}")
                        
                        # If this is a .tiff file, also rename the corresponding .jpg if it exists
                        if is_tiff and not already_renamed_tiff:
                            old_jpg_name = os.path.splitext(os.path.basename(old_temp_path))[0] + '.jpg'
                            old_jpg_path = os.path.join(temp_objs_dir, old_jpg_name)
                            new_jpg_name = os.path.splitext(tiff_filename)[0] + '.jpg'
                            new_jpg_path = os.path.join(temp_objs_dir, new_jpg_name)
                            
                            if os.path.exists(old_jpg_path):
                                os.rename(old_jpg_path, new_jpg_path)
                                self.logger.info(f"Renamed corresponding JPG: {old_jpg_name} -> {new_jpg_name}")
                        
                        # Rename thumbnail in TN directory if it exists
                        if temp_tn_dir and os.path.exists(temp_tn_dir):
                            old_basename = os.path.splitext(os.path.basename(old_temp_path))[0]
                            old_thumb_name = f"{old_basename}.jpg.clientThumb"
                            old_thumb_path = os.path.join(temp_tn_dir, old_thumb_name)
                            
                            # Determine new thumbnail name based on file type
                            if is_wav and not already_renamed_wav:
                                new_basename = os.path.splitext(wav_filename)[0]
                            elif is_tiff and not already_renamed_tiff:
                                new_basename = os.path.splitext(tiff_filename)[0]
                            elif not is_wav and not is_tiff:
                                new_basename = os.path.splitext(dg_filename)[0]
                            else:
                                new_basename = old_basename
                            
                            new_thumb_name = f"{new_basename}.jpg.clientThumb"
                            new_thumb_path = os.path.join(temp_tn_dir, new_thumb_name)
                            
                            if os.path.exists(old_thumb_path) and old_thumb_path != new_thumb_path:
                                os.rename(old_thumb_path, new_thumb_path)
                                self.logger.info(f"Renamed TN thumbnail: {old_thumb_name} -> {new_thumb_name}")
                        
                        # Rename small derivative in SMALL directory if it exists
                        if temp_small_dir and os.path.exists(temp_small_dir):
                            old_basename = os.path.splitext(os.path.basename(old_temp_path))[0]
                            old_small_name = f"{old_basename}.jpg.clientViewFullSize"
                            old_small_path = os.path.join(temp_small_dir, old_small_name)
                            
                            # Determine new small derivative name based on file type
                            if is_wav and not already_renamed_wav:
                                new_basename = os.path.splitext(wav_filename)[0]
                            elif is_tiff and not already_renamed_tiff:
                                new_basename = os.path.splitext(tiff_filename)[0]
                            elif not is_wav and not is_tiff:
                                new_basename = os.path.splitext(dg_filename)[0]
                            else:
                                new_basename = old_basename
                            
                            new_small_name = f"{new_basename}.jpg.clientViewFullSize"
                            new_small_path = os.path.join(temp_small_dir, new_small_name)
                            
                            if os.path.exists(old_small_path) and old_small_path != new_small_path:
                                os.rename(old_small_path, new_small_path)
                                self.logger.info(f"Renamed SMALL derivative: {old_small_name} -> {new_small_name}")
                        
                        # Update temp_file_info if available
                        if file_idx < len(temp_file_info):
                            info = temp_file_info[file_idx].copy()
                            info['temp_path'] = new_temp_path
                            if is_wav:
                                info['sanitized_filename'] = wav_filename
                                info['is_wav'] = True
                            elif is_tiff:
                                info['sanitized_filename'] = tiff_filename
                                info['is_tiff'] = True
                            else:
                                info['sanitized_filename'] = dg_filename
                            updated_temp_file_info.append(info)
                        else:
                            # Create new info entry
                            new_info = {
                                'original_path': file_path,
                                'original_filename': filename,
                                'temp_path': new_temp_path,
                                'sanitized_filename': wav_filename if is_wav else (tiff_filename if is_tiff else dg_filename)
                            }
                            if is_wav:
                                new_info['is_wav'] = True
                            elif is_tiff:
                                new_info['is_tiff'] = True
                            updated_temp_file_info.append(new_info)
                    elif already_renamed_wav or already_renamed_tiff:
                        # Keep existing info for already-renamed files
                        if file_idx < len(temp_file_info):
                            updated_temp_file_info.append(temp_file_info[file_idx])
                except Exception as rename_err:
                    self.logger.error(f"Failed to rename temp file {filename}: {rename_err}")
                    # Keep original temp file info if rename fails
                    if file_idx < len(temp_file_info):
                        updated_temp_file_info.append(temp_file_info[file_idx])
            
            file_idx += 1
            
            # Add to generated data
            self.generated_csv_data.append(row)
        
        # Update session with new temp file info
        if updated_temp_file_info:
            self.page.session.set("temp_file_info", updated_temp_file_info)
            # Update temp_files list with new paths
            new_temp_paths = [info['temp_path'] for info in updated_temp_file_info]
            self.page.session.set("temp_files", new_temp_paths)
            self.page.session.set("selected_file_paths", new_temp_paths)
        
        self.logger.info(f"Generated {len(self.generated_csv_data)} CSV rows")
        
        # Save to persistent.json
        self.save_generated_csv()
        
        # Save generated CSV to temp directory
        csv_filename = self.save_generated_csv_to_temp()
        
        # Append a new row for the CSV file itself (before creating values.csv)
        if csv_filename:
            self.append_csv_metadata_row(csv_filename)
        
        # Create values.csv in temp directory
        self.save_values_csv()
        
        # Update display
        self.display_csv_data()
        
        # Update the generated rows count
        if self.generated_rows_text:
            self.generated_rows_text.value = f"Generated Rows: {len(self.generated_csv_data)}"
        
        # Enable export and clear buttons
        if self.export_button:
            self.export_button.disabled = False
        if self.clear_button:
            self.clear_button.disabled = False
        
        # Enable merge button if metadata is already loaded
        if self.merge_button and self.metadata_df is not None:
            self.logger.info("Enabling merge button after CSV generation (metadata already loaded)")
            self.merge_button.disabled = False
        
        self.page.update()
        
        self.show_snack(f"Generated {len(self.generated_csv_data)} CSV rows")
    
    def save_generated_csv(self):
        """Save generated CSV data to session storage."""
        try:
            # Save to session storage
            self.page.session.set("generated_csv_rows", self.generated_csv_data)
            self.logger.info(f"Saved {len(self.generated_csv_data)} rows to session storage")
        except Exception as e:
            self.logger.error(f"Failed to save generated CSV data: {e}")
    
    def save_generated_csv_to_temp(self):
        """
        Save the generated CSV file to the temp directory with a timestamped name.
        Returns the CSV filename if successful, None otherwise.
        """
        try:
            # Get temp directory from session
            temp_dir = self.page.session.get("temp_directory")
            
            if not temp_dir or not os.path.exists(temp_dir):
                self.logger.warning("No temp directory available, skipping CSV file creation")
                return None
            
            if not self.generated_csv_data:
                self.logger.warning("No CSV data to save")
                return None
            
            # Convert to DataFrame
            df = pd.DataFrame(self.generated_csv_data)
            
            # Create filename with timestamp
            from datetime import datetime
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            csv_filename = f"generated_metadata_{timestamp}.csv"
            csv_path = os.path.join(temp_dir, csv_filename)
            
            # Save CSV file
            df.to_csv(csv_path, index=False, encoding='utf-8', quoting=0)
            
            # Store the CSV filename in session for the upload script
            self.page.session.set("generated_csv_filename", csv_filename)
            
            self.logger.info(f"Saved generated CSV to: {csv_path} ({len(df)} rows)")
            return csv_filename
            
        except Exception as e:
            self.logger.error(f"Failed to save generated CSV to temp: {e}")
            return None
    
    def append_csv_metadata_row(self, csv_filename):
        """
        Append a new row to the generated CSV data for the CSV file itself.
        This self-referential row is required for Alma Digital upload.
        
        Args:
            csv_filename: The name of the generated CSV file
        """
        try:
            # Only append in Alma mode
            current_mode = self.page.session.get("mode", "Alma")
            if current_mode != "Alma":
                self.logger.info("Skipping CSV metadata row append (not in Alma mode)")
                return
            
            # Generate unique ID
            unique_id = utils.generate_unique_id(self.page)
            
            # Extract numeric portion for Handle URL
            numeric_part = unique_id.split('_')[-1] if '_' in unique_id else unique_id
            handle_url = f"http://hdl.handle.net/11084/{numeric_part}"
            
            # Get CSV headings to create a proper row
            headings = self.load_csv_headings()
            if not headings:
                self.logger.error("Cannot append CSV metadata row: failed to load headings")
                return
            
            # Create new row with all empty values first
            new_row = {col: '' for col in headings}
            
            # Populate specific columns
            new_row['originating_system_id'] = unique_id
            new_row['dc:identifier'] = handle_url  # Use Handle URL format
            new_row['collection_id'] = '81342586470004641'  # Self-referential row has collection_id
            new_row['dc:type'] = 'Dataset'  # CSV file is a dataset
            new_row['dc:title'] = csv_filename
            new_row['file_name_1'] = csv_filename
            
            # Append the new row to generated_csv_data
            self.generated_csv_data.append(new_row)
            
            self.logger.info(f"Appended CSV metadata row with ID: {unique_id}, filename: {csv_filename}")
            
            # Update session storage
            self.page.session.set("generated_csv_rows", self.generated_csv_data)
            
        except Exception as e:
            self.logger.error(f"Failed to append CSV metadata row: {e}")
    
    def save_values_csv(self):
        """
        Save a values.csv file in the temp directory with multi-valued field expansion.
        This file has no comment rows, collection_id blanked (except last row), 
        and multi-valued fields (containing |) expanded into multiple single-valued columns.
        """
        try:
            # Get temp directory from session
            temp_dir = self.page.session.get("temp_directory")
            
            if not temp_dir or not os.path.exists(temp_dir):
                self.logger.warning("No temp directory available, skipping values.csv creation")
                return False
            
            if not self.generated_csv_data:
                self.logger.warning("No CSV data to save to values.csv")
                return False
            
            # Convert to DataFrame
            df = pd.DataFrame(self.generated_csv_data)
            
            # Blank out collection_id column for all rows EXCEPT the last one (self-referential CSV row)
            if 'collection_id' in df.columns and len(df) > 0:
                # Store the last row's collection_id value
                last_collection_id = df.iloc[-1]['collection_id'] if pd.notna(df.iloc[-1]['collection_id']) else ''
                # Blank out all collection_id values
                df['collection_id'] = ''
                # Restore the last row's collection_id
                df.iloc[-1, df.columns.get_loc('collection_id')] = last_collection_id
                self.logger.info(f"Blanked out collection_id column in values.csv (except last row: {last_collection_id})")
            
            # EXPANSION LOGIC: Analyze and expand multi-valued fields (with | separators)
            # Step 1: Count max occurrences of | in each column
            heading_counter = {}
            for col in df.columns:
                max_count = 1  # At least 1 column for every heading
                for value in df[col].fillna('').astype(str):
                    if len(value) > 0:
                        parts = value.count('|') + 1
                        if parts > max_count:
                            max_count = parts
                heading_counter[col] = max_count
            
            # Log expansion details
            expanded_columns = {col: count for col, count in heading_counter.items() if count > 1}
            if expanded_columns:
                self.logger.info(f"Expanding multi-valued columns: {expanded_columns}")
            
            # Step 2: Build expanded headings (duplicate column names for multi-valued fields)
            expanded_headings = []
            for col in df.columns:
                count = heading_counter[col]
                for _ in range(count):
                    expanded_headings.append(col)
            
            self.logger.info(f"Original columns: {len(df.columns)}, Expanded columns: {len(expanded_headings)}")
            
            # Step 3: Create expanded data rows
            import csv
            values_csv_path = os.path.join(temp_dir, "values.csv")
            with open(values_csv_path, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)
                
                # Write expanded headings
                writer.writerow(expanded_headings)
                
                # Calculate first column position for each original column in expanded format
                first_col_positions = [0]
                for i, col in enumerate(df.columns):
                    count = max(heading_counter[col], 1)
                    first_col_positions.append(first_col_positions[i] + count)
                
                # Write expanded data rows
                for _, row in df.iterrows():
                    new_row = [''] * len(expanded_headings)
                    
                    for col_idx, col in enumerate(df.columns):
                        cell_value = str(row[col]) if pd.notna(row[col]) else ''
                        # Split on | and distribute across expanded columns
                        values = cell_value.split('|')
                        first_pos = first_col_positions[col_idx]
                        
                        for val_idx, val in enumerate(values):
                            # Escape double quotes
                            escaped_val = val.replace('\\','\\\\').replace('"',r'\"')
                            new_row[first_pos + val_idx] = escaped_val
                    
                    writer.writerow(new_row)
            
            self.logger.info(f"Saved expanded values.csv to: {values_csv_path} ({len(df)} rows)")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to save values.csv: {e}")
            return False
    
    def load_generated_csv(self):
        """Load generated CSV data from session storage."""
        try:
            # Load from session storage
            session_data = self.page.session.get("generated_csv_rows")
            if session_data:
                self.generated_csv_data = session_data
                self.logger.info(f"Loaded {len(self.generated_csv_data)} rows from session storage")
            else:
                self.generated_csv_data = []
        except Exception as e:
            self.logger.error(f"Failed to load generated CSV data: {e}")
            self.generated_csv_data = []
    
    def on_metadata_csv_result(self, e: ft.FilePickerResultEvent):
        """Handle metadata CSV file selection."""
        if e.files and len(e.files) > 0:
            self.metadata_csv_path = e.files[0].path
            try:
                # Load the metadata CSV
                self.metadata_df = pd.read_csv(self.metadata_csv_path, dtype=str, keep_default_na=False)
                self.logger.info(f"Loaded metadata CSV with {len(self.metadata_df)} rows and {len(self.metadata_df.columns)} columns")
                self.show_snack(f"Loaded metadata CSV: {os.path.basename(self.metadata_csv_path)}")
                
                # Update the metadata CSV text display
                if self.metadata_csv_text:
                    self.metadata_csv_text.value = f"Metadata CSV: {os.path.basename(self.metadata_csv_path)}"
                    self.logger.info(f"Updated metadata_csv_text to: {self.metadata_csv_text.value}")
                
                # Enable merge button if we have generated data
                if self.merge_button and self.generated_csv_data:
                    self.logger.info(f"Enabling merge button - have {len(self.generated_csv_data)} generated rows")
                    self.merge_button.disabled = False
                else:
                    self.logger.info(f"Not enabling merge button - merge_button exists: {self.merge_button is not None}, generated_csv_data count: {len(self.generated_csv_data) if self.generated_csv_data else 0}")
                
                self.page.update()
                    
            except Exception as ex:
                self.logger.error(f"Failed to load metadata CSV: {ex}")
                self.show_snack(f"Failed to load metadata CSV: {ex}", is_error=True)
                self.metadata_csv_path = None
                self.metadata_df = None
    
    def upload_metadata_csv(self, e):
        """Open file picker to select metadata CSV."""
        metadata_picker = ft.FilePicker(on_result=self.on_metadata_csv_result)
        self.page.overlay.append(metadata_picker)
        self.page.update()
        metadata_picker.pick_files(
            dialog_title="Select Metadata CSV File",
            allowed_extensions=["csv"],
            allow_multiple=False
        )
    
    def merge_metadata(self, e):
        """Merge metadata from uploaded CSV into generated rows."""
        self.logger.info(f"merge_metadata called - metadata_df is None: {self.metadata_df is None}, generated_csv_data count: {len(self.generated_csv_data)}")
        
        if self.metadata_df is None or not self.generated_csv_data:
            self.show_snack("Please generate CSV rows and upload metadata CSV first", is_error=True)
            return
        
        try:
            # Determine which column to use for matching
            # Try file_name_1 first (most direct), then dc:identifier, dc:title, or Title
            match_column = None
            potential_match_cols = ['file_name_1', 'dc:identifier', 'dc:title', 'Title', 'title', 'Filename', 'filename']
            
            for col in potential_match_cols:
                if col in self.metadata_df.columns:
                    match_column = col
                    self.logger.info(f"Using '{match_column}' for matching")
                    break
            
            if not match_column:
                self.logger.error(f"No suitable match column found. Metadata CSV columns: {list(self.metadata_df.columns)}")
                self.show_snack(f"Metadata CSV must contain one of: {', '.join(potential_match_cols[:3])}", is_error=True)
                return
            
            self.logger.info(f"Starting merge with match column: {match_column}")
            self.logger.info(f"Metadata CSV columns: {list(self.metadata_df.columns)}")
            
            merged_count = 0
            fields_merged = 0
            
            self.logger.info(f"Processing {len(self.generated_csv_data)} generated rows")
            
            for row in self.generated_csv_data:
                # Try to find a match value in the generated row
                # Start with file_name_1 (always present in generated rows)
                match_value = None
                if 'file_name_1' in row and row['file_name_1']:
                    match_value = row['file_name_1']
                
                if not match_value:
                    continue
                
                # Normalize the match value for flexible matching
                normalized_match = utils.normalize_for_matching(match_value)
                
                # Try exact match first
                matching_rows = self.metadata_df[self.metadata_df[match_column] == match_value]
                
                # If no exact match, try normalized matching
                if matching_rows.empty:
                    # Find rows where normalized metadata value matches normalized generated value
                    metadata_normalized = self.metadata_df[match_column].apply(utils.normalize_for_matching)
                    
                    matching_rows = self.metadata_df[
                        metadata_normalized == normalized_match
                    ]
                    if not matching_rows.empty:
                        self.logger.info(f"Matched '{match_value}' using normalized comparison")
                
                if not matching_rows.empty:
                    metadata_row = matching_rows.iloc[0]
                    
                    # Merge metadata into generated row
                    row_fields_merged = 0
                    for col in self.metadata_df.columns:
                        if col in row and pd.notna(metadata_row[col]) and metadata_row[col]:
                            # Special handling for dc:title - always overwrite from metadata
                            if col == 'dc:title':
                                row[col] = str(metadata_row[col])
                                row_fields_merged += 1
                            # Only populate other fields if the generated row value is empty
                            elif not row[col]:
                                row[col] = str(metadata_row[col])
                                row_fields_merged += 1
                    
                    # Generate unique ID for originating_system_id
                    if 'originating_system_id' in row:
                        unique_id = utils.generate_unique_id(self.page)
                        row['originating_system_id'] = unique_id
                        
                        # Convert to Handle URL for dc:identifier
                        if 'dc:identifier' in row:
                            # Extract numeric portion (e.g., "dg_1234567890" -> "1234567890")
                            numeric_part = unique_id.split('_')[-1] if '_' in unique_id else unique_id
                            row['dc:identifier'] = f"http://hdl.handle.net/11084/{numeric_part}"
                            row_fields_merged += 2  # Count both originating_system_id and dc:identifier
                    
                    if row_fields_merged > 0:
                        fields_merged += row_fields_merged
                        merged_count += 1
            
            self.logger.info(f"Merged metadata for {merged_count} rows ({fields_merged} total fields)")
            
            # Save and refresh display
            self.save_generated_csv()
            self.display_csv_data()
            
            self.show_snack(f"Merged {fields_merged} fields across {merged_count} of {len(self.generated_csv_data)} rows")
            
        except Exception as ex:
            self.logger.error(f"Failed to merge metadata: {ex}")
            self.show_snack(f"Merge failed: {ex}", is_error=True)
    
    def display_csv_data(self):
        """Display the generated CSV data in a table."""
        if not self.generated_csv_data:
            if self.csv_data_table:
                self.csv_data_table.rows = []
                self.page.update()
            return
        
        # Convert to DataFrame for easier display
        df = pd.DataFrame(self.generated_csv_data)
        
        # Get only non-empty columns for display
        non_empty_cols = [col for col in df.columns if df[col].notna().any() and (df[col] != '').any()]
        
        if not non_empty_cols:
            # Show at least the first few columns if all are empty
            non_empty_cols = df.columns[:5].tolist()
        
        # Create table
        colors = self.get_theme_colors()
        
        # Create columns for DataTable
        columns = [ft.DataColumn(ft.Text(col, size=12, weight=ft.FontWeight.BOLD)) 
                  for col in non_empty_cols]
        
        # Create rows for DataTable
        rows = []
        for idx, row in df.iterrows():
            cells = []
            for col in non_empty_cols:
                value = str(row[col]) if pd.notna(row[col]) and row[col] != '' else ''
                cells.append(ft.DataCell(ft.Text(value, size=11)))
            rows.append(ft.DataRow(cells=cells))
        
        # Update the data table
        if self.csv_data_table:
            self.csv_data_table.columns = columns
            self.csv_data_table.rows = rows
            self.page.update()
    
    def on_save_directory_result(self, e: ft.FilePickerResultEvent):
        """Handle the directory picker result for saving CSV."""
        if e.path:
            save_dir = e.path
            
            try:
                # Create CSV filename
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                csv_filename = f"generated_metadata_{timestamp}.csv"
                csv_path = os.path.join(save_dir, csv_filename)
                
                # Write to CSV
                df = pd.DataFrame(self.generated_csv_data)
                df.to_csv(csv_path, index=False, encoding='utf-8', quoting=0)
                
                self.logger.info(f"Exported CSV to: {csv_path}")
                self.show_snack(f"Exported to: {csv_filename}")
                
            except Exception as ex:
                self.logger.error(f"Failed to export CSV: {ex}")
                self.show_snack(f"Export failed: {ex}", is_error=True)
        else:
            self.logger.info("CSV export cancelled - no directory selected")
    
    def export_to_csv(self, e):
        """Export generated CSV data to a file."""
        if not self.generated_csv_data:
            self.show_snack("No CSV data to export", is_error=True)
            return
        
        # Create and show directory picker
        save_dir_picker = ft.FilePicker(on_result=self.on_save_directory_result)
        self.page.overlay.append(save_dir_picker)
        self.page.update()
        
        # Open directory picker
        save_dir_picker.get_directory_path(dialog_title="Select Directory to Save CSV")
    
    def clear_csv_data(self, e):
        """Clear the generated CSV data."""
        self.generated_csv_data = []
        self.page.session.set("generated_csv_rows", [])
        self.display_csv_data()
        
        # Update the generated rows count
        if self.generated_rows_text:
            self.generated_rows_text.value = f"Generated Rows: 0"
        
        # Disable export and clear buttons
        if self.export_button:
            self.export_button.disabled = True
        if self.clear_button:
            self.clear_button.disabled = True
        
        self.page.update()
        self.show_snack("Cleared CSV data")
        self.logger.info("Cleared generated CSV data from session storage")
    
    def render(self) -> ft.Column:
        """
        Render the CSV generator view.
        
        Returns:
            ft.Column: The CSV generator page layout
        """
        self.on_view_enter()
        
        # Load any existing generated data
        self.load_generated_csv()
        
        # Get theme-appropriate colors
        colors = self.get_theme_colors()
        
        # Get file count from session
        file_paths = self.page.session.get("selected_file_paths") or []
        file_count = len(file_paths)
        
        # Create data table
        self.csv_data_table = ft.DataTable(
            columns=[ft.DataColumn(ft.Text("No Data", size=12))],
            rows=[],
            border=ft.border.all(1, colors['border']),
            border_radius=5,
            vertical_lines=ft.BorderSide(1, colors['border']),
            horizontal_lines=ft.BorderSide(1, colors['border']),
            heading_row_color=colors['container_bg'],
            heading_row_height=40,
            data_row_min_height=35,
            data_row_max_height=35,
            column_spacing=10,
        )
        
        # Display existing data if available
        if self.generated_csv_data:
            self.display_csv_data()
        
        # Create text elements that need to be updated
        self.generated_rows_text = ft.Text(
            f"Generated Rows: {len(self.generated_csv_data)}",
            size=12,
            color=colors['secondary_text']
        )
        
        self.metadata_csv_text = ft.Text(
            f"Metadata CSV: {os.path.basename(self.metadata_csv_path) if self.metadata_csv_path else 'None'}",
            size=12,
            color=colors['secondary_text']
        )
        
        self.export_button = ft.ElevatedButton(
            text="Export to CSV File",
            icon=ft.Icons.DOWNLOAD,
            on_click=self.export_to_csv,
            style=ft.ButtonStyle(
                color=ft.Colors.WHITE,
                bgcolor=ft.Colors.GREEN
            ),
            disabled=len(self.generated_csv_data) == 0
        )
        
        self.clear_button = ft.ElevatedButton(
            text="Clear Data",
            icon=ft.Icons.CLEAR,
            on_click=self.clear_csv_data,
            style=ft.ButtonStyle(
                color=ft.Colors.WHITE,
                bgcolor=ft.Colors.ORANGE
            ),
            disabled=len(self.generated_csv_data) == 0
        )
        
        self.upload_metadata_button = ft.ElevatedButton(
            text="Upload Metadata CSV",
            icon=ft.Icons.UPLOAD_FILE,
            on_click=self.upload_metadata_csv,
            style=ft.ButtonStyle(
                color=ft.Colors.WHITE,
                bgcolor=ft.Colors.PURPLE
            )
        )
        
        self.merge_button = ft.ElevatedButton(
            text="Merge Metadata",
            icon=ft.Icons.MERGE,
            on_click=self.merge_metadata,
            style=ft.ButtonStyle(
                color=ft.Colors.WHITE,
                bgcolor=ft.Colors.DEEP_PURPLE
            ),
            disabled=True  # Will be enabled when both CSV data and metadata are available
        )
        
        # Create checkbox for manual compound object processing
        self.compound_checkbox = ft.Checkbox(
            label="Process as a Compound Object",
            value=False,
            disabled=file_count < 2,
            tooltip="When checked, all selected files will be formatted as a single compound object (requires 2+ files)"
        )
        
        return ft.Column(
            controls=[
                *self.create_page_header("CSV Generator", include_log_button=True),
                ft.Container(
                    content=ft.Column([
                        ft.Text(
                            "Generate CSV Metadata Rows",
                            size=18,
                            weight=ft.FontWeight.BOLD,
                            color=colors['primary_text']
                        ),
                        ft.Divider(height=1, color=colors['divider']),
                        ft.Text(
                            "This tool creates CSV metadata rows based on selected files using the Alma Digital CSV structure.",
                            size=14,
                            color=colors['secondary_text']
                        ),
                        ft.Container(height=10),
                        ft.Container(
                            content=ft.Column([
                                ft.Row([
                                    ft.Icon(ft.Icons.INFO_OUTLINE, size=16, color=colors['primary_text']),
                                    ft.Text(
                                        f"Selected Files: {file_count}",
                                        size=14,
                                        weight=ft.FontWeight.BOLD,
                                        color=colors['primary_text']
                                    ),
                                ], spacing=5),
                                self.generated_rows_text,
                                self.metadata_csv_text,
                            ], spacing=4),
                            bgcolor=colors['markdown_bg'],
                            border=ft.border.all(1, colors['border']),
                            border_radius=4,
                            padding=10,
                            margin=ft.margin.only(top=5, bottom=10)
                        ),
                        self.compound_checkbox,
                        ft.Row([
                            ft.ElevatedButton(
                                text="Generate CSV Rows",
                                icon=ft.Icons.LIGHTBULB_OUTLINE,
                                on_click=self.generate_csv_rows,
                                style=ft.ButtonStyle(
                                    color=ft.Colors.WHITE,
                                    bgcolor=ft.Colors.BLUE
                                ),
                                disabled=file_count == 0
                            ),
                            self.upload_metadata_button,
                            self.merge_button,
                        ], spacing=10),
                        ft.Row([
                            self.export_button,
                            self.clear_button,
                        ], spacing=10),
                        ft.Container(height=10),
                        ft.Text(
                            "Generated CSV Data (showing non-empty columns):",
                            size=14,
                            weight=ft.FontWeight.BOLD,
                            color=colors['primary_text']
                        ),
                        ft.Container(height=5),
                        ft.Container(
                            content=ft.Column([
                                self.csv_data_table
                            ], scroll=ft.ScrollMode.AUTO),
                            border=ft.border.all(1, colors['border']),
                            border_radius=5,
                            padding=5,
                            height=400,
                        ),
                    ], spacing=10),
                    bgcolor=colors['container_bg'],
                    border=ft.border.all(1, colors['border']),
                    border_radius=8,
                    padding=20,
                    margin=ft.margin.only(top=10)
                )
            ],
            spacing=0,
            horizontal_alignment=ft.CrossAxisAlignment.STRETCH,
            expand=True
        )
