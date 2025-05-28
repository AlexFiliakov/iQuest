# G075: Test Suite Repair Coordination and Execution Strategy

## Status: in_progress
Priority: HIGH
Type: COORDINATION
Parallel: This is the master coordination task
Started: 2025-05-28 00:00

## Overview
This task coordinates the parallel execution of test suite repairs across 8 major work streams. The goal is to fix all test failures while maintaining code quality and test coverage.

## Test Failure Summary
- Total unique failing test methods: ~400+
- Most affected: comprehensive unit coverage (43), UI components (24), performance (20)
- Critical paths: DailyMetricsCalculator, UI imports, Integration mocks

## Detailed Task Breakdown

### Phase 1: Critical Foundation (Parallel - Week 1)
**Must complete first as other tasks depend on these:**

#### G067: Fix DailyMetricsCalculator initialization
- **Impact**: Unblocks 43+ tests
- **Approach**: Adapter pattern (recommended)
- **Effort**: 3-4 days
- **Dependencies**: None
- **Deliverables**:
  - DataSource protocol definition
  - DataFrame adapter implementation
  - Updated calculator initialization
  - Migration guide

#### G068: Repair UI component imports
- **Impact**: Unblocks all UI tests
- **Approach**: Module reorganization (recommended)
- **Effort**: 2-3 days
- **Dependencies**: None
- **Deliverables**:
  - New module structure
  - Import fix script
  - Updated __init__.py files
  - Import documentation

#### G074: Update test data generators
- **Impact**: Foundation for all test data
- **Approach**: Modular generator system (recommended)
- **Effort**: 4-5 days
- **Dependencies**: None
- **Deliverables**:
  - New generator framework
  - Health data generators
  - Fixture factory
  - Migration script

### Phase 2: Test Infrastructure (Parallel - Week 1-2)
**Can start after Phase 1 basics are working:**

#### G069: Fix integration test mocks
- **Impact**: Fixes 20+ integration tests
- **Approach**: Protocol-based mocks (recommended)
- **Effort**: 3-4 days
- **Dependencies**: G074 partially
- **Deliverables**:
  - Mock data source implementations
  - Test fixture factory
  - Interface compliance tests
  - Testing guide

#### G071: Fix performance benchmarks
- **Impact**: 20 performance tests
- **Approach**: Hybrid pytest-benchmark + custom (recommended)
- **Effort**: 3-4 days
- **Dependencies**: G074 for data generation
- **Deliverables**:
  - Benchmark infrastructure
  - Adaptive thresholds
  - CI/CD integration
  - Performance baselines

#### G072: Repair visual regression tests
- **Impact**: 19 visual tests
- **Approach**: Perceptual comparison (recommended)
- **Effort**: 3-4 days
- **Dependencies**: G068 for UI components
- **Deliverables**:
  - Visual test framework
  - Platform-specific baselines
  - Comparison algorithms
  - Baseline update tools

#### G073: Fix cache/database tests
- **Impact**: 11 cache tests + database tests
- **Approach**: Hybrid in-memory/file approach (recommended)
- **Effort**: 2-3 days
- **Dependencies**: None
- **Deliverables**:
  - Test database factory
  - Time mocking utilities
  - Transaction helpers
  - Isolation fixtures

### Phase 3: Consolidation (Sequential - Week 2)
**Must wait for all other fixes:**

#### G070: Consolidate and prune duplicate tests
- **Impact**: Reduce test count by 40%
- **Approach**: Moderate refactoring (recommended)
- **Effort**: 3-4 days
- **Dependencies**: All other tasks complete
- **Deliverables**:
  - Test coverage analysis
  - Consolidated test files
  - New test structure
  - Performance report

## Execution Plan

### Week 1 Schedule
```
Day 1-2: Start G067, G068, G074 in parallel
Day 3-4: Continue Phase 1, start G069, G073
Day 5: Phase 1 integration testing, start G071, G072
```

### Week 2 Schedule
```
Day 1-2: Complete Phase 2 tasks
Day 3: Integration of all fixes
Day 4-5: Execute G070 consolidation
```

## Branch Strategy
```
main
├── test-repair-main (integration branch)
│   ├── fix/g067-calculator-init
│   ├── fix/g068-ui-imports
│   ├── fix/g069-test-mocks
│   ├── fix/g070-consolidation
│   ├── fix/g071-performance
│   ├── fix/g072-visual-tests
│   ├── fix/g073-cache-tests
│   └── fix/g074-data-generators
```

## Integration Checklist
For each task completion:
- [ ] All task-specific tests pass
- [ ] No regression in other areas
- [ ] Documentation updated
- [ ] Code review completed
- [ ] Merged to test-repair-main
- [ ] Full test suite run

## Communication Plan

### Daily Standups (15 min)
- What was completed yesterday
- What's planned for today
- Any blockers or dependencies

### Integration Points
- End of Phase 1: Full integration test
- Mid Phase 2: Cross-task compatibility check
- Before Phase 3: Complete system test

### Documentation Requirements
Each task must deliver:
1. Implementation documentation
2. Migration guide (if applicable)
3. Updated test patterns guide
4. Known issues/limitations

## Success Criteria
- [ ] All ~400 failing tests now pass
- [ ] Test execution time < 5 minutes
- [ ] Zero flaky tests
- [ ] Code coverage ≥ 90%
- [ ] All platform tests pass (Windows, Linux, macOS)
- [ ] Performance benchmarks established
- [ ] Visual baselines created
- [ ] Documentation complete

## Risk Mitigation

### Technical Risks
1. **Dependency conflicts**
   - Mitigation: Daily integration tests
   - Fallback: Feature flags for gradual rollout

2. **Performance regression**
   - Mitigation: Benchmark before/after
   - Fallback: Keep old test suite temporarily

3. **Platform differences**
   - Mitigation: Test on all platforms daily
   - Fallback: Platform-specific fixes

### Process Risks
1. **Scope creep**
   - Mitigation: Stick to defined approaches
   - Fallback: Defer enhancements to Phase 4

2. **Integration conflicts**
   - Mitigation: Frequent merges to integration branch
   - Fallback: Pair programming for conflicts

## Claude Output Log
[2025-05-28 00:00]: Started test coordination task
[2025-05-28 00:00]: Analyzed current test status - 692 tests collected with 15 collection errors
[2025-05-28 00:00]: Primary issues identified: PyQt6 imports (11 tests), Type annotation errors (4 tests)
[2025-05-28 00:00]: Need to check PyQt6 installation and fix typing imports before proceeding with coordination

## Immediate Action Items
1. **Fix PyQt6 dependency issue** - Check requirements.txt and virtual environment
2. **Fix typing imports** - Add missing `Any` imports in performance test modules
3. **Re-assess test execution plan** based on actual current state

## Post-Repair Phase 4 (Optional)
After all tests pass:
1. Performance optimization pass
2. Additional test coverage for gaps
3. Test execution parallelization
4. CI/CD optimization
5. Test dashboard creation