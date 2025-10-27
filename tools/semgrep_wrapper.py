import subprocess
import json
import tempfile
import os
from typing import Dict, Any, List

class SemgrepWrapper:
    def __init__(self, semgrep_path: str = "semgrep"):
        self.semgrep_path = semgrep_path
    
    def analyze(self, codebase_path: str, rules: str = "auto") -> Dict[str, Any]:
        """Run semgrep analysis on codebase"""
        try:
            cmd = [self.semgrep_path, "--json", "--config", rules, codebase_path]
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=120
            )
            
            if result.returncode == 0:
                return json.loads(result.stdout)
            else:
                return {"error": result.stderr, "results": []}
                
        except Exception as e:
            return {"error": str(e), "results": []}
    
    def analyze_multiple(self, codebase_paths: List[str]) -> Dict[str, Any]:
        """Analyze multiple codebases"""
        all_results = {}
        for path in codebase_paths:
            all_results[path] = self.analyze(path)
        return all_results