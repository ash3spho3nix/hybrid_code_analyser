from typing import Dict, Any, Union, List
from pathlib import Path
import subprocess
import sys
import tempfile
import json
import traceback
import importlib.util
import os
from datetime import datetime
from analyzer.dynamic_analyzer_base import DynamicAnalyzer as DynamicAnalyzerBase, ExecutionFailure, FailureType, FailureSeverity

class DynamicAnalyzerHelpers(DynamicAnalyzerBase):
    def _create_memory_profiler_script(self, script_path: str) -> str:
        """Create temporary script for memory profiling"""
        profiler_code = f'''
from memory_profiler import profile
@profile
def run_analysis():
    with open("{script_path}") as f:
        exec(f.read())

if __name__ == "__main__":
    run_analysis()
'''
        temp_file = tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False)
        temp_file.write(profiler_code)
        temp_file.close()
        return temp_file.name
       
    def _parse_trace_output(self, stdout: str, stderr: str) -> Dict[str, Any]:
        """Parse trace module output"""
        lines = stdout.split('\n')
        executed_lines = [line for line in lines if line.startswith(' ') and ':' in line]
           
        return {
            "executed_lines_count": len(executed_lines),
            "execution_summary": f"Executed {len(executed_lines)} lines",
            "coverage_estimate": len(executed_lines) / 1000,  # Simplified metric
            "trace_details": executed_lines[:50]  # Sample of executed lines
        }
       
    def _parse_memory_profile(self, output: str) -> Dict[str, Any]:
        """Parse memory profiler output"""
        lines = output.split('\n')
        memory_usage = [] 
           
        for line in lines:
            if 'MiB' in line and 'line' in line:
                parts = line.split()
                if len(parts) >= 6:
                    memory_usage.append({
                        "memory_mib": float(parts[2]),
                        "line_number": int(parts[4]),
                        "code_snippet": ' '.join(parts[5:])
                    })
           
        return {
            "memory_usage_by_line": memory_usage,
            "peak_memory": max([m["memory_mib"] for m in memory_usage]) if memory_usage else 0
        }
       
    def _analyze_call_complexity(self, call_graph: Dict) -> Dict[str, Any]:
        """Analyze complexity from call graph"""
        functions = list(call_graph.keys())
        complexity_metrics = {} 
           
        for func in functions:
            calls = call_graph[func]
            complexity_metrics[func] = {
                "outbound_calls": len(calls),
                "complexity_score": len(calls) * 10  # Simplified metric
            }
           
        return {
            "total_functions": len(functions),
            "most_complex": sorted(complexity_metrics.items(), 
                                  key=lambda x: x[1]["complexity_score"], reverse=True)[:10],
            "call_graph_summary": f"Analyzed {len(functions)} functions"
        }
       
    def _extract_execution_path(self, trace_output: str) -> List[str]:
        """Extract execution path from trace output"""
        lines = trace_output.split('\n')
        execution_lines = [] 
           
        for line in lines:
            if 'call' in line or 'return' in line:
                execution_lines.append(line.strip())
           
        return execution_lines[:100]  # Limit output size