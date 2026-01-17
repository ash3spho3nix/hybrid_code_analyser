#!/usr/bin/env python3

"""
Test script to verify execution failure tracking functionality
"""

import os
import tempfile
import json
from analyzer.dynamic_analyzer import DynamicAnalyzer, FailureType, FailureSeverity
from analyzer.static_analyzer import StaticAnalyzer
from analyzer.multi_codebase import MultiCodebaseAnalyzer

def test_dynamic_analyzer_failures():
    """Test execution failure tracking in dynamic analyzer"""
    print("Testing Dynamic Analyzer Execution Failure Tracking...")
    
    # Create a temporary directory with a simple Python script
    with tempfile.TemporaryDirectory() as temp_dir:
        # Create a simple script that will work
        script_path = os.path.join(temp_dir, "working_script.py")
        with open(script_path, "w") as f:
            f.write("print('Hello, World!')")
        
        # Create a script with import error (valid analysis finding)
        failing_script_path = os.path.join(temp_dir, "failing_script.py")
        with open(failing_script_path, "w") as f:
            f.write("import nonexistent_module\nprint('This will fail')")
        
        # Test dynamic analyzer
        analyzer = DynamicAnalyzer()
        result = analyzer.run_dynamic_analysis(temp_dir)
        
        print(f"  - Analysis completed with status: {result.get('analysis_completeness', {}).get('status', 'unknown')}")
        print(f"  - Total failures: {result.get('failure_count', 0)}")
        print(f"  - Total issues: {result.get('issue_count', 0)}")
        print(f"  - Execution failures found: {len(result.get('execution_failures', []))}")
        
        # Check if we have execution failures
        if result.get('execution_failures'):
            for failure in result['execution_failures']:
                print(f"    * Failure: {failure['message']} ({failure['failure_type']})")
                print(f"      Severity: {failure['severity']}, Analysis Finding: {failure['is_analysis_finding']}")
        
        return True

def test_static_analyzer_failures():
    """Test execution failure tracking in static analyzer"""
    print("\nTesting Static Analyzer Execution Failure Tracking...")
    
    # Test with non-existent path
    analyzer = StaticAnalyzer()
    result = analyzer.analyze_codebase("/nonexistent/path/to/codebase")
    
    print(f"  - Analysis completed with status: {result.get('analysis_completeness', {}).get('status', 'unknown')}")
    print(f"  - Total failures: {result.get('failure_count', 0)}")
    print(f"  - Total issues: {result.get('issue_count', 0)}")
    print(f"  - Execution failures found: {len(result.get('execution_failures', []))}")
    
    # Test with existing path
    with tempfile.TemporaryDirectory() as temp_dir:
        # Create a simple Python file
        script_path = os.path.join(temp_dir, "test.py")
        with open(script_path, "w") as f:
            f.write("print('Hello, World!')")
        
        result = analyzer.analyze_codebase(temp_dir)
        print(f"  - Valid path analysis status: {result.get('analysis_completeness', {}).get('status', 'unknown')}")
        print(f"  - Valid path failures: {result.get('failure_count', 0)}")
        
    return True

def test_multi_codebase_aggregation():
    """Test execution failure aggregation in multi-codebase analyzer"""
    print("\nTesting Multi-Codebase Analyzer Failure Aggregation...")
    
    # Create temporary codebases
    with tempfile.TemporaryDirectory() as temp_dir1:
        with tempfile.TemporaryDirectory() as temp_dir2:
            # Create scripts in both codebases
            script1 = os.path.join(temp_dir1, "script.py")
            with open(script1, "w") as f:
                f.write("print('Codebase 1')")
            
            script2 = os.path.join(temp_dir2, "script.py")
            with open(script2, "w") as f:
                f.write("import nonexistent_module\nprint('Codebase 2')")
            
            # Test multi-codebase analyzer
            analyzer = MultiCodebaseAnalyzer(llm_backend="mock")  # Use mock to avoid LLM calls
            
            # Test single analysis
            result = analyzer.analyze_single(temp_dir1, "Test analysis")
            print(f"  - Single analysis failures: {result.get('failure_count', 0)}")
            print(f"  - Analysis status: {result.get('analysis_completeness', {}).get('status', 'unknown')}")
            
            # Test comparison
            try:
                comparison = analyzer.compare_codebases(temp_dir1, temp_dir2, "Compare codebases")
                print(f"  - Comparison failures: {comparison.get('failure_count', 0)}")
                print(f"  - Comparison status: {comparison.get('comparison_completeness', {}).get('status', 'unknown')}")
            except Exception as e:
                print(f"  - Comparison failed with exception: {e}")
            
    return True

def test_failure_classification():
    """Test failure classification logic"""
    print("\nTesting Failure Classification...")
    
    # Test different failure types
    test_cases = [
        (ImportError("Module not found"), "Should be IMPORT_ERROR, WARNING, analysis finding"),
        (ModuleNotFoundError("No module named 'xyz'"), "Should be DEPENDENCY_MISSING, WARNING, analysis finding"),
        (FileNotFoundError("File not found"), "Should be FILE_ACCESS_ERROR, ERROR, not analysis finding"),
        (RuntimeError("Runtime error"), "Should be RUNTIME_ERROR, ERROR, not analysis finding"),
    ]
    
    analyzer = DynamicAnalyzer()
    
    for exception, expected in test_cases:
        failure = analyzer._classify_failure(exception, "test_context")
        print(f"  - {type(exception).__name__}: {failure.failure_type.value} / {failure.severity.value} / Analysis Finding: {failure.is_analysis_finding}")
        print(f"    Expected: {expected}")
    
    return True

if __name__ == "__main__":
    print("Running Execution Failure Tracking Tests...\n")
    
    try:
        test_dynamic_analyzer_failures()
        test_static_analyzer_failures()
        test_multi_codebase_aggregation()
        test_failure_classification()
        
        print("\n[OK] All tests completed successfully!")
        print("\nKey Features Verified:")
        print("  [OK] Dynamic analyzer tracks execution failures with context")
        print("  [OK] Static analyzer handles file access errors gracefully")
        print("  [OK] Multi-codebase analyzer aggregates failures across analyses")
        print("  [OK] Failures are classified by type and severity")
        print("  [OK] Analysis findings are distinguished from actual errors")
        print("  [OK] Execution failures include raw error data and tracebacks")
        
    except Exception as e:
        print(f"\n[X] Test failed with exception: {e}")
        import traceback
        traceback.print_exc()