import os
from typing import List, Dict, Any


class PathValidationResult:
    def __init__(self):
        """Initialize path validation result"""
        self.valid_paths = []
        self.errors = []
        self.is_valid = True
    
    @property
    def error_count(self) -> int:
        """Get the count of validation errors"""
        return len(self.errors)
    
    def add_valid_path(self, path: str):
        """Add a valid path to the result"""
        self.valid_paths.append(path)
    
    def add_error(self, path: str, error_message: str):
        """Add an error to the result"""
        self.errors.append({
            'path': path,
            'error': error_message
        })
        self.is_valid = False
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert validation result to dictionary"""
        return {
            'is_valid': self.is_valid,
            'valid_paths': self.valid_paths,
            'errors': self.errors,
            'error_count': len(self.errors)
        }
    
    def get_error_summary(self) -> str:
        """Get a summary of validation errors"""
        if not self.errors:
            return "All paths are valid"
        
        error_messages = [f"{e['path']}: {e['error']}" for e in self.errors]
        return "Validation errors:\n" + "\n".join(error_messages)


class PathScopeValidator:
    def __init__(self):
        """Initialize the path scope validator"""
        pass
    
    def validate_paths(self, root_paths: List[str]) -> PathValidationResult:
        """
        Validate that all root paths exist and are accessible
        
        Args:
            root_paths: List of root paths to validate
            
        Returns:
            PathValidationResult with validation status and errors
        """
        validation_result = PathValidationResult()
        
        for root_path in root_paths:
            try:
                # Normalize path
                normalized_path = self._normalize_path(root_path)
                
                # Check if path exists
                if not os.path.exists(normalized_path):
                    validation_result.add_error(
                        normalized_path, 
                        f"Path does not exist: {normalized_path}"
                    )
                    continue
                
                # Check if path is accessible (readable)
                if not os.access(normalized_path, os.R_OK):
                    validation_result.add_error(
                        normalized_path,
                        f"Path not readable: {normalized_path}"
                    )
                    continue
                
                # Check if path is a directory
                if not os.path.isdir(normalized_path):
                    validation_result.add_error(
                        normalized_path,
                        f"Path is not a directory: {normalized_path}"
                    )
                    continue
                
                # Add valid path
                validation_result.add_valid_path(normalized_path)
                
            except Exception as e:
                validation_result.add_error(
                    root_path,
                    f"Error validating path: {str(e)}"
                )
        
        return validation_result
    
    def validate_file_scope(self, file_path: str, root_paths: List[str]) -> bool:
        """
        Validate that a file is within the allowed root paths
        
        Args:
            file_path: Path to validate
            root_paths: List of allowed root paths
            
        Returns:
            True if file is within scope, False otherwise
        """
        # Normalize file path
        normalized_file = self._normalize_path(file_path)
        
        # Check against each root path
        for root_path in root_paths:
            normalized_root = self._normalize_path(root_path)
            
            # Use os.path.commonpath to check if file is within root
            try:
                common_path = os.path.commonpath([normalized_file, normalized_root])
                if common_path == normalized_root:
                    return True
            except ValueError:
                # Different drives or invalid paths
                continue
        
        return False
    
    def check_directory_traversal(self, file_path: str, root_path: str) -> bool:
        """
        Check for directory traversal attempts
        
        Args:
            file_path: Path to check
            root_path: Root path to check against
            
        Returns:
            True if directory traversal detected, False otherwise
        """
        # Normalize paths
        normalized_file = self._normalize_path(file_path)
        normalized_root = self._normalize_path(root_path)
        
        # Check if file path starts with root path
        if normalized_file.startswith(normalized_root):
            # Check for suspicious patterns
            relative_path = normalized_file[len(normalized_root):]
            
            # Check for .. in relative path
            if '..' in relative_path or '\\..' in relative_path:
                return True
            
            # Check for symlink traversal
            if os.path.islink(normalized_file):
                target = os.readlink(normalized_file)
                if not self.validate_file_scope(target, [normalized_root]):
                    return True
        else:
            # File is outside root path
            return True
        
        return False
    
    def _normalize_path(self, path: str) -> str:
        """
        Normalize path for consistent comparison
        
        Args:
            path: Path to normalize
            
        Returns:
            Normalized path
        """
        # Convert to absolute path
        abs_path = os.path.abspath(path)
        
        # Normalize path (resolve .., ., etc.)
        normalized = os.path.normpath(abs_path)
        
        # Convert to consistent separator (forward slashes)
        normalized = normalized.replace('\\', '/')
        
        return normalized