#!/usr/bin/env python3
"""
Project Comparison Analysis Script
Comprehensive analysis and comparison of multiple codebases using the hybrid code analyzer framework
"""

import argparse
import json
import logging
import os
import sys
import traceback
from datetime import datetime
from typing import Dict, Any, List

# Import necessary modules from the analyzer package
from analyzer.multi_codebase import MultiCodebaseAnalyzer
from analyzer.discovery_artifact import DiscoveryArtifactGenerator

# Set up comprehensive logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('project_comparison_analysis.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class ProjectComparisonAnalyzer:
    """
    Comprehensive project comparison analyzer using the hybrid code analyzer framework
    """
    
    def __init__(self, llm_backend: str = "ollama"):
        """Initialize the analyzer with LLM backend"""
        self.analyzer = MultiCodebaseAnalyzer(llm_backend=llm_backend)
        self.discovery_generator = DiscoveryArtifactGenerator()
        self.projects = []
        self.results = {}
        
    def analyze_all_projects(self, project_paths: List[str], question: str = "Analyze this codebase") -> Dict[str, Any]:
        """
        Analyze all projects using MultiCodebaseAnalyzer
        
        Args:
            project_paths: List of project paths to analyze
            question: Analysis question for LLM
            
        Returns:
            Dictionary containing analysis results for all projects
        """
        logger.info(f"Starting analysis of {len(project_paths)} projects")
        
        all_results = {}
        
        for i, project_path in enumerate(project_paths, 1):
            project_name = os.path.basename(project_path.rstrip('\\/'))
            logger.info(f"Analyzing project {i}/{len(project_paths)}: {project_name}")
            
            try:
                # Analyze the project using MultiCodebaseAnalyzer
                result = self.analyzer.analyze_single(project_path, question)
                
                # Generate discovery summary
                discovery_summary = self._generate_discovery_summary(result, project_name)
                
                # Store results
                all_results[project_name] = {
                    'project_path': project_path,
                    'analysis_result': result,
                    'discovery_summary': discovery_summary,
                    'analysis_timestamp': datetime.now().isoformat()
                }
                
                logger.info(f"Completed analysis for {project_name}")
                
            except Exception as e:
                logger.error(f"Failed to analyze project {project_name}: {str(e)}")
                traceback.print_exc()
                
                # Store error information
                all_results[project_name] = {
                    'project_path': project_path,
                    'error': str(e),
                    'error_type': type(e).__name__,
                    'analysis_timestamp': datetime.now().isoformat()
                }
        
        self.results = all_results
        return all_results
    
    def _generate_discovery_summary(self, result: Dict[str, Any], project_name: str) -> Dict[str, Any]:
        """
        Generate comprehensive discovery summary for a project
        
        Args:
            result: Analysis result from MultiCodebaseAnalyzer
            project_name: Name of the project
            
        Returns:
            Dictionary containing discovery summary
        """
        summary = {
            'project_name': project_name,
            'discovery_statistics': {},
            'analysis_coverage': {},
            'execution_failures': {}
        }
        
        try:
            # Extract discovery artifacts if available
            if "discovery_artifacts" in result:
                artifacts = result["discovery_artifacts"]
                
                # Process static discovery
                if artifacts.get("static"):
                    static_artifact = artifacts["static"]
                    summary['discovery_statistics']['static'] = {
                        'files_discovered': static_artifact['discovery_summary']['files_discovered'],
                        'files_passed_to_analysis': static_artifact['discovery_summary']['files_passed_to_analysis'],
                        'analysis_coverage_percentage': static_artifact['discovery_summary']['analysis_coverage_percentage']
                    }
                
                # Process dynamic discovery
                if artifacts.get("dynamic"):
                    dynamic_artifact = artifacts["dynamic"]
                    summary['discovery_statistics']['dynamic'] = {
                        'files_discovered': dynamic_artifact['discovery_summary']['files_discovered'],
                        'files_passed_to_analysis': dynamic_artifact['discovery_summary']['files_passed_to_analysis'],
                        'analysis_coverage_percentage': dynamic_artifact['discovery_summary']['analysis_coverage_percentage']
                    }
            
            # Extract analysis completeness
            if "analysis_completeness" in result:
                completeness = result["analysis_completeness"]
                summary['analysis_coverage'] = {
                    'status': completeness["status"],
                    'total_failures': completeness["total_failures"],
                    'total_issues': completeness["total_issues"],
                    'static_coverage': completeness["coverage_metrics"]["static_coverage"],
                    'dynamic_coverage': completeness["coverage_metrics"]["dynamic_coverage"],
                    'overall_coverage': completeness["coverage_metrics"]["overall_coverage"],
                    'completeness_context': completeness["coverage_metrics"]["completeness_context"]
                }
            
            # Extract execution failures
            if "execution_failures" in result:
                summary['execution_failures'] = {
                    'total_failures': len(result["execution_failures"]),
                    'analysis_findings': len([f for f in result["execution_failures"] if f.get("is_analysis_finding", False)]),
                    'actual_errors': len([f for f in result["execution_failures"] if not f.get("is_analysis_finding", True)])
                }
            
        except Exception as e:
            logger.error(f"Error generating discovery summary for {project_name}: {str(e)}")
            summary['error'] = str(e)
        
        return summary
    
    def compare_results(self) -> Dict[str, Any]:
        """
        Compare metrics across all analyzed projects
        
        Returns:
            Dictionary containing comprehensive comparison report
        """
        if not self.results:
            logger.warning("No analysis results available for comparison")
            return {"error": "No analysis results available"}
        
        logger.info("Generating comprehensive comparison report")
        
        comparison_report = {
            'timestamp': datetime.now().isoformat(),
            'project_count': len(self.results),
            'projects_analyzed': list(self.results.keys()),
            'comparison_metrics': {},
            'key_differences': {},
            'similarities': {},
            'recommendations': {}
        }
        
        try:
            # Initialize metrics collection
            metrics = {
                'discovery_statistics': {},
                'analysis_coverage': {},
                'execution_failures': {},
                'file_counts': {},
                'coverage_scores': {}
            }
            
            # Collect metrics from all projects
            for project_name, project_data in self.results.items():
                if 'error' in project_data:
                    continue
                
                # Extract discovery statistics
                if 'discovery_summary' in project_data:
                    discovery = project_data['discovery_summary']
                    
                    # Static discovery metrics
                    if 'static' in discovery['discovery_statistics']:
                        static = discovery['discovery_statistics']['static']
                        metrics['discovery_statistics'][project_name] = {
                            'static_files_discovered': static['files_discovered'],
                            'static_files_analyzed': static['files_passed_to_analysis'],
                            'static_coverage': static['analysis_coverage_percentage']
                        }
                    
                    # Dynamic discovery metrics
                    if 'dynamic' in discovery['discovery_statistics']:
                        dynamic = discovery['discovery_statistics']['dynamic']
                        if project_name not in metrics['discovery_statistics']:
                            metrics['discovery_statistics'][project_name] = {}
                        metrics['discovery_statistics'][project_name].update({
                            'dynamic_files_discovered': dynamic['files_discovered'],
                            'dynamic_files_analyzed': dynamic['files_passed_to_analysis'],
                            'dynamic_coverage': dynamic['analysis_coverage_percentage']
                        })
                
                # Extract analysis coverage
                if 'analysis_coverage' in project_data['discovery_summary']:
                    coverage = project_data['discovery_summary']['analysis_coverage']
                    metrics['analysis_coverage'][project_name] = {
                        'status': coverage['status'],
                        'overall_coverage': coverage['overall_coverage'],
                        'static_coverage': coverage['static_coverage'],
                        'dynamic_coverage': coverage['dynamic_coverage'],
                        'total_failures': coverage['total_failures'],
                        'total_issues': coverage['total_issues']
                    }
                
                # Extract execution failures
                if 'execution_failures' in project_data['discovery_summary']:
                    failures = project_data['discovery_summary']['execution_failures']
                    metrics['execution_failures'][project_name] = {
                        'total_failures': failures['total_failures'],
                        'analysis_findings': failures['analysis_findings'],
                        'actual_errors': failures['actual_errors']
                    }
            
            # Generate comparison metrics
            comparison_report['comparison_metrics'] = self._generate_comparison_metrics(metrics)
            
            # Identify key differences and similarities
            comparison_report['key_differences'] = self._identify_key_differences(metrics)
            comparison_report['similarities'] = self._identify_similarities(metrics)
            
            # Generate recommendations
            comparison_report['recommendations'] = self._generate_recommendations(metrics)
            
            logger.info("Completed comparison report generation")
            
        except Exception as e:
            logger.error(f"Error generating comparison report: {str(e)}")
            traceback.print_exc()
            comparison_report['error'] = str(e)
        
        return comparison_report
    
    def _generate_comparison_metrics(self, metrics: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate detailed comparison metrics from collected data
        
        Args:
            metrics: Collected metrics from all projects
            
        Returns:
            Dictionary containing comparison metrics
        """
        comparison_metrics = {}
        
        # Compare discovery statistics
        if metrics['discovery_statistics']:
            comparison_metrics['discovery_comparison'] = {}
            
            # Find projects with static analysis
            static_projects = [p for p, data in metrics['discovery_statistics'].items() if 'static_files_discovered' in data]
            if static_projects:
                comparison_metrics['discovery_comparison']['static'] = {
                    'projects': static_projects,
                    'max_files_discovered': max([metrics['discovery_statistics'][p]['static_files_discovered'] for p in static_projects]),
                    'min_files_discovered': min([metrics['discovery_statistics'][p]['static_files_discovered'] for p in static_projects]),
                    'avg_files_discovered': sum([metrics['discovery_statistics'][p]['static_files_discovered'] for p in static_projects]) / len(static_projects),
                    'max_coverage': max([metrics['discovery_statistics'][p]['static_coverage'] for p in static_projects]),
                    'min_coverage': min([metrics['discovery_statistics'][p]['static_coverage'] for p in static_projects]),
                    'avg_coverage': sum([metrics['discovery_statistics'][p]['static_coverage'] for p in static_projects]) / len(static_projects)
                }
            
            # Find projects with dynamic analysis
            dynamic_projects = [p for p, data in metrics['discovery_statistics'].items() if 'dynamic_files_discovered' in data]
            if dynamic_projects:
                comparison_metrics['discovery_comparison']['dynamic'] = {
                    'projects': dynamic_projects,
                    'max_files_discovered': max([metrics['discovery_statistics'][p]['dynamic_files_discovered'] for p in dynamic_projects]),
                    'min_files_discovered': min([metrics['discovery_statistics'][p]['dynamic_files_discovered'] for p in dynamic_projects]),
                    'avg_files_discovered': sum([metrics['discovery_statistics'][p]['dynamic_files_discovered'] for p in dynamic_projects]) / len(dynamic_projects),
                    'max_coverage': max([metrics['discovery_statistics'][p]['dynamic_coverage'] for p in dynamic_projects]),
                    'min_coverage': min([metrics['discovery_statistics'][p]['dynamic_coverage'] for p in dynamic_projects]),
                    'avg_coverage': sum([metrics['discovery_statistics'][p]['dynamic_coverage'] for p in dynamic_projects]) / len(dynamic_projects)
                }
        
        # Compare analysis coverage
        if metrics['analysis_coverage']:
            comparison_metrics['coverage_comparison'] = {
                'projects': list(metrics['analysis_coverage'].keys()),
                'max_overall_coverage': max([metrics['analysis_coverage'][p]['overall_coverage'] for p in metrics['analysis_coverage']]),
                'min_overall_coverage': min([metrics['analysis_coverage'][p]['overall_coverage'] for p in metrics['analysis_coverage']]),
                'avg_overall_coverage': sum([metrics['analysis_coverage'][p]['overall_coverage'] for p in metrics['analysis_coverage']]) / len(metrics['analysis_coverage']),
                'total_failures_across_projects': sum([metrics['analysis_coverage'][p]['total_failures'] for p in metrics['analysis_coverage']]),
                'total_issues_across_projects': sum([metrics['analysis_coverage'][p]['total_issues'] for p in metrics['analysis_coverage']])
            }
        
        # Compare execution failures
        if metrics['execution_failures']:
            comparison_metrics['failure_comparison'] = {
                'projects': list(metrics['execution_failures'].keys()),
                'max_failures': max([metrics['execution_failures'][p]['total_failures'] for p in metrics['execution_failures']]),
                'min_failures': min([metrics['execution_failures'][p]['total_failures'] for p in metrics['execution_failures']]),
                'avg_failures': sum([metrics['execution_failures'][p]['total_failures'] for p in metrics['execution_failures']]) / len(metrics['execution_failures']),
                'total_failures_across_projects': sum([metrics['execution_failures'][p]['total_failures'] for p in metrics['execution_failures']]),
                'total_analysis_findings': sum([metrics['execution_failures'][p]['analysis_findings'] for p in metrics['execution_failures']]),
                'total_actual_errors': sum([metrics['execution_failures'][p]['actual_errors'] for p in metrics['execution_failures']])
            }
        
        return comparison_metrics
    
    def _identify_key_differences(self, metrics: Dict[str, Any]) -> Dict[str, Any]:
        """
        Identify key differences between projects
        
        Args:
            metrics: Collected metrics from all projects
            
        Returns:
            Dictionary containing identified differences
        """
        differences = {}
        
        # Compare discovery statistics
        if metrics['discovery_statistics'] and len(metrics['discovery_statistics']) > 1:
            projects = list(metrics['discovery_statistics'].keys())
            
            # Compare file counts
            if all('static_files_discovered' in metrics['discovery_statistics'][p] for p in projects):
                file_counts = {p: metrics['discovery_statistics'][p]['static_files_discovered'] for p in projects}
                max_project = max(file_counts, key=file_counts.get)
                min_project = min(file_counts, key=file_counts.get)
                
                differences['file_count_differences'] = {
                    'largest_codebase': max_project,
                    'smallest_codebase': min_project,
                    'size_ratio': file_counts[max_project] / max(1, file_counts[min_project])
                }
            
            # Compare coverage
            if all('static_coverage' in metrics['discovery_statistics'][p] for p in projects):
                coverages = {p: metrics['discovery_statistics'][p]['static_coverage'] for p in projects}
                best_project = max(coverages, key=coverages.get)
                worst_project = min(coverages, key=coverages.get)
                
                differences['coverage_differences'] = {
                    'best_coverage': best_project,
                    'worst_coverage': worst_project,
                    'coverage_gap': coverages[best_project] - coverages[worst_project]
                }
        
        # Compare execution failures
        if metrics['execution_failures'] and len(metrics['execution_failures']) > 1:
            projects = list(metrics['execution_failures'].keys())
            
            if all('total_failures' in metrics['execution_failures'][p] for p in projects):
                failures = {p: metrics['execution_failures'][p]['total_failures'] for p in projects}
                most_stable = min(failures, key=failures.get)
                least_stable = max(failures, key=failures.get)
                
                differences['stability_differences'] = {
                    'most_stable_project': most_stable,
                    'least_stable_project': least_stable,
                    'failure_ratio': failures[least_stable] / max(1, failures[most_stable])
                }
        
        return differences
    
    def _identify_similarities(self, metrics: Dict[str, Any]) -> Dict[str, Any]:
        """
        Identify similarities between projects
        
        Args:
            metrics: Collected metrics from all projects
            
        Returns:
            Dictionary containing identified similarities
        """
        similarities = {}
        
        # Check if all projects have similar analysis status
        if metrics['analysis_coverage']:
            statuses = set(metrics['analysis_coverage'][p]['status'] for p in metrics['analysis_coverage'])
            if len(statuses) == 1:
                similarities['analysis_status'] = {
                    'common_status': list(statuses)[0],
                    'all_projects_consistent': True
                }
            else:
                similarities['analysis_status'] = {
                    'statuses_found': list(statuses),
                    'all_projects_consistent': False
                }
        
        # Check coverage ranges
        if metrics['analysis_coverage'] and len(metrics['analysis_coverage']) > 1:
            coverages = [metrics['analysis_coverage'][p]['overall_coverage'] for p in metrics['analysis_coverage']]
            coverage_range = max(coverages) - min(coverages)
            
            similarities['coverage_range'] = {
                'range': coverage_range,
                'narrow_range': coverage_range < 20  # Consider <20% as narrow range
            }
        
        return similarities
    
    def _generate_recommendations(self, metrics: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate recommendations based on comparison analysis
        
        Args:
            metrics: Collected metrics from all projects
            
        Returns:
            Dictionary containing recommendations
        """
        recommendations = {}
        
        # Recommendations for projects with low coverage
        if metrics['analysis_coverage']:
            low_coverage_projects = [
                p for p, data in metrics['analysis_coverage'].items() 
                if data['overall_coverage'] < 50
            ]
            
            if low_coverage_projects:
                recommendations['low_coverage_projects'] = {
                    'projects': low_coverage_projects,
                    'recommendation': 'These projects have low analysis coverage (<50%). Consider improving test coverage and analysis depth.'
                }
        
        # Recommendations for projects with high failure rates
        if metrics['execution_failures']:
            high_failure_projects = [
                p for p, data in metrics['execution_failures'].items() 
                if data['total_failures'] > 10
            ]
            
            if high_failure_projects:
                recommendations['high_failure_projects'] = {
                    'projects': high_failure_projects,
                    'recommendation': 'These projects have high failure rates (>10 failures). Consider addressing execution issues and improving code quality.'
                }
        
        # General recommendations
        recommendations['general'] = [
            'Consider running more comprehensive static and dynamic analysis on all projects',
            'Review and update ignore rules to ensure optimal file coverage',
            'Address execution failures to improve analysis completeness',
            'Use the detailed analysis results to identify specific areas for improvement'
        ]
        
        return recommendations
    
    def save_results(self, output_dir: str = "comparison_results") -> Dict[str, Any]:
        """
        Save analysis results to JSON files
        
        Args:
            output_dir: Directory to save results
            
        Returns:
            Dictionary containing paths to saved files
        """
        logger.info(f"Saving results to {output_dir}")
        
        # Create output directory if it doesn't exist
        os.makedirs(output_dir, exist_ok=True)
        
        saved_files = {}
        
        try:
            # Save individual project results
            for project_name, project_data in self.results.items():
                if 'error' in project_data:
                    continue
                
                project_filename = os.path.join(output_dir, f"{project_name}_analysis_results.json")
                
                with open(project_filename, 'w', encoding='utf-8') as f:
                    json.dump(project_data, f, indent=2, ensure_ascii=False)
                
                saved_files[f'{project_name}_analysis'] = project_filename
                logger.info(f"Saved analysis results for {project_name} to {project_filename}")
            
            # Generate and save comparison report
            comparison_report = self.compare_results()
            comparison_filename = os.path.join(output_dir, "master_comparison_report.json")
            
            with open(comparison_filename, 'w', encoding='utf-8') as f:
                json.dump(comparison_report, f, indent=2, ensure_ascii=False)
            
            saved_files['master_comparison'] = comparison_filename
            logger.info(f"Saved master comparison report to {comparison_filename}")
            
            # Save summary report
            summary_report = self._generate_summary_report()
            summary_filename = os.path.join(output_dir, "comparison_summary.json")
            
            with open(summary_filename, 'w', encoding='utf-8') as f:
                json.dump(summary_report, f, indent=2, ensure_ascii=False)
            
            saved_files['summary_report'] = summary_filename
            logger.info(f"Saved comparison summary to {summary_filename}")
            
        except Exception as e:
            logger.error(f"Error saving results: {str(e)}")
            traceback.print_exc()
            saved_files['error'] = str(e)
        
        return saved_files
    
    def _generate_summary_report(self) -> Dict[str, Any]:
        """
        Generate a concise summary report
        
        Returns:
            Dictionary containing summary report
        """
        summary = {
            'timestamp': datetime.now().isoformat(),
            'project_count': len(self.results),
            'projects_analyzed': [],
            'overall_statistics': {},
            'key_findings': []
        }
        
        # Collect basic project information
        for project_name, project_data in self.results.items():
            project_info = {
                'name': project_name,
                'path': project_data['project_path'],
                'status': 'error' if 'error' in project_data else 'analyzed'
            }
            
            if 'error' not in project_data and 'analysis_coverage' in project_data['discovery_summary']:
                coverage = project_data['discovery_summary']['analysis_coverage']
                project_info.update({
                    'overall_coverage': coverage['overall_coverage'],
                    'total_failures': coverage['total_failures'],
                    'total_issues': coverage['total_issues']
                })
            
            summary['projects_analyzed'].append(project_info)
        
        # Generate overall statistics
        successful_projects = [p for p in summary['projects_analyzed'] if p['status'] == 'analyzed']
        summary['overall_statistics'] = {
            'successful_analyses': len(successful_projects),
            'failed_analyses': len(summary['projects_analyzed']) - len(successful_projects),
            'success_rate': len(successful_projects) / max(1, len(summary['projects_analyzed'])) * 100
        }
        
        # Generate key findings
        if successful_projects:
            avg_coverage = sum(p['overall_coverage'] for p in successful_projects) / len(successful_projects)
            total_failures = sum(p['total_failures'] for p in successful_projects)
            
            summary['key_findings'] = [
                f"Average analysis coverage across projects: {avg_coverage:.1f}%",
                f"Total execution failures: {total_failures}",
                f"Average failures per project: {total_failures / len(successful_projects):.1f}"
            ]
        
        return summary

def main():
    """
    Main function with argument parsing and execution
    """
    parser = argparse.ArgumentParser(
        description="Project Comparison Analysis Tool - Comprehensive analysis and comparison of multiple codebases"
    )
    
    # Project paths arguments
    parser.add_argument("--projects", nargs='+', 
                       help="List of project paths to analyze (space-separated)",
                       required=True)
    
    # Analysis options
    parser.add_argument("--question", 
                       help="Analysis question for LLM",
                       default="Analyze this codebase")
    parser.add_argument("--backend", 
                       choices=["ollama", "vllm"], 
                       default="ollama",
                       help="LLM backend to use")
    
    # Output options
    parser.add_argument("--output-dir", 
                       help="Output directory for results",
                       default="comparison_results")
    parser.add_argument("--skip-comparison", 
                       action="store_true",
                       help="Skip comparison analysis and only save individual results")
    
    # Logging options
    parser.add_argument("--verbose", 
                       action="store_true",
                       help="Enable verbose logging")
    parser.add_argument("--log-file",
                       help="Custom log file path")
    
    args = parser.parse_args()
    
    # Configure logging based on arguments
    if args.verbose:
        logger.setLevel(logging.DEBUG)
        logging.getLogger('analyzer').setLevel(logging.DEBUG)
    
    if args.log_file:
        # Remove existing file handler and add custom one
        for handler in logger.handlers[:]:
            if isinstance(handler, logging.FileHandler):
                logger.removeHandler(handler)
        
        file_handler = logging.FileHandler(args.log_file)
        file_handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
        logger.addHandler(file_handler)
    
    logger.info("Starting Project Comparison Analysis")
    logger.info(f"Projects to analyze: {args.projects}")
    logger.info(f"LLM Backend: {args.backend}")
    logger.info(f"Output Directory: {args.output_dir}")
    
    try:
        # Initialize analyzer
        analyzer = ProjectComparisonAnalyzer(llm_backend=args.backend)
        
        # Analyze all projects
        logger.info("Beginning project analysis...")
        analysis_results = analyzer.analyze_all_projects(args.projects, args.question)
        
        # Save results
        logger.info("Saving analysis results...")
        saved_files = analyzer.save_results(args.output_dir)
        
        # Print summary
        print("\n" + "="*80)
        print("PROJECT COMPARISON ANALYSIS COMPLETE")
        print("="*80)
        print(f"Projects Analyzed: {len(args.projects)}")
        print(f"Results Directory: {args.output_dir}")
        print("\nSaved Files:")
        for file_type, file_path in saved_files.items():
            if file_type != 'error':
                print(f"  - {file_type}: {file_path}")
        print("\nAnalysis Summary:")
        
        # Print basic statistics
        successful = sum(1 for p in analysis_results.values() if 'error' not in p)
        failed = len(analysis_results) - successful
        
        print(f"  Successful Analyses: {successful}")
        print(f"  Failed Analyses: {failed}")
        
        if successful > 0:
            # Calculate average coverage
            coverages = []
            for project_data in analysis_results.values():
                if 'error' not in project_data and 'analysis_coverage' in project_data['discovery_summary']:
                    coverages.append(project_data['discovery_summary']['analysis_coverage']['overall_coverage'])
            
            if coverages:
                avg_coverage = sum(coverages) / len(coverages)
                print(f"  Average Coverage: {avg_coverage:.1f}%")
        
        print("="*80)
        
    except Exception as e:
        logger.error(f"Fatal error during analysis: {str(e)}")
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()