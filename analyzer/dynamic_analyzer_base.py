import subprocess
import sys
import tempfile
import json
import traceback
import logging
import warnings
import os
from pathlib import Path
from typing import Dict, Any, List, Union
from enum import Enum
from datetime import datetime

# Add this import at the top of the file
from analyzer.file_discovery import FileDiscoveryService

# Configure logging and suppress warnings
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Suppress FAISS warnings
warnings.filterwarnings('ignore', category=UserWarning, module='faiss')
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'  # Suppress TensorFlow warnings if present

class FailureType(Enum):
    """Classification of execution failures"""
    IMPORT_ERROR = "IMPORT_ERROR"
    RUNTIME_ERROR = "RUNTIME_ERROR"
    DEPENDENCY_MISSING = "DEPENDENCY_MISSING"
    TIMEOUT_ERROR = "TIMEOUT_ERROR"
    TOOL_ERROR = "TOOL_ERROR"
    UNKNOWN_ERROR = "UNKNOWN_ERROR"

class FailureSeverity(Enum):
    """Severity levels for execution failures"""
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"

class ExecutionFailure:
    """Structured representation of execution failures"""
    def __init__(self, 
                 failure_type: FailureType, 
                 severity: FailureSeverity, 
                 message: str, 
                 context: str = "", 
                 raw_error: str = "", 
                 traceback_str: str = "", 
                 is_analysis_finding: bool = False, 
                 timestamp: str = None, 
                 execution_log: str = ""):
        self.failure_type = failure_type
        self.severity = severity
        self.message = message
        self.context = context
        self.raw_error = raw_error
        self.traceback_str = traceback_str
        self.is_analysis_finding = is_analysis_finding
        self.timestamp = timestamp or datetime.utcnow().isoformat()
        self.execution_log = execution_log
       
    def to_dict(self) -> Dict[str, Any]:
        return {
            "failure_type": self.failure_type.value,
            "severity": self.severity.value,
            "message": self.message,
            "context": self.context,
            "raw_error": self.raw_error,
            "traceback": self.traceback_str,
            "is_analysis_finding": self.is_analysis_finding,
            "timestamp": self.timestamp,
            "execution_log": self.execution_log
        }

class DynamicAnalyzer:
    def __init__(self):
        self.analysis_results = {} 
        self.execution_failures = []  # Track all execution failures across analysis
        self.failure_count = 0
        self.issue_count = 0
            
    def _classify_failure(self, exception: Exception, context: str = "") -> ExecutionFailure:
        """Classify execution failures based on exception type and context"""
        failure_type = FailureType.UNKNOWN_ERROR
        severity = FailureSeverity.ERROR
        is_analysis_finding = False
           
        # Classify based on exception type
        if isinstance(exception, ImportError):
            failure_type = FailureType.IMPORT_ERROR
            severity = FailureSeverity.WARNING
            is_analysis_finding = True  # Missing imports are valid analysis findings
        elif isinstance(exception, ModuleNotFoundError):
            failure_type = FailureType.DEPENDENCY_MISSING
            severity = FailureSeverity.WARNING
            is_analysis_finding = True  # Missing dependencies are valid analysis findings
        elif isinstance(exception, TimeoutError):
            failure_type = FailureType.TIMEOUT_ERROR
            severity = FailureSeverity.WARNING
        elif isinstance(exception, subprocess.TimeoutExpired):
            failure_type = FailureType.TIMEOUT_ERROR
            severity = FailureSeverity.WARNING
        elif isinstance(exception, FileNotFoundError):
            failure_type = FailureType.TOOL_ERROR
            severity = FailureSeverity.ERROR
        elif isinstance(exception, subprocess.CalledProcessError):
            failure_type = FailureType.TOOL_ERROR
            severity = FailureSeverity.ERROR
        elif isinstance(exception, RuntimeError):
            failure_type = FailureType.RUNTIME_ERROR
            severity = FailureSeverity.ERROR
           
        # Create structured failure record
        failure = ExecutionFailure(
            failure_type=failure_type,
            severity=severity,
            message=str(exception),
            context=context,
            raw_error=str(exception),
            traceback_str=traceback.format_exc(),
            is_analysis_finding=is_analysis_finding
        )
           
        return failure
       
    def _record_failure(self, failure: ExecutionFailure):
        """Record an execution failure and update counters"""
        self.execution_failures.append(failure.to_dict())
        self.failure_count += 1
        if not failure.is_analysis_finding:
            # Only count non-analysis-finding failures as issues
            self.issue_count += 1
       
    def _get_execution_context(self, script_path: Union[str, Path], method_name: str) -> str:
        """Generate context information for execution failures"""
        try:
            script_name = os.path.basename(str(script_path))
            return f"{method_name} analysis of {script_name}"
        except:
            return f"{method_name} analysis"
   
    def _extract_execution_path(self, trace_output: str) -> List[str]:
        """Extract execution path from trace output"""
        lines = trace_output.split('\n')
        execution_lines = [] 
           
        for line in lines:
            if 'call' in line or 'return' in line:
                execution_lines.append(line.strip())
           
        return execution_lines[:100]  # Limit output size
   
    def _get_execution_context(self, script_path: Union[str, Path], method_name: str) -> str:
        """Generate context information for execution failures"""
        try:
            script_name = os.path.basename(str(script_path))
            return f"{method_name} analysis of {script_name}"
        except:
            return f"{method_name} analysis"