from typing import Dict, Any, Union, List
from pathlib import Path
import subprocess
import sys
import tempfile
import json
import traceback
import importlib.util
from datetime import datetime
from analyzer.dynamic_analyzer_base import DynamicAnalyzer as DynamicAnalyzerBase, ExecutionFailure, FailureType, FailureSeverity

class DynamicAnalyzerProfiling(DynamicAnalyzerBase):
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
               
            # Validate Scalene execution with enhanced failure detection
            execution_success = self._validate_scalene_execution(result, context)
            
            # Parse Scalene output
            scalene_data = self._parse_scalene_output(result)
            scalene_data['execution_success'] = execution_success
                
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
   
    def _validate_scalene_execution(self, result: Dict[str, Any], context: str) -> bool:
        """Validate Scalene execution success with detailed failure mode detection"""
        execution_success = True
        
        # Check for execution errors
        if result.get('stderr'):
            error_msg = result['stderr']
            
            # Determine failure mode based on error content
            error_lower = str(error_msg).lower()
            
            if "not found" in error_lower or "command not found" in error_lower:
                failure = ExecutionFailure(
                    failure_type=FailureType.TOOL_ERROR,
                    severity=FailureSeverity.CRITICAL,
                    message=f"Scalene tool not found: {error_msg}",
                    context=context,
                    raw_error=error_msg,
                    is_analysis_finding=False
                )
            elif "timeout" in error_lower or "timed out" in error_lower:
                failure = ExecutionFailure(
                    failure_type=FailureType.TIMEOUT_ERROR,
                    severity=FailureSeverity.WARNING,
                    message=f"Scalene execution timed out: {error_msg}",
                    context=context,
                    raw_error=error_msg,
                    is_analysis_finding=False
                )
            elif "permission denied" in error_lower:
                failure = ExecutionFailure(
                    failure_type=FailureType.FILE_ACCESS_ERROR,
                    severity=FailureSeverity.ERROR,
                    message=f"Scalene permission error: {error_msg}",
                    context=context,
                    raw_error=error_msg,
                    is_analysis_finding=False
                )
            elif "memory error" in error_lower or "out of memory" in error_lower:
                failure = ExecutionFailure(
                    failure_type=FailureType.RUNTIME_ERROR,
                    severity=FailureSeverity.ERROR,
                    message=f"Scalene memory error: {error_msg}",
                    context=context,
                    raw_error=error_msg,
                    is_analysis_finding=False
                )
            else:
                failure = ExecutionFailure(
                    failure_type=FailureType.TOOL_ERROR,
                    severity=FailureSeverity.ERROR,
                    message=f"Scalene execution error: {error_msg}",
                    context=context,
                    raw_error=error_msg,
                    is_analysis_finding=False
                )
            
            self._record_failure(failure)
            execution_success = False
        
        return execution_success
    
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
              
            # Validate VizTracer execution with enhanced failure detection
            execution_success = self._validate_viztracer_execution(result, context)
            
            # Parse VizTracer output
            trace_data = self._parse_viztracer_output(result)
            trace_data['execution_success'] = execution_success
                
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
  
    def _validate_viztracer_execution(self, result: Dict[str, Any], context: str) -> bool:
        """Validate VizTracer execution success with detailed failure mode detection"""
        execution_success = True
        
        # Check for execution errors
        if result.get('stderr'):
            error_msg = result['stderr']
            
            # Determine failure mode based on error content
            error_lower = str(error_msg).lower()
            
            if "not found" in error_lower or "command not found" in error_lower:
                failure = ExecutionFailure(
                    failure_type=FailureType.TOOL_ERROR,
                    severity=FailureSeverity.CRITICAL,
                    message=f"VizTracer tool not found: {error_msg}",
                    context=context,
                    raw_error=error_msg,
                    is_analysis_finding=False
                )
            elif "timeout" in error_lower or "timed out" in error_lower:
                failure = ExecutionFailure(
                    failure_type=FailureType.TIMEOUT_ERROR,
                    severity=FailureSeverity.WARNING,
                    message=f"VizTracer execution timed out: {error_msg}",
                    context=context,
                    raw_error=error_msg,
                    is_analysis_finding=False
                )
            elif "permission denied" in error_lower:
                failure = ExecutionFailure(
                    failure_type=FailureType.FILE_ACCESS_ERROR,
                    severity=FailureSeverity.ERROR,
                    message=f"VizTracer permission error: {error_msg}",
                    context=context,
                    raw_error=error_msg,
                    is_analysis_finding=False
                )
            elif "memory error" in error_lower or "out of memory" in error_lower:
                failure = ExecutionFailure(
                    failure_type=FailureType.RUNTIME_ERROR,
                    severity=FailureSeverity.ERROR,
                    message=f"VizTracer memory error: {error_msg}",
                    context=context,
                    raw_error=error_msg,
                    is_analysis_finding=False
                )
            else:
                failure = ExecutionFailure(
                    failure_type=FailureType.TOOL_ERROR,
                    severity=FailureSeverity.ERROR,
                    message=f"VizTracer execution error: {error_msg}",
                    context=context,
                    raw_error=error_msg,
                    is_analysis_finding=False
                )
            
            self._record_failure(failure)
            execution_success = False
        
        return execution_success
    
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