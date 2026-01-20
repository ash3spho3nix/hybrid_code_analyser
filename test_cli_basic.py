#!/usr/bin/env python3
"""
Basic test to verify CLI structure works
"""

import sys
import os

# Add the analyzer_cli directory to Python path
cli_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'analyzer_cli')
sys.path.insert(0, cli_dir)

# Test basic imports
try:
    from utils import get_current_timestamp, generate_unique_id
    from error_handler import AnalysisError
    from input_handler import validate_and_prepare_inputs
    from output_formatter import create_json_output
    from guardrails import apply_guardrails
    from incremental import should_perform_incremental_analysis
    
    print("[OK] All CLI module imports successful")
    
    # Test basic functionality
    timestamp = get_current_timestamp()
    print(f"[OK] Timestamp generation: {timestamp}")
    
    unique_id = generate_unique_id("test_")
    print(f"[OK] Unique ID generation: {unique_id}")
    
    # Test error handling
    try:
        raise AnalysisError("test_error", "This is a test error", "low")
    except AnalysisError as e:
        print(f"[OK] Error handling: {e.error_type}")
    
    print("\n[OK] CLI structure test completed successfully!")
    
except Exception as e:
    print(f"[ERROR] CLI structure test failed: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)