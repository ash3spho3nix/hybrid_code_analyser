#!/usr/bin/env python3
"""
Results Validator

This script validates test results against expected criteria, checks pass/fail
conditions, generates validation report, and handles result persistence.
"""

import os
import json
import sys
import argparse
from datetime import datetime
from typing import Dict, List, Any

# Add the project root to Python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))


class ResultsValidator:
    """
    Validator for test results.
    
    Responsibilities:
    - Validate test results against expected criteria
    - Check pass/fail conditions
    - Generate validation report
    - Handle result persistence
    """
    
    def __init__(self, results_dir: str = "test_framework/results"):
        """
        Initialize the results validator.
        
        Args:
            results_dir: Directory containing test results
        """
        self.results_dir = results_dir
        self.validation_report = {
            "validation_name": "Complete Test Results Validation",
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "validations": [],
            "summary": {},
            "status": "generating"
        }
    
    def validate_all_results(self) -> Dict[str, Any]:
        """
        Validate all test results against expected criteria.
        
        Returns:
            Dictionary containing validation results
        """
        print("Validating Test Results")
        print("=" * 50)
        
        try:
            # Validate different types of results
            self._validate_failure_zoo_results()
            self._validate_regression_results()
            self._validate_analyzer_validation_results()
            self._validate_faiss_validation_results()
            self._validate_comprehensive_report()
            
            # Generate summary
            self._generate_summary()
            self.validation_report["status"] = "completed"
            
            # Save validation report
            self._save_validation_report()
            
            print("\n" + "=" * 50)
            print("RESULTS VALIDATION COMPLETED")
            print("=" * 50)
            print(f"Overall Status: {self.validation_report['summary']['overall_status']}")
            print(f"Total Validations: {self.validation_report['summary']['total_validations']}")
            print(f"Passed Validations: {self.validation_report['summary']['passed_validations']}")
            print(f"Failed Validations: {self.validation_report['summary']['failed_validations']}")
            print("=" * 50)
            
            return self.validation_report
            
        except Exception as e:
            self.validation_report["status"] = "failed"
            self.validation_report["error"] = str(e)
            print(f"Results validation failed: {e}")
            raise
    
    def _validate_failure_zoo_results(self):
        """
        Validate failure zoo test results.
        """
        try:
            # Look for failure zoo results
            failure_zoo_results_path = os.path.join(
                self.results_dir, 
                "failure_zoo_results.json"
            )
            
            if os.path.exists(failure_zoo_results_path):
                with open(failure_zoo_results_path, 'r') as f:
                    failure_zoo_results = json.load(f)
                
                validation = {
                    "component": "failure_zoo",
                    "status": "FAIL",
                    "details": {},
                    "message": ""
                }
                
                # Check if results have expected structure
                if "test_cases" in failure_zoo_results and "summary" in failure_zoo_results:
                    total_tests = failure_zoo_results["summary"].get("total_tests", 0)
                    passed_tests = failure_zoo_results["summary"].get("passed_tests", 0)
                    
                    validation["details"]["total_tests"] = total_tests
                    validation["details"]["passed_tests"] = passed_tests
                    
                    # Validate that we have the expected number of test cases (7 categories)
                    if total_tests == 7:
                        validation["status"] = "PASS"
                        validation["message"] = f"Failure zoo has correct number of test cases: {total_tests}"
                    else:
                        validation["message"] = f"Failure zoo test count mismatch: expected 7, got {total_tests}"
                    
                    # Check if all tests passed
                    if passed_tests == total_tests:
                        validation["details"]["all_tests_passed"] = True
                    else:
                        validation["details"]["all_tests_passed"] = False
                else:
                    validation["message"] = "Failure zoo results missing required fields"
                
                self.validation_report["validations"].append(validation)
                print(f"✓ Failure zoo validation: {validation['status']}")
            else:
                print("⚠ Failure zoo results not found")
            
        except Exception as e:
            print(f"⚠ Could not validate failure zoo results: {e}")
    
    def _validate_regression_results(self):
        """
        Validate regression test results.
        """
        try:
            # Look for regression test results
            regression_results_path = os.path.join(
                self.results_dir, 
                "regression_test_results.json"
            )
            
            if os.path.exists(regression_results_path):
                with open(regression_results_path, 'r') as f:
                    regression_results = json.load(f)
                
                validation = {
                    "component": "regression_tests",
                    "status": "FAIL",
                    "details": {},
                    "message": ""
                }
                
                # Check if results have expected structure
                if "test_runs" in regression_results and "summary" in regression_results:
                    test_runs = len(regression_results["test_runs"])
                    overall_status = regression_results["summary"].get("overall_status", "unknown")
                    
                    validation["details"]["test_runs"] = test_runs
                    validation["details"]["overall_status"] = overall_status
                    
                    # Validate that we have 3 test runs
                    if test_runs == 3:
                        validation["status"] = "PASS"
                        validation["message"] = f"Regression tests have correct number of runs: {test_runs}"
                    else:
                        validation["message"] = f"Regression test runs mismatch: expected 3, got {test_runs}"
                    
                    # Check if overall status is PASS
                    if overall_status == "PASS":
                        validation["details"]["overall_pass"] = True
                    else:
                        validation["details"]["overall_pass"] = False
                else:
                    validation["message"] = "Regression results missing required fields"
                
                self.validation_report["validations"].append(validation)
                print(f"✓ Regression tests validation: {validation['status']}")
            else:
                print("⚠ Regression test results not found")
            
        except Exception as e:
            print(f"⚠ Could not validate regression results: {e}")
    
    def _validate_analyzer_validation_results(self):
        """
        Validate analyzer validation results.
        """
        try:
            # Look for analyzer validation results
            analyzer_validation_path = os.path.join(
                self.results_dir, 
                "analyzer_validation_results.json"
            )
            
            if os.path.exists(analyzer_validation_path):
                with open(analyzer_validation_path, 'r') as f:
                    analyzer_validation_results = json.load(f)
                
                validation = {
                    "component": "analyzer_validation",
                    "status": "FAIL",
                    "details": {},
                    "message": ""
                }
                
                # Check if results have expected structure
                if "validations" in analyzer_validation_results and "overall_status" in analyzer_validation_results:
                    overall_status = analyzer_validation_results["overall_status"]
                    validation_count = len(analyzer_validation_results["validations"])
                    
                    validation["details"]["validation_count"] = validation_count
                    validation["details"]["overall_status"] = overall_status
                    
                    # Validate that we have the expected validation types
                    expected_validations = ["analysis_status", "execution_failures", "coverage_percentage", 
                                          "completeness_context", "no_false_success"]
                    
                    if validation_count >= len(expected_validations):
                        validation["status"] = "PASS"
                        validation["message"] = f"Analyzer validation has correct structure with {validation_count} validations"
                    else:
                        validation["message"] = f"Analyzer validation count low: expected >= {len(expected_validations)}, got {validation_count}"
                    
                    # Check if overall status is PASS
                    if overall_status == "PASS":
                        validation["details"]["overall_pass"] = True
                    else:
                        validation["details"]["overall_pass"] = False
                else:
                    validation["message"] = "Analyzer validation results missing required fields"
                
                self.validation_report["validations"].append(validation)
                print(f"✓ Analyzer validation results: {validation['status']}")
            else:
                print("⚠ Analyzer validation results not found")
            
        except Exception as e:
            print(f"⚠ Could not validate analyzer validation results: {e}")
    
    def _validate_faiss_validation_results(self):
        """
        Validate FAISS validation results.
        """
        try:
            # Look for FAISS validation results
            faiss_validation_path = os.path.join(
                self.results_dir, 
                "faiss_validation_engine_results.json"
            )
            
            if os.path.exists(faiss_validation_path):
                with open(faiss_validation_path, 'r') as f:
                    faiss_validation_results = json.load(f)
                
                validation = {
                    "component": "faiss_validation",
                    "status": "FAIL",
                    "details": {},
                    "message": ""
                }
                
                # Check if results have expected structure
                if "validations" in faiss_validation_results and "overall_status" in faiss_validation_results:
                    overall_status = faiss_validation_results["overall_status"]
                    validation_count = len(faiss_validation_results["validations"])
                    
                    validation["details"]["validation_count"] = validation_count
                    validation["details"]["overall_status"] = overall_status
                    
                    # Validate that we have the expected validation types
                    expected_validations = ["vector_stability", "similarity_scores", "metadata_consistency", 
                                          "error_clustering", "index_persistence"]
                    
                    if validation_count >= len(expected_validations):
                        validation["status"] = "PASS"
                        validation["message"] = f"FAISS validation has correct structure with {validation_count} validations"
                    else:
                        validation["message"] = f"FAISS validation count low: expected >= {len(expected_validations)}, got {validation_count}"
                    
                    # Check if overall status is PASS
                    if overall_status == "PASS":
                        validation["details"]["overall_pass"] = True
                    else:
                        validation["details"]["overall_pass"] = False
                else:
                    validation["message"] = "FAISS validation results missing required fields"
                
                self.validation_report["validations"].append(validation)
                print(f"✓ FAISS validation results: {validation['status']}")
            else:
                print("⚠ FAISS validation results not found")
            
        except Exception as e:
            print(f"⚠ Could not validate FAISS validation results: {e}")
    
    def _validate_comprehensive_report(self):
        """
        Validate comprehensive report.
        """
        try:
            # Look for comprehensive report
            comprehensive_report_path = os.path.join(
                self.results_dir, 
                "comprehensive_report.json"
            )
            
            if os.path.exists(comprehensive_report_path):
                with open(comprehensive_report_path, 'r') as f:
                    comprehensive_report = json.load(f)
                
                validation = {
                    "component": "comprehensive_report",
                    "status": "FAIL",
                    "details": {},
                    "message": ""
                }
                
                # Check if report has expected structure
                if ("test_components" in comprehensive_report and 
                    "summary" in comprehensive_report and 
                    "metrics" in comprehensive_report):
                    
                    component_count = len(comprehensive_report["test_components"])
                    overall_status = comprehensive_report["summary"].get("overall_status", "unknown")
                    
                    validation["details"]["component_count"] = component_count
                    validation["details"]["overall_status"] = overall_status
                    
                    # Validate that we have expected components
                    expected_components = ["failure_zoo", "regression_tests", "analyzer_validation", "faiss_validation"]
                    
                    if component_count >= len(expected_components):
                        validation["status"] = "PASS"
                        validation["message"] = f"Comprehensive report has correct structure with {component_count} components"
                    else:
                        validation["message"] = f"Comprehensive report component count low: expected >= {len(expected_components)}, got {component_count}"
                    
                    # Check if overall status is PASS
                    if overall_status == "PASS":
                        validation["details"]["overall_pass"] = True
                    else:
                        validation["details"]["overall_pass"] = False
                else:
                    validation["message"] = "Comprehensive report missing required fields"
                
                self.validation_report["validations"].append(validation)
                print(f"✓ Comprehensive report validation: {validation['status']}")
            else:
                print("⚠ Comprehensive report not found")
            
        except Exception as e:
            print(f"⚠ Could not validate comprehensive report: {e}")
    
    def _generate_summary(self):
        """
        Generate summary of all validation results.
        """
        summary = {
            "total_validations": len(self.validation_report["validations"]),
            "passed_validations": 0,
            "failed_validations": 0,
            "validation_statuses": {}
        }
        
        # Count passed and failed validations
        for validation in self.validation_report["validations"]:
            component = validation["component"]
            status = validation["status"]
            
            summary["validation_statuses"][component] = status
            
            if status == "PASS":
                summary["passed_validations"] += 1
            elif status == "FAIL":
                summary["failed_validations"] += 1
        
        # Determine overall status
        if summary["failed_validations"] == 0 and summary["total_validations"] > 0:
            summary["overall_status"] = "PASS"
        elif summary["passed_validations"] == 0:
            summary["overall_status"] = "FAIL"
        else:
            summary["overall_status"] = "PARTIAL"
        
        self.validation_report["summary"] = summary
    
    def _save_validation_report(self):
        """
        Save validation report to file.
        """
        try:
            # Save validation report
            validation_report_path = os.path.join(
                self.results_dir, 
                "results_validation_report.json"
            )
            
            with open(validation_report_path, 'w') as f:
                json.dump(self.validation_report, f, indent=2)
            
            print(f"✓ Validation report saved to: {validation_report_path}")
            
        except Exception as e:
            print(f"⚠ Could not save validation report: {e}")
            raise


def parse_arguments() -> argparse.Namespace:
    """
    Parse command line arguments.
    
    Returns:
        Parsed arguments namespace
    """
    parser = argparse.ArgumentParser(
        description="Results Validator - Validates test results against expected criteria"
    )
    
    parser.add_argument(
        "--results-dir",
        type=str,
        default="test_framework/results",
        help="Directory containing test results (default: test_framework/results)"
    )
    
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Enable verbose output"
    )
    
    return parser.parse_args()


def main():
    """
    Main entry point for results validation.
    """
    # Parse command line arguments
    args = parse_arguments()
    
    print("Results Validator")
    print("=" * 50)
    print(f"Results Directory: {args.results_dir}")
    print("=" * 50)
    
    # Create and configure validator
    validator = ResultsValidator(results_dir=args.results_dir)
    
    try:
        # Validate all results
        results = validator.validate_all_results()
        
        return 0
        
    except Exception as e:
        print(f"\nResults validation failed: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())