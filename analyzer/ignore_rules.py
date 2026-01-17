import os
import re
from typing import List, Tuple, Pattern, Dict, Any
import logging

# Set up logger
logger = logging.getLogger(__name__)

# Add this import at the top of the file
from config.ignore_rules_config import get_default_ignore_rules

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
        self.default_rules = get_default_ignore_rules()  # Load default rules
    
    def load_ignore_rules(self, root_path: str, analyzer_type: str = None) -> List[IgnoreRule]:
        """
        Load and merge ignore rules with new precedence logic

        NEW PRECEDENCE ORDER:
        1. .analyzerignore (highest priority)
        2. .gitignore
        3. .kilocodeignore
        4. Default rules from config (fallback)

        Args:
            root_path: Root directory to search for ignore files
            analyzer_type: Optional analyzer type (not used in new logic)

        Returns:
            List of IgnoreRule objects in precedence order
        """
        rules = []
        
        # Check cache first
        cache_key = f"{root_path}:{analyzer_type}"
        if cache_key in self.rule_cache:
            logger.debug(f"Cache hit for ignore rules at {root_path}")
            return self.rule_cache[cache_key]
        
        # NEW LOGIC: Check .analyzerignore FIRST (highest priority)
        analyzerignore_path = os.path.join(root_path, '.analyzerignore')
        if os.path.exists(analyzerignore_path):
            logger.info(f"Using .analyzerignore rules from {analyzerignore_path}")
            analyzerignore_rules = self._parse_gitignore_file(analyzerignore_path, '.analyzerignore')
            rules.extend(analyzerignore_rules)
            self.rule_cache[cache_key] = rules
            return rules  # Return immediately - .analyzerignore takes full precedence
        
        # SECOND: Check .gitignore
        gitignore_path = os.path.join(root_path, '.gitignore')
        if os.path.exists(gitignore_path):
            logger.info(f"Using .gitignore rules from {gitignore_path}")
            gitignore_rules = self._parse_gitignore_file(gitignore_path, '.gitignore')
            rules.extend(gitignore_rules)
            self.rule_cache[cache_key] = rules
            return rules
        
        # THIRD: Check .kilocodeignore
        kiloignore_path = os.path.join(root_path, '.kilocodeignore')
        if os.path.exists(kiloignore_path):
            logger.info(f"Using .kilocodeignore rules from {kiloignore_path}")
            kiloignore_rules = self._parse_gitignore_file(kiloignore_path, '.kilocodeignore')
            rules.extend(kiloignore_rules)
            self.rule_cache[cache_key] = rules
            return rules
        
        # FOURTH: Use default rules from configuration
        logger.info("No ignore files found, using default ignore rules")
        default_rules = []
        for pattern in self.default_rules:
            rule = IgnoreRule(pattern=pattern, source='default_config', line_number=0)
            default_rules.append(rule)

        self.rule_cache[cache_key] = default_rules
        return default_rules
    
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