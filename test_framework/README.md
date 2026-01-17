# Hybrid Code Analyzer Test Framework

This is the comprehensive test framework for validating the hybrid code analyzer's failure reporting and FAISS-based error similarity detection capabilities.

## Overview

The test framework consists of several components that work together to ensure the hybrid code analyzer functions correctly:

1. **Controlled Failure Zoo** - Predefined test cases with known failure patterns
2. **Regression Memory Test** - FAISS-based error similarity detection validation
3. **Validation Engine** - Core validation logic for analyzer outputs
4. **Test Execution Scripts** - Main scripts to run the complete test suite

## Directory Structure

```
test_framework/
├── validation_engine/                    # Core validation components
│   ├── analyzer_validator.py             # Validates analyzer output
│   ├── faiss_validator.py                # Validates FAISS behavior
│   └── test_reporter.py                  # Generates comprehensive reports
├── regression_tests/                     # FAISS regression tests
│   ├── faiss_validator.py                # FAISS validation logic
│   ├── similarity_scorer.py              # Error similarity scoring
│   └── (test_runner.py would go here)    # Main test execution
├── scripts/                             # Test execution scripts
│   ├── run_failure_zoo.py                # Run failure zoo tests
│   ├── run_regression_tests.py           # Run FAISS regression tests
│   ├── run_all_tests.py                  # Run complete test suite
│   ├── validate_results.py               # Validate test results
│   └── generate_test_report.py           # Generate comprehensive report
├── results/                             # Test results storage
│   ├── failure_zoo_results.json          # Failure zoo test results
│   ├── regression_results/               # Regression test results
│   ├── analyzer_validation_results.json  # Analyzer validation results
│   ├── faiss_validation_results.json     # FAISS validation results
│   └── comprehensive_report.json         # Final comprehensive report
└── README.md                             # This documentation
```

## Components

### 1. Validation Engine

The validation engine contains the core validation logic:

- **analyzer_validator.py**: Validates analyzer output including:
  - Analysis status correctness (complete/partial/failed)
  - Execution failures accuracy and completeness
  - Coverage percentages
  - Completeness context
  - No false successes

- **faiss_validator.py**: Validates FAISS behavior including:
  - Vector similarity scores
  - FAISS ID stability across runs
  - Metadata consistency
  - Error clustering behavior
  - Index persistence

- **test_reporter.py**: Generates comprehensive reports with:
  - Aggregated results from all components
  - JSON reports in exact format from design
  - Human-readable summaries
  - Detailed metrics and statistics
  - Component-level status tracking

### 2. Test Execution Scripts

The scripts directory contains the main execution scripts:

- **run_failure_zoo.py**: Executes all failure zoo test cases
  - Iterates through all failure categories
  - Validates against expected outputs
  - Generates failure zoo test report

- **run_regression_tests.py**: Executes FAISS regression tests
  - Runs the 3-run test sequence
  - Validates FAISS behavior
  - Generates regression test report

- **run_all_tests.py**: Main script for complete test suite
  - Runs failure zoo tests
  - Runs regression memory tests
  - Runs validation engine tests
  - Generates comprehensive final report

- **validate_results.py**: Validates test results
  - Checks pass/fail conditions
  - Generates validation report
  - Handles result persistence

- **generate_test_report.py**: Generates comprehensive reports
  - Aggregates all test results
  - Creates human-readable summaries
  - Provides detailed metrics

### 3. Failure Zoo

The failure zoo contains predefined test cases in `test_failure_zoo/`:

- **missing_import**: Tests import error detection
- **circular_import**: Tests circular import detection
- **syntax_error**: Tests syntax error detection
- **runtime_exception**: Tests runtime exception handling
- **missing_dependency**: Tests dependency error detection
- **ignored_by_rules**: Tests file exclusion by rules
- **discovered_not_executed**: Tests discovery without execution

Each test case includes:
- Test files that induce specific failures
- `expected_output.json` with expected analyzer output
- Comprehensive validation criteria

## Usage

### Running the Complete Test Suite

```bash
# Run the complete test suite
python test_framework/scripts/run_all_tests.py

# With verbose output
python test_framework/scripts/run_all_tests.py --verbose

# Skip specific components
python test_framework/scripts/run_all_tests.py --skip-regression --verbose
```

### Running Individual Components

```bash
# Run failure zoo tests only
python test_framework/scripts/run_failure_zoo.py

# Run regression tests only
python test_framework/scripts/run_regression_tests.py

# Validate results
python test_framework/scripts/validate_results.py

# Generate comprehensive report
python test_framework/scripts/generate_test_report.py --human-readable
```

### Running Validation Engine Components

```bash
# Run analyzer validator
python test_framework/validation_engine/analyzer_validator.py

# Run FAISS validator
python test_framework/validation_engine/faiss_validator.py

# Run test reporter
python test_framework/validation_engine/test_reporter.py
```

## Test Architecture

The test framework follows a comprehensive architecture:

1. **Controlled Failure Zoo**: Predefined test cases with known failure patterns
2. **Regression Memory Test**: FAISS-based error similarity detection validation
3. **Validation Engine**: Core validation logic for analyzer outputs
4. **Test Reporting**: Comprehensive reporting and metrics

### Test Validation Criteria

**Test Pass Conditions:**
1. All induced failures are detected and reported
2. No false successes are reported
3. Analysis status correctly reflects completeness
4. Coverage percentages are accurate
5. Completeness context provides meaningful explanation

**Test Fail Conditions:**
1. Any induced failure is not detected
2. Analysis reports "complete" status when failures exist
3. Coverage percentages are inaccurate
4. Missing or incorrect completeness context

### FAISS Validation Requirements

1. **Vector Stability**: FAISS IDs must remain stable across runs
2. **Metadata Consistency**: Record ID to FAISS ID mappings must be preserved
3. **Index Persistence**: FAISS index must be saved and loaded correctly
4. **Vector Removal**: Resolved errors must be properly handled in FAISS

## Expected Test Outputs

### Failure Zoo Test Output

```json
{
  "test_name": "Controlled Failure Zoo",
  "timestamp": "2026-01-17T16:00:00Z",
  "test_cases": [
    {
      "category": "missing_import",
      "status": "PASS",
      "expected_failures": 1,
      "actual_failures": 1,
      "analysis_status": "partial",
      "coverage_percentage": 0.0,
      "validation_results": {
        "failure_detection": "PASS",
        "status_accuracy": "PASS",
        "coverage_accuracy": "PASS",
        "completeness_context": "PASS"
      }
    }
  ],
  "summary": {
    "total_tests": 7,
    "passed_tests": 7,
    "failed_tests": 0,
    "overall_status": "PASS"
  }
}
```

### Regression Test Output

```json
{
  "test_name": "FAISS Regression Memory Test",
  "timestamp": "2026-01-17T16:00:00Z",
  "test_runs": [
    {
      "run_number": 1,
      "description": "Initial run with full failure zoo",
      "faiss_stats": {
        "vectors_added": 7,
        "index_size": 7,
        "metadata_consistency": "PASS"
      }
    }
  ],
  "summary": {
    "faiss_behavior": "PASS",
    "vector_stability": "PASS",
    "similarity_detection": "PASS",
    "error_clustering": "PASS",
    "overall_status": "PASS"
  }
}
```

## Test Framework Success Criteria

The test framework is considered successful when:

1. **Failure Zoo Tests**: All 7 failure categories pass validation
2. **Regression Tests**: All 3 test runs show correct FAISS behavior
3. **Validation Engine**: All analyzer outputs are correctly validated
4. **Reporting**: Comprehensive test reports are generated
5. **Reproducibility**: Tests can be run multiple times with consistent results

## Implementation Details

### Analyzer Validator

The analyzer validator checks:
- Analysis status correctness (complete/partial/failed)
- Execution failures accuracy and completeness
- Coverage percentages match expected values
- Completeness context provides meaningful explanations
- No false successes are reported

### FAISS Validator

The FAISS validator checks:
- Vector similarity scores meet expected criteria
- FAISS ID stability across multiple runs
- Metadata consistency and proper indexing
- Error clustering behavior
- Proper index persistence and file management

### Test Reporter

The test reporter provides:
- Aggregated results from all test components
- Comprehensive JSON report in exact format from design
- Human-readable summary with pass/fail status
- Detailed metrics and statistics
- Component-level status tracking

## Troubleshooting

### Common Issues

1. **Missing test results files**: Ensure all test components have been run before generating reports
2. **FAISS index not found**: Run regression tests first to generate the FAISS index
3. **Validation failures**: Check individual component outputs for specific errors

### Debugging

```bash
# Run with verbose output to see detailed logs
python test_framework/scripts/run_all_tests.py --verbose

# Check individual component results
ls -la test_framework/results/

# View specific result files
cat test_framework/results/failure_zoo_results.json
```

## Future Enhancements

1. **Additional failure categories**: Expand the failure zoo with more test cases
2. **Performance metrics**: Add timing and resource usage tracking
3. **CI/CD integration**: Add support for continuous integration pipelines
4. **Visualization**: Add graphical representations of test results
5. **Automated test generation**: Generate test cases automatically from code analysis

## License

This test framework is part of the hybrid code analyzer project and follows the same licensing terms.