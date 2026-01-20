#!/usr/bin/env python3
"""
Main entry point for Hybrid Code Analyzer CLI
This script can be run directly as: python hybrid_analyzer_cli.py
"""

import sys
import os

# Add the analyzer_cli directory to Python path
cli_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'analyzer_cli')
sys.path.insert(0, cli_dir)

# Import the main function from cli_wrapper
from analyzer_cli.cli_wrapper import HybridAnalyzerCLI

def main():
    """Entry point for the CLI"""
    cli = HybridAnalyzerCLI()
    exit_code = cli.run()
    sys.exit(exit_code)

if __name__ == "__main__":
    main()