# G090: Background Metrics Processing for Activity Timeline

## Overview
Implement background processing for the Activity Timeline component to prevent UI freezing and show insights progressively as they become available.

---
task_id: G090
status: planned
complexity: High
last_updated: 2025-06-01 18:21
---

## Problem Statement
The Activity Timeline in the Daily tab performs heavy ML operations (KMeans clustering, DBSCAN anomaly detection, correlation analysis) synchronously on the main thread, causing:
- UI freezes during processing
- Empty timeline until all processing completes
- Poor user experience with no feedback
- This is a critical hotfix that must be implemented before work on this sprint can progress

## Proposed Solution: QThread-based Background Processing

### Architecture Overview
```
Main Thread                          Background Thread
-----------                          -----------------
ActivityTimelineComponent     <-->   TimelineAnalyticsWorker
  |                                        |
  |- Basic data display                    |- KMeans clustering
  |- Progress indicators                   |- DBSCAN anomaly detection
  |- Progressive updates                   |- Correlation analysis
  |                                        |- Pattern detection
  v                                        |
TimelineInsightsPanel                      v
  |                                   Emits signals with results
  |- Shows available insights
  |- Updates as data arrives
```

## Implementation Plan

### Phase 1: Create Analytics Worker Thread

#### Task 1.1: Design TimelineAnalyticsWorker class
- **File**: `src/analytics/timeline_analytics_worker.py`
- **Selected Approach**: Option A - Single worker with sequential processing
- **Subtasks**:
  - Define worker signals: `progress_updated`, `insights_ready`, `error_occurred`
  - Implement run() method with proper exception handling
  - Add cancellation support via QThread.isInterruptionRequested()

#### Task 1.2: Move analytics methods to worker
- **Subtasks**:
  - Extract `perform_clustering()` logic
  - Extract `detect_activity_patterns()` logic
  - Extract `calculate_correlations()` logic
  - Ensure methods are thread-safe (no GUI updates)
  - Add progress reporting between steps

### Phase 2: Modify ActivityTimelineComponent

#### Task 2.1: Implement progressive data display
- **Show raw timeline immediately**
  - Display basic hourly data without analytics
  - Add "Analyzing..." indicator
  - Pros: Immediate visual feedback
  - Cons: May show "boring" data initially

- **Subtasks**:
  - Split `update_data()` into `update_data_immediate()` and `start_analytics()`
  - Create basic timeline visualization without ML insights
  - Add loading indicators to UI

#### Task 2.2: Integrate worker thread
- **Reuse single worker instance**
  - Pros: Better performance, can queue requests
  - Cons: Need to handle state/cancellation
  
- **Subtasks**:
  - Initialize worker in `__init__()`
  - Connect worker signals to update methods
  - Implement proper cleanup in destructor
  - Add request queuing/cancellation logic

#### Task 2.3: Handle progressive updates
- **Option A: Update after each analytics step**
  - Show patterns → then anomalies → then correlations
  - Pros: Most responsive feel
  - Cons: Multiple UI updates
  
- **Subtasks**:
  - Create `update_insights_partial()` method
  - Implement insight priority system
  - Add visual indicators for pending analyses

### Phase 3: Update TimelineInsightsPanel

#### Task 3.1: Support partial data updates
- **Subtasks**:
  - Modify `update_insights()` to accept partial data
  - Add "loading" states to insight cards
  - Implement graceful handling of None values
  - Show placeholder text while loading

#### Task 3.2: Add progress indicators
- **Single progress indicator** ✓ (Recommended)
  - Small spinner or progress in timeline header
  - Pros: Cleaner UI
  - Cons: Less granular feedback
  
- **Subtasks**:
  - Add QProgressBar or custom spinner
  - Connect to worker progress signals
  - Auto-hide when complete

### Phase 4: Optimization & Polish

#### Task 4.1: Implement smart caching
  **Disk cache with memory LRU** ✓ (Recommended)
  - Use existing cache_manager infrastructure
  - Pros: Persistent, leverages existing code
  - Cons: More complex
  
- **Subtasks**:
  - Define cache key structure
  - Integrate with project's cache_manager
  - Add cache invalidation logic
  - Implement cache warming on date change

#### Task 4.2: Add cancellation support
- **Subtasks**:
  - Cancel previous analysis when date changes
  - Add "Cancel Analysis" button if taking too long
  - Ensure clean thread termination
  - Handle partial results appropriately

## Implementation Considerations

### Thread Safety
- No direct GUI updates from worker thread
- Use signals/slots for all communication
- Protect shared data with locks if needed
- Ensure pandas operations are thread-safe

### Error Handling
- Graceful degradation if analytics fail
- Show basic timeline even if ML fails
- Log errors without crashing
- User-friendly error messages

### Testing Strategy
1. Unit tests for worker analytics methods
2. UI tests for progressive updates
3. Error injection tests

## Risks & Mitigations

### Risk 1: Thread synchronization issues
- **Mitigation**: Use Qt's signal/slot mechanism exclusively
- **Mitigation**: Avoid shared mutable state

### Risk 2: Memory leaks from threads
- **Mitigation**: Proper thread cleanup in destructors
- **Mitigation**: Use QThread's built-in management

### Risk 3: Confusing partial results
- **Mitigation**: Clear loading indicators
- **Mitigation**: Consistent insight ordering

## Alternative Approaches Considered

### QThreadPool with QRunnable
- Pros: Better for many small tasks
- Cons: Less control, harder cancellation
- **Decision**: Not suitable for our long-running analytics

### AsyncIO/Concurrent.futures
- Pros: Modern Python approach
- Cons: Mixing with Qt event loop is complex
- **Decision**: Stick with Qt's threading model

### Web Worker Pattern (via QWebEngine)
- Pros: True isolation
- Cons: Massive overhead, complex data passing
- **Decision**: Over-engineered for this use case

## Success Criteria
1. Timeline shows basic data within 100ms
2. No UI freezing during analysis
3. Insights appear progressively
4. Analysis can be cancelled cleanly
5. Cached results load instantly

## Next Steps
1. Create TimelineAnalyticsWorker class
2. Refactor ActivityTimelineComponent incrementally
3. Test with real data at each phase
