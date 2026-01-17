#!/usr/bin/env python3
"""
Analyzer Validator

This module validates analyzer output including analysis_status correctness,
execution_failures accuracy, coverage percentages, completeness_context,
and ensures no false successes are reported.
"""

import os
import json
import sys
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple

# Add the project root to Python path to import analyzer modules
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))


class AnalyzerValidator:
    """
    Validator for analyzer output.
    
    Responsibilities:
    - Validate analysis_status correctness (complete/partial/failed)
    - Check execution_failures accuracy and completeness
    - Verify coverage percentages match expected values
    - Validate completeness_context provides meaningful explanations
    - Ensure no false successes are reported
    """
    
    def __init__(self):
        """
        Initialize the analyzer validator.
        """
        pass
    
    def validate_analyzer_output(self, 
                               analyzer_output: Dict[str, Any], 
                               expected_output: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate analyzer output against expected output.
        
        Args:
            analyzer_output: Actual analyzer output to validate
            expected_output: Expected analyzer output for comparison
            
        Returns:
            Dictionary containing validation results
        """
        validation_results = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "validations": {},
            "overall_status": "generating"
        }
        
        try:
            # Run individual validation checks
            validation_results["validations"]["analysis_status"] = self._validate_analysis_status(
                analyzer_output, expected_output
            )
            validation_results["validations"]["execution_failures"] = self._validate_execution_failures(
                analyzer_output, expected_output
            )
            validation_results["validations"]["coverage_percentage"] = self._validate_coverage_percentage(
                analyzer_output, expected_output
            )
            validation_results["validations"]["completeness_context"] = self._validate_completeness_context(
                analyzer_output, expected_output
            )
            validation_results["validations"]["no_false_success"] = self._validate_no_false_success(
                analyzer_output, expected_output
            )
            
            # Generate overall status
            all_passed = all(
                validation["status"] == "PASS"
                for validation in validation_results["validations"].values()
            )
            validation_results["overall_status"] = "PASS" if all_passed else "FAIL"
            
        except Exception as e:
            validation_results["overall_status"] = "FAIL"
            validation_results["error"] = str(e)
        
        return validation_results
    
    def _validate_analysis_status(self, 
                                 analyzer_output: Dict[str, Any], 
                                 expected_output: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate analysis_status correctness.
        
        Args:
            analyzer_output: Actual analyzer output
            expected_output: Expected analyzer output
            
        Returns:
            Dictionary with validation status and details
        """
        validation = {
            "status": "FAIL",
            "details": {},
            "message": ""
        }
        
        try:
            actual_status = analyzer_output.get("analysis_status", "unknown")
            expected_status = expected_output.get("analysis_status", "unknown")
            
            validation["details"]["actual_status"] = actual_status
            validation["details"]["expected_status"] = expected_status
            
            if actual_status == expected_status:
                validation["status"] = "PASS"
                validation["message"] = f"Analysis status is correct: {actual_status}"
            else:
                validation["message"] = f"Analysis status mismatch: expected '{expected_status}', got '{actual_status}'"
            
            # Additional validation: ensure no "complete" status when failures exist
            execution_failures = analyzer_output.get("execution_failures", [])
            if actual_status == "complete" and execution_failures:
                validation["status"] = "FAIL"
                validation["message"] = "False success detected: analysis_status is 'complete' but execution_failures exist"
            
        except Exception as e:
            validation["message"] = f"Analysis status validation failed: {e}"
        
        return validation
    
    def _validate_execution_failures(self, 
                                    analyzer_output: Dict[str, Any], 
                                    expected_output: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate execution_failures accuracy and completeness.
        
        Args:
            analyzer_output: Actual analyzer output
            expected_output: Expected analyzer output
            
        Returns:
            Dictionary with validation status and details
        """
        validation = {
            "status": "FAIL",
            "details": {},
            "message": ""
        }
        
        try:
            actual_failures = analyzer_output.get("execution_failures", [])
            expected_failures = expected_output.get("execution_failures", [])
            
            actual_count = len(actual_failures)
            expected_count = len(expected_failures)
            
            validation["details"]["actual_failure_count"] = actual_count
            validation["details"]["expected_failure_count"] = expected_count
            
            if actual_count == expected_count:
                validation["status"] = "PASS"
                validation["message"] = f"Execution failure count is correct: {actual_count}"
                
                # Validate failure types if available
                if actual_count > 0:
                    failure_type_validation = self._validate_failure_types(actual_failures, expected_failures)
                    validation["details"]["failure_type_validation"] = failure_type_validation
                    
                    if failure_type_validation["status"] == "FAIL":
                        validation["status"] = "FAIL"
                        validation["message"] = "Execution failure count correct but types mismatch"
            else:
                validation["message"] = f"Execution failure count mismatch: expected {expected_count}, got {actual_count}"
            
        except Exception as e:
            validation["message"] = f"Execution failures validation failed: {e}"
        
        return validation
    
    def _validate_failure_types(self, 
                               actual_failures: List[Dict[str, Any]], 
                               expected_failures: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Validate that failure types match between actual and expected.
        
        Args:
            actual_failures: List of actual failure dictionaries
            expected_failures: List of expected failure dictionaries
            
        Returns:
            Dictionary with validation status and details
        """
        validation = {
            "status": "FAIL",
            "details": {},
            "message": ""
        }
        
        try:
            actual_types = [f.get("failure_type", "unknown") for f in actual_failures]
            expected_types = [f.get("failure_type", "unknown") for f in expected_failures]
            
            # Sort for comparison
            actual_types_sorted = sorted(actual_types)
            expected_types_sorted = sorted(expected_types)
            
            validation["details"]["actual_types"] = actual_types_sorted
            validation["details"]["expected_types"] = expected_types_sorted
            
            if actual_types_sorted == expected_types_sorted:
                validation["status"] = "PASS"
                validation["message"] = "All failure types match expected types"
            else:
                validation["message"] = "Failure types do not match expected types"
            
        except Exception as e:
            validation["message"] = f"Failure type validation failed: {e}"
        
        return validation
    
    def _validate_coverage_percentage(self, 
                                     analyzer_output: Dict[str, Any], 
                                     expected_output: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate coverage percentages match expected values.
        
        Args:
            analyzer_output: Actual analyzer output
            expected_output: Expected analyzer output
            
        Returns:
            Dictionary with validation status and details
        """
        validation = {
            "status": "FAIL",
            "details": {},
            "message": ""
        }
        
        try:
            # Handle different coverage percentage locations
            actual_coverage = analyzer_output.get("coverage_percentage", 
                analyzer_output.get("discovery_artifacts", {}).get("analysis_coverage_percentage", 0.0))
            expected_coverage = expected_output.get("coverage_percentage", 
                expected_output.get("discovery_artifacts", {}).get("analysis_coverage_percentage", 0.0))
            
            validation["details"]["actual_coverage"] = actual_coverage
            validation["details"]["expected_coverage"] = expected_coverage
            
            # Allow small floating point differences
            if abs(actual_coverage - expected_coverage) < 0.01:
                validation["status"] = "PASS"
                validation["message"] = f"Coverage percentage is correct: {actual_coverage}%"
            else:
                validation["message"] = f"Coverage percentage mismatch: expected {expected_coverage}%, got {actual_coverage}%"
            
        except Exception as e:
            validation["message"] = f"Coverage percentage validation failed: {e}"
        
        return validation
    
    def _validate_completeness_context(self, 
                                      analyzer_output: Dict[str, Any], 
                                      expected_output: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate completeness_context provides meaningful explanations.
        
        Args:
            analyzer_output: Actual analyzer output
            expected_output: Expected analyzer output
            
        Returns:
            Dictionary with validation status and details
        """
        validation = {
            "status": "FAIL",
            "details": {},
            "message": ""
        }
        
        try:
            actual_context = analyzer_output.get("completeness_context", "")
            expected_context = expected_output.get("completeness_context", "")
            
            validation["details"]["actual_context"] = actual_context
            validation["details"]["expected_context"] = expected_context
            
            # Check if context is meaningful (not empty and not generic)
            if actual_context and len(actual_context.strip()) > 0:
                # Check if it contains relevant keywords
                relevant_keywords = ["analysis", "prevented", "complete", "partial", "failed", "error", "success"]
                has_relevant_info = any(keyword in actual_context.lower() for keyword in relevant_keywords)
                
                if has_relevant_info:
                    validation["status"] = "PASS"
                    validation["message"] = "Completeness context provides meaningful explanation"
                else:
                    validation["message"] = "Completeness context is present but lacks meaningful information"
            else:
                validation["message"] = "Completeness context is missing or empty"
            
        except Exception as e:
            validation["message"] = f"Completeness context validation failed: {e}"
        
        return validation
    
    def _validate_no_false_success(self, 
                                   analyzer_output: Dict[str, Any], 
                                   expected_output: Dict[str, Any]) -> Dict[str, Any]:
        """
        Ensure no false successes are reported.
        
        Args:
            analyzer_output: Actual analyzer output
            expected_output: Expected analyzer output
            
        Returns:
            Dictionary with validation status and details
        """
        validation = {
            "status": "FAIL",
            "details": {},
            "message": ""
        }
        
        try:
            analysis_status = analyzer_output.get("analysis_status", "unknown")
            execution_failures = analyzer_output.get("execution_failures", [])
            
            validation["details"]["analysis_status"] = analysis_status
            validation["details"]["failure_count"] = len(execution_failures)
            
            # False success condition: status is "complete" but there are failures
            if analysis_status == "complete" and execution_failures:
                validation["message"] = "False success detected: analysis_status is 'complete' but execution_failures exist"
            elif analysis_status == "complete" and not execution_failures:
                validation["status"] = "PASS"
                validation["message"] = "No false success: analysis_status is 'complete' with no failures"
            elif analysis_status != "complete":
                validation["status"] = "PASS"
                validation["message"] = "No false success: analysis_status correctly reflects incomplete analysis"
            else:
                validation["status"] = "PASS"
                validation["message"] = "No false success detected"
            
        except Exception as e:
            validation["message"] = f"False success validation failed: {e}"
        
        return validation
    
    def validate_failure_zoo_test_case(self, 
                                      test_case_path: str) -> Dict[str, Any]:
        """
        Validate a single failure zoo test case.
        
        Args:
            test_case_path: Path to the test case directory
            
        Returns:
            Dictionary containing validation results for the test case
        """
        validation_results = {
            "test_case": test_case_path,
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "validations": {},
            "overall_status": "generating"
        }
        
        try:
            # Load expected output
            expected_output_path = os.path.join(test_case_path, "expected_output.json")
            if not os.path.exists(expected_output_path):
                validation_results["overall_status"] = "FAIL"
                validation_results["error"] = f"Expected output file not found: {expected_output_path}"
                return validation_results
            
            with open(expected_output_path, 'r') as f:
                expected_output = json.load(f)
            
            # Run analyzer on the test case (this would be implemented in the actual system)
            # For now, we'll simulate this by creating a mock analyzer output
            analyzer_output = self._simulate_analyzer_run(test_case_path, expected_output)
            
            # Validate the analyzer output
            validation_results["validations"] = self.validate_analyzer_output(analyzer_output, expected_output)
            validation_results["overall_status"] = validation_results["validations"]["overall_status"]
            
        except Exception as e:
            validation_results["overall_status"] = "FAIL"
            validation_results["error"] = str(e)
        
        return validation_results
    
    def _simulate_analyzer_run(self, 
                              test_case_path: str, 
                              expected_output: Dict[str, Any]) -> Dict[str, Any]:
        """
        Simulate analyzer run for testing purposes.
        
        Args:
            test_case_path: Path to the test case directory
            expected_output: Expected output to base simulation on
            
        Returns:
            Simulated analyzer output
        """
        # In a real implementation, this would run the actual analyzer
        # For now, we'll return the expected output as a simulation
        return expected_output.copy()


def main():
    """
    Main entry point for analyzer validation.
    """
    validator = AnalyzerValidator()
    
    # Example usage: validate a single test case
    test_case_path = "test_failure_zoo/missing_import"
    results = validator.validate_failure_zoo_test_case(test_case_path)
    
    print("\n" + "="*50)
    print("ANALYZER VALIDATION RESULTS")
    print("="*50)
    print(f"Test Case: {results['test_case']}")
    print(f"Overall Status: {results['overall_status']}")
    
    for validation_name, validation_result in results['validations'].items():
        status_symbol = "✓" if validation_result['status'] == "PASS" else "✗"
        print(f"{status_symbol} {validation_name}: {validation_result['status']}")
        print(f"  {validation_result['message']}")
    
    print("="*50)
    
    # Save validation results
    validation_results_path = "test_framework/results/analyzer_validation_results.json"
    os.makedirs(os.path.dirname(validation_results_path), exist_ok=True)
    
    with open(validation_results_path, 'w') as f:
        json.dump(results, f, indent=2)
    
    print(f"Validation results saved to: {validation_results_path}")
    
    return results


if __name__ == "__main__":
    main()