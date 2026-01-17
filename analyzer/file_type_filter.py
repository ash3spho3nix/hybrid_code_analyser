"""
File Type Filter Module

This module provides functionality for filtering files based on their extensions
during the code discovery phase of the hybrid code analyzer.
"""

import os
from typing import List, Set, Tuple, Dict, Any
from collections import defaultdict


class FileTypeFilterReport:
    def __init__(self, supported_extensions: Set[str]):
        """
        Initialize file type filter report
        
        Args:
            supported_extensions: Set of supported extensions
        """
        self.supported_extensions = supported_extensions
        self.filtered_files = []
        self.filtered_extensions = defaultdict(int)
    
    @property
    def total_files_filtered(self) -> int:
        """Get total number of files filtered"""
        return len(self.filtered_files)
    
    def add_filtered_file(self, file_path: str, extension: str):
        """
        Add a file to the filter report
        
        Args:
            file_path: Path of the filtered file
            extension: Extension that caused filtering
        """
        self.filtered_files.append({
            'file': file_path,
            'extension': extension
        })
        self.filtered_extensions[extension] += 1
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert filter report to dictionary
        
        Returns:
            Dictionary representation of the report
        """
        return {
            'total_files_filtered': self.total_files_filtered,
            'supported_extensions': sorted(list(self.supported_extensions)),
            'filtered_extensions': dict(self.filtered_extensions),
            'filtered_files': self.filtered_files
        }
    
    def get_filter_summary(self) -> str:
        """
        Get a human-readable summary of filtering results
        
        Returns:
            Summary string
        """
        total = len(self.filtered_files)
        unique_extensions = len(self.filtered_extensions)
        
        return (f"Filtered {total} files with {unique_extensions} different "
                f"unsupported extensions: {sorted(self.filtered_extensions.keys())}")


class FileTypeFilter:
    def __init__(self, custom_extensions: List[str] = None):
        """
        Initialize the file type filter
        
        Args:
            custom_extensions: Optional list of custom extensions to support
        """
        # Default supported code extensions
        self.default_extensions = {
            '.py', '.js', '.ts', '.java', '.c', '.cpp', '.cs', '.go',
            '.rb', '.php', '.swift', '.kt', '.scala', '.rs', '.sh',
            '.html', '.css', '.sql', '.yaml', '.yml', '.json', '.xml'
        }
        
        # Merge with custom extensions if provided
        self.supported_extensions = self.default_extensions.copy()
        if custom_extensions:
            for ext in custom_extensions:
                if ext.startswith('.'):
                    self.supported_extensions.add(ext)
                else:
                    self.supported_extensions.add(f'.{ext}')
    
    def filter_files(self, files: List[str]) -> Tuple[List[str], FileTypeFilterReport]:
        """
        Filter files to only include supported code file types
        
        Args:
            files: List of file paths to filter
            
        Returns:
            Tuple of (filtered_files, filter_report)
        """
        filtered_files = []
        filter_report = FileTypeFilterReport(self.supported_extensions)
        
        for file_path in files:
            file_ext = self._get_file_extension(file_path)
            
            if file_ext in self.supported_extensions:
                filtered_files.append(file_path)
            else:
                filter_report.add_filtered_file(file_path, file_ext)
        
        return filtered_files, filter_report
    
    def _get_file_extension(self, file_path: str) -> str:
        """
        Extract file extension from path
        
        Args:
            file_path: Path to extract extension from
            
        Returns:
            File extension including dot, or empty string
        """
        # Handle case where file has no extension
        base_name = os.path.basename(file_path)
        
        # Find last dot (handles cases like .tar.gz)
        last_dot_index = base_name.rfind('.')
        
        if last_dot_index > 0:  # Dot must not be first character
            return base_name[last_dot_index:]
        
        return ''
    
    def is_supported_extension(self, extension: str) -> bool:
        """
        Check if an extension is supported
        
        Args:
            extension: Extension to check (with or without dot)
            
        Returns:
            True if the extension is supported
        """
        # Normalize extension
        if not extension.startswith('.'):
            extension = f'.{extension}'
        
        return extension in self.supported_extensions
    
    def add_custom_extension(self, extension: str):
        """
        Add a custom extension to the supported list
        
        Args:
            extension: Extension to add (with or without dot)
        """
        if not extension.startswith('.'):
            extension = f'.{extension}'
        
        self.supported_extensions.add(extension)