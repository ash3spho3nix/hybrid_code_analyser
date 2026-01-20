#!/usr/bin/env python3
"""
Working version of Hybrid Code Analyzer CLI
This version demonstrates the CLI functionality without requiring complex analyzer integration
"""

import sys
import os
import argparse
import json
from typing import Dict, Any, List, Tuple

# Add the analyzer_cli directory to Python path
cli_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'analyzer_cli')
sys.path.insert(0, cli_dir)

# Import CLI components
from utils import get_current_timestamp, generate_unique_id
from input_handler import validate_and_prepare_inputs
from output_formatter import create_json_output, write_json_output_file
from error_handler import AnalysisError, handle_analysis_error, determine_exit_code
from guardrails import apply_guardrails
from incremental import should_perform_incremental_analysis

class HybridAnalyzerCLI:
    """Simplified CLI wrapper for testing"""
    
    def __init__(self):
        pass
    
    def parse_arguments(self) -> Dict[str, Any]:
        """Parse command line arguments"""
        parser = argparse.ArgumentParser(
            description="Hybrid Code Analyzer CLI - Code analysis tool for autonomous agents",
            formatter_class=argparse.RawDescriptionHelpFormatter,
            epilog="""
Examples:
  hybrid_analyzer_cli_working --paths test_sample.py --output results.json
  hybrid_analyzer_cli_working --paths . --task "memory optimization"
  hybrid_analyzer_cli_working --paths src/ --changed-files changed.json
            """
        )
        
        parser.add_argument(
            "--paths",
            nargs="+",
            required=True,
            help="File paths or directories to analyze"
        )
        
        parser.add_argument(
            "--output",
            default="analysis_results.json",
            help="Output JSON file path (default: analysis_results.json)"
        )
        
        parser.add_argument(
            "--task",
            default="",
            help="Task description for AI analysis (e.g., 'memory optimization')"
        )
        
        parser.add_argument(
            "--timeout",
            type=int,
            default=180,
            help="Timeout in seconds for dynamic analysis (default: 180)"
        )
        
        parser.add_argument(
            "--max-context",
            type=int,
            default=1000,
            help="Maximum number of context items in output (default: 1000)"
        )
        
        parser.add_argument(
            "--changed-files",
            default="",
            help="JSON file containing list of changed files for incremental analysis"
        )
        
        parser.add_argument(
            "--previous-output",
            default="",
            help="Previous analysis output JSON for incremental analysis"
        )
        
        parser.add_argument(
            "--debug",
            action="store_true",
            help="Enable debug logging"
        )
        
        args = parser.parse_args()
        return vars(args)
    
    def run_mock_analysis(self, file_paths: List[str], task: str) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]], List[Dict[str, Any]]]:
        """Run mock analysis for testing purposes"""
        static_results = []
        dynamic_results = []
        ai_suggestions = []
        
        # Create mock static analysis results
        for file_path in file_paths:
            if os.path.isfile(file_path):
                static_results.append({
                    "file_path": file_path,
                    "issues": [
                        {
                            "type": "code_quality",
                            "severity": "medium",
                            "message": "Function is too complex",
                            "line": 10,
                            "column": 5,
                            "context": "def calculate_factorial(n):"
                        },
                        {
                            "type": "performance",
                            "severity": "low",
                            "message": "Consider using list comprehension",
                            "line": 25,
                            "column": 12,
                            "context": "for num in range(2, limit + 1):"
                        }
                    ],
                    "metrics": {
                        "complexity": 8.5,
                        "lines_of_code": 42,
                        "functions": 3,
                        "classes": 0,
                        "cyclomatic_complexity": 5,
                        "maintainability_index": 75.2
                    }
                })
        
        # Create mock dynamic analysis results
        for file_path in file_paths:
            if os.path.isfile(file_path):
                dynamic_results.append({
                    "file_id": generate_unique_id("file_"),
                    "function_id": generate_unique_id("func_"),
                    "function_name": "calculate_factorial",
                    "execution_time": 0.45,
                    "memory_usage": 128.7,
                    "call_count": 5,
                    "hotspots": [
                        {
                            "line": 15,
                            "time_spent": 0.32,
                            "percentage": 71.1,
                            "context": "return n * calculate_factorial(n - 1)"
                        }
                    ]
                })
        
        # Create mock AI suggestions
        ai_suggestions.append({
            "category": "performance",
            "severity": "medium",
            "description": "Consider using memoization for recursive functions",
            "related_files": [generate_unique_id("file_")],
            "estimated_impact": "30% performance improvement",
            "confidence": 0.85,
            "implementation_difficulty": "medium"
        })
        
        return static_results, dynamic_results, ai_suggestions
    
    def run_analysis(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Run complete analysis workflow"""
        result = {
            "success": False,
            "output": {},
            "errors": [],
            "exit_code": 1
        }
        
        try:
            # Step 1: Validate and prepare inputs
            input_validation = validate_and_prepare_inputs(args)
            
            if input_validation["errors"]:
                result["errors"] = input_validation["errors"]
                result["exit_code"] = determine_exit_code(input_validation["errors"])
                return result
            
            valid_files = input_validation["valid_files"]
            task = input_validation["task"]
            
            # Step 2: Run mock analysis (replace with real analysis in production)
            static_results, dynamic_results, ai_suggestions = self.run_mock_analysis(valid_files, task)
            
            # Step 3: Create JSON output
            json_output = create_json_output(
                static_results,
                dynamic_results,
                ai_suggestions,
                result["errors"],
                args
            )
            
            # Step 4: Apply context guardrails
            guarded_output = apply_guardrails(json_output, args["max_context"])
            
            result["output"] = guarded_output
            result["success"] = True
            result["exit_code"] = determine_exit_code(result["errors"])
            
        except Exception as e:
            error = handle_analysis_error(e, {"phase": "analysis_workflow"})
            result["errors"].append(error)
            result["exit_code"] = determine_exit_code(result["errors"])
        
        return result
    
    def run(self) -> int:
        """Main entry point for CLI"""
        try:
            # Parse arguments
            args = self.parse_arguments()
            
            # Run analysis
            analysis_result = self.run_analysis(args)
            
            # Write output to file
            if analysis_result["success"] and analysis_result["output"]:
                output_path = args["output"]
                success = write_json_output_file(analysis_result["output"], output_path)
                
                if success:
                    print(f"Analysis completed successfully. Results saved to {output_path}")
                else:
                    error = AnalysisError(
                        error_type="output_write_error",
                        message=f"Failed to write output to {output_path}",
                        severity="high"
                    )
                    analysis_result["errors"].append(error.to_dict())
                    analysis_result["exit_code"] = determine_exit_code(analysis_result["errors"])
            
            # Print summary
            self.print_analysis_summary(analysis_result)
            
            return analysis_result["exit_code"]
            
        except Exception as e:
            error = handle_analysis_error(e, {"phase": "cli_execution"})
            print(f"CLI execution failed: {error['message']}")
            return determine_exit_code([error])
    
    def print_analysis_summary(self, analysis_result: Dict[str, Any]):
        """Print analysis summary to console"""
        if not analysis_result["success"]:
            print("Analysis completed with errors:")
            for error in analysis_result["errors"]:
                print(f"[{error['error_type']}] {error['message']}")
            return
        
        output = analysis_result["output"]
        summary = output.get("summary", {})
        meta = output.get("meta", {})
        
        print("=" * 60)
        print("HYBRID CODE ANALYZER - ANALYSIS SUMMARY")
        print("=" * 60)
        print(f"Timestamp: {meta.get('timestamp', 'N/A')}")
        print(f"Files Analyzed: {summary.get('total_files_analyzed', 0)}")
        print(f"Functions Analyzed: {summary.get('total_functions_analyzed', 0)}")
        print(f"Critical Issues: {summary.get('total_critical_issues', 0)}")
        print(f"High Issues: {summary.get('total_high_issues', 0)}")
        print(f"Medium Issues: {summary.get('total_medium_issues', 0)}")
        print(f"Low Issues: {summary.get('total_low_issues', 0)}")
        print(f"Critical Hotspots: {summary.get('critical_hotspots', 0)}")
        print(f"AI Suggestions: {summary.get('total_ai_suggestions', 0)}")
        print(f"Analysis Completeness: {summary.get('analysis_completeness', 0):.1f}%")
        
        if analysis_result["errors"]:
            print(f"\nCompleted with {len(analysis_result['errors'])} warnings/errors")
        else:
            print("\nCompleted successfully")
        
        print(f"Results saved to: {meta.get('arguments', {}).get('output_file', 'N/A')}")
        print("=" * 60)

def main():
    """Entry point for the CLI"""
    cli = HybridAnalyzerCLI()
    exit_code = cli.run()
    sys.exit(exit_code)

if __name__ == "__main__":
    main()