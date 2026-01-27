#!/usr/bin/env python3
"""
Test script for VizTracer function call tracing
This script has complex function call patterns to test VizTracer's ability to trace function calls
"""

def simple_function():
    """A simple function"""
    return "Hello from simple_function"

def function_with_args(arg1, arg2):
    """Function with arguments"""
    result = arg1 + arg2
    return result

def function_with_return_value():
    """Function that returns a value"""
    return {"key": "value", "number": 42}

def recursive_function(n):
    """Recursive function"""
    if n <= 1:
        return 1
    return n * recursive_function(n - 1)

def function_with_exception():
    """Function that raises an exception"""
    try:
        raise ValueError("This is a test exception")
    except ValueError as e:
        return f"Caught exception: {e}"

def nested_function_calls():
    """Function with nested calls"""
    result1 = simple_function()
    result2 = function_with_args(1, 2)
    result3 = function_with_return_value()
    
    combined = f"{result1} - {result2} - {result3}"
    return combined

def main():
    """Main function that calls other functions"""
    print("Starting VizTracer function call test...")
    
    # Call various functions
    simple_function()
    function_with_args(5, 3)
    function_with_return_value()
    recursive_function(5)
    function_with_exception()
    nested_function_calls()
    
    print("VizTracer function call test completed")
    return "success"

if __name__ == "__main__":
    main()