---
task_id: T03_S06
sprint_sequence_id: S06
status: open
complexity: Medium
last_updated: 2025-01-28T00:00:00Z
dependencies: ["T01_S06", "T02_S06"]
---

# Task: Save and Edit Journal Entry Functionality

## Description
Implement the core functionality to save and edit journal entries, connecting the UI editor component to the database layer. This includes handling create, update, and delete operations with proper error handling and user feedback.

## Goal / Objectives
- Connect journal editor to database operations
- Implement save with conflict resolution
- Handle edit mode for existing entries
- Provide clear user feedback for all operations
- Ensure data integrity and error recovery

## Acceptance Criteria
- [ ] New entries save successfully to database
- [ ] Existing entries load correctly in editor
- [ ] Updates overwrite previous entries (upsert)
- [ ] Delete functionality with confirmation dialog
- [ ] Success/error messages display appropriately
- [ ] Concurrent edit conflicts handled gracefully
- [ ] Rollback works on save failures
- [ ] All operations logged for debugging

## Implementation Analysis

### Notification System Choice
- **Toast Notifications** - Floating messages
   - Pros: Modern UX, attention-grabbing
   - Cons: Need custom implementation

### Conflict Resolution Strategy
- **Optimistic Locking** - Version checking
   - Pros: Prevents conflicts, safe
   - Cons: More complex, needs versioning

### Error Handling Approach
- **Silent Retry** - Automatic retry on failure for 5 attempts
- **Immediate Error Dialog** - Show all errors after 5 attempts failed

## Detailed Subtasks

### 1. JournalManager Class Structure
- [ ] Create src/ui/journal_manager.py module
- [ ] Define JournalManager class with singleton pattern:
  ```python
  class JournalManager(QObject):
      # Signals
      entrySaved = pyqtSignal(str, str)  # date, type
      entryDeleted = pyqtSignal(str, str)
      errorOccurred = pyqtSignal(str)
  ```
- [ ] Initialize with database connection
- [ ] Add thread-safe operation queue
- [ ] Implement operation history tracking

### 2. Save Entry Implementation
- [ ] Create save_entry method:
  ```python
  def save_entry(self, date: QDate, entry_type: str, 
                 content: str, callback=None):
      # Validate inputs
      # Check character limit
      # Format date based on entry_type
      # Call database save in worker thread
      # Emit signals on completion
  ```
- [ ] Input validation:
  - [ ] Validate date is not in future
  - [ ] Check entry_type in ['daily', 'weekly', 'monthly']
  - [ ] Enforce 10,000 character limit
  - [ ] Strip whitespace, normalize line endings
- [ ] Calculate derived fields:
  - [ ] week_start_date for weekly entries
  - [ ] month_year for monthly entries
- [ ] Handle database errors gracefully
- [ ] Queue failed saves for retry

### 3. Load Entry Implementation
- [ ] Create load_entry method:
  ```python
  def load_entry(self, date: QDate, entry_type: str) -> Optional[Dict]:
      # Format date for query
      # Fetch from database
      # Handle missing entries
      # Return entry data or None
  ```
- [ ] Add caching layer for recent entries
- [ ] Implement prefetching for adjacent dates
- [ ] Handle database connection errors
- [ ] Add loading progress callback

### 4. Update Entry with Conflict Detection
- [ ] Add version field to journal_entries table
- [ ] Implement optimistic locking:
  ```python
  def update_entry(self, date, entry_type, content, version):
      # Check current version in database
      # If mismatch, show conflict dialog
      # Otherwise proceed with update
  ```
- [ ] Create conflict resolution dialog:
  - [ ] Show current vs. new content
  - [ ] Options: Keep Mine, Keep Theirs, Cancel
  - [ ] Preview of both versions
- [ ] Log all conflict occurrences

### 5. Delete Entry Implementation
- [ ] Create delete confirmation dialog:
  ```python
  class DeleteConfirmDialog(QDialog):
      # Show entry preview
      # Confirm deletion intent
      # Option to export before delete
  ```
- [ ] Implement soft delete option:
  - [ ] Add 'deleted' flag to database
  - [ ] Allow recovery within session
- [ ] Hard delete with transaction safety
- [ ] Update related UI components

### 6. Toast Notification System
- [ ] Create ToastNotification widget:
  ```python
  class ToastNotification(QWidget):
      # Semi-transparent background
      # Icon + message display
      # Auto-hide after 3 seconds
      # Click to dismiss
  ```
- [ ] Notification types:
  - [ ] Success: Green (#95C17B) background
  - [ ] Warning: Yellow (#FFD166) background
  - [ ] Error: Red (#E76F51) background
  - [ ] Info: Blue (#6C9BD1) background
- [ ] Stack multiple notifications
- [ ] Smooth slide-in/fade-out animations
- [ ] Position: top-right corner

### 7. Error Dialog Implementation
- [ ] Create detailed error dialog:
  - [ ] User-friendly message
  - [ ] Technical details (collapsible)
  - [ ] Suggested actions
  - [ ] Report bug option
- [ ] Error categories:
  - [ ] Database errors (connection, lock)
  - [ ] Validation errors (date, content)
  - [ ] System errors (disk full, permissions)
- [ ] Log errors to file for debugging

### 8. Transaction Wrapper
- [ ] Create database transaction decorator:
  ```python
  @with_transaction
  def database_operation(self, *args):
      # Automatic BEGIN/COMMIT/ROLLBACK
      # Retry logic for locks
      # Error propagation
  ```
- [ ] Implement savepoint support
- [ ] Add operation timeout handling
- [ ] Monitor transaction performance

### 9. Operation Logging
- [ ] Create operation logger:
  - [ ] Log all CRUD operations
  - [ ] Include timestamps, user actions
  - [ ] Track performance metrics
- [ ] Log format:
  ```
  [2025-01-28 10:15:23] SAVE entry_type=daily date=2025-01-28 
  size=1234 duration=45ms status=success
  ```
- [ ] Implement log rotation
- [ ] Add debug mode for verbose logging

### 10. Edge Case Handling
- [ ] Disk space:
  - [ ] Check available space before save
  - [ ] Warn user if low (<10MB)
  - [ ] Suggest cleanup options
- [ ] Concurrent access:
  - [ ] File locking for database
  - [ ] Session management
  - [ ] Graceful handling of locks

### 11. Worker Thread Implementation
- [ ] Create JournalWorker(QThread) for async operations:
  ```python
  class JournalWorker(QThread):
      # Separate thread for database operations
      # Prevents UI freezing
      # Progress signals
  ```
- [ ] Operation queue management
- [ ] Priority handling (saves before loads)
- [ ] Cancellation support

### 12. Testing Implementation
- [ ] Create tests/unit/test_journal_manager.py:
  - [ ] Test save/load/update/delete operations
  - [ ] Test validation logic
  - [ ] Test error handling
  - [ ] Test conflict resolution

### 13. Integration with Editor
- [ ] Connect JournalManager to JournalEditorWidget
- [ ] Wire up save button to save_entry
- [ ] Handle save callbacks in UI
- [ ] Update UI state based on operations
- [ ] Show appropriate notifications

### 14. Documentation
- [ ] Document JournalManager API
- [ ] Create sequence mermaid diagrams in the appropriate directory for operations
- [ ] Add error handling guide

## Output Log
[2025-01-28 00:00:00] Task created - Core CRUD operations for journal entries