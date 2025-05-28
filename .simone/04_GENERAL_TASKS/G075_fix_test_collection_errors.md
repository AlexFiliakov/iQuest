---
task_id: G075
status: open
complexity: Medium
last_updated: 2025-05-28T11:25:00Z
---

# Fix Test Collection Errors

## Description
Address the 6 test collection errors identified during test consolidation that prevent proper test discovery and execution. These errors are blocking full test suite validation and need to be resolved to ensure the consolidated test structure works correctly.

## Goal / Objectives
- Resolve all test collection errors in the test suite
- Ensure all distributed and consolidated tests can be discovered by pytest
- Validate that test imports and dependencies are correctly structured
- Enable reliable test execution across all test categories

## Acceptance Criteria
- [ ] All 6 test collection errors are identified and fixed
- [ ] `pytest --collect-only` runs without errors across all test directories
- [ ] All distributed test files can be imported successfully
- [ ] Consolidated widget tests are properly discovered
- [ ] Test markers are correctly applied and functional
- [ ] No import errors or missing dependencies in test files

## Subtasks
- [ ] Run pytest collection with verbose output to identify specific error locations
- [ ] Fix import paths in distributed test files
- [ ] Resolve missing dependency issues in test files
- [ ] Validate base test class inheritance is working correctly
- [ ] Test consolidated widget file collection
- [ ] Verify all test markers are properly recognized
- [ ] Run full collection test across unit/, integration/, ui/ directories

## Output Log
*(This section is populated as work progresses on the task)*