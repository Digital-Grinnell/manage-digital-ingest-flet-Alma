"""
CSV Generator view for creating CSV rows from selected files.
"""
import os
import json
import csv
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
        
        if not file_paths:
            self.show_snack("No files selected. Please use File Selector first.", is_error=True)
            return
        
        # Load CSV headings
        headings = self.load_csv_headings()
        if not headings:
            self.show_snack("Failed to load CSV headings", is_error=True)
            return
        
        # Generate rows
        self.generated_csv_data = []
        
        for file_path in file_paths:
            # Create a row dictionary with all headings as keys
            row = {heading: "" for heading in headings}
            
            # Populate basic fields from filename
            filename = os.path.basename(file_path)
            name_without_ext = os.path.splitext(filename)[0]
            
            # Set file_name_1 to the filename
            if 'file_name_1' in row:
                row['file_name_1'] = filename
            
            # Set dc:title to filename without extension
            if 'dc:title' in row:
                row['dc:title'] = name_without_ext
            
            # Add to generated data
            self.generated_csv_data.append(row)
        
        self.logger.info(f"Generated {len(self.generated_csv_data)} CSV rows")
        
        # Save to persistent.json
        self.save_generated_csv()
        
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
                            ], spacing=4),
                            bgcolor=colors['markdown_bg'],
                            border=ft.border.all(1, colors['border']),
                            border_radius=4,
                            padding=10,
                            margin=ft.margin.only(top=5, bottom=10)
                        ),
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
