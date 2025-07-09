"""
Report File Tool

This tool allows saving various types of data to files in different formats including
text, JSON, CSV, and markdown. It provides flexible file writing capabilities with
proper error handling and validation.
"""

import json
import os
import csv
from datetime import datetime
from typing import Any, Dict, List, Optional, Union
from crewai.tools import BaseTool
from pydantic import BaseModel, Field


class ReportFileTool(BaseTool):
    """Tool for saving data to files in various formats"""
    
    name: str = "Report File Tool"
    description: str = (
        "Saves data to files in various formats including text, JSON, CSV, and markdown. "
        "Use 'save_text' to save plain text, 'save_json' to save JSON data, 'save_csv' to save "
        "tabular data, 'save_markdown' to save formatted reports, or 'save_custom' for other formats. "
        "Supports creating directories, appending to files, and automatic timestamping."
    )

    def _run(self, action: str, file_path: str, data: Any, 
             append: bool = False, create_dirs: bool = True, 
             add_timestamp: bool = False, encoding: str = "utf-8") -> str:
        """
        Save data to a file in the specified format
        
        Args:
            action: Type of save operation ('save_text', 'save_json')
            file_path: Path where the file should be saved
            data: Data to save (string, dict, list, etc.)
            append: Whether to append to existing file or overwrite
            create_dirs: Whether to create directories if they don't exist
            add_timestamp: Whether to add timestamp to the data
            encoding: File encoding (default: utf-8)
        """
        try:
            if action == "save_text":
                return self._save_text(file_path, data, append, create_dirs, add_timestamp, encoding)
            elif action == "save_json":
                return self._save_json(file_path, data, append, create_dirs, add_timestamp, encoding)
            elif action == "save_csv":
                return self._save_csv(file_path, data, append, create_dirs, add_timestamp, encoding)
            elif action == "save_markdown":
                return self._save_markdown(file_path, data, append, create_dirs, add_timestamp, encoding)
            elif action == "save_custom":
                return self._save_custom(file_path, data, append, create_dirs, add_timestamp, encoding)
            else:
                return f"Error: Unknown action '{action}'. Available actions: save_text, save_json, save_csv, save_markdown, save_custom"
                
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

    def _add_timestamp_to_data(self, data: Any, add_timestamp: bool) -> Any:
        """Add timestamp to data if requested"""
        if not add_timestamp:
            return data
        
        timestamp = datetime.now().isoformat()
        
        if isinstance(data, dict):
            data_copy = data.copy()
            data_copy["timestamp"] = timestamp
            return data_copy
        elif isinstance(data, str):
            return f"[{timestamp}] {data}"
        else:
            return data

    def _save_text(self, file_path: str, data: Any, append: bool, create_dirs: bool, 
                   add_timestamp: bool, encoding: str) -> str:
        """Save data as plain text"""
        self._ensure_directory(file_path, create_dirs)
        
        # Convert data to string if it isn't already
        if not isinstance(data, str):
            if isinstance(data, (dict, list)):
                text_data = json.dumps(data, indent=2, ensure_ascii=False)
            else:
                text_data = str(data)
        else:
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

    def _save_json(self, file_path: str, data: Any, append: bool, create_dirs: bool, 
                   add_timestamp: bool, encoding: str) -> str:
        """Save data as JSON"""
        self._ensure_directory(file_path, create_dirs)
        
        # Add timestamp to data if requested
        data_with_timestamp = self._add_timestamp_to_data(data, add_timestamp)
        
        if append and os.path.exists(file_path):
            # Load existing data and append
            try:
                with open(file_path, "r", encoding=encoding) as f:
                    existing_data = json.load(f)
                
                if isinstance(existing_data, list) and isinstance(data_with_timestamp, (dict, list)):
                    if isinstance(data_with_timestamp, list):
                        existing_data.extend(data_with_timestamp)
                    else:
                        existing_data.append(data_with_timestamp)
                    final_data = existing_data
                elif isinstance(existing_data, dict) and isinstance(data_with_timestamp, dict):
                    existing_data.update(data_with_timestamp)
                    final_data = existing_data
                else:
                    # Create a list with both old and new data
                    final_data = [existing_data, data_with_timestamp]
            except (json.JSONDecodeError, FileNotFoundError):
                final_data = data_with_timestamp
        else:
            final_data = data_with_timestamp
        
        with open(file_path, "w", encoding=encoding) as f:
            json.dump(final_data, f, indent=2, ensure_ascii=False, default=str)
        
        action_type = "appended to" if append else "saved to"
        return f"✅ JSON data {action_type} {file_path} successfully"

    def _save_csv(self, file_path: str, data: Any, append: bool, create_dirs: bool, 
                  add_timestamp: bool, encoding: str) -> str:
        """Save data as CSV"""
        self._ensure_directory(file_path, create_dirs)
        
        if not isinstance(data, list):
            return "Error: CSV data must be a list of dictionaries or lists"
        
        if not data:
            return "Error: Cannot save empty data to CSV"
        
        # Add timestamp column if requested
        if add_timestamp:
            timestamp = datetime.now().isoformat()
            for row in data:
                if isinstance(row, dict):
                    row["timestamp"] = timestamp
                elif isinstance(row, list):
                    row.append(timestamp)
        
        mode = "a" if append else "w"
        file_exists = os.path.exists(file_path) and append
        
        with open(file_path, mode, newline='', encoding=encoding) as f:
            if isinstance(data[0], dict):
                fieldnames = data[0].keys()
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                
                if not file_exists:
                    writer.writeheader()
                writer.writerows(data)
            else:
                writer = csv.writer(f)
                writer.writerows(data)
        
        action_type = "appended to" if append else "saved to"
        return f"✅ CSV data {action_type} {file_path} successfully ({len(data)} rows)"

    def _save_markdown(self, file_path: str, data: Any, append: bool, create_dirs: bool, 
                       add_timestamp: bool, encoding: str) -> str:
        """Save data as markdown format"""
        self._ensure_directory(file_path, create_dirs)
        
        # Convert data to markdown format
        if isinstance(data, dict):
            markdown_content = self._dict_to_markdown(data)
        elif isinstance(data, list):
            markdown_content = self._list_to_markdown(data)
        elif isinstance(data, str):
            markdown_content = data
        else:
            markdown_content = f"```\n{str(data)}\n```"
        
        # Add timestamp header if requested
        if add_timestamp:
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            markdown_content = f"## Report Generated: {timestamp}\n\n{markdown_content}"
        
        mode = "a" if append else "w"
        with open(file_path, mode, encoding=encoding) as f:
            if append:
                f.write("\n\n---\n\n")
            f.write(markdown_content)
        
        action_type = "appended to" if append else "saved to"
        return f"✅ Markdown data {action_type} {file_path} successfully"

    def _dict_to_markdown(self, data: dict) -> str:
        """Convert dictionary to markdown format"""
        markdown = ""
        for key, value in data.items():
            markdown += f"## {key.replace('_', ' ').title()}\n\n"
            if isinstance(value, dict):
                for sub_key, sub_value in value.items():
                    markdown += f"- **{sub_key.replace('_', ' ').title()}**: {sub_value}\n"
            elif isinstance(value, list):
                for item in value:
                    if isinstance(item, dict):
                        markdown += f"- {json.dumps(item, indent=2)}\n"
                    else:
                        markdown += f"- {item}\n"
            else:
                markdown += f"{value}\n"
            markdown += "\n"
        return markdown

    def _list_to_markdown(self, data: list) -> str:
        """Convert list to markdown format"""
        if not data:
            return "No data available."
        
        # Check if it's a list of dictionaries (table format)
        if isinstance(data[0], dict):
            return self._list_of_dicts_to_markdown_table(data)
        else:
            markdown = ""
            for i, item in enumerate(data, 1):
                markdown += f"{i}. {item}\n"
            return markdown

    def _list_of_dicts_to_markdown_table(self, data: List[dict]) -> str:
        """Convert list of dictionaries to markdown table"""
        if not data:
            return "No data available."
        
        # Get all unique keys
        all_keys = set()
        for item in data:
            all_keys.update(item.keys())
        
        keys = sorted(list(all_keys))
        
        # Create header
        header = "| " + " | ".join(key.replace('_', ' ').title() for key in keys) + " |"
        separator = "| " + " | ".join("---" for _ in keys) + " |"
        
        # Create rows
        rows = []
        for item in data:
            row_values = []
            for key in keys:
                value = item.get(key, "")
                if isinstance(value, (dict, list)):
                    value = json.dumps(value)
                row_values.append(str(value))
            rows.append("| " + " | ".join(row_values) + " |")
        
        return "\n".join([header, separator] + rows)

    def _save_custom(self, file_path: str, data: Any, append: bool, create_dirs: bool, 
                     add_timestamp: bool, encoding: str) -> str:
        """Save data in custom format (raw data)"""
        self._ensure_directory(file_path, create_dirs)
        
        # Add timestamp if requested and data is string
        if add_timestamp and isinstance(data, str):
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            data = f"[{timestamp}] {data}"
        
        mode = "ab" if append else "wb"
        
        if isinstance(data, str):
            data_bytes = data.encode(encoding)
        elif isinstance(data, bytes):
            data_bytes = data
        else:
            data_bytes = str(data).encode(encoding)
        
        with open(file_path, mode) as f:
            f.write(data_bytes)
            if append:
                f.write(b"\n")
        
        action_type = "appended to" if append else "saved to"
        return f"✅ Custom data {action_type} {file_path} successfully ({len(data_bytes)} bytes)"