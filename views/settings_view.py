"""
Settings View for Manage Digital Ingest Application - Alma Edition

This module contains the SettingsView class for displaying and managing
application settings and configurations.
"""

import flet as ft
from views.base_view import BaseView
import json
import os


class SettingsView(BaseView):
    """
    Settings view class for configuration management.
    Alma Edition - Mode is fixed to 'Alma'.
    """
    
    # Application mode constant - fixed for Alma Edition
    APP_MODE = "Alma"
    
    def load_persistent_settings(self):
        """Load settings from persistent.json"""
        try:
            persistent_path = os.path.join("_data", "persistent.json")
            if os.path.exists(persistent_path):
                with open(persistent_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    return data
        except Exception as e:
            self.logger.warning(f"Failed to load persistent settings: {e}")
        return {}
    
    def save_persistent_settings(self, settings):
        """Save settings to persistent.json"""
        try:
            persistent_path = os.path.join("_data", "persistent.json")
            # Ensure the _data directory exists
            os.makedirs("_data", exist_ok=True)
            
            # Load existing data to preserve other settings
            existing_data = {}
            if os.path.exists(persistent_path):
                try:
                    with open(persistent_path, 'r', encoding='utf-8') as f:
                        existing_data = json.load(f)
                except Exception:
                    self.logger.warning("Failed to read existing persistent data")
            
            # Update with new settings
            existing_data.update(settings)
            
            # Write back to file
            with open(persistent_path, 'w', encoding='utf-8') as f:
                json.dump(existing_data, f, indent=2)
            
            self.logger.info(f"Saved persistent settings: {settings}")
        except Exception as e:
            self.logger.error(f"Failed to save persistent settings: {e}")
    
    def clear_session(self, e):
        """
        Clear all session data and delete the persistent session file.
        Resets the application to pristine initial state.
        """
        try:
            # Import here to avoid circular dependency
            from views.about_view import AboutView
            
            # Get all session keys before clearing
            session_keys = list(self.page.session.get_keys())
            key_count = len(session_keys)
            
            # Clear all session variables
            for key in session_keys:
                self.page.session.remove(key)
            
            # Delete the persistent session file if it exists
            persistent_session_file = AboutView.PERSISTENT_SESSION_FILE
            if os.path.exists(persistent_session_file):
                os.remove(persistent_session_file)
                self.logger.info(f"Deleted persistent session file: {persistent_session_file}")
            
            self.logger.info(f"Cleared {key_count} session keys - session reset to pristine state")
            
            self.page.snack_bar = ft.SnackBar(
                content=ft.Text(f"Session cleared! {key_count} keys removed. Application reset to initial state."),
                bgcolor=ft.Colors.ORANGE_700
            )
            self.page.snack_bar.open = True
            self.page.update()
            
            # Refresh the settings view to show cleared state
            self.page.go("/settings")
            
        except Exception as e:
            self.logger.error(f"Error clearing session: {e}")
            self.page.snack_bar = ft.SnackBar(
                content=ft.Text(f"Error: {str(e)}"),
                bgcolor=ft.Colors.RED_600
            )
            self.page.snack_bar.open = True
            self.page.update()
    
    def render(self) -> ft.Column:
        """
        Render the settings view content.
        
        Returns:
            ft.Column: The settings page layout
        """
        self.on_view_enter()
        
        # Get theme-appropriate colors
        colors = self.get_theme_colors()
        
        # File selector options for Alma (CSV is primary method)
        file_selector_options = ["CSV", "FilePicker"]
        
        # Log available options
        self.logger.info(f"Available file selector options: {file_selector_options}")
        
        # Load persistent settings
        persistent_settings = self.load_persistent_settings()
        
        # Auto-set mode to Alma for this app (using class constant)
        current_mode = self.APP_MODE
        self.page.session.set("selected_mode", current_mode)
        self.save_persistent_settings({"selected_mode": current_mode})
        
        # Get current selections from session or fall back to persistent settings
        current_file_option = self.page.session.get("selected_file_option") or persistent_settings.get("selected_file_option")
        # Store in session if loaded from persistent
        if current_file_option:
            self.page.session.set("selected_file_option", current_file_option)
        
        # Log current session selections if they exist
        self.logger.info(f"Current mode selection: {current_mode} (auto-set for Alma app)")
        if current_file_option:
            self.logger.info(f"Current file option selection: {current_file_option}")
        
        # Dropdown change handlers
        def on_file_option_change(e):
            self.page.session.set("selected_file_option", e.control.value)
            self.save_persistent_settings({"selected_file_option": e.control.value})
            self.logger.info(f"File option selected: {e.control.value}")
            self.log_all_current_selections()
        
        # Temp directory preservation handlers
        def on_preserve_temp_change(e):
            """Handle temp directory preservation toggle"""
            preserve_value = e.control.value
            self.save_persistent_settings({"preserve_temp_directory": preserve_value})
            self.page.session.set("preserve_temp_directory", preserve_value)
            self.logger.info(f"Preserve temp directory: {preserve_value}")
            # Update UI to show/hide directory picker
            temp_dir_picker_container.visible = preserve_value
            self.page.update()
        
        def on_temp_backup_dir_result(e: ft.FilePickerResultEvent):
            """Handle directory picker result for temp backup location"""
            if e.path:
                backup_path = e.path
                self.save_persistent_settings({"temp_backup_directory": backup_path})
                self.page.session.set("temp_backup_directory", backup_path)
                self.logger.info(f"Temp backup directory set to: {backup_path}")
                temp_backup_dir_text.value = f"Backup Location: {backup_path}"
                self.page.update()
        
        # Create directory picker for temp backup location
        temp_backup_dir_picker = ft.FilePicker(on_result=on_temp_backup_dir_result)
        self.page.overlay.append(temp_backup_dir_picker)
        
        def pick_temp_backup_directory(e):
            """Open directory picker for temp backup location"""
            temp_backup_dir_picker.get_directory_path(dialog_title="Select Temp Backup Directory")
        
        # Get current settings
        current_preserve_temp = persistent_settings.get("preserve_temp_directory", False)
        current_backup_dir = persistent_settings.get("temp_backup_directory", "")
        
        # Store in session if loaded from persistent
        self.page.session.set("preserve_temp_directory", current_preserve_temp)
        if current_backup_dir:
            self.page.session.set("temp_backup_directory", current_backup_dir)
        
        # Theme selector handler
        def on_theme_change(e):
            """Handle theme mode changes"""
            theme_value = e.control.value
            if theme_value == "Light":
                self.page.theme_mode = ft.ThemeMode.LIGHT
            elif theme_value == "Dark":
                self.page.theme_mode = ft.ThemeMode.DARK
            
            self.page.update()
            self.save_persistent_settings({"selected_theme": theme_value})
            self.logger.info(f"Theme changed to: {theme_value}")
            self.page.session.set("selected_theme", theme_value)
        
        # Get current theme for selector - check persistent settings first
        current_theme = persistent_settings.get("selected_theme", "Light")
        # Override with current page theme if different
        if self.page.theme_mode == ft.ThemeMode.DARK:
            current_theme = "Dark"
        elif self.page.theme_mode == ft.ThemeMode.LIGHT:
            current_theme = "Light"
        
        # Theme selector container
        theme_settings_container = ft.Container(
            content=ft.Row([
                ft.Icon(
                    name=ft.Icons.PALETTE_OUTLINED,
                    size=20,
                    color=colors['container_text']
                ),
                ft.Text("Theme:", size=16, weight=ft.FontWeight.BOLD, color=colors['container_text']),
                ft.Dropdown(
                    label="Select Theme",
                    value=current_theme,
                    options=[
                        ft.dropdown.Option("Light"),
                        ft.dropdown.Option("Dark")
                    ],
                    on_change=on_theme_change,
                    width=150
                )
            ], alignment=ft.MainAxisAlignment.CENTER, spacing=8),
            padding=ft.padding.all(8),
            border=ft.border.all(1, colors['border']),
            border_radius=10,
            margin=ft.margin.symmetric(vertical=4),
            bgcolor=colors['container_bg']
        )
        
        # For Alma app: Display mode as read-only text instead of dropdown
        mode_settings_container = ft.Container(
            content=ft.Column([
                ft.Text(f"Processing Mode: {self.APP_MODE}", size=16, weight=ft.FontWeight.BOLD, color=colors['primary_text']),
                ft.Text(f"This app is configured for {self.APP_MODE} workflows only", size=12, italic=True, color=colors['secondary_text'])
            ]),
            padding=ft.padding.all(8),
            border=ft.border.all(1, colors['border']),
            border_radius=10,
            margin=ft.margin.symmetric(vertical=4),
            bgcolor=colors['container_bg']
        )
        
        file_selector_settings_container = ft.Container(
            content=ft.Column([
                # ft.Text("File Selector Options", size=18, weight=ft.FontWeight.BOLD, color=colors['container_text']),
                ft.Dropdown(
                    label="Choose a File Selection Option",
                    value=current_file_option if current_file_option else "",
                    options=[ft.dropdown.Option(option) for option in file_selector_options],
                    on_change=on_file_option_change,
                    width=300
                )
            ]),
            padding=ft.padding.all(8),
            border=ft.border.all(1, colors['border']),
            border_radius=10,
            margin=ft.margin.symmetric(vertical=4),
            bgcolor=colors['container_bg']
        )
        
        # Temp directory preservation UI
        temp_backup_dir_text = ft.Text(
            f"Backup Location: {current_backup_dir}" if current_backup_dir else "No backup location selected",
            size=12,
            color=colors['secondary_text']
        )
        
        temp_dir_picker_container = ft.Container(
            content=ft.Column([
                temp_backup_dir_text,
                ft.ElevatedButton(
                    "Select Backup Location",
                    icon=ft.Icons.FOLDER_OPEN,
                    on_click=pick_temp_backup_directory,
                    bgcolor=ft.Colors.BLUE_700,
                    color=ft.Colors.WHITE
                ),
            ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=8),
            visible=current_preserve_temp
        )
        
        temp_preservation_container = ft.Container(
            content=ft.Column([
                ft.Text("Temporary Directory Preservation", size=16, weight=ft.FontWeight.BOLD, color=colors['primary_text']),
                ft.Text(
                    "When enabled, copies of temporary processing directories will be saved before cleanup",
                    size=12, italic=True, color=colors['secondary_text']
                ),
                ft.Container(height=5),
                ft.Checkbox(
                    label="Preserve temporary directories on shutdown",
                    value=current_preserve_temp,
                    on_change=on_preserve_temp_change
                ),
                temp_dir_picker_container
            ], horizontal_alignment=ft.CrossAxisAlignment.CENTER),
            padding=ft.padding.all(10),
            border=ft.border.all(1, colors['border']),
            border_radius=10,
            margin=ft.margin.symmetric(vertical=4),
            bgcolor=colors['container_bg']
        )
        
        return ft.Column([
            *self.create_page_header("Settings Page", include_log_button=False),
            mode_settings_container,
            file_selector_settings_container,
            ft.Divider(height=15, color=colors['divider']),
            theme_settings_container,
            ft.Divider(height=15, color=colors['divider']),
            temp_preservation_container,
            ft.Divider(height=15, color=colors['divider']),
            ft.Container(
                content=ft.Column([
                    ft.Text("Session Management", size=16, weight=ft.FontWeight.BOLD, color=colors['primary_text']),
                    ft.Text(
                        "Clear all session data and reset to pristine initial settings",
                        size=12, italic=True, color=colors['secondary_text']
                    ),
                    ft.Container(height=5),
                    ft.ElevatedButton(
                        "Clear Session & Reset to Defaults",
                        icon=ft.Icons.RESTART_ALT,
                        on_click=self.clear_session,
                        bgcolor=ft.Colors.ORANGE_700,
                        color=ft.Colors.WHITE
                    ),
                ], horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                padding=ft.padding.all(10),
            )
        ], alignment="start", spacing=0)
    
    def log_all_current_selections(self):
        """Log all current selections in one summary"""
        selections = {
            "mode": self.page.session.get("selected_mode"),
            "file_option": self.page.session.get("selected_file_option")
        }
        self.logger.info(f"Current selections summary: {selections}")