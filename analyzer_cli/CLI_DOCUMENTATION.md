# Hybrid Code Analyzer CLI Documentation

## Overview

The Hybrid Code Analyzer CLI provides a command-line interface for analyzing codebases and generating structured JSON output suitable for autonomous agents. The CLI wraps the existing analyzer modules and provides additional features like incremental analysis, context guardrails, and comprehensive error handling.

## Installation

The CLI is included as part of the Hybrid Code Analyzer package. No additional installation is required beyond the main package dependencies.

## Usage

### Basic Usage

```bash
hybrid_analyzer_cli --paths <file_or_directory> --output <output_file.json>
```

### Command Line Arguments

| Argument | Description | Default Value |
|----------|-------------|---------------|
| `--paths` | File paths or directories to analyze (required) | - |
| `--output` | Output JSON file path | `analysis_results.json` |
| `--task` | Task description for AI analysis | "" |
| `--timeout` | Timeout in seconds for dynamic analysis | 180 |
| `--max-context` | Maximum number of context items in output | 1000 |
| `--changed-files` | JSON file containing list of changed files for incremental analysis | "" |
| `--previous-output` | Previous analysis output JSON for incremental analysis | "" |
| `--debug` | Enable debug logging | False |

### Examples

1. **Analyze a single file:**
   ```bash
hybrid_analyzer_cli --paths src/main.py --output results.json
   ```

2. **Analyze multiple files:**
   ```bash
hybrid_analyzer_cli --paths src/main.py src/utils.py --output results.json
   ```

3. **Analyze a directory:**
   ```bash
hybrid_analyzer_cli --paths src/ --output results.json
   ```

4. **Analyze with specific task:**
   ```bash
hybrid_analyzer_cli --paths src/ --task "memory optimization" --output results.json
   ```

5. **Incremental analysis:**
   ```bash
hybrid_analyzer_cli --paths src/ --changed-files changed_files.json --previous-output previous_results.json --output results.json
   ```

6. **Custom context limits:**
   ```bash
hybrid_analyzer_cli --paths src/ --max-context 500 --output results.json
   ```

## Output Format

The CLI generates structured JSON output with the following format:

```json
{
  "static_results": [
    {
      "file_id": "unique_id",
      "file_path": "/path/to/file.py",
      "issues": [
        {
          "issue_id": "unique_id",
          "type": "security|performance|code_quality",
          "severity": "critical|high|medium|low",
          "message": "Issue description",
          "line": 42,
          "column": 5,
          "context": "Code context"
        }
      ],
      "metrics": {
        "complexity": 8.5,
        "lines_of_code": 42,
        "functions": 3,
        "classes": 0,
        "cyclomatic_complexity": 5,
        "maintainability_index": 75.2
      }
    }
  ],
  "dynamic_results": [
    {
      "function_id": "unique_id",
      "file_id": "unique_id",
      "function_name": "function_name",
      "execution_time": 0.45,
      "memory_usage": 128.7,
      "call_count": 5,
      "hotspots": [
        {
          "hotspot_id": "unique_id",
          "line": 15,
          "time_spent": 0.32,
          "percentage": 71.1,
          "context": "Code context"
        }
      ]
    }
  ],
  "AI_suggestions": [
    {
      "id": "unique_id",
      "category": "performance|security|maintainability",
      "severity": "critical|high|medium|low",
      "description": "Suggestion description",
      "related_files": ["file_id_1", "file_id_2"],
      "estimated_impact": "30% performance improvement",
      "confidence": 0.85,
      "implementation_difficulty": "easy|medium|hard"
    }
  ],
  "summary": {
    "total_files_analyzed": 1,
    "total_functions_analyzed": 5,
    "total_ai_suggestions": 2,
    "total_errors": 0,
    "total_warnings": 3,
    "total_critical_issues": 1,
    "total_high_issues": 2,
    "total_medium_issues": 4,
    "total_low_issues": 6,
    "critical_hotspots": 2,
    "analysis_completeness": 95.5
  },
  "meta": {
    "timestamp": "2026-01-20T14:30:19.199999Z",
    "analyzer_version": "1.0.0",
    "cli_version": "1.0.0",
    "arguments": {
      "paths": ["test_sample.py"],
      "task": "performance optimization",
      "timeout": 180,
      "max_context": 1000,
      "output_file": "analysis_results.json",
      "changed_files": ""
    }
  },
  "errors": []
}
```

## Features

### 1. Input Validation

- Validates file paths and extensions
- Supports common programming languages (.py, .js, .java, etc.)
- Handles single files, multiple files, and directories
- Implements size limits and safety checks

### 2. Analysis Workflow

1. **Input Validation**: Validates all inputs and discovers files
2. **Static Analysis**: Code quality, security, and complexity analysis
3. **Dynamic Analysis**: Performance profiling and execution tracing
4. **AI Analysis**: Generates improvement suggestions based on analysis results
5. **Output Formatting**: Creates structured JSON output
6. **Context Guardrails**: Limits output size to prevent context overload

### 3. Incremental Analysis

- Accepts `--changed-files` JSON file listing modified files
- Compares file timestamps and content hashes
- Only re-analyzes modified files
- Merges results with previous analysis

### 4. Context Guardrails

- Configurable maximum context items (default: 1000)
- Automatic overflow handling
- Prevents context overloading for autonomous agents
- Creates separate summary files for overflow items

### 5. Error Handling

- Comprehensive error classification
- Structured error output in JSON format
- Graceful degradation on partial failures
- Exit codes for different failure types:
  - 0: Success
  - 1: Partial issues
  - 2: Critical failure
  - 3: Timeout error
  - 4: Input error

## Exit Codes

| Exit Code | Meaning | Description |
|-----------|---------|-------------|
| 0 | SUCCESS | Analysis completed successfully |
| 1 | PARTIAL_ISSUES | Analysis completed with some issues |
| 2 | CRITICAL_FAILURE | Critical failure occurred |
| 3 | TIMEOUT_ERROR | Analysis timed out |
| 4 | INPUT_ERROR | Invalid input provided |

## Best Practices

### 1. File Selection

- Start with small, focused codebases
- Use incremental analysis for large projects
- Exclude generated files and dependencies

### 2. Performance Optimization

- Adjust `--timeout` based on codebase size
- Use `--max-context` to limit output size
- For large projects, analyze modules separately

### 3. Task Descriptions

- Be specific about optimization goals
- Examples: "memory optimization", "security audit", "performance profiling"
- Task descriptions guide AI suggestion generation

### 4. Incremental Analysis

- Maintain previous analysis results
- Track changed files between runs
- Use source control integration for best results

## Integration with Autonomous Agents

The CLI is designed for seamless integration with autonomous agents:

### Input Requirements

- Agents should provide clean file paths
- Task descriptions should be specific and actionable
- Changed files should be provided in JSON format

### Output Processing

- JSON output is machine-readable
- Unique IDs enable cross-referencing
- Structured severity levels for prioritization
- Context information for decision making

### Error Handling

- Agents should check exit codes
- Error arrays provide detailed failure information
- Partial results are still useful

## Troubleshooting

### Common Issues

1. **File not found errors**:
   - Verify file paths are correct
   - Check file permissions
   - Use absolute paths if relative paths fail

2. **Timeout errors**:
   - Increase `--timeout` value
   - Reduce codebase size
   - Analyze smaller modules separately

3. **Context overflow**:
   - Increase `--max-context` value
   - Focus on specific modules
   - Use incremental analysis

4. **Import errors**:
   - Verify Python environment
   - Check dependency installation
   - Review error messages for missing modules

### Debugging

Enable debug logging with `--debug` flag:

```bash
hybrid_analyzer_cli --paths src/ --output results.json --debug
```

## Advanced Usage

### Custom Analysis Tasks

Create custom task profiles by combining specific analysis parameters:

```bash
# Security audit
hybrid_analyzer_cli --paths src/ --task "security audit" --output security_results.json

# Performance optimization
hybrid_analyzer_cli --paths src/ --task "performance optimization" --output perf_results.json

# Code quality assessment
hybrid_analyzer_cli --paths src/ --task "code quality assessment" --output quality_results.json
```

### Continuous Integration

Integrate with CI/CD pipelines:

```bash
# Basic CI integration
hybrid_analyzer_cli --paths src/ --output ci_results.json
exit_code=$?
if [ $exit_code -ne 0 ]; then
    echo "Analysis failed with exit code $exit_code"
    exit 1
fi

# Incremental CI integration
hybrid_analyzer_cli --paths src/ --changed-files $(git diff --name-only) --output ci_results.json
```

## Future Enhancements

The CLI architecture supports future enhancements including:

- Custom analysis plugins
- Additional programming language support
- Advanced AI analysis capabilities
- Integration with version control systems
- Custom reporting formats

## Support

For issues and feature requests, please refer to the main Hybrid Code Analyzer documentation and support channels.