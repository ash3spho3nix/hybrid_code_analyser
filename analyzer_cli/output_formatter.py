"""
JSON output formatting for the Hybrid Code Analyzer CLI
"""
import json
import os
import ast
from typing import Dict, Any, List, Optional
from datetime import datetime
from utils import generate_unique_id, get_current_timestamp
import logging

# Configure logging
logger = logging.getLogger(__name__)

# Standard severity scale for consistency across all analysis types
STANDARD_SEVERITY_SCALE = ["critical", "high", "medium", "low"]

# Mapping from analyzer severity levels to standard scale
SEVERITY_MAPPING = {
    "INFO": "low",
    "WARNING": "medium",
    "ERROR": "high",
    "CRITICAL": "critical",
    "info": "low",
    "warning": "medium",
    "error": "high",
    "critical": "critical"
}


def extract_symbols_from_file(file_path: str) -> Dict[str, Any]:
    """Extract symbols (functions, classes, methods) from a Python file using AST"""
    symbols = {
        'functions': [],
        'classes': [],
        'methods': []
    }
    
    try:
        if not os.path.exists(file_path):
            return symbols
            
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        try:
            tree = ast.parse(content)
        except SyntaxError:
            logger.warning(f"Syntax error parsing {file_path} for symbol extraction")
            return symbols
        
        # Extract symbols using AST visitor
        class SymbolVisitor(ast.NodeVisitor):
            def __init__(self):
                self.current_class = None
                self.namespace = []
                
            def visit_FunctionDef(self, node):
                if self.current_class:
                    # This is a method
                    method_info = {
                        'name': node.name,
                        'line': node.lineno,
                        'class': self.current_class,
                        'fqn': f"{'.'.join(self.namespace)}.{self.current_class}.{node.name}"
                    }
                    symbols['methods'].append(method_info)
                else:
                    # This is a function
                    function_info = {
                        'name': node.name,
                        'line': node.lineno,
                        'fqn': f"{'.'.join(self.namespace)}.{node.name}"
                    }
                    symbols['functions'].append(function_info)
                self.generic_visit(node)
                
            def visit_ClassDef(self, node):
                # Track current class for method detection
                old_class = self.current_class
                self.current_class = node.name
                
                # Add class to namespace
                self.namespace.append(node.name)
                
                # Record the class
                class_info = {
                    'name': node.name,
                    'line': node.lineno,
                    'fqn': f"{'.'.join(self.namespace)}"
                }
                symbols['classes'].append(class_info)
                
                self.generic_visit(node)
                
                # Restore previous state
                self.current_class = old_class
                self.namespace.pop()
                
            def visit_AsyncFunctionDef(self, node):
                # Handle async functions/methods
                if self.current_class:
                    method_info = {
                        'name': node.name,
                        'line': node.lineno,
                        'class': self.current_class,
                        'fqn': f"{'.'.join(self.namespace)}.{self.current_class}.{node.name}",
                        'async': True
                    }
                    symbols['methods'].append(method_info)
                else:
                    function_info = {
                        'name': node.name,
                        'line': node.lineno,
                        'fqn': f"{'.'.join(self.namespace)}.{node.name}",
                        'async': True
                    }
                    symbols['functions'].append(function_info)
                self.generic_visit(node)
        
        visitor = SymbolVisitor()
        visitor.visit(tree)
        
    except Exception as e:
        logger.warning(f"Error extracting symbols from {file_path}: {str(e)}")
    
    return symbols


def extract_fqn_from_path(file_path: str, symbol_name: str, symbol_type: str = 'function') -> str:
    """Generate Fully Qualified Name from file path and symbol name"""
    try:
        # Get module path (relative to current directory or project root)
        module_path = os.path.splitext(file_path)[0]
        module_path = module_path.replace(os.sep, '.')
        
        # Clean up the path
        if module_path.startswith('.'):
            module_path = module_path[1:]
            
        # Construct FQN based on symbol type
        if symbol_type == 'class':
            return f"{module_path}.{symbol_name}"
        elif symbol_type == 'method':
            # For methods, we need class context which we don't have here
            # This is a fallback - actual method FQNs should be extracted via AST
            return f"{module_path}.{symbol_name}"
        else:  # function
            return f"{module_path}.{symbol_name}"
            
    except Exception:
        return symbol_name


def get_symbol_context_from_issue(issue: Dict[str, Any], file_path: str) -> Dict[str, Any]:
    """Extract symbol context from issue data"""
    context = {
        'function': None,
        'class': None,
        'method': None,
        'fqn': None
    }
    
    try:
        # Check if issue has direct symbol information
        if 'symbol' in issue:
            context.update(issue['symbol'])
        elif 'function' in issue:
            context['function'] = issue['function']
            context['fqn'] = extract_fqn_from_path(file_path, issue['function'], 'function')
        elif 'class' in issue:
            context['class'] = issue['class']
            context['fqn'] = extract_fqn_from_path(file_path, issue['class'], 'class')
        
    except Exception as e:
        logger.debug(f"Error extracting symbol context from issue: {str(e)}")
    
    return context

def format_static_analysis_results(static_results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Format static analysis results for JSON output with symbol-level mapping"""
    formatted_results = []
    
    for result in static_results:
        try:
            file_id = generate_unique_id("file_")
            file_path = result.get("file_path", "")
            
            # Extract symbols from the file for symbol mapping
            file_symbols = extract_symbols_from_file(file_path)
            
            formatted_result = {
                "file_id": file_id,
                "file_path": file_path,
                "issues": [],
                "metrics": {},
                "symbols": {
                    "functions": file_symbols["functions"],
                    "classes": file_symbols["classes"],
                    "methods": file_symbols["methods"],
                    "total_functions": len(file_symbols["functions"]),
                    "total_classes": len(file_symbols["classes"]),
                    "total_methods": len(file_symbols["methods"])
                }
            }
            
            # Format issues with symbol context
            for issue in result.get("issues", []):
                # Extract symbol context for this issue
                symbol_context = get_symbol_context_from_issue(issue, file_path)
                
                # Try to find the closest symbol to the issue line
                closest_symbol = None
                if issue.get("line", 0) > 0:
                    # Find closest function/method to this line
                    all_symbols = file_symbols["functions"] + file_symbols["methods"]
                    for symbol in all_symbols:
                        if symbol["line"] <= issue["line"]:
                            if closest_symbol is None or symbol["line"] > closest_symbol["line"]:
                                closest_symbol = symbol
                
                # Standardize severity using mapping
                raw_severity = issue.get("severity", "medium")
                standardized_severity = SEVERITY_MAPPING.get(raw_severity, "medium")
                
                formatted_issue = {
                    "issue_id": generate_unique_id("issue_"),
                    "type": issue.get("type", "unknown"),
                    "severity": standardized_severity,
                    "raw_severity": raw_severity,  # Preserve original for reference
                    "message": issue.get("message", ""),
                    "line": issue.get("line", 0),
                    "column": issue.get("column", 0),
                    "context": issue.get("context", ""),
                    "symbol_context": {
                        "function": symbol_context.get("function") or (closest_symbol["name"] if closest_symbol and closest_symbol.get("class") is None else None),
                        "class": symbol_context.get("class") or (closest_symbol["class"] if closest_symbol and closest_symbol.get("class") else None),
                        "method": symbol_context.get("method") or (closest_symbol["name"] if closest_symbol and closest_symbol.get("class") else None),
                        "fqn": symbol_context.get("fqn") or (closest_symbol["fqn"] if closest_symbol else None),
                        "symbol_type": "method" if closest_symbol and closest_symbol.get("class") else ("function" if closest_symbol else None)
                    }
                }
                formatted_result["issues"].append(formatted_issue)
            
            # Format metrics with symbol information
            metrics = result.get("metrics", {})
            formatted_result["metrics"] = {
                "complexity": metrics.get("complexity", 0),
                "lines_of_code": metrics.get("lines_of_code", 0),
                "functions": metrics.get("functions", len(file_symbols["functions"])),
                "classes": metrics.get("classes", len(file_symbols["classes"])),
                "methods": metrics.get("methods", len(file_symbols["methods"])),
                "cyclomatic_complexity": metrics.get("cyclomatic_complexity", 0),
                "maintainability_index": metrics.get("maintainability_index", 0),
                "symbol_density": {
                    "functions_per_kilo_loc": len(file_symbols["functions"]) / max(1, metrics.get("lines_of_code", 1) / 1000),
                    "classes_per_kilo_loc": len(file_symbols["classes"]) / max(1, metrics.get("lines_of_code", 1) / 1000),
                    "methods_per_class": len(file_symbols["methods"]) / max(1, len(file_symbols["classes"]))
                }
            }
            
            formatted_results.append(formatted_result)
            
        except Exception as e:
            logger.error(f"Error formatting static result: {str(e)}")
            continue
    
    return formatted_results

def format_dynamic_analysis_results(dynamic_results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Format dynamic analysis results for JSON output with class/method context and FQN support"""
    formatted_results = []
    
    # Group results by file to optimize symbol extraction
    results_by_file = {}
    for result in dynamic_results:
        file_id = result.get("file_id", "")
        if file_id not in results_by_file:
            results_by_file[file_id] = []
        results_by_file[file_id].append(result)
    
    # Process each file's results with symbol context
    for file_id, file_results in results_by_file.items():
        try:
            # Extract file path from the first result (assuming all results for same file have same path)
            file_path = ""
            if file_results and hasattr(file_results[0], 'get'):
                # Check if file_id is actually a file path or if we need to map it
                if os.path.exists(file_id):
                    file_path = file_id
                else:
                    # Try to find file path from result metadata
                    file_path = file_results[0].get("file_path", file_id)
            
            # Extract symbols from the file for context mapping
            file_symbols = extract_symbols_from_file(file_path) if file_path else {
                'functions': [], 'classes': [], 'methods': []
            }
            
            # Create FQN mapping for functions and methods
            fqn_mapping = {}
            for func in file_symbols["functions"]:
                fqn_mapping[func["name"]] = func["fqn"]
            for method in file_symbols["methods"]:
                fqn_mapping[method["name"]] = method["fqn"]
            
            # Process each function result with enhanced context
            for result in file_results:
                try:
                    function_id = generate_unique_id("func_")
                    function_name = result.get("function_name", "")
                    
                    # Determine symbol type and context
                    symbol_info = None
                    symbol_type = "function"
                    class_context = None
                    
                    # Check if this is a method by looking at the symbols
                    for method in file_symbols["methods"]:
                        if method["name"] == function_name:
                            symbol_info = method
                            symbol_type = "method"
                            class_context = method.get("class")
                            break
                    
                    # If not found as method, check if it's a function
                    if symbol_info is None:
                        for func in file_symbols["functions"]:
                            if func["name"] == function_name:
                                symbol_info = func
                                symbol_type = "function"
                                break
                    
                    # Generate FQN
                    fqn = fqn_mapping.get(function_name, extract_fqn_from_path(file_path, function_name, symbol_type))
                    
                    # Get severity from result or assign default
                    raw_severity = result.get("severity", "medium")
                    standardized_severity = SEVERITY_MAPPING.get(raw_severity, "medium")
                    
                    formatted_result = {
                        "function_id": function_id,
                        "file_id": result.get("file_id", file_id),
                        "function_name": function_name,
                        "execution_time": result.get("execution_time", 0.0),
                        "memory_usage": result.get("memory_usage", 0.0),
                        "call_count": result.get("call_count", 0),
                        "severity": standardized_severity,
                        "raw_severity": raw_severity,  # Preserve original for reference
                        "hotspots": [],
                        "symbol_context": {
                            "symbol_type": symbol_type,
                            "class_context": class_context,
                            "fqn": fqn,
                            "line_number": symbol_info["line"] if symbol_info else None,
                            "is_async": symbol_info.get("async", False) if symbol_info else False
                        }
                    }
                    
                    # Format hotspots with enhanced context
                    for hotspot in result.get("hotspots", []):
                        # Try to find symbol context for hotspot line
                        hotspot_symbol = None
                        hotspot_line = hotspot.get("line", 0)
                        
                        if hotspot_line > 0:
                            # Find closest symbol to this hotspot line
                            all_symbols = file_symbols["functions"] + file_symbols["methods"]
                            for symbol in all_symbols:
                                if symbol["line"] <= hotspot_line:
                                    if hotspot_symbol is None or symbol["line"] > hotspot_symbol["line"]:
                                        hotspot_symbol = symbol
                        
                        hotspot_fqn = None
                        hotspot_symbol_type = None
                        if hotspot_symbol:
                            hotspot_fqn = hotspot_symbol["fqn"]
                            hotspot_symbol_type = "method" if hotspot_symbol.get("class") else "function"
                        
                        formatted_hotspot = {
                            "hotspot_id": generate_unique_id("hotspot_"),
                            "line": hotspot.get("line", 0),
                            "time_spent": hotspot.get("time_spent", 0.0),
                            "percentage": hotspot.get("percentage", 0.0),
                            "context": hotspot.get("context", ""),
                            "symbol_context": {
                                "symbol_type": hotspot_symbol_type,
                                "fqn": hotspot_fqn,
                                "function": hotspot_symbol["name"] if hotspot_symbol and not hotspot_symbol.get("class") else None,
                                "method": hotspot_symbol["name"] if hotspot_symbol and hotspot_symbol.get("class") else None,
                                "class": hotspot_symbol["class"] if hotspot_symbol and hotspot_symbol.get("class") else None
                            }
                        }
                        formatted_result["hotspots"].append(formatted_hotspot)
                    
                    formatted_results.append(formatted_result)
                    
                except Exception as e:
                    logger.error(f"Error formatting dynamic result for {function_name}: {str(e)}")
                    continue
                    
        except Exception as e:
            logger.error(f"Error processing file {file_id} for dynamic results: {str(e)}")
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
    
    # Count issues by severity (using standardized severity)
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
    
    # Count dynamic analysis issues by severity
    for result in dynamic_results:
        # Check function-level severity
        func_severity = result.get("severity", "medium")
        if func_severity == "critical":
            summary["total_critical_issues"] += 1
        elif func_severity == "high":
            summary["total_high_issues"] += 1
        elif func_severity == "medium":
            summary["total_medium_issues"] += 1
        else:
            summary["total_low_issues"] += 1
        
        # Check hotspot severity
        for hotspot in result.get("hotspots", []):
            # Hotspot severity can be inferred from percentage
            if hotspot.get("percentage", 0) > 50:
                summary["total_high_issues"] += 1
            elif hotspot.get("percentage", 0) > 30:
                summary["total_medium_issues"] += 1
    
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