# Packaging Tests

This directory contains comprehensive testing infrastructure for validating the packaged distributions of the Apple Health Dashboard application.

## Overview

The packaging tests ensure that all distribution formats (direct EXE, NSIS installer, and portable ZIP) work correctly on clean Windows 10 and Windows 11 systems. These tests validate functionality, performance, security, and user experience.

## Test Structure

```
tests/packaging/
├── README.md                      # This file
├── packaging_test_checklist.md   # Manual test checklist
├── test_packaged_app.py          # Automated test suite
├── setup_test_environment.py     # Test environment setup
├── performance_benchmarks.py     # Performance testing
├── packaging_issues_template.md  # Issue tracking
└── packaging_tests/              # Test execution directory (created by setup)
    ├── exe_tests/               # Direct EXE testing
    ├── installer_tests/         # NSIS installer testing
    ├── portable_tests/          # Portable ZIP testing
    ├── results/                 # Test results
    ├── logs/                    # Test logs
    └── screenshots/             # Test screenshots
```

## Quick Start

### 1. Set Up Test Environment

```bash
# Run on a clean Windows 10/11 system
python tests/packaging/setup_test_environment.py
```

This will:
- Check system prerequisites
- Create test directories
- Generate sample test data
- Clean existing app data
- Create test report templates

### 2. Run Automated Tests

For direct EXE:
```bash
python tests/packaging/test_packaged_app.py dist/AppleHealthDashboard.exe
```

For comprehensive testing:
```bash
cd packaging_tests
run_packaging_tests.bat
```

### 3. Run Performance Benchmarks

```bash
python tests/packaging/performance_benchmarks.py dist/AppleHealthDashboard.exe
```

### 4. Manual Testing

Follow the checklist in `packaging_test_checklist.md` for comprehensive manual validation.

## Test Categories

### Installation Tests
- First run behavior
- File associations
- Registry entries
- Shortcuts and menu items
- Upgrade scenarios

### Feature Tests
- Data import (XML/CSV)
- All dashboards (Daily/Weekly/Monthly)
- Charts and visualizations
- Journal functionality
- Settings persistence
- Export capabilities

### Performance Tests
- Startup time (<5 seconds requirement)
- Memory usage
- CPU utilization
- File operation speed
- UI responsiveness

### Security Tests
- Code signing validation
- Antivirus compatibility
- Permissions required
- Data protection

### Update Tests
- Clean updates
- Skip version updates
- Data preservation
- Settings migration

### Uninstall Tests
- Complete removal
- User data handling
- Registry cleanup

## Automated Test Suite

The `test_packaged_app.py` script provides automated testing for:

- **Startup Performance**: Measures cold and warm start times
- **Memory Usage**: Monitors memory consumption over time
- **CPU Usage**: Tracks CPU utilization patterns
- **File Operations**: Validates data persistence
- **Portable Mode**: Ensures proper portable operation

### Running Automated Tests

Basic usage:
```bash
python test_packaged_app.py <path_to_exe>
```

With benchmarking:
```bash
python test_packaged_app.py <path_to_exe> --benchmark
```

### Test Results

Results are saved to `packaging_test_results.json` with format:
```json
{
  "exe_path": "path/to/exe",
  "test_time": "2025-06-02T23:00:00",
  "os_version": "Windows 10.0.19045",
  "results": {
    "startup_time": {
      "value": 3.2,
      "passed": true,
      "target": 5.0
    },
    ...
  }
}
```

## Performance Benchmarking

The `performance_benchmarks.py` script provides detailed performance analysis:

- **Cold Start**: First run after system restart
- **Warm Start**: Subsequent application launches
- **Memory Profile**: Usage patterns over time
- **CPU Profile**: Processing patterns and idle behavior
- **I/O Operations**: File handling performance

### Benchmark Results

Results include statistical analysis:
- Average, median, min/max values
- Standard deviation
- Performance target compliance
- System configuration context

## Issue Tracking

Use `packaging_issues_template.md` to document any issues found:

1. Assign unique ID (PKG-XXX)
2. Document severity and affected formats
3. Provide clear reproduction steps
4. Include screenshots/logs if applicable
5. Document workarounds
6. Track resolution status

## Test Environments

### Minimum Requirements
- Windows 10 version 1809 or later
- Windows 11 version 22H2 or later
- 4GB RAM minimum
- 10GB free disk space
- .NET Framework 4.8
- Visual C++ Redistributable 2015-2022

### Clean System Setup
1. Use fresh VM or clean Windows install
2. No development tools installed
3. Default security settings
4. Windows Defender enabled

## Best Practices

1. **Test on Clean Systems**: Always use fresh VMs or clean installs
2. **Document Everything**: Use templates for consistency
3. **Test All Formats**: Don't skip any distribution format
4. **Performance Baselines**: Compare against documented targets
5. **Security Validation**: Check signing and AV compatibility
6. **User Perspective**: Test as a non-technical user would

## Troubleshooting

### Common Issues

**Issue**: Tests fail to find window
**Solution**: Ensure executable has UI and check window title

**Issue**: Permission denied errors
**Solution**: Run from user-writable directory, not Program Files

**Issue**: Slow performance on first run
**Solution**: Normal behavior - use warm start benchmarks

### Debug Mode

Set environment variable for verbose output:
```bash
set DEBUG_PACKAGING_TESTS=1
python test_packaged_app.py dist/AppleHealthDashboard.exe
```

## CI/CD Integration

For automated builds, integrate these tests:

```yaml
# Example GitHub Actions
- name: Run Packaging Tests
  run: |
    python tests/packaging/test_packaged_app.py dist/AppleHealthDashboard.exe
    python tests/packaging/performance_benchmarks.py dist/AppleHealthDashboard.exe
```

## Reporting

After testing, compile results into a release readiness report:

1. Automated test results
2. Performance benchmark summary
3. Manual test checklist completion
4. Issue summary with severity
5. Go/No-go recommendation

## Contact

For questions about packaging tests:
- Check existing issues in `packaging_issues_template.md`
- Review test output logs
- Consult troubleshooting guide (T07_S07)