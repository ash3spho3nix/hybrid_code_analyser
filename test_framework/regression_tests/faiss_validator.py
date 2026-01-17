#!/usr/bin/env python3
"""
FAISS Validator

This module validates FAISS behavior including vector similarity scores,
FAISS ID stability, metadata consistency, error clustering, and index persistence.
"""

import os
import json
import numpy as np
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple
import sys

# Add the project root to Python path to import analyzer modules
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))


class FAISSValidator:
    """
    Validator for FAISS index behavior and similarity scoring.
    
    Responsibilities:
    - Validate vector similarity scores
    - Check FAISS ID stability across runs
    - Verify metadata consistency
    - Validate error clustering behavior
    - Ensure proper index persistence
    """
    
    def __init__(self, results_dir: str = "test_framework/results/regression_results"):
        """
        Initialize the FAISS validator.
        
        Args:
            results_dir: Directory containing test results and FAISS files
        """
        self.results_dir = results_dir
        self.faiss_index_path = os.path.join(results_dir, "faiss_index.faiss")
        self.faiss_metadata_path = os.path.join(results_dir, "faiss_metadata.json")
        self.test_results_path = os.path.join(results_dir, "regression_test_results.json")
        
        # Load test results
        self.test_results = self._load_test_results()
        self.faiss_metadata = self._load_faiss_metadata()
    
    def validate_all(self) -> Dict[str, Any]:
        """
        Run all FAISS validation checks.
        
        Returns:
            Dictionary containing all validation results
        """
        validation_results = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "validations": {}
        }
        
        try:
            # Run individual validation checks
            validation_results["validations"]["vector_stability"] = self.validate_vector_stability()
            validation_results["validations"]["similarity_scores"] = self.validate_similarity_scores()
            validation_results["validations"]["metadata_consistency"] = self.validate_metadata_consistency()
            validation_results["validations"]["error_clustering"] = self.validate_error_clustering()
            validation_results["validations"]["index_persistence"] = self.validate_index_persistence()
            
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
    
    def validate_vector_stability(self) -> Dict[str, Any]:
        """
        Validate that FAISS IDs remain stable across runs.
        
        Returns:
            Dictionary with validation status and details
        """
        validation = {
            "status": "FAIL",
            "details": {},
            "message": ""
        }
        
        try:
            if not self.test_results or len(self.test_results.get("test_runs", [])) < 2:
                validation["message"] = "Insufficient test runs for vector stability validation"
                return validation
            
            run1 = self.test_results["test_runs"][0]
            run2 = self.test_results["test_runs"][1]
            
            # Check if FAISS metadata is available
            if not self.faiss_metadata or "run_1" not in self.faiss_metadata:
                validation["message"] = "FAISS metadata not available for validation"
                return validation
            
            # For this validation, we check that the number of vectors is consistent
            run1_vectors = run1["analysis_results"]["total_failures"]
            run2_vectors = run2["analysis_results"]["total_failures"]
            
            if run1_vectors == run2_vectors:
                validation["status"] = "PASS"
                validation["message"] = f"Vector count stable: {run1_vectors} vectors in both runs"
                validation["details"]["run1_vectors"] = run1_vectors
                validation["details"]["run2_vectors"] = run2_vectors
            else:
                validation["message"] = f"Vector count mismatch: Run1={run1_vectors}, Run2={run2_vectors}"
                validation["details"]["run1_vectors"] = run1_vectors
                validation["details"]["run2_vectors"] = run2_vectors
            
        except Exception as e:
            validation["message"] = f"Vector stability validation failed: {e}"
        
        return validation
    
    def validate_similarity_scores(self) -> Dict[str, Any]:
        """
        Validate FAISS similarity scores meet expected criteria.
        
        Returns:
            Dictionary with validation status and details
        """
        validation = {
            "status": "FAIL",
            "details": {},
            "message": ""
        }
        
        try:
            if not self.test_results or len(self.test_results.get("test_runs", [])) < 2:
                validation["message"] = "Insufficient test runs for similarity validation"
                return validation
            
            run2 = self.test_results["test_runs"][1]
            run3 = self.test_results["test_runs"][2]
            
            # Check Run 2: All similarities should be 1.0 (perfect matches)
            run2_scores = run2["faiss_stats"]["similarity_scores"]
            run2_avg = run2["faiss_stats"]["average_similarity"]
            
            if run2_avg >= 0.99 and all(score >= 0.99 for score in run2_scores):
                run2_status = "PASS"
                run2_message = "All Run 2 similarities are perfect matches (>= 0.99)"
            else:
                run2_status = "FAIL"
                run2_message = f"Run 2 similarity issues: avg={run2_avg}, scores={run2_scores}"
            
            # Check Run 3: Similarities should be > 0.95 for recurring errors
            run3_scores = run3["faiss_stats"]["similarity_scores"]
            run3_avg = run3["faiss_stats"]["average_similarity"]
            
            if run3_avg >= 0.95 and all(score >= 0.95 for score in run3_scores):
                run3_status = "PASS"
                run3_message = "All Run 3 similarities meet threshold (>= 0.95)"
            else:
                run3_status = "FAIL"
                run3_message = f"Run 3 similarity issues: avg={run3_avg}, scores={run3_scores}"
            
            # Overall validation status
            if run2_status == "PASS" and run3_status == "PASS":
                validation["status"] = "PASS"
                validation["message"] = "All similarity scores meet expected criteria"
            else:
                validation["message"] = "Some similarity scores do not meet criteria"
            
            validation["details"]["run2"] = {
                "status": run2_status,
                "message": run2_message,
                "average_similarity": run2_avg,
                "scores": run2_scores
            }
            
            validation["details"]["run3"] = {
                "status": run3_status,
                "message": run3_message,
                "average_similarity": run3_avg,
                "scores": run3_scores
            }
            
        except Exception as e:
            validation["message"] = f"Similarity validation failed: {e}"
        
        return validation
    
    def validate_metadata_consistency(self) -> Dict[str, Any]:
        """
        Validate FAISS metadata consistency across runs.
        
        Returns:
            Dictionary with validation status and details
        """
        validation = {
            "status": "FAIL",
            "details": {},
            "message": ""
        }
        
        try:
            if not self.faiss_metadata:
                validation["message"] = "No FAISS metadata available"
                return validation
            
            # Check if metadata has expected structure
            if "run_1" in self.faiss_metadata:
                run1_meta = self.faiss_metadata["run_1"]
                
                if "index_stats" in run1_meta and "vectors" in run1_meta:
                    validation["status"] = "PASS"
                    validation["message"] = "FAISS metadata has correct structure"
                    validation["details"]["vector_count"] = run1_meta["index_stats"]["total_vectors"]
                    validation["details"]["has_vectors"] = len(run1_meta["vectors"]) > 0
                else:
                    validation["message"] = "FAISS metadata missing required fields"
            else:
                validation["message"] = "FAISS metadata missing run_1 data"
            
        except Exception as e:
            validation["message"] = f"Metadata validation failed: {e}"
        
        return validation
    
    def validate_error_clustering(self) -> Dict[str, Any]:
        """
        Validate error clustering behavior.
        
        Returns:
            Dictionary with validation status and details
        """
        validation = {
            "status": "FAIL",
            "details": {},
            "message": ""
        }
        
        try:
            if not self.test_results or len(self.test_results.get("test_runs", [])) < 3:
                validation["message"] = "Insufficient test runs for clustering validation"
                return validation
            
            run1 = self.test_results["test_runs"][0]
            run2 = self.test_results["test_runs"][1]
            run3 = self.test_results["test_runs"][2]
            
            # Run 2 validation: All errors should be recurring
            run2_recurring = run2["faiss_stats"]["recurring_errors"]
            run2_new = run2["faiss_stats"]["new_errors"]
            run2_total = run2["analysis_results"]["total_failures"]
            
            if run2_recurring == run2_total and run2_new == 0:
                run2_status = "PASS"
                run2_message = f"Run 2: All {run2_total} errors correctly identified as recurring"
            else:
                run2_status = "FAIL"
                run2_message = f"Run 2: Expected all {run2_total} errors to be recurring, got {run2_recurring}"
            
            # Run 3 validation: Should have 6 recurring, 1 resolved, 0 new
            run3_recurring = run3["faiss_stats"]["recurring_errors"]
            run3_new = run3["faiss_stats"]["new_errors"]
            run3_resolved = run3["faiss_stats"]["resolved_errors"]
            run3_total = run3["analysis_results"]["total_failures"]
            
            expected_recurring = 6
            expected_resolved = 1
            expected_new = 0
            
            if (run3_recurring == expected_recurring and 
                run3_resolved == expected_resolved and 
                run3_new == expected_new):
                run3_status = "PASS"
                run3_message = f"Run 3: Correct clustering - {run3_recurring} recurring, {run3_resolved} resolved, {run3_new} new"
            else:
                run3_status = "FAIL"
                run3_message = (f"Run 3: Expected {expected_recurring} recurring, {expected_resolved} resolved, "
                               f"{expected_new} new. Got {run3_recurring}, {run3_resolved}, {run3_new}")
            
            # Overall validation status
            if run2_status == "PASS" and run3_status == "PASS":
                validation["status"] = "PASS"
                validation["message"] = "Error clustering behavior is correct"
            else:
                validation["message"] = "Error clustering has issues"
            
            validation["details"]["run2"] = {
                "status": run2_status,
                "message": run2_message,
                "recurring_errors": run2_recurring,
                "new_errors": run2_new,
                "total_failures": run2_total
            }
            
            validation["details"]["run3"] = {
                "status": run3_status,
                "message": run3_message,
                "recurring_errors": run3_recurring,
                "new_errors": run3_new,
                "resolved_errors": run3_resolved,
                "total_failures": run3_total
            }
            
        except Exception as e:
            validation["message"] = f"Error clustering validation failed: {e}"
        
        return validation
    
    def validate_index_persistence(self) -> Dict[str, Any]:
        """
        Validate FAISS index persistence.
        
        Returns:
            Dictionary with validation status and details
        """
        validation = {
            "status": "FAIL",
            "details": {},
            "message": ""
        }
        
        try:
            # Check if FAISS index file exists
            index_exists = os.path.exists(self.faiss_index_path)
            metadata_exists = os.path.exists(self.faiss_metadata_path)
            
            if index_exists and metadata_exists:
                validation["status"] = "PASS"
                validation["message"] = "FAISS index and metadata files exist"
                
                # Get file sizes
                index_size = os.path.getsize(self.faiss_index_path)
                metadata_size = os.path.getsize(self.faiss_metadata_path)
                
                validation["details"]["index_file_size"] = index_size
                validation["details"]["metadata_file_size"] = metadata_size
                validation["details"]["index_file_path"] = self.faiss_index_path
                validation["details"]["metadata_file_path"] = self.faiss_metadata_path
            else:
                validation["message"] = "FAISS index or metadata files missing"
                validation["details"]["index_exists"] = index_exists
                validation["details"]["metadata_exists"] = metadata_exists
            
        except Exception as e:
            validation["message"] = f"Index persistence validation failed: {e}"
        
        return validation
    
    def _load_test_results(self) -> Optional[Dict[str, Any]]:
        """
        Load test results from file.
        
        Returns:
            Dictionary containing test results, or None if not found
        """
        try:
            if os.path.exists(self.test_results_path):
                with open(self.test_results_path, 'r') as f:
                    return json.load(f)
            return None
        except Exception as e:
            print(f"Warning: Could not load test results: {e}")
            return None
    
    def _load_faiss_metadata(self) -> Optional[Dict[str, Any]]:
        """
        Load FAISS metadata from file.
        
        Returns:
            Dictionary containing FAISS metadata, or None if not found
        """
        try:
            if os.path.exists(self.faiss_metadata_path):
                with open(self.faiss_metadata_path, 'r') as f:
                    return json.load(f)
            return None
        except Exception as e:
            print(f"Warning: Could not load FAISS metadata: {e}")
            return None


def main():
    """
    Main entry point for FAISS validation.
    """
    validator = FAISSValidator()
    results = validator.validate_all()
    
    print("\n" + "="*50)
    print("FAISS VALIDATION RESULTS")
    print("="*50)
    print(f"Overall Status: {results['overall_status']}")
    
    for validation_name, validation_result in results['validations'].items():
        status_symbol = "✓" if validation_result['status'] == "PASS" else "✗"
        print(f"{status_symbol} {validation_name}: {validation_result['status']}")
        print(f"  {validation_result['message']}")
    
    print("="*50)
    
    # Save validation results
    validation_results_path = os.path.join(validator.results_dir, "faiss_validation_results.json")
    with open(validation_results_path, 'w') as f:
        json.dump(results, f, indent=2)
    
    print(f"Validation results saved to: {validation_results_path}")
    
    return results


if __name__ == "__main__":
    main()