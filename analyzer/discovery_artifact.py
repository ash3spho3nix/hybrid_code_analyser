from typing import List, Dict, Any, Optional
from datetime import datetime
import os
import json
from collections import defaultdict
import logging

# Set up logging
logger = logging.getLogger(__name__)

class DiscoveryArtifactGenerator:
    def __init__(self):
        """Initialize the discovery artifact generator"""
        pass
    
    def generate_artifact(self, all_files: List[str], ignore_report: Optional['IgnoreReport'], 
                         type_filter_report: Optional['FileTypeFilterReport'], final_files: List[str]) -> Dict[str, Any]:
        """
        Generate comprehensive discovery artifact
        
        Args:
            all_files: All files discovered before filtering
            ignore_report: Report from ignore rules processing
            type_filter_report: Report from file type filtering
            final_files: Files passed to analysis
            
        Returns:
            Dictionary containing complete discovery artifact
        """
        # Calculate metrics
        files_discovered = len(all_files)
        files_ignored_by_rule = ignore_report.total_files_ignored if ignore_report else 0
        files_ignored_by_type = type_filter_report.total_files_filtered if type_filter_report else 0
        files_passed_to_analysis = len(final_files)
        
        # Calculate coverage percentage
        coverage_percentage = 0.0
        if files_discovered > 0:
            coverage_percentage = (files_passed_to_analysis / files_discovered) * 100
        
        # Generate artifact
        artifact = {
            'discovery_metadata': {
                'timestamp': datetime.utcnow().isoformat() + 'Z',
                'artifact_version': '1.0',
                'generator': 'DiscoveryArtifactGenerator'
            },
            'discovery_summary': {
                'files_discovered': files_discovered,
                'files_ignored_by_rule': files_ignored_by_rule,
                'files_ignored_by_type': files_ignored_by_type,
                'files_passed_to_analysis': files_passed_to_analysis,
                'analysis_coverage_percentage': round(coverage_percentage, 2)
            },
            'ignore_processing': self._generate_ignore_section(ignore_report),
            'file_type_filtering': self._generate_filter_section(type_filter_report),
            'file_list': self._generate_file_list_section(final_files)
        }
        
        return artifact
    
    def _generate_ignore_section(self, ignore_report: Optional['IgnoreReport']) -> Dict[str, Any]:
        """Generate ignore processing section of artifact"""
        if not ignore_report:
            return {
                'rules_applied': False,
                'files_ignored': 0,
                'sources': []
            }
        
        return {
            'rules_applied': True,
            'files_ignored': ignore_report.total_files_ignored,
            'sources': list(ignore_report.ignore_sources),
            'patterns_used': list(ignore_report.patterns_applied),
            'ignored_files_count': len(ignore_report.ignored_files),
            'ignored_files_sample': ignore_report.ignored_files[:10] if ignore_report.ignored_files else []
        }
    
    def _generate_filter_section(self, filter_report: Optional['FileTypeFilterReport']) -> Dict[str, Any]:
        """Generate file type filtering section of artifact"""
        if not filter_report:
            return {
                'filtering_applied': False,
                'files_filtered': 0,
                'supported_extensions': []
            }
        
        return {
            'filtering_applied': True,
            'files_filtered': filter_report.total_files_filtered,
            'supported_extensions': filter_report.supported_extensions,
            'filtered_extensions': filter_report.filtered_extensions,
            'filtered_files_count': len(filter_report.filtered_files),
            'filtered_files_sample': filter_report.filtered_files[:10] if filter_report.filtered_files else []
        }
    
    def _generate_file_list_section(self, final_files: List[str]) -> Dict[str, Any]:
        """Generate file list section of artifact"""
        # Group files by extension for better organization
        files_by_extension = defaultdict(list)
        
        for file_path in final_files:
            ext = self._get_file_extension(file_path)
            files_by_extension[ext].append(file_path)
        
        return {
            'total_files': len(final_files),
            'files_by_extension': {ext: files for ext, files in files_by_extension.items()},
            'file_list': final_files[:100]  # Limit to first 100 files for size control
        }
    
    def _get_file_extension(self, file_path: str) -> str:
        """Extract file extension from path"""
        base_name = os.path.basename(file_path)
        last_dot_index = base_name.rfind('.')
        
        if last_dot_index > 0:
            return base_name[last_dot_index:]
        
        return 'no_extension'
    
    def generate_console_summary(self, artifact: Dict[str, Any]) -> str:
        """
        Generate human-readable console summary from artifact
        
        Args:
            artifact: Discovery artifact dictionary
            
        Returns:
            Formatted console summary string
        """
        summary = []
        summary.append("=" * 60)
        summary.append("FILE DISCOVERY SUMMARY")
        summary.append("=" * 60)
        
        # Add discovery statistics
        disc = artifact['discovery_summary']
        summary.append(f"Files Discovered: {disc['files_discovered']}")
        summary.append(f"Files Ignored by Rules: {disc['files_ignored_by_rule']}")
        summary.append(f"Files Ignored by Type: {disc['files_ignored_by_type']}")
        summary.append(f"Files Passed to Analysis: {disc['files_passed_to_analysis']}")
        summary.append(f"Analysis Coverage: {disc['analysis_coverage_percentage']}%")
        summary.append("-" * 60)
        
        # Add ignore processing info
        ignore = artifact['ignore_processing']
        if ignore['rules_applied']:
            summary.append(f"Ignore Rules Applied: {len(ignore['sources'])} sources")
            summary.append(f"  Sources: {', '.join(ignore['sources'])}")
            summary.append(f"  Files Ignored: {ignore['files_ignored']}")
        else:
            summary.append("No ignore rules applied")
        
        # Add file type filtering info
        filter_section = artifact['file_type_filtering']
        if filter_section['filtering_applied']:
            summary.append(f"File Type Filtering Applied")
            summary.append(f"  Supported Extensions: {len(filter_section['supported_extensions'])}")
            summary.append(f"  Files Filtered: {filter_section['files_filtered']}")
        else:
            summary.append("No file type filtering applied")
        
        summary.append("=" * 60)
        
        return '\n'.join(summary)
    
    def save_artifact_to_file(self, artifact: Dict[str, Any], output_path: str) -> bool:
        """
        Save discovery artifact to JSON file
        
        Args:
            artifact: Discovery artifact dictionary
            output_path: Path to save JSON file
            
        Returns:
            True if successful, False if failed
        """
        try:
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(artifact, f, indent=2, ensure_ascii=False)
            return True
        except Exception as e:
            logger.error(f"Failed to save discovery artifact: {str(e)}")
            return False