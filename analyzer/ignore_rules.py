import os
import re
from typing import List, Tuple, Pattern
import logging

# Set up logger
logger = logging.getLogger(__name__)

class IgnoreRule:
    def __init__(self, pattern: str, source: str, line_number: int):
        """Initialize an ignore rule"""
        self.pattern = pattern
        self.source = source
        self.line_number = line_number
        self.compiled_pattern = self._compile_pattern(pattern)
        
    def _compile_pattern(self, pattern: str) -> Pattern:
        """
        Compile gitignore-style pattern to regex
        
        Args:
            pattern: Gitignore-style pattern
            
        Returns:
            Compiled regex pattern
        """
        # Handle common gitignore patterns
        gitignore_pattern = pattern
        
        # Escape special regex characters except * and ?
        gitignore_pattern = re.escape(gitignore_pattern)
        
        # Convert * to .*
        gitignore_pattern = gitignore_pattern.replace(r'\*', '.*')
        
        # Convert ? to .
        gitignore_pattern = gitignore_pattern.replace(r'\?', '.')
        
        # Handle directory patterns (trailing /)
        if pattern.endswith('/'):
            gitignore_pattern = gitignore_pattern[:-2] + '.*/'  # Remove escaped / and add .*/
        
        # Handle ** for recursive directory matching
        if '**' in pattern:
            gitignore_pattern = gitignore_pattern.replace(r'\*\*', '.*')
        
        # Anchor pattern to match from start
        compiled = re.compile(f'^{gitignore_pattern}')
        
        return compiled
    
    def matches(self, file_path: str) -> bool:
        """
        Check if this rule matches the given file path
        
        Args:
            file_path: Path to check against the rule
            
        Returns:
            True if the path matches the rule
        """
        # Normalize path for consistent matching
        normalized_path = os.path.normpath(file_path)
        
        # Convert to forward slashes for consistent matching
        normalized_path = normalized_path.replace('\\', '/')
        
        # Check if pattern matches
        return bool(self.compiled_pattern.match(normalized_path))
    
    def __repr__(self) -> str:
        return f"IgnoreRule(pattern='{self.pattern}', source='{self.source}')"

class IgnoreRulesProcessor:
    def __init__(self):
        """Initialize the ignore rules processor"""
        self.pattern_cache = {}  # Cache for parsed patterns
        self.rule_cache = {}     # Cache for loaded rules per directory
        
    def load_ignore_rules(self, root_path: str, analyzer_type: str = None) -> List[IgnoreRule]:
        """
        Load and merge ignore rules from multiple sources
        
        Args:
            root_path: Root directory to search for ignore files
            analyzer_type: Optional analyzer type for specific ignore files
            
        Returns:
            List of IgnoreRule objects in precedence order
        """
        rules = []
        
        # Check cache first
        cache_key = f"{root_path}:{analyzer_type}"
        if cache_key in self.rule_cache:
            logger.debug(f"Cache hit for ignore rules at {root_path}")
            return self.rule_cache[cache_key]
        
        # 1. Load .gitignore (highest priority)
        gitignore_path = os.path.join(root_path, '.gitignore')
        if os.path.exists(gitignore_path):
            gitignore_rules = self._parse_gitignore_file(gitignore_path, '.gitignore')
            rules.extend(gitignore_rules)
        
        # 2. Load .kilocodeignore
        kiloignore_path = os.path.join(root_path, '.kilocodeignore')
        if os.path.exists(kiloignore_path):
            kiloignore_rules = self._parse_gitignore_file(kiloignore_path, '.kilocodeignore')
            rules.extend(kiloignore_rules)
        
        # 3. Load analyzer-specific ignore file (lowest priority)
        if analyzer_type:
            analyzer_ignore = os.path.join(root_path, f'.{analyzer_type}ignore')
            if os.path.exists(analyzer_ignore):
                analyzer_rules = self._parse_gitignore_file(analyzer_ignore, f'.{analyzer_type}ignore')
                rules.extend(analyzer_rules)
        
        # Cache the rules
        self.rule_cache[cache_key] = rules
        logger.debug(f"Cached {len(rules)} ignore rules for {root_path}")
        
        return rules
    
    def should_ignore_file(self, file_path: str, rules: List[IgnoreRule]) -> Tuple[bool, str]:
        """
        Check if a file should be ignored based on the rules
        
        Args:
            file_path: Path to check
            rules: List of IgnoreRule objects to apply
            
        Returns:
            Tuple of (should_ignore, reason)
        """
        if not rules:
            return False, "No ignore rules applied"
        
        # Check each rule in order (precedence already handled by load order)
        for rule in rules:
            if rule.matches(file_path):
                return True, f"Ignored by {rule.source} [pattern: {rule.pattern}]"
        
        return False, "Not ignored by any rule"
    
    def _parse_gitignore_file(self, file_path: str, source: str) -> List[IgnoreRule]:
        """
        Parse a gitignore-style file and convert to IgnoreRule objects
        
        Args:
            file_path: Path to the ignore file
            source: Source identifier (e.g., '.gitignore')
            
        Returns:
            List of IgnoreRule objects
        """
        rules = []
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                for line_num, line in enumerate(f, 1):
                    line = line.strip()
                    
                    # Skip empty lines and comments
                    if not line or line.startswith('#'):
                        continue
                    
                    # Skip negation patterns for now (could be added later)
                    if line.startswith('!'):
                        continue
                    
                    # Create ignore rule
                    rule = IgnoreRule(pattern=line, source=source, line_number=line_num)
                    rules.append(rule)
        
        except Exception as e:
            # Log error but continue with empty rules
            logger.warning(f"Failed to parse {source} at {file_path}: {str(e)}")
        
        return rules