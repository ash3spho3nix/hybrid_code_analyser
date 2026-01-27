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
from analyzer_cli.utils import get_current_timestamp, generate_unique_id

# Configure logging
logger = logging.getLogger(__name__)

# Exit codes
SUCCESS = 0
PARTIAL_ISSUES = 1
CRITICAL_FAILURE = 2
TIMEOUT_ERROR = 3
INPUT_ERROR = 4
TOOL_HEALTH_CHECK_FAILURE = 5
TOOL_EXECUTION_FAILURE = 6

def run_with_timeout(command: List[str], timeout: int = 180, tool_name: str = "unknown_tool") -> Dict[str, Any]:
    """Run command in subprocess with timeout and enhanced execution validation"""
    result = {
        "success": False,
        "output": "",
        "error": "",
        "exit_code": -1,
        "timed_out": False,
        "tool_name": tool_name,
        "execution_metadata": {
            "start_time": get_current_timestamp(),
            "command": command,
            "timeout_seconds": timeout,
            "tool_category": "external_tool",
            "machine_detectable": True
        }
    }
    
    try:
        # Start subprocess
        # Note: os.setsid is not available on Windows, so we use a conditional approach
        preexec_fn = os.setsid if hasattr(os, 'setsid') else None
        
        process = subprocess.Popen(
            command,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            preexec_fn=preexec_fn  # Create new process group for better cleanup (Unix only)
        )
        
        try:
            # Wait for process to complete with timeout
            stdout, stderr = process.communicate(timeout=timeout)
            
            result["output"] = stdout
            result["error"] = stderr
            result["exit_code"] = process.returncode
            result["success"] = process.returncode == 0
            result["execution_status"] = "completed"
            
            # Add execution timing metadata
            result["execution_metadata"]["end_time"] = get_current_timestamp()
            result["execution_metadata"]["execution_status"] = "success" if result["success"] else "failed"
            
            # Add failure analysis for non-zero exit codes
            if not result["success"]:
                result["failure_reason"] = f"Non-zero exit code: {process.returncode}"
                result["failure_type"] = "execution_failure"
                result["execution_metadata"]["failure_modes"] = [f"exit_code_{process.returncode}"]
                
        except subprocess.TimeoutExpired:
            # Timeout occurred
            result["timed_out"] = True
            result["error"] = f"Process timed out after {timeout} seconds"
            result["execution_status"] = "timeout"
            result["failure_reason"] = "timeout"
            result["failure_type"] = "timeout_error"
            result["execution_metadata"]["failure_modes"] = ["timeout"]
            
            # Terminate process group (Unix) or process (Windows)
            if hasattr(os, 'killpg') and hasattr(os, 'getpgid'):
                os.killpg(os.getpgid(process.pid), signal.SIGTERM)
            else:
                process.terminate()
            
            try:
                stdout, stderr = process.communicate(timeout=5)
                result["output"] = stdout
                result["error"] += f"\n{stderr}" if stderr else ""
            except subprocess.TimeoutExpired:
                # Force kill if still running (Unix) or process (Windows)
                if hasattr(os, 'killpg') and hasattr(os, 'getpgid'):
                    os.killpg(os.getpgid(process.pid), signal.SIGKILL)
                else:
                    process.kill()
                result["error"] += "\nProcess forcefully terminated"
                result["execution_metadata"]["failure_modes"].append("force_terminated")
        
    except FileNotFoundError as e:
        result["error"] = f"Tool not found: {str(e)}"
        result["execution_status"] = "failed"
        result["failure_reason"] = "tool_not_found"
        result["failure_type"] = "tool_not_found_error"
        result["execution_metadata"]["failure_modes"] = ["tool_not_found"]
        logger.error(f"Tool not found: {e}")
        
    except PermissionError as e:
        result["error"] = f"Permission denied: {str(e)}"
        result["execution_status"] = "failed"
        result["failure_reason"] = "permission_denied"
        result["failure_type"] = "permission_error"
        result["execution_metadata"]["failure_modes"] = ["permission_denied"]
        logger.error(f"Permission denied: {e}")
        
    except Exception as e:
        result["error"] = f"Failed to execute command: {str(e)}"
        result["execution_status"] = "failed"
        result["failure_reason"] = "execution_error"
        result["failure_type"] = "execution_error"
        result["execution_metadata"]["failure_modes"] = ["execution_error"]
        logger.error(f"Command execution failed: {e}")
    
    # Add final metadata
    result["execution_metadata"]["end_time"] = result["execution_metadata"].get("end_time", get_current_timestamp())
    result["execution_metadata"]["machine_detectable"] = True
    
    return result


def check_tool_health(tool_name: str, tool_path: str = None) -> Dict[str, Any]:
    """
    Check if a tool is installed and accessible
    
    Args:
        tool_name: Name of the tool to check (e.g., 'semgrep', 'scalene', 'viztracer')
        tool_path: Optional specific path to the tool
        
    Returns:
        Dictionary with health check results including success/failure indicators
    """
    health_check = {
        "tool_name": tool_name,
        "tool_path": tool_path or tool_name,
        "is_installed": False,
        "is_accessible": False,
        "version": None,
        "health_status": "unknown",
        "error": None,
        "timestamp": get_current_timestamp(),
        "machine_detectable": True,
        "metadata": {
            "check_type": "tool_health_check",
            "tool_category": "analysis_tool"
        }
    }
    
    try:
        # Try to get version info to check if tool is accessible
        command = [tool_path or tool_name, "--version"]
        result = subprocess.run(
            command,
            capture_output=True,
            text=True,
            timeout=30
        )
        
        if result.returncode == 0:
            health_check["is_installed"] = True
            health_check["is_accessible"] = True
            health_check["version"] = result.stdout.strip()
            health_check["health_status"] = "healthy"
        else:
            health_check["error"] = f"Tool returned non-zero exit code: {result.returncode}"
            health_check["health_status"] = "unhealthy"
            
    except FileNotFoundError:
        health_check["error"] = f"Tool not found: {tool_name}"
        health_check["health_status"] = "not_installed"
        
    except subprocess.TimeoutExpired:
        health_check["error"] = f"Tool health check timed out for {tool_name}"
        health_check["health_status"] = "timeout"
        
    except Exception as e:
        health_check["error"] = f"Tool health check failed: {str(e)}"
        health_check["health_status"] = "error"
        
    return health_check


def validate_tool_execution_result(result: Dict[str, Any], tool_name: str) -> Dict[str, Any]:
    """
    Validate that a tool executed successfully and add explicit success/failure indicators
    
    Args:
        result: The result dictionary from tool execution
        tool_name: Name of the tool that was executed
        
    Returns:
        Enhanced result dictionary with explicit success/failure indicators
    """
    if not isinstance(result, dict):
        return {
            "success": False,
            "tool_name": tool_name,
            "error": "Invalid result format - expected dictionary",
            "original_result": result,
            "execution_status": "invalid_format",
            "metadata": {
                "validation_type": "tool_execution_validation",
                "timestamp": get_current_timestamp()
            }
        }
        
    # Add explicit success/failure indicators
    validated_result = result.copy()
    
    # Determine execution status based on result content
    if "error" in result and result["error"]:
        validated_result["success"] = False
        validated_result["execution_status"] = "failed"
        validated_result["failure_reason"] = result.get("error", "Unknown error")
        validated_result["failure_type"] = "tool_execution_error"
        
    elif result.get("success") is False:
        validated_result["success"] = False
        validated_result["execution_status"] = "failed"
        validated_result["failure_reason"] = result.get("error", "Tool execution failed")
        validated_result["failure_type"] = "tool_execution_error"
        
    else:
        # If no error and success is not explicitly False, assume success
        validated_result["success"] = True
        validated_result["execution_status"] = "success"
        validated_result["failure_reason"] = None
        validated_result["failure_type"] = None
        
    # Add metadata for machine-detectable failures
    validated_result["metadata"] = {
        "tool_name": tool_name,
        "validation_type": "tool_execution_validation",
        "timestamp": get_current_timestamp(),
        "machine_detectable": True,
        "failure_modes": []
    }
    
    # Add specific failure modes if applicable
    if not validated_result["success"]:
        failure_modes = []
        
        if "timed_out" in result and result["timed_out"]:
            failure_modes.append("timeout")
            
        if "exit_code" in result and result["exit_code"] != 0:
            failure_modes.append(f"exit_code_{result['exit_code']}")
            
        if "error" in result:
            error_msg = str(result["error"])
            if "not found" in error_msg.lower():
                failure_modes.append("tool_not_found")
            elif "permission denied" in error_msg.lower():
                failure_modes.append("permission_denied")
            elif "timeout" in error_msg.lower():
                failure_modes.append("timeout")
            else:
                failure_modes.append("execution_error")
                
        validated_result["metadata"]["failure_modes"] = failure_modes
        
    return validated_result


def create_tool_health_report(tool_health_checks: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Create a comprehensive tool health report from individual health checks
    
    Args:
        tool_health_checks: List of tool health check results
        
    Returns:
        Comprehensive tool health report
    """
    report = {
        "tool_health_report": {
            "timestamp": get_current_timestamp(),
            "tools_checked": len(tool_health_checks),
            "healthy_tools": 0,
            "unhealthy_tools": 0,
            "not_installed_tools": 0,
            "tools_in_error": 0,
            "tools_timed_out": 0,
            "overall_status": "unknown",
            "tool_details": {}
        }
    }
    
    for check in tool_health_checks:
        tool_name = check["tool_name"]
        health_status = check["health_status"]
        
        report["tool_health_report"]["tool_details"][tool_name] = check
        
        if health_status == "healthy":
            report["tool_health_report"]["healthy_tools"] += 1
        elif health_status == "unhealthy":
            report["tool_health_report"]["unhealthy_tools"] += 1
        elif health_status == "not_installed":
            report["tool_health_report"]["not_installed_tools"] += 1
        elif health_status == "error":
            report["tool_health_report"]["tools_in_error"] += 1
        elif health_status == "timeout":
            report["tool_health_report"]["tools_timed_out"] += 1
    
    # Determine overall status
    total_tools = report["tool_health_report"]["tools_checked"]
    healthy_tools = report["tool_health_report"]["healthy_tools"]
    
    if total_tools == 0:
        report["tool_health_report"]["overall_status"] = "no_tools_checked"
    elif healthy_tools == total_tools:
        report["tool_health_report"]["overall_status"] = "all_healthy"
    elif healthy_tools > 0:
        report["tool_health_report"]["overall_status"] = "partial_healthy"
    else:
        report["tool_health_report"]["overall_status"] = "all_unhealthy"
        
    # Add machine-detectable indicators
    report["tool_health_report"]["machine_detectable"] = True
    report["tool_health_report"]["has_failures"] = (
        report["tool_health_report"]["unhealthy_tools"] > 0 or
        report["tool_health_report"]["not_installed_tools"] > 0 or
        report["tool_health_report"]["tools_in_error"] > 0 or
        report["tool_health_report"]["tools_timed_out"] > 0
    )
    
    return report


def add_execution_metadata_to_output(output: Dict[str, Any], tool_name: str, execution_result: Dict[str, Any]) -> Dict[str, Any]:
    """
    Add execution metadata to the output structure to ensure failures are machine-detectable
    
    Args:
        output: The output dictionary to enhance
        tool_name: Name of the tool that was executed
        execution_result: The validated execution result
        
    Returns:
        Enhanced output with execution metadata
    """
    if "metadata" not in output:
        output["metadata"] = {}
        
    if "tool_execution" not in output["metadata"]:
        output["metadata"]["tool_execution"] = {}
        
    # Add tool-specific execution metadata
    output["metadata"]["tool_execution"][tool_name] = {
        "success": execution_result.get("success", False),
        "execution_status": execution_result.get("execution_status", "unknown"),
        "failure_reason": execution_result.get("failure_reason"),
        "failure_type": execution_result.get("failure_type"),
        "failure_modes": execution_result.get("metadata", {}).get("failure_modes", []),
        "timestamp": get_current_timestamp(),
        "machine_detectable": True
    }
    
    # Add overall execution status
    if "execution_status" not in output["metadata"]:
        output["metadata"]["execution_status"] = "partial"  # Default to partial
        
    # Update overall execution status based on tool results
    if not execution_result.get("success", True):
        if output["metadata"]["execution_status"] != "failed":
            output["metadata"]["execution_status"] = "partial"
    else:
        # If this tool succeeded, check if we can upgrade to complete
        all_tools_succeeded = all(
            tool_data.get("success", True)
            for tool_data in output["metadata"]["tool_execution"].values()
        )
        
        if all_tools_succeeded:
            output["metadata"]["execution_status"] = "complete"
    
    return output


def create_analysis_validation_report(
    tool_health_checks: List[Dict[str, Any]],
    execution_results: List[Dict[str, Any]],
    analysis_results: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Create a comprehensive analysis validation report that distinguishes between
    'no bugs found' (clean code) and 'analysis failed silently'
    
    Args:
        tool_health_checks: List of tool health check results
        execution_results: List of tool execution results
        analysis_results: The final analysis results
        
    Returns:
        Comprehensive validation report with explicit success/failure indicators
    """
    validation_report = {
        "validation_report": {
            "timestamp": get_current_timestamp(),
            "analysis_status": "unknown",
            "tool_health_status": "unknown",
            "execution_status": "unknown",
            "analysis_completeness": "unknown",
            "failure_detection": {
                "silent_failures_detected": False,
                "explicit_failures": 0,
                "tool_health_issues": 0,
                "execution_issues": 0,
                "analysis_quality": "unknown"
            },
            "machine_detectable": True,
            "metadata": {
                "report_type": "analysis_validation",
                "purpose": "distinguish_clean_code_from_silent_failures"
            }
        }
    }
    
    # Analyze tool health status
    healthy_tools = 0
    unhealthy_tools = 0
    
    for health_check in tool_health_checks:
        if health_check.get("health_status") == "healthy":
            healthy_tools += 1
        else:
            unhealthy_tools += 1
    
    total_tools = len(tool_health_checks)
    if total_tools > 0:
        if unhealthy_tools == 0:
            validation_report["validation_report"]["tool_health_status"] = "all_healthy"
        elif healthy_tools > 0:
            validation_report["validation_report"]["tool_health_status"] = "partial_healthy"
        else:
            validation_report["validation_report"]["tool_health_status"] = "all_unhealthy"
    
    # Analyze execution status
    successful_executions = 0
    failed_executions = 0
    
    for exec_result in execution_results:
        if exec_result.get("success", False):
            successful_executions += 1
        else:
            failed_executions += 1
    
    total_executions = len(execution_results)
    if total_executions > 0:
        if failed_executions == 0:
            validation_report["validation_report"]["execution_status"] = "all_successful"
        elif successful_executions > 0:
            validation_report["validation_report"]["execution_status"] = "partial_success"
        else:
            validation_report["validation_report"]["execution_status"] = "all_failed"
    
    # Analyze overall analysis status
    has_analysis_results = (
        analysis_results.get("static_results") or
        analysis_results.get("dynamic_results") or
        analysis_results.get("AI_suggestions")
    )
    
    has_errors = (
        analysis_results.get("errors") and len(analysis_results["errors"]) > 0
    )
    
    has_execution_failures = failed_executions > 0
    has_tool_health_issues = unhealthy_tools > 0
    
    # Determine if we have silent failures
    silent_failures_detected = (
        (not has_analysis_results or len(analysis_results.get("static_results", [])) == 0) and
        (has_tool_health_issues or has_execution_failures) and
        not has_errors
    )
    
    # Determine analysis completeness
    if has_analysis_results and not has_execution_failures and not has_tool_health_issues:
        validation_report["validation_report"]["analysis_completeness"] = "complete"
        validation_report["validation_report"]["analysis_status"] = "success"
        
    elif has_analysis_results and (has_execution_failures or has_tool_health_issues):
        validation_report["validation_report"]["analysis_completeness"] = "partial"
        validation_report["validation_report"]["analysis_status"] = "partial_success"
        
    elif not has_analysis_results and (has_execution_failures or has_tool_health_issues):
        validation_report["validation_report"]["analysis_completeness"] = "failed"
        validation_report["validation_report"]["analysis_status"] = "failed"
        
    else:
        # No analysis results and no failures - this might be clean code or silent failure
        validation_report["validation_report"]["analysis_completeness"] = "indeterminate"
        validation_report["validation_report"]["analysis_status"] = "indeterminate"
    
    # Update failure detection
    validation_report["validation_report"]["failure_detection"]["silent_failures_detected"] = silent_failures_detected
    validation_report["validation_report"]["failure_detection"]["explicit_failures"] = failed_executions
    validation_report["validation_report"]["failure_detection"]["tool_health_issues"] = unhealthy_tools
    validation_report["validation_report"]["failure_detection"]["execution_issues"] = failed_executions
    
    # Determine analysis quality
    if validation_report["validation_report"]["analysis_status"] == "success":
        validation_report["validation_report"]["failure_detection"]["analysis_quality"] = "high"
    elif validation_report["validation_report"]["analysis_status"] == "partial_success":
        validation_report["validation_report"]["failure_detection"]["analysis_quality"] = "medium"
    elif validation_report["validation_report"]["analysis_status"] == "failed":
        validation_report["validation_report"]["failure_detection"]["analysis_quality"] = "low"
    else:
        validation_report["validation_report"]["failure_detection"]["analysis_quality"] = "unknown"
    
    # Add detailed failure analysis
    failure_modes = set()
    
    # Collect failure modes from tool health checks
    for health_check in tool_health_checks:
        if health_check.get("health_status") != "healthy":
            failure_modes.add(f"tool_health_{health_check.get('health_status')}")
    
    # Collect failure modes from execution results
    for exec_result in execution_results:
        if not exec_result.get("success", True):
            failure_type = exec_result.get("failure_type")
            if failure_type:
                failure_modes.add(f"execution_{failure_type}")
            
            failure_modes.update(exec_result.get("execution_metadata", {}).get("failure_modes", []))
    
    # Add failure modes to report
    validation_report["validation_report"]["failure_modes"] = list(failure_modes)
    
    # Add recommendations
    recommendations = []
    
    if silent_failures_detected:
        recommendations.append("Silent failures detected - analysis may have failed without explicit errors")
        recommendations.append("Check tool installation and accessibility")
        recommendations.append("Review execution logs for hidden failures")
    
    if has_tool_health_issues:
        recommendations.append("Some tools have health issues - address tool installation/accessibility")
    
    if has_execution_failures:
        recommendations.append("Some tools failed during execution - review execution errors")
    
    if not has_analysis_results and not silent_failures_detected:
        recommendations.append("No analysis results found - this may indicate clean code or failed analysis")
        recommendations.append("Verify analysis tools executed successfully")
    
    validation_report["validation_report"]["recommendations"] = recommendations
    
    return validation_report


def determine_exit_code_from_validation(validation_report: Dict[str, Any]) -> int:
    """
    Determine appropriate exit code based on validation report
    
    Args:
        validation_report: The validation report created by create_analysis_validation_report
        
    Returns:
        Appropriate exit code
    """
    if not validation_report or "validation_report" not in validation_report:
        return CRITICAL_FAILURE
    
    report = validation_report["validation_report"]
    
    # Check for silent failures first (highest priority)
    if report["failure_detection"]["silent_failures_detected"]:
        return TOOL_HEALTH_CHECK_FAILURE
    
    # Check for tool health issues
    if report["tool_health_status"] in ["all_unhealthy", "partial_healthy"]:
        return TOOL_HEALTH_CHECK_FAILURE
    
    # Check for execution failures
    if report["execution_status"] in ["all_failed", "partial_success"]:
        return TOOL_EXECUTION_FAILURE
    
    # Check for explicit failures
    if report["failure_detection"]["explicit_failures"] > 0:
        return CRITICAL_FAILURE
    
    # Check analysis status
    if report["analysis_status"] == "failed":
        return CRITICAL_FAILURE
    elif report["analysis_status"] == "partial_success":
        return PARTIAL_ISSUES
    elif report["analysis_status"] == "success":
        return SUCCESS
    else:
        # Indeterminate - could be clean code or silent failure
        # Lean towards success to avoid false positives
        return SUCCESS

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