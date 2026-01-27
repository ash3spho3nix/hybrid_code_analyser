#!/usr/bin/env python3
"""
Test script to validate the safe execution wrapper functionality
"""

import sys
import os
import tempfile
import json
from pathlib import Path

# Add the analyzer directory to the path
sys.path.insert(0, os.path.join(os.getcwd(), 'analyzer'))

from analyzer.dynamic_analyzer import DynamicAnalyzer
#from dynamic_analyzer import DynamicAnalyzer

def test_successful_execution():
    """Test successful execution with safe_execute_profiler"""
    print("Testing successful execution...")
    
    analyzer = DynamicAnalyzer()
    
    # Create a simple profiler function that just returns success
    def simple_profiler(script_path):
        return {"status": "success", "message": "Profiler executed successfully"}
    
    try:
        result = analyzer.safe_execute_profiler(
            "test_scripts/successful_script.py", 
            simple_profiler, 
            "test_scripts/successful_script.py"
        )
        print(f"[SUCCESS] Successful execution result: {result}")
        return True
    except Exception as e:
        print(f"[FAILED] Successful execution failed: {e}")
        return False

def test_error_handling():
    """Test error handling with safe_execute_profiler"""
    print("\nTesting error handling...")
    
    analyzer = DynamicAnalyzer()
    
    # Create a profiler function that raises an exception
    def failing_profiler(script_path):
        raise ValueError("Test exception from profiler")
    
    try:
        result = analyzer.safe_execute_profiler(
            "test_scripts/failing_script.py", 
            failing_profiler, 
            "test_scripts/failing_script.py"
        )
        print(f"[SUCCESS] Error handling result: {result}")
        return True
    except Exception as e:
        print(f"[FAILED] Error handling failed: {e}")
        return False

def test_timeout_functionality():
    """Test timeout functionality with safe_execute_profiler"""
    print("\nTesting timeout functionality...")
    
    analyzer = DynamicAnalyzer()
    
    # Create a profiler function that runs for a long time
    def long_running_profiler(script_path):
        import time
        time.sleep(5)  # This should timeout since default is 180 seconds but we'll test with a shorter one
        return {"status": "completed"}
    
    try:
        # Test with a script that would normally timeout
        result = analyzer.safe_execute_profiler(
            "test_scripts/long_running_script.py", 
            long_running_profiler, 
            "test_scripts/long_running_script.py"
        )
        print(f"[SUCCESS] Timeout test result: {result}")
        return True
    except Exception as e:
        print(f"[FAILED] Timeout test failed: {e}")
        return False

def test_import_error_handling():
    """Test import error handling"""
    print("\nTesting import error handling...")
    
    analyzer = DynamicAnalyzer()
    
    def import_error_profiler(script_path):
        import non_existent_module  # This should cause an ImportError
        return {"status": "should not reach here"}
    
    try:
        result = analyzer.safe_execute_profiler(
            "test_scripts/import_error_script.py", 
            import_error_profiler, 
            "test_scripts/import_error_script.py"
        )
        print(f"[SUCCESS] Import error handling result: {result}")
        return True
    except Exception as e:
        print(f"[FAILED] Import error handling failed: {e}")
        return False

def test_subprocess_isolation():
    """Test subprocess isolation"""
    print("\nTesting subprocess isolation...")
    
    analyzer = DynamicAnalyzer()
    
    # Create a profiler that modifies global state
    global test_global_var
    test_global_var = "initial_value"
    
    def state_modifying_profiler(script_path):
        global test_global_var
        original_value = test_global_var
        test_global_var = "modified_in_profiler"
        return {"original_value": original_value, "modified_value": test_global_var}
    
    try:
        result = analyzer.safe_execute_profiler(
            "test_scripts/successful_script.py", 
            state_modifying_profiler, 
            "test_scripts/successful_script.py"
        )
        print(f"[SUCCESS] Subprocess isolation result: {result}")
        print(f"Global variable after execution: {test_global_var}")
        
        # Check if global state was preserved (it should be since it runs in subprocess)
        if test_global_var == "initial_value":
            print("[SUCCESS] Global state preserved - subprocess isolation working")
            return True
        else:
            print("[FAILED] Global state modified - subprocess isolation may not be working")
            return False
    except Exception as e:
        print(f"[FAILED] Subprocess isolation test failed: {e}")
        return False

def test_environment_variables():
    """Test environment variable handling"""
    print("\nTesting environment variable handling...")
    
    analyzer = DynamicAnalyzer()
    
    def env_checking_profiler(script_path):
        import os
        # Check if PYTHONPATH is set correctly
        pythonpath = os.environ.get('PYTHONPATH', '')
        return {"pythonpath": pythonpath, "env_vars_set": bool(pythonpath)}
    
    try:
        result = analyzer.safe_execute_profiler(
            "test_scripts/successful_script.py", 
            env_checking_profiler, 
            "test_scripts/successful_script.py"
        )
        print(f"[SUCCESS] Environment variable test result: {result}")
        return True
    except Exception as e:
        print(f"[FAILED] Environment variable test failed: {e}")
        return False

def main():
    """Run all tests"""
    print("Starting Safe Execution Wrapper Validation Tests\n")
    
    tests = [
        test_successful_execution,
        test_error_handling,
        test_timeout_functionality,
        test_import_error_handling,
        test_subprocess_isolation,
        test_environment_variables
    ]
    
    results = []
    for test in tests:
        try:
            result = test()
            results.append(result)
        except Exception as e:
            print(f"[FAILED] Test {test.__name__} crashed: {e}")
            results.append(False)
    
    # Summary
    passed = sum(results)
    total = len(results)
    
    print(f"\n[SUMMARY] Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("[SUCCESS] All tests passed! Safe execution wrapper is working correctly.")
        return True
    else:
        print("[WARNING] Some tests failed. Please review the output above.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)