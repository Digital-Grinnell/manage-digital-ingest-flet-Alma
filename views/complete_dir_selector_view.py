"""
Complete Directory Selector View for Manage Digital Ingest Application

This module allows loading a previously saved complete directory structure
from a prior session, bypassing file selection and CSV generation steps.
"""

import flet as ft
from views.base_view import BaseView
import os
import json
import pandas as pd


class CompleteDirSelectorView(BaseView):
    """
    Complete directory selector view for loading previously saved work.
    Allows direct navigation to final ingest steps by loading complete directory structure.
    """
    
    def __init__(self, page: ft.Page):
        """Initialize the complete directory selector view."""
        super().__init__(page)
        self.selector_type = "Complete Directory"
        self.selected_directory = None
        self.dir_picker = None
        self.status_text = None
        self.load_button = None
        self.clear_button = None
        self.directory_info_container = None
    
    def on_view_enter(self):
        """Called when the view is entered."""
        super().on_view_enter()
        self.logger.info("Entered Complete Directory Selector View")
    
    def on_directory_selected(self, e: ft.FilePickerResultEvent):
        """Handle directory selection."""
        if e.path:
            self.selected_directory = e.path
            self.logger.info(f"Selected directory: {self.selected_directory}")
            
            # Validate the directory structure
            is_valid, message, info = self.validate_directory_structure(self.selected_directory)
            
            if is_valid:
                self.update_directory_info(info)
                if self.load_button:
                    self.load_button.disabled = False
                self.show_snack(f"Valid directory selected: {os.path.basename(self.selected_directory)}")
            else:
                self.selected_directory = None
                if self.load_button:
                    self.load_button.disabled = True
                self.clear_directory_info()
                self.show_snack(f"Invalid directory: {message}", is_error=True)
            
            self.page.update()
    
    def validate_directory_structure(self, directory):
        """
        Validate that the directory has the expected structure.
        
        Returns:
            tuple: (is_valid: bool, message: str, info: dict)
        """
        try:
            # Check for required subdirectories
            objs_dir = os.path.join(directory, "OBJS")
            tn_dir = os.path.join(directory, "TN")
            small_dir = os.path.join(directory, "SMALL")
            
            if not os.path.exists(objs_dir):
                return False, "Missing OBJS directory", {}
            
            # Scan for files
            objs_files = [f for f in os.listdir(objs_dir) if os.path.isfile(os.path.join(objs_dir, f))]
            tn_files = [f for f in os.listdir(tn_dir) if os.path.isfile(os.path.join(tn_dir, f))] if os.path.exists(tn_dir) else []
            small_files = [f for f in os.listdir(small_dir) if os.path.isfile(os.path.join(small_dir, f))] if os.path.exists(small_dir) else []
            
            # Look for CSV files
            csv_files = [f for f in os.listdir(directory) if f.endswith('.csv')]
            generated_csv = [f for f in csv_files if f.startswith('generated_metadata_')]
            values_csv = 'values.csv' in csv_files
            
            if not objs_files:
                return False, "OBJS directory is empty", {}
            
            info = {
                'objs_count': len(objs_files),
                'tn_count': len(tn_files),
                'small_count': len(small_files),
                'has_generated_csv': len(generated_csv) > 0,
                'generated_csv_name': generated_csv[0] if generated_csv else None,
                'has_values_csv': values_csv,
                'directory_name': os.path.basename(directory)
            }
            
            return True, "Valid directory structure", info
            
        except Exception as ex:
            self.logger.error(f"Error validating directory: {ex}")
            return False, f"Error: {str(ex)}", {}
    
    def update_directory_info(self, info):
        """Update the directory information display."""
        if self.directory_info_container:
            colors = self.get_theme_colors()
            self.directory_info_container.content = ft.Column([
                ft.Text(f"📁 {info['directory_name']}", size=16, weight=ft.FontWeight.BOLD, color=colors['primary_text']),
                ft.Container(height=10),
                ft.Row([
                    ft.Icon(ft.Icons.FOLDER, size=16, color=ft.Colors.BLUE),
                    ft.Text(f"OBJS: {info['objs_count']} files", size=14, color=colors['secondary_text'])
                ]),
                ft.Row([
                    ft.Icon(ft.Icons.IMAGE, size=16, color=ft.Colors.GREEN),
                    ft.Text(f"TN: {info['tn_count']} files", size=14, color=colors['secondary_text'])
                ]),
                ft.Row([
                    ft.Icon(ft.Icons.PHOTO_SIZE_SELECT_LARGE, size=16, color=ft.Colors.ORANGE),
                    ft.Text(f"SMALL: {info['small_count']} files", size=14, color=colors['secondary_text'])
                ]),
                ft.Container(height=10),
                ft.Row([
                    ft.Icon(ft.Icons.TABLE_CHART if info['has_generated_csv'] else ft.Icons.CANCEL, 
                           size=16, 
                           color=ft.Colors.GREEN if info['has_generated_csv'] else ft.Colors.RED),
                    ft.Text(f"Generated CSV: {info['generated_csv_name'] if info['has_generated_csv'] else 'Not found'}", 
                           size=14, color=colors['secondary_text'])
                ]),
                ft.Row([
                    ft.Icon(ft.Icons.TABLE_ROWS if info['has_values_csv'] else ft.Icons.CANCEL, 
                           size=16, 
                           color=ft.Colors.GREEN if info['has_values_csv'] else ft.Colors.RED),
                    ft.Text(f"Values CSV: {'Found' if info['has_values_csv'] else 'Not found'}", 
                           size=14, color=colors['secondary_text'])
                ])
            ], spacing=5)
            self.directory_info_container.bgcolor = ft.Colors.GREEN_50
            self.directory_info_container.border = ft.border.all(1, ft.Colors.GREEN_200)
            self.page.update()
    
    def clear_directory_info(self):
        """Clear the directory information display."""
        if self.directory_info_container:
            colors = self.get_theme_colors()
            self.directory_info_container.content = ft.Text(
                "No directory selected", 
                size=14, 
                color=colors['secondary_text']
            )
            self.directory_info_container.bgcolor = ft.Colors.ORANGE_50
            self.directory_info_container.border = ft.border.all(1, ft.Colors.ORANGE_200)
            self.page.update()
    
    def load_directory(self, e):
        """Load the selected directory into session."""
        if not self.selected_directory:
            self.show_snack("No directory selected", is_error=True)
            return
        
        try:
            # Validate again before loading
            is_valid, message, info = self.validate_directory_structure(self.selected_directory)
            if not is_valid:
                self.show_snack(f"Directory validation failed: {message}", is_error=True)
                return
            
            # Set up directory paths in session
            objs_dir = os.path.join(self.selected_directory, "OBJS")
            tn_dir = os.path.join(self.selected_directory, "TN")
            small_dir = os.path.join(self.selected_directory, "SMALL")
            
            self.page.session.set("temp_directory", self.selected_directory)
            # Update tracker for shutdown cleanup
            tracker = self.page.session.get("_update_temp_dir_tracker")
            if tracker:
                tracker(self.selected_directory)
            
            self.page.session.set("temp_objs_directory", objs_dir)
            self.page.session.set("temp_tn_directory", tn_dir)
            self.page.session.set("temp_small_directory", small_dir)
            
            # Load file lists
            objs_files = [os.path.join(objs_dir, f) for f in os.listdir(objs_dir) 
                         if os.path.isfile(os.path.join(objs_dir, f))]
            
            self.page.session.set("temp_files", objs_files)
            self.page.session.set("selected_file_paths", objs_files)
            
            # Create temp_file_info from the files
            temp_file_info = []
            for file_path in objs_files:
                filename = os.path.basename(file_path)
                temp_file_info.append({
                    'original_path': file_path,
                    'original_filename': filename,
                    'temp_path': file_path,
                    'sanitized_filename': filename
                })
            self.page.session.set("temp_file_info", temp_file_info)
            
            # Load generated CSV if it exists
            if info['has_generated_csv']:
                csv_path = os.path.join(self.selected_directory, info['generated_csv_name'])
                try:
                    df = pd.read_csv(csv_path, dtype=str, keep_default_na=False)
                    csv_data = df.to_dict('records')
                    self.page.session.set("generated_csv_rows", csv_data)
                    self.page.session.set("generated_csv_filename", info['generated_csv_name'])
                    self.logger.info(f"Loaded generated CSV: {len(csv_data)} rows")
                except Exception as csv_ex:
                    self.logger.warning(f"Could not load generated CSV: {csv_ex}")
            
            self.logger.info(f"Successfully loaded complete directory with {len(objs_files)} files")
            self.show_snack(f"Loaded {len(objs_files)} files from {info['directory_name']}")
            
            # Show success message
            if self.status_text:
                self.status_text.value = f"✅ Loaded {len(objs_files)} files. Ready to proceed to Instructions view for final Alma import."
                self.status_text.color = ft.Colors.GREEN_700
                self.page.update()
            
        except Exception as ex:
            self.logger.error(f"Error loading directory: {ex}")
            self.show_snack(f"Error loading directory: {str(ex)}", is_error=True)
    
    def clear_selection(self):
        """Clear the selected directory."""
        self.selected_directory = None
        self.page.session.set("temp_directory", None)
        # Update tracker for shutdown cleanup
        tracker = self.page.session.get("_update_temp_dir_tracker")
        if tracker:
            tracker(None)
        self.page.session.set("temp_files", [])
        self.page.session.set("selected_file_paths", [])
        self.page.session.set("temp_file_info", [])
        self.page.session.set("generated_csv_rows", [])
        
        if self.load_button:
            self.load_button.disabled = True
        if self.status_text:
            self.status_text.value = ""
        
        self.clear_directory_info()
        self.show_snack("Cleared directory selection")
        self.logger.info("Cleared directory selection")
        self.page.update()
    
    def render(self) -> ft.Column:
        """
        Render the complete directory selector view.
        
        Returns:
            ft.Column: The view layout
        """
        self.on_view_enter()
        
        # Get theme-appropriate colors
        colors = self.get_theme_colors()
        
        # Get default backup directory from settings
        default_dir = None
        try:
            persistent_path = os.path.join("_data", "persistent.json")
            if os.path.exists(persistent_path):
                with open(persistent_path, 'r', encoding='utf-8') as f:
                    settings = json.load(f)
                    default_dir = settings.get("temp_backup_directory", None)
        except Exception:
            pass
        
        # Create directory picker
        self.dir_picker = ft.FilePicker(on_result=self.on_directory_selected)
        self.page.overlay.append(self.dir_picker)
        self.page.update()
        
        # Status text
        self.status_text = ft.Text("", size=14, color=colors['primary_text'])
        
        # Directory info container
        self.directory_info_container = ft.Container(
            content=ft.Text("No directory selected", size=14, color=colors['secondary_text']),
            padding=ft.padding.all(15),
            border=ft.border.all(1, ft.Colors.ORANGE_200),
            border_radius=5,
            bgcolor=ft.Colors.ORANGE_50
        )
        
        # Buttons
        def open_directory_picker(e):
            self.dir_picker.get_directory_path(
                dialog_title="Select Complete Directory",
                initial_directory=default_dir if default_dir and os.path.exists(default_dir) else None
            )
        
        select_button = ft.ElevatedButton(
            "Select Directory",
            icon=ft.Icons.FOLDER_OPEN,
            on_click=open_directory_picker,
            bgcolor=ft.Colors.BLUE_700,
            color=ft.Colors.WHITE
        )
        
        self.load_button = ft.ElevatedButton(
            "Load Directory",
            icon=ft.Icons.UPLOAD,
            on_click=self.load_directory,
            disabled=True,
            bgcolor=ft.Colors.GREEN_700,
            color=ft.Colors.WHITE
        )
        
        self.clear_button = ft.ElevatedButton(
            "Clear Selection",
            icon=ft.Icons.CLEAR,
            on_click=lambda e: self.clear_selection(),
            bgcolor=ft.Colors.ORANGE_600,
            color=ft.Colors.WHITE
        )
        
        return ft.Column([
            ft.Row([
                ft.Text(f"File Selector - {self.selector_type}", size=24, weight=ft.FontWeight.BOLD),
                self.create_log_button("Show Logs", ft.Icons.LIST_ALT)
            ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
            ft.Divider(height=15, color=colors['divider']),
            ft.Text(
                "Load a Previously Saved Complete Directory",
                size=18,
                weight=ft.FontWeight.BOLD,
                color=colors['primary_text']
            ),
            ft.Container(height=10),
            ft.Text(
                "Select a directory that contains OBJS, TN, and SMALL subdirectories from a previous session.",
                size=14,
                color=colors['secondary_text']
            ),
            ft.Text(
                "This allows you to bypass file selection, derivatives creation, and CSV generation.",
                size=14,
                color=colors['secondary_text'],
                italic=True
            ),
            ft.Text(
                "Use this to resume from a saved backup and proceed directly to the final Alma import step.",
                size=14,
                color=colors['secondary_text'],
                italic=True
            ),
            ft.Container(height=15),
            ft.Text(
                f"Default location: {default_dir if default_dir else 'Not set (configure in Settings)'}",
                size=12,
                color=colors['secondary_text'],
                italic=True
            ),
            ft.Container(height=20),
            ft.Row([
                select_button,
                self.load_button,
                self.clear_button
            ], alignment=ft.MainAxisAlignment.CENTER, spacing=15),
            ft.Container(height=20),
            self.directory_info_container,
            ft.Container(height=15),
            self.status_text
        ], alignment="start", expand=True, scroll=ft.ScrollMode.AUTO, spacing=0)
