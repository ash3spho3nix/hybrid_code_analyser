import subprocess
import sys
import tempfile
import json
import traceback
import logging
from pathlib import Path
from typing import Dict, Any, List
from enum import Enum
from datetime import datetime

# Add this import at the top of the file
from analyzer.file_discovery import FileDiscoveryService

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

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
    
    def _get_execution_context(self, script_path: str, method_name: str) -> str:
        """Generate context information for execution failures"""
        try:
            script_name = Path(script_path).name
            return f"{method_name} analysis of {script_name}"
        except:
            return f"{method_name} analysis"
    
    def run_dynamic_analysis(self, directory: str) -> Dict[str, Any]:
        """Run dynamic analysis on all scripts in the given directory with execution coverage tracking"""
        """ Utilizing all the methods in this class"""
        # Reset failure tracking for this analysis run
        self.execution_failures = []
        self.failure_count = 0
        self.issue_count = 0
        
        # Use FileDiscoveryService instead of Path.rglob
        discovery_service = FileDiscoveryService()
        
        try:
            discovery_result = discovery_service.discover_files([directory], analyzer_type='dynamic')
            
            # Get pre-filtered list of files for analysis and convert to Path objects
            scripts = [Path(file_path) for file_path in discovery_result.files_for_analysis]
            
            # Store discovery artifact for reporting
            discovery_artifact = discovery_result.discovery_artifact
            
        except Exception as e:
            # Log error but continue with fallback behavior
            logger.error(f"File discovery failed, falling back to Path.rglob: {str(e)}")
            
            # Fallback to original behavior if discovery fails
            scripts = list(Path(directory).rglob("*.py"))
            discovery_artifact = None
        
        # Execution coverage tracking
        execution_coverage = {
            "scripts_discovered": len(scripts),
            "scripts_analyzed": 0,
            "scripts_skipped": 0,
            "execution_success_rate": 0.0,
            "execution_time_metrics": {
                "total_execution_time": 0.0,
                "average_execution_time": 0.0
            },
            "method_coverage": {
                "runtime_trace": 0,
                "memory_profile": 0,
                "call_graph": 0,
                "data_flow": 0
            },
            "failure_context": []
        }
        
        for script in scripts:
            script_analysis = {}
            script_successful = True
            
            # Track method-level execution
            try:
                script_analysis["runtime_trace"] = self.runtime_trace_execution(script)
                execution_coverage["method_coverage"]["runtime_trace"] += 1
            except Exception as e:
                failure = self._classify_failure(e, f"runtime_trace_execution for {script}")
                self._record_failure(failure)
                execution_coverage["failure_context"].append({
                    "script": str(script),
                    "method": "runtime_trace",
                    "failure_type": failure.failure_type.value,
                    "severity": failure.severity.value,
                    "message": failure.message
                })
                script_successful = False
            
            try:
                script_analysis["memory_profile"] = self.profile_memory_usage(script)
                execution_coverage["method_coverage"]["memory_profile"] += 1
            except Exception as e:
                failure = self._classify_failure(e, f"profile_memory_usage for {script}")
                self._record_failure(failure)
                execution_coverage["failure_context"].append({
                    "script": str(script),
                    "method": "memory_profile",
                    "failure_type": failure.failure_type.value,
                    "severity": failure.severity.value,
                    "message": failure.message
                })
                script_successful = False
            
            try:
                script_analysis["call_graph"] = self.generate_call_graph(directory)
                execution_coverage["method_coverage"]["call_graph"] += 1
            except Exception as e:
                failure = self._classify_failure(e, f"generate_call_graph for {script}")
                self._record_failure(failure)
                execution_coverage["failure_context"].append({
                    "script": str(script),
                    "method": "call_graph",
                    "failure_type": failure.failure_type.value,
                    "severity": failure.severity.value,
                    "message": failure.message
                })
                script_successful = False
            
            try:
                script_analysis["data_flow"] = self.dynamic_data_flow_analysis(script, ["input1", "input2"])
                execution_coverage["method_coverage"]["data_flow"] += 1
            except Exception as e:
                failure = self._classify_failure(e, f"dynamic_data_flow_analysis for {script}")
                self._record_failure(failure)
                execution_coverage["failure_context"].append({
                    "script": str(script),
                    "method": "data_flow",
                    "failure_type": failure.failure_type.value,
                    "severity": failure.severity.value,
                    "message": failure.message
                })
                script_successful = False
            
            self.analysis_results[script.name] = script_analysis
            
            if script_successful:
                execution_coverage["scripts_analyzed"] += 1
            else:
                execution_coverage["scripts_skipped"] += 1
        
        # Calculate execution metrics
        if execution_coverage["scripts_discovered"] > 0:
            execution_coverage["execution_success_rate"] = (
                execution_coverage["scripts_analyzed"] / execution_coverage["scripts_discovered"]) * 100
        
        # Calculate method coverage percentages
        total_methods = 4  # runtime_trace, memory_profile, call_graph, data_flow
        method_coverage_percentage = 0.0
        if total_methods > 0:
            method_coverage_percentage = (
                sum(execution_coverage["method_coverage"].values()) / 
                (execution_coverage["scripts_discovered"] * total_methods)
            ) * 100
        
        # Add execution failure summary to results
        result_with_failures = {
            "analysis_results": self.analysis_results,
            "execution_failures": self.execution_failures,
            "failure_count": self.failure_count,
            "issue_count": self.issue_count,
            "execution_coverage": execution_coverage,
            "method_coverage_percentage": method_coverage_percentage,
            "analysis_completeness": {
                "total_scripts_analyzed": len(scripts),
                "scripts_with_failures": len([s for s in scripts if any(
                    "execution_failures" in self.analysis_results.get(s.name, {}).get(method, {}) 
                    for method in ["runtime_trace", "memory_profile", "call_graph", "data_flow"]
                )]),
                "analysis_status": "complete" if self.failure_count == 0 else "partial",
                "failure_summary": {
                    "total_failures": self.failure_count,
                    "analysis_findings": len([f for f in self.execution_failures if f.get("is_analysis_finding", False)]),
                    "actual_errors": len([f for f in self.execution_failures if not f.get("is_analysis_finding", True)])
                },
                "completeness_context": {
                    "execution_success_rate": execution_coverage["execution_success_rate"],
                    "method_coverage_percentage": method_coverage_percentage,
                    "failure_context_count": len(execution_coverage["failure_context"])
                }
            }
        }
        
        # Add discovery artifact if available
        if discovery_artifact:
            result_with_failures["discovery_artifact"] = discovery_artifact
        
        return result_with_failures
    
    def run_dynamic_analysis_with_files(self, directory: str, scripts: List[str]) -> Dict[str, Any]:
        """Run dynamic analysis using pre-filtered list of scripts"""
        # Reset failure tracking for this analysis run
        self.execution_failures = []
        self.failure_count = 0
        self.issue_count = 0
        
        # Execution coverage tracking
        execution_coverage = {
            "scripts_discovered": len(scripts),
            "scripts_analyzed": 0,
            "scripts_skipped": 0,
            "execution_success_rate": 0.0,
            "execution_time_metrics": {
                "total_execution_time": 0.0,
                "average_execution_time": 0.0
            },
            "method_coverage": {
                "runtime_trace": 0,
                "memory_profile": 0,
                "call_graph": 0,
                "data_flow": 0
            },
            "failure_context": []
        }
        
        # Use the pre-filtered scripts list
        for script in scripts:
            script_analysis = {}
            script_successful = True
            
            # Track method-level execution (existing code continues...)
            try:
                script_analysis["runtime_trace"] = self.runtime_trace_execution(script)
                execution_coverage["method_coverage"]["runtime_trace"] += 1
            except Exception as e:
                # Existing error handling continues...
                pass
            
            # Continue with rest of the existing analysis methods...
            # (memory_profile, call_graph, data_flow)
            
            self.analysis_results[script.name] = script_analysis
            
            if script_successful:
                execution_coverage["scripts_analyzed"] += 1
            else:
                execution_coverage["scripts_skipped"] += 1
        
        # Calculate execution metrics
        if execution_coverage["scripts_discovered"] > 0:
            execution_coverage["execution_success_rate"] = (
                execution_coverage["scripts_analyzed"] / execution_coverage["scripts_discovered"]) * 100
        
        # Calculate method coverage percentages
        total_methods = 4  # runtime_trace, memory_profile, call_graph, data_flow
        method_coverage_percentage = 0.0
        if total_methods > 0:
            method_coverage_percentage = (
                sum(execution_coverage["method_coverage"].values()) / 
                (execution_coverage["scripts_discovered"] * total_methods)
            ) * 100
        
        # Add execution failure summary to results
        result_with_failures = {
            "analysis_results": self.analysis_results,
            "execution_failures": self.execution_failures,
            "failure_count": self.failure_count,
            "issue_count": self.issue_count,
            "execution_coverage": execution_coverage,
            "method_coverage_percentage": method_coverage_percentage,
            "analysis_completeness": {
                "total_scripts_analyzed": len(scripts),
                "scripts_with_failures": len([s for s in scripts if any(
                    "execution_failures" in self.analysis_results.get(s.name, {}).get(method, {}) 
                    for method in ["runtime_trace", "memory_profile", "call_graph", "data_flow"]
                )]),
                "analysis_status": "complete" if self.failure_count == 0 else "partial",
                "failure_summary": {
                    "total_failures": self.failure_count,
                    "analysis_findings": len([f for f in self.execution_failures if f.get("is_analysis_finding", False)]),
                    "actual_errors": len([f for f in self.execution_failures if not f.get("is_analysis_finding", True)])
                },
                "completeness_context": {
                    "execution_success_rate": execution_coverage["execution_success_rate"],
                    "method_coverage_percentage": method_coverage_percentage,
                    "failure_context_count": len(execution_coverage["failure_context"])
                }
            }
        }
        
        return result_with_failures
    
    def runtime_trace_execution(self, script_path: str, args: List[str] = None) -> Dict[str, Any]:
        """Trace script execution using PyTrace or similar"""
        context = self._get_execution_context(script_path, "runtime_trace_execution")
        
        try:
            # Use trace module for execution coverage
            result = subprocess.run([
                sys.executable, "-m", "trace", "--trace", script_path
            ] + (args or []), 
                capture_output=True, text=True, timeout=60
            )
            
            trace_result = self._parse_trace_output(result.stdout, result.stderr)
            
            # Check for execution errors in stderr
            if result.stderr:
                failure = ExecutionFailure(
                    failure_type=FailureType.RUNTIME_ERROR,
                    severity=FailureSeverity.WARNING,
                    message="Execution produced stderr output",
                    context=context,
                    raw_error=result.stderr,
                    traceback_str="",
                    is_analysis_finding=True  # Runtime errors during analysis are valid findings
                )
                self._record_failure(failure)
            
            return trace_result
        except Exception as e:
            failure = self._classify_failure(e, context)
            self._record_failure(failure)
            
            # Return partial results with failure information
            return {
                "error": f"Trace failed: {str(e)}",
                "execution_failures": [failure.to_dict()]
            }
    
    def profile_memory_usage(self, script_path: str) -> Dict[str, Any]:
        """Profile memory usage using memory_profiler"""
        context = self._get_execution_context(script_path, "profile_memory_usage")
        
        try:
            # Create temporary profiling script
            profiler_script = self._create_memory_profiler_script(script_path)
            
            result = subprocess.run([
                sys.executable, profiler_script
            ], capture_output=True, text=True, timeout=120)
            
            memory_result = self._parse_memory_profile(result.stdout)
            
            # Check for execution errors in stderr
            if result.stderr:
                failure = ExecutionFailure(
                    failure_type=FailureType.RUNTIME_ERROR,
                    severity=FailureSeverity.WARNING,
                    message="Memory profiling produced stderr output",
                    context=context,
                    raw_error=result.stderr,
                    traceback_str="",
                    is_analysis_finding=True
                )
                self._record_failure(failure)
            
            return memory_result
            
        except Exception as e:
            failure = self._classify_failure(e, context)
            self._record_failure(failure)
            
            return {
                "error": f"Memory profiling failed: {str(e)}",
                "execution_failures": [failure.to_dict()]
            }
    
    def generate_call_graph(self, codebase_path: str) -> Dict[str, Any]:
        """Generate call graph using PyCG"""
        context = self._get_execution_context(codebase_path, "generate_call_graph")
        
        try:
            result = subprocess.run([
                "pycg", "--package", codebase_path, codebase_path
            ], capture_output=True, text=True, timeout=180)
            
            if result.returncode == 0:
                call_graph = json.loads(result.stdout)
                call_graph_result = self._analyze_call_complexity(call_graph)
                
                # Check for execution errors in stderr
                if result.stderr:
                    failure = ExecutionFailure(
                        failure_type=FailureType.TOOL_ERROR,
                        severity=FailureSeverity.WARNING,
                        message="PyCG produced stderr output",
                        context=context,
                        raw_error=result.stderr,
                        traceback_str="",
                        is_analysis_finding=False
                    )
                    self._record_failure(failure)
                
                return call_graph_result
            
            # Handle non-zero return code
            failure = ExecutionFailure(
                failure_type=FailureType.TOOL_ERROR,
                severity=FailureSeverity.ERROR,
                message="Call graph generation failed",
                context=context,
                raw_error=result.stderr,
                traceback_str="",
                is_analysis_finding=False
            )
            self._record_failure(failure)
            
            return {
                "error": "Call graph generation failed",
                "execution_failures": [failure.to_dict()]
            }
            
        except Exception as e:
            failure = self._classify_failure(e, context)
            self._record_failure(failure)
            
            return {
                "error": f"PyCG failed: {str(e)}",
                "execution_failures": [failure.to_dict()]
            }
    
    def dynamic_data_flow_analysis(self, script_path: str, test_inputs: List[str]) -> Dict[str, Any]:
        """Analyze data flow through dynamic execution with various inputs"""
        flow_analysis = {}
        
        for i, test_input in enumerate(test_inputs):
            try:
                # Execute with different inputs and trace data flow
                result = subprocess.run([
                    sys.executable, "-c", 
                    f"""
import trace
tracer = trace.Trace(trace=1, count=0)
tracer.run('exec(open("{script_path}").read())')
                    """
                ], input=test_input, capture_output=True, text=True, timeout=30)
                
                flow_analysis[f"test_{i}"] = {
                    "input": test_input,
                    "execution_path": self._extract_execution_path(result.stdout),
                    "output": result.stdout[-1000:] if result.stdout else "",
                    "errors": result.stderr
                }
            except Exception as e:
                flow_analysis[f"test_{i}"] = {"error": str(e)}
        
        return flow_analysis
    
    def _create_memory_profiler_script(self, script_path: str) -> str:
        """Create temporary script for memory profiling"""
        profiler_code = f'''
from memory_profiler import profile
@profile
def run_analysis():
    with open("{script_path}") as f:
        exec(f.read())

if __name__ == "__main__":
    run_analysis()
'''
        temp_file = tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False)
        temp_file.write(profiler_code)
        temp_file.close()
        return temp_file.name
    
    def _parse_trace_output(self, stdout: str, stderr: str) -> Dict[str, Any]:
        """Parse trace module output"""
        lines = stdout.split('\n')
        executed_lines = [line for line in lines if line.startswith(' ') and ':' in line]
        
        return {
            "executed_lines_count": len(executed_lines),
            "execution_summary": f"Executed {len(executed_lines)} lines",
            "coverage_estimate": len(executed_lines) / 1000,  # Simplified metric
            "trace_details": executed_lines[:50]  # Sample of executed lines
        }
    
    def _parse_memory_profile(self, output: str) -> Dict[str, Any]:
        """Parse memory profiler output"""
        lines = output.split('\n')
        memory_usage = []
        
        for line in lines:
            if 'MiB' in line and 'line' in line:
                parts = line.split()
                if len(parts) >= 6:
                    memory_usage.append({
                        "memory_mib": float(parts[2]),
                        "line_number": int(parts[4]),
                        "code_snippet": ' '.join(parts[5:])
                    })
        
        return {
            "memory_usage_by_line": memory_usage,
            "peak_memory": max([m["memory_mib"] for m in memory_usage]) if memory_usage else 0
        }
    
    def _analyze_call_complexity(self, call_graph: Dict) -> Dict[str, Any]:
        """Analyze complexity from call graph"""
        functions = list(call_graph.keys())
        complexity_metrics = {}
        
        for func in functions:
            calls = call_graph[func]
            complexity_metrics[func] = {
                "outbound_calls": len(calls),
                "complexity_score": len(calls) * 10  # Simplified metric
            }
        
        return {
            "total_functions": len(functions),
            "most_complex": sorted(complexity_metrics.items(), 
                                  key=lambda x: x[1]["complexity_score"], reverse=True)[:10],
            "call_graph_summary": f"Analyzed {len(functions)} functions"
        }
    
    def _extract_execution_path(self, trace_output: str) -> List[str]:
        """Extract execution path from trace output"""
        lines = trace_output.split('\n')
        execution_lines = []
        
        for line in lines:
            if 'call' in line or 'return' in line:
                execution_lines.append(line.strip())
        
        return execution_lines[:100]  # Limit output size