"""
Derivatives View for Manage Digital Ingest Application

This module contains the DerivativesView class for creating file derivatives.
"""

import flet as ft
from views.base_view import BaseView
import os
import shutil
from thumbnail import generate_thumbnail, generate_pdf_thumbnail
# Transcript creation has been moved to: https://github.com/Digital-Grinnell/Oral-History-Workflow
# from transcript_helper import TranscriptHelper, open_transcript_workflow


class DerivativesView(BaseView):
    """
    Derivatives view class for derivative creation operations.
    """
    
    def __init__(self, page: ft.Page):
        """Initialize the derivatives view."""
        super().__init__(page)
        self.log_view = None
        self.processing = False
        self.cancel_processing = False
    
    def create_image_derivatives(self, file_path, temp_base_dir, root):
        """
        Create derivatives for TIFF/TIF image files:
        1. Convert TIFF to high-quality JPG in OBJS directory
        2. Create thumbnail using standard thumbnail generation
        
        Args:
            file_path: Path to the source TIFF file
            temp_base_dir: Base temp directory
            root: Root filename (without extension)
            
        Returns:
            tuple: (success: bool, message: str)
        """
        try:
            from PIL import Image
            
            # Get colors for UI updates
            colors = self.get_theme_colors()
            
            # Create OBJS directory if needed
            objs_dir = os.path.join(temp_base_dir, 'OBJS')
            os.makedirs(objs_dir, exist_ok=True)
            
            # Create TN directory if needed
            tn_dir = os.path.join(temp_base_dir, 'TN')
            os.makedirs(tn_dir, exist_ok=True)
            
            # 1. Convert TIFF to high-quality JPG in OBJS
            jpg_filename = f"{root}.jpg"
            jpg_path = os.path.join(objs_dir, jpg_filename)
            
            # Get file size for logging
            try:
                tiff_size_mb = os.path.getsize(file_path) / (1024 * 1024)
                msg = f"  Starting image conversion: {os.path.basename(file_path)} ({tiff_size_mb:.2f} MB)"
                self.logger.info(msg)
                if hasattr(self, 'log_view') and self.log_view:
                    self.log_view.controls.append(ft.Text(msg, size=11, color=colors['secondary_text']))
                    self.page.update()
            except:
                msg = f"  Starting image conversion: {os.path.basename(file_path)}"
                self.logger.info(msg)
                if hasattr(self, 'log_view') and self.log_view:
                    self.log_view.controls.append(ft.Text(msg, size=11, color=colors['secondary_text']))
                    self.page.update()
            
            msg = "  Converting TIFF to high-quality JPG..."
            self.logger.info(msg)
            if hasattr(self, 'log_view') and self.log_view:
                self.log_view.controls.append(ft.Text(msg, size=11, color=colors['secondary_text']))
                self.page.update()
            
            # Open and convert TIFF to JPG
            with Image.open(file_path) as img:
                # Convert to RGB if needed (TIFF might be CMYK, RGBA, etc.)
                if img.mode not in ('RGB', 'L'):
                    # Convert CMYK or other modes to RGB
                    if img.mode == 'CMYK':
                        # For CMYK images, use a more careful conversion
                        from PIL import ImageCms
                        try:
                            # Try to use ICC profile if available
                            img = ImageCms.profileToProfile(img, 
                                                           ImageCms.createProfile('sRGB'), 
                                                           ImageCms.createProfile('sRGB'),
                                                           outputMode='RGB')
                        except:
                            # Fall back to simple conversion
                            img = img.convert('RGB')
                    else:
                        img = img.convert('RGB')
                
                # Save as high-quality JPG (95% quality for archival access copy)
                img.save(jpg_path, 'JPEG', quality=95, optimize=True)
            
            # Log success with file size
            try:
                jpg_size_mb = os.path.getsize(jpg_path) / (1024 * 1024)
                msg = f"  ✓ JPG conversion complete: {jpg_filename} ({jpg_size_mb:.2f} MB)"
                self.logger.info(msg)
                if hasattr(self, 'log_view') and self.log_view:
                    self.log_view.controls.append(ft.Text(msg, size=11, color=ft.Colors.GREEN_600))
                    self.page.update()
            except:
                msg = f"  ✓ JPG conversion complete: {jpg_filename}"
                self.logger.info(msg)
                if hasattr(self, 'log_view') and self.log_view:
                    self.log_view.controls.append(ft.Text(msg, size=11, color=ft.Colors.GREEN_600))
            msg = f"  Creating thumbnail for {root}..."
            self.logger.info(msg)
            if hasattr(self, 'log_view') and self.log_view:
                self.log_view.controls.append(ft.Text(msg, size=11, color=colors['secondary_text']))
                self.page.update()
            
            # Create thumbnail with Alma naming convention
            thumbnail_filename = f"{root}.jpg.clientThumb"
            thumbnail_path = os.path.join(tn_dir, thumbnail_filename)
            
            # Use the generate_thumbnail function for consistent quality
            options = {
                'trim': False,
                'height': 200,
                'width': 200,
                'quality': 85,
                'type': 'thumbnail'
            }
            
            success = generate_thumbnail(file_path, thumbnail_path, options)
            
            if not success:
                error_msg = f"Failed to create thumbnail for TIFF: {thumbnail_path}"
                self.logger.error(error_msg)
                return False, error_msg
            
            msg = f"  ✓ Thumbnail created: {thumbnail_filename}"
            self.logger.info(msg)
            if hasattr(self, 'log_view') and self.log_view:
                self.log_view.controls.append(ft.Text(msg, size=11, color=ft.Colors.GREEN_600))
                self.page.update()
            
            return True, f"Created JPG: {jpg_filename}, Thumbnail: {thumbnail_filename}"
            
        except Exception as e:
            error_msg = f"Error creating image derivatives: {str(e)}"
            self.logger.error(error_msg)
            return False, error_msg
    
    def create_audio_derivatives(self, file_path, temp_base_dir, root):
        """
        Create derivatives for audio files (.wav or .mp3):
        1. Convert .wav to high-quality .mp3 in OBJS directory (if input is .wav)
        2. Create thumbnail from gc_media_TN.jpeg asset
        
        Note: Transcript creation has been moved to:
        https://github.com/Digital-Grinnell/Oral-History-Workflow
        
        Args:
            file_path: Path to the source audio file (.wav or .mp3)
            temp_base_dir: Base temp directory
            root: Root filename (without extension)
            
        Returns:
            tuple: (success: bool, message: str)
        """
        try:
            import subprocess
            
            # Get colors for UI updates
            colors = self.get_theme_colors()
            
            # Create OBJS directory if needed
            objs_dir = os.path.join(temp_base_dir, 'OBJS')
            os.makedirs(objs_dir, exist_ok=True)
            
            # Create TN directory if needed
            tn_dir = os.path.join(temp_base_dir, 'TN')
            os.makedirs(tn_dir, exist_ok=True)
            
            # Determine if input is WAV or MP3
            _, ext = os.path.splitext(file_path)
            is_wav = ext.lower() == '.wav'
            is_mp3 = ext.lower() == '.mp3'
            
            # 1. Convert .wav to high-quality .mp3 in OBJS (or use existing MP3)
            mp3_filename = f"{root}.mp3"
            mp3_path = os.path.join(objs_dir, mp3_filename)
            
            if is_wav:
                # Get file size for logging
                try:
                    wav_size_mb = os.path.getsize(file_path) / (1024 * 1024)
                    msg = f"  Starting audio conversion: {os.path.basename(file_path)} ({wav_size_mb:.2f} MB)"
                    self.logger.info(msg)
                    if hasattr(self, 'log_view') and self.log_view:
                        self.log_view.controls.append(ft.Text(msg, size=11, color=colors['secondary_text']))
                        self.page.update()
                except:
                    msg = f"  Starting audio conversion: {os.path.basename(file_path)}"
                    self.logger.info(msg)
                    if hasattr(self, 'log_view') and self.log_view:
                        self.log_view.controls.append(ft.Text(msg, size=11, color=colors['secondary_text']))
                        self.page.update()
                
                # Use ffmpeg for high-quality conversion
                # -q:a 0 means highest quality VBR MP3
                ffmpeg_cmd = [
                    'ffmpeg',
                    '-i', file_path,
                    '-q:a', '0',  # Highest quality VBR
                    '-map', 'a',  # Map audio stream
                    '-y',  # Overwrite output file
                    mp3_path
                ]
                
                msg = "  Converting to high-quality .mp3 (VBR) - this may take a moment for large files..."
                self.logger.info(msg)
                if hasattr(self, 'log_view') and self.log_view:
                    self.log_view.controls.append(ft.Text(msg, size=11, color=colors['secondary_text']))
                    self.page.update()
                
                result = subprocess.run(ffmpeg_cmd, capture_output=True, text=True)
                
                if result.returncode != 0:
                    error_msg = f"FFmpeg conversion failed: {result.stderr}"
                    self.logger.error(error_msg)
                    return False, error_msg
                
                # Log success with file size
                try:
                    mp3_size_mb = os.path.getsize(mp3_path) / (1024 * 1024)
                    msg = f"  ✓ MP3 conversion complete: {mp3_filename} ({mp3_size_mb:.2f} MB)"
                    self.logger.info(msg)
                    if hasattr(self, 'log_view') and self.log_view:
                        self.log_view.controls.append(ft.Text(msg, size=11, color=ft.Colors.GREEN_600))
                        self.page.update()
                except:
                    msg = f"  ✓ MP3 conversion complete: {mp3_filename}"
                    self.logger.info(msg)
                    if hasattr(self, 'log_view') and self.log_view:
                        self.log_view.controls.append(ft.Text(msg, size=11, color=ft.Colors.GREEN_600))
                        self.page.update()
            elif is_mp3:
                # MP3 file provided directly - copy to OBJS directory
                import shutil
                msg = f"  Using provided MP3 file: {os.path.basename(file_path)}"
                self.logger.info(msg)
                if hasattr(self, 'log_view') and self.log_view:
                    self.log_view.controls.append(ft.Text(msg, size=11, color=colors['secondary_text']))
                    self.page.update()
                
                # If file is already in OBJS, no need to copy
                if os.path.abspath(file_path) != os.path.abspath(mp3_path):
                    shutil.copy2(file_path, mp3_path)
                    msg = f"  ✓ MP3 file ready: {mp3_filename}"
                else:
                    msg = f"  ✓ MP3 file already in place: {mp3_filename}"
                self.logger.info(msg)
                if hasattr(self, 'log_view') and self.log_view:
                    self.log_view.controls.append(ft.Text(msg, size=11, color=ft.Colors.GREEN_600))
                    self.page.update()
            
            # 2. Use gc_media_TN.jpeg as thumbnail for all audio files (WAV/MP3)
            msg = f"  Creating audio thumbnail for {root}..."
            self.logger.info(msg)
            if hasattr(self, 'log_view') and self.log_view:
                self.log_view.controls.append(ft.Text(msg, size=11, color=colors['secondary_text']))
                self.page.update()
            
            # Use absolute path to ensure thumbnail is always found
            source_thumbnail = '/Users/mcfatem/GitHub/manage-digital-ingest-flet-Alma/assets/gc_media_TN.jpeg'
            
            # Fallback to relative path if absolute doesn't exist (for portability)
            if not os.path.exists(source_thumbnail):
                assets_dir = os.path.join(os.getcwd(), 'assets')
                source_thumbnail = os.path.join(assets_dir, 'gc_media_TN.jpeg')
            
            if not os.path.exists(source_thumbnail):
                error_msg = f"Thumbnail template not found: {source_thumbnail}"
                self.logger.error(error_msg)
                return False, error_msg
            
            # Create thumbnail with Alma naming convention
            thumbnail_filename = f"{root}.jpg.clientThumb"
            thumbnail_path = os.path.join(tn_dir, thumbnail_filename)
            
            # Resize the source thumbnail to 200x200 for Alma
            from PIL import Image
            with Image.open(source_thumbnail) as img:
                # Resize to 200x200
                img_resized = img.resize((200, 200), Image.Resampling.LANCZOS)
                # Convert to RGB if needed (in case of RGBA)
                if img_resized.mode != 'RGB':
                    img_resized = img_resized.convert('RGB')
                # Save as JPEG
                img_resized.save(thumbnail_path, 'JPEG', quality=85)
            
            msg = f"  ✓ Audio thumbnail created: {thumbnail_filename}"
            self.logger.info(msg)
            if hasattr(self, 'log_view') and self.log_view:
                self.log_view.controls.append(ft.Text(msg, size=11, color=ft.Colors.GREEN_600))
                self.page.update()
            
            # Transcript creation has been moved to: https://github.com/Digital-Grinnell/Oral-History-Workflow
            # self.offer_transcript_creation(mp3_path, root)
            
            return True, f"Created MP3: {mp3_filename}, Thumbnail: {thumbnail_filename}"
            
        except FileNotFoundError as e:
            if 'ffmpeg' in str(e):
                error_msg = "FFmpeg not found. Please install FFmpeg to process audio files."
                self.logger.error(error_msg)
                return False, error_msg
            else:
                error_msg = f"File not found: {str(e)}"
                self.logger.error(error_msg)
                return False, error_msg
        except Exception as e:
            error_msg = f"Error creating audio derivatives: {str(e)}"
            self.logger.error(error_msg)
            return False, error_msg
    
    def create_single_derivative(self, file_path, mode, derivative_type='thumbnail'):
        """
        Create a single derivative for a file based on mode and type.
        
        Args:
            file_path: Path to the source file (should be sanitized temp file)
            mode: Mode to use - always 'Alma' for this application
            derivative_type: Type of derivative ('thumbnail' or 'small')
            
        Returns:
            tuple: (success: bool, result: str)
        """
        try:
            # Parse file path components
            # Note: File paths should already be sanitized by the file selector
            dirname, basename = os.path.split(file_path)
            root, ext = os.path.splitext(basename)
            
            # Determine the base temp directory (go up one level from OBJS)
            if dirname.endswith('OBJS'):
                temp_base_dir = os.path.dirname(dirname)
            else:
                temp_base_dir = dirname
            
            self.logger.info(f"Processing file: {file_path}")
            self.logger.info(f"Directory: {dirname}, Basename: {basename}, Root: {root}, Extension: {ext}")
            self.logger.info(f"Temp base directory: {temp_base_dir}")
            
            if mode == 'Alma':
                # Alma mode - create thumbnail with .jpg.clientThumb extension in TN/ directory
                tn_dir = os.path.join(temp_base_dir, 'TN')
                os.makedirs(tn_dir, exist_ok=True)
                derivative_filename = f"{root}.jpg.clientThumb"
                derivative_path = os.path.join(tn_dir, derivative_filename)
                self.logger.info(f"Alma derivative path: {derivative_path}")
                
                # Define options for Alma thumbnails
                options = {
                    'trim': False,
                    'height': 200,
                    'width': 200,
                    'quality': 85,
                    'type': 'thumbnail'
                }
                
                # Process based on file type
                if ext.lower() in ['.tiff', '.tif']:
                    # Handle TIFF files - convert to JPG and create thumbnail
                    success, message = self.create_image_derivatives(file_path, temp_base_dir, root)
                    if success:
                        self.logger.info(f"Created image derivatives: {message}")
                        return True, message
                    else:
                        self.logger.error(f"Failed to create image derivatives: {message}")
                        return False, message
                elif ext.lower() in ['.jpg', '.jpeg', '.png', '.gif', '.bmp']:
                    success = generate_thumbnail(file_path, derivative_path, options)
                    if success:
                        self.logger.info(f"Created Alma thumbnail: {derivative_path}")
                        return True, derivative_path
                    else:
                        error_msg = f"Failed to create Alma thumbnail: {derivative_path}"
                        self.logger.error(error_msg)
                        return False, error_msg
                elif ext.lower() == '.pdf':
                    success = generate_pdf_thumbnail(file_path, derivative_path, options)
                    if success:
                        self.logger.info(f"Created Alma PDF thumbnail: {derivative_path}")
                        return True, derivative_path
                    else:
                        error_msg = f"Failed to create PDF thumbnail: {derivative_path}"
                        self.logger.error(error_msg)
                        return False, error_msg
                elif ext.lower() in ['.wav', '.mp3']:
                    # Handle audio files - convert to MP3 (if WAV) and create thumbnail
                    success, message = self.create_audio_derivatives(file_path, temp_base_dir, root)
                    if success:
                        self.logger.info(f"Created audio derivatives: {message}")
                        return True, message
                    else:
                        self.logger.error(f"Failed to create audio derivatives: {message}")
                        return False, message
                else:
                    error_msg = f"Unsupported file type for Alma: {ext}"
                    self.logger.error(error_msg)
                    return False, error_msg
            else:
                error_msg = f"Unsupported mode: {mode} (only 'Alma' supported)"
                self.logger.error(error_msg)
                return False, error_msg
                
        except Exception as e:
            error_msg = f"Exception in create_single_derivative: {str(e)}"
            self.logger.error(error_msg)
            return False, error_msg
    
    def create_derivatives_for_files(self):
        """Process all selected files and create derivatives."""
        colors = self.get_theme_colors()
        
        # Get current settings
        current_mode = self.page.session.get("selected_mode")
        selected_files = self.page.session.get("selected_file_paths") or []
        total_files = len(selected_files)
        
        if not current_mode:
            self.log_view.controls.clear()
            self.log_view.controls.append(ft.Text(
                "❌ No mode selected. Please go to Settings first.",
                size=12,
                color=colors['error']
            ))
            self.page.update()
            return
        
        if not selected_files:
            self.log_view.controls.clear()
            self.log_view.controls.append(ft.Text(
                "❌ No files selected. Please go to File Selector first.",
                size=12,
                color=colors['error']
            ))
            self.page.update()
            return
        
        # Update UI to show processing state
        self.processing = True
        self.cancel_processing = False
        
        # Update button states
        if hasattr(self, 'create_button'):
            self.create_button.disabled = True
        if hasattr(self, 'clear_button'):
            self.clear_button.disabled = True
        if hasattr(self, 'cancel_button'):
            self.cancel_button.visible = True
        
        self.page.update()
        
        # Start processing
        msg = f"Starting derivative creation for {total_files} files in {current_mode} mode"
        self.logger.info(msg)
        self.log_view.controls.clear()
        self.log_view.controls.append(ft.Text(msg, size=12, color=colors['primary_text']))
        
        self.log_view.controls.append(ft.Text(
            f"🔄 Processing {total_files} files in {current_mode} mode...",
            size=12,
            color=colors['primary_text']
        ))
        self.page.update()
        
        processed_count = 0
        success_count = 0
        error_count = 0
        
        for index, file_path in enumerate(selected_files):
            # Check for cancellation
            if self.cancel_processing:
                self.log_view.controls.append(ft.Text(
                    f"⚠️ Processing cancelled by user. Processed {processed_count}/{total_files} files.",
                    size=12,
                    color=colors['error']
                ))
                self.page.update()
                self.logger.info(f"Processing cancelled by user at file {index + 1}/{total_files}")
                break
                
            try:
                display_name = os.path.basename(file_path)
                self.logger.info(f"Processing file {index + 1}/{total_files}: {file_path}")
                
                # Update log
                self.log_view.controls.append(ft.Text(
                    f"🔄 Processing file {index + 1}/{total_files}: {display_name}",
                    size=12,
                    color=colors['primary_text']
                ))
                self.page.update()
                
                # Create derivatives based on mode
                if current_mode == "CollectionBuilder":
                    # Create thumbnail
                    thumbnail_success, thumbnail_result = self.create_single_derivative(
                        file_path, current_mode, 'thumbnail'
                    )
                    
                    # Create small derivative
                    small_success, small_result = self.create_single_derivative(
                        file_path, current_mode, 'small'
                    )
                    
                    # Log results
                    if thumbnail_success and small_success:
                        result_text = f"✅ {display_name} - Created thumbnail and small derivatives"
                        success_count += 1
                        self.logger.info(f"Successfully created derivatives for {file_path}")
                    else:
                        result_text = f"❌ {display_name} - Failed to create derivatives"
                        if not thumbnail_success:
                            self.logger.error(f"Thumbnail failed: {thumbnail_result}")
                        if not small_success:
                            self.logger.error(f"Small derivative failed: {small_result}")
                        error_count += 1
                        
                elif current_mode == "Alma":
                    # Create derivatives for Alma
                    # For audio files (WAV/MP3), this creates both MP3 and thumbnail
                    # For images, this creates just the thumbnail
                    _, ext = os.path.splitext(file_path)
                    is_audio = ext.lower() in ['.wav', '.mp3']
                    
                    thumbnail_success, thumbnail_result = self.create_single_derivative(
                        file_path, current_mode, 'thumbnail'
                    )
                    
                    if thumbnail_success:
                        if is_audio:
                            # Audio files create 2 derivatives: MP3 + thumbnail
                            result_text = f"✅ {display_name} - Created MP3 and thumbnail derivatives"
                            success_count += 2  # Count both MP3 and thumbnail
                        else:
                            # Image/PDF files create 1 derivative: thumbnail only
                            result_text = f"✅ {display_name} - Created thumbnail derivative"
                            success_count += 1
                        self.logger.info(f"Successfully created derivatives for {file_path}")
                    else:
                        if is_audio:
                            # Failed to create audio derivatives (MP3 + thumbnail)
                            result_text = f"❌ {display_name} - Failed to create derivatives"
                            error_count += 2  # Count both MP3 and thumbnail as failed
                        else:
                            # Failed to create thumbnail
                            result_text = f"❌ {display_name} - Failed to create thumbnail"
                            error_count += 1
                        self.logger.error(f"Derivative creation failed: {thumbnail_result}")
                else:
                    result_text = f"❌ {display_name} - Unsupported mode: {current_mode}"
                    error_count += 1
                    self.logger.error(f"Unsupported mode {current_mode} for file {file_path}")
                
                # Add result to UI
                self.log_view.controls.append(
                    ft.Text(result_text, size=12, color=colors['primary_text'])
                )
                self.page.update()
                processed_count += 1
                
            except Exception as e:
                error_count += 1
                error_text = f"❌ {display_name} - Error: {str(e)}"
                self.log_view.controls.append(
                    ft.Text(error_text, size=12, color=colors['error'])
                )
                self.logger.error(f"Exception processing {file_path}: {str(e)}")
                self.page.update()
            
            # Update progress
            self.log_view.controls.append(
                ft.Text(
                    f"Progress: {index + 1}/{total_files} files ({(index + 1)/total_files:.0%})",
                    size=12,
                    color=colors['primary_text']
                )
            )
            self.page.update()
        
        # Final summary
        total_derivatives = success_count + error_count
        if not self.cancel_processing:
            summary_text = f"\n✅ Processing complete!\nFiles: {total_files} | Derivatives Created: {success_count}/{total_derivatives} | Failed: {error_count}"
        else:
            summary_text = f"\n⚠️ Processing cancelled!\nFiles Processed: {processed_count}/{total_files} | Derivatives Created: {success_count}/{total_derivatives} | Failed: {error_count}"
        
        self.log_view.controls.append(
            ft.Text(summary_text, size=14, weight=ft.FontWeight.BOLD, color=colors['primary_text'])
        )
        self.page.update()
        self.logger.info(summary_text)
        
        # Reset processing state
        self.processing = False
        self.cancel_processing = False
        
        # Update button states back to normal
        if hasattr(self, 'create_button'):
            self.create_button.disabled = False
        if hasattr(self, 'clear_button'):
            self.clear_button.disabled = False
        if hasattr(self, 'cancel_button'):
            self.cancel_button.visible = False
        
        self.page.update()
        
        self.logger.info("Processing completed, buttons reset")
    
    # Transcript creation has been moved to: https://github.com/Digital-Grinnell/Oral-History-Workflow
    # The following methods (offer_transcript_creation and show_transcript_instructions) are no longer used
    # and have been commented out. For transcript creation, please refer to the Oral-History-Workflow repository.
    
    # def offer_transcript_creation(self, mp3_path: str, root: str):
    #     """
    #     Offer the user the option to create a transcript from the MP3 file.
    #     
    #     Args:
    #         mp3_path: Path to the MP3 file
    #         root: Root filename (without extension)
    #     """
    #     ... (method commented out - see Oral-History-Workflow repository)
    
    # def show_transcript_instructions(self, mp3_path: str):
    #     """
    #     Display transcript creation instructions in a dialog.
    #     
    #     Args:
    #         mp3_path: Path to the MP3 file
    #     """
    #     ... (method commented out - see Oral-History-Workflow repository)
    
    def interrupt_processing(self, e):
        """Interrupt the current processing operation."""
        if self.processing:
            self.cancel_processing = True
            self.logger.info("Processing interruption requested by user")
            
            # Update UI to show cancellation in progress
            colors = self.get_theme_colors()
            self.log_view.controls.append(ft.Text(
                "🛑 Cancellation requested... stopping after current file.",
                size=12,
                color=colors['error']
            ))
            self.page.update()
    
    def render(self) -> ft.Column:
        """
        Render the derivatives view content.
        
        Returns:
            ft.Column: The derivatives page layout
        """
        self.on_view_enter()
        
        # Get theme-appropriate colors
        colors = self.get_theme_colors()
        
        # Get current mode and files from session
        current_mode = self.page.session.get("selected_mode")
        selected_files = self.page.session.get("selected_file_paths") or []
        total_files = len(selected_files)
        
        # Prepare status information controls
        status_info_controls = [
            ft.Text(f"Current Mode: {current_mode or 'None selected'}", 
                   size=16, weight=ft.FontWeight.BOLD, color=colors['container_text']),
            ft.Text(f"Selected Files: {total_files}", 
                   size=16, weight=ft.FontWeight.BOLD, color=colors['container_text'])
        ]
        
        status_info_controls.extend([
            ft.Container(height=5),
            ft.Text("Derivative Types:", size=14, weight=ft.FontWeight.BOLD, color=colors['container_text']),
            ft.Text("• Images/PDFs: .clientThumb (200x200, preserves extension)", 
                   size=12, color=colors['container_text']),
            ft.Text("• Images/PDFs: _TN.jpg (200x200) thumbnail", 
                   size=12, color=colors['container_text']),
            ft.Text("• Audio (.wav): .mp3 conversion + audio thumbnail", 
                   size=12, color=colors['container_text'])
        ])
        
        # Create log view
        self.log_view = ft.ListView(
            spacing=2,
            padding=5,
            height=300,
            expand=True,
            auto_scroll=True
        )
        
        # Add initial message
        if not current_mode:
            self.log_view.controls.append(
                ft.Text("⚠️ Please select a mode in Settings before creating derivatives.",
                       size=12, color=colors['secondary_text'])
            )
        elif total_files == 0:
            self.log_view.controls.append(
                ft.Text("⚠️ Please select files in File Selector before creating derivatives.",
                       size=12, color=colors['secondary_text'])
            )
        else:
            self.log_view.controls.append(
                ft.Text(f"Ready to create derivatives for {total_files} files in {current_mode} mode.",
                       size=12, color=colors['primary_text'])
            )
        
        def on_create_derivatives_click(e):
            """Handle the create derivatives button click."""
            self.create_derivatives_for_files()
        
        def on_interrupt_click(e):
            """Handle the interrupt/cancel button click."""
            self.interrupt_processing(e)
        
        def on_clear_results_click(e):
            """Clear the results log."""
            self.log_view.controls.clear()
            self.log_view.controls.append(
                ft.Text("Log cleared. Ready to process files.",
                       size=12, color=colors['secondary_text'])
            )
            self.page.update()
            self.logger.info("Cleared derivatives log")
        
        # Create buttons with references that can be updated
        create_button = ft.ElevatedButton(
            "Create Derivatives",
            icon=ft.Icons.AUTO_FIX_HIGH,
            on_click=on_create_derivatives_click,
            disabled=(not current_mode or total_files == 0)
        )
        
        clear_button = ft.ElevatedButton(
            "Clear Results",
            icon=ft.Icons.CLEAR,
            on_click=on_clear_results_click
        )
        
        # Store button references for dynamic updates
        self.create_button = create_button
        self.clear_button = clear_button
        
        start_button = ft.Row([
            create_button,
            clear_button
        ], alignment=ft.MainAxisAlignment.CENTER, spacing=10)
        
        # Create cancel button (always present, visibility controlled dynamically)
        self.cancel_button = ft.Container(
            content=ft.Column([
                ft.Container(height=10),
                ft.Row([
                    ft.ElevatedButton(
                        "🛑 Cancel Processing",
                        icon=ft.Icons.CANCEL,
                        on_click=on_interrupt_click,
                        bgcolor=ft.Colors.RED_600,
                        color=ft.Colors.WHITE
                    )
                ], alignment=ft.MainAxisAlignment.CENTER)
            ], spacing=0),
            visible=self.processing  # Initially hidden unless already processing
        )
        
        # Build the layout controls list
        layout_controls = [
            *self.create_page_header("Derivatives Creation"),
            
            # Status information
            ft.Container(
                content=ft.Column(status_info_controls, spacing=2),
                padding=ft.padding.all(10),
                border=ft.border.all(1, colors['border']),
                border_radius=10,
                bgcolor=colors['container_bg'],
                margin=ft.margin.symmetric(vertical=5)
            ),
            
            # Start button at top
            start_button,
            
            ft.Container(height=5),
            
            # Log view
            ft.Text("Processing Log:", size=16, weight=ft.FontWeight.BOLD, color=colors['primary_text']),
            ft.Container(height=5),
            ft.Container(
                content=self.log_view,
                border=ft.border.all(1, colors['border']),
                border_radius=5,
                padding=2,
                expand=True
            ),
            
            # Cancel button below log (only visible during processing)
            self.cancel_button
        ]
        
        # Create the UI layout
        return ft.Column(layout_controls, alignment="start", expand=True, spacing=0, scroll=ft.ScrollMode.AUTO)
