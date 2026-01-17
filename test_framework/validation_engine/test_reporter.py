#!/usr/bin/env python3
"""
Test Reporter

This module aggregates results from all test components, generates comprehensive
JSON report in exact format from design, creates human-readable summary with
pass/fail status, provides detailed metrics and statistics, and includes
component-level status tracking.
"""

import os
import json
import sys
from datetime import datetime
from typing import Dict, List, Any, Optional

# Add the project root to Python path to import analyzer modules
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))


class TestReporter:
    """
    Generator for comprehensive test reports.
    
    Responsibilities:
    - Aggregate results from all test components
    - Generate comprehensive JSON report in exact format from design
    - Create human-readable summary with pass/fail status
    - Provide detailed metrics and statistics
    - Include component-level status tracking
    """
    
    def __init__(self, results_dir: str = "test_framework/results"):
        """
        Initialize the test reporter.
        
        Args:
            results_dir: Directory containing test results
        """
        self.results_dir = results_dir
        self.report_data = {
            "report_name": "Comprehensive Test Framework Report",
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "test_components": [],
            "summary": {},
            "metrics": {},
            "status": "generating"
        }
    
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
            self._collect_failure_zoo_results()
            self._collect_regression_test_results()
            self._collect_analyzer_validation_results()
            self._collect_faiss_validation_results()
            
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
    
    def _collect_failure_zoo_results(self):
        """
        Collect failure zoo test results.
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
                
                self.report_data["test_components"].append({
                    "component": "failure_zoo",
                    "type": "test_execution",
                    "results": failure_zoo_results,
                    "status": failure_zoo_results.get("summary", {}).get("overall_status", "unknown")
                })
                
                print("✓ Failure zoo results collected")
            else:
                print("⚠ Failure zoo results not found")
            
        except Exception as e:
            print(f"⚠ Could not collect failure zoo results: {e}")
    
    def _collect_regression_test_results(self):
        """
        Collect regression test results.
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
    
    def _collect_analyzer_validation_results(self):
        """
        Collect analyzer validation results.
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
                
                self.report_data["test_components"].append({
                    "component": "analyzer_validation",
                    "type": "validation",
                    "results": analyzer_validation_results,
                    "status": analyzer_validation_results.get("overall_status", "unknown")
                })
                
                print("✓ Analyzer validation results collected")
            else:
                print("⚠ Analyzer validation results not found")
            
        except Exception as e:
            print(f"⚠ Could not collect analyzer validation results: {e}")
    
    def _collect_faiss_validation_results(self):
        """
        Collect FAISS validation results.
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
                
                self.report_data["test_components"].append({
                    "component": "faiss_validation",
                    "type": "validation",
                    "results": faiss_validation_results,
                    "status": faiss_validation_results.get("overall_status", "unknown")
                })
                
                print("✓ FAISS validation results collected")
            else:
                print("⚠ FAISS validation results not found")
            
        except Exception as e:
            print(f"⚠ Could not collect FAISS validation results: {e}")
    
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
        
        # Extract metrics from failure zoo if available
        failure_zoo_component = self._find_component("failure_zoo")
        if failure_zoo_component:
            failure_zoo_results = failure_zoo_component["results"]
            if "summary" in failure_zoo_results:
                metrics["failure_zoo"] = {
                    "total_tests": failure_zoo_results["summary"].get("total_tests", 0),
                    "passed_tests": failure_zoo_results["summary"].get("passed_tests", 0),
                    "failed_tests": failure_zoo_results["summary"].get("failed_tests", 0),
                    "overall_status": failure_zoo_results["summary"].get("overall_status", "unknown")
                }
        
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
        
        # Extract metrics from analyzer validation if available
        analyzer_component = self._find_component("analyzer_validation")
        if analyzer_component:
            analyzer_results = analyzer_component["results"]
            if "validations" in analyzer_results:
                metrics["analyzer_validation"] = {}
                for validation_name, validation_result in analyzer_results["validations"].items():
                    metrics["analyzer_validation"][validation_name] = validation_result["status"]
        
        # Extract metrics from FAISS validation if available
        faiss_component = self._find_component("faiss_validation")
        if faiss_component:
            faiss_results = faiss_component["results"]
            if "validations" in faiss_results:
                metrics["faiss_validation"] = {}
                for validation_name, validation_result in faiss_results["validations"].items():
                    metrics["faiss_validation"][validation_name] = validation_result["status"]
        
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
            comprehensive_report_path = os.path.join(self.results_dir, "comprehensive_report.json")
            
            with open(comprehensive_report_path, 'w') as f:
                json.dump(self.report_data, f, indent=2)
            
            print(f"✓ Comprehensive report saved to: {comprehensive_report_path}")
            
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
        summary_lines.append("COMPREHENSIVE TEST FRAMEWORK REPORT SUMMARY")
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
            
            # Failure zoo metrics
            if "failure_zoo" in self.report_data["metrics"]:
                fz_metrics = self.report_data["metrics"]["failure_zoo"]
                summary_lines.append(f"  Failure Zoo Tests: {fz_metrics.get('total_tests', 0)} total, {fz_metrics.get('passed_tests', 0)} passed, {fz_metrics.get('failed_tests', 0)} failed")
                summary_lines.append(f"  Failure Zoo Status: {fz_metrics.get('overall_status', 'unknown')}")
            
            # Regression test metrics
            if "regression_tests" in self.report_data["metrics"]:
                reg_metrics = self.report_data["metrics"]["regression_tests"]
                summary_lines.append(f"  Regression Failures (Run 1): {reg_metrics.get('total_failures_run1', 0)}")
                summary_lines.append(f"  Regression Failures (Run 2): {reg_metrics.get('total_failures_run2', 0)}")
                summary_lines.append(f"  Regression Failures (Run 3): {reg_metrics.get('total_failures_run3', 0)}")
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


def main():
    """
    Main entry point for test reporting.
    """
    # Create test reporter instance
    reporter = TestReporter()
    
    print("Test Reporter")
    print("=" * 50)
    print(f"Results Directory: {reporter.results_dir}")
    print("=" * 50)
    
    try:
        # Generate comprehensive report
        report = reporter.generate_comprehensive_report()
        
        # Print human-readable summary
        print("\n")
        reporter.print_human_readable_summary()
        
        print("\n" + "=" * 50)
        print("REPORT GENERATION COMPLETED")
        print("=" * 50)
        print(f"Overall Status: {report['summary']['overall_status']}")
        print(f"Report saved to: {os.path.join(reporter.results_dir, 'comprehensive_report.json')}")
        print("=" * 50)
        
        return 0
        
    except Exception as e:
        print(f"\nReport generation failed: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())