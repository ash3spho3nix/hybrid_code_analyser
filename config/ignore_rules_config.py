from typing import List

# Default ignore rules when no ignore files exist
DEFAULT_IGNORE_RULES = [
    # Common non-code directories
    "node_modules/",
    "venv/",
    ".venv/",
    "env/",
    ".env/",
    "__pycache__/",
    ".pyc",
    
    # Build artifacts
    "build/",
    "dist/",
    "*.egg-info/",
    ".egg-info/",
    
    # Test files
    "test_*.py",
    "*.test.py",
    "tests/",
    
    # Common non-code files
    "*.log",
    "*.tmp",
    "*.bak",
    "*.swp",
    
    # IDE-specific files
    ".idea/",
    ".vscode/",
    "*.iml",
    
    # Documentation
    "docs/",
    "*.md",
    "*.rst",
    
    # Configuration files
    "*.ini",
    "*.cfg",
    "*.conf",
    
    # Database files
    "*.db",
    "*.sqlite",
    "*.sqlite3",
    
    # Virtual environment markers
    "pyvenv.cfg",
    ".python-version",
]

def get_default_ignore_rules() -> List[str]:
    """
    Get default ignore rules from configuration
    
    Returns:
        List of default ignore patterns
    
    This function provides a set of sensible default ignore rules that are used
    when no .analyzerignore, .gitignore, or .kilocodeignore files are found
    in the project root directory.
    
    The default rules include:
    - Common non-code directories (node_modules, venv, etc.)
    - Build artifacts and distribution files
    - Test files and directories
    - Common non-code file extensions
    - IDE-specific files and directories
    - Documentation files
    - Configuration files
    - Database files
    - Virtual environment markers
    
    These defaults can be customized by creating an .analyzerignore file
    in the project root directory.
    """
    return DEFAULT_IGNORE_RULES.copy()