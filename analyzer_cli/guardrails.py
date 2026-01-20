"""
Context guardrails for the Hybrid Code Analyzer CLI
"""
import json
import gzip
from typing import Dict, Any, List, Tuple
import logging
from utils import get_current_timestamp

# Configure logging
logger = logging.getLogger(__name__)

def limit_output_context(
    output: Dict[str, Any],
    max_issues: int = 1000,
    max_hotspots: int = 500,
    max_suggestions: int = 200
) -> Dict[str, Any]:
    """Limit the number of items in each output section to prevent context overload"""
    limited_output = output.copy()
    overflow_info = {}
    
    # Limit static analysis issues
    if "static_results" in limited_output:
        total_issues_before = 0
        total_issues_after = 0
        
        for result in limited_output["static_results"]:
            issues = result.get("issues", [])
            total_issues_before += len(issues)
            
            if len(issues) > max_issues:
                result["issues"] = issues[:max_issues]
                result["issues_overflow"] = len(issues) - max_issues
                total_issues_after += max_issues
            else:
                total_issues_after += len(issues)
        
        if total_issues_before > max_issues:
            overflow_info["static_issues"] = {
                "before": total_issues_before,
                "after": total_issues_after,
                "limit": max_issues
            }
    
    # Limit dynamic analysis hotspots
    if "dynamic_results" in limited_output:
        total_hotspots_before = 0
        total_hotspots_after = 0
        
        for result in limited_output["dynamic_results"]:
            hotspots = result.get("hotspots", [])
            total_hotspots_before += len(hotspots)
            
            if len(hotspots) > max_hotspots:
                result["hotspots"] = hotspots[:max_hotspots]
                result["hotspots_overflow"] = len(hotspots) - max_hotspots
                total_hotspots_after += max_hotspots
            else:
                total_hotspots_after += len(hotspots)
        
        if total_hotspots_before > max_hotspots:
            overflow_info["dynamic_hotspots"] = {
                "before": total_hotspots_before,
                "after": total_hotspots_after,
                "limit": max_hotspots
            }
    
    # Limit AI suggestions
    if "AI_suggestions" in limited_output:
        suggestions = limited_output["AI_suggestions"]
        if len(suggestions) > max_suggestions:
            limited_output["AI_suggestions"] = suggestions[:max_suggestions]
            overflow_info["ai_suggestions"] = {
                "before": len(suggestions),
                "after": max_suggestions,
                "limit": max_suggestions
            }
    
    # Add overflow info to meta if any limits were applied
    if overflow_info:
        if "meta" not in limited_output:
            limited_output["meta"] = {}
        limited_output["meta"]["overflow_info"] = overflow_info
        limited_output["meta"]["context_limited"] = True
    
    return limited_output

def compress_large_output(
    output: Dict[str, Any],
    size_threshold: int = 1024 * 1024  # 1MB
) -> bytes:
    """Compress large JSON output using gzip"""
    try:
        json_str = json.dumps(output, ensure_ascii=False)
        json_bytes = json_str.encode('utf-8')
        
        if len(json_bytes) > size_threshold:
            return gzip.compress(json_bytes)
        else:
            return json_bytes
    except Exception as e:
        logger.error(f"Error compressing output: {str(e)}")
        return json.dumps({"error": "Failed to compress output"}).encode('utf-8')

def create_overflow_summary(
    output: Dict[str, Any],
    overflow_output_path: str
) -> bool:
    """Create separate summary file for overflow items"""
    try:
        overflow_summary = {
            "timestamp": get_current_timestamp(),
            "overflow_summary": True,
            "original_analysis_file": output.get("meta", {}).get("output_file", "unknown"),
            "overflow_items": {}
        }
        
        # Count overflow items
        if "static_results" in output:
            total_overflow = 0
            for result in output["static_results"]:
                if "issues_overflow" in result:
                    total_overflow += result["issues_overflow"]
            if total_overflow > 0:
                overflow_summary["overflow_items"]["static_issues"] = total_overflow
        
        if "dynamic_results" in output:
            total_overflow = 0
            for result in output["dynamic_results"]:
                if "hotspots_overflow" in result:
                    total_overflow += result["hotspots_overflow"]
            if total_overflow > 0:
                overflow_summary["overflow_items"]["dynamic_hotspots"] = total_overflow
        
        if "AI_suggestions" in output and isinstance(output["AI_suggestions"], list):
            # If suggestions were limited, we can't know the exact overflow without original data
            # This would be handled by the context limiting function
            pass
        
        # Write overflow summary to file
        with open(overflow_output_path, 'w', encoding='utf-8') as f:
            json.dump(overflow_summary, f, indent=2, ensure_ascii=False)
        
        return True
        
    except Exception as e:
        logger.error(f"Error creating overflow summary: {str(e)}")
        return False

def validate_context_size(
    output: Dict[str, Any],
    max_size_mb: int = 5
) -> Tuple[bool, int]:
    """Validate that output context doesn't exceed size limits"""
    try:
        json_str = json.dumps(output, ensure_ascii=False)
        json_bytes = json_str.encode('utf-8')
        size_mb = len(json_bytes) / (1024 * 1024)
        
        if size_mb > max_size_mb:
            return False, size_mb
        else:
            return True, size_mb
    except Exception as e:
        logger.error(f"Error validating context size: {str(e)}")
        return False, 0

def apply_guardrails(
    output: Dict[str, Any],
    max_context: int = 1000,
    max_size_mb: int = 5
) -> Dict[str, Any]:
    """Apply all context guardrails to output"""
    # First, limit the number of items
    limited_output = limit_output_context(
        output,
        max_issues=max_context,
        max_hotspots=max_context // 2,
        max_suggestions=max_context // 5
    )
    
    # Check if output exceeds size limits
    within_limits, size_mb = validate_context_size(limited_output, max_size_mb)
    
    if not within_limits:
        logger.warning(f"Output size {size_mb:.2f}MB exceeds limit of {max_size_mb}MB")
        
        # Add warning to meta
        if "meta" not in limited_output:
            limited_output["meta"] = {}
        limited_output["meta"]["size_warning"] = {
            "current_size_mb": size_mb,
            "max_size_mb": max_size_mb,
            "message": f"Output exceeds recommended size limit. Consider increasing max_size_mb or reducing analysis scope."
        }
    
    return limited_output

def create_context_guardrails_report(
    original_output: Dict[str, Any],
    guarded_output: Dict[str, Any]
) -> Dict[str, Any]:
    """Create report showing what was limited by guardrails"""
    report = {
        "guardrails_applied": False,
        "limitations": {},
        "timestamp": get_current_timestamp()
    }
    
    # Compare static results
    if "static_results" in original_output and "static_results" in guarded_output:
        orig_issues = sum(len(r.get("issues", [])) for r in original_output["static_results"])
        guarded_issues = sum(len(r.get("issues", [])) for r in guarded_output["static_results"])
        
        if guarded_issues < orig_issues:
            report["guardrails_applied"] = True
            report["limitations"]["static_issues"] = {
                "original_count": orig_issues,
                "guarded_count": guarded_issues,
                "reduced_by": orig_issues - guarded_issues
            }
    
    # Compare dynamic results
    if "dynamic_results" in original_output and "dynamic_results" in guarded_output:
        orig_hotspots = sum(len(r.get("hotspots", [])) for r in original_output["dynamic_results"])
        guarded_hotspots = sum(len(r.get("hotspots", [])) for r in guarded_output["dynamic_results"])
        
        if guarded_hotspots < orig_hotspots:
            report["guardrails_applied"] = True
            report["limitations"]["dynamic_hotspots"] = {
                "original_count": orig_hotspots,
                "guarded_count": guarded_hotspots,
                "reduced_by": orig_hotspots - guarded_hotspots
            }
    
    # Compare AI suggestions
    if "AI_suggestions" in original_output and "AI_suggestions" in guarded_output:
        orig_suggestions = len(original_output["AI_suggestions"])
        guarded_suggestions = len(guarded_output["AI_suggestions"])
        
        if guarded_suggestions < orig_suggestions:
            report["guardrails_applied"] = True
            report["limitations"]["ai_suggestions"] = {
                "original_count": orig_suggestions,
                "guarded_count": guarded_suggestions,
                "reduced_by": orig_suggestions - guarded_suggestions
            }
    
    return report