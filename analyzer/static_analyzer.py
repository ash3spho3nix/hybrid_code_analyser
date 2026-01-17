import os
import ast
import subprocess
import logging
from typing import Dict, Any, List
from enum import Enum
from tools.semgrep_wrapper import SemgrepWrapper
from datetime import datetime

# Add this import at the top of the file
from analyzer.file_discovery import FileDiscoveryService

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class FailureType(Enum):
    """Classification of execution failures for static analysis"""
    FILE_ACCESS_ERROR = "FILE_ACCESS_ERROR"
    TOOL_ERROR = "TOOL_ERROR"
    PARSING_ERROR = "PARSING_ERROR"
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

class StaticAnalyzer:
    def __init__(self):
        self.semgrep = SemgrepWrapper()
        self._check_tool_status()
        self.execution_failures = []
        self.failure_count = 0
        self.issue_count = 0
             
    def _is_tool_installed(self, tool_name: str) -> bool:
        """Checks if a given tool is installed and accessible."""
        try:
            subprocess.run([tool_name, "--version"], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            return True
        except (subprocess.CalledProcessError, FileNotFoundError):
            return False
         
    def _check_tool_status(self):
        """Checks if Semgrep is installed and accessible."""
        if not self._is_tool_installed("semgrep"):
            print("Warning: 'semgrep' not found. Semgrep analysis will be skipped.")
            self.semgrep = None # Disable Semgrep if not found
     
    def _classify_failure(self, exception: Exception, context: str = "") -> ExecutionFailure:
        """Classify execution failures based on exception type and context"""
        failure_type = FailureType.UNKNOWN_ERROR
        severity = FailureSeverity.ERROR
        is_analysis_finding = False
         
        # Classify based on exception type
        if isinstance(exception, FileNotFoundError):
            failure_type = FailureType.FILE_ACCESS_ERROR
            severity = FailureSeverity.ERROR
        elif isinstance(exception, PermissionError):
            failure_type = FailureType.FILE_ACCESS_ERROR
            severity = FailureSeverity.ERROR
        elif isinstance(exception, subprocess.CalledProcessError):
            failure_type = FailureType.TOOL_ERROR
            severity = FailureSeverity.ERROR
        elif isinstance(exception, SyntaxError):
            failure_type = FailureType.PARSING_ERROR
            severity = FailureSeverity.WARNING
            is_analysis_finding = True  # Syntax errors are valid analysis findings
        elif isinstance(exception, (OSError, IOError)):
            failure_type = FailureType.FILE_ACCESS_ERROR
            severity = FailureSeverity.ERROR
         
        # Create structured failure record
        failure = ExecutionFailure(
            failure_type=failure_type,
            severity=severity,
            message=str(exception),
            context=context,
            raw_error=str(exception),
            traceback_str="",
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
     
    def _get_analysis_context(self, codebase_path: str, method_name: str) -> str:
        """Generate context information for analysis failures"""
        try:
            return f"{method_name} analysis of {codebase_path}"
        except:
            return f"{method_name} analysis"
 
    def analyze_codebase(self, codebase_path: str) -> Dict[str, Any]:
        """Comprehensive analysis of a single codebase using Semgrep"""
        # Reset failure tracking for this analysis run
        self.execution_failures = []
        self.failure_count = 0
        self.issue_count = 0
         
        context = self._get_analysis_context(codebase_path, "analyze_codebase")
         
        if not os.path.exists(codebase_path):
            # Existing error handling remains the same
            failure = ExecutionFailure(
                failure_type=FailureType.FILE_ACCESS_ERROR,
                severity=FailureSeverity.CRITICAL,
                message=f"Codebase path does not exist: {codebase_path}",
                context=context,
                raw_error="",
                traceback_str="",
                is_analysis_finding=False
            )
            self._record_failure(failure)
             
            return {
                "error": f"Codebase path does not exist: {codebase_path}",
                "execution_failures": [failure.to_dict()],
                "analysis_completeness": {
                    "status": "failed",
                    "reason": "Codebase path does not exist"
                }
            }
         
        # Use FileDiscoveryService instead of os.walk
        discovery_service = FileDiscoveryService()
         
        try:
            discovery_result = discovery_service.discover_files([codebase_path], analyzer_type='static')
             
            # Get pre-filtered list of files for analysis
            files_to_analyze = discovery_result.files_for_analysis
             
            # Store discovery artifact for reporting
            discovery_artifact = discovery_result.discovery_artifact
             
        except Exception as e:
            failure = ExecutionFailure(
                failure_type=FailureType.TOOL_ERROR,
                severity=FailureSeverity.ERROR,
                message=f"File discovery failed: {str(e)}",
                context=f"{context} - file discovery",
                raw_error=str(e),
                traceback_str="",
                is_analysis_finding=False
            )
            self._record_failure(failure)
             
            # Fallback to original behavior if discovery fails
            files_to_analyze = []
            for root, dirs, files in os.walk(codebase_path):
                for file in files:
                    file_path = os.path.join(root, file)
                    files_to_analyze.append(file_path)
             
            discovery_artifact = None
         
        # Run Semgrep analysis (primary static analysis tool)
        semgrep_results = self.semgrep.analyze(codebase_path)
         
        # Check for Semgrep errors
        if "error" in semgrep_results:
            # Existing error handling remains the same
            failure = ExecutionFailure(
                failure_type=FailureType.TOOL_ERROR,
                severity=FailureSeverity.ERROR,
                message=f"Semgrep analysis failed: {semgrep_results['error']}",
                context=f"{context} - Semgrep analysis",
                raw_error=semgrep_results.get("error", ""),
                traceback_str="",
                is_analysis_finding=False
            )
            self._record_failure(failure)
         
        # Update custom analysis to use pre-filtered files
        custom_analysis = self._custom_analysis_with_files(files_to_analyze, codebase_path)
         
        # Generate summary with failure information
        summary = self._generate_summary(semgrep_results, custom_analysis)
         
        # Add discovery artifact to results
        result_with_failures = {
            "semgrep": semgrep_results,
            "custom_analysis": custom_analysis,
            "summary": summary,
            "execution_failures": self.execution_failures,
            "failure_count": self.failure_count,
            "issue_count": self.issue_count,
            "analysis_completeness": {
                "status": "complete" if self.failure_count == 0 else "partial",
                "failure_summary": {
                    "total_failures": self.failure_count,
                    "analysis_findings": len([f for f in self.execution_failures if f.get("is_analysis_finding", False)]),
                    "actual_errors": len([f for f in self.execution_failures if not f.get("is_analysis_finding", True)])
                }
            }
        }
         
        # Add discovery artifact if available
        if discovery_artifact:
            result_with_failures["discovery_artifact"] = discovery_artifact
         
        return result_with_failures
     
    def _custom_analysis(self, codebase_path: str) -> Dict[str, Any]:
        """Perform custom static analysis with completeness tracking"""
        context = self._get_analysis_context(codebase_path, "custom_analysis")
         
        analysis = {
            "file_count": 0,
            "file_types": {},
            "complex_files": [],
            "large_files": [],
            "file_access_errors": [],
            "files_discovered": 0,
            "files_analyzed": 0,
            "files_skipped": 0,
            "file_size_distribution": {
                "small": 0,      # < 10KB
                "medium": 0,     # 10KB - 100KB
                "large": 0,      # 100KB - 1MB
                "very_large": 0  # > 1MB
            },
            "coverage_metrics": {
                "coverage_percentage": 0.0,
                "analysis_completeness": "complete"
            }
        }
         
        try:
            for root, dirs, files in os.walk(codebase_path):
                for file in files:
                    file_path = os.path.join(root, file)
                    analysis["files_discovered"] += 1
                     
                    try:
                        analysis["file_count"] += 1
                        analysis["files_analyzed"] += 1
                         
                        # Count file types
                        ext = os.path.splitext(file)[1]
                        analysis["file_types"][ext] = analysis["file_types"].get(ext, 0) + 1
                         
                        # File size analysis with distribution
                        try:
                            size = os.path.getsize(file_path)
                            if size < 10000:  # < 10KB
                                analysis["file_size_distribution"]["small"] += 1
                            elif size < 100000:  # 10KB - 100KB
                                analysis["file_size_distribution"]["medium"] += 1
                            elif size < 1000000:  # 100KB - 1MB
                                analysis["file_size_distribution"]["large"] += 1
                            else:  # > 1MB
                                analysis["file_size_distribution"]["very_large"] += 1
                                analysis["large_files"].append({"file": file_path, "size": size})
                        except Exception as e:
                            failure = self._classify_failure(e, f"{context} - file size check for {file_path}")
                            self._record_failure(failure)
                            analysis["file_access_errors"].append({"file": file_path, "error": str(e)})
                            analysis["files_skipped"] += 1
                             
                    except Exception as e:
                        failure = self._classify_failure(e, f"{context} - file access for {file_path}")
                        self._record_failure(failure)
                        analysis["file_access_errors"].append({"file": file_path, "error": str(e)})
                        analysis["files_skipped"] += 1
                         
        except Exception as e:
            failure = self._classify_failure(e, context)
            self._record_failure(failure)
            analysis["error"] = f"Custom analysis failed: {str(e)}"
            analysis["coverage_metrics"]["analysis_completeness"] = "failed"
         
        # Calculate coverage metrics
        if analysis["files_discovered"] > 0:
            analysis["coverage_metrics"]["coverage_percentage"] = (
                analysis["files_analyzed"] / analysis["files_discovered"]) * 100
             
            # Determine completeness status
            if analysis["files_skipped"] > 0:
                analysis["coverage_metrics"]["analysis_completeness"] = "partial"
            elif analysis["coverage_metrics"]["coverage_percentage"] == 100:
                analysis["coverage_metrics"]["analysis_completeness"] = "complete"
            else:
                analysis["coverage_metrics"]["analysis_completeness"] = "partial"
         
        return analysis
    
    def _generate_summary(self, semgrep: Dict, custom: Dict) -> Dict[str, Any]:
        """Generate analysis summary using Semgrep results with completeness metrics"""
        return {
            "total_issues": len(semgrep.get("results", [])),
            "files_analyzed": custom.get("file_count", 0),
            "files_discovered": custom.get("files_discovered", 0),
            "files_skipped": custom.get("files_skipped", 0),
            "file_types": custom.get("file_types", {}),
            "file_size_distribution": custom.get("file_size_distribution", {}),
            "coverage_percentage": custom.get("coverage_metrics", {}).get("coverage_percentage", 0.0),
            "analysis_completeness": custom.get("coverage_metrics", {}).get("analysis_completeness", "unknown"),
            "quality_metrics": {
                "large_files": len(custom.get("large_files", [])),
                "semgrep_findings": len(semgrep.get("results", [])),
                "coverage_score": custom.get("coverage_metrics", {}).get("coverage_percentage", 0.0)
            }
        }
 
    def _custom_analysis_with_files(self, files_to_analyze: List[str], codebase_path: str) -> Dict[str, Any]:
        """Perform custom static analysis with pre-filtered files"""
        context = self._get_analysis_context(codebase_path, "custom_analysis")
         
        analysis = {
            "file_count": 0,
            "file_types": {},
            "complex_files": [],
            "large_files": [],
            "file_access_errors": [],
            "files_discovered": len(files_to_analyze),
            "files_analyzed": 0,
            "files_skipped": 0,
            "file_size_distribution": {
                "small": 0,      # < 10KB
                "medium": 0,     # 10KB - 100KB
                "large": 0,      # 100KB - 1MB
                "very_large": 0  # > 1MB
            },
            "coverage_metrics": {
                "coverage_percentage": 0.0,
                "analysis_completeness": "complete"
            }
        }
         
        try:
            for file_path in files_to_analyze:
                try:
                    analysis["file_count"] += 1
                    analysis["files_analyzed"] += 1
                     
                    # Count file types
                    ext = os.path.splitext(file_path)[1]
                    analysis["file_types"][ext] = analysis["file_types"].get(ext, 0) + 1
                     
                    # File size analysis with distribution
                    try:
                        size = os.path.getsize(file_path)
                        if size < 10000:  # < 10KB
                            analysis["file_size_distribution"]["small"] += 1
                        elif size < 100000:  # 10KB - 100KB
                            analysis["file_size_distribution"]["medium"] += 1
                        elif size < 1000000:  # 100KB - 1MB
                            analysis["file_size_distribution"]["large"] += 1
                        else:  # > 1MB
                            analysis["file_size_distribution"]["very_large"] += 1
                            analysis["large_files"].append({"file": file_path, "size": size})
                    except Exception as e:
                        failure = self._classify_failure(e, f"{context} - file size check for {file_path}")
                        self._record_failure(failure)
                        analysis["file_access_errors"].append({"file": file_path, "error": str(e)})
                        analysis["files_skipped"] += 1
                         
                except Exception as e:
                    failure = self._classify_failure(e, f"{context} - file access for {file_path}")
                    self._record_failure(failure)
                    analysis["file_access_errors"].append({"file": file_path, "error": str(e)})
                    analysis["files_skipped"] += 1
                     
        except Exception as e:
            failure = self._classify_failure(e, context)
            self._record_failure(failure)
            analysis["error"] = f"Custom analysis failed: {str(e)}"
            analysis["coverage_metrics"]["analysis_completeness"] = "failed"
         
        # Calculate coverage metrics
        if analysis["files_discovered"] > 0:
            analysis["coverage_metrics"]["coverage_percentage"] = (
                analysis["files_analyzed"] / analysis["files_discovered"]) * 100
             
            # Determine completeness status
            if analysis["files_skipped"] > 0:
                analysis["coverage_metrics"]["analysis_completeness"] = "partial"
            elif analysis["coverage_metrics"]["coverage_percentage"] == 100:
                analysis["coverage_metrics"]["analysis_completeness"] = "complete"
            else:
                analysis["coverage_metrics"]["analysis_completeness"] = "partial"
         
        return analysis

    def analyze_codebase_with_files(self, codebase_path: str, files_to_analyze: List[str]) -> Dict[str, Any]:
        """Analyze codebase using pre-filtered list of files"""
        # Reset failure tracking for this analysis run
        self.execution_failures = []
        self.failure_count = 0
        self.issue_count = 0
        
        context = self._get_analysis_context(codebase_path, "analyze_codebase")
        
        if not os.path.exists(codebase_path):
            failure = ExecutionFailure(
                failure_type=FailureType.FILE_ACCESS_ERROR,
                severity=FailureSeverity.CRITICAL,
                message=f"Codebase path does not exist: {codebase_path}",
                context=context,
                raw_error="",
                traceback_str="",
                is_analysis_finding=False
            )
            self._record_failure(failure)
            
            return {
                "error": f"Codebase path does not exist: {codebase_path}",
                "execution_failures": [failure.to_dict()],
                "analysis_completeness": {
                    "status": "failed",
                    "reason": "Codebase path does not exist"
                }
            }
        
        # Run Semgrep analysis (primary static analysis tool)
        semgrep_results = self.semgrep.analyze(codebase_path)
        
        # Check for Semgrep errors
        if "error" in semgrep_results:
            failure = ExecutionFailure(
                failure_type=FailureType.TOOL_ERROR,
                severity=FailureSeverity.ERROR,
                message=f"Semgrep analysis failed: {semgrep_results['error']}",
                context=f"{context} - Semgrep analysis",
                raw_error=semgrep_results.get("error", ""),
                traceback_str="",
                is_analysis_finding=False
            )
            self._record_failure(failure)
        
        # Use the pre-filtered files for custom analysis
        custom_analysis = self._custom_analysis_with_files(files_to_analyze, codebase_path)
        
        # Generate summary with failure information
        summary = self._generate_summary(semgrep_results, custom_analysis)
        
        result_with_failures = {
            "semgrep": semgrep_results,
            "custom_analysis": custom_analysis,
            "summary": summary,
            "execution_failures": self.execution_failures,
            "failure_count": self.failure_count,
            "issue_count": self.issue_count,
            "analysis_completeness": {
                "status": "complete" if self.failure_count == 0 else "partial",
                "failure_summary": {
                    "total_failures": self.failure_count,
                    "analysis_findings": len([f for f in self.execution_failures if f.get("is_analysis_finding", False)]),
                    "actual_errors": len([f for f in self.execution_failures if not f.get("is_analysis_finding", True)])
                }
            }
        }
        
        return result_with_failures