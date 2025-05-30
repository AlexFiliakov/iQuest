# Test Infrastructure Next Steps

Created: 2025-05-30 14:45
Related to: G085_FIX_BROKEN_TESTS

## Remaining Test Issues

### 1. Integration Test Failures
**Status**: Not investigated
**Observations**: 
- Integration tests are timing out in some cases
- May be related to database setup/teardown
- Some tests passed when run individually

**Effective Approach**:
- Run integration tests individually to identify specific failures
- Check for resource cleanup issues between tests
- Consider adding test isolation fixtures
- Review database transaction handling in tests

### 2. Performance Test Failures
**Status**: Partially fixed
**Observations**:
- Fixed the monthly calculator AttributeError
- Many other performance tests still failing with API mismatches
- Tests expect different method names or return values

**Effective Approach**:
- Systematically review each failing performance test
- Update test expectations to match current API
- Consider if the implementation or tests should be changed
- Document any API changes discovered

### 3. Deprecation Warnings

#### Direct DataFrame Usage
**Status**: Not addressed
**Count**: ~200+ warnings
**Pattern**: "Direct DataFrame usage is deprecated. Please use DataSourceProtocol implementations."

**Effective Approach**:
- Create a DataSourceProtocol adapter for tests
- Update test fixtures to use the protocol
- Consider creating a test-specific data source implementation
- This is a significant refactor but improves test quality

#### Pytest-asyncio Configuration
**Status**: Configuration exists but warning persists
**Issue**: Warning appears despite asyncio_default_fixture_loop_scope being set in pytest.ini

**Effective Approach**:
- Verify pytest.ini is being read correctly
- Check if the warning is from a specific plugin version
- Consider updating pytest-asyncio version
- May need to set configuration programmatically in conftest.py

### 4. Test Coverage Analysis
**Status**: Not performed
**Goal**: Maintain 80%+ coverage

**Effective Approach**:
- Run `pytest --cov=src --cov-report=html`
- Identify modules with low coverage
- Focus on critical business logic first
- Add tests for error handling paths

### 5. Visual Regression Tests
**Status**: Not investigated
**Observations**: Visual tests exist but status unknown

**Effective Approach**:
- Check if baseline images exist
- Run visual tests on current platform
- Update baselines if UI has legitimately changed
- Consider platform-specific baselines

## Successful Patterns Discovered

1. **Clear Test Isolation**: Clearing database records and in-memory state before tests prevents cross-test contamination

2. **API Verification**: When tests fail with AttributeError, check the actual implementation first rather than assuming the test is correct

3. **Flexible Assertions**: For time-based tests, use ranges rather than exact values (e.g., `24 <= days <= 25`)

4. **Skip vs Fix**: For complex tests requiring specific conditions, consider skipping with clear messages rather than creating fragile fixes

## Priority Recommendations

1. **High Priority**: Fix remaining integration test failures - these test real user workflows
2. **Medium Priority**: Address Direct DataFrame deprecation warnings - improves code quality
3. **Low Priority**: Update performance baselines - can be done as needed
4. **Optional**: Visual regression tests - only if UI testing is critical

## Testing Philosophy Notes

The test suite appears to be comprehensive but has accumulated technical debt. The most effective approach is:

1. Fix critical failures that block CI/CD
2. Address deprecations that will become errors in future versions
3. Improve test isolation to prevent flaky tests
4. Document any API changes discovered during fixes

The goal should be a reliable test suite that gives developers confidence, not 100% pass rate at any cost.