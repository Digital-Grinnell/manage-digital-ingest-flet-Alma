"""
Transcript Helper Module for Manage Digital Ingest

This module provides functionality for semi-automated transcript creation from audio files
using Microsoft Word Office 365's transcription feature. It handles:
1. Opening audio files in appropriate locations for easy Word access
2. Watching for completed .docx transcript files
3. Parsing Word transcripts into structured CSV format
4. Managing the transcript workflow

Based on the Digital Grinnell Oral History Workflow:
https://github.com/Digital-Grinnell/Oral-History-Workflow
"""

import os
import re
import csv
import time
import subprocess
from pathlib import Path
from typing import Tuple, List, Optional
from datetime import datetime


class TranscriptHelper:
    """Helper class for managing audio transcription workflow."""
    
    def __init__(self, logger=None):
        """
        Initialize the transcript helper.
        
        Args:
            logger: Optional logger instance for logging operations
        """
        self.logger = logger
        
    def log(self, message: str, level: str = "info"):
        """Log a message if logger is available."""
        if self.logger:
            if level == "error":
                self.logger.error(message)
            elif level == "warning":
                self.logger.warning(message)
            else:
                self.logger.info(message)
    
    def get_word_transcription_instructions(self, mp3_path: str) -> str:
        """
        Generate instructions for transcribing an audio file in Microsoft Word.
        
        Args:
            mp3_path: Path to the MP3 file to transcribe
            
        Returns:
            Formatted instruction text
        """
        filename = os.path.basename(mp3_path)
        instructions = f"""Audio File: {filename}
Location: {os.path.dirname(mp3_path)}

STEPS TO CREATE TRANSCRIPT:

1. Use the "Open Word Online" link above to launch Microsoft Word
   (Office 365 subscription required)

2. Click on the "Home" tab

3. Click the "Dictate" dropdown menu → Select "Transcribe"

4. In the Transcribe pane, click "Upload audio"

5. Browse to and select this file:
   {filename}

6. Wait for transcription to complete (this may take several minutes)
   • Word will identify speakers automatically (Speaker 1, Speaker 2, etc.)
   • Timestamps will be added to each segment
   • You can edit speaker names while transcription is in progress

7. When complete, click "Add to document" to insert the transcript

8. Save the document as a .docx file with the same base name:
   {os.path.splitext(filename)[0]}.docx

9. Save the .docx file in the SAME directory as the MP3 file

10. This application will automatically detect and process the transcript!

OPTIONAL: Edit speaker names in the .docx file before saving:
   • Replace "Speaker 1" with actual names (e.g., "John Smith")
   • Replace "Speaker 2" with actual names (e.g., "Jane Doe")

Note: You must have an active Microsoft 365 subscription with internet
      connection to use Word's transcription feature.
"""
        return instructions
    
    def reveal_in_finder(self, file_path: str) -> bool:
        """
        Open Finder and reveal the file (macOS only).
        
        Args:
            file_path: Path to the file to reveal
            
        Returns:
            True if successful, False otherwise
        """
        try:
            subprocess.run(['open', '-R', file_path], check=True)
            self.log(f"Revealed file in Finder: {file_path}")
            return True
        except subprocess.CalledProcessError as e:
            self.log(f"Failed to reveal file in Finder: {e}", "error")
            return False
        except Exception as e:
            self.log(f"Error revealing file: {e}", "error")
            return False
    
    def parse_docx_transcript(self, docx_path: str, output_csv_path: Optional[str] = None) -> Tuple[bool, str]:
        """
        Parse a Microsoft Word transcript .docx file into CSV format.
        
        The expected format from Word's transcription feature:
        Speaker 1 0:00:05
        This is the text that was said.
        
        Speaker 2 0:00:15
        This is a response.
        
        Args:
            docx_path: Path to the .docx transcript file
            output_csv_path: Optional path for output CSV. If None, uses same name as .docx
            
        Returns:
            Tuple of (success: bool, message: str)
        """
        try:
            # Import here to avoid requiring python-docx unless transcript feature is used
            try:
                from docx import Document
            except ImportError:
                return False, "python-docx package not installed. Install with: pip install python-docx"
            
            # Check if input file exists
            if not os.path.exists(docx_path):
                return False, f"Input file not found: {docx_path}"
            
            # Determine output CSV path
            if output_csv_path is None:
                output_csv_path = os.path.splitext(docx_path)[0] + '.csv'
            
            self.log(f"Parsing transcript: {docx_path}")
            
            # Open the Word document
            doc = Document(docx_path)
            
            # Pattern to match "Speaker X HH:MM:SS" or "Speaker Name HH:MM:SS"
            # Handles formats like "0:05", "0:00:05", "1:23:45"
            speaker_pattern = re.compile(r'^(.+?)\s+(\d{1,2}:\d{2}(?::\d{2})?)$')
            
            transcript_data = []
            current_speaker = None
            current_timestamp = None
            current_text = []
            
            # Process each paragraph
            for para in doc.paragraphs:
                text = para.text.strip()
                
                if not text:
                    continue
                
                # Check if this is a speaker/timestamp line
                match = speaker_pattern.match(text)
                
                if match:
                    # Save previous entry if exists
                    if current_speaker and current_text:
                        transcript_data.append({
                            'Speaker': current_speaker,
                            'Timestamp': current_timestamp,
                            'Text': ' '.join(current_text)
                        })
                    
                    # Start new entry
                    current_speaker = match.group(1).strip()
                    current_timestamp = match.group(2).strip()
                    current_text = []
                else:
                    # This is transcript text
                    if current_speaker:
                        current_text.append(text)
            
            # Save final entry
            if current_speaker and current_text:
                transcript_data.append({
                    'Speaker': current_speaker,
                    'Timestamp': current_timestamp,
                    'Text': ' '.join(current_text)
                })
            
            if not transcript_data:
                return False, "No transcript data found in document. Ensure the document follows the expected format."
            
            # Write to CSV
            with open(output_csv_path, 'w', newline='', encoding='utf-8') as csvfile:
                fieldnames = ['Speaker', 'Timestamp', 'Text']
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                
                writer.writeheader()
                for row in transcript_data:
                    writer.writerow(row)
            
            self.log(f"Successfully created transcript CSV: {output_csv_path}")
            self.log(f"Processed {len(transcript_data)} transcript entries")
            
            return True, f"Successfully created transcript with {len(transcript_data)} entries: {output_csv_path}"
            
        except Exception as e:
            error_msg = f"Error parsing transcript: {str(e)}"
            self.log(error_msg, "error")
            return False, error_msg
    
    def watch_for_transcript(self, directory: str, base_name: str, timeout: int = 300) -> Optional[str]:
        """
        Watch a directory for a new .docx file with the given base name.
        
        Args:
            directory: Directory to watch
            base_name: Base filename (without extension) to look for
            timeout: Maximum seconds to wait (default 300 = 5 minutes)
            
        Returns:
            Path to the detected .docx file, or None if timeout reached
        """
        expected_filename = f"{base_name}.docx"
        expected_path = os.path.join(directory, expected_filename)
        
        self.log(f"Watching for transcript file: {expected_filename}")
        self.log(f"Will check every 5 seconds for up to {timeout} seconds...")
        
        start_time = time.time()
        
        while (time.time() - start_time) < timeout:
            if os.path.exists(expected_path):
                # File exists! Wait a moment to ensure it's fully written
                time.sleep(2)
                self.log(f"Detected transcript file: {expected_filename}")
                return expected_path
            
            time.sleep(5)  # Check every 5 seconds
        
        self.log(f"Timeout reached. No transcript file detected.", "warning")
        return None
    
    def check_for_existing_transcript(self, audio_path: str) -> Optional[str]:
        """
        Check if a transcript already exists for an audio file.
        
        Args:
            audio_path: Path to the audio file (.mp3 or .wav)
            
        Returns:
            Path to existing transcript CSV if found, None otherwise
        """
        base_path = os.path.splitext(audio_path)[0]
        csv_path = f"{base_path}.csv"
        
        if os.path.exists(csv_path):
            self.log(f"Found existing transcript: {csv_path}")
            return csv_path
        
        return None


def open_transcript_workflow(mp3_path: str, logger=None) -> Tuple[bool, str]:
    """
    Convenience function to start the transcript workflow for an MP3 file.
    
    This function:
    1. Reveals the MP3 file in Finder for easy access
    2. Returns instructions for the user
    
    Args:
        mp3_path: Path to the MP3 file to transcribe
        logger: Optional logger instance
        
    Returns:
        Tuple of (success: bool, instructions: str)
    """
    helper = TranscriptHelper(logger)
    
    # Check if transcript already exists
    existing = helper.check_for_existing_transcript(mp3_path)
    if existing:
        return True, f"Transcript already exists: {existing}"
    
    # Reveal in Finder
    helper.reveal_in_finder(mp3_path)
    
    # Get instructions
    instructions = helper.get_word_transcription_instructions(mp3_path)
    
    return True, instructions


def process_transcript_docx(docx_path: str, logger=None) -> Tuple[bool, str]:
    """
    Convenience function to process a completed transcript .docx file.
    
    Args:
        docx_path: Path to the Word transcript document
        logger: Optional logger instance
        
    Returns:
        Tuple of (success: bool, message: str)
    """
    helper = TranscriptHelper(logger)
    return helper.parse_docx_transcript(docx_path)


if __name__ == "__main__":
    # CLI usage for standalone testing
    import sys
    
    if len(sys.argv) < 2:
        print("Usage:")
        print("  python transcript_helper.py <transcript.docx>")
        print("  python transcript_helper.py <transcript.docx> <output.csv>")
        sys.exit(1)
    
    input_file = sys.argv[1]
    output_file = sys.argv[2] if len(sys.argv) > 2 else None
    
    helper = TranscriptHelper()
    success, message = helper.parse_docx_transcript(input_file, output_file)
    
    print(message)
    sys.exit(0 if success else 1)
