#!/usr/bin/env python3
"""
Test script for VizTracer exception tracing
This script tests VizTracer's ability to trace exceptions and error handling
"""

def function_with_uncaught_exception():
    """Function that raises an uncaught exception"""
    raise ValueError("This is an uncaught exception")

def function_with_caught_exception():
    """Function that catches an exception"""
    try:
        raise RuntimeError("This is a caught exception")
    except RuntimeError as e:
        return f"Caught: {e}"

def function_with_multiple_exceptions():
    """Function that handles multiple exception types"""
    try:
        # This might raise different exceptions
        result = 10 / 0
    except ZeroDivisionError as e:
        return f"ZeroDivisionError: {e}"
    except Exception as e:
        return f"Generic exception: {e}"

def function_with_nested_exceptions():
    """Function with nested exception handling"""
    try:
        try:
            raise ValueError("Inner exception")
        except ValueError as e:
            raise RuntimeError("Outer exception") from e
    except RuntimeError as e:
        return f"Nested exception: {e}"

def main():
    """Main function"""
    print("Starting VizTracer exception tracing test...")
    
    # Test different exception scenarios
    try:
        function_with_uncaught_exception()
    except Exception as e:
        print(f"Caught uncaught exception: {e}")
    
    function_with_caught_exception()
    function_with_multiple_exceptions()
    function_with_nested_exceptions()
    
    print("VizTracer exception tracing test completed")
    return "success"

if __name__ == "__main__":
    main()