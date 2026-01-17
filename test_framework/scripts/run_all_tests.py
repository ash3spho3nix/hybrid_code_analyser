#!/usr/bin/env python3
"""
Main Test Execution Script

This is the main script to execute the complete test suite including:
- Failure zoo tests
- Regression memory tests  
- Validation engine tests
- Generate comprehensive final report
- Handle command-line arguments
"""

import os
import json
import sys
import argparse
import subprocess
from datetime import datetime
from typing import Dict, Any

# Add the project root to Python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from test_framework.validation_engine.test_reporter import TestReporter


class CompleteTestExecutor:
    """
    Main executor for the complete test suite.
    
    Responsibilities:
    - Run failure zoo tests
    - Run regression memory tests
    - Run validation engine tests
    - Generate comprehensive final report
    - Handle command-line interface
    """
    
    def __init__(self):
        """
        Initialize the complete test executor.
        """
        self.config = {
            "failure_zoo_path": "test_failure_zoo",
            "results_dir": "test_framework/results",
            "run_failure_zoo": True,
            "run_regression": True,
            "run_validation": True,
            "generate_report": True,
            "verbose": False
        }
    
    def run_complete_test_suite(self) -> Dict[str, Any]:
        """
        Execute the complete test suite.
        
        Returns:
            Dictionary containing complete test results
        """
        print("Starting Complete Test Suite Execution")
        print("=" * 60)
        
        try:
            # Step 1: Run failure zoo tests
            if self.config["run_failure_zoo"]:
                print("Step 1/4: Running Failure Zoo Tests...")
                self._run_failure_zoo_tests()
            
            # Step 2: Run regression memory tests
            if self.config["run_regression"]:
                print("\nStep 2/4: Running Regression Memory Tests...")
                self._run_regression_tests()
            
            # Step 3: Run validation engine tests
            if self.config["run_validation"]:
                print("\nStep 3/4: Running Validation Engine Tests...")
                self._run_validation_engine_tests()
            
            # Step 4: Generate comprehensive report
            if self.config["generate_report"]:
                print("\nStep 4/4: Generating Comprehensive Report...")
                self._generate_comprehensive_report()
            
            print("\n" + "=" * 60)
            print("COMPLETE TEST SUITE EXECUTION COMPLETED")
            print("=" * 60)
            
            # Return summary results
            return {
                "status": "completed",
                "timestamp": datetime.utcnow().isoformat() + "Z",
                "message": "All test suite components executed successfully"
            }
            
        except Exception as e:
            print(f"Complete test suite execution failed: {e}")
            return {
                "status": "failed",
                "timestamp": datetime.utcnow().isoformat() + "Z",
                "error": str(e)
            }
    
    def _run_failure_zoo_tests(self):
        """
        Run failure zoo tests.
        """
        try:
            # Run the failure zoo test script
            script_path = os.path.join("test_framework", "scripts", "run_failure_zoo.py")
            
            cmd = [
                sys.executable, script_path,
                "--failure-zoo", self.config["failure_zoo_path"],
                "--results-dir", self.config["results_dir"]
            ]
            
            if self.config["verbose"]:
                cmd.append("--verbose")
            
            print(f"Running: {' '.join(cmd)}")
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode == 0:
                print("✓ Failure zoo tests completed successfully")
                if self.config["verbose"]:
                    print(result.stdout)
            else:
                print("✗ Failure zoo tests failed")
                if self.config["verbose"]:
                    print(result.stderr)
                raise Exception(f"Failure zoo tests failed: {result.stderr}")
                
        except Exception as e:
            print(f"✗ Could not run failure zoo tests: {e}")
            raise
    
    def _run_regression_tests(self):
        """
        Run regression memory tests.
        """
        try:
            # Run the regression test script
            script_path = os.path.join("test_framework", "scripts", "run_regression_tests.py")
            
            cmd = [
                sys.executable, script_path,
                "--test-type", "complete",
                "--failure-zoo", self.config["failure_zoo_path"],
                "--results-dir", os.path.join(self.config["results_dir"], "regression_results")
            ]
            
            if self.config["verbose"]:
                cmd.append("--verbose")
            
            print(f"Running: {' '.join(cmd)}")
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode == 0:
                print("✓ Regression memory tests completed successfully")
                if self.config["verbose"]:
                    print(result.stdout)
            else:
                print("✗ Regression memory tests failed")
                if self.config["verbose"]:
                    print(result.stderr)
                raise Exception(f"Regression memory tests failed: {result.stderr}")
                
        except Exception as e:
            print(f"✗ Could not run regression tests: {e}")
            raise
    
    def _run_validation_engine_tests(self):
        """
        Run validation engine tests.
        """
        try:
            # Run analyzer validator
            print("  Running analyzer validator...")
            analyzer_script = os.path.join("test_framework", "validation_engine", "analyzer_validator.py")
            
            cmd = [sys.executable, analyzer_script]
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode == 0:
                print("  ✓ Analyzer validator completed successfully")
            else:
                print("  ✗ Analyzer validator failed")
                if self.config["verbose"]:
                    print(result.stderr)
                raise Exception(f"Analyzer validator failed: {result.stderr}")
            
            # Run FAISS validator
            print("  Running FAISS validator...")
            faiss_script = os.path.join("test_framework", "validation_engine", "faiss_validator.py")
            
            cmd = [sys.executable, faiss_script]
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode == 0:
                print("  ✓ FAISS validator completed successfully")
            else:
                print("  ✗ FAISS validator failed")
                if self.config["verbose"]:
                    print(result.stderr)
                raise Exception(f"FAISS validator failed: {result.stderr}")
            
            print("✓ Validation engine tests completed successfully")
            
        except Exception as e:
            print(f"✗ Could not run validation engine tests: {e}")
            raise
    
    def _generate_comprehensive_report(self):
        """
        Generate comprehensive final report.
        """
        try:
            # Create test reporter instance
            reporter = TestReporter(results_dir=self.config["results_dir"])
            
            # Generate comprehensive report
            report = reporter.generate_comprehensive_report()
            
            # Print human-readable summary
            print("\nComprehensive Test Report Summary:")
            print("-" * 40)
            reporter.print_human_readable_summary()
            
            print("✓ Comprehensive report generated successfully")
            
        except Exception as e:
            print(f"✗ Could not generate comprehensive report: {e}")
            raise


def parse_arguments() -> argparse.Namespace:
    """
    Parse command line arguments.
    
    Returns:
        Parsed arguments namespace
    """
    parser = argparse.ArgumentParser(
        description="Complete Test Suite - Executes all test framework components"
    )
    
    parser.add_argument(
        "--failure-zoo",
        type=str,
        default="test_failure_zoo",
        help="Path to failure zoo directory (default: test_failure_zoo)"
    )
    
    parser.add_argument(
        "--results-dir",
        type=str,
        default="test_framework/results",
        help="Directory for test results (default: test_framework/results)"
    )
    
    parser.add_argument(
        "--skip-failure-zoo",
        action="store_true",
        help="Skip failure zoo tests"
    )
    
    parser.add_argument(
        "--skip-regression",
        action="store_true",
        help="Skip regression memory tests"
    )
    
    parser.add_argument(
        "--skip-validation",
        action="store_true",
        help="Skip validation engine tests"
    )
    
    parser.add_argument(
        "--skip-report",
        action="store_true",
        help="Skip comprehensive report generation"
    )
    
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Enable verbose output"
    )
    
    return parser.parse_args()


def main():
    """
    Main entry point for complete test suite execution.
    """
    # Parse command line arguments
    args = parse_arguments()
    
    print("Complete Test Suite Framework")
    print("=" * 60)
    print(f"Failure Zoo Path: {args.failure_zoo}")
    print(f"Results Directory: {args.results_dir}")
    print(f"Run Failure Zoo: {not args.skip_failure_zoo}")
    print(f"Run Regression: {not args.skip_regression}")
    print(f"Run Validation: {not args.skip_validation}")
    print(f"Generate Report: {not args.skip_report}")
    print("=" * 60)
    
    # Create and configure executor
    executor = CompleteTestExecutor()
    executor.config.update({
        "failure_zoo_path": args.failure_zoo,
        "results_dir": args.results_dir,
        "run_failure_zoo": not args.skip_failure_zoo,
        "run_regression": not args.skip_regression,
        "run_validation": not args.skip_validation,
        "generate_report": not args.skip_report,
        "verbose": args.verbose
    })
    
    try:
        # Run complete test suite
        results = executor.run_complete_test_suite()
        
        # Print final summary
        print("\n" + "=" * 60)
        print("FINAL TEST SUITE RESULTS")
        print("=" * 60)
        print(f"Status: {results['status']}")
        print(f"Timestamp: {results['timestamp']}")
        if results['status'] == 'completed':
            print("Message: All test suite components executed successfully")
        else:
            print(f"Error: {results.get('error', 'Unknown error')}")
        print("=" * 60)
        
        return 0
        
    except Exception as e:
        print(f"\nComplete test suite execution failed: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())