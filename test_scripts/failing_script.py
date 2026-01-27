#!/usr/bin/env python3
"""
Test script that fails with an exception
"""

def failing_function():
    """A function that raises an exception"""
    raise ValueError("This is a test exception")

def main():
    """Main function that calls failing function"""
    try:
        failing_function()
    except Exception as e:
        print(f"Caught exception: {e}")
        raise

if __name__ == "__main__":
    main()