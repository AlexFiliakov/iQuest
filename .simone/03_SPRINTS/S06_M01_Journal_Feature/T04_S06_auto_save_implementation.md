---
task_id: T04_S06
sprint_sequence_id: S06
status: open
complexity: Medium
last_updated: 2025-01-28T00:00:00Z
dependencies: ["T02_S06", "T03_S06"]
---

# Task: Auto-Save Implementation

## Description
Implement auto-save functionality with debouncing to prevent data loss while users type their journal entries. The system should save drafts periodically and indicate save status to users without interrupting their writing flow.

## Goal / Objectives
- Implement debounced auto-save (save after 3 seconds of inactivity)
- Show save status indicator in UI
- Handle save conflicts gracefully
- Minimize performance impact while typing
- Recover unsaved work after crashes

## Acceptance Criteria
- [ ] Auto-save triggers after 3 seconds of no typing
- [ ] Save status indicator shows: "Saving...", "Saved", "Error"
- [ ] Manual save (Ctrl+S) works alongside auto-save
- [ ] No UI freezing during auto-save operations
- [ ] Draft recovery works after application crash
- [ ] Auto-save can be disabled in settings
- [ ] Performance impact <5% while typing
- [ ] Network/database errors don't interrupt typing

## Implementation Analysis

### Debouncing Strategy
**Options:**
1. **Simple Timer Reset** - Reset timer on each keystroke
   - Pros: Easy to implement, predictable behavior
   - Cons: May never save during continuous typing
2. **Hybrid Approach** - Debounce with max interval
   - Pros: Guarantees save within time window, balances responsiveness
   - Cons: More complex state management
3. **Incremental Save** - Save chunks as user types
   - Pros: Minimal data loss, progressive saving
   - Cons: Complex implementation, potential conflicts

**Recommendation:** Hybrid Approach (#2) - Best balance of UX and data safety

### Draft Storage Mechanism
- **Separate Database Table** - journal_drafts table
   - Pros: Clean separation, transaction safety, queryable
   - Cons: Schema maintenance, migration complexity

### Conflict Resolution
- **Version Comparison** - Check timestamps/hashes
   - Pros: Detects conflicts, safe
   - Cons: User intervention needed

## Detailed Subtasks

### 1. AutoSaveManager Class Implementation
- [ ] Create src/ui/auto_save_manager.py module
- [ ] Define AutoSaveManager(QObject) class:
  ```python
  class AutoSaveManager(QObject):
      saveRequested = pyqtSignal(str, str, str)  # date, type, content
      saveCompleted = pyqtSignal(bool, str)  # success, message
      statusChanged = pyqtSignal(str)  # status text
  ```
- [ ] Implement configuration properties:
  - [ ] debounce_delay: int = 3000  # milliseconds
  - [ ] max_wait_time: int = 30000  # force save after 30s
  - [ ] enabled: bool = True
  - [ ] save_drafts: bool = True
- [ ] Create internal state tracking:
  - [ ] last_save_time: datetime
  - [ ] pending_save: bool
  - [ ] content_hash: str
  - [ ] save_in_progress: bool

### 2. Debouncing Logic Implementation
- [ ] Create DebouncedTimer class:
  ```python
  class DebouncedTimer:
      def __init__(self, delay: int, max_wait: int):
          self.timer = QTimer()
          self.max_timer = QTimer()
          self.last_reset = time.time()
  ```
- [ ] Implement reset() method with max wait tracking
- [ ] Add force_trigger() for immediate save
- [ ] Handle timer lifecycle (start/stop/cleanup)
- [ ] Add unit tests for edge cases:
  - [ ] Rapid resets
  - [ ] Max wait timeout
  - [ ] Timer cleanup

### 3. Save Status Indicator Widget
- [ ] Create SaveStatusIndicator(QWidget):
  - [ ] Use QHBoxLayout with icon and label
  - [ ] Implement status states:
    - [ ] Idle: No icon, empty text
    - [ ] Modified: "●" icon, "Modified"
    - [ ] Saving: Spinner animation, "Saving..."
    - [ ] Saved: "✓" icon, "Saved at HH:MM"
    - [ ] Error: "⚠" icon, "Save failed"
- [ ] Add fade animations between states
- [ ] Style with warm colors:
  ```python
  self.setStyleSheet("""
      QLabel {
          color: #8B7355;
          font-size: 12px;
      }
      .saved { color: #95C17B; }
      .error { color: #E76F51; }
  """)
  ```
- [ ] Add click handler to show error details

### 4. Draft Storage Schema
- [ ] Create journal_drafts table:
  ```sql
  CREATE TABLE journal_drafts (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      entry_date DATE NOT NULL,
      entry_type VARCHAR(10) NOT NULL,
      content TEXT NOT NULL,
      content_hash VARCHAR(64),
      saved_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
      session_id VARCHAR(36),
      is_recovered BOOLEAN DEFAULT FALSE,
      UNIQUE(entry_date, entry_type, session_id)
  );
  ```
- [ ] Add indexes for performance:
  - [ ] idx_drafts_date_type ON (entry_date, entry_type)
  - [ ] idx_drafts_session ON session_id
  - [ ] idx_drafts_saved_at ON saved_at
- [ ] Create cleanup trigger for old drafts (>7 days)

### 5. Text Change Detection
- [ ] Connect to QPlainTextEdit.textChanged signal
- [ ] Implement content comparison:
  - [ ] Track character count changes
  - [ ] Calculate content hash (MD5/SHA256)
  - [ ] Detect meaningful changes (ignore whitespace-only)
- [ ] Add change categorization:
  - [ ] Minor: <10 character change
  - [ ] Major: >100 character change
  - [ ] Structural: Paragraph additions/deletions
- [ ] Optimize for performance:
  - [ ] Incremental hash calculation
  - [ ] Batch change notifications

### 6. Background Save Worker
- [ ] Create SaveWorker(QThread) class:
  ```python
  class SaveWorker(QThread):
      progress = pyqtSignal(int)
      finished = pyqtSignal(bool, str)
      error = pyqtSignal(str)
  ```
- [ ] Implement thread-safe database operations
- [ ] Add connection pooling for threads
- [ ] Handle interruption gracefully
- [ ] Implement retry logic:
  - [ ] Max retries: 5
  - [ ] Exponential backoff
  - [ ] Error categorization

### 7. Save Queue Implementation
- [ ] Create SaveQueue class with deque
- [ ] Implement queue operations:
  - [ ] enqueue(): Add save request
  - [ ] dequeue(): Get next save
  - [ ] clear(): Remove duplicates
  - [ ] prioritize(): Move to front
- [ ] Add persistence for offline mode:
  ```python
  class PersistentQueue:
      def __init__(self, file_path):
          self.queue = deque()
          self.persist_file = file_path
  ```
- [ ] Implement queue limits (max 100 items)
- [ ] Add queue status monitoring

### 8. Conflict Resolution System
- [ ] Create ConflictResolver class
- [ ] Implement version tracking:
  - [ ] Generate version IDs (UUID)
  - [ ] Track modification timestamps
  - [ ] Store version metadata
- [ ] Build conflict detection:
  ```python
  def detect_conflict(self, local_version, remote_version):
      if local_version.base_id != remote_version.base_id:
          return ConflictType.DIVERGED
  ```
- [ ] Create resolution UI dialog:
  - [ ] Show both versions side-by-side
  - [ ] Highlight differences
  - [ ] Offer merge options
  - [ ] Keep both as separate entries

### 9. Draft Recovery System
- [ ] Implement startup draft check:
  ```python
  def check_for_drafts(self):
      # Find drafts from crashed sessions
      orphaned = self.find_orphaned_drafts()
      if orphaned:
          self.show_recovery_dialog(orphaned)
  ```
- [ ] Create RecoveryDialog(QDialog):
  - [ ] List recoverable drafts
  - [ ] Show preview of content
  - [ ] Options: Recover, Discard, Later
- [ ] Add session management:
  - [ ] Generate session UUID on start
  - [ ] Track session lifecycle
  - [ ] Clean up on normal exit

### 10. Performance Optimization
- [ ] Implement save throttling:
  - [ ] Limit saves per minute
  - [ ] Batch rapid changes
  - [ ] Skip redundant saves
- [ ] Add performance metrics:
  ```python
  class PerformanceMonitor:
      def track_save(self, duration, size):
          self.save_times.append(duration)
          self.save_sizes.append(size)
  ```
- [ ] Profile memory usage:
  - [ ] Monitor draft accumulation
  - [ ] Implement memory limits
  - [ ] Add garbage collection hints

### 11. Settings Integration
- [ ] Add auto-save preferences:
  - [ ] Enable/disable toggle
  - [ ] Debounce delay slider (1-10 seconds)
  - [ ] Draft retention period
  - [ ] Maximum draft size
- [ ] Create settings UI panel:
  ```python
  class AutoSaveSettings(QWidget):
      def __init__(self):
          self.enabled_check = QCheckBox("Enable auto-save")
          self.delay_slider = QSlider(Qt.Horizontal)
  ```
- [ ] Persist settings to config file
- [ ] Apply settings without restart

### 12. Error Handling
- [ ] Implement comprehensive error catching:
  - [ ] Database errors
  - [ ] Disk space issues
  - [ ] Permission problems
- [ ] Create error notification system:
  - [ ] Toast notifications
  - [ ] Status bar messages
  - [ ] Error log file
- [ ] Add graceful degradation:
  - [ ] Fall back to local storage
  - [ ] Queue saves for retry
  - [ ] Maintain typing flow

### 13. Testing Implementation
- [ ] Create tests/unit/test_auto_save_manager.py:
  - [ ] Test debouncing logic
  - [ ] Test max wait timeout
  - [ ] Test queue operations
  - [ ] Test conflict detection
  - [ ] Mock timer behaviors

### 14. User Documentation
- [ ] Create auto-save help section
- [ ] Document recovery process
- [ ] Add troubleshooting guide
- [ ] Create tooltips for UI elements:
  ```python
  self.status_indicator.setToolTip(
      "Auto-save is active. Your work is saved every 3 seconds."
  )

## Output Log
[2025-01-28 00:00:00] Task created - Auto-save prevents data loss during journal writing