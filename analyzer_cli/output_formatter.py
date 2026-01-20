"""
JSON output formatting for the Hybrid Code Analyzer CLI
"""
import json
from typing import Dict, Any, List
from datetime import datetime
from utils import generate_unique_id, get_current_timestamp
import logging

# Configure logging
logger = logging.getLogger(__name__)

def format_static_analysis_results(static_results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Format static analysis results for JSON output"""
    formatted_results = []
    
    for result in static_results:
        try:
            file_id = generate_unique_id("file_")
            
            formatted_result = {
                "file_id": file_id,
                "file_path": result.get("file_path", ""),
                "issues": [],
                "metrics": {}
            }
            
            # Format issues
            for issue in result.get("issues", []):
                formatted_issue = {
                    "issue_id": generate_unique_id("issue_"),
                    "type": issue.get("type", "unknown"),
                    "severity": issue.get("severity", "medium"),
                    "message": issue.get("message", ""),
                    "line": issue.get("line", 0),
                    "column": issue.get("column", 0),
                    "context": issue.get("context", "")
                }
                formatted_result["issues"].append(formatted_issue)
            
            # Format metrics
            metrics = result.get("metrics", {})
            formatted_result["metrics"] = {
                "complexity": metrics.get("complexity", 0),
                "lines_of_code": metrics.get("lines_of_code", 0),
                "functions": metrics.get("functions", 0),
                "classes": metrics.get("classes", 0),
                "cyclomatic_complexity": metrics.get("cyclomatic_complexity", 0),
                "maintainability_index": metrics.get("maintainability_index", 0)
            }
            
            formatted_results.append(formatted_result)
            
        except Exception as e:
            logger.error(f"Error formatting static result: {str(e)}")
            continue
    
    return formatted_results

def format_dynamic_analysis_results(dynamic_results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Format dynamic analysis results for JSON output"""
    formatted_results = []
    
    for result in dynamic_results:
        try:
            function_id = generate_unique_id("func_")
            
            formatted_result = {
                "function_id": function_id,
                "file_id": result.get("file_id", ""),
                "function_name": result.get("function_name", ""),
                "execution_time": result.get("execution_time", 0.0),
                "memory_usage": result.get("memory_usage", 0.0),
                "call_count": result.get("call_count", 0),
                "hotspots": []
            }
            
            # Format hotspots
            for hotspot in result.get("hotspots", []):
                formatted_hotspot = {
                    "hotspot_id": generate_unique_id("hotspot_"),
                    "line": hotspot.get("line", 0),
                    "time_spent": hotspot.get("time_spent", 0.0),
                    "percentage": hotspot.get("percentage", 0.0),
                    "context": hotspot.get("context", "")
                }
                formatted_result["hotspots"].append(formatted_hotspot)
            
            formatted_results.append(formatted_result)
            
        except Exception as e:
            logger.error(f"Error formatting dynamic result: {str(e)}")
            continue
    
    return formatted_results

def format_ai_suggestions(ai_suggestions: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Format AI suggestions for JSON output"""
    formatted_suggestions = []
    
    for suggestion in ai_suggestions:
        try:
            suggestion_id = generate_unique_id("suggestion_")
            
            formatted_suggestion = {
                "id": suggestion_id,
                "category": suggestion.get("category", "general"),
                "severity": suggestion.get("severity", "medium"),
                "description": suggestion.get("description", ""),
                "related_files": suggestion.get("related_files", []),
                "estimated_impact": suggestion.get("estimated_impact", ""),
                "confidence": suggestion.get("confidence", 0.0),
                "implementation_difficulty": suggestion.get("implementation_difficulty", "medium")
            }
            
            formatted_suggestions.append(formatted_suggestion)
            
        except Exception as e:
            logger.error(f"Error formatting AI suggestion: {str(e)}")
            continue
    
    return formatted_suggestions

def create_summary_section(
    static_results: List[Dict[str, Any]], 
    dynamic_results: List[Dict[str, Any]],
    ai_suggestions: List[Dict[str, Any]],
    errors: List[Dict[str, Any]]
) -> Dict[str, Any]:
    """Create summary section for JSON output"""
    summary = {
        "total_files_analyzed": len(static_results),
        "total_functions_analyzed": len(dynamic_results),
        "total_ai_suggestions": len(ai_suggestions),
        "total_errors": len(errors),
        "total_warnings": 0,
        "total_critical_issues": 0,
        "total_high_issues": 0,
        "total_medium_issues": 0,
        "total_low_issues": 0,
        "critical_hotspots": 0,
        "analysis_completeness": 100.0
    }
    
    # Count issues by severity
    for result in static_results:
        for issue in result.get("issues", []):
            severity = issue.get("severity", "medium")
            if severity == "critical":
                summary["total_critical_issues"] += 1
            elif severity == "high":
                summary["total_high_issues"] += 1
            elif severity == "medium":
                summary["total_medium_issues"] += 1
            else:
                summary["total_low_issues"] += 1
    
    # Count warnings (medium severity issues)
    summary["total_warnings"] = summary["total_medium_issues"]
    
    # Count critical hotspots
    for result in dynamic_results:
        for hotspot in result.get("hotspots", []):
            if hotspot.get("percentage", 0) > 50:  # Hotspot consuming >50% of function time
                summary["critical_hotspots"] += 1
    
    # Calculate analysis completeness
    total_files = summary["total_files_analyzed"]
    if total_files > 0:
        files_with_issues = sum(1 for result in static_results if result.get("issues"))
        summary["analysis_completeness"] = min(100.0, (files_with_issues / total_files) * 100)
    
    return summary

def create_meta_section(args: Dict[str, Any]) -> Dict[str, Any]:
    """Create meta section for JSON output"""
    meta = {
        "timestamp": get_current_timestamp(),
        "analyzer_version": "1.0.0",
        "cli_version": "1.0.0",
        "arguments": {
            "paths": args.get("paths", []),
            "task": args.get("task", ""),
            "timeout": args.get("timeout", 180),
            "max_context": args.get("max_context", 1000),
            "output_file": args.get("output_file", "analysis_results.json"),
            "changed_files": args.get("changed_files", "")
        }
    }
    
    return meta

def create_json_output(
    static_results: List[Dict[str, Any]],
    dynamic_results: List[Dict[str, Any]],
    ai_suggestions: List[Dict[str, Any]],
    errors: List[Dict[str, Any]],
    args: Dict[str, Any]
) -> Dict[str, Any]:
    """Create complete JSON output structure"""
    output = {
        "static_results": format_static_analysis_results(static_results),
        "dynamic_results": format_dynamic_analysis_results(dynamic_results),
        "AI_suggestions": format_ai_suggestions(ai_suggestions),
        "summary": create_summary_section(static_results, dynamic_results, ai_suggestions, errors),
        "meta": create_meta_section(args),
        "errors": errors
    }
    
    return output

def apply_context_guardrails(output: Dict[str, Any], max_context: int = 1000) -> Dict[str, Any]:
    """Apply context guardrails to limit output size"""
    # Count total issues
    total_issues = 0
    for result in output.get("static_results", []):
        total_issues += len(result.get("issues", []))
    
    total_hotspots = 0
    for result in output.get("dynamic_results", []):
        total_hotspots += len(result.get("hotspots", []))
    
    total_suggestions = len(output.get("AI_suggestions", []))
    
    # If we exceed context limits, create overflow indicators
    if total_issues + total_hotspots + total_suggestions > max_context:
        overflow_info = {
            "context_overflow": True,
            "total_issues": total_issues,
            "total_hotspots": total_hotspots,
            "total_suggestions": total_suggestions,
            "max_context": max_context,
            "message": f"Context exceeds maximum of {max_context} items. Consider increasing max_context or analyzing smaller codebase."
        }
        
        # Add overflow info to meta
        if "meta" in output:
            output["meta"]["overflow_info"] = overflow_info
        
        # Limit the number of items in each section
        max_items_per_section = max_context // 3
        
        # Limit static results
        for result in output.get("static_results", []):
            if len(result.get("issues", [])) > max_items_per_section:
                result["issues"] = result["issues"][:max_items_per_section]
                result["issues_overflow"] = len(result.get("issues_original", [])) - max_items_per_section
        
        # Limit dynamic results
        for result in output.get("dynamic_results", []):
            if len(result.get("hotspots", [])) > max_items_per_section:
                result["hotspots"] = result["hotspots"][:max_items_per_section]
                result["hotspots_overflow"] = len(result.get("hotspots_original", [])) - max_items_per_section
        
        # Limit AI suggestions
        if len(output.get("AI_suggestions", [])) > max_items_per_section:
            output["AI_suggestions"] = output["AI_suggestions"][:max_items_per_section]
            output["suggestions_overflow"] = len(output.get("AI_suggestions_original", [])) - max_items_per_section
    
    return output

def write_json_output_file(output: Dict[str, Any], output_path: str) -> bool:
    """Write JSON output to file"""
    try:
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(output, f, indent=2, ensure_ascii=False)
        return True
    except Exception as e:
        logger.error(f"Error writing JSON output to {output_path}: {str(e)}")
        return False