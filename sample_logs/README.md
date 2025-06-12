# Sample Log Files

This directory contains sample log files for testing the Enterprise Log Analyzer.

## Files Included

- **sample_healthy_system.log**: A clean system log with no errors (tests false positive elimination)
- Additional sample logs will be added here for comprehensive testing

## Usage

Test the analyzer with these samples:

```bash
# Test healthy system detection
python terminal_test.py sample_healthy_system.log

# Test with GUI
python desktop-analyzer-ultimate.py
# Then select any sample file through the interface
```

## Expected Results

- **Healthy logs**: Should show 0 errors detected
- **Problem logs**: Should identify specific issues with confidence scoring
- **No false positives**: Successful operations should not be flagged as errors