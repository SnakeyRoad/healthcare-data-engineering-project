# Healthcare Data Engineering Project - System Tests

This directory contains system tests for the healthcare data engineering ETL pipeline.

## System Test Overview

The system test analyzes existing ETL outputs and logs to provide a comprehensive overview of:
- ETL pipeline performance
- Data quality metrics
- Query execution performance
- System health and file integrity

## Files

- `system_test.py` - Main system test script
- `system_test_report.txt` - Generated test report (created after running the test)
- `system_test.log` - Log file for the system test itself

## How to Run the System Test

### Prerequisites
1. Ensure the ETL pipeline has been run at least once
2. Activate the virtual environment: `source venv/bin/activate`

### Running the Test
```bash
python tests/system_test.py
```

### What the Test Does
1. **Analyzes ETL Logs**: Extracts performance metrics, errors, and warnings from log files
2. **Analyzes Data Quality**: Reads quality reports to assess data integrity
3. **Analyzes Query Performance**: Measures query execution times and identifies performance issues
4. **Checks System Health**: Validates file integrity and data completeness
5. **Generates Report**: Creates a comprehensive test report

## Understanding the Test Report

### Test Status
- **PASSED**: All checks passed, no issues detected
- **WARNING**: Some issues found but not critical
- **FAILED**: Critical issues detected

### Report Sections

#### ETL Performance Summary
- Total records processed
- Data quality score
- ETL step execution times
- Number of log files analyzed

#### Data Quality Summary
- Overall quality score
- Table-specific quality scores
- Missing data analysis
- Validation issues

#### Query Performance Summary
- Number of queries executed
- Execution times for each query
- Performance issues (queries taking >1 second)
- Sample query results

#### System Health Summary
- Total record counts by dataset
- File integrity status
- Data completeness checks
- Recommendations for improvement

## Exit Codes
- `0`: Test passed successfully
- `1`: Test failed with critical issues
- `2`: Test completed with warnings

## Best Practices

### When to Run
- After completing the ETL pipeline
- Before submitting assignments
- When troubleshooting issues
- For performance monitoring

### What to Look For
- **Performance Issues**: Queries taking longer than 1 second
- **Data Quality**: Scores below 95%
- **Missing Files**: Expected output files not found
- **Errors**: Any ERROR entries in logs

### Interpreting Results
- **Green (OK)**: Everything is working correctly
- **Yellow (WARNING)**: Minor issues that should be investigated
- **Red (ERROR)**: Critical issues that need immediate attention

## Customization

The system test can be customized by modifying:
- Performance thresholds in `system_test.py`
- File patterns to check
- Quality score requirements
- Output format preferences

## Troubleshooting

### Common Issues
1. **No log files found**: Run the ETL pipeline first
2. **Missing quality reports**: Ensure data cleaning completed successfully
3. **Empty output files**: Check for ETL errors
4. **Permission errors**: Ensure proper file permissions

### Debug Mode
For detailed debugging, check the `system_test.log` file in this directory.

## Integration with CI/CD

The system test can be integrated into continuous integration pipelines:
```bash
# Example CI command
python tests/system_test.py
if [ $? -eq 0 ]; then
    echo "System test passed"
else
    echo "System test failed"
    exit 1
fi
``` 