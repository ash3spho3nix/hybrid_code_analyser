from typing import Dict, Any, List
from .static_analyzer import StaticAnalyzer
from .llm_client import LLMClient
import os
from .dynamic_analyzer import DynamicAnalyzer
from .improvement_suggester import ImprovementSuggester
from pathlib import Path
from .file_discovery import FileDiscoveryService
#from .analysis_storage import AnalysisStorage

class MultiCodebaseAnalyzer:
    def __init__(self, llm_backend: str = "ollama"):
        self.static_analyzer = StaticAnalyzer()
        self.llm_client = LLMClient(llm_backend)
        self.dynamic_analyzer = DynamicAnalyzer()
        self.improvement_suggester = ImprovementSuggester()
#        self.analysis_storage = AnalysisStorage()
    
    def analyze_single(self, codebase_path: str, question: str = "Analyze this codebase") -> Dict[str, Any]:
        """Analyze single codebase with question"""
        
        # Use FileDiscoveryService to coordinate discovery for both analyzers
        discovery_service = FileDiscoveryService()
        
        # Get discovery results for static analysis
        static_discovery = discovery_service.discover_files([codebase_path], analyzer_type='static')
        
        # Get discovery results for dynamic analysis
        dynamic_discovery = discovery_service.discover_files([codebase_path], analyzer_type='dynamic')
        
        # Pass pre-filtered files to analyzers
        static_analysis = self.static_analyzer.analyze_codebase_with_files(
            codebase_path, 
            static_discovery.files_for_analysis
        )
        
        dynamic_analysis = self.dynamic_analyzer.run_dynamic_analysis_with_files(
            codebase_path,
            dynamic_discovery.files_for_analysis
        )
        
        llm_analysis = self.llm_client.analyze_single(static_analysis, question)
        
        # Aggregate execution failures from both analyzers
        all_execution_failures = []
        total_failure_count = 0
        total_issue_count = 0
        
        # Collect static analysis failures
        if "execution_failures" in static_analysis:
            all_execution_failures.extend(static_analysis["execution_failures"])
            total_failure_count += static_analysis.get("failure_count", 0)
            total_issue_count += static_analysis.get("issue_count", 0)
        
        # Collect dynamic analysis failures  
        if "execution_failures" in dynamic_analysis:
            all_execution_failures.extend(dynamic_analysis["execution_failures"])
            total_failure_count += dynamic_analysis.get("failure_count", 0)
            total_issue_count += dynamic_analysis.get("issue_count", 0)
        
        # Calculate overall analysis completeness
        analysis_completeness = {
            "status": "complete",
            "total_failures": total_failure_count,
            "total_issues": total_issue_count,
            "analysis_findings": 0,
            "actual_errors": 0,
            "coverage_metrics": {
                "static_coverage": 0.0,
                "dynamic_coverage": 0.0,
                "overall_coverage": 0.0,
                "completeness_context": ""
            }
        }
        
        if total_failure_count > 0:
            analysis_completeness["status"] = "partial"
            analysis_completeness["analysis_findings"] = len([f for f in all_execution_failures if f.get("is_analysis_finding", False)])
            analysis_completeness["actual_errors"] = len([f for f in all_execution_failures if not f.get("is_analysis_finding", True)])
        
        # Extract coverage metrics from static analysis
        static_coverage = static_analysis.get("summary", {}).get("coverage_percentage", 0.0)
        analysis_completeness["coverage_metrics"]["static_coverage"] = static_coverage
        
        # Extract coverage metrics from dynamic analysis
        dynamic_coverage = dynamic_analysis.get("method_coverage_percentage", 0.0)
        analysis_completeness["coverage_metrics"]["dynamic_coverage"] = dynamic_coverage
        
        # Calculate overall coverage (weighted average)
        if static_coverage > 0 and dynamic_coverage > 0:
            analysis_completeness["coverage_metrics"]["overall_coverage"] = (
                (static_coverage * 0.6) + (dynamic_coverage * 0.4)
            )
        elif static_coverage > 0:
            analysis_completeness["coverage_metrics"]["overall_coverage"] = static_coverage
        elif dynamic_coverage > 0:
            analysis_completeness["coverage_metrics"]["overall_coverage"] = dynamic_coverage
        
        # Generate completeness context
        if analysis_completeness["status"] == "complete":
            analysis_completeness["coverage_metrics"]["completeness_context"] = (
                f"Analysis completed successfully with {analysis_completeness['coverage_metrics']['overall_coverage']:.1f}% overall coverage"
            )
        else:
            analysis_completeness["coverage_metrics"]["completeness_context"] = (
                f"Analysis completed with {analysis_completeness['coverage_metrics']['overall_coverage']:.1f}% coverage. "
                f"Encountered {total_failure_count} failures ({analysis_completeness['analysis_findings']} findings, "
                f"{analysis_completeness['actual_errors']} errors)"
            )
        
        # Include discovery artifacts in final result
        result = {
            "static_analysis": static_analysis,
            "dynamic_analysis": dynamic_analysis,
            "llm_analysis": llm_analysis,
            "execution_failures": all_execution_failures,
            "failure_count": total_failure_count,
            "issue_count": total_issue_count,
            "analysis_completeness": analysis_completeness
        }
        
        # Add discovery artifacts if available
        if hasattr(static_discovery, 'discovery_artifact') and static_discovery.discovery_artifact:
            result["discovery_artifacts"] = {
                'static': static_discovery.discovery_artifact,
                'dynamic': dynamic_discovery.discovery_artifact if hasattr(dynamic_discovery, 'discovery_artifact') else None
            }
        
        return result
        
    def compare_codebases(self, codebase_a: str, codebase_b: str, question: str) -> Dict[str, Any]:
        """Compare two codebases"""
        analysis_a = self.static_analyzer.analyze_codebase(codebase_a)
        analysis_b = self.static_analyzer.analyze_codebase(codebase_b)
        
        comparison = self.llm_client.compare_codebases(analysis_a, analysis_b, question)
        
        # Aggregate execution failures from both codebase analyses
        all_execution_failures = []
        total_failure_count = 0
        total_issue_count = 0
        
        # Collect failures from codebase A
        if "execution_failures" in analysis_a:
            all_execution_failures.extend(analysis_a["execution_failures"])
            total_failure_count += analysis_a.get("failure_count", 0)
            total_issue_count += analysis_a.get("issue_count", 0)
        
        # Collect failures from codebase B
        if "execution_failures" in analysis_b:
            all_execution_failures.extend(analysis_b["execution_failures"])
            total_failure_count += analysis_b.get("failure_count", 0)
            total_issue_count += analysis_b.get("issue_count", 0)
        
        # Calculate overall comparison completeness
        comparison_completeness = {
            "status": "complete",
            "total_failures": total_failure_count,
            "total_issues": total_issue_count,
            "analysis_findings": 0,
            "actual_errors": 0,
            "coverage_metrics": {
                "codebase_a_coverage": 0.0,
                "codebase_b_coverage": 0.0,
                "comparison_coverage": 0.0,
                "completeness_context": ""
            }
        }
        
        if total_failure_count > 0:
            comparison_completeness["status"] = "partial"
            comparison_completeness["analysis_findings"] = len([f for f in all_execution_failures if f.get("is_analysis_finding", False)])
            comparison_completeness["actual_errors"] = len([f for f in all_execution_failures if not f.get("is_analysis_finding", True)])
        
        # Extract coverage metrics from both codebase analyses
        codebase_a_coverage = analysis_a.get("summary", {}).get("coverage_percentage", 0.0)
        codebase_b_coverage = analysis_b.get("summary", {}).get("coverage_percentage", 0.0)
        
        comparison_completeness["coverage_metrics"]["codebase_a_coverage"] = codebase_a_coverage
        comparison_completeness["coverage_metrics"]["codebase_b_coverage"] = codebase_b_coverage
        
        # Calculate comparison coverage (average of both codebases)
        comparison_completeness["coverage_metrics"]["comparison_coverage"] = (
            (codebase_a_coverage + codebase_b_coverage) / 2
        )
        
        # Generate completeness context
        if comparison_completeness["status"] == "complete":
            comparison_completeness["coverage_metrics"]["completeness_context"] = (
                f"Comparison completed successfully with {comparison_completeness['coverage_metrics']['comparison_coverage']:.1f}% coverage"
            )
        else:
            comparison_completeness["coverage_metrics"]["completeness_context"] = (
                f"Comparison completed with {comparison_completeness['coverage_metrics']['comparison_coverage']:.1f}% coverage. "
                f"Encountered {total_failure_count} failures ({comparison_completeness['analysis_findings']} findings, "
                f"{comparison_completeness['actual_errors']} errors)"
            )
        
        return {
            "codebase_a": analysis_a,
            "codebase_b": analysis_b, 
            "comparison_analysis": comparison,
            "execution_failures": all_execution_failures,
            "failure_count": total_failure_count,
            "issue_count": total_issue_count,
            "comparison_completeness": comparison_completeness
        }
    
    def analyze_merge(self, codebase_a: str, codebase_b: str) -> Dict[str, Any]:
        """Analyze merging two codebases"""
        return self.compare_codebases(
            codebase_a, 
            codebase_b,
            "What are the main challenges and recommended approach for merging these two codebases?"
        )