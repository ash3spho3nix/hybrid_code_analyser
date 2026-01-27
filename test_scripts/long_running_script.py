#!/usr/bin/env python3
"""
Test script that runs for a long time to test timeout functionality
"""

import time

def long_running_function():
    """A function that runs for a long time"""
    print("Starting long running function...")
    for i in range(100):
        print(f"Iteration {i}")
        time.sleep(1)  # Sleep for 1 second per iteration
    print("Long running function completed")

def main():
    """Main function"""
    long_running_function()

if __name__ == "__main__":
    main()