#!/usr/bin/env python3
"""
Main entry point for Hybrid Code Analyzer CLI
"""

import sys
import os

# Add the analyzer_cli directory to Python path
cli_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, cli_dir)

# Import the main function from cli_wrapper
from cli_wrapper import main

if __name__ == "__main__":
    main()