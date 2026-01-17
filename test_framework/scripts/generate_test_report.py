#!/usr/bin/env python3
"""
Test Report Generator

This script aggregates all test results, generates comprehensive JSON report,
creates human-readable summary, provides pass/fail status, and includes
detailed metrics as specified in the test architecture design.
"""

import os
import sys
import json
import argparse
from datetime import datetime
from typing import Dict, Any, List

# Add the project root to Python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))


class TestReportGenerator:
    """
    Generator for comprehensive test reports.
    
    Responsibilities:
    - Aggregate all test results
    - Generate comprehensive JSON report
    - Create human-readable summary
    - Provide pass/fail status
    - Include detailed metrics
    """
    
    def __init__(self):
        """
        Initialize the report generator.
        """
        self.report_data = {
            "report_name": "Comprehensive Test Report",
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "test_components": [],
            "summary": {},
            "metrics": {},
            "status": "generating"
        }
        
        # Default paths
        self.results_dir = "test_framework/results"
        self.regression_results_dir = os.path.join(self.results_dir, "regression_results")
        self.comprehensive_report_path = os.path.join(self.results_dir, "comprehensive_report.json")
    
    def generate_comprehensive_report(self) -> Dict[str, Any]:
        """
        Generate comprehensive test report by aggregating all available results.
        
        Returns:
            Complete report dictionary
        """
        print("Generating Comprehensive Test Report...")
        print("=" * 50)
        
        try:
            # Collect all available test results
            self._collect_regression_test_results()
            self._collect_validation_results()
            self._collect_similarity_results()
            
            # Generate summary and metrics
            self._generate_summary()
            self._generate_metrics()
            
            # Finalize report
            self.report_data["status"] = "completed"
            
            # Save report
            self._save_report()
            
            print("Comprehensive report generation completed successfully.")
            return self.report_data
            
        except Exception as e:
            self.report_data["status"] = "failed"
            self.report_data["error"] = str(e)
            print(f"Report generation failed: {e}")
            raise
    
    def _collect_regression_test_results(self):
        """
        Collect regression test results.
        """
        try:
            # Look for regression test results
            regression_results_path = os.path.join(
                self.regression_results_dir, 
                "regression_test_results.json"
            )
            
            if os.path.exists(regression_results_path):
                with open(regression_results_path, 'r') as f:
                    regression_results = json.load(f)
                
                self.report_data["test_components"].append({
                    "component": "regression_tests",
                    "type": "test_execution",
                    "results": regression_results,
                    "status": regression_results.get("summary", {}).get("overall_status", "unknown")
                })
                
                print("✓ Regression test results collected")
            else:
                print("⚠ Regression test results not found")
            
        except Exception as e:
            print(f"⚠ Could not collect regression test results: {e}")
    
    def _collect_validation_results(self):
        """
        Collect FAISS validation results.
        """
        try:
            # Look for FAISS validation results
            validation_results_path = os.path.join(
                self.regression_results_dir, 
                "faiss_validation_results.json"
            )
            
            if os.path.exists(validation_results_path):
                with open(validation_results_path, 'r') as f:
                    validation_results = json.load(f)
                
                self.report_data["test_components"].append({
                    "component": "faiss_validation",
                    "type": "validation",
                    "results": validation_results,
                    "status": validation_results.get("overall_status", "unknown")
                })
                
                print("✓ FAISS validation results collected")
            else:
                print("⚠ FAISS validation results not found")
            
        except Exception as e:
            print(f"⚠ Could not collect validation results: {e}")
    
    def _collect_similarity_results(self):
        """
        Collect similarity scoring results.
        """
        try:
            # Look for similarity report
            similarity_results_path = os.path.join(
                self.regression_results_dir, 
                "similarity_report_example.json"
            )
            
            if os.path.exists(similarity_results_path):
                with open(similarity_results_path, 'r') as f:
                    similarity_results = json.load(f)
                
                self.report_data["test_components"].append({
                    "component": "similarity_scorer",
                    "type": "analysis",
                    "results": similarity_results,
                    "status": "completed"  # Similarity scorer doesn't have pass/fail status
                })
                
                print("✓ Similarity scoring results collected")
            else:
                print("⚠ Similarity scoring results not found")
            
        except Exception as e:
            print(f"⚠ Could not collect similarity results: {e}")
    
    def _generate_summary(self):
        """
        Generate comprehensive summary of all test results.
        """
        summary = {
            "total_components": len(self.report_data["test_components"]),
            "passed_components": 0,
            "failed_components": 0,
            "component_statuses": {}
        }
        
        # Analyze each component
        for component in self.report_data["test_components"]:
            component_name = component["component"]
            component_status = component["status"]
            
            summary["component_statuses"][component_name] = component_status
            
            if component_status == "PASS":
                summary["passed_components"] += 1
            elif component_status == "FAIL":
                summary["failed_components"] += 1
        
        # Determine overall status
        if summary["failed_components"] == 0 and summary["total_components"] > 0:
            summary["overall_status"] = "PASS"
        elif summary["passed_components"] == 0:
            summary["overall_status"] = "FAIL"
        else:
            summary["overall_status"] = "PARTIAL"
        
        self.report_data["summary"] = summary
    
    def _generate_metrics(self):
        """
        Generate detailed metrics from test results.
        """
        metrics = {}
        
        # Extract metrics from regression tests if available
        regression_component = self._find_component("regression_tests")
        if regression_component:
            regression_results = regression_component["results"]
            if "summary" in regression_results:
                metrics["regression_tests"] = {
                    "total_failures_run1": regression_results["summary"].get("total_failures_run1", 0),
                    "total_failures_run2": regression_results["summary"].get("total_failures_run2", 0),
                    "total_failures_run3": regression_results["summary"].get("total_failures_run3", 0),
                    "failures_resolved": regression_results["summary"].get("failures_resolved", 0),
                    "recurring_errors_run2": regression_results["summary"].get("recurring_errors_run2", 0),
                    "recurring_errors_run3": regression_results["summary"].get("recurring_errors_run3", 0),
                    "faiss_behavior": regression_results["summary"].get("faiss_behavior", "unknown"),
                    "vector_stability": regression_results["summary"].get("vector_stability", "unknown"),
                    "similarity_detection": regression_results["summary"].get("similarity_detection", "unknown"),
                    "error_clustering": regression_results["summary"].get("error_clustering", "unknown")
                }
        
        # Extract metrics from FAISS validation if available
        validation_component = self._find_component("faiss_validation")
        if validation_component:
            validation_results = validation_component["results"]
            if "validations" in validation_results:
                metrics["faiss_validation"] = {}
                for validation_name, validation_result in validation_results["validations"].items():
                    metrics["faiss_validation"][validation_name] = validation_result["status"]
        
        # Extract metrics from similarity scorer if available
        similarity_component = self._find_component("similarity_scorer")
        if similarity_component:
            similarity_results = similarity_component["results"]
            if "statistics" in similarity_results:
                metrics["similarity_scorer"] = {
                    "average_similarity": similarity_results["statistics"].get("average_similarity", 0.0),
                    "min_similarity": similarity_results["statistics"].get("min_similarity", 0.0),
                    "max_similarity": similarity_results["statistics"].get("max_similarity", 0.0),
                    "median_similarity": similarity_results["statistics"].get("median_similarity", 0.0),
                    "recurring_errors": similarity_results["summary"].get("recurring", 0),
                    "new_errors": similarity_results["summary"].get("new", 0),
                    "resolved_errors": similarity_results["summary"].get("resolved", 0)
                }
        
        self.report_data["metrics"] = metrics
    
    def _find_component(self, component_name: str) -> Optional[Dict[str, Any]]:
        """
        Find a component in the report data.
        
        Args:
            component_name: Name of component to find
            
        Returns:
            Component dictionary or None if not found
        """
        for component in self.report_data["test_components"]:
            if component["component"] == component_name:
                return component
        return None
    
    def _save_report(self):
        """
        Save the comprehensive report to file.
        """
        try:
            # Save to comprehensive report path
            with open(self.comprehensive_report_path, 'w') as f:
                json.dump(self.report_data, f, indent=2)
            
            print(f"✓ Comprehensive report saved to: {self.comprehensive_report_path}")
            
            # Also save a copy in regression results directory
            regression_report_path = os.path.join(
                self.regression_results_dir, 
                "comprehensive_report_copy.json"
            )
            
            with open(regression_report_path, 'w') as f:
                json.dump(self.report_data, f, indent=2)
            
            print(f"✓ Report copy saved to: {regression_report_path}")
            
        except Exception as e:
            print(f"⚠ Could not save report: {e}")
            raise
    
    def generate_human_readable_summary(self) -> str:
        """
        Generate human-readable summary of test results.
        
        Returns:
            Human-readable summary string
        """
        summary_lines = []
        summary_lines.append("=" * 60)
        summary_lines.append("COMPREHENSIVE TEST REPORT SUMMARY")
        summary_lines.append("=" * 60)
        
        # Add timestamp
        summary_lines.append(f"Generated: {self.report_data['timestamp']}")
        summary_lines.append("")
        
        # Add overall status
        overall_status = self.report_data["summary"].get("overall_status", "unknown")
        status_color = "🟢" if overall_status == "PASS" else "🔴" if overall_status == "FAIL" else "🟡"
        summary_lines.append(f"Overall Status: {status_color} {overall_status}")
        summary_lines.append("")
        
        # Add component statuses
        summary_lines.append("Component Statuses:")
        for component_name, component_status in self.report_data["summary"]["component_statuses"].items():
            status_color = "🟢" if component_status == "PASS" else "🔴" if component_status == "FAIL" else "🟡"
            summary_lines.append(f"  {status_color} {component_name}: {component_status}")
        
        summary_lines.append("")
        
        # Add metrics if available
        if "metrics" in self.report_data and self.report_data["metrics"]:
            summary_lines.append("Key Metrics:")
            
            # Regression test metrics
            if "regression_tests" in self.report_data["metrics"]:
                reg_metrics = self.report_data["metrics"]["regression_tests"]
                summary_lines.append(f"  Failures (Run 1): {reg_metrics.get('total_failures_run1', 0)}")
                summary_lines.append(f"  Failures (Run 2): {reg_metrics.get('total_failures_run2', 0)}")
                summary_lines.append(f"  Failures (Run 3): {reg_metrics.get('total_failures_run3', 0)}")
                summary_lines.append(f"  Failures Resolved: {reg_metrics.get('failures_resolved', 0)}")
                summary_lines.append(f"  FAISS Behavior: {reg_metrics.get('faiss_behavior', 'unknown')}")
                summary_lines.append(f"  Vector Stability: {reg_metrics.get('vector_stability', 'unknown')}")
                summary_lines.append(f"  Error Clustering: {reg_metrics.get('error_clustering', 'unknown')}")
            
            summary_lines.append("")
        
        # Add statistics
        summary_lines.append("Statistics:")
        summary_lines.append(f"  Total Components: {self.report_data['summary']['total_components']}")
        summary_lines.append(f"  Passed Components: {self.report_data['summary']['passed_components']}")
        summary_lines.append(f"  Failed Components: {self.report_data['summary']['failed_components']}")
        
        summary_lines.append("=" * 60)
        
        return "\n".join(summary_lines)
    
    def print_human_readable_summary(self):
        """
        Print human-readable summary to console.
        """
        summary = self.generate_human_readable_summary()
        print(summary)


def parse_arguments() -> argparse.Namespace:
    """
    Parse command line arguments.
    
    Returns:
        Parsed arguments namespace
    """
    parser = argparse.ArgumentParser(
        description="Test Report Generator - Creates comprehensive test reports"
    )
    
    parser.add_argument(
        "--results-dir",
        type=str,
        default="test_framework/results",
        help="Directory containing test results (default: test_framework/results)"
    )
    
    parser.add_argument(
        "--output",
        type=str,
        default="test_framework/results/comprehensive_report.json",
        help="Output path for comprehensive report (default: test_framework/results/comprehensive_report.json)"
    )
    
    parser.add_argument(
        "--human-readable",
        action="store_true",
        help="Print human-readable summary to console"
    )
    
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Enable verbose output"
    )
    
    return parser.parse_args()


def main():
    """
    Main entry point for test report generation.
    """
    # Parse command line arguments
    args = parse_arguments()
    
    print("Test Report Generator")
    print("=" * 50)
    print(f"Results Directory: {args.results_dir}")
    print(f"Output Path: {args.output}")
    print("=" * 50)
    
    # Create and configure report generator
    generator = TestReportGenerator()
    generator.results_dir = args.results_dir
    generator.comprehensive_report_path = args.output
    
    try:
        # Generate comprehensive report
        report = generator.generate_comprehensive_report()
        
        # Print human-readable summary if requested
        if args.human_readable:
            print("\n")
            generator.print_human_readable_summary()
        
        print("\n" + "=" * 50)
        print("REPORT GENERATION COMPLETED")
        print("=" * 50)
        print(f"Overall Status: {report['summary']['overall_status']}")
        print(f"Report saved to: {args.output}")
        print("=" * 50)
        
        return 0
        
    except Exception as e:
        print(f"\nReport generation failed: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())