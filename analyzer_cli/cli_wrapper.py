"""
Core CLI wrapper logic for the Hybrid Code Analyzer
"""
import sys
import os
import json
import argparse
from typing import Dict, Any, List, Tuple
import logging

# Add analyzer directory to path to import existing modules
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'analyzer'))

from utils import get_current_timestamp, generate_unique_id
from input_handler import validate_and_prepare_inputs
from output_formatter import create_json_output, write_json_output_file
from error_handler import (
    AnalysisError, handle_analysis_error,
    determine_exit_code, run_with_timeout
)
from incremental import (
    should_perform_incremental_analysis,
    create_incremental_analysis_plan,
    merge_analysis_results
)
from guardrails import apply_guardrails

# Import existing analyzer modules
try:
    # Add analyzer directory to path
    analyzer_dir = os.path.join(os.path.dirname(__file__), '..', 'analyzer')
    if analyzer_dir not in sys.path:
        sys.path.append(analyzer_dir)
    
    from analyzer.static_analyzer import StaticAnalyzer
    from analyzer.dynamic_analyzer import DynamicAnalyzer
    from analyzer.improvement_suggester import ImprovementSuggester
    from analyzer.multi_codebase import MultiCodebaseAnalyzer
except ImportError as e:
    logging.error(f"Failed to import analyzer modules: {e}")
    sys.exit(1)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class HybridAnalyzerCLI:
    """Main CLI wrapper for Hybrid Code Analyzer"""
    
    def __init__(self):
        self.static_analyzer = StaticAnalyzer()
        self.dynamic_analyzer = DynamicAnalyzer()
        self.improvement_suggester = ImprovementSuggester()
        self.multi_codebase_analyzer = MultiCodebaseAnalyzer()
    
    def parse_arguments(self) -> Dict[str, Any]:
        """Parse command line arguments"""
        parser = argparse.ArgumentParser(
            description="Hybrid Code Analyzer CLI - Code analysis tool for autonomous agents",
            formatter_class=argparse.RawDescriptionHelpFormatter,
            epilog="""
Examples:
  hybrid_analyzer_cli --paths src/ --output results.json
  hybrid_analyzer_cli --paths file.py --task "memory optimization"
  hybrid_analyzer_cli --paths src/ --changed-files changed.json --previous-output prev_results.json
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
            "--max-file-size",
            type=int,
            default=10,
            help="Maximum file size in MB for analysis (default: 10)"
        )
        
        parser.add_argument(
            "--debug",
            action="store_true",
            help="Enable debug logging"
        )
        
        parser.add_argument(
            "--version",
            action="version",
            version="Hybrid Code Analyzer CLI 1.0.0",
            help="Show version information"
        )
        
        args = parser.parse_args()
        
        # Convert to dict for easier handling
        args_dict = vars(args)
        
        if args.debug:
            logging.getLogger().setLevel(logging.DEBUG)
            logger.debug("Debug logging enabled")
        
        return args_dict
    
    def run_static_analysis(self, file_paths: List[str]) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
        """Run static analysis on specified files"""
        static_results = []
        errors = []
        
        try:
            logger.info(f"Running static analysis on {len(file_paths)} files...")
            
            # The existing static analyzer works with directories, so we need to adapt it
            # For now, we'll analyze each file individually by creating temporary analysis
            
            for file_path in file_paths:
                try:
                    # Check if it's a file or directory
                    if os.path.isfile(file_path):
                        # For single files, we need to analyze the containing directory
                        dir_path = os.path.dirname(file_path)
                        if not dir_path:
                            dir_path = "."
                        
                        # Run analysis on the directory
                        analysis_result = self.static_analyzer.analyze_codebase(dir_path)
                        
                        # Extract results for our specific file
                        formatted_result = self._extract_file_results_from_static_analysis(file_path, analysis_result)
                        if formatted_result:
                            static_results.append(formatted_result)
                    elif os.path.isdir(file_path):
                        # For directories, run full analysis
                        analysis_result = self.static_analyzer.analyze_codebase(file_path)
                        
                        # Extract results for all files in the directory
                        dir_results = self._extract_all_file_results_from_static_analysis(analysis_result)
                        static_results.extend(dir_results)
                    
                except Exception as e:
                    error = handle_analysis_error(e, {"file_path": file_path, "phase": "static_analysis"})
                    errors.append(error)
                    logger.error(f"Static analysis failed for {file_path}: {str(e)}")
        
        except Exception as e:
            error = handle_analysis_error(e, {"phase": "static_analysis"})
            errors.append(error)
        
        return static_results, errors
    
    def _extract_file_results_from_static_analysis(self, file_path: str, analysis_result: Dict[str, Any]) -> Dict[str, Any]:
        """Extract results for a specific file from static analysis result"""
        try:
            # Look for results in semgrep section
            semgrep_results = analysis_result.get("semgrep", {}).get("results", [])
            
            # Filter results for our specific file
            file_semgrep_results = [r for r in semgrep_results if r.get("path") == file_path]
            
            # Look for custom analysis results
            custom_analysis = analysis_result.get("custom_analysis", {})
            
            # Create formatted result
            formatted_result = {
                "file_path": file_path,
                "issues": [],
                "metrics": {}
            }
            
            # Convert semgrep issues
            for issue in file_semgrep_results:
                formatted_result["issues"].append({
                    "type": issue.get("check_id", "semgrep"),
                    "severity": issue.get("severity", "medium"),
                    "message": issue.get("message", ""),
                    "line": issue.get("start", {}).get("line", 0),
                    "column": issue.get("start", {}).get("col", 0),
                    "context": issue.get("extra", {}).get("message", "")
                })
            
            # Add metrics from custom analysis if available
            formatted_result["metrics"] = {
                "complexity": custom_analysis.get("complexity", 0),
                "lines_of_code": custom_analysis.get("lines_of_code", 0),
                "functions": custom_analysis.get("functions", 0),
                "classes": custom_analysis.get("classes", 0),
                "cyclomatic_complexity": custom_analysis.get("cyclomatic_complexity", 0),
                "maintainability_index": custom_analysis.get("maintainability_index", 0)
            }
            
            return formatted_result
            
        except Exception as e:
            logger.error(f"Error extracting file results from static analysis: {str(e)}")
            return None
    
    def _extract_all_file_results_from_static_analysis(self, analysis_result: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Extract results for all files from static analysis result"""
        results = []
        
        try:
            # Get all semgrep results grouped by file
            semgrep_results = analysis_result.get("semgrep", {}).get("results", [])
            
            # Group by file path
            files_in_results = set(r.get("path") for r in semgrep_results if r.get("path"))
            
            for file_path in files_in_results:
                file_result = self._extract_file_results_from_static_analysis(file_path, analysis_result)
                if file_result:
                    results.append(file_result)
            
        except Exception as e:
            logger.error(f"Error extracting all file results from static analysis: {str(e)}")
        
        return results
    
    def run_dynamic_analysis(self, file_paths: List[str], timeout: int) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
        """Run dynamic analysis on specified files"""
        dynamic_results = []
        errors = []
        
        try:
            logger.info(f"Running dynamic analysis on {len(file_paths)} files...")
            
            # The existing dynamic analyzer works with directories and specific file lists
            # We need to adapt it to work with individual files
            
            for file_path in file_paths:
                try:
                    if os.path.isfile(file_path):
                        # For single files, run analysis on that specific file
                        analysis_result = self.dynamic_analyzer.run_dynamic_analysis_with_files(
                            os.path.dirname(file_path) or ".",
                            [file_path]
                        )
                        
                        # Extract results for our specific file
                        file_results = self._extract_file_results_from_dynamic_analysis(file_path, analysis_result)
                        dynamic_results.extend(file_results)
                    elif os.path.isdir(file_path):
                        # For directories, run full analysis
                        analysis_result = self.dynamic_analyzer.run_dynamic_analysis(file_path)
                        
                        # Extract results for all files
                        dir_results = self._extract_all_file_results_from_dynamic_analysis(analysis_result)
                        dynamic_results.extend(dir_results)
                    
                except Exception as e:
                    error = handle_analysis_error(e, {"file_path": file_path, "phase": "dynamic_analysis"})
                    errors.append(error)
                    logger.error(f"Dynamic analysis failed for {file_path}: {str(e)}")
        
        except Exception as e:
            error = handle_analysis_error(e, {"phase": "dynamic_analysis"})
            errors.append(error)
        
        return dynamic_results, errors
    
    def _extract_file_results_from_dynamic_analysis(self, file_path: str, analysis_result: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Extract results for a specific file from dynamic analysis result"""
        results = []
        
        try:
            # Get profiling results for this file
            file_name = os.path.basename(file_path)
            file_profiling = analysis_result.get("profiling_results", {}).get(file_name, {})
            
            if not file_profiling:
                return results
            
            # Process Scalene profiling results
            scalene_results = file_profiling.get("scalene_profiling", {})
            if scalene_results:
                for func_name, func_data in scalene_results.get("functions", {}).items():
                    formatted_result = {
                        "file_id": generate_unique_id("file_"),
                        "function_id": generate_unique_id("func_"),
                        "function_name": func_name,
                        "execution_time": func_data.get("total_time", 0.0),
                        "memory_usage": func_data.get("memory_usage", 0.0),
                        "call_count": func_data.get("call_count", 0),
                        "hotspots": []
                    }
                    
                    # Add hotspots from line-level data
                    for line_num, line_data in func_data.get("lines", {}).items():
                        if line_data.get("time_spent", 0) > 0:
                            formatted_result["hotspots"].append({
                                "line": line_num,
                                "time_spent": line_data.get("time_spent", 0.0),
                                "percentage": line_data.get("percentage", 0.0),
                                "context": line_data.get("context", "")
                            })
                    
                    results.append(formatted_result)
            
            # Process VizTracer results
            viztracer_results = file_profiling.get("viztracer_tracing", {})
            if viztracer_results:
                for func_name, func_data in viztracer_results.get("functions", {}).items():
                    formatted_result = {
                        "file_id": generate_unique_id("file_"),
                        "function_id": generate_unique_id("func_"),
                        "function_name": func_name,
                        "execution_time": func_data.get("execution_time", 0.0),
                        "memory_usage": 0.0,  # VizTracer doesn't provide memory data
                        "call_count": func_data.get("call_count", 0),
                        "hotspots": []
                    }
                    
                    # Add hotspots
                    for hotspot in func_data.get("hotspots", []):
                        formatted_result["hotspots"].append({
                            "line": hotspot.get("line", 0),
                            "time_spent": hotspot.get("time_spent", 0.0),
                            "percentage": hotspot.get("percentage", 0.0),
                            "context": hotspot.get("context", "")
                        })
                    
                    results.append(formatted_result)
            
        except Exception as e:
            logger.error(f"Error extracting file results from dynamic analysis: {str(e)}")
        
        return results
    
    def _extract_all_file_results_from_dynamic_analysis(self, analysis_result: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Extract results for all files from dynamic analysis result"""
        results = []
        
        try:
            profiling_results = analysis_result.get("profiling_results", {})
            
            for file_name, file_data in profiling_results.items():
                # This is a simplified approach - in a real implementation, we'd need to
                # reconstruct the full file path
                file_results = self._extract_file_results_from_dynamic_analysis(file_name, analysis_result)
                results.extend(file_results)
            
        except Exception as e:
            logger.error(f"Error extracting all file results from dynamic analysis: {str(e)}")
        
        return results
    
    def run_ai_analysis(self, static_results: List[Dict[str, Any]], dynamic_results: List[Dict[str, Any]], task: str) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
        """Run AI analysis to generate improvement suggestions"""
        ai_suggestions = []
        errors = []
        
        try:
            logger.info("Running AI analysis for improvement suggestions...")
            
            # Prepare analysis data for AI suggester
            analysis_data = {
                "static_results": static_results,
                "dynamic_results": dynamic_results,
                "task": task
            }
            
            # Use the existing improvement suggester
            suggestions = self.improvement_suggester.generate_suggestions(analysis_data)
            
            # Convert to our expected format
            for suggestion in suggestions:
                ai_suggestions.append({
                    "category": suggestion.get("category", "general"),
                    "severity": suggestion.get("severity", "medium"),
                    "description": suggestion.get("description", ""),
                    "related_files": suggestion.get("related_files", []),
                    "estimated_impact": suggestion.get("estimated_impact", ""),
                    "confidence": suggestion.get("confidence", 0.0),
                    "implementation_difficulty": suggestion.get("implementation_difficulty", "medium")
                })
                
        except Exception as e:
            error = handle_analysis_error(e, {"phase": "ai_analysis"})
            errors.append(error)
        
        return ai_suggestions, errors
    
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
            logger.info("Validating and preparing inputs...")
            input_validation = validate_and_prepare_inputs(args)
            
            if input_validation["errors"]:
                result["errors"] = input_validation["errors"]
                result["exit_code"] = determine_exit_code(input_validation["errors"])
                return result
            
            valid_files = input_validation["valid_files"]
            task = input_validation["task"]
            
            # Step 2: Check if incremental analysis should be performed
            perform_incremental = should_perform_incremental_analysis(args)
            
            if perform_incremental:
                logger.info("Performing incremental analysis...")
                
                # Load previous analysis
                previous_output = args.get("previous_output", "")
                if previous_output:
                    try:
                        with open(previous_output, 'r', encoding='utf-8') as f:
                            previous_analysis = json.load(f)
                    except Exception as e:
                        error = handle_analysis_error(e, {"phase": "loading_previous_analysis"})
                        result["errors"].append(error)
                        previous_analysis = {}
                else:
                    previous_analysis = {}
                
                # Create incremental analysis plan
                analysis_plan = create_incremental_analysis_plan(
                    valid_files,
                    previous_analysis,
                    input_validation["changed_files"]
                )
                
                files_to_analyze = analysis_plan["files_to_analyze"]
                logger.info(f"Analyzing {len(files_to_analyze)} files (skipping {len(analysis_plan['files_to_skip'])} unchanged files)")
                
            else:
                logger.info("Performing full analysis...")
                files_to_analyze = valid_files
            
            # Step 3: Run static analysis
            logger.info("Starting static analysis...")
            static_results, static_errors = self.run_static_analysis(files_to_analyze)
            result["errors"] += static_errors
            
            # Step 4: Run dynamic analysis
            logger.info("Starting dynamic analysis...")
            dynamic_results, dynamic_errors = self.run_dynamic_analysis(files_to_analyze, args["timeout"])
            result["errors"] += dynamic_errors
            
            # Step 5: Run AI analysis
            logger.info("Starting AI analysis...")
            ai_suggestions, ai_errors = self.run_ai_analysis(static_results, dynamic_results, task)
            result["errors"] += ai_errors
            
            # Step 6: Create JSON output
            logger.info("Creating JSON output...")
            json_output = create_json_output(
                static_results,
                dynamic_results,
                ai_suggestions,
                result["errors"],
                args
            )
            
            # Step 7: Apply context guardrails
            logger.info("Applying context guardrails...")
            guarded_output = apply_guardrails(json_output, args["max_context"])
            
            # Step 8: For incremental analysis, merge with previous results
            if perform_incremental and previous_analysis:
                logger.info("Merging with previous analysis results...")
                final_output = merge_analysis_results(guarded_output, previous_analysis, files_to_analyze)
            else:
                final_output = guarded_output
            
            result["output"] = final_output
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
                    logger.info(f"Analysis completed successfully. Results saved to {output_path}")
                else:
                    error = AnalysisError(
                        error_type="output_write_error",
                        message=f"Failed to write output to {output_path}",
                        severity="high"
                    )
                    analysis_result["errors"].append(error.to_dict())
                    analysis_result["exit_code"] = determine_exit_code(analysis_result["errors"])
            
            # Print summary to console
            self.print_analysis_summary(analysis_result)
            
            return analysis_result["exit_code"]
            
        except Exception as e:
            error = handle_analysis_error(e, {"phase": "cli_execution"})
            logger.error(f"CLI execution failed: {error['message']}")
            return determine_exit_code([error])
    
    def print_analysis_summary(self, analysis_result: Dict[str, Any]):
        """Print analysis summary to console"""
        if not analysis_result["success"]:
            logger.error("Analysis completed with errors")
            for error in analysis_result["errors"]:
                logger.error(f"[{error['error_type']}] {error['message']}")
            return
        
        output = analysis_result["output"]
        summary = output.get("summary", {})
        meta = output.get("meta", {})
        
        logger.info("=" * 50)
        logger.info("ANALYSIS SUMMARY")
        logger.info("=" * 50)
        logger.info(f"Timestamp: {meta.get('timestamp', 'N/A')}")
        logger.info(f"Files Analyzed: {summary.get('total_files_analyzed', 0)}")
        logger.info(f"Functions Analyzed: {summary.get('total_functions_analyzed', 0)}")
        logger.info(f"Critical Issues: {summary.get('total_critical_issues', 0)}")
        logger.info(f"High Issues: {summary.get('total_high_issues', 0)}")
        logger.info(f"Medium Issues: {summary.get('total_medium_issues', 0)}")
        logger.info(f"Low Issues: {summary.get('total_low_issues', 0)}")
        logger.info(f"Critical Hotspots: {summary.get('critical_hotspots', 0)}")
        logger.info(f"AI Suggestions: {summary.get('total_ai_suggestions', 0)}")
        logger.info(f"Analysis Completeness: {summary.get('analysis_completeness', 0):.1f}%")
        
        if analysis_result["errors"]:
            logger.warning(f"Completed with {len(analysis_result['errors'])} errors")
        else:
            logger.info("Completed successfully")
        
        logger.info(f"Results saved to: {meta.get('arguments', {}).get('output_file', 'N/A')}")
        logger.info("=" * 50)

def main():
    """Entry point for the CLI"""
    cli = HybridAnalyzerCLI()
    exit_code = cli.run()
    sys.exit(exit_code)

if __name__ == "__main__":
    main()