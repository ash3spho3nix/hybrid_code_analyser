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

class DynamicAnalyzerExecution(DynamicAnalyzerBase):
    def runtime_trace_execution(self, script_path: Union[str, Path], args: List[str] = None) -> Dict[str, Any]:
        """Trace script execution using PyTrace or similar"""
        context = self._get_execution_context(script_path, "runtime_trace_execution")
           
        try:
            # Use trace module for execution coverage
            result = subprocess.run([
                sys.executable, "-m", "trace", "--trace", str(script_path)
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
       
    def profile_memory_usage(self, script_path: Union[str, Path]) -> Dict[str, Any]:
        """Profile memory usage using memory_profiler"""
        context = self._get_execution_context(script_path, "profile_memory_usage")
           
        try:
            # Create temporary profiling script
            profiler_script = self._create_memory_profiler_script(str(script_path))
               
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
       
    def dynamic_data_flow_analysis(self, script_path: Union[str, Path], test_inputs: List[str]) -> Dict[str, Any]:
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
tracer.run('exec(open("{str(script_path)}").read())')
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