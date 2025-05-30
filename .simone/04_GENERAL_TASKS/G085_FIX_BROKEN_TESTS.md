---
task_id: G085
sprint_sequence_id: null
status: open
complexity: High
last_updated: 2025-05-30T00:00:00Z
---

# Task: Fix Broken Tests

## Description
Address failing tests in the Apple Health Monitor test suite. Recent test runs show multiple failures across unit, integration, and performance test categories. This task involves diagnosing test failures, fixing broken tests, and ensuring the test suite runs successfully with good coverage.

## Goal / Objectives
Restore the test suite to a passing state while maintaining or improving code coverage.
- Fix all failing unit tests
- Fix all failing integration tests  
- Fix all failing performance tests
- Ensure test coverage remains above 80%
- Update any outdated test fixtures or mocks

## Acceptance Criteria
- [ ] All unit tests pass (`pytest tests/unit/`)
- [ ] All integration tests pass (`pytest tests/integration/`)
- [ ] All performance tests pass (`pytest tests/performance/`)
- [ ] Overall test coverage is >= 80%
- [ ] No flaky tests (tests pass consistently)
- [ ] Test execution time is reasonable (< 5 minutes for full suite)

## Subtasks
- [x] Run full test suite and catalog all failures
- [x] Analyze pytest failure summaries in tests/ directory
- [x] Group failures by root cause (e.g., missing mocks, outdated fixtures, actual bugs)
- [ ] Fix unit test failures
  - [ ] Address Qt import issues in WCAG validator tests
  - [ ] Fix AttributeError in monthly calculator performance tests
  - [ ] Fix GroupChallenge initialization failures
  - [ ] Fix AchievementSystem test failures
  - [ ] Fix PersonalRecordsTracker detection failures
  - [ ] Update tests for recent code changes
- [ ] Fix integration test failures
  - [ ] Ensure proper database setup/teardown
  - [ ] Update integration test data
  - [ ] Fix timing/async issues
- [ ] Fix performance test failures
  - [ ] Fix monthly calculator performance test AttributeError
  - [ ] Update performance baselines if needed
  - [ ] Address timeout problems
- [ ] Fix warnings
  - [ ] Configure pytest-asyncio fixture loop scope
  - [ ] Fix pandas FutureWarning for fillna method
  - [ ] Fix numpy RuntimeWarnings for invalid values
  - [ ] Fix DeprecationWarning for Direct DataFrame usage
  - [ ] Register pytest.mark.chaos custom mark
- [ ] Run coverage analysis and improve if needed
- [ ] Document any significant test infrastructure changes

## Detailed Subtask Analysis

### 1. Qt Import Issues (test_accessibility_compliance.py)
**Problem**: WCAG validator tests fail with "name 'Qt' is not defined"
**Root Cause**: Missing import of Qt from PyQt6.QtCore in wcag_validator.py
**Approach**: 
- Add proper import: `from PyQt6.QtCore import Qt`
- Verify all Qt usage in accessibility modules has proper imports
- Consider creating a common imports module for PyQt6 components

### 2. AttributeError in Monthly Calculator Performance Tests
**Problem**: `'MonthlyMetrics' object has no attribute 'stats'`
**Root Cause**: Test expects benchmark result to have stats attribute, but MonthlyMetrics object is returned instead
**Approach**:
- Review test_calculator_benchmarks.py line 128
- Either fix the test to access correct attributes or update calculator to return expected format
- Check if API changed between test creation and current implementation

### 3. GroupChallenge Test Failures (test_peer_group_comparison.py)
**Problem**: GroupChallenge initialization and active status tests fail
**Root Cause**: Likely missing or changed constructor parameters
**Approach**:
- Review GroupChallenge class definition in peer_group_comparison.py
- Update test fixtures to match current constructor signature
- Verify challenge lifecycle methods work as expected

### 4. AchievementSystem Test Failures (test_personal_records_tracker.py)
**Problem**: Achievement tests return empty lists when achievements expected
**Root Cause**: Achievement criteria may have changed or system not properly initialized
**Approach**:
- Review achievement trigger conditions in personal_records_tracker.py
- Ensure test data meets achievement criteria
- Check if achievement system requires explicit initialization

### 5. PersonalRecordsTracker Detection Failures
**Problem**: Record detection returning fewer records than expected
**Root Cause**: Detection algorithms may have stricter criteria or data not meeting thresholds
**Approach**:
- Review detection logic for single day and rolling average records
- Adjust test data to ensure records are detectable
- Consider if thresholds need adjustment or parameterization

### 6. Deprecation Warnings
**Problem**: Multiple deprecation warnings for pandas, numpy, and custom code
**Root Cause**: Using outdated APIs
**Approach**:
- Replace `fillna(method='ffill')` with `ffill()`
- Update Direct DataFrame usage to use DataSourceProtocol
- Configure pytest-asyncio properly in pytest.ini
- Register custom pytest marks

## Consolidated Problem Categories

### Category 1: Import and Dependency Issues
- **Qt Import Error**: WCAG validator missing PyQt6 imports
- **Module Import Error**: test_chaos_scenarios.py has incorrect import path
- **Tradeoffs**: 
  - Quick fix: Add missing imports individually
  - Better approach: Create centralized import management for PyQt6 components
  - Best approach: Audit all modules for import consistency and create import guidelines

### Category 2: API Mismatches Between Tests and Implementation
- **Monthly Calculator**: Test expects benchmark stats, gets MonthlyMetrics object
- **Achievement System**: Tests expect achievements that aren't triggered
- **Personal Records**: Detection criteria mismatch between tests and implementation
- **Tradeoffs**:
  - Update tests to match current API (faster, maintains current functionality)
  - Update implementation to match test expectations (ensures backward compatibility)
  - Create adapter layer for backward compatibility while moving forward

### Category 3: Deprecation and Future Compatibility
- **pandas fillna**: Need to use ffill()/bfill() instead of method parameter
- **Direct DataFrame usage**: Should use DataSourceProtocol
- **pytest-asyncio configuration**: Needs explicit loop scope setting
- **Tradeoffs**:
  - Minimal changes: Just fix warnings (quick but may break later)
  - Proper refactor: Update to modern patterns throughout codebase
  - Gradual migration: Fix critical issues now, plan migration for others

### Category 4: Test Infrastructure Issues
- **Unknown pytest marks**: chaos mark not registered
- **Test timeouts**: Some test suites timing out
- **Coverage gaps**: Need to maintain 80%+ coverage
- **Tradeoffs**:
  - Quick fixes in pytest.ini for marks and timeouts
  - Comprehensive test infrastructure overhaul
  - Selective optimization of slow tests

## Implementation Priority

1. **Critical Fixes** (blocks all testing):
   - Fix Qt imports in WCAG validator
   - Fix monthly calculator performance test
   - Configure pytest-asyncio

2. **High Priority** (multiple test failures):
   - Fix achievement and records detection logic
   - Update deprecated pandas calls
   - Register pytest marks

3. **Medium Priority** (warnings and improvements):
   - Migrate to DataSourceProtocol
   - Optimize slow tests
   - Improve test data generators

4. **Low Priority** (nice to have):
   - Comprehensive import audit
   - Test infrastructure documentation
   - Performance baseline updates

## Output Log
*(This section is populated as work progresses on the task)*

[2025-05-30 00:00:00] Task created
[2025-05-30 08:45:00] Analyzed test failures and categorized issues
[2025-05-30 08:45:00] Created detailed subtasks with root cause analysis
[2025-05-30 08:45:00] Consolidated issues into 4 main categories
[2025-05-30 08:45:00] Defined implementation priorities and tradeoffs