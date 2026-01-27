#!/usr/bin/env python3
"""
Test script that has an import error
"""

def main():
    """Main function that tries to import a non-existent module"""
    try:
        import non_existent_module
    except ImportError as e:
        print(f"Import error: {e}")
        raise

if __name__ == "__main__":
    main()