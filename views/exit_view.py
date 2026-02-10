"""
Exit View for Manage Digital Ingest Application

This module contains the ExitView class for handling application termination.
"""

import flet as ft
import sys
import os
import shutil
import json
from datetime import datetime
from views.base_view import BaseView


class ExitView(BaseView):
    """
    Exit view class for application termination.
    Provides a confirmation dialog with Confirm/Cancel options.
    """
    
    def render(self) -> ft.Column:
        """
        Render the exit view content.
        
        Returns:
            ft.Column: The exit page layout
        """
        self.on_view_enter()
        
        # Get theme-appropriate colors
        colors = self.get_theme_colors()
        
        # Status message container
        status_message = ft.Text("", size=14, text_align=ft.TextAlign.CENTER)
        
        def on_prepare_exit(e):
            """Handle backup of temp directory before exit."""
            self.logger.info("User preparing to exit application")
            
            try:
                # Get temp directory from session
                temp_dir = self.page.session.get("temp_directory")
                
                if temp_dir and os.path.exists(temp_dir):
                    # Check if preservation is enabled
                    preserve_temp = False
                    backup_dir = ""
                    
                    try:
                        persistent_path = os.path.join("_data", "persistent.json")
                        if os.path.exists(persistent_path):
                            with open(persistent_path, 'r', encoding='utf-8') as f:
                                settings = json.load(f)
                                preserve_temp = settings.get("preserve_temp_directory", False)
                                backup_dir = settings.get("temp_backup_directory", "")
                    except Exception as settings_ex:
                        self.logger.error(f"Could not load preservation settings: {settings_ex}")
                    
                    # Backup if enabled
                    if preserve_temp and backup_dir:
                        try:
                            os.makedirs(backup_dir, exist_ok=True)
                            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                            temp_dir_name = os.path.basename(temp_dir)
                            backup_path = os.path.join(backup_dir, f"{temp_dir_name}_backup_{timestamp}")
                            shutil.copytree(temp_dir, backup_path, dirs_exist_ok=True)
                            self.logger.info(f"Backed up temporary directory to: {backup_path}")
                            
                            status_message.value = f"✅ Temporary files backed up to:\n{backup_path}\n\nSafe to close the window now."
                            status_message.color = ft.Colors.GREEN_600
                        except Exception as backup_ex:
                            self.logger.error(f"Error backing up temp directory: {backup_ex}")
                            status_message.value = f"⚠️ Error backing up files: {str(backup_ex)}\n\nPlease close the window to exit anyway."
                            status_message.color = colors['error']
                    else:
                        # Preservation not enabled
                        status_message.value = "Temporary file preservation is not enabled.\n\nSafe to close the window now."
                        status_message.color = colors['secondary_text']
                        self.logger.info("Temp preservation not enabled, no backup needed")
                else:
                    # No temp directory
                    status_message.value = "No temporary files to preserve.\n\nSafe to close the window now."
                    status_message.color = colors['secondary_text']
                    self.logger.info("No temp directory found")
                    
            except Exception as ex:
                self.logger.error(f"Error during exit preparation: {ex}")
                status_message.value = f"⚠️ Error: {str(ex)}\n\nPlease close the window to exit anyway."
                status_message.color = colors['error']
            
            self.page.update()
        
        def on_cancel_exit(e):
            """Handle cancellation of exit action."""
            self.logger.info("User cancelled application exit")
            # Navigate back to home page
            self.page.go("/")
        
        return ft.Column([
            ft.Container(height=50),
            ft.Icon(
                ft.Icons.EXIT_TO_APP,
                size=64,
                color=colors['primary_text']
            ),
            ft.Container(height=20),
            ft.Text(
                "Exit Application",
                size=24,
                weight=ft.FontWeight.BOLD,
                color=colors['primary_text']
            ),
            ft.Container(height=15),
            ft.Text(
                "Click 'Prepare Exit' to save temporary files (if enabled),",
                size=16,
                color=colors['secondary_text']
            ),
            ft.Text(
                "then close the window using the red ● button.",
                size=16,
                color=colors['secondary_text']
            ),
            ft.Container(height=20),
            status_message,
            ft.Container(height=30),
            ft.Row([
                ft.ElevatedButton(
                    "Prepare Exit",
                    icon=ft.Icons.SAVE,
                    on_click=on_prepare_exit,
                    style=ft.ButtonStyle(
                        bgcolor=ft.Colors.BLUE_700,
                        color=ft.Colors.WHITE
                    ),
                    width=150,
                    height=40
                ),
                ft.ElevatedButton(
                    "Cancel",
                    icon=ft.Icons.CANCEL,
                    on_click=on_cancel_exit,
                    style=ft.ButtonStyle(
                        bgcolor=ft.Colors.GREY_400,
                        color=ft.Colors.WHITE
                    ),
                    width=120,
                    height=40
                )
            ], 
            alignment=ft.MainAxisAlignment.CENTER,
            spacing=20)
        ], 
        alignment=ft.MainAxisAlignment.CENTER,
        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
        expand=True)