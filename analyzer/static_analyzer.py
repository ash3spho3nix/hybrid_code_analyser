import os
import ast
import subprocess
from typing import Dict, Any, List
from tools.sonarqube_wrapper import SonarQubeWrapper
from tools.semgrep_wrapper import SemgrepWrapper

class StaticAnalyzer:
    def __init__(self):
        self.sonarqube = SonarQubeWrapper("sonar-scanner")
        self.semgrep = SemgrepWrapper()
    
    def analyze_codebase(self, codebase_path: str) -> Dict[str, Any]:
        """Comprehensive analysis of a single codebase"""
        if not os.path.exists(codebase_path):
            return {"error": f"Codebase path does not exist: {codebase_path}"}
        
        # Run multiple analysis tools
        sonar_results = self.sonarqube.analyze(codebase_path)
        semgrep_results = self.semgrep.analyze(codebase_path)
        custom_analysis = self._custom_analysis(codebase_path)
        
        return {
            "sonarqube": sonar_results,
            "semgrep": semgrep_results,
            "custom_analysis": custom_analysis,
            "summary": self._generate_summary(sonar_results, semgrep_results, custom_analysis)
        }
    
    def _custom_analysis(self, codebase_path: str) -> Dict[str, Any]:
        """Perform custom static analysis"""
        analysis = {
            "file_count": 0,
            "file_types": {},
            "complex_files": [],
            "large_files": []
        }
        
        for root, dirs, files in os.walk(codebase_path):
            for file in files:
                file_path = os.path.join(root, file)
                analysis["file_count"] += 1
                
                # Count file types
                ext = os.path.splitext(file)[1]
                analysis["file_types"][ext] = analysis["file_types"].get(ext, 0) + 1
                
                # Find large files
                try:
                    size = os.path.getsize(file_path)
                    if size > 1000000:  # 1MB
                        analysis["large_files"].append({"file": file_path, "size": size})
                except:
                    pass
        
        return analysis
    
    def _generate_summary(self, sonar: Dict, semgrep: Dict, custom: Dict) -> Dict[str, Any]:
        """Generate analysis summary"""
        return {
            "total_issues": len(sonar.get("issues", [])) + len(semgrep.get("results", [])),
            "files_analyzed": custom.get("file_count", 0),
            "file_types": custom.get("file_types", {}),
            "quality_metrics": {
                "large_files": len(custom.get("large_files", [])),
                "sonar_issues": len(sonar.get("issues", [])),
                "semgrep_findings": len(semgrep.get("results", []))
            }
        }