from typing import Dict, Any, List
from .static_analyzer import StaticAnalyzer
from .llm_client import LLMClient
import os

class MultiCodebaseAnalyzer:
    def __init__(self, llm_backend: str = "ollama"):
        self.static_analyzer = StaticAnalyzer()
        self.llm_client = LLMClient(llm_backend)
    
    def analyze_single(self, codebase_path: str, question: str = "Analyze this codebase") -> Dict[str, Any]:
        """Analyze single codebase with question"""
        analysis = self.static_analyzer.analyze_codebase(codebase_path)
        llm_analysis = self.llm_client.analyze_single(analysis, question)
        
        return {
            "static_analysis": analysis,
            "llm_analysis": llm_analysis
        }
    
    def compare_codebases(self, codebase_a: str, codebase_b: str, question: str) -> Dict[str, Any]:
        """Compare two codebases"""
        analysis_a = self.static_analyzer.analyze_codebase(codebase_a)
        analysis_b = self.static_analyzer.analyze_codebase(codebase_b)
        
        comparison = self.llm_client.compare_codebases(analysis_a, analysis_b, question)
        
        return {
            "codebase_a": analysis_a,
            "codebase_b": analysis_b, 
            "comparison_analysis": comparison
        }
    
    def analyze_merge(self, codebase_a: str, codebase_b: str) -> Dict[str, Any]:
        """Analyze merging two codebases"""
        return self.compare_codebases(
            codebase_a, 
            codebase_b,
            "What are the main challenges and recommended approach for merging these two codebases?"
        )