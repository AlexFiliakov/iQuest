# Test Repair Tasks for Remaining Failures

## Overview
This document organizes test repair tasks based on failure analysis from `tests/pytest_failure_summaries.txt`. Tasks are grouped by type and priority for efficient parallel execution.

## Task Categories

### 🔴 Priority 1: API/Constructor Issues (Can be done in parallel)

#### Task 1.1: Fix MetricStatistics Constructor Issues
**Files Affected:**
- `src/analytics/comparative_analytics.py`
- Related test files

**Error:** `MetricStatistics.__init__() got an unexpected keyword argument 'metric_name'`

**Subtasks:**
1. **Option A: Update MetricStatistics class**
   - Add `metric_name` parameter to constructor
   - **Pros:** Maintains backward compatibility, adds useful metadata
   - **Cons:** May require updates to all instantiation sites
   ```python
   def __init__(self, ..., metric_name: Optional[str] = None):
       self.metric_name = metric_name
   ```

2. **Option B: Remove metric_name from callers**
   - Update comparative_analytics.py to not pass metric_name
   - **Pros:** Simpler, no API changes
   - **Cons:** Loses potentially useful information

**Recommended:** Option A - Add parameter with default None

#### Task 1.2: Fix Activity Level Validation
**Error:** `Invalid activity level: moderate`

**Subtasks:**
1. Update activity level enum/validation to include 'moderate'
2. Add comprehensive activity level constants
```python
ACTIVITY_LEVELS = ['sedentary', 'light', 'moderate', 'active', 'very_active']
```

### 🟡 Priority 2: Database Issues (Sequential execution required)

#### Task 2.1: Fix Database Table Creation
**Error:** `no such table: health_records`

**Subtasks:**
1. **Analyze database schema initialization**
   - Check if migrations are missing
   - Verify table creation order

2. **Fix initialization sequence**
   - **Option A:** Add explicit table creation in test setup
   ```python
   @pytest.fixture
   def db_with_tables():
       db = create_test_db()
       db.create_all_tables()  # Ensure all tables exist
       return db
   ```
   
   - **Option B:** Use alembic migrations in tests
   - **Pros:** Matches production behavior
   - **Cons:** Slower test execution

**Recommended:** Option A for test speed

### 🟢 Priority 3: Calculation/Algorithm Issues (Can be done in parallel)

#### Task 3.1: Fix SVD Convergence in Health Score
**Error:** `SVD did not converge in Linear Least Squares`

**Subtasks:**
1. **Add numerical stability checks**
   ```python
   try:
       result = np.linalg.lstsq(A, b, rcond=None)
   except np.linalg.LinAlgError:
       # Fallback to regularized solution
       result = np.linalg.lstsq(A + 1e-10 * np.eye(A.shape[0]), b, rcond=None)
   ```

2. **Validate input data**
   - Check for NaN/Inf values
   - Ensure matrix is not singular

#### Task 3.2: Fix Seasonal Decomposition Parameters
**Error:** `seasonal must be an odd positive integer >= 3`

**Subtasks:**
1. **Validate period parameter**
   ```python
   def get_seasonal_period(data_length):
       period = min(data_length // 2, 365)  # Annual seasonality
       return period if period % 2 == 1 else period + 1  # Ensure odd
   ```

2. **Add data length checks**
   - Minimum data requirement: 2 * period + 1

### 🔵 Priority 4: UI/Integration Test Issues

#### Task 4.1: Fix Dashboard Performance Tests
**Affected Tests:**
- `test_scalability_performance[10/50/100]`

**Subtasks:**
1. **Mock heavy operations**
   ```python
   @patch('src.ui.core_health_dashboard.DailyMetricsCalculator')
   def test_scalability_performance(mock_calculator):
       mock_calculator.return_value.calculate.return_value = mock_data
   ```

2. **Add performance benchmarks**
   - Set realistic thresholds
   - Use pytest-benchmark properly

#### Task 4.2: Fix Week-over-Week Integration Tests
**Subtasks:**
1. **Fix prediction integration**
   - Ensure sufficient historical data
   - Mock ML model responses

2. **Fix edge case handling**
   - Add validation for minimum data requirements
   - Return appropriate error states

### 🟣 Priority 5: Chaos Testing Issues

#### Task 5.1: Improve Data Validation
**Affected Tests:**
- `test_handle_corrupted_step_data`
- `test_handle_missing_date_columns`
- `test_handle_duplicate_dates`

**Subtasks:**
1. **Implement robust data cleaning**
   ```python
   def clean_health_data(df):
       # Remove duplicates
       df = df.drop_duplicates(subset=['date', 'type'])
       
       # Handle missing dates
       if 'date' not in df.columns and 'creationDate' in df.columns:
           df['date'] = df['creationDate']
       
       # Validate data types
       df['value'] = pd.to_numeric(df['value'], errors='coerce')
       df = df.dropna(subset=['date', 'value'])
       
       return df
   ```

2. **Add comprehensive error handling**
   - Log specific issues
   - Provide meaningful error messages

## Execution Plan

### Phase 1: Parallel Execution (Tasks 1.1, 1.2, 3.1, 3.2)
- Estimated time: 2-3 hours
- Can be assigned to different developers

### Phase 2: Sequential Execution (Task 2.1)
- Estimated time: 1-2 hours
- Must be done before integration tests

### Phase 3: Integration Testing (Tasks 4.1, 4.2)
- Estimated time: 2-3 hours
- Depends on Phase 1 & 2

### Phase 4: Chaos Testing (Task 5.1)
- Estimated time: 1-2 hours
- Can run in parallel with Phase 3

## Testing Strategy

1. **Run targeted tests after each fix**
   ```bash
   pytest tests/integration/test_comparative_analytics_integration.py -xvs
   ```

2. **Verify no regression**
   ```bash
   pytest tests/unit -x
   ```

3. **Final full suite run**
   ```bash
   pytest --cov=src --cov-report=html
   ```

## Success Criteria

- All identified test failures resolved
- No regression in previously passing tests
- Code coverage maintained or improved
- Performance benchmarks met

## Notes

- Consider adding more comprehensive fixtures for integration tests
- Database initialization should be standardized across all tests
- Performance tests may need environment-specific thresholds