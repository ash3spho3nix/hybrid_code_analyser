"""
Input validation and handling for the Hybrid Code Analyzer CLI
"""
import os
import json
from typing import Dict, Any, List, Tuple
import logging
from utils import (
    validate_file_path, validate_directory_path,
    is_valid_file_extension, get_supported_file_extensions,
    get_file_size, get_file_hash
)
from error_handler import AnalysisError

# Configure logging
logger = logging.getLogger(__name__)

def validate_paths(paths: List[str]) -> Tuple[List[str], List[Dict[str, Any]]]:
    """Validate file and directory paths"""
    valid_paths = []
    errors = []
    
    for path in paths:
        try:
            if os.path.isfile(path):
                if validate_file_path(path):
                    valid_paths.append(path)
                else:
                    error = AnalysisError(
                        error_type="file_access_error",
                        message=f"Cannot access file: {path}",
                        severity="high",
                        context={"path": path}
                    )
                    errors.append(error.to_dict())
            elif os.path.isdir(path):
                if validate_directory_path(path):
                    valid_paths.append(path)
                else:
                    error = AnalysisError(
                        error_type="directory_access_error",
                        message=f"Cannot access directory: {path}",
                        severity="high",
                        context={"path": path}
                    )
                    errors.append(error.to_dict())
            else:
                error = AnalysisError(
                    error_type="path_not_found",
                    message=f"Path not found: {path}",
                    severity="high",
                    context={"path": path}
                )
                errors.append(error.to_dict())
        except Exception as e:
            error = AnalysisError(
                error_type="path_validation_error",
                message=f"Error validating path {path}: {str(e)}",
                severity="high",
                context={"path": path, "error": str(e)}
            )
            errors.append(error.to_dict())
    
    return valid_paths, errors

def discover_files_from_paths(paths: List[str]) -> Tuple[List[str], List[Dict[str, Any]]]:
    """Discover all valid files from given paths (files and directories)"""
    all_files = []
    errors = []
    supported_extensions = get_supported_file_extensions()
    
    for path in paths:
        try:
            if os.path.isfile(path):
                # Single file
                if is_valid_file_extension(path, supported_extensions):
                    all_files.append(path)
                else:
                    error = AnalysisError(
                        error_type="unsupported_file_type",
                        message=f"Unsupported file type: {path}",
                        severity="medium",
                        context={"path": path, "extension": os.path.splitext(path)[1]}
                    )
                    errors.append(error.to_dict())
            elif os.path.isdir(path):
                # Directory - discover all supported files
                for root, dirs, files in os.walk(path):
                    for file in files:
                        file_path = os.path.join(root, file)
                        if is_valid_file_extension(file_path, supported_extensions):
                            all_files.append(file_path)
        except Exception as e:
            error = AnalysisError(
                error_type="file_discovery_error",
                message=f"Error discovering files in {path}: {str(e)}",
                severity="high",
                context={"path": path, "error": str(e)}
            )
            errors.append(error.to_dict())
    
    return all_files, errors

def validate_task_description(task: str) -> Tuple[bool, Dict[str, Any]]:
    """Validate task description for AI analysis"""
    if not task:
        return True, {}  # Empty task is allowed
    
    try:
        # Basic validation - task should be reasonable length
        if len(task) > 5000:
            error = AnalysisError(
                error_type="task_too_long",
                message="Task description exceeds maximum length of 5000 characters",
                severity="medium",
                context={"task_length": len(task), "max_length": 5000}
            )
            return False, error.to_dict()
        
        return True, {}
    except Exception as e:
        error = AnalysisError(
            error_type="task_validation_error",
            message=f"Error validating task description: {str(e)}",
            severity="medium",
            context={"error": str(e)}
        )
        return False, error.to_dict()

def parse_changed_files_json(changed_files_path: str) -> Tuple[Dict[str, Any], List[Dict[str, Any]]]:
    """Parse changed files JSON for incremental analysis"""
    changed_files_data = {}
    errors = []
    
    try:
        if not changed_files_path:
            return changed_files_data, errors  # No changed files specified
        
        if not os.path.isfile(changed_files_path):
            error = AnalysisError(
                error_type="file_not_found",
                message=f"Changed files JSON not found: {changed_files_path}",
                severity="high",
                context={"file_path": changed_files_path}
            )
            errors.append(error.to_dict())
            return changed_files_data, errors
        
        with open(changed_files_path, 'r', encoding='utf-8') as f:
            changed_files_data = json.load(f)
        
        # Validate structure
        if not isinstance(changed_files_data, dict):
            error = AnalysisError(
                error_type="invalid_json_structure",
                message="Changed files JSON should be an object with file paths as keys",
                severity="high",
                context={"file_path": changed_files_path}
            )
            errors.append(error.to_dict())
            return {}, errors
        
    except json.JSONDecodeError as e:
        error = AnalysisError(
            error_type="json_parse_error",
            message=f"Invalid JSON in changed files file: {str(e)}",
            severity="high",
            context={"file_path": changed_files_path, "error": str(e)}
        )
        errors.append(error.to_dict())
    except Exception as e:
        error = AnalysisError(
            error_type="changed_files_error",
            message=f"Error processing changed files: {str(e)}",
            severity="high",
            context={"file_path": changed_files_path, "error": str(e)}
        )
        errors.append(error.to_dict())
    
    return changed_files_data, errors

def get_file_metadata(file_path: str) -> Dict[str, Any]:
    """Get metadata for a file (size, hash, modification time)"""
    metadata = {
        "file_path": file_path,
        "size_bytes": 0,
        "hash": "",
        "modified_time": "",
        "extension": os.path.splitext(file_path)[1].lower()
    }
    
    try:
        # Get file stats
        stat = os.stat(file_path)
        metadata["size_bytes"] = stat.st_size
        metadata["modified_time"] = stat.st_mtime
        
        # Calculate hash
        metadata["hash"] = get_file_hash(file_path)
        
    except Exception as e:
        logger.warning(f"Error getting metadata for {file_path}: {str(e)}")
    
    return metadata

def validate_and_prepare_inputs(args: Dict[str, Any]) -> Dict[str, Any]:
    """Validate and prepare all inputs for analysis"""
    result = {
        "valid_files": [],
        "errors": [],
        "task": args.get("task", ""),
        "changed_files": {},
        "metadata": {}
    }
    
    # Validate paths
    paths = args.get("paths", [])
    if not paths:
        error = AnalysisError(
            error_type="no_paths_specified",
            message="No paths specified for analysis",
            severity="critical"
        )
        result["errors"].append(error.to_dict())
        return result
    
    valid_paths, path_errors = validate_paths(paths)
    result["errors"] += path_errors
    
    if not valid_paths:
        return result
    
    # Discover files
    all_files, discovery_errors = discover_files_from_paths(valid_paths)
    result["errors"] += discovery_errors
    
    if not all_files:
        error = AnalysisError(
            error_type="no_valid_files",
            message="No valid files found for analysis",
            severity="critical"
        )
        result["errors"].append(error.to_dict())
        return result
    
    # Validate task
    task_valid, task_error = validate_task_description(args.get("task", ""))
    if task_error:
        result["errors"].append(task_error)
    
    # Parse changed files for incremental analysis
    changed_files_data, changed_files_errors = parse_changed_files_json(args.get("changed_files"))
    result["errors"] += changed_files_errors
    result["changed_files"] = changed_files_data
    
    # Get metadata for all files
    for file_path in all_files:
        result["metadata"][file_path] = get_file_metadata(file_path)
    
    result["valid_files"] = all_files
    
    return result