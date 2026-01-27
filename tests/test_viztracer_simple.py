#!/usr/bin/env python3

"""
Simple test to check VizTracer functionality specifically.
"""

try:
    from analyzer.dynamic_analyzer import DynamicAnalyzer
    import tempfile
    import os
    
    print("Testing VizTracer functionality...")
    
    # Create a simple test script
    test_script_content = '''
def test_function():
    print("Hello from test function")
    return 42

result = test_function()
print(f"Result: {result}")
'''
    
    # Write test script to a temporary file
    with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
        f.write(test_script_content)
        test_script_path = f.name
    
    print(f"Created test script: {test_script_path}")
    
    # Create analyzer instance
    analyzer = DynamicAnalyzer()
    print("Created DynamicAnalyzer instance")
    
    # Try to run VizTracer tracing
    print("Running VizTracer tracing...")
    result = analyzer.trace_with_viztracer(test_script_path)
    
    print(f"VizTracer result: {result}")
    
    # Check if we got expected keys
    expected_keys = ['function_calls', 'call_count', 'exception_trace', 'exception_count', 'execution_flow', 'coverage', 'execution_success']
    
    for key in expected_keys:
        if key in result:
            print(f"[+] Found key '{key}': {type(result[key])}")
        else:
            print(f"[-] Missing key '{key}'")
    
    # Clean up
    os.unlink(test_script_path)
    print("Test completed")
    
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()