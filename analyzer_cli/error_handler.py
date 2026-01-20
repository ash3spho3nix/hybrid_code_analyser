"""
Error handling and safety features for the Hybrid Code Analyzer CLI
"""
import subprocess
import signal
import sys
import traceback
import os
from typing import Dict, Any, List, Optional
from datetime import datetime
import logging
from utils import get_current_timestamp, generate_unique_id

# Configure logging
logger = logging.getLogger(__name__)

# Exit codes
SUCCESS = 0
PARTIAL_ISSUES = 1
CRITICAL_FAILURE = 2
TIMEOUT_ERROR = 3
INPUT_ERROR = 4

def run_with_timeout(command: List[str], timeout: int = 180) -> Dict[str, Any]:
    """Run command in subprocess with timeout"""
    result = {
        "success": False,
        "output": "",
        "error": "",
        "exit_code": -1,
        "timed_out": False
    }
    
    try:
        # Start subprocess
        process = subprocess.Popen(
            command,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            preexec_fn=os.setsid  # Create new process group for better cleanup
        )
        
        try:
            # Wait for process to complete with timeout
            stdout, stderr = process.communicate(timeout=timeout)
            
            result["output"] = stdout
            result["error"] = stderr
            result["exit_code"] = process.returncode
            result["success"] = process.returncode == 0
            
        except subprocess.TimeoutExpired:
            # Timeout occurred
            result["timed_out"] = True
            result["error"] = f"Process timed out after {timeout} seconds"
            
            # Terminate process group
            os.killpg(os.getpgid(process.pid), signal.SIGTERM)
            
            try:
                stdout, stderr = process.communicate(timeout=5)
                result["output"] = stdout
                result["error"] += f"\n{stderr}" if stderr else ""
            except subprocess.TimeoutExpired:
                # Force kill if still running
                os.killpg(os.getpgid(process.pid), signal.SIGKILL)
                result["error"] += "\nProcess forcefully terminated"
    
    except Exception as e:
        result["error"] = f"Failed to execute command: {str(e)}"
        logger.error(f"Command execution failed: {e}")
    
    return result

class AnalysisError(Exception):
    """Custom exception for analysis errors"""
    def __init__(self, error_type: str, message: str, severity: str = "high", 
                 context: Optional[Dict[str, Any]] = None):
        self.error_type = error_type
        self.message = message
        self.severity = severity
        self.context = context or {}
        self.timestamp = get_current_timestamp()
        self.error_id = generate_unique_id("error_")
        
        # Call parent constructor
        super().__init__(f"[{error_type}] {message}")
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert error to dictionary for JSON output"""
        return {
            "error_id": self.error_id,
            "error_type": self.error_type,
            "message": self.message,
            "severity": self.severity,
            "timestamp": self.timestamp,
            "context": self.context
        }

def handle_analysis_error(error: Exception, context: Dict[str, Any] = None) -> Dict[str, Any]:
    """Handle analysis errors and return structured error information"""
    error_data = {
        "error_type": "unknown",
        "message": str(error),
        "severity": "high",
        "timestamp": get_current_timestamp(),
        "context": context or {}
    }
    
    if isinstance(error, AnalysisError):
        return error.to_dict()
    elif isinstance(error, subprocess.TimeoutExpired):
        error_data["error_type"] = "timeout"
        error_data["message"] = "Analysis timed out"
        error_data["severity"] = "critical"
    elif isinstance(error, FileNotFoundError):
        error_data["error_type"] = "file_not_found"
        error_data["message"] = f"File not found: {str(error)}"
        error_data["severity"] = "high"
    elif isinstance(error, PermissionError):
        error_data["error_type"] = "permission_denied"
        error_data["message"] = f"Permission denied: {str(error)}"
        error_data["severity"] = "critical"
    elif isinstance(error, MemoryError):
        error_data["error_type"] = "memory_error"
        error_data["message"] = "Insufficient memory for analysis"
        error_data["severity"] = "critical"
    else:
        error_data["error_type"] = "analysis_error"
        error_data["message"] = f"Analysis failed: {str(error)}"
        error_data["severity"] = "high"
    
    # Add stack trace for debugging
    error_data["stack_trace"] = traceback.format_exc()
    
    return error_data

def classify_error_severity(error_type: str) -> str:
    """Classify error severity based on error type"""
    critical_errors = ["timeout", "memory_error", "permission_denied"]
    high_errors = ["file_not_found", "analysis_error", "syntax_error"]
    medium_errors = ["validation_error", "configuration_error"]
    
    if error_type in critical_errors:
        return "critical"
    elif error_type in high_errors:
        return "high"
    elif error_type in medium_errors:
        return "medium"
    else:
        return "low"

def determine_exit_code(errors: List[Dict[str, Any]]) -> int:
    """Determine appropriate exit code based on errors"""
    if not errors:
        return SUCCESS
    
    # Check for critical errors
    critical_errors = [e for e in errors if e.get("severity") == "critical"]
    if critical_errors:
        return CRITICAL_FAILURE
    
    # Check for timeout errors
    timeout_errors = [e for e in errors if e.get("error_type") == "timeout"]
    if timeout_errors:
        return TIMEOUT_ERROR
    
    # Check for input errors
    input_errors = [e for e in errors if e.get("error_type") in ["file_not_found", "permission_denied"]]
    if input_errors:
        return INPUT_ERROR
    
    # Partial issues (some analysis completed)
    return PARTIAL_ISSUES

def log_error(error_data: Dict[str, Any]):
    """Log error information"""
    severity = error_data.get("severity", "unknown").upper()
    error_type = error_data.get("error_type", "unknown")
    message = error_data.get("message", "No error message")
    
    log_method = getattr(logger, severity.lower(), logger.error)
    log_method(f"[{error_type}] {message}")
    
    if "stack_trace" in error_data:
        logger.debug(f"Stack trace: {error_data['stack_trace']}")

def validate_resource_limits(file_paths: List[str], max_size_mb: int = 10) -> List[Dict[str, Any]]:
    """Validate that files don't exceed resource limits"""
    errors = []
    max_size_bytes = max_size_mb * 1024 * 1024
    
    for file_path in file_paths:
        try:
            file_size = os.path.getsize(file_path)
            if file_size > max_size_bytes:
                error = AnalysisError(
                    error_type="file_too_large",
                    message=f"File {file_path} exceeds maximum size of {max_size_mb}MB",
                    severity="high",
                    context={"file_path": file_path, "file_size": file_size, "max_size": max_size_bytes}
                )
                errors.append(error.to_dict())
        except Exception as e:
            error = AnalysisError(
                error_type="file_access_error",
                message=f"Cannot access file {file_path}: {str(e)}",
                severity="high",
                context={"file_path": file_path}
            )
            errors.append(error.to_dict())
    
    return errors