#!/usr/bin/env python3
"""
Failure Zoo Test Runner

This script executes all failure zoo test cases, validates against expected outputs,
generates failure zoo test report, and handles command-line arguments.
"""

import os
import json
import sys
import argparse
from datetime import datetime
from typing import Dict, List, Any

# Add the project root to Python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from test_framework.validation_engine.analyzer_validator import AnalyzerValidator


class FailureZooTestRunner:
    """
    Runner for failure zoo test cases.
    
    Responsibilities:
    - Iterate through all failure categories
    - Execute analyzer on each test case
    - Capture and store analyzer output
    - Validate against expected outputs
    - Generate failure zoo test report
    """
    
    def __init__(self, failure_zoo_path: str = "test_failure_zoo"):
        """
        Initialize the failure zoo test runner.
        
        Args:
            failure_zoo_path: Path to the failure zoo directory
        """
        self.failure_zoo_path = failure_zoo_path
        self.validator = AnalyzerValidator()
        self.test_results = {
            "test_name": "Controlled Failure Zoo",
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "test_cases": [],
            "summary": {},
            "status": "generating"
        }
    
    def run_all_tests(self) -> Dict[str, Any]:
        """
        Run all failure zoo test cases.
        
        Returns:
            Dictionary containing all test results
        """
        print("Running Failure Zoo Tests")
        print("=" * 50)
        
        try:
            # Get all test case directories
            test_categories = self._get_test_categories()
            
            print(f"Found {len(test_categories)} test categories")
            
            # Run tests for each category
            for category in test_categories:
                print(f"\nRunning tests for category: {category}")
                test_case_results = self._run_test_category(category)
                self.test_results["test_cases"].append(test_case_results)
            
            # Generate summary
            self._generate_summary()
            self.test_results["status"] = "completed"
            
            # Save results
            self._save_results()
            
            print("\n" + "=" * 50)
            print("FAILURE ZOO TESTS COMPLETED")
            print("=" * 50)
            print(f"Overall Status: {self.test_results['summary']['overall_status']}")
            print(f"Total Tests: {self.test_results['summary']['total_tests']}")
            print(f"Passed Tests: {self.test_results['summary']['passed_tests']}")
            print(f"Failed Tests: {self.test_results['summary']['failed_tests']}")
            print("=" * 50)
            
            return self.test_results
            
        except Exception as e:
            self.test_results["status"] = "failed"
            self.test_results["error"] = str(e)
            print(f"Failure zoo tests failed: {e}")
            raise
    
    def _get_test_categories(self) -> List[str]:
        """
        Get all test case categories from the failure zoo.
        
        Returns:
            List of test category names
        """
        categories = []
        
        try:
            # List all directories in the failure zoo path
            for item in os.listdir(self.failure_zoo_path):
                item_path = os.path.join(self.failure_zoo_path, item)
                if os.path.isdir(item_path) and item != "__pycache__":
                    # Check if it has expected_output.json
                    expected_output_path = os.path.join(item_path, "expected_output.json")
                    if os.path.exists(expected_output_path):
                        categories.append(item)
            
            # Sort categories for consistent ordering
            categories.sort()
            
        except Exception as e:
            print(f"Warning: Could not get test categories: {e}")
        
        return categories
    
    def _run_test_category(self, category: str) -> Dict[str, Any]:
        """
        Run tests for a single failure category.
        
        Args:
            category: Name of the test category
            
        Returns:
            Dictionary containing test results for the category
        """
        test_case_results = {
            "category": category,
            "status": "generating",
            "timestamp": datetime.utcnow().isoformat() + "Z"
        }
        
        try:
            # Get the test case path
            test_case_path = os.path.join(self.failure_zoo_path, category)
            
            # Load expected output
            expected_output_path = os.path.join(test_case_path, "expected_output.json")
            with open(expected_output_path, 'r') as f:
                expected_output = json.load(f)
            
            # Validate the test case
            validation_results = self.validator.validate_failure_zoo_test_case(test_case_path)
            
            # Extract key information
            test_case_results["expected_failures"] = len(expected_output.get("execution_failures", []))
            test_case_results["analysis_status"] = expected_output.get("analysis_status", "unknown")
            test_case_results["coverage_percentage"] = expected_output.get("coverage_percentage", 
                expected_output.get("discovery_artifacts", {}).get("analysis_coverage_percentage", 0.0))
            
            # Add validation results
            test_case_results["validation_results"] = validation_results["validations"]
            
            # Determine test case status
            if validation_results["overall_status"] == "PASS":
                test_case_results["status"] = "PASS"
            else:
                test_case_results["status"] = "FAIL"
            
            print(f"  Category {category}: {test_case_results['status']}")
            
        except Exception as e:
            test_case_results["status"] = "FAIL"
            test_case_results["error"] = str(e)
            print(f"  Category {category}: FAIL - {e}")
        
        return test_case_results
    
    def _generate_summary(self):
        """
        Generate summary of all test results.
        """
        summary = {
            "total_tests": len(self.test_results["test_cases"]),
            "passed_tests": 0,
            "failed_tests": 0,
            "test_case_statuses": {}
        }
        
        # Count passed and failed tests
        for test_case in self.test_results["test_cases"]:
            category = test_case["category"]
            status = test_case["status"]
            
            summary["test_case_statuses"][category] = status
            
            if status == "PASS":
                summary["passed_tests"] += 1
            elif status == "FAIL":
                summary["failed_tests"] += 1
        
        # Determine overall status
        if summary["failed_tests"] == 0 and summary["total_tests"] > 0:
            summary["overall_status"] = "PASS"
        elif summary["passed_tests"] == 0:
            summary["overall_status"] = "FAIL"
        else:
            summary["overall_status"] = "PARTIAL"
        
        self.test_results["summary"] = summary
    
    def _save_results(self):
        """
        Save test results to file.
        """
        try:
            # Create results directory if it doesn't exist
            os.makedirs(self.failure_zoo_path, exist_ok=True)
            
            # Save to failure zoo results path
            failure_zoo_results_path = os.path.join("test_framework", "results", "failure_zoo_results.json")
            os.makedirs(os.path.dirname(failure_zoo_results_path), exist_ok=True)
            
            with open(failure_zoo_results_path, 'w') as f:
                json.dump(self.test_results, f, indent=2)
            
            print(f"✓ Failure zoo results saved to: {failure_zoo_results_path}")
            
        except Exception as e:
            print(f"⚠ Could not save failure zoo results: {e}")
            raise


def parse_arguments() -> argparse.Namespace:
    """
    Parse command line arguments.
    
    Returns:
        Parsed arguments namespace
    """
    parser = argparse.ArgumentParser(
        description="Failure Zoo Test Runner - Executes all failure zoo test cases"
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
        "--verbose",
        action="store_true",
        help="Enable verbose output"
    )
    
    return parser.parse_args()


def main():
    """
    Main entry point for failure zoo test execution.
    """
    # Parse command line arguments
    args = parse_arguments()
    
    print("Failure Zoo Test Runner")
    print("=" * 50)
    print(f"Failure Zoo Path: {args.failure_zoo}")
    print(f"Results Directory: {args.results_dir}")
    print("=" * 50)
    
    # Create and configure test runner
    test_runner = FailureZooTestRunner(failure_zoo_path=args.failure_zoo)
    
    try:
        # Run all tests
        results = test_runner.run_all_tests()
        
        return 0
        
    except Exception as e:
        print(f"\nFailure zoo test execution failed: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())