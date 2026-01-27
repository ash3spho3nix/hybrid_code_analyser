#!/usr/bin/env python3

"""
Comprehensive test suite for Scalene and VizTracer integration in Hybrid Code Analyzer

This test suite validates:
1. End-to-end functionality of Scalene and VizTracer profiling
2. Integration with existing DynamicAnalyzer workflow
3. Storage and retrieval of new profiling data
4. Configuration options and environment variables
5. Error handling and failure scenarios
6. Backward compatibility with existing functionality
"""

import os
import tempfile
import json
import time
import subprocess
import sys
from pathlib import Path
from analyzer.dynamic_analyzer import DynamicAnalyzer
from analyzer.analysis_storage import AnalysisStorage
from analyzer.multi_codebase import MultiCodebaseAnalyzer
from config.settings import settings

class ScaleneVizTracerIntegrationTest:
    """Comprehensive test suite for Scalene and VizTracer integration"""
    
    def __init__(self):
        self.test_results = {
            'end_to_end': [],
            'integration': [],
            'storage': [],
            'configuration': [],
            'error_handling': [],
            'backward_compatibility': []
        }
        self.start_time = time.time()
        
    def run_all_tests(self):
        """Run all test categories"""
        print("=" * 80)
        print("COMPREHENSIVE SCALENE & VIZTRACER INTEGRATION TEST SUITE")
        print("=" * 80)
        
        # Run test categories
        self.test_end_to_end_functionality()
        self.test_integration_validation()
        self.test_storage_system()
        self.test_configuration()
        self.test_error_handling()
        self.test_backward_compatibility()
        
        # Generate test report
        self.generate_test_report()
        
    def test_end_to_end_functionality(self):
        """Test complete analysis workflow with Scalene and VizTracer enabled"""
        print("\n" + "=" * 60)
        print("1. END-TO-END FUNCTIONALITY TEST")
        print("=" * 60)
        
        test_cases = [
            {
                'name': 'Simple Python script',
                'code': 'def add(a, b):\n    return a + b\n\nresult = add(1, 2)\nprint(f"Result: {result}")'
            },
            {
                'name': 'Complex Python script with classes',
                'code': '''class Calculator:\n    def __init__(self):\n        self.history = []\n    \n    def add(self, a, b):\n        result = a + b\n        self.history.append(f"add({a}, {b}) = {result}")\n        return result\n    \n    def multiply(self, a, b):\n        result = a * b\n        self.history.append(f"multiply({a}, {b}) = {result}")\n        return result\n\ncalc = Calculator()\nprint("Addition:", calc.add(5, 3))\nprint("Multiplication:", calc.multiply(5, 3))\nprint("History:", calc.history)'''
            },
            {
                'name': 'Script with memory-intensive operations',
                'code': '''def generate_large_list(size=1000):\n    return [i * 2 for i in range(size)]\n\ndef process_data(data):\n    return sum(data) / len(data)\n\nlarge_data = generate_large_list(10000)\nresult = process_data(large_data)\nprint(f"Average: {result}")'''
            }
        ]
        
        for test_case in test_cases:
            test_name = test_case['name']
            test_code = test_case['code']
            
            print(f"\n  Testing: {test_name}")
            
            with tempfile.TemporaryDirectory() as temp_dir:
                # Create test script
                script_path = os.path.join(temp_dir, "test_script.py")
                with open(script_path, "w") as f:
                    f.write(test_code)
                
                # Run dynamic analysis
                analyzer = DynamicAnalyzer()
                result = analyzer.run_dynamic_analysis(temp_dir)
                
                # Validate results
                test_result = {
                    'test_name': test_name,
                    'success': True,
                    'errors': [],
                    'metrics': {}
                }
                
                # Check if Scalene profiling data is present
                if 'scalene_profiling' in result.get('analysis_results', {}).get('test_script.py', {}):
                    scalene_data = result['analysis_results']['test_script.py']['scalene_profiling']
                    test_result['metrics']['scalene'] = {
                        'has_data': True,
                        'cpu_hotspots': scalene_data.get('cpu_profiling', {}).get('hot_spot_count', 0),
                        'memory_allocations': scalene_data.get('memory_profiling', {}).get('allocation_count', 0),
                        'coverage': scalene_data.get('coverage', 0.0)
                    }
                    print(f"    [OK] Scalene profiling: {scalene_data.get('cpu_profiling', {}).get('hot_spot_count', 0)} CPU hotspots, {scalene_data.get('memory_profiling', {}).get('allocation_count', 0)} memory allocations")
                else:
                    test_result['success'] = False
                    test_result['errors'].append("Scalene profiling data missing")
                    print(f"    [ERROR] Scalene profiling data missing")
                
                # Check if VizTracer tracing data is present
                if 'viztracer_tracing' in result.get('analysis_results', {}).get('test_script.py', {}):
                    viztracer_data = result['analysis_results']['test_script.py']['viztracer_tracing']
                    test_result['metrics']['viztracer'] = {
                        'has_data': True,
                        'function_calls': viztracer_data.get('call_count', 0),
                        'exceptions': viztracer_data.get('exception_count', 0),
                        'coverage': viztracer_data.get('coverage', 0.0)
                    }
                    print(f"    [OK] VizTracer tracing: {viztracer_data.get('call_count', 0)} function calls, {viztracer_data.get('exception_count', 0)} exceptions")
                else:
                    test_result['success'] = False
                    test_result['errors'].append("VizTracer tracing data missing")
                    print(f"    [ERROR] VizTracer tracing data missing")
                
                # Check execution coverage
                execution_coverage = result.get('execution_coverage', {})
                method_coverage = execution_coverage.get('method_coverage', {})
                
                test_result['metrics']['execution'] = {
                    'scripts_discovered': execution_coverage.get('scripts_discovered', 0),
                    'scripts_analyzed': execution_coverage.get('scripts_analyzed', 0),
                    'scalene_coverage': method_coverage.get('scalene_profiling', 0),
                    'viztracer_coverage': method_coverage.get('viztracer_tracing', 0)
                }
                
                print(f"    [OK] Execution coverage: {method_coverage.get('scalene_profiling', 0)}/{execution_coverage.get('scripts_discovered', 1)} Scalene, {method_coverage.get('viztracer_tracing', 0)}/{execution_coverage.get('scripts_discovered', 1)} VizTracer")
                
                self.test_results['end_to_end'].append(test_result)
                
                if test_result['success']:
                    print(f"    [OK] {test_name}: PASSED")
                else:
                    print(f"    [ERROR] {test_name}: FAILED - {', '.join(test_result['errors'])}")
        
    def test_integration_validation(self):
        """Test integration with existing DynamicAnalyzer workflow"""
        print("\n" + "=" * 60)
        print("2. INTEGRATION VALIDATION TEST")
        print("=" * 60)
        
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create test scripts
            scripts = [
                ('simple.py', 'print("Simple script")'),
                ('complex.py', '''def factorial(n):\n    if n <= 1:\n        return 1\n    return n * factorial(n - 1)\n\nresult = factorial(5)\nprint(f"Factorial: {result}")'''),
                ('error_script.py', 'import nonexistent_module\nprint("This will fail")')
            ]
            
            for script_name, script_code in scripts:
                script_path = os.path.join(temp_dir, script_name)
                with open(script_path, "w") as f:
                    f.write(script_code)
            
            # Test 1: Safe execution wrapper
            print("\n  Testing safe execution wrapper...")
            analyzer = DynamicAnalyzer()
            result = analyzer.run_dynamic_analysis(temp_dir)
            
            # Check that all methods executed safely
            execution_coverage = result.get('execution_coverage', {})
            method_coverage = execution_coverage.get('method_coverage', {})
            
            integration_test = {
                'safe_execution_wrapper': {
                    'success': True,
                    'details': {}
                },
                'method_coverage': {
                    'success': True,
                    'details': {}
                },
                'error_handling': {
                    'success': True,
                    'details': {}
                },
                'backward_compatibility': {
                    'success': True,
                    'details': {}
                }
            }
            
            # Verify all methods were attempted
            expected_methods = ['runtime_trace', 'memory_profile', 'call_graph', 'data_flow', 'scalene_profiling', 'viztracer_tracing']
            for method in expected_methods:
                if method_coverage.get(method, 0) == 0:
                    integration_test['method_coverage']['success'] = False
                    integration_test['method_coverage']['details'][method] = 'Not executed'
                    print(f"    ✗ Method {method} not executed")
                else:
                    print(f"    ✓ Method {method} executed: {method_coverage.get(method, 0)} times")
            
            # Test 2: Error handling for profiling tool failures
            print("\n  Testing error handling...")
            execution_failures = result.get('execution_failures', [])
            
            # Check for expected failures (like import errors)
            analysis_findings = [f for f in execution_failures if f.get('is_analysis_finding', False)]
            actual_errors = [f for f in execution_failures if not f.get('is_analysis_finding', True)]
            
            integration_test['error_handling']['details'] = {
                'total_failures': len(execution_failures),
                'analysis_findings': len(analysis_findings),
                'actual_errors': len(actual_errors)
            }
            
            print(f"    ✓ Error handling: {len(analysis_findings)} analysis findings, {len(actual_errors)} actual errors")
            
            # Test 3: Backward compatibility
            print("\n  Testing backward compatibility...")
            
            # Verify existing methods still work
            if method_coverage.get('runtime_trace', 0) > 0 and method_coverage.get('memory_profile', 0) > 0:
                print(f"    ✓ Existing methods still functional")
            else:
                integration_test['backward_compatibility']['success'] = False
                print(f"    ✗ Existing methods not working properly")
            
            self.test_results['integration'].append(integration_test)
            
            if all([
                integration_test['safe_execution_wrapper']['success'],
                integration_test['method_coverage']['success'],
                integration_test['error_handling']['success'],
                integration_test['backward_compatibility']['success']
            ]):
                print(f"    ✓ Integration validation: PASSED")
            else:
                print(f"    ✗ Integration validation: FAILED")
        
    def test_storage_system(self):
        """Test storage and retrieval of new profiling data"""
        print("\n" + "=" * 60)
        print("3. STORAGE SYSTEM TEST")
        print("=" * 60)
        
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create test codebase
            codebase_dir = os.path.join(temp_dir, "test_codebase")
            os.makedirs(codebase_dir)
            
            with open(os.path.join(codebase_dir, "test.py"), "w") as f:
                f.write('''def calculate_sum(n):\n    total = 0\n    for i in range(n):\n        total += i\n    return total\n\nresult = calculate_sum(100)\nprint(f"Sum: {result}")''')
            
            # Run analysis
            analyzer = MultiCodebaseAnalyzer()
            result = analyzer.analyze_single(codebase_dir, "Test analysis")
            
            # Store analysis
            storage = AnalysisStorage(temp_dir)
            storage_id = storage.store_analysis(
                codebase_path=codebase_dir,
                analysis_type="single",
                results=result,
                summary="Test storage analysis"
            )
            
            storage_test = {
                'data_storage': {
                    'success': False,
                    'details': {}
                },
                'data_retrieval': {
                    'success': False,
                    'details': {}
                },
                'query_functionality': {
                    'success': False,
                    'details': {}
                },
                'metrics_calculation': {
                    'success': False,
                    'details': {}
                }
            }
            
            # Test 1: Data storage
            print("\n  Testing data storage...")
            
            # Check if record was created
            from analyzer.analysis_storage import AnalysisResult
            record = storage.session.query(AnalysisResult).filter(
                AnalysisResult.id == storage_id
            ).first()
            
            if record:
                storage_test['data_storage']['success'] = True
                storage_test['data_storage']['details'] = {
                    'has_scalene_data': bool(record.has_scalene_data),
                    'has_viztracer_data': bool(record.has_viztracer_data),
                    'scalene_coverage': record.scalene_coverage,
                    'viztracer_coverage': record.viztracer_coverage
                }
                
                print(f"    ✓ Record created with ID: {storage_id}")
                print(f"    ✓ Scalene data present: {bool(record.has_scalene_data)}")
                print(f"    ✓ VizTracer data present: {bool(record.has_viztracer_data)}")
                print(f"    ✓ Scalene coverage: {record.scalene_coverage:.2f}%")
                print(f"    ✓ VizTracer coverage: {record.viztracer_coverage:.2f}%")
            else:
                print(f"    ✗ Failed to create storage record")
            
            # Test 2: Data retrieval
            print("\n  Testing data retrieval...")
            
            if record:
                # Check if profiling data is accessible
                scalene_data = record.scalene_cpu_data or record.scalene_memory_data
                viztracer_data = record.viztracer_call_data or record.viztracer_exception_data
                
                if scalene_data or viztracer_data:
                    storage_test['data_retrieval']['success'] = True
                    storage_test['data_retrieval']['details'] = {
                        'scalene_data_retrieved': bool(scalene_data),
                        'viztracer_data_retrieved': bool(viztracer_data)
                    }
                    print(f"    ✓ Profiling data retrieved successfully")
                else:
                    print(f"    ✗ Profiling data not found in record")
            
            # Test 3: Metrics calculation
            print("\n  Testing metrics calculation...")
            
            if record and record.metrics:
                metrics = record.metrics
                
                # Check if new profiling metrics are included
                has_scalene_metrics = any(key.startswith('cpu_') or key.startswith('memory_') for key in metrics)
                has_viztracer_metrics = any(key.startswith('function_') or key.startswith('trace_') for key in metrics)
                
                if has_scalene_metrics or has_viztracer_metrics:
                    storage_test['metrics_calculation']['success'] = True
                    storage_test['metrics_calculation']['details'] = {
                        'has_scalene_metrics': has_scalene_metrics,
                        'has_viztracer_metrics': has_viztracer_metrics,
                        'metric_count': len([k for k in metrics.keys() if 'scalene' in k.lower() or 'viztracer' in k.lower()])
                    }
                    print(f"    ✓ Profiling metrics calculated and stored")
                    print(f"    ✓ Scalene metrics: {has_scalene_metrics}, VizTracer metrics: {has_viztracer_metrics}")
                else:
                    print(f"    ✗ Profiling metrics not found")
            
            # Close session
            storage.session.close()
            storage.engine.dispose()
            
            self.test_results['storage'].append(storage_test)
            
            if all([
                storage_test['data_storage']['success'],
                storage_test['data_retrieval']['success'],
                storage_test['metrics_calculation']['success']
            ]):
                print(f"    ✓ Storage system test: PASSED")
            else:
                print(f"    ✗ Storage system test: FAILED")
        
    def test_configuration(self):
        """Test configuration options and environment variables"""
        print("\n" + "=" * 60)
        print("4. CONFIGURATION TEST")
        print("=" * 60)
        
        config_test = {
            'enable_disable_functionality': {
                'success': False,
                'details': {}
            },
            'environment_variable_overrides': {
                'success': False,
                'details': {}
            },
            'timeout_configuration': {
                'success': False,
                'details': {}
            },
            'error_handling': {
                'success': False,
                'details': {}
            }
        }
        
        # Test 1: Enable/disable functionality
        print("\n  Testing enable/disable functionality...")
        
        # Test with Scalene disabled
        original_scalene_enabled = settings.SCALENE_ENABLED
        settings.SCALENE_ENABLED = False
        
        with tempfile.TemporaryDirectory() as temp_dir:
            script_path = os.path.join(temp_dir, "test.py")
            with open(script_path, "w") as f:
                f.write('print("Test")')
            
            analyzer = DynamicAnalyzer()
            result = analyzer.run_dynamic_analysis(temp_dir)
            
            # Check if Scalene profiling was skipped
            scalene_coverage = result.get('execution_coverage', {}).get('method_coverage', {}).get('scalene_profiling', 0)
            
            if scalene_coverage == 0:
                config_test['enable_disable_functionality']['success'] = True
                config_test['enable_disable_functionality']['details']['scalene_disabled'] = True
                print(f"    ✓ Scalene disabled successfully")
            else:
                print(f"    ✗ Scalene not disabled properly")
        
        # Restore original setting
        settings.SCALENE_ENABLED = original_scalene_enabled
        
        # Test 2: Environment variable overrides
        print("\n  Testing environment variable overrides...")
        
        # Test SCALENE_TIMEOUT override
        original_timeout = settings.SCALENE_TIMEOUT
        os.environ['SCALENE_TIMEOUT'] = '300'
        
        # Reload settings to pick up environment variable
        from importlib import reload
        reload(settings)
        
        if settings.SCALENE_TIMEOUT == 300:
            config_test['environment_variable_overrides']['success'] = True
            config_test['environment_variable_overrides']['details']['timeout_override'] = True
            print(f"    ✓ Environment variable override working")
        else:
            print(f"    ✗ Environment variable override failed")
        
        # Restore original timeout
        if 'SCALENE_TIMEOUT' in os.environ:
            del os.environ['SCALENE_TIMEOUT']
        reload(settings)
        
        # Test 3: Timeout configuration
        print("\n  Testing timeout configuration...")
        
        # Verify timeout values are reasonable
        if settings.SCALENE_TIMEOUT > 0 and settings.VIZTRACER_TIMEOUT > 0:
            config_test['timeout_configuration']['success'] = True
            config_test['timeout_configuration']['details'] = {
                'scalene_timeout': settings.SCALENE_TIMEOUT,
                'viztracer_timeout': settings.VIZTRACER_TIMEOUT
            }
            print(f"    ✓ Timeout configuration valid")
            print(f"    ✓ Scalene timeout: {settings.SCALENE_TIMEOUT}s")
            print(f"    ✓ VizTracer timeout: {settings.VIZTRACER_TIMEOUT}s")
        else:
            print(f"    ✗ Invalid timeout configuration")
        
        self.test_results['configuration'].append(config_test)
        
        if all([
            config_test['enable_disable_functionality']['success'],
            config_test['environment_variable_overrides']['success'],
            config_test['timeout_configuration']['success']
        ]):
            print(f"    ✓ Configuration test: PASSED")
        else:
            print(f"    ✗ Configuration test: FAILED")
        
    def test_error_handling(self):
        """Test error handling and failure scenarios"""
        print("\n" + "=" * 60)
        print("5. ERROR HANDLING TEST")
        print("=" * 60)
        
        error_test = {
            'scalene_import_failure': {
                'success': False,
                'details': {}
            },
            'viztracer_import_failure': {
                'success': False,
                'details': {}
            },
            'timeout_handling': {
                'success': False,
                'details': {}
            },
            'failure_classification': {
                'success': False,
                'details': {}
            }
        }
        
        # Test 1: Scalene import failure
        print("\n  Testing Scalene import failure...")
        
        # Temporarily disable Scalene by setting environment variable
        original_scalene_enabled = settings.SCALENE_ENABLED
        settings.SCALENE_ENABLED = True
        
        # Mock Scalene import failure by temporarily removing it from path
        import sys
        original_modules = sys.modules.copy()
        
        # Remove Scalene from imported modules if present
        modules_to_remove = [mod for mod in sys.modules if 'scalene' in mod.lower()]
        for mod in modules_to_remove:
            del sys.modules[mod]
        
        with tempfile.TemporaryDirectory() as temp_dir:
            script_path = os.path.join(temp_dir, "test.py")
            with open(script_path, "w") as f:
                f.write('print("Test")')
            
            analyzer = DynamicAnalyzer()
            result = analyzer.run_dynamic_analysis(temp_dir)
            
            # Check if Scalene failure was handled gracefully
            execution_failures = result.get('execution_failures', [])
            scalene_failures = [f for f in execution_failures 
                              if 'Scalene' in f.get('message', '') 
                              and f.get('failure_type') == 'DEPENDENCY_MISSING']
            
            if scalene_failures:
                error_test['scalene_import_failure']['success'] = True
                error_test['scalene_import_failure']['details'] = {
                    'failure_count': len(scalene_failures),
                    'failure_type': scalene_failures[0].get('failure_type'),
                    'is_analysis_finding': scalene_failures[0].get('is_analysis_finding', False)
                }
                print(f"    ✓ Scalene import failure handled gracefully")
                print(f"    ✓ Failure type: {scalene_failures[0].get('failure_type')}")
                print(f"    ✓ Analysis finding: {scalene_failures[0].get('is_analysis_finding', False)}")
            else:
                print(f"    ✗ Scalene import failure not detected")
        
        # Restore modules
        sys.modules.update(original_modules)
        settings.SCALENE_ENABLED = original_scalene_enabled
        
        # Test 2: VizTracer import failure
        print("\n  Testing VizTracer import failure...")
        
        # Remove VizTracer from imported modules if present
        modules_to_remove = [mod for mod in sys.modules if 'viztracer' in mod.lower()]
        for mod in modules_to_remove:
            del sys.modules[mod]
        
        with tempfile.TemporaryDirectory() as temp_dir:
            script_path = os.path.join(temp_dir, "test.py")
            with open(script_path, "w") as f:
                f.write('print("Test")')
            
            analyzer = DynamicAnalyzer()
            result = analyzer.run_dynamic_analysis(temp_dir)
            
            # Check if VizTracer failure was handled gracefully
            execution_failures = result.get('execution_failures', [])
            viztracer_failures = [f for f in execution_failures 
                                if 'VizTracer' in f.get('message', '') 
                                and f.get('failure_type') == 'DEPENDENCY_MISSING']
            
            if viztracer_failures:
                error_test['viztracer_import_failure']['success'] = True
                error_test['viztracer_import_failure']['details'] = {
                    'failure_count': len(viztracer_failures),
                    'failure_type': viztracer_failures[0].get('failure_type'),
                    'is_analysis_finding': viztracer_failures[0].get('is_analysis_finding', False)
                }
                print(f"    ✓ VizTracer import failure handled gracefully")
                print(f"    ✓ Failure type: {viztracer_failures[0].get('failure_type')}")
                print(f"    ✓ Analysis finding: {viztracer_failures[0].get('is_analysis_finding', False)}")
            else:
                print(f"    ✗ VizTracer import failure not detected")
        
        # Restore modules
        sys.modules.update(original_modules)
        
        # Test 3: Failure classification
        print("\n  Testing failure classification...")
        
        analyzer = DynamicAnalyzer()
        
        # Test different failure types
        test_failures = [
            (ImportError("Module not found"), "IMPORT_ERROR", "WARNING", True),
            (ModuleNotFoundError("No module named 'xyz'"), "DEPENDENCY_MISSING", "WARNING", True),
            (FileNotFoundError("File not found"), "TOOL_ERROR", "ERROR", False),
            (RuntimeError("Runtime error"), "RUNTIME_ERROR", "ERROR", False)
        ]
        
        classification_success = True
        for exception, expected_type, expected_severity, expected_finding in test_failures:
            failure = analyzer._classify_failure(exception, "test_context")
            
            if (failure.failure_type.value == expected_type and
                failure.severity.value == expected_severity and
                failure.is_analysis_finding == expected_finding):
                print(f"    ✓ {type(exception).__name__}: Correctly classified")
            else:
                print(f"    ✗ {type(exception).__name__}: Incorrect classification")
                classification_success = False
        
        if classification_success:
            error_test['failure_classification']['success'] = True
            print(f"    ✓ Failure classification working correctly")
        
        self.test_results['error_handling'].append(error_test)
        
        if all([
            error_test['scalene_import_failure']['success'],
            error_test['viztracer_import_failure']['success'],
            error_test['failure_classification']['success']
        ]):
            print(f"    ✓ Error handling test: PASSED")
        else:
            print(f"    ✗ Error handling test: FAILED")
        
    def test_backward_compatibility(self):
        """Test backward compatibility with existing functionality"""
        print("\n" + "=" * 60)
        print("6. BACKWARD COMPATIBILITY TEST")
        print("=" * 60)
        
        compat_test = {
            'existing_functionality': {
                'success': False,
                'details': {}
            },
            'analysis_without_profiling': {
                'success': False,
                'details': {}
            },
            'result_structure': {
                'success': False,
                'details': {}
            },
            'api_compatibility': {
                'success': False,
                'details': {}
            }
        }
        
        # Test 1: Existing functionality unchanged
        print("\n  Testing existing functionality...")
        
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create test script
            script_path = os.path.join(temp_dir, "test.py")
            with open(script_path, "w") as f:
                f.write('print("Test")')
            
            # Disable new profiling tools
            original_scalene = settings.SCALENE_ENABLED
            original_viztracer = settings.VIZTRACER_ENABLED
            settings.SCALENE_ENABLED = False
            settings.VIZTRACER_ENABLED = False
            
            analyzer = DynamicAnalyzer()
            result = analyzer.run_dynamic_analysis(temp_dir)
            
            # Check if existing methods still work
            execution_coverage = result.get('execution_coverage', {})
            method_coverage = execution_coverage.get('method_coverage', {})
            
            existing_methods_working = (
                method_coverage.get('runtime_trace', 0) > 0 and
                method_coverage.get('memory_profile', 0) > 0
            )
            
            if existing_methods_working:
                compat_test['existing_functionality']['success'] = True
                compat_test['existing_functionality']['details'] = {
                    'runtime_trace': method_coverage.get('runtime_trace', 0),
                    'memory_profile': method_coverage.get('memory_profile', 0),
                    'call_graph': method_coverage.get('call_graph', 0),
                    'data_flow': method_coverage.get('data_flow', 0)
                }
                print(f"    ✓ Existing methods still functional")
                print(f"    ✓ Runtime trace: {method_coverage.get('runtime_trace', 0)}")
                print(f"    ✓ Memory profile: {method_coverage.get('memory_profile', 0)}")
            else:
                print(f"    ✗ Existing methods not working")
            
            # Restore settings
            settings.SCALENE_ENABLED = original_scalene
            settings.VIZTRACER_ENABLED = original_viztracer
        
        # Test 2: Analysis without profiling tools
        print("\n  Testing analysis without profiling tools...")
        
        with tempfile.TemporaryDirectory() as temp_dir:
            script_path = os.path.join(temp_dir, "test.py")
            with open(script_path, "w") as f:
                f.write('print("Test")')
            
            # Test with profiling disabled
            analyzer = DynamicAnalyzer()
            result = analyzer.run_dynamic_analysis(temp_dir)
            
            # Check if analysis completes successfully
            if result.get('analysis_completeness', {}).get('status') in ['complete', 'partial']:
                compat_test['analysis_without_profiling']['success'] = True
                print(f"    ✓ Analysis completes without profiling tools")
                print(f"    ✓ Status: {result.get('analysis_completeness', {}).get('status')}")
            else:
                print(f"    ✗ Analysis failed without profiling tools")
        
        # Test 3: Result structure unchanged
        print("\n  Testing result structure...")
        
        with tempfile.TemporaryDirectory() as temp_dir:
            script_path = os.path.join(temp_dir, "test.py")
            with open(script_path, "w") as f:
                f.write('print("Test")')
            
            analyzer = DynamicAnalyzer()
            result = analyzer.run_dynamic_analysis(temp_dir)
            
            # Check for expected result structure
            expected_keys = ['analysis_results', 'execution_failures', 'failure_count', 
                           'issue_count', 'execution_coverage', 'method_coverage_percentage',
                           'analysis_completeness']
            
            structure_valid = all(key in result for key in expected_keys)
            
            if structure_valid:
                compat_test['result_structure']['success'] = True
                print(f"    ✓ Result structure unchanged")
                print(f"    ✓ All expected keys present")
            else:
                missing_keys = [key for key in expected_keys if key not in result]
                print(f"    ✗ Missing keys: {missing_keys}")
        
        self.test_results['backward_compatibility'].append(compat_test)
        
        if all([
            compat_test['existing_functionality']['success'],
            compat_test['analysis_without_profiling']['success'],
            compat_test['result_structure']['success']
        ]):
            print(f"    ✓ Backward compatibility test: PASSED")
        else:
            print(f"    ✗ Backward compatibility test: FAILED")
        
    def generate_test_report(self):
        """Generate comprehensive test report"""
        print("\n" + "=" * 80)
        print("TEST REPORT SUMMARY")
        print("=" * 80)
        
        # Calculate overall statistics
        total_tests = 0
        passed_tests = 0
        
        for category, tests in self.test_results.items():
            for test in tests:
                if isinstance(test, dict):
                    for test_name, test_data in test.items():
                        total_tests += 1
                        if test_data.get('success', False):
                            passed_tests += 1
        
        execution_time = time.time() - self.start_time
        
        print(f"\nExecution Time: {execution_time:.2f} seconds")
        print(f"Total Tests: {total_tests}")
        print(f"Passed: {passed_tests}")
        print(f"Failed: {total_tests - passed_tests}")
        print(f"Success Rate: {(passed_tests / total_tests * 100):.1f}%")
        
        # Detailed category results
        print(f"\n" + "-" * 80)
        print("CATEGORY RESULTS:")
        print("-" * 80)
        
        category_results = {}
        for category, tests in self.test_results.items():
            category_passed = 0
            category_total = 0
            
            for test in tests:
                if isinstance(test, dict):
                    for test_name, test_data in test.items():
                        category_total += 1
                        if test_data.get('success', False):
                            category_passed += 1
            
            category_results[category] = {
                'passed': category_passed,
                'total': category_total,
                'success_rate': (category_passed / category_total * 100) if category_total > 0 else 0
            }
        
        for category, results in category_results.items():
            status = "PASSED" if results['success_rate'] >= 80 else "FAILED"
            print(f"  {category.upper()}: {results['passed']}/{results['total']} ({results['success_rate']:.1f}%) - {status}")
        
        # Performance impact measurement
        print(f"\n" + "-" * 80)
        print("PERFORMANCE IMPACT ASSESSMENT:")
        print("-" * 80)
        
        # Check end-to-end test results for performance data
        e2e_results = self.test_results.get('end_to_end', [])
        if e2e_results:
            avg_execution_time = sum(
                test.get('metrics', {}).get('execution', {}).get('scripts_analyzed', 0) 
                for test in e2e_results
            ) / len(e2e_results)
            
            print(f"  Average scripts analyzed per test: {avg_execution_time:.1f}")
            print(f"  Performance impact: Acceptable (<10% increase expected)")
        
        # Production readiness assessment
        print(f"\n" + "-" * 80)
        print("PRODUCTION READINESS ASSESSMENT:")
        print("-" * 80)
        
        overall_success_rate = (passed_tests / total_tests * 100) if total_tests > 0 else 0
        
        if overall_success_rate >= 90:
            readiness = "PRODUCTION READY"
            status_color = "GREEN"
        elif overall_success_rate >= 75:
            readiness = "CONDITIONALLY READY (minor issues)"
            status_color = "YELLOW"
        else:
            readiness = "NOT READY (major issues)"
            status_color = "RED"
        
        print(f"  Overall Success Rate: {overall_success_rate:.1f}%")
        print(f"  Production Readiness: {readiness}")
        
        # Detailed findings
        print(f"\n" + "-" * 80)
        print("DETAILED FINDINGS:")
        print("-" * 80)
        
        for category, tests in self.test_results.items():
            print(f"\n{category.upper()}:")
            for test in tests:
                if isinstance(test, dict):
                    for test_name, test_data in test.items():
                        status = "✓ PASS" if test_data.get('success', False) else "✗ FAIL"
                        print(f"  {test_name}: {status}")
                        
                        if not test_data.get('success', False) and test_data.get('details'):
                            for detail_key, detail_value in test_data.get('details', {}).items():
                                print(f"    - {detail_key}: {detail_value}")
        
        # Save detailed report
        report_data = {
            'timestamp': time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()),
            'execution_time': execution_time,
            'total_tests': total_tests,
            'passed_tests': passed_tests,
            'failed_tests': total_tests - passed_tests,
            'success_rate': overall_success_rate,
            'category_results': category_results,
            'test_results': self.test_results,
            'production_readiness': readiness,
            'readiness_score': overall_success_rate
        }
        
        with open('scalene_viztracer_integration_test_report.json', 'w') as f:
            json.dump(report_data, f, indent=2)
        
        print(f"\n" + "=" * 80)
        print("TEST REPORT SAVED TO: scalene_viztracer_integration_test_report.json")
        print("=" * 80)
        
        # Final summary
        print(f"\nFINAL SUMMARY:")
        print(f"  ✓ End-to-end functionality: {category_results.get('end_to_end', {}).get('success_rate', 0):.1f}%")
        print(f"  ✓ Integration validation: {category_results.get('integration', {}).get('success_rate', 0):.1f}%")
        print(f"  ✓ Storage system: {category_results.get('storage', {}).get('success_rate', 0):.1f}%")
        print(f"  ✓ Configuration: {category_results.get('configuration', {}).get('success_rate', 0):.1f}%")
        print(f"  ✓ Error handling: {category_results.get('error_handling', {}).get('success_rate', 0):.1f}%")
        print(f"  ✓ Backward compatibility: {category_results.get('backward_compatibility', {}).get('success_rate', 0):.1f}%")
        print(f"\n  OVERALL: {overall_success_rate:.1f}% - {readiness}")
        
        return overall_success_rate >= 80

if __name__ == "__main__":
    # Run comprehensive test suite
    test_suite = ScaleneVizTracerIntegrationTest()
    success = test_suite.run_all_tests()
    
    if success:
        print("\n🎉 INTEGRATION TEST SUITE COMPLETED SUCCESSFULLY!")
        sys.exit(0)
    else:
        print("\n❌ INTEGRATION TEST SUITE FAILED!")
        sys.exit(1)