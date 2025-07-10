"""
Report File Tool

This tool allows saving text data to files with proper error handling and validation.
"""

import json
import os
from datetime import datetime
from typing import Any
from crewai.tools import BaseTool


class ReportFileTool(BaseTool):
    """Tool for saving data to text files"""
    
    name: str = "Report File Tool"
    description: str = (
        "Saves string data to text files. Only accepts string input. "
        "Supports creating directories, appending to files, and automatic timestamping."
    )

    def _run(self, file_path: str, data: str, 
             append: bool = False, create_dirs: bool = True, 
             add_timestamp: bool = False, encoding: str = "utf-8") -> str:
        """
        Save data to a text file
        
        Args:
            file_path: Path where the file should be saved
            data: String data to save
            append: Whether to append to existing file or overwrite
            create_dirs: Whether to create directories if they don't exist
            add_timestamp: Whether to add timestamp to the data
            encoding: File encoding (default: utf-8)
        """
        if not isinstance(data, str):
            return f"Error: Only string data is accepted. Received: {type(data).__name__}"
        
        try:
            return self._save_text(file_path, data, append, create_dirs, add_timestamp, encoding)
        except Exception as e:
            return f"Error in ReportFileTool: {str(e)}"

    def _ensure_directory(self, file_path: str, create_dirs: bool) -> bool:
        """Ensure the directory exists for the file path"""
        directory = os.path.dirname(file_path)
        if directory and not os.path.exists(directory):
            if create_dirs:
                os.makedirs(directory, exist_ok=True)
                return True
            else:
                raise FileNotFoundError(f"Directory does not exist: {directory}")
        return True

    def _save_text(self, file_path: str, data: str, append: bool, create_dirs: bool, 
                   add_timestamp: bool, encoding: str) -> str:
        """Save data as plain text"""
        self._ensure_directory(file_path, create_dirs)
        
        text_data = data
        
        # Add timestamp if requested
        if add_timestamp:
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            text_data = f"[{timestamp}] {text_data}"
        
        mode = "a" if append else "w"
        with open(file_path, mode, encoding=encoding) as f:
            f.write(text_data)
            if append:
                f.write("\n")
        
        action_type = "appended to" if append else "saved to"
        return f"✅ Text data {action_type} {file_path} successfully ({len(text_data)} characters)"