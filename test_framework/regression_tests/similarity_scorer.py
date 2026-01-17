#!/usr/bin/env python3
"""
Similarity Scorer

This module calculates cosine similarity between error vectors and determines
"same error" vs "new error" based on threshold (0.95). It handles recurring
errors, resolved errors, and new error identification.
"""

import os
import json
import numpy as np
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple
from sklearn.metrics.pairwise import cosine_similarity
import sys

# Add the project root to Python path to import analyzer modules
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))


class SimilarityScorer:
    """
    Similarity scorer for error clustering and classification.
    
    Responsibilities:
    - Calculate cosine similarity between error vectors
    - Determine "same error" vs "new error" based on threshold (0.95)
    - Identify recurring errors
    - Detect resolved errors
    - Handle new error identification
    """
    
    def __init__(self, similarity_threshold: float = 0.95):
        """
        Initialize the similarity scorer.
        
        Args:
            similarity_threshold: Threshold for considering errors as "same" (default: 0.95)
        """
        self.similarity_threshold = similarity_threshold
    
    def calculate_similarity_matrix(self, vectors1: List[np.ndarray], vectors2: List[np.ndarray]) -> np.ndarray:
        """
        Calculate cosine similarity matrix between two sets of vectors.
        
        Args:
            vectors1: First set of vectors
            vectors2: Second set of vectors
            
        Returns:
            Similarity matrix where similarity_matrix[i][j] is the similarity
            between vectors1[i] and vectors2[j]
        """
        if not vectors1 or not vectors2:
            return np.array([])
            
        # Convert to numpy arrays if needed
        array1 = np.array(vectors1)
        array2 = np.array(vectors2)
        
        # Reshape to 2D arrays if needed
        if array1.ndim == 1:
            array1 = array1.reshape(1, -1)
        if array2.ndim == 1:
            array2 = array2.reshape(1, -1)
        
        # Calculate cosine similarity
        similarity_matrix = cosine_similarity(array1, array2)
        
        return similarity_matrix
    
    def classify_errors(self, 
                      current_errors: List[Dict[str, Any]], 
                      previous_errors: List[Dict[str, Any]],
                      current_vectors: Optional[List[np.ndarray]] = None,
                      previous_vectors: Optional[List[np.ndarray]] = None) -> Dict[str, Any]:
        """
        Classify errors into recurring, new, and resolved categories.
        
        Args:
            current_errors: List of current error dictionaries
            previous_errors: List of previous error dictionaries
            current_vectors: Optional list of current error vectors
            previous_vectors: Optional list of previous error vectors
            
        Returns:
            Dictionary containing classification results
        """
        classification = {
            "recurring_errors": [],
            "new_errors": [],
            "resolved_errors": [],
            "similarity_scores": [],
            "classification_summary": {}
        }
        
        # If no previous errors, all current errors are new
        if not previous_errors:
            classification["new_errors"] = current_errors
            classification["classification_summary"]["recurring"] = 0
            classification["classification_summary"]["new"] = len(current_errors)
            classification["classification_summary"]["resolved"] = 0
            return classification
        
        # If no current errors, all previous errors are resolved
        if not current_errors:
            classification["resolved_errors"] = previous_errors
            classification["classification_summary"]["recurring"] = 0
            classification["classification_summary"]["new"] = 0
            classification["classification_summary"]["resolved"] = len(previous_errors)
            return classification
        
        # Use vector-based classification if vectors are provided
        if current_vectors and previous_vectors:
            return self._classify_with_vectors(current_errors, previous_errors, current_vectors, previous_vectors)
        else:
            # Fallback to metadata-based classification
            return self._classify_with_metadata(current_errors, previous_errors)
    
    def _classify_with_vectors(self, 
                             current_errors: List[Dict[str, Any]], 
                             previous_errors: List[Dict[str, Any]],
                             current_vectors: List[np.ndarray],
                             previous_vectors: List[np.ndarray]) -> Dict[str, Any]:
        """
        Classify errors using vector similarity.
        
        Args:
            current_errors: List of current error dictionaries
            previous_errors: List of previous error dictionaries
            current_vectors: List of current error vectors
            previous_vectors: List of previous error vectors
            
        Returns:
            Dictionary containing classification results
        """
        classification = {
            "recurring_errors": [],
            "new_errors": [],
            "resolved_errors": [],
            "similarity_scores": [],
            "classification_summary": {}
        }
        
        # Calculate similarity matrix
        similarity_matrix = self.calculate_similarity_matrix(current_vectors, previous_vectors)
        
        # Track which previous errors have been matched
        matched_previous_indices = set()
        
        # Classify each current error
        for i, current_error in enumerate(current_errors):
            current_error_id = current_error.get("error_id", f"current_{i}")
            
            # Find best match among previous errors
            best_match_index = -1
            best_similarity = -1
            
            for j, previous_error in enumerate(previous_errors):
                if j in matched_previous_indices:
                    continue
                
                similarity = similarity_matrix[i][j] if similarity_matrix.size > 0 else 0.0
                
                if similarity > best_similarity:
                    best_similarity = similarity
                    best_match_index = j
            
            # Store similarity score
            classification["similarity_scores"].append(best_similarity)
            
            # Classify based on similarity threshold
            if best_similarity >= self.similarity_threshold:
                # This is a recurring error
                matched_error = previous_errors[best_match_index]
                matched_error_id = matched_error.get("error_id", f"previous_{best_match_index}")
                
                # Add metadata to both errors
                current_error["similarity_score"] = best_similarity
                current_error["matched_error_id"] = matched_error_id
                current_error["classification"] = "recurring"
                
                matched_error["similarity_score"] = best_similarity
                matched_error["matched_error_id"] = current_error_id
                matched_error["classification"] = "recurring"
                
                classification["recurring_errors"].append({
                    "current_error": current_error,
                    "previous_error": matched_error,
                    "similarity_score": best_similarity
                })
                
                matched_previous_indices.add(best_match_index)
            else:
                # This is a new error
                current_error["similarity_score"] = best_similarity
                current_error["classification"] = "new"
                classification["new_errors"].append(current_error)
        
        # Identify resolved errors (previous errors not matched)
        for j, previous_error in enumerate(previous_errors):
            if j not in matched_previous_indices:
                previous_error["classification"] = "resolved"
                classification["resolved_errors"].append(previous_error)
        
        # Generate summary
        classification["classification_summary"]["recurring"] = len(classification["recurring_errors"])
        classification["classification_summary"]["new"] = len(classification["new_errors"])
        classification["classification_summary"]["resolved"] = len(classification["resolved_errors"])
        
        return classification
    
    def _classify_with_metadata(self, 
                              current_errors: List[Dict[str, Any]], 
                              previous_errors: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Classify errors using metadata when vectors are not available.
        
        Args:
            current_errors: List of current error dictionaries
            previous_errors: List of previous error dictionaries
            
        Returns:
            Dictionary containing classification results
        """
        classification = {
            "recurring_errors": [],
            "new_errors": [],
            "resolved_errors": [],
            "similarity_scores": [],
            "classification_summary": {}
        }
        
        # Create lookup for previous errors by key characteristics
        previous_error_lookup = {}
        for j, previous_error in enumerate(previous_errors):
            error_key = self._create_error_key(previous_error)
            previous_error_lookup[error_key] = previous_error
        
        # Classify current errors
        for i, current_error in enumerate(current_errors):
            error_key = self._create_error_key(current_error)
            
            if error_key in previous_error_lookup:
                # This is a recurring error
                matched_error = previous_error_lookup[error_key]
                
                # Simulate high similarity score
                similarity_score = 0.98  # High similarity for metadata match
                
                current_error["similarity_score"] = similarity_score
                current_error["matched_error_id"] = matched_error.get("error_id", f"previous_{error_key}")
                current_error["classification"] = "recurring"
                
                matched_error["similarity_score"] = similarity_score
                matched_error["matched_error_id"] = current_error.get("error_id", f"current_{error_key}")
                matched_error["classification"] = "recurring"
                
                classification["recurring_errors"].append({
                    "current_error": current_error,
                    "previous_error": matched_error,
                    "similarity_score": similarity_score
                })
                
                classification["similarity_scores"].append(similarity_score)
                
                # Remove from lookup to prevent duplicate matching
                del previous_error_lookup[error_key]
            else:
                # This is a new error
                current_error["similarity_score"] = 0.0  # No similarity
                current_error["classification"] = "new"
                classification["new_errors"].append(current_error)
                classification["similarity_scores"].append(0.0)
        
        # Remaining previous errors are resolved
        for error_key, previous_error in previous_error_lookup.items():
            previous_error["classification"] = "resolved"
            classification["resolved_errors"].append(previous_error)
        
        # Generate summary
        classification["classification_summary"]["recurring"] = len(classification["recurring_errors"])
        classification["classification_summary"]["new"] = len(classification["new_errors"])
        classification["classification_summary"]["resolved"] = len(classification["resolved_errors"])
        
        return classification
    
    def _create_error_key(self, error: Dict[str, Any]) -> str:
        """
        Create a unique key for an error based on its characteristics.
        
        Args:
            error: Error dictionary
            
        Returns:
            String key representing the error
        """
        # Use key characteristics that define error identity
        failure_type = error.get("failure_type", "unknown")
        message = error.get("message", "")
        file_path = error.get("file_path", "")
        line_number = error.get("line_number", "")
        
        # Create a hashable key
        error_key = f"{failure_type}|{message[:50]}|{file_path}|{line_number}"
        return error_key
    
    def calculate_error_vector(self, error: Dict[str, Any]) -> np.ndarray:
        """
        Calculate a vector representation for an error.
        
        Args:
            error: Error dictionary
            
        Returns:
            Numpy array representing the error vector
        """
        # This is a simplified vectorization for demonstration
        # In a real implementation, this would use proper embedding
        
        # Extract features from error
        failure_type = error.get("failure_type", "")
        severity = error.get("severity", "")
        message = error.get("message", "")
        
        # Create a simple feature vector
        # Note: This is a placeholder - real implementation would use proper embeddings
        features = []
        
        # Add failure type features (one-hot encoding)
        failure_types = ["IMPORT_ERROR", "CIRCULAR_IMPORT", "SYNTAX_ERROR", "RUNTIME_ERROR", "DEPENDENCY_ERROR"]
        for ft in failure_types:
            features.append(1.0 if failure_type == ft else 0.0)
        
        # Add severity features
        severities = ["ERROR", "WARNING", "INFO"]
        for sev in severities:
            features.append(1.0 if severity == sev else 0.0)
        
        # Add message length feature (normalized)
        message_length = min(len(message), 100) / 100.0
        features.append(message_length)
        
        # Convert to numpy array
        error_vector = np.array(features)
        
        return error_vector
    
    def generate_similarity_report(self, 
                                  classification_results: Dict[str, Any],
                                  run_number: int = 1) -> Dict[str, Any]:
        """
        Generate a comprehensive similarity report.
        
        Args:
            classification_results: Results from classify_errors method
            run_number: Run number for reporting
            
        Returns:
            Dictionary containing the similarity report
        """
        report = {
            "run_number": run_number,
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "similarity_threshold": self.similarity_threshold,
            "summary": classification_results["classification_summary"],
            "detailed_results": {
                "recurring_errors": [],
                "new_errors": [],
                "resolved_errors": []
            },
            "statistics": {}
        }
        
        # Process recurring errors
        for recurring in classification_results["recurring_errors"]:
            report["detailed_results"]["recurring_errors"].append({
                "current_error_id": recurring["current_error"].get("error_id", "unknown"),
                "previous_error_id": recurring["previous_error"].get("error_id", "unknown"),
                "similarity_score": recurring["similarity_score"],
                "failure_type": recurring["current_error"].get("failure_type", "unknown"),
                "message": recurring["current_error"].get("message", "")
            })
        
        # Process new errors
        for new_error in classification_results["new_errors"]:
            report["detailed_results"]["new_errors"].append({
                "error_id": new_error.get("error_id", "unknown"),
                "failure_type": new_error.get("failure_type", "unknown"),
                "message": new_error.get("message", ""),
                "similarity_score": new_error.get("similarity_score", 0.0)
            })
        
        # Process resolved errors
        for resolved_error in classification_results["resolved_errors"]:
            report["detailed_results"]["resolved_errors"].append({
                "error_id": resolved_error.get("error_id", "unknown"),
                "failure_type": resolved_error.get("failure_type", "unknown"),
                "message": resolved_error.get("message", ""),
                "previous_similarity_score": resolved_error.get("similarity_score", 1.0)
            })
        
        # Calculate statistics
        similarity_scores = classification_results["similarity_scores"]
        if similarity_scores:
            report["statistics"]["average_similarity"] = float(np.mean(similarity_scores))
            report["statistics"]["min_similarity"] = float(np.min(similarity_scores))
            report["statistics"]["max_similarity"] = float(np.max(similarity_scores))
            report["statistics"]["median_similarity"] = float(np.median(similarity_scores))
        else:
            report["statistics"]["average_similarity"] = 0.0
            report["statistics"]["min_similarity"] = 0.0
            report["statistics"]["max_similarity"] = 0.0
            report["statistics"]["median_similarity"] = 0.0
        
        return report


def main():
    """
    Main entry point for similarity scorer demonstration.
    """
    # Create a similarity scorer instance
    scorer = SimilarityScorer(similarity_threshold=0.95)
    
    # Example error data (simplified for demonstration)
    previous_errors = [
        {
            "error_id": "err_1",
            "failure_type": "IMPORT_ERROR",
            "severity": "ERROR",
            "message": "ModuleNotFoundError: No module named 'non_existent_module'",
            "file_path": "test_missing_import.py",
            "line_number": 1
        },
        {
            "error_id": "err_2", 
            "failure_type": "SYNTAX_ERROR",
            "severity": "ERROR",
            "message": "SyntaxError: unexpected EOF while parsing",
            "file_path": "test_syntax_error.py",
            "line_number": 3
        }
    ]
    
    current_errors = [
        {
            "error_id": "err_1_new",
            "failure_type": "IMPORT_ERROR", 
            "severity": "ERROR",
            "message": "ModuleNotFoundError: No module named 'non_existent_module'",
            "file_path": "test_missing_import.py",
            "line_number": 1
        },
        {
            "error_id": "err_3",
            "failure_type": "RUNTIME_ERROR",
            "severity": "ERROR",
            "message": "ValueError: Test runtime exception",
            "file_path": "test_runtime_exception.py",
            "line_number": 5
        }
    ]
    
    print("Running similarity classification...")
    
    # Classify errors
    classification = scorer.classify_errors(current_errors, previous_errors)
    
    # Generate report
    report = scorer.generate_similarity_report(classification, run_number=2)
    
    print("\n" + "="*50)
    print("SIMILARITY CLASSIFICATION RESULTS")
    print("="*50)
    print(f"Recurring Errors: {report['summary']['recurring']}")
    print(f"New Errors: {report['summary']['new']}")
    print(f"Resolved Errors: {report['summary']['resolved']}")
    print(f"Average Similarity: {report['statistics']['average_similarity']:.3f}")
    print("="*50)
    
    # Save report
    report_path = "test_framework/results/similarity_report_example.json"
    with open(report_path, 'w') as f:
        json.dump(report, f, indent=2)
    
    print(f"Similarity report saved to: {report_path}")
    
    return report


if __name__ == "__main__":
    main()