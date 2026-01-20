import os
from typing import List, Dict, Any, Tuple, Optional

# Add these imports at the top of the file
from analyzer.ignore_rules import IgnoreRulesProcessor
from analyzer.file_type_filter import FileTypeFilter, FileTypeFilterReport
from analyzer.path_validator import PathScopeValidator, PathValidationResult
from analyzer.discovery_artifact import DiscoveryArtifactGenerator

# Note: IgnoreReport is defined locally in this file to maintain compatibility
# with the existing DiscoveryResult structure and avoid circular imports.


class DiscoveryResult:
    def __init__(self):
        self.files_discovered = 0
        self.files_ignored_by_rule = 0
        self.files_ignored_by_type = 0
        self.files_passed_to_analysis = 0
        self.ignore_report = None
        self.type_filter_report = None
        self.discovery_artifact = None
        # Initialize files_for_analysis to prevent AttributeError
        self.files_for_analysis = []

    def to_dict(self) -> Dict[str, Any]:
        """Convert discovery result to dictionary for JSON serialization"""
        return {
            'files_discovered': self.files_discovered,
            'files_ignored_by_rule': self.files_ignored_by_rule,
            'files_ignored_by_type': self.files_ignored_by_type,
            'files_passed_to_analysis': self.files_passed_to_analysis,
            'ignore_report': self.ignore_report.to_dict() if self.ignore_report else None,
            'type_filter_report': self.type_filter_report.to_dict() if self.type_filter_report else None,
            'discovery_artifact': self.discovery_artifact
        }


class IgnoreReport:
    def __init__(self):
        self.ignored_files = []
        self.ignore_sources = set()
        self.patterns_applied = set()
        self.rules_source = None  # Track which source was used
        self.fallback_used = False  # Track if fallback was used

    @property
    def total_files_ignored(self) -> int:
        """Get total number of files ignored"""
        return len(self.ignored_files)

    def set_rules_source(self, source: str, is_fallback: bool = False):
        """Set the source of ignore rules"""
        self.rules_source = source
        self.fallback_used = is_fallback

    def add_ignored_file(self, file_path: str, reason: str):
        """Add a file to the ignore report with reason"""
        self.ignored_files.append({'file': file_path, 'reason': reason})

        # Extract source and pattern from reason
        if 'Ignored by' in reason and '[' in reason and ']' in reason:
            # Extract source from "Ignored by SOURCE [pattern: PATTERN]"
            source_part = reason.split('Ignored by ')[1].split(' [')[0]
            self.ignore_sources.add(source_part)
            
            # Extract pattern from "[pattern: PATTERN]"
            if 'pattern:' in reason:
                pattern = reason.split('pattern:')[1].split(']')[0].strip()
                self.patterns_applied.add(pattern)

    def to_dict(self) -> Dict[str, Any]:
        """Convert ignore report to dictionary"""
        return {
            'total_files_ignored': self.total_files_ignored,
            'ignore_sources': list(self.ignore_sources),
            'patterns_applied': list(self.patterns_applied),
            'rules_source': self.rules_source,
            'fallback_used': self.fallback_used,
            'ignored_files': self.ignored_files
        }


class FileDiscoveryService:
    def __init__(self):
        """Initialize the file discovery service with real implementations"""
        # Initialize with real component instances
        self.ignore_processor = IgnoreRulesProcessor()
        self.file_type_filter = FileTypeFilter()
        self.path_validator = PathScopeValidator()
        self.artifact_generator = DiscoveryArtifactGenerator()


    def discover_files(self, root_paths: List[str], analyzer_type: str = None) -> DiscoveryResult:
        """
        Main file discovery method with full ignore processing
        
        Args:
            root_paths: List of root folder paths to search
            analyzer_type: Optional analyzer type for specific ignore files
        
        Returns:
            DiscoveryResult object containing all discovery data
        """
        # Initialize discovery result early to ensure it always exists
        discovery_result = DiscoveryResult()
        
        try:
            # 1. Validate input paths
            validation_result = self.path_validator.validate_paths(root_paths)
            if not validation_result.is_valid:
                raise ValueError(f"Invalid paths: {validation_result.errors}")
            
            # 2. Discover all files in root paths
            all_files = self._discover_all_files(root_paths)
            
            # 3. Apply ignore rules
            filtered_files, ignore_report = self._apply_ignore_rules(all_files, root_paths, analyzer_type)
            
            # 4. Apply file type filtering
            code_files, type_filter_report = self.file_type_filter.filter_files(filtered_files)
            
            # 5. Generate discovery artifacts
            artifact = self.artifact_generator.generate_artifact(
                all_files,
                ignore_report,
                type_filter_report,
                code_files
            )
            
            # Create DiscoveryResult object from the artifact
            discovery_result.files_discovered = artifact['discovery_summary']['files_discovered']
            discovery_result.files_ignored_by_rule = artifact['discovery_summary']['files_ignored_by_rule']
            discovery_result.files_ignored_by_type = artifact['discovery_summary']['files_ignored_by_type']
            discovery_result.files_passed_to_analysis = artifact['discovery_summary']['files_passed_to_analysis']
            discovery_result.ignore_report = ignore_report
            discovery_result.type_filter_report = type_filter_report
            discovery_result.discovery_artifact = artifact
            # Store the actual file list for use by analyzers
            discovery_result.files_for_analysis = code_files
            
        except Exception as e:
            # Ensure files_for_analysis is always set even on error
            discovery_result.files_for_analysis = []
            # Re-raise the exception to let caller handle it
            raise
        
        return discovery_result

    def _discover_all_files(self, root_paths: List[str]) -> List[str]:
        """
        Recursively discover all files in the given root paths
        
        Args:
            root_paths: List of root paths to search
        
        Returns:
            List of all file paths found
        """
        all_files = []
        for root_path in root_paths:
            try:
                for dirpath, dirnames, filenames in os.walk(root_path):
                    for filename in filenames:
                        file_path = os.path.join(dirpath, filename)
                        # Normalize path for consistency
                        normalized_path = os.path.normpath(file_path)
                        all_files.append(normalized_path)
            except PermissionError:
                # Skip directories we don't have permission to access
                continue
            except OSError as e:
                # Handle other filesystem errors
                print(f"Warning: Could not access {root_path}: {e}")
                continue
        return all_files

    def _apply_ignore_rules(self, files: List[str], root_paths: List[str], analyzer_type: str = None):
        """
        Apply ignore rules to the list of files using real implementations
        """
        # Load ignore rules from all root paths
        all_ignore_rules = []
        ignore_report = IgnoreReport()
        
        for root_path in root_paths:
            rules = self.ignore_processor.load_ignore_rules(root_path, analyzer_type)
            
            # Track which source was used
            if rules:
                source = "unknown"
                if rules[0].source == '.analyzerignore':
                    source = '.analyzerignore'
                elif rules[0].source == '.gitignore':
                    source = '.gitignore'
                elif rules[0].source == '.kilocodeignore':
                    source = '.kilocodeignore'
                elif rules[0].source == 'default_config':
                    source = 'default_config'
                    ignore_report.set_rules_source(source, is_fallback=True)
                else:
                    source = rules[0].source
                
                ignore_report.set_rules_source(source, is_fallback=(source == 'default_config'))
            
            all_ignore_rules.extend(rules)

        # Apply ignore rules to each file
        filtered_files = []

        for file_path in files:
            should_ignore, reason = self.ignore_processor.should_ignore_file(file_path, all_ignore_rules)
            if should_ignore:
                ignore_report.add_ignored_file(file_path, reason)
            else:
                filtered_files.append(file_path)

        return filtered_files, ignore_report
