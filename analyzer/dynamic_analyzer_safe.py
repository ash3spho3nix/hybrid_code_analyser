from typing import Dict, Any, Union, List
from pathlib import Path
import subprocess
import sys
import tempfile
import json
import traceback
import importlib.util
import os
from datetime import datetime
from analyzer.dynamic_analyzer_base import DynamicAnalyzer as DynamicAnalyzerBase, ExecutionFailure, FailureType, FailureSeverity

class DynamicAnalyzerSafe(DynamicAnalyzerBase):
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
    # Import the module containing the profiler function
    module = importlib.import_module('{func_module}')
     
    # Check if the function is a class method (starts with underscore)
    if '{func_name}'.startswith('_'):
        # For class methods, create an instance and call the method
        analyzer_class = getattr(module, 'DynamicAnalyzer')
        analyzer_instance = analyzer_class()
        profiler_func = getattr(analyzer_instance, '{func_name}')
    else:
        # For regular functions
        profiler_func = getattr(module, '{func_name}')
     
    # Execute the profiler with provided arguments
    result = profiler_func(*args, **kwargs)
     
    # Return successful result - ensure proper JSON serialization
    result_dict = {{'result': result}}
    print(json.dumps(result_dict, default=str))
     
    
except Exception as e:
    # Return error information with full traceback
    error_dict = {{
        'error': str(e),
        'traceback': traceback.format_exc(),
        'error_type': type(e).__name__
    }}
    print(json.dumps(error_dict))
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