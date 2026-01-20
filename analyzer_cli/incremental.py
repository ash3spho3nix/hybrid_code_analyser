"""
Incremental analysis support for the Hybrid Code Analyzer CLI
"""
import os
import json
from typing import Dict, Any, List, Tuple
import logging
from utils import get_file_hash, get_current_timestamp
from error_handler import AnalysisError

# Configure logging
logger = logging.getLogger(__name__)

def detect_changed_files(
    current_files: List[str],
    previous_analysis: Dict[str, Any],
    changed_files_json: Dict[str, Any]
) -> Tuple[List[str], List[str], List[str]]:
    """
    Detect changed files by comparing with previous analysis and changed files JSON
    Returns: (new_files, modified_files, unchanged_files)
    """
    new_files = []
    modified_files = []
    unchanged_files = []
    
    # Get previous file metadata
    previous_files = {}
    if previous_analysis and "metadata" in previous_analysis:
        for file_path, metadata in previous_analysis["metadata"].items():
            previous_files[file_path] = {
                "hash": metadata.get("hash", ""),
                "modified_time": metadata.get("modified_time", 0)
            }
    
    # Check each current file
    for file_path in current_files:
        try:
            current_hash = get_file_hash(file_path)
            current_mtime = os.path.getmtime(file_path)
            
            # Check if file is in changed_files JSON
            if changed_files_json and file_path in changed_files_json:
                modified_files.append(file_path)
                continue
            
            # Check if file existed in previous analysis
            if file_path in previous_files:
                prev_hash = previous_files[file_path]["hash"]
                prev_mtime = previous_files[file_path]["modified_time"]
                
                # File is modified if hash or mtime changed
                if current_hash != prev_hash or current_mtime != prev_mtime:
                    modified_files.append(file_path)
                else:
                    unchanged_files.append(file_path)
            else:
                # New file
                new_files.append(file_path)
                
        except Exception as e:
            logger.warning(f"Error checking file changes for {file_path}: {str(e)}")
            # If we can't determine, assume it needs analysis
            modified_files.append(file_path)
    
    return new_files, modified_files, unchanged_files

def load_previous_analysis(previous_output_path: str) -> Dict[str, Any]:
    """Load previous analysis results from JSON file"""
    if not previous_output_path or not os.path.isfile(previous_output_path):
        return {}
    
    try:
        with open(previous_output_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"Error loading previous analysis from {previous_output_path}: {str(e)}")
        return {}

def merge_analysis_results(
    current_results: Dict[str, Any],
    previous_results: Dict[str, Any],
    files_to_analyze: List[str]
) -> Dict[str, Any]:
    """Merge current analysis results with previous results"""
    merged_results = previous_results.copy()
    
    # Merge static results
    if "static_results" in current_results:
        # Create mapping of file paths to results
        current_file_results = {}
        for result in current_results["static_results"]:
            file_path = result.get("file_path", "")
            if file_path:
                current_file_results[file_path] = result
        
        # Update previous results with current results for analyzed files
        if "static_results" in merged_results:
            for i, prev_result in enumerate(merged_results["static_results"]):
                file_path = prev_result.get("file_path", "")
                if file_path in current_file_results:
                    merged_results["static_results"][i] = current_file_results[file_path]
        else:
            merged_results["static_results"] = current_results["static_results"]
    
    # Merge dynamic results
    if "dynamic_results" in current_results:
        # Create mapping of function IDs to results
        current_func_results = {}
        for result in current_results["dynamic_results"]:
            func_id = result.get("function_id", "")
            if func_id:
                current_func_results[func_id] = result
        
        # Update previous results with current results
        if "dynamic_results" in merged_results:
            for i, prev_result in enumerate(merged_results["dynamic_results"]):
                func_id = prev_result.get("function_id", "")
                if func_id in current_func_results:
                    merged_results["dynamic_results"][i] = current_func_results[func_id]
        else:
            merged_results["dynamic_results"] = current_results["dynamic_results"]
    
    # Merge AI suggestions
    if "AI_suggestions" in current_results:
        # Combine suggestions, removing duplicates by ID
        current_suggestions = current_results["AI_suggestions"]
        prev_suggestions = merged_results.get("AI_suggestions", [])
        
        # Create set of current suggestion IDs
        current_suggestion_ids = {s.get("id", "") for s in current_suggestions}
        
        # Keep previous suggestions not in current analysis
        merged_suggestions = [s for s in prev_suggestions if s.get("id", "") not in current_suggestion_ids]
        
        # Add current suggestions
        merged_suggestions.extend(current_suggestions)
        
        merged_results["AI_suggestions"] = merged_suggestions
    
    # Update summary
    if "summary" in current_results:
        merged_results["summary"] = current_results["summary"]
    
    # Update metadata
    if "meta" in current_results:
        merged_results["meta"] = current_results["meta"]
    
    return merged_results

def create_incremental_analysis_plan(
    current_files: List[str],
    previous_analysis: Dict[str, Any],
    changed_files_json: Dict[str, Any]
) -> Dict[str, Any]:
    """Create analysis plan for incremental analysis"""
    plan = {
        "files_to_analyze": [],
        "files_to_skip": [],
        "reason": "full_analysis"  # Default to full analysis
    }
    
    # If no previous analysis, do full analysis
    if not previous_analysis:
        plan["files_to_analyze"] = current_files
        plan["reason"] = "no_previous_analysis"
        return plan
    
    # Detect changed files
    new_files, modified_files, unchanged_files = detect_changed_files(
        current_files, previous_analysis, changed_files_json
    )
    
    # Files to analyze are new and modified files
    plan["files_to_analyze"] = new_files + modified_files
    plan["files_to_skip"] = unchanged_files
    
    if plan["files_to_analyze"]:
        plan["reason"] = "incremental_analysis"
        plan["new_files"] = new_files
        plan["modified_files"] = modified_files
        plan["unchanged_files"] = unchanged_files
    else:
        plan["reason"] = "no_changes_detected"
    
    return plan

def save_incremental_state(
    analysis_results: Dict[str, Any],
    state_file_path: str
) -> bool:
    """Save incremental analysis state for future runs"""
    try:
        # Create a simplified state with essential information
        state = {
            "timestamp": get_current_timestamp(),
            "metadata": analysis_results.get("metadata", {}),
            "file_hashes": {},
            "summary": analysis_results.get("summary", {})
        }
        
        # Extract file hashes from metadata
        for file_path, metadata in analysis_results.get("metadata", {}).items():
            state["file_hashes"][file_path] = {
                "hash": metadata.get("hash", ""),
                "modified_time": metadata.get("modified_time", 0)
            }
        
        # Save state to file
        with open(state_file_path, 'w', encoding='utf-8') as f:
            json.dump(state, f, indent=2, ensure_ascii=False)
        
        return True
        
    except Exception as e:
        logger.error(f"Error saving incremental state to {state_file_path}: {str(e)}")
        return False

def load_incremental_state(state_file_path: str) -> Dict[str, Any]:
    """Load incremental analysis state from file"""
    if not state_file_path or not os.path.isfile(state_file_path):
        return {}
    
    try:
        with open(state_file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"Error loading incremental state from {state_file_path}: {str(e)}")
        return {}

def should_perform_incremental_analysis(args: Dict[str, Any]) -> bool:
    """Determine if incremental analysis should be performed"""
    # Incremental analysis is performed if:
    # 1. Previous output file is specified
    # 2. Changed files JSON is provided OR previous analysis exists
    
    has_previous_output = args.get("previous_output") and os.path.isfile(args.get("previous_output"))
    has_changed_files = args.get("changed_files") and os.path.isfile(args.get("changed_files"))
    
    return has_previous_output or has_changed_files