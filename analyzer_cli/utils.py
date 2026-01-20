"""
Utility functions for the Hybrid Code Analyzer CLI
"""
import os
import json
import hashlib
import uuid
from datetime import datetime
from typing import Dict, Any, List
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def generate_unique_id(prefix: str = "") -> str:
    """Generate a unique identifier for files, functions, or suggestions"""
    unique_id = str(uuid.uuid4())[:8]
    return f"{prefix}{unique_id}" if prefix else unique_id

def get_file_hash(file_path: str) -> str:
    """Calculate SHA256 hash of file content for change detection"""
    try:
        sha256_hash = hashlib.sha256()
        with open(file_path, 'rb') as f:
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        return sha256_hash.hexdigest()
    except Exception as e:
        logger.error(f"Error calculating hash for {file_path}: {e}")
        return ""

def get_file_size(file_path: str) -> int:
    """Get file size in bytes"""
    try:
        return os.path.getsize(file_path)
    except Exception as e:
        logger.error(f"Error getting size for {file_path}: {e}")
        return 0

def get_file_extension(file_path: str) -> str:
    """Get file extension in lowercase"""
    _, ext = os.path.splitext(file_path)
    return ext.lower()

def is_valid_file_extension(file_path: str, allowed_extensions: List[str]) -> bool:
    """Check if file has a valid extension"""
    ext = get_file_extension(file_path)
    return ext in allowed_extensions

def get_current_timestamp() -> str:
    """Get current UTC timestamp in ISO format"""
    return datetime.utcnow().isoformat() + "Z"

def ensure_directory_exists(directory_path: str) -> bool:
    """Create directory if it doesn't exist"""
    try:
        os.makedirs(directory_path, exist_ok=True)
        return True
    except Exception as e:
        logger.error(f"Error creating directory {directory_path}: {e}")
        return False

def write_json_output(output_path: str, data: Dict[str, Any]) -> bool:
    """Write JSON data to file with proper formatting"""
    try:
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        return True
    except Exception as e:
        logger.error(f"Error writing JSON output to {output_path}: {e}")
        return False

def read_json_file(file_path: str) -> Dict[str, Any]:
    """Read JSON file and return parsed data"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"Error reading JSON file {file_path}: {e}")
        return {}

def validate_file_path(file_path: str) -> bool:
    """Validate that file exists and is readable"""
    return os.path.isfile(file_path) and os.access(file_path, os.R_OK)

def validate_directory_path(directory_path: str) -> bool:
    """Validate that directory exists and is readable"""
    return os.path.isdir(directory_path) and os.access(directory_path, os.R_OK | os.X_OK)

def get_supported_file_extensions() -> List[str]:
    """Get list of supported file extensions"""
    return [
        '.py', '.js', '.ts', '.java', '.c', '.cpp', '.cs', '.go', 
        '.rb', '.php', '.swift', '.kt', '.rs', '.html', '.css', '.sql'
    ]

def format_error_message(error_type: str, message: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
    """Format error message for JSON output"""
    error_data = {
        "error_type": error_type,
        "message": message,
        "timestamp": get_current_timestamp()
    }
    if context:
        error_data["context"] = context
    return error_data