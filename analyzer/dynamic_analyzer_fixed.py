#!/usr/bin/env python3
"""
Fixed version of DynamicAnalyzer with corrected safe_execute_profiler method
"""

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
   
    def profile_with_scalene(self, script_path: Union[str, Path]) -> Dict[str, Any]:
        """Profile script using Scalene for CPU, memory, and GPU analysis"""
        context = self._get_execution_context(script_path, "scalene_profiling")
           
        try:
            # Use safe execution wrapper
            result = self.safe_execute_profiler(
                script_path, 
                self._run_scalene_profiling,
                script_path
            )
               
            # Parse Scalene output
            scalene_data = self._parse_scalene_output(result)
               
            # Check for execution errors
            if result.get('stderr'):
                failure = ExecutionFailure(
                    failure_type=FailureType.TOOL_ERROR,
                    severity=FailureSeverity.WARNING,
                    message="Scalene produced stderr output",
                    context=context,
                    raw_error=result['stderr'],
                    is_analysis_finding=False
                )
                self._record_failure(failure)
               
            return scalene_data
               
        except ImportError:
            # Handle Scalene not being installed
            failure = ExecutionFailure(
                failure_type=FailureType.DEPENDENCY_MISSING,
                severity=FailureSeverity.WARNING,
                message="Scalene library not installed",
                context=context,
                raw_error="Scalene import failed",
                is_analysis_finding=True  # Missing dependency is an analysis finding
            )
            self._record_failure(failure)
            return {"error": "Scalene not installed", "execution_failures": [failure.to_dict()]}
               
        except Exception as e:
            failure = self._classify_failure(e, context)
            self._record_failure(failure)
            return {"error": f"Scalene profiling failed: {str(e)}", "execution_failures": [failure.to_dict()]}
   
    def _run_scalene_profiling(self, script_path: str) -> Dict[str, Any]:
        """Run Scalene profiling on target script"""
        from scalene import scalene_profiler
        import importlib.util
           
        # Execute script with Scalene profiling
        with scalene_profiler.enable_profiling():
            # Import and execute target script
            spec = importlib.util.spec_from_file_location("target_module", script_path)
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
           
        # Get profiling results
        return scalene_profiler.get_profiling_results()
   
    def _parse_scalene_output(self, scalene_data: Dict[str, Any]) -> Dict[str, Any]:
        """Parse Scalene profiling output into standardized format"""
        return {
            "cpu_profiling": {
                "hot_spots": scalene_data.get("cpu_hot_spots", []),
                "line_level": scalene_data.get("cpu_line_level", {}),
                "total_time": scalene_data.get("total_time", 0),
                "hot_spot_count": len(scalene_data.get("cpu_hot_spots", []))
            },
            "memory_profiling": {
                "allocations": scalene_data.get("memory_allocations", []),
                "peak_usage": scalene_data.get("peak_memory", 0),
                "growth_patterns": scalene_data.get("memory_growth", []),
                "allocation_count": len(scalene_data.get("memory_allocations", []))
            },
            "gpu_profiling": scalene_data.get("gpu_data", {}),
            "optimization_suggestions": scalene_data.get("ai_suggestions", []),
            "coverage": min(len(scalene_data.get("cpu_line_level", {})) / 1000, 1.0),  # Simplified metric
            "execution_success": True
        }
  
    def trace_with_viztracer(self, script_path: Union[str, Path]) -> Dict[str, Any]:
        """Trace script execution using VizTracer for function call analysis"""
        context = self._get_execution_context(script_path, "viztracer_tracing")
          
        try:
            # Use safe execution wrapper
            result = self.safe_execute_profiler(
                script_path,
                self._run_viztracer_tracing,
                script_path
            )
              
            # Parse VizTracer output
            trace_data = self._parse_viztracer_output(result)
              
            # Check for execution errors
            if result.get('stderr'):
                failure = ExecutionFailure(
                    failure_type=FailureType.TOOL_ERROR,
                    severity=FailureSeverity.WARNING,
                    message="VizTracer produced stderr output",
                    context=context,
                    raw_error=result['stderr'],
                    is_analysis_finding=False
                )
                self._record_failure(failure)
              
            return trace_data
              
        except ImportError:
            # Handle VizTracer not being installed
            failure = ExecutionFailure(
                failure_type=FailureType.DEPENDENCY_MISSING,
                severity=FailureSeverity.WARNING,
                message="VizTracer library not installed",
                context=context,
                raw_error="VizTracer import failed",
                is_analysis_finding=True  # Missing dependency is an analysis finding
            )
            self._record_failure(failure)
            return {"error": "VizTracer not installed", "execution_failures": [failure.to_dict()]}
              
        except Exception as e:
            failure = self._classify_failure(e, context)
            self._record_failure(failure)
            return {"error": f"VizTracer tracing failed: {str(e)}", "execution_failures": [failure.to_dict()]}
  
    def _run_viztracer_tracing(self, script_path: str) -> Dict[str, Any]:
        """Run VizTracer on target script with comprehensive tracing"""
        from viztracer import VizTracer
        import json
        import importlib.util
        import tempfile
          
        # Configure VizTracer with comprehensive options
        tracer = VizTracer(
            log_func_args=True,
            log_func_retval=True,
            max_stack_depth=20
        )
          
        # Start tracing
        tracer.start()
          
        try:
            # Import and execute target script
            spec = importlib.util.spec_from_file_location("target_module", script_path)
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
              
        finally:
            # Stop tracing and get results
            tracer.stop()
              
            # Save to temporary file and parse
            with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
                tracer.save(output_file=f.name)
                  
                # Parse the JSON output
                with open(f.name, 'r') as json_file:
                    return json.load(json_file)
  
    def _parse_viztracer_output(self, trace_data: Dict[str, Any]) -> Dict[str, Any]:
        """Parse VizTracer output into standardized format"""
         
        # Extract function calls
        function_calls = []
        for event in trace_data.get("traceEvents", []):
            if event.get("ph") == "X" and "name" in event:  # Complete events
                function_calls.append({
                    "function_name": event["name"],
                    "start_time": event.get("ts", 0),
                    "duration": event.get("dur", 0),
                    "args": event.get("args", {}).get("func_args", ""),
                    "return_value": event.get("args", {}).get("return_value", ""),
                    "file": event.get("args", {}).get("file", ""),
                    "line": event.get("args", {}).get("line", 0)
                })
          
        # Extract exceptions
        exceptions = []
        for event in trace_data.get("traceEvents", []):
            if event.get("ph") == "i" and "exception" in event.get("name", ""):
                exceptions.append({
                    "exception_type": event["name"],
                    "timestamp": event.get("ts", 0),
                    "file": event.get("args", {}).get("file", ""),
                    "line": event.get("args", {}).get("line", 0),
                    "context": event.get("args", {}).get("context", "")
                })
          
        return {
            "function_calls": function_calls,
            "call_count": len(function_calls),
            "exception_trace": exceptions,
            "exception_count": len(exceptions),
            "execution_flow": self._extract_execution_flow(trace_data),
            "coverage": min(len(function_calls) / 100, 1.0) if function_calls else 0.0,  # Simplified coverage metric
            "execution_success": True
        }
  
    def _extract_execution_flow(self, trace_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Extract execution flow from VizTracer trace data"""
        execution_flow = []
        call_stack = []
          
        for event in trace_data.get("traceEvents", []):
            if event.get("ph") == "B" and "name" in event:  # Begin events
                call_stack.append(event["name"])
            elif event.get("ph") == "E" and call_stack:  # End events
                if len(call_stack) > 1:
                    execution_flow.append({
                        "from": call_stack[-2],
                        "to": call_stack[-1],
                        "timestamp": event.get("ts", 0),
                        "duration": event.get("dur", 0)
                    })
                call_stack.pop()
          
        return execution_flow
  
    def safe_execute_profiler(self, script_path: Union[str, Path], profiler_func, *args, **kwargs) -> Dict[str, Any]:
        """Execute profiler in isolated subprocess with safety checks
           
        Args:
            script_path: Path to the script to analyze (str or Path object)
            profiler_func: The profiler function to execute
            *args: Additional positional arguments for the profiler
            **kwargs: Additional keyword arguments for the profiler
               
        Returns:
            Dict containing profiling results or error information
        """
        context = self._get_execution_context(script_path, "safe_execute_profiler")
           
        try:
            # Convert Path to str for subprocess compatibility
            script_str = str(script_path) if isinstance(script_path, Path) else script_path
               
            # Create temporary execution script for isolation
            with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as temp_file:
                # Get the function source code and module information
                func_module = profiler_func.__module__
                func_name = profiler_func.__name__
                   
                # Write execution code that imports and runs the profiler
                temp_file.write(f"""
import sys
import json
import traceback
import importlib
import os

# Add the analyzer directory to Python path to ensure modules are found
analyzer_path = os.path.join(os.getcwd(), 'analyzer')
if os.path.exists(analyzer_path):
    sys.path.insert(0, analyzer_path)

# Also add the current directory
sys.path.insert(0, os.getcwd())

try:
    # Import the profiler function dynamically
    module = importlib.import_module('{func_module}')
    profiler_func = getattr(module, '{func_name}')
    
    # Execute the profiler with provided arguments
    result = profiler_func(*{repr(args)}, **{repr(kwargs)})
    
    # Return successful result
    print(json.dumps({{'result': result}}))
    
except Exception as e:
    # Return error information with full traceback
    print(json.dumps({{
        'error': str(e),
        'traceback': traceback.format_exc(),
        'error_type': type(e).__name__
    }}))
""")
                temp_script = temp_file.name
               
            # Also ensure the analyzer directory is in the Python path for the subprocess
            env = os.environ.copy()
            analyzer_dir = os.path.join(os.getcwd(), 'analyzer')
            if 'PYTHONPATH' in env:
                env['PYTHONPATH'] = f"{analyzer_dir}{os.pathsep}{env['PYTHONPATH']}"
            else:
                env['PYTHONPATH'] = analyzer_dir
               
            # Execute in subprocess with timeout (180 seconds max)
            result = subprocess.run([
                sys.executable, temp_script, script_str
            ], capture_output=True, text=True, timeout=180, env=env)
               
            # Parse and validate results
            if result.returncode == 0:
                try:
                    parsed = json.loads(result.stdout)
                    if 'error' in parsed:
                        # Profiler execution failed - classify as tool error
                        failure = ExecutionFailure(
                            failure_type=FailureType.TOOL_ERROR,
                            severity=FailureSeverity.ERROR,
                            message=f"Profiler execution failed: {parsed['error']}",
                            context=context,
                            raw_error=parsed['error'],
                            traceback_str=parsed.get('traceback', ''),
                            is_analysis_finding=False
                        )
                        self._record_failure(failure)
                        return {"error": parsed['error'], "execution_failures": [failure.to_dict()]}
                       
                    return parsed['result']
                       
                except json.JSONDecodeError as e:
                    # Failed to parse profiler output
                    failure = ExecutionFailure(
                        failure_type=FailureType.TOOL_ERROR,
                        severity=FailureSeverity.ERROR,
                        message=f"Failed to parse profiler output: {str(e)}",
                        context=context,
                        raw_error=result.stdout,
                        traceback_str="",
                        is_analysis_finding=False
                    )
                    self._record_failure(failure)
                    return {"error": f"Output parsing failed: {str(e)}", "execution_failures": [failure.to_dict()]}
            else:
                # Subprocess failed - classify based on stderr
                error_msg = result.stderr or "Unknown subprocess error"
                failure = ExecutionFailure(
                    failure_type=FailureType.TOOL_ERROR,
                    severity=FailureSeverity.ERROR,
                    message=f"Subprocess execution failed: {error_msg}",
                    context=context,
                    raw_error=error_msg,
                    traceback_str="",
                    is_analysis_finding=False
                )
                self._record_failure(failure)
                return {"error": f"Subprocess failed: {error_msg}", "execution_failures": [failure.to_dict()]}
               
        except subprocess.TimeoutExpired as e:
            # Handle timeout specifically
            failure = self._classify_failure(e, context)
            self._record_failure(failure)
            return {"error": f"Execution timed out after 180 seconds", "execution_failures": [failure.to_dict()]}
               
        except Exception as e:
            # Handle all other exceptions using existing classification system
            failure = self._classify_failure(e, context)
            self._record_failure(failure)
            return {"error": str(e), "execution_failures": [failure.to_dict()]}
           
        finally:
            # Clean up temporary script file
            try:
                if 'temp_script' in locals():
                    os.unlink(temp_script)
            except:
                pass  # Ignore cleanup errors
