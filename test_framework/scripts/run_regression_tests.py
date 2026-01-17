#!/usr/bin/env python3
"""
Main Regression Test Execution Script

This script executes the complete regression test sequence, handles command-line
arguments, manages test execution flow, and generates intermediate results.
"""

import os
import sys
import json
import argparse
from datetime import datetime
from typing import Dict, Any

# Add the project root to Python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from test_framework.regression_tests.test_runner import TestRunner
from test_framework.regression_tests.faiss_validator import FAISSValidator
from test_framework.regression_tests.similarity_scorer import SimilarityScorer


class RegressionTestExecutor:
    """
    Main executor for regression tests.
    
    Handles the complete test execution workflow including:
    - Running the 3-run test sequence
    - Validating FAISS behavior
    - Generating reports
    - Managing command-line interface
    """
    
    def __init__(self):
        """
        Initialize the test executor.
        """
        self.test_runner = TestRunner()
        self.faiss_validator = FAISSValidator()
        self.similarity_scorer = SimilarityScorer()
        
        # Default configuration
        self.config = {
            "failure_zoo_path": "test_failure_zoo",
            "results_dir": "test_framework/results/regression_results",
            "run_validation": True,
            "generate_report": True,
            "verbose": False
        }
    
    def run_complete_test_sequence(self) -> Dict[str, Any]:
        """
        Execute the complete regression test sequence.
        
        Returns:
            Dictionary containing complete test results
        """
        print("Starting Complete Regression Test Sequence")
        print("=" * 50)
        
        # Step 1: Run the 3-run test sequence
        print("Step 1/3: Running 3-run test sequence...")
        test_results = self.test_runner.run_test_sequence()
        
        # Step 2: Validate FAISS behavior
        print("\nStep 2/3: Validating FAISS behavior...")
        validation_results = self.faiss_validator.validate_all()
        
        # Step 3: Generate comprehensive report
        print("\nStep 3/3: Generating comprehensive report...")
        comprehensive_report = self._generate_comprehensive_report(test_results, validation_results)
        
        print("\n" + "=" * 50)
        print("REGRESSION TEST SEQUENCE COMPLETED")
        print("=" * 50)
        
        return comprehensive_report
    
    def _generate_comprehensive_report(self, 
                                     test_results: Dict[str, Any], 
                                     validation_results: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate comprehensive test report.
        
        Args:
            test_results: Results from test runner
            validation_results: Results from FAISS validator
            
        Returns:
            Comprehensive report dictionary
        """
        report = {
            "test_name": "Complete Regression Memory Test",
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "test_execution": test_results,
            "faiss_validation": validation_results,
            "summary": {},
            "status": "completed"
        }
        
        # Generate summary
        test_status = test_results.get("summary", {}).get("overall_status", "unknown")
        validation_status = validation_results.get("overall_status", "unknown")
        
        report["summary"]["test_execution_status"] = test_status
        report["summary"]["faiss_validation_status"] = validation_status
        
        # Overall status
        if test_status == "PASS" and validation_status == "PASS":
            report["summary"]["overall_status"] = "PASS"
        else:
            report["summary"]["overall_status"] = "FAIL"
        
        # Add metrics from test execution
        if "summary" in test_results:
            report["summary"].update({
                "total_failures_run1": test_results["summary"].get("total_failures_run1", 0),
                "total_failures_run2": test_results["summary"].get("total_failures_run2", 0),
                "total_failures_run3": test_results["summary"].get("total_failures_run3", 0),
                "failures_resolved": test_results["summary"].get("failures_resolved", 0),
                "recurring_errors_run2": test_results["summary"].get("recurring_errors_run2", 0),
                "recurring_errors_run3": test_results["summary"].get("recurring_errors_run3", 0)
            })
        
        # Save comprehensive report
        self._save_comprehensive_report(report)
        
        return report
    
    def _save_comprehensive_report(self, report: Dict[str, Any]):
        """
        Save comprehensive report to file.
        
        Args:
            report: Report dictionary to save
        """
        # Save to regression results directory
        regression_report_path = os.path.join(
            self.config["results_dir"], 
            "comprehensive_regression_report.json"
        )
        
        with open(regression_report_path, 'w') as f:
            json.dump(report, f, indent=2)
        
        print(f"Comprehensive report saved to: {regression_report_path}")
        
        # Also update the main comprehensive report
        main_report_path = "test_framework/results/comprehensive_report.json"
        with open(main_report_path, 'w') as f:
            json.dump(report, f, indent=2)
        
        print(f"Main report updated at: {main_report_path}")
    
    def run_individual_tests(self, test_type: str = "all"):
        """
        Run individual test components.
        
        Args:
            test_type: Type of test to run ('runner', 'validator', 'scorer', 'all')
        """
        if test_type in ["runner", "all"]:
            print("Running Test Runner...")
            test_results = self.test_runner.run_test_sequence()
            print("Test Runner completed.")
            
        if test_type in ["validator", "all"]:
            print("Running FAISS Validator...")
            validation_results = self.faiss_validator.validate_all()
            print("FAISS Validator completed.")
            
        if test_type in ["scorer", "all"]:
            print("Running Similarity Scorer...")
            # Run a sample classification
            sample_report = self.similarity_scorer.main()
            print("Similarity Scorer completed.")


def parse_arguments() -> argparse.Namespace:
    """
    Parse command line arguments.
    
    Returns:
        Parsed arguments namespace
    """
    parser = argparse.ArgumentParser(
        description="Regression Memory Test Framework - Main Execution Script"
    )
    
    parser.add_argument(
        "--test-type",
        choices=["complete", "runner", "validator", "scorer"],
        default="complete",
        help="Type of test to run (default: complete)"
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
        default="test_framework/results/regression_results",
        help="Directory for test results (default: test_framework/results/regression_results)"
    )
    
    parser.add_argument(
        "--no-validation",
        action="store_true",
        help="Skip FAISS validation step"
    )
    
    parser.add_argument(
        "--no-report",
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
    Main entry point for regression test execution.
    """
    # Parse command line arguments
    args = parse_arguments()
    
    print("Regression Memory Test Framework")
    print("=" * 50)
    print(f"Test Type: {args.test_type}")
    print(f"Failure Zoo: {args.failure_zoo}")
    print(f"Results Directory: {args.results_dir}")
    print("=" * 50)
    
    # Create and configure executor
    executor = RegressionTestExecutor()
    executor.config.update({
        "failure_zoo_path": args.failure_zoo,
        "results_dir": args.results_dir,
        "run_validation": not args.no_validation,
        "generate_report": not args.no_report,
        "verbose": args.verbose
    })
    
    try:
        if args.test_type == "complete":
            # Run complete test sequence
            results = executor.run_complete_test_sequence()
            
            # Print final summary
            print("\n" + "=" * 50)
            print("FINAL TEST RESULTS")
            print("=" * 50)
            print(f"Overall Status: {results['summary']['overall_status']}")
            print(f"Test Execution: {results['summary']['test_execution_status']}")
            print(f"FAISS Validation: {results['summary']['faiss_validation_status']}")
            print(f"Failures Resolved: {results['summary']['failures_resolved']}")
            print("=" * 50)
            
        else:
            # Run individual test components
            executor.run_individual_tests(args.test_type)
            
        return 0
        
    except Exception as e:
        print(f"\nTest execution failed: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())