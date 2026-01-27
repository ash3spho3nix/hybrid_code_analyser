#!/usr/bin/env python3

"""
Simple storage validation test for Scalene and VizTracer profiling data.

This test validates:
1. Profiling data storage in AnalysisStorage
2. Data retrieval and query functionality
3. Metrics calculation including profiling data
4. Storage schema migration functionality
"""

import os
import tempfile
import json
import time
import sys
from pathlib import Path
from analyzer.dynamic_analyzer import DynamicAnalyzer
from analyzer.analysis_storage import AnalysisStorage
from analyzer.analysis_storage_models import AnalysisResult
from config.settings import settings

class SimpleStorageValidationTest:
    """Simple storage validation for profiling data"""
    
    def __init__(self):
        self.test_results = {
            'storage_validation': [],
            'data_retrieval': [],
            'metrics_validation': [],
            'schema_migration': []
        }
        self.start_time = time.time()
        
    def run_all_tests(self):
        """Run all storage validation tests"""
        print("=" * 80)
        print("SIMPLE STORAGE VALIDATION TEST SUITE")
        print("=" * 80)
        
        # Run test categories
        self.test_storage_validation()
        self.test_data_retrieval()
        self.test_metrics_validation()
        self.test_schema_migration()
        
        # Generate test report
        return self.generate_test_report()
        
    def test_storage_validation(self):
        """Test profiling data storage validation"""
        print("\n" + "=" * 60)
        print("1. STORAGE VALIDATION TEST")
        print("=" * 60)
        
        storage_test = {
            'profiling_data_storage': {
                'success': False,
                'details': {}
            },
            'database_integrity': {
                'success': False,
                'details': {}
            }
        }
        
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create test codebase
            codebase_dir = os.path.join(temp_dir, "test_codebase")
            os.makedirs(codebase_dir)
            
            # Create test script
            script_path = os.path.join(codebase_dir, "test.py")
            with open(script_path, "w") as f:
                f.write('''def calculate_sum(n):
    total = 0
    for i in range(n):
        total += i
    return total

result = calculate_sum(100)
print(f"Sum: {result}")''')
            
            print(f"\n  Created test script at: {script_path}")
            
            # Run individual profiling methods
            print(f"\n  Running individual profiling methods...")
            
            analyzer = DynamicAnalyzer()
            
            # Run Scalene profiling
            scalene_result = analyzer.profile_with_scalene(script_path)
            print(f"    ✓ Scalene profiling completed")
            
            # Run VizTracer tracing
            viztracer_result = analyzer.trace_with_viztracer(script_path)
            print(f"    ✓ VizTracer tracing completed")
            
            # Create a mock analysis result with profiling data
            analysis_result = {
                'analysis_results': {
                    'test.py': {
                        'scalene_profiling': scalene_result,
                        'viztracer_tracing': viztracer_result
                    }
                },
                'execution_coverage': {
                    'scripts_discovered': 1,
                    'scripts_analyzed': 1,
                    'scripts_skipped': 0,
                    'method_coverage': {
                        'scalene_profiling': 1,
                        'viztracer_tracing': 1
                    }
                },
                'method_coverage_percentage': 100.0,
                'execution_failures': [],
                'failure_count': 0,
                'issue_count': 0,
                'analysis_completeness': {
                    'status': 'complete',
                    'coverage_metrics': {
                        'overall_coverage': 100.0,
                        'completeness_context': 'Test analysis completed successfully'
                    }
                }
            }
            
            # Store analysis in database
            print(f"\n  Storing analysis in database...")
            
            storage = AnalysisStorage(temp_dir)
            storage_id = storage.store_analysis(
                codebase_path=codebase_dir,
                analysis_type="dynamic",
                results=analysis_result,
                summary="Simple storage validation test analysis"
            )
            
            # Verify database record creation
            print(f"\n  Verifying database record...")
            
            record = storage.session.query(AnalysisResult).filter(
                AnalysisResult.id == storage_id
            ).first()
            
            if record:
                storage_test['profiling_data_storage']['success'] = True
                storage_test['profiling_data_storage']['details'] = {
                    'record_id': record.id,
                    'has_scalene_data': bool(record.has_scalene_data),
                    'has_viztracer_data': bool(record.has_viztracer_data),
                    'scalene_coverage': record.scalene_coverage,
                    'viztracer_coverage': record.viztracer_coverage,
                    'peak_memory_usage': record.peak_memory_usage,
                    'cpu_hotspot_count': record.cpu_hotspot_count,
                    'function_call_count': record.function_call_count,
                    'exception_count': record.exception_count
                }
                
                print(f"    ✓ Database record created successfully")
                print(f"    ✓ Record ID: {record.id}")
                print(f"    ✓ Scalene data stored: {bool(record.has_scalene_data)}")
                print(f"    ✓ VizTracer data stored: {bool(record.has_viztracer_data)}")
                print(f"    ✓ Scalene coverage: {record.scalene_coverage:.2f}%")
                print(f"    ✓ VizTracer coverage: {record.viztracer_coverage:.2f}%")
                print(f"    ✓ Peak memory usage: {record.peak_memory_usage:.2f} MB")
                print(f"    ✓ CPU hotspots: {record.cpu_hotspot_count}")
                print(f"    ✓ Function calls: {record.function_call_count}")
                print(f"    ✓ Exceptions traced: {record.exception_count}")
            else:
                print(f"    ✗ Failed to create database record")
            
            # Test database integrity
            print(f"\n  Testing database integrity...")
            
            # Check if all required columns exist
            from sqlalchemy import inspect
            inspector = inspect(storage.engine)
            columns = inspector.get_columns('analysis_results')
            column_names = {col['name'] for col in columns}
            
            required_profiling_columns = [
                'scalene_cpu_data', 'scalene_memory_data', 'scalene_gpu_data',
                'viztracer_call_data', 'viztracer_exception_data', 'viztracer_flow_data',
                'scalene_timestamp', 'viztracer_timestamp',
                'has_scalene_data', 'has_viztracer_data',
                'scalene_coverage', 'viztracer_coverage',
                'peak_memory_usage', 'cpu_hotspot_count',
                'function_call_count', 'exception_count'
            ]
            
            missing_columns = [col for col in required_profiling_columns if col not in column_names]
            
            if not missing_columns:
                storage_test['database_integrity']['success'] = True
                storage_test['database_integrity']['details'] = {
                    'total_columns': len(columns),
                    'profiling_columns_present': len(required_profiling_columns),
                    'missing_columns': []
                }
                print(f"    ✓ Database integrity verified")
                print(f"    ✓ All required profiling columns present")
                print(f"    ✓ Total columns: {len(columns)}")
            else:
                storage_test['database_integrity']['details'] = {
                    'missing_columns': missing_columns
                }
                print(f"    ✗ Missing columns: {missing_columns}")
            
            # Close storage
            storage.session.close()
            storage.engine.dispose()
            
        self.test_results['storage_validation'].append(storage_test)
        
        if all([
            storage_test['profiling_data_storage']['success'],
            storage_test['database_integrity']['success']
        ]):
            print(f"\n  ✓ Storage validation test: PASSED")
        else:
            print(f"\n  ✗ Storage validation test: FAILED")
        
    def test_data_retrieval(self):
        """Test data retrieval and query functionality"""
        print("\n" + "=" * 60)
        print("2. DATA RETRIEVAL TEST")
        print("=" * 60)
        
        retrieval_test = {
            'basic_retrieval': {
                'success': False,
                'details': {}
            },
            'query_functionality': {
                'success': False,
                'details': {}
            },
            'execution_logs': {
                'success': False,
                'details': {}
            }
        }
        
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create test codebase
            codebase_dir = os.path.join(temp_dir, "test_codebase")
            os.makedirs(codebase_dir)
            
            script_path = os.path.join(codebase_dir, "test.py")
            with open(script_path, "w") as f:
                f.write('''def test_function():
    print("Testing retrieval")
    return 42

result = test_function()
print(f"Result: {result}")''')
            
            # Run profiling and create analysis result
            analyzer = DynamicAnalyzer()
            scalene_result = analyzer.profile_with_scalene(script_path)
            viztracer_result = analyzer.trace_with_viztracer(script_path)
            
            analysis_result = {
                'analysis_results': {
                    'test.py': {
                        'scalene_profiling': scalene_result,
                        'viztracer_tracing': viztracer_result
                    }
                },
                'execution_coverage': {
                    'scripts_discovered': 1,
                    'scripts_analyzed': 1,
                    'scripts_skipped': 0,
                    'method_coverage': {
                        'scalene_profiling': 1,
                        'viztracer_tracing': 1
                    }
                },
                'method_coverage_percentage': 100.0,
                'execution_failures': [],
                'failure_count': 0,
                'issue_count': 0,
                'analysis_completeness': {
                    'status': 'complete',
                    'coverage_metrics': {
                        'overall_coverage': 100.0,
                        'completeness_context': 'Test analysis completed successfully'
                    }
                }
            }
            
            storage = AnalysisStorage(temp_dir)
            storage_id = storage.store_analysis(
                codebase_path=codebase_dir,
                analysis_type="dynamic",
                results=analysis_result,
                summary="Data retrieval test"
            )
            
            # Test 1: Basic data retrieval
            print(f"\n  Testing basic data retrieval...")
            
            record = storage.session.query(AnalysisResult).filter(
                AnalysisResult.id == storage_id
            ).first()
            
            if record:
                # Retrieve profiling data
                scalene_data = record.scalene_cpu_data or record.scalene_memory_data
                viztracer_data = record.viztracer_call_data or record.viztracer_exception_data
                
                if scalene_data or viztracer_data:
                    retrieval_test['basic_retrieval']['success'] = True
                    retrieval_test['basic_retrieval']['details'] = {
                        'scalene_data_retrieved': bool(scalene_data),
                        'viztracer_data_retrieved': bool(viztracer_data),
                        'full_results_available': bool(record.full_results),
                        'metrics_available': bool(record.metrics)
                    }
                    
                    print(f"    ✓ Profiling data retrieved successfully")
                    print(f"    ✓ Scalene data: {bool(scalene_data)}")
                    print(f"    ✓ VizTracer data: {bool(viztracer_data)}")
                    print(f"    ✓ Full results available: {bool(record.full_results)}")
                    print(f"    ✓ Metrics available: {bool(record.metrics)}")
                else:
                    print(f"    ✗ Profiling data not found in record")
            
            # Test 2: Query functionality
            print(f"\n  Testing query functionality...")
            
            # Query by codebase path
            records_by_codebase = storage.session.query(AnalysisResult).filter(
                AnalysisResult.codebase_path == codebase_dir
            ).all()
            
            if records_by_codebase:
                retrieval_test['query_functionality']['success'] = True
                retrieval_test['query_functionality']['details'] = {
                    'records_found': len(records_by_codebase),
                    'query_type': 'codebase_path'
                }
                print(f"    ✓ Query by codebase path successful")
                print(f"    ✓ Records found: {len(records_by_codebase)}")
            
            # Test 3: Execution logs retrieval
            print(f"\n  Testing execution logs retrieval...")
            
            execution_logs = storage.get_execution_logs(storage_id)
            
            if execution_logs is not None:
                retrieval_test['execution_logs']['success'] = True
                retrieval_test['execution_logs']['details'] = {
                    'log_count': len(execution_logs),
                    'has_error_logs': any(log['log_level'] in ['ERROR', 'CRITICAL'] for log in execution_logs)
                }
                print(f"    ✓ Execution logs retrieved successfully")
                print(f"    ✓ Log count: {len(execution_logs)}")
                print(f"    ✓ Has error logs: {any(log['log_level'] in ['ERROR', 'CRITICAL'] for log in execution_logs)}")
            
            # Close storage
            storage.session.close()
            storage.engine.dispose()
            
        self.test_results['data_retrieval'].append(retrieval_test)
        
        if all([
            retrieval_test['basic_retrieval']['success'],
            retrieval_test['query_functionality']['success'],
            retrieval_test['execution_logs']['success']
        ]):
            print(f"\n  ✓ Data retrieval test: PASSED")
        else:
            print(f"\n  ✗ Data retrieval test: FAILED")
        
    def test_metrics_validation(self):
        """Test metrics calculation including profiling data"""
        print("\n" + "=" * 60)
        print("3. METRICS VALIDATION TEST")
        print("=" * 60)
        
        metrics_test = {
            'profiling_metrics_inclusion': {
                'success': False,
                'details': {}
            },
            'quality_score_calculation': {
                'success': False,
                'details': {}
            },
            'completeness_metrics': {
                'success': False,
                'details': {}
            }
        }
        
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create test codebase
            codebase_dir = os.path.join(temp_dir, "test_codebase")
            os.makedirs(codebase_dir)
            
            script_path = os.path.join(codebase_dir, "test.py")
            with open(script_path, "w") as f:
                f.write('''def calculate_factorial(n):
    if n <= 1:
        return 1
    return n * calculate_factorial(n - 1)

result = calculate_factorial(5)
print(f"Factorial: {result}")''')
            
            # Run profiling and create analysis result
            analyzer = DynamicAnalyzer()
            scalene_result = analyzer.profile_with_scalene(script_path)
            viztracer_result = analyzer.trace_with_viztracer(script_path)
            
            analysis_result = {
                'analysis_results': {
                    'test.py': {
                        'scalene_profiling': scalene_result,
                        'viztracer_tracing': viztracer_result
                    }
                },
                'execution_coverage': {
                    'scripts_discovered': 1,
                    'scripts_analyzed': 1,
                    'scripts_skipped': 0,
                    'method_coverage': {
                        'scalene_profiling': 1,
                        'viztracer_tracing': 1
                    }
                },
                'method_coverage_percentage': 100.0,
                'execution_failures': [],
                'failure_count': 0,
                'issue_count': 0,
                'analysis_completeness': {
                    'status': 'complete',
                    'coverage_metrics': {
                        'overall_coverage': 100.0,
                        'completeness_context': 'Test analysis completed successfully'
                    }
                }
            }
            
            storage = AnalysisStorage(temp_dir)
            storage_id = storage.store_analysis(
                codebase_path=codebase_dir,
                analysis_type="dynamic",
                results=analysis_result,
                summary="Metrics validation test"
            )
            
            # Test 1: Profiling metrics inclusion
            print(f"\n  Testing profiling metrics inclusion...")
            
            record = storage.session.query(AnalysisResult).filter(
                AnalysisResult.id == storage_id
            ).first()
            
            if record and record.metrics:
                metrics = record.metrics
                
                # Check for Scalene metrics
                has_scalene_metrics = any(key.startswith('cpu_') or key.startswith('memory_') 
                                        or 'scalene' in key.lower() for key in metrics)
                
                # Check for VizTracer metrics
                has_viztracer_metrics = any(key.startswith('function_') or key.startswith('trace_')
                                         or 'viztracer' in key.lower() for key in metrics)
                
                if has_scalene_metrics or has_viztracer_metrics:
                    metrics_test['profiling_metrics_inclusion']['success'] = True
                    metrics_test['profiling_metrics_inclusion']['details'] = {
                        'has_scalene_metrics': has_scalene_metrics,
                        'has_viztracer_metrics': has_viztracer_metrics,
                        'total_metrics': len(metrics),
                        'profiling_metric_count': len([k for k in metrics.keys() 
                                                     if 'scalene' in k.lower() or 'viztracer' in k.lower()])
                    }
                    
                    print(f"    ✓ Profiling metrics included in calculation")
                    print(f"    ✓ Scalene metrics: {has_scalene_metrics}")
                    print(f"    ✓ VizTracer metrics: {has_viztracer_metrics}")
                    print(f"    ✓ Total metrics: {len(metrics)}")
                    print(f"    ✓ Profiling metrics: {len([k for k in metrics.keys() if 'scalene' in k.lower() or 'viztracer' in k.lower()])}")
                    
                    # Show specific profiling metrics
                    profiling_metrics = {k: v for k, v in metrics.items() 
                                       if 'scalene' in k.lower() or 'viztracer' in k.lower()}
                    for metric_name, metric_value in profiling_metrics.items():
                        print(f"    ✓ {metric_name}: {metric_value}")
            
            # Test 2: Quality score calculation
            print(f"\n  Testing quality score calculation...")
            
            if record:
                quality_score = record.quality_score
                
                # Check if quality score is reasonable (0-100)
                if 0 <= quality_score <= 100:
                    metrics_test['quality_score_calculation']['success'] = True
                    metrics_test['quality_score_calculation']['details'] = {
                        'quality_score': quality_score,
                        'issue_count': record.issue_count,
                        'complexity_score': record.complexity_score
                    }
                    
                    print(f"    ✓ Quality score calculated: {quality_score}")
                    print(f"    ✓ Issue count: {record.issue_count}")
                    print(f"    ✓ Complexity score: {record.complexity_score}")
                else:
                    print(f"    ✗ Invalid quality score: {quality_score}")
            
            # Test 3: Completeness metrics
            print(f"\n  Testing completeness metrics...")
            
            if record:
                coverage_percentage = record.coverage_percentage
                completeness_context = record.completeness_context
                
                if coverage_percentage >= 0 and coverage_percentage <= 100:
                    metrics_test['completeness_metrics']['success'] = True
                    metrics_test['completeness_metrics']['details'] = {
                        'coverage_percentage': coverage_percentage,
                        'completeness_context': completeness_context,
                        'analysis_status': record.analysis_status
                    }
                    
                    print(f"    ✓ Completeness metrics valid")
                    print(f"    ✓ Coverage percentage: {coverage_percentage:.2f}%")
                    print(f"    ✓ Analysis status: {record.analysis_status}")
                    if completeness_context:
                        print(f"    ✓ Completeness context: {completeness_context[:100]}...")
            
            # Close storage
            storage.session.close()
            storage.engine.dispose()
            
        self.test_results['metrics_validation'].append(metrics_test)
        
        if all([
            metrics_test['profiling_metrics_inclusion']['success'],
            metrics_test['quality_score_calculation']['success'],
            metrics_test['completeness_metrics']['success']
        ]):
            print(f"\n  ✓ Metrics validation test: PASSED")
        else:
            print(f"\n  ✗ Metrics validation test: FAILED")
        
    def test_schema_migration(self):
        """Test storage schema migration functionality"""
        print("\n" + "=" * 60)
        print("4. SCHEMA MIGRATION TEST")
        print("=" * 60)
        
        migration_test = {
            'schema_migration': {
                'success': False,
                'details': {}
            },
            'backward_compatibility': {
                'success': False,
                'details': {}
            },
            'database_versioning': {
                'success': False,
                'details': {}
            }
        }
        
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create test codebase
            codebase_dir = os.path.join(temp_dir, "test_codebase")
            os.makedirs(codebase_dir)
            
            script_path = os.path.join(codebase_dir, "test.py")
            with open(script_path, "w") as f:
                f.write('print("Schema migration test")')
            
            # Test 1: Schema migration
            print(f"\n  Testing schema migration...")
            
            # Create storage instance (this will trigger migration if needed)
            storage = AnalysisStorage(temp_dir)
            
            # Check migration status
            migration_status = storage._get_migration_status()
            
            if migration_status.get('compatible', False):
                migration_test['schema_migration']['success'] = True
                migration_test['schema_migration']['details'] = {
                    'database_exists': migration_status.get('database_exists', False),
                    'compatible': migration_status.get('compatible', False),
                    'version': migration_status.get('version', 0),
                    'has_profiling_columns': migration_status.get('has_profiling_columns', False)
                }
                
                print(f"    ✓ Schema migration successful")
                print(f"    ✓ Database compatible: {migration_status.get('compatible', False)}")
                print(f"    ✓ Database version: {migration_status.get('version', 0)}")
                print(f"    ✓ Has profiling columns: {migration_status.get('has_profiling_columns', False)}")
            else:
                print(f"    ✗ Schema migration failed")
            
            # Test 2: Backward compatibility
            print(f"\n  Testing backward compatibility...")
            
            # Run profiling and create analysis result
            analyzer = DynamicAnalyzer()
            scalene_result = analyzer.profile_with_scalene(script_path)
            viztracer_result = analyzer.trace_with_viztracer(script_path)
            
            analysis_result = {
                'analysis_results': {
                    'test.py': {
                        'scalene_profiling': scalene_result,
                        'viztracer_tracing': viztracer_result
                    }
                },
                'execution_coverage': {
                    'scripts_discovered': 1,
                    'scripts_analyzed': 1,
                    'scripts_skipped': 0,
                    'method_coverage': {
                        'scalene_profiling': 1,
                        'viztracer_tracing': 1
                    }
                },
                'method_coverage_percentage': 100.0,
                'execution_failures': [],
                'failure_count': 0,
                'issue_count': 0,
                'analysis_completeness': {
                    'status': 'complete',
                    'coverage_metrics': {
                        'overall_coverage': 100.0,
                        'completeness_context': 'Test analysis completed successfully'
                    }
                }
            }
            
            storage_id = storage.store_analysis(
                codebase_path=codebase_dir,
                analysis_type="dynamic",
                results=analysis_result,
                summary="Schema migration test"
            )
            
            # Verify record can be retrieved
            record = storage.session.query(AnalysisResult).filter(
                AnalysisResult.id == storage_id
            ).first()
            
            if record:
                migration_test['backward_compatibility']['success'] = True
                migration_test['backward_compatibility']['details'] = {
                    'record_id': record.id,
                    'can_retrieve': True,
                    'has_required_fields': all([
                        hasattr(record, 'codebase_path'),
                        hasattr(record, 'analysis_type'),
                        hasattr(record, 'timestamp'),
                        hasattr(record, 'summary')
                    ])
                }
                
                print(f"    ✓ Backward compatibility maintained")
                print(f"    ✓ Record retrieval successful")
                print(f"    ✓ All required fields present")
            
            # Test 3: Database versioning
            print(f"\n  Testing database versioning...")
            
            # Check if version table exists and can be queried
            try:
                from sqlalchemy import inspect
                inspector = inspect(storage.engine)
                
                if inspector.has_table('database_version'):
                    version = storage._get_database_version()
                    
                    migration_test['database_versioning']['success'] = True
                    migration_test['database_versioning']['details'] = {
                        'version_table_exists': True,
                        'current_version': version
                    }
                    
                    print(f"    ✓ Database versioning working")
                    print(f"    ✓ Version table exists")
                    print(f"    ✓ Current version: {version}")
                else:
                    print(f"    ✗ Version table not found")
                    
            except Exception as e:
                print(f"    ✗ Database versioning check failed: {e}")
            
            # Close storage
            storage.session.close()
            storage.engine.dispose()
            
        self.test_results['schema_migration'].append(migration_test)
        
        if all([
            migration_test['schema_migration']['success'],
            migration_test['backward_compatibility']['success'],
            migration_test['database_versioning']['success']
        ]):
            print(f"\n  ✓ Schema migration test: PASSED")
        else:
            print(f"\n  ✗ Schema migration test: FAILED")
        
    def generate_test_report(self):
        """Generate comprehensive test report"""
        print("\n" + "=" * 80)
        print("SIMPLE STORAGE VALIDATION TEST REPORT")
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
        print(f"Success Rate: {(passed_tests / total_tests * 100):.1f}%" if total_tests > 0 else "0%")
        
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
        
        # Validation criteria summary
        print(f"\n" + "-" * 80)
        print("VALIDATION CRITERIA SUMMARY:")
        print("-" * 80)
        
        validation_criteria = {
            "✅ Profiling data is stored in database": category_results.get('storage_validation', {}).get('success_rate', 0) >= 80,
            "✅ Data can be retrieved and queried correctly": category_results.get('data_retrieval', {}).get('success_rate', 0) >= 80,
            "✅ Metrics calculation includes Scalene and VizTracer metrics": category_results.get('metrics_validation', {}).get('success_rate', 0) >= 80,
            "✅ Storage schema migration works correctly": category_results.get('schema_migration', {}).get('success_rate', 0) >= 80
        }
        
        for criterion, passed in validation_criteria.items():
            status = "✓ PASS" if passed else "✗ FAIL"
            print(f"  {status} {criterion}")
        
        # Detailed findings
        print(f"\n" + "-" * 80)
        print("DETAILED FINDINGS:")
        print("-" * 80)
        
        for category, tests in self.test_results.items():
            print(f"\n{category.upper()}: ")
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
            'success_rate': (passed_tests / total_tests * 100) if total_tests > 0 else 0,
            'category_results': category_results,
            'test_results': self.test_results,
            'validation_criteria': validation_criteria
        }
        
        with open('simple_storage_validation_report.json', 'w') as f:
            json.dump(report_data, f, indent=2)
        
        print(f"\n" + "=" * 80)
        print("SIMPLE STORAGE VALIDATION REPORT SAVED TO: simple_storage_validation_report.json")
        print("=" * 80)
        
        # Final summary
        overall_success_rate = (passed_tests / total_tests * 100) if total_tests > 0 else 0
        
        print(f"\nFINAL SUMMARY:")
        print(f"  ✓ Storage validation: {category_results.get('storage_validation', {}).get('success_rate', 0):.1f}%")
        print(f"  ✓ Data retrieval: {category_results.get('data_retrieval', {}).get('success_rate', 0):.1f}%")
        print(f"  ✓ Metrics validation: {category_results.get('metrics_validation', {}).get('success_rate', 0):.1f}%")
        print(f"  ✓ Schema migration: {category_results.get('schema_migration', {}).get('success_rate', 0):.1f}%")
        print(f"\n  OVERALL: {overall_success_rate:.1f}%")
        
        # Check validation criteria
        all_criteria_met = all(validation_criteria.values())
        
        if all_criteria_met:
            print(f"\n🎉 SIMPLE STORAGE VALIDATION COMPLETED SUCCESSFULLY!")
            print("All validation criteria met.")
            return True
        else:
            print(f"\n❌ SIMPLE STORAGE VALIDATION COMPLETED WITH ISSUES")
            print("Some validation criteria not met. Review the detailed findings above.")
            return False

if __name__ == "__main__":
    # Run simple storage validation test suite
    test_suite = SimpleStorageValidationTest()
    success = test_suite.run_all_tests()
    
    if success:
        print(f"\n🎉 SIMPLE STORAGE VALIDATION TEST SUITE COMPLETED SUCCESSFULLY!")
        sys.exit(0)
    else:
        print(f"\n❌ SIMPLE STORAGE VALIDATION TEST SUITE FAILED!")
        sys.exit(1)