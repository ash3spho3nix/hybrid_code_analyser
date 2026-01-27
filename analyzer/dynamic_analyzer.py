"""
Main DynamicAnalyzer module that combines all functionality from helper modules.
This file maintains the original interface while splitting implementation across smaller files.
"""

from analyzer.dynamic_analyzer_base import DynamicAnalyzer as DynamicAnalyzerBase, ExecutionFailure, FailureType, FailureSeverity
from datetime import datetime
from typing import Dict, Any, List, Union
from pathlib import Path
import ast
import importlib.util
import sys
import os
import traceback



# Import all the helper classes to make their methods available
try:
    from analyzer.dynamic_analyzer_profiling import DynamicAnalyzerProfiling
    from analyzer.dynamic_analyzer_execution import DynamicAnalyzerExecution  
    from analyzer.dynamic_analyzer_safe import DynamicAnalyzerSafe
    from analyzer.dynamic_analyzer_helpers import DynamicAnalyzerHelpers
    
    # Set flag indicating all helper classes are available
    HELPER_CLASSES_AVAILABLE = True
except ImportError as e:
    # Graceful degradation when helper classes can't be imported
    HELPER_CLASSES_AVAILABLE = False
    print(f"Warning: Some helper classes could not be imported: {e}")
    
    # Create dummy classes for graceful degradation
    class DynamicAnalyzerProfiling:
        pass
    class DynamicAnalyzerExecution:
        pass
    class DynamicAnalyzerSafe:
        pass
    class DynamicAnalyzerHelpers:
        pass

class DynamicAnalyzer(DynamicAnalyzerBase):
    """
    Main DynamicAnalyzer class that combines all functionality.
    This class uses proper composition pattern to combine functionality from helper classes.
    """
    def __init__(self):
        # Initialize the base class
        super().__init__()
        
        # Initialize helper class components
        self._profiling = DynamicAnalyzerProfiling()
        self._execution = DynamicAnalyzerExecution()
        self._safe = DynamicAnalyzerSafe()
        self._helpers = DynamicAnalyzerHelpers()
        
        # Set up method delegation for proper composition
        self._setup_method_delegation()
     
    def _setup_method_delegation(self):
        """Set up proper method delegation using composition pattern"""
        # Delegate profiling methods
        if hasattr(self._profiling, 'profile_with_scalene'):
            self.profile_with_scalene = self._profiling.profile_with_scalene
        if hasattr(self._profiling, 'trace_with_viztracer'):
            self.trace_with_viztracer = self._profiling.trace_with_viztracer
            
        # Delegate execution methods
        if hasattr(self._execution, 'runtime_trace_execution'):
            self.runtime_trace_execution = self._execution.runtime_trace_execution
        if hasattr(self._execution, 'profile_memory_usage'):
            self.profile_memory_usage = self._execution.profile_memory_usage
        if hasattr(self._execution, 'generate_call_graph'):
            self.generate_call_graph = self._execution.generate_call_graph
        if hasattr(self._execution, 'dynamic_data_flow_analysis'):
            self.dynamic_data_flow_analysis = self._execution.dynamic_data_flow_analysis
            
        # Delegate safe execution methods
        if hasattr(self._safe, 'safe_execute_profiler'):
            self.safe_execute_profiler = self._safe.safe_execute_profiler
            
        # Delegate helper methods
        if hasattr(self._helpers, '_create_memory_profiler_script'):
            self._create_memory_profiler_script = self._helpers._create_memory_profiler_script
        if hasattr(self._helpers, '_parse_trace_output'):
            self._parse_trace_output = self._helpers._parse_trace_output
        if hasattr(self._helpers, '_parse_memory_profile'):
            self._parse_memory_profile = self._helpers._parse_memory_profile
        if hasattr(self._helpers, '_analyze_call_complexity'):
            self._analyze_call_complexity = self._helpers._analyze_call_complexity
        if hasattr(self._helpers, '_extract_execution_path'):
            self._extract_execution_path = self._helpers._extract_execution_path
    
    def _assign_profiling_severity(self, profiling_data: Dict[str, Any]) -> str:
        """
        Assign severity level to profiling results based on performance metrics.
        Uses standard severity scale: critical, high, medium, low
        """
        severity = "low"  # Default severity
         
        # Check for critical performance issues
        if profiling_data.get('execution_time', 0) > 10.0:  # >10 seconds
            severity = "critical"
        elif profiling_data.get('execution_time', 0) > 5.0:  # >5 seconds
            severity = "high"
        elif profiling_data.get('execution_time', 0) > 2.0:  # >2 seconds
            severity = "medium"
         
        # Check memory usage (more realistic thresholds in MB)
        if profiling_data.get('memory_usage', 0) > 100:  # >100 MB
            severity = max(severity, "critical")
        elif profiling_data.get('memory_usage', 0) > 50:  # >50 MB
            severity = max(severity, "high")
        elif profiling_data.get('memory_usage', 0) > 20:  # >20 MB
            severity = max(severity, "medium")
         
        # Check for hotspots (lines consuming significant time)
        hotspots = profiling_data.get('hotspots', [])
        for hotspot in hotspots:
            if hotspot.get('percentage', 0) > 80:  # Single line >80% of function time
                severity = max(severity, "critical")
            elif hotspot.get('percentage', 0) > 50:  # Single line >50% of function time
                severity = max(severity, "high")
            elif hotspot.get('percentage', 0) > 30:  # Single line >30% of function time
                severity = max(severity, "medium")
         
        return severity
     
    def _extract_symbol_context(self, function_name: str, file_path: str) -> Dict[str, Any]:
        """
        Extract class/method context and FQN for a given function.
        
        Args:
            function_name: Name of the function to analyze
            file_path: Path to the source file
             
        Returns:
            Dictionary containing symbol context including class, method, and FQN
        """
        try:
            # Parse the source file to extract symbol context
            with open(file_path, 'r', encoding='utf-8') as file:
                source_code = file.read()
             
            # Parse the AST
            tree = ast.parse(source_code)
            
            # Initialize result
            symbol_context = {
                'function_name': function_name,
                'class_name': None,
                'method_name': None,
                'fqn': function_name,
                'file_path': file_path,
                'is_class_method': False,
                'is_static_method': False
            }
            
            # Traverse the AST to find the function and its context
            for node in ast.walk(tree):
                # Check if this is a function definition
                if isinstance(node, ast.FunctionDef) and node.name == function_name:
                    # Check if this function is inside a class
                    for parent in ast.walk(tree):
                        if isinstance(parent, ast.ClassDef):
                            for item in parent.body:
                                if isinstance(item, ast.FunctionDef) and item.name == function_name:
                                    # This is a method
                                    symbol_context['class_name'] = parent.name
                                    symbol_context['method_name'] = function_name
                                    symbol_context['fqn'] = f"{parent.name}.{function_name}"
                                    symbol_context['is_class_method'] = any(isinstance(decorator, ast.Name) and decorator.id == 'classmethod' for decorator in item.decorator_list)
                                    symbol_context['is_static_method'] = any(isinstance(decorator, ast.Name) and decorator.id == 'staticmethod' for decorator in item.decorator_list)
                                    return symbol_context
                 
                # Check if this is an async function definition
                elif isinstance(node, ast.AsyncFunctionDef) and node.name == function_name:
                    # Check if this async function is inside a class
                    for parent in ast.walk(tree):
                        if isinstance(parent, ast.ClassDef):
                            for item in parent.body:
                                if isinstance(item, ast.AsyncFunctionDef) and item.name == function_name:
                                    # This is an async method
                                    symbol_context['class_name'] = parent.name
                                    symbol_context['method_name'] = function_name
                                    symbol_context['fqn'] = f"{parent.name}.{function_name}"
                                    symbol_context['is_class_method'] = any(isinstance(decorator, ast.Name) and decorator.id == 'classmethod' for decorator in item.decorator_list)
                                    symbol_context['is_static_method'] = any(isinstance(decorator, ast.Name) and decorator.id == 'staticmethod' for decorator in item.decorator_list)
                                    return symbol_context
             
            return symbol_context
            
        except Exception as e:
            # If AST parsing fails, return basic context
            return {
                'function_name': function_name,
                'class_name': None,
                'method_name': None,
                'fqn': function_name,
                'file_path': file_path,
                'is_class_method': False,
                'is_static_method': False,
                'error': str(e)
            }
       
    def _enhance_symbols_with_context(self, symbols: List[Dict[str, Any]], file_path: str) -> List[Dict[str, Any]]:
        """
        Enhance a list of symbols with class/method context and FQN.
        
        Args:
            symbols: List of symbol dictionaries
            file_path: Path to the source file
            
        Returns:
            List of enhanced symbol dictionaries with context and FQN
        """
        enhanced_symbols = []
        
        for symbol in symbols:
            # Extract function name from the symbol
            function_name = symbol.get('function_name') or symbol.get('name') or symbol.get('function')
            
            if function_name:
                # Get symbol context
                context = self._extract_symbol_context(function_name, file_path)
                 
                # Create enhanced symbol
                enhanced_symbol = {**symbol, **context}
                enhanced_symbols.append(enhanced_symbol)
            else:
                # If no function name, keep original symbol
                enhanced_symbols.append(symbol)
        
        return enhanced_symbols
    
    def _classify_failure(self, exception: Exception, context: str = "") -> ExecutionFailure:
        """Enhanced failure classification with additional failure types"""
        # Use the extended failure type enum
        failure_type = FailureType.UNKNOWN_ERROR
        severity = FailureSeverity.ERROR
        is_analysis_finding = False
        
        # Classify based on exception type
        if isinstance(exception, ImportError):
            failure_type = FailureType.IMPORT_ERROR
            severity = FailureSeverity.WARNING
            is_analysis_finding = True
        elif isinstance(exception, ModuleNotFoundError):
            failure_type = FailureType.DEPENDENCY_MISSING
            severity = FailureSeverity.WARNING
            is_analysis_finding = True
        elif isinstance(exception, TimeoutError):
            failure_type = FailureType.TIMEOUT_ERROR
            severity = FailureSeverity.WARNING
        elif isinstance(exception, subprocess.TimeoutExpired):
            failure_type = FailureType.TIMEOUT_ERROR
            severity = FailureSeverity.WARNING
        elif isinstance(exception, FileNotFoundError):
            failure_type = FailureType.TOOL_ERROR
            severity = FailureSeverity.ERROR
        elif isinstance(exception, PermissionError):
            failure_type = FailureTypeExtended.FILE_ACCESS_ERROR
            severity = FailureSeverity.ERROR
        elif isinstance(exception, subprocess.CalledProcessError):
            failure_type = FailureType.TOOL_ERROR
            severity = FailureSeverity.ERROR
        elif isinstance(exception, RuntimeError):
            failure_type = FailureType.RUNTIME_ERROR
            severity = FailureSeverity.ERROR
        elif isinstance(exception, MemoryError):
            failure_type = FailureType.RUNTIME_ERROR
            severity = FailureSeverity.CRITICAL
            
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
    
    def _get_execution_context(self, script_path: Union[str, Path], method_name: str) -> str:
        """Generate context information for execution failures with improved error handling"""
        try:
            script_name = os.path.basename(str(script_path))
            return f"{method_name} analysis of {script_name}"
        except Exception as e:
            # Handle cases where script_path might be invalid
            failure = self._classify_failure(e, "context_generation")
            self._record_failure(failure)
            return f"{method_name} analysis (context generation failed)"
    
    def run_dynamic_analysis(self, codebase_path: str) -> Dict[str, Any]:
        """
        Main entry point for dynamic analysis that orchestrates all profiling methods.
        
        Args:
            codebase_path: Path to the codebase directory to analyze
            
        Returns:
            Dict containing comprehensive analysis results from all profilers
        """
        from analyzer.file_discovery import FileDiscoveryService
        import os
        
        # Initialize comprehensive results dictionary
        analysis_results = {
            'codebase_path': codebase_path,
            'analysis_timestamp': datetime.utcnow().isoformat(),
            'execution_coverage': {},
            'method_coverage': {},
            'execution_failures': [],
            'failure_count': 0,
            'issue_count': 0,
            'files_analyzed': 0,
            'files_with_errors': 0,
            'profiling_results': {}
        }
        
        # Use file discovery service to find Python files
        discovery_service = FileDiscoveryService()
        discovery_result = discovery_service.discover_files([codebase_path], analyzer_type='dynamic')
        
        # Store discovery information
        analysis_results['discovery_summary'] = {
            'files_discovered': discovery_result.files_discovered,
            'files_ignored_by_rule': discovery_result.files_ignored_by_rule,
            'files_ignored_by_type': discovery_result.files_ignored_by_type,
            'files_passed_to_analysis': discovery_result.files_passed_to_analysis
        }
        
        # Get the list of Python files to analyze
        python_files = discovery_result.files_for_analysis
        analysis_results['files_analyzed'] = len(python_files)
        
        # Track method coverage
        method_coverage = {}
        execution_coverage = {}
        
        # Execute all available profiling methods on each file
        for file_path in python_files:
            file_name = os.path.basename(file_path)
            file_results = {}
            
            # Track which methods succeeded for this file
            methods_executed = []
            methods_failed = []
            
            try:
                # Execute Scalene profiling
                try:
                    scalene_result = self.profile_with_scalene(file_path)
                    file_results['scalene_profiling'] = scalene_result
                    methods_executed.append('scalene_profiling')
                except Exception as e:
                    methods_failed.append('scalene_profiling')
                    analysis_results['files_with_errors'] += 1
                    failure = self._classify_failure(e, f"Scalene profiling of {file_name}")
                    self._record_failure(failure)
                    analysis_results['execution_failures'].append(failure.to_dict())
                 
                # Execute VizTracer tracing
                try:
                    viztracer_result = self.trace_with_viztracer(file_path)
                    file_results['viztracer_tracing'] = viztracer_result
                    methods_executed.append('viztracer_tracing')
                except Exception as e:
                    methods_failed.append('viztracer_tracing')
                    analysis_results['files_with_errors'] += 1
                    failure = self._classify_failure(e, f"VizTracer tracing of {file_name}")
                    self._record_failure(failure)
                    analysis_results['execution_failures'].append(failure.to_dict())
                 
                # Execute runtime trace execution
                try:
                    runtime_trace_result = self.runtime_trace_execution(file_path)
                    file_results['runtime_trace_execution'] = runtime_trace_result
                    methods_executed.append('runtime_trace_execution')
                except Exception as e:
                    methods_failed.append('runtime_trace_execution')
                    analysis_results['files_with_errors'] += 1
                    failure = self._classify_failure(e, f"Runtime trace execution of {file_name}")
                    self._record_failure(failure)
                    analysis_results['execution_failures'].append(failure.to_dict())
                 
                # Execute memory profiling
                try:
                    memory_profile_result = self.profile_memory_usage(file_path)
                    file_results['memory_profiling'] = memory_profile_result
                    methods_executed.append('memory_profiling')
                except Exception as e:
                    methods_failed.append('memory_profiling')
                    analysis_results['files_with_errors'] += 1
                    failure = self._classify_failure(e, f"Memory profiling of {file_name}")
                    self._record_failure(failure)
                    analysis_results['execution_failures'].append(failure.to_dict())
                
                # Add severity to each profiling result
                for method_name, method_data in file_results.items():
                    if isinstance(method_data, dict):  # Ensure it's a profiling result
                        method_data['severity'] = self._assign_profiling_severity(method_data)
                        
                        # Enhance symbols with context and FQN if this method contains function symbols
                        if 'function_calls' in method_data:
                            method_data['function_calls'] = self._enhance_symbols_with_context(
                                method_data['function_calls'], file_path
                            )
                        elif 'functions' in method_data:
                            method_data['functions'] = self._enhance_symbols_with_context(
                                method_data['functions'], file_path
                            )
                 
                # Store file-specific results
                analysis_results['profiling_results'][file_name] = file_results
                
                # Update method coverage for this file
                execution_coverage[file_name] = {
                    'methods_executed': methods_executed,
                    'methods_failed': methods_failed,
                    'coverage_percentage': len(methods_executed) / 4.0 if len(methods_executed) + len(methods_failed) > 0 else 0.0
                }
                
            except Exception as e:
                # Handle file-level failures
                analysis_results['files_with_errors'] += 1
                failure = self._classify_failure(e, f"Dynamic analysis of {file_name}")
                self._record_failure(failure)
                analysis_results['execution_failures'].append(failure.to_dict())
                
                # Store error information for this file
                analysis_results['profiling_results'][file_name] = {
                    'error': str(e),
                    'file_processed': False
                }
         
        # Calculate overall method coverage
        total_methods_executed = sum(len(coverage['methods_executed']) for coverage in execution_coverage.values())
        total_methods_attempted = sum(len(coverage['methods_executed']) + len(coverage['methods_failed']) for coverage in execution_coverage.values())
        
        method_coverage = {
            'scalene_profiling': sum(1 for cov in execution_coverage.values() if 'scalene_profiling' in cov['methods_executed']),
            'viztracer_tracing': sum(1 for cov in execution_coverage.values() if 'viztracer_tracing' in cov['methods_executed']),
            'runtime_trace_execution': sum(1 for cov in execution_coverage.values() if 'runtime_trace_execution' in cov['methods_executed']),
            'memory_profiling': sum(1 for cov in execution_coverage.values() if 'memory_profiling' in cov['methods_executed'])
        }
        
        # Calculate coverage percentages
        if len(execution_coverage) > 0:
            # Create a list of method names to avoid modifying dict during iteration
            methods = list(method_coverage.keys())
            for method in methods:
                method_coverage[method + '_percentage'] = method_coverage[method] / len(execution_coverage)
         
        analysis_results['execution_coverage'] = execution_coverage
        analysis_results['method_coverage'] = method_coverage
        analysis_results['method_coverage_percentage'] = total_methods_executed / total_methods_attempted if total_methods_attempted > 0 else 0.0
        
        # Update failure counts
        analysis_results['failure_count'] = self.failure_count
        analysis_results['issue_count'] = self.issue_count
        
        return analysis_results
    
    def run_dynamic_analysis_with_files(self, codebase_path: str, files: List[str]) -> Dict[str, Any]:
        """
        Run dynamic analysis on a specific list of files (used by multi-codebase analyzer).
        
        Args:
            codebase_path: Path to the codebase directory
            files: List of specific files to analyze
            
        Returns:
            Dict containing comprehensive analysis results from all profilers
        """
        import os
        
        # Initialize comprehensive results dictionary
        analysis_results = {
            'codebase_path': codebase_path,
            'analysis_timestamp': datetime.utcnow().isoformat(),
            'execution_coverage': {},
            'method_coverage': {},
            'execution_failures': [],
            'failure_count': 0,
            'issue_count': 0,
            'files_analyzed': len(files),
            'files_with_errors': 0,
            'profiling_results': {}
        }
        
        # Track method coverage
        method_coverage = {}
        execution_coverage = {}
        
        # Execute all available profiling methods on each file
        for file_path in files:
            file_name = os.path.basename(file_path)
            file_results = {}
            
            # Track which methods succeeded for this file
            methods_executed = []
            methods_failed = []
            
            try:
                # Execute Scalene profiling
                try:
                    scalene_result = self.profile_with_scalene(file_path)
                    file_results['scalene_profiling'] = scalene_result
                    methods_executed.append('scalene_profiling')
                except Exception as e:
                    methods_failed.append('scalene_profiling')
                    analysis_results['files_with_errors'] += 1
                    failure = self._classify_failure(e, f"Scalene profiling of {file_name}")
                    self._record_failure(failure)
                    analysis_results['execution_failures'].append(failure.to_dict())
                 
                # Execute VizTracer tracing
                try:
                    viztracer_result = self.trace_with_viztracer(file_path)
                    file_results['viztracer_tracing'] = viztracer_result
                    methods_executed.append('viztracer_tracing')
                except Exception as e:
                    methods_failed.append('viztracer_tracing')
                    analysis_results['files_with_errors'] += 1
                    failure = self._classify_failure(e, f"VizTracer tracing of {file_name}")
                    self._record_failure(failure)
                    analysis_results['execution_failures'].append(failure.to_dict())
                 
                # Execute runtime trace execution
                try:
                    runtime_trace_result = self.runtime_trace_execution(file_path)
                    file_results['runtime_trace_execution'] = runtime_trace_result
                    methods_executed.append('runtime_trace_execution')
                except Exception as e:
                    methods_failed.append('runtime_trace_execution')
                    analysis_results['files_with_errors'] += 1
                    failure = self._classify_failure(e, f"Runtime trace execution of {file_name}")
                    self._record_failure(failure)
                    analysis_results['execution_failures'].append(failure.to_dict())
                 
                # Execute memory profiling
                try:
                    memory_profile_result = self.profile_memory_usage(file_path)
                    file_results['memory_profiling'] = memory_profile_result
                    methods_executed.append('memory_profiling')
                except Exception as e:
                    methods_failed.append('memory_profiling')
                    analysis_results['files_with_errors'] += 1
                    failure = self._classify_failure(e, f"Memory profiling of {file_name}")
                    self._record_failure(failure)
                    analysis_results['execution_failures'].append(failure.to_dict())
                
                # Add severity to each profiling result
                for method_name, method_data in file_results.items():
                    if isinstance(method_data, dict):  # Ensure it's a profiling result
                        method_data['severity'] = self._assign_profiling_severity(method_data)
                 
                # Store file-specific results
                analysis_results['profiling_results'][file_name] = file_results
                
                # Update method coverage for this file
                execution_coverage[file_name] = {
                    'methods_executed': methods_executed,
                    'methods_failed': methods_failed,
                    'coverage_percentage': len(methods_executed) / 4.0 if len(methods_executed) + len(methods_failed) > 0 else 0.0
                }
                
            except Exception as e:
                # Handle file-level failures
                analysis_results['files_with_errors'] += 1
                failure = self._classify_failure(e, f"Dynamic analysis of {file_name}")
                self._record_failure(failure)
                analysis_results['execution_failures'].append(failure.to_dict())
                
                # Store error information for this file
                analysis_results['profiling_results'][file_name] = {
                    'error': str(e),
                    'file_processed': False
                }
         
        # Calculate overall method coverage
        total_methods_executed = sum(len(coverage['methods_executed']) for coverage in execution_coverage.values())
        total_methods_attempted = sum(len(coverage['methods_executed']) + len(coverage['methods_failed']) for coverage in execution_coverage.values())
        
        method_coverage = {
            'scalene_profiling': sum(1 for cov in execution_coverage.values() if 'scalene_profiling' in cov['methods_executed']),
            'viztracer_tracing': sum(1 for cov in execution_coverage.values() if 'viztracer_tracing' in cov['methods_executed']),
            'runtime_trace_execution': sum(1 for cov in execution_coverage.values() if 'runtime_trace_execution' in cov['methods_executed']),
            'memory_profiling': sum(1 for cov in execution_coverage.values() if 'memory_profiling' in cov['methods_executed'])
        }
        
        # Calculate coverage percentages
        if len(execution_coverage) > 0:
            # Create a list of method names to avoid modifying dict during iteration
            methods = list(method_coverage.keys())
            for method in methods:
                method_coverage[method + '_percentage'] = method_coverage[method] / len(execution_coverage)
         
        analysis_results['execution_coverage'] = execution_coverage
        analysis_results['method_coverage'] = method_coverage
        analysis_results['method_coverage_percentage'] = total_methods_executed / total_methods_attempted if total_methods_attempted > 0 else 0.0
        
        # Update failure counts
        analysis_results['failure_count'] = self.failure_count
        analysis_results['issue_count'] = self.issue_count
        
        return analysis_results

# Re-export all classes and enums for backward compatibility
__all__ = ['DynamicAnalyzer', 'DynamicAnalyzerBase', 'ExecutionFailure', 'FailureType', 'FailureSeverity']

# Also export the original base class for any code that might import it directly
DynamicAnalyzerBase = DynamicAnalyzerBase