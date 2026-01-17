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

    @property
    def total_files_ignored(self) -> int:
        """Get total number of files ignored"""
        return len(self.ignored_files)

    def add_ignored_file(self, file_path: str, reason: str):
        """Add a file to the ignore report with reason"""
        self.ignored_files.append({'file': file_path, 'reason': reason})

        # Extract source and pattern from reason
        if '[' in reason and ']' in reason:
            source = reason.split('[')[1].split(']')[0]
            self.ignore_sources.add(source)
            pattern = reason.split('pattern:')[1].strip() if 'pattern:' in reason else 'unknown'
            self.patterns_applied.add(pattern)

    def to_dict(self) -> Dict[str, Any]:
        """Convert ignore report to dictionary"""
        return {
            'total_files_ignored': self.total_files_ignored,
            'ignore_sources': list(self.ignore_sources),
            'patterns_applied': list(self.patterns_applied),
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
        discovery_result = DiscoveryResult()
        discovery_result.files_discovered = artifact['discovery_summary']['files_discovered']
        discovery_result.files_ignored_by_rule = artifact['discovery_summary']['files_ignored_by_rule']
        discovery_result.files_ignored_by_type = artifact['discovery_summary']['files_ignored_by_type']
        discovery_result.files_passed_to_analysis = artifact['discovery_summary']['files_passed_to_analysis']
        discovery_result.ignore_report = ignore_report
        discovery_result.type_filter_report = type_filter_report
        discovery_result.discovery_artifact = artifact
        # Store the actual file list for use by analyzers
        discovery_result.files_for_analysis = code_files
        
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
        Apply ignore rules to the list of files
        
        Args:
            files: List of file paths to filter
            root_paths: Root paths for ignore file discovery
            analyzer_type: Optional analyzer type for specific ignore files
            
        Returns:
            Tuple of (filtered_files, ignore_report)
        """
        # Load ignore rules from all root paths
        all_ignore_rules = []
        for root_path in root_paths:
            try:
                rules = self.ignore_processor.load_ignore_rules(root_path, analyzer_type)
                all_ignore_rules.extend(rules)
            except Exception as e:
                print(f"Warning: Could not load ignore rules from {root_path}: {e}")
                continue

        # Apply ignore rules to each file
        filtered_files = []
        ignore_report = IgnoreReport()

        for file_path in files:
            try:
                should_ignore, reason = self.ignore_processor.should_ignore_file(file_path, all_ignore_rules)
                if should_ignore:
                    ignore_report.add_ignored_file(file_path, reason)
                else:
                    filtered_files.append(file_path)
            except Exception as e:
                # If there's an error checking ignore rules, include the file
                print(f"Warning: Error checking ignore rules for {file_path}: {e}")
                filtered_files.append(file_path)

        return filtered_files, ignore_report