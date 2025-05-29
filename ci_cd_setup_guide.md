# CI/CD Setup Guide for Visualization Testing

The visualization testing framework is now integrated with GitHub Actions for continuous integration.

## Workflow Configuration

The main workflow file is located at: `.github/workflows/visualization_tests.yml`

### Workflow Features

1. **Multi-Platform Testing**
   - Tests run on Ubuntu, Windows, and macOS
   - Multiple Python versions (3.9, 3.10, 3.11)
   - Multiple Qt versions (6.5.0, 6.6.0)

2. **Test Types**
   - Unit tests for visualization components
   - Visual regression tests with baseline comparison
   - Performance benchmarks
   - Accessibility compliance checks
   - Integration tests

3. **Automated Baseline Management**
   - Visual baselines are stored and compared automatically
   - Diffs are generated for any visual changes
   - Baselines are uploaded as artifacts

## Triggering the Workflow

The visualization tests run automatically when:
- Code is pushed to `main` or `develop` branches
- Pull requests are created against `main`
- Changes are made to:
  - `src/ui/charts/**`
  - `src/ui/visualizations/**`
  - `tests/visual/**`
  - `tests/unit/test_visualization_*.py`

## Workflow Jobs

### 1. test-visualizations
Tests all visualization components across platforms:
```yaml
strategy:
  matrix:
    os: [ubuntu-latest, windows-latest, macos-latest]
    python-version: ['3.9', '3.10', '3.11']
    qt-version: ['6.5.0', '6.6.0']
```

### 2. coverage
Measures test coverage for visualization components:
- Target: 90%+ coverage
- Reports uploaded to Codecov

### 3. visual-diff
Compares visual baselines between branches:
- Automatically detects visual regressions
- Generates diff images for review

### 4. accessibility-audit
Runs automated accessibility testing:
- WCAG 2.1 AA compliance checks
- Color contrast validation
- Keyboard navigation testing

## Local Testing

To run the same tests locally:

```bash
# Run all visualization tests
pytest tests/visual tests/unit/test_visualization_*.py -v

# Run with coverage
pytest tests/visual --cov=src/ui/charts --cov=src/ui/visualizations

# Run visual regression tests only
pytest tests/visual -m visual

# Run performance benchmarks
pytest tests/performance -m performance --benchmark-only

# Run accessibility tests
python tests/accessibility/audit_visualizations.py
```

## Monitoring Test Results

1. **GitHub Actions UI**: View test results in the Actions tab
2. **Pull Request Checks**: Tests must pass before merging
3. **Artifacts**: Download test reports and visual diffs
4. **Coverage Reports**: View coverage trends over time

## Best Practices

1. **Before Pushing**
   - Run tests locally first
   - Update baselines if visual changes are intentional
   - Ensure accessibility compliance

2. **Visual Changes**
   - Document why visual changes were made
   - Review diff images carefully
   - Update baselines in a separate commit

3. **Performance**
   - Monitor test execution times
   - Keep test suite under 10 minutes
   - Use test markers for selective testing

## Troubleshooting

### Common Issues

1. **Qt Platform Errors**
   - Solution: Set `QT_QPA_PLATFORM=offscreen` for headless environments

2. **Missing Dependencies**
   - Solution: Install with `pip install -r requirements-test.txt`

3. **Visual Test Failures**
   - Check diff images in artifacts
   - Update baselines if changes are intentional
   - Ensure consistent rendering environment

4. **Slow Tests**
   - Use pytest-xdist for parallel execution
   - Skip slow tests with markers
   - Optimize test data generation

## Next Steps

1. Monitor initial test runs in CI/CD
2. Adjust timeout and resource limits as needed
3. Add badge to README showing test status
4. Set up notifications for test failures