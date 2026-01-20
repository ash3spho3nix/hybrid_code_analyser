"""
Main DynamicAnalyzer module that combines all functionality from helper modules.
This file maintains the original interface while splitting implementation across smaller files.
"""

from analyzer.dynamic_analyzer_base import DynamicAnalyzer as DynamicAnalyzerBase, ExecutionFailure, FailureType, FailureSeverity
from datetime import datetime
from typing import Dict, Any, List

# Import all the helper classes to make their methods available
from analyzer.dynamic_analyzer_profiling import DynamicAnalyzerProfiling
from analyzer.dynamic_analyzer_execution import DynamicAnalyzerExecution
from analyzer.dynamic_analyzer_safe import DynamicAnalyzerSafe
from analyzer.dynamic_analyzer_helpers import DynamicAnalyzerHelpers

class DynamicAnalyzer(DynamicAnalyzerBase):
    """
    Main DynamicAnalyzer class that combines all functionality.
    This class inherits from the base class and mixes in methods from helper classes.
    """
    def __init__(self):
        # Initialize the base class
        super().__init__()
        
        # Mix in methods from helper classes
        self._mix_in_helper_methods()
    
    def _mix_in_helper_methods(self):
        """Mix in methods from all helper classes"""
        helper_classes = [DynamicAnalyzerProfiling, DynamicAnalyzerExecution, DynamicAnalyzerSafe, DynamicAnalyzerHelpers]
        
        for helper_class in helper_classes:
            for attr_name in dir(helper_class):
                if not attr_name.startswith('__'):
                    attr = getattr(helper_class, attr_name)
                    if callable(attr) and not hasattr(self, attr_name):
                        # Bind the method to this instance
                        bound_method = attr.__get__(self, self.__class__)
                        setattr(self, attr_name, bound_method)

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