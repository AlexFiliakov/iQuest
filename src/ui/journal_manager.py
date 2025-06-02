"""Journal management system for save, edit, and delete operations.

This module provides the core functionality for managing journal entries in the
Apple Health Monitor application. It implements a thread-safe journal manager
that handles all CRUD operations with proper error handling, transaction safety,
and user notifications.

The JournalManager class acts as a bridge between the UI layer and the data
access layer, providing:
    - Thread-safe database operations using QThread workers
    - Optimistic locking for conflict detection
    - Automatic retry logic for transient failures
    - Toast notifications for user feedback
    - Operation history tracking for debugging
    - Transaction safety with rollback support

Key features:
    - Singleton pattern for global access
    - Signal-based communication for async operations
    - Comprehensive error handling with user-friendly messages
    - Character limit enforcement (10,000 chars)
    - Smart date handling for different entry types
    - Conflict resolution with version tracking

Example:
    Basic usage with the journal editor:
    
    >>> manager = JournalManager()
    >>> manager.entrySaved.connect(self.on_entry_saved)
    >>> manager.errorOccurred.connect(self.show_error)
    >>> 
    >>> # Save an entry
    >>> manager.save_entry(
    ...     QDate.currentDate(),
    ...     'daily',
    ...     'Today was productive!',
    ...     callback=lambda success: print(f"Save: {success}")
    ... )
    
    Handling conflicts:
    
    >>> def handle_conflict(current_content, new_content):
    ...     # Show dialog and return user's choice
    ...     return 'keep_mine'  # or 'keep_theirs'
    >>> 
    >>> manager.set_conflict_handler(handle_conflict)
"""

import logging
from typing import Optional, Dict, Any, Callable, List
from datetime import date, datetime, timedelta
from collections import deque
import threading
import time

from PyQt6.QtCore import (
    QObject, pyqtSignal, QThread, QDate, QMutex, QMutexLocker
)
from PyQt6.QtWidgets import QMessageBox

from ..data_access import DataAccess, JournalDAO
from ..models import JournalEntry
from ..utils.logging_config import get_logger
from ..utils.error_handler import DatabaseError, DataValidationError as ValidationError

logger = get_logger(__name__)


class JournalWorker(QThread):
    """Worker thread for asynchronous journal database operations.
    
    This worker thread handles all database operations in the background to
    prevent UI freezing. It processes operations from a queue and emits
    signals for results and progress updates.
    
    Attributes:
        operationComplete (pyqtSignal): Emitted when an operation completes
        operationFailed (pyqtSignal): Emitted when an operation fails
        progressUpdate (pyqtSignal): Emitted for progress updates
    """
    
    operationComplete = pyqtSignal(str, bool, object)  # operation_id, success, result
    operationFailed = pyqtSignal(str, str)  # operation_id, error_message
    progressUpdate = pyqtSignal(str, int)  # operation_id, progress_percent
    
    def __init__(self):
        """Initialize the worker thread."""
        super().__init__()
        self.operations_queue = deque()
        self.current_operation = None
        self.is_running = True
        self.mutex = QMutex()
        
    def add_operation(self, operation: Dict[str, Any]):
        """Add an operation to the queue with priority handling.
        
        Args:
            operation: Dictionary containing operation details
        """
        with QMutexLocker(self.mutex):
            # Priority handling: saves go to front, others to back
            if operation.get('type') == 'save':
                self.operations_queue.appendleft(operation)
            else:
                self.operations_queue.append(operation)
            
    def stop(self):
        """Stop the worker thread."""
        self.is_running = False
        self.quit()
        self.wait()
        
    def run(self):
        """Main worker thread loop."""
        while self.is_running:
            operation = None
            
            # Get next operation from queue
            with QMutexLocker(self.mutex):
                if self.operations_queue:
                    operation = self.operations_queue.popleft()
                    
            if operation:
                self.current_operation = operation
                self.process_operation(operation)
            else:
                # No operations, sleep briefly
                self.msleep(100)
                
    def process_operation(self, operation: Dict[str, Any]):
        """Process a single operation.
        
        Args:
            operation: The operation to process
        """
        op_type = operation.get('type')
        op_id = operation.get('id')
        
        try:
            if op_type == 'save':
                result = self.process_save_operation(operation)
            elif op_type == 'load':
                result = self.process_load_operation(operation)
            elif op_type == 'delete':
                result = self.process_delete_operation(operation)
            elif op_type == 'search':
                result = self.process_search_operation(operation)
            else:
                raise ValueError(f"Unknown operation type: {op_type}")
                
            self.operationComplete.emit(op_id, True, result)
            
        except Exception as e:
            logger.error(f"Operation {op_id} failed: {e}")
            self.operationFailed.emit(op_id, str(e))
            
    def process_save_operation(self, operation: Dict[str, Any]) -> int:
        """Process a save operation.
        
        Args:
            operation: Save operation details
            
        Returns:
            int: The saved entry ID
        """
        entry_date = operation['entry_date']
        entry_type = operation['entry_type']
        content = operation['content']
        week_start_date = operation.get('week_start_date')
        month_year = operation.get('month_year')
        expected_version = operation.get('expected_version')
        retry_count = operation.get('retry_count', 0)
        max_retries = 5
        
        # Retry logic for transient failures
        while retry_count < max_retries:
            try:
                start_time = time.time()
                entry_id = JournalDAO.save_journal_entry(
                    entry_date=entry_date,
                    entry_type=entry_type,
                    content=content,
                    week_start_date=week_start_date,
                    month_year=month_year,
                    expected_version=expected_version
                )
                duration_ms = int((time.time() - start_time) * 1000)
                
                # Log operation in specified format
                logger.info(
                    f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] SAVE "
                    f"entry_type={entry_type} date={entry_date} "
                    f"size={len(content)} duration={duration_ms}ms status=success"
                )
                
                return entry_id
                
            except ValueError as e:
                # Version conflict - don't retry
                logger.warning(f"Version conflict during save: {e}")
                raise
                
            except Exception as e:
                retry_count += 1
                if retry_count >= max_retries:
                    raise
                    
                # Exponential backoff
                wait_time = (2 ** retry_count) * 0.1
                logger.warning(f"Save retry {retry_count}/{max_retries} after {wait_time}s")
                time.sleep(wait_time)
                
    def process_load_operation(self, operation: Dict[str, Any]) -> Optional[JournalEntry]:
        """Process a load operation.
        
        Args:
            operation: Load operation details
            
        Returns:
            Optional[JournalEntry]: The loaded entry or None
        """
        entry_date = operation['entry_date']
        entry_type = operation['entry_type']
        
        # Get entries for the specific date
        entries = JournalDAO.get_journal_entries(
            start_date=entry_date,
            end_date=entry_date,
            entry_type=entry_type
        )
        
        return entries[0] if entries else None
        
    def process_delete_operation(self, operation: Dict[str, Any]) -> bool:
        """Process a delete operation.
        
        Args:
            operation: Delete operation details
            
        Returns:
            bool: True if deletion successful
        """
        entry_date = operation['entry_date']
        entry_type = operation['entry_type']
        
        # Delete using JournalDAO
        start_time = time.time()
        result = JournalDAO.delete_journal_entry(
            entry_date=entry_date,
            entry_type=entry_type
        )
        duration_ms = int((time.time() - start_time) * 1000)
        
        # Log operation in specified format
        logger.info(
            f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] DELETE "
            f"entry_type={entry_type} date={entry_date} "
            f"duration={duration_ms}ms status={'success' if result else 'not_found'}"
        )
        
        return result
        
    def process_search_operation(self, operation: Dict[str, Any]) -> List[JournalEntry]:
        """Process a search operation.
        
        Args:
            operation: Search operation details
            
        Returns:
            List[JournalEntry]: Search results
        """
        search_term = operation['search_term']
        return JournalDAO.search_journal_entries(search_term)


class JournalManager(QObject):
    """Central manager for all journal entry operations.
    
    This class provides a high-level interface for managing journal entries
    with thread safety, error handling, and user notifications. It implements
    the singleton pattern to ensure a single instance manages all operations.
    
    Attributes:
        entrySaved (pyqtSignal): Emitted when an entry is successfully saved
        entryDeleted (pyqtSignal): Emitted when an entry is deleted
        errorOccurred (pyqtSignal): Emitted when an error occurs
        conflictDetected (pyqtSignal): Emitted when a save conflict is detected
    """
    
    _instance = None
    _mutex = QMutex()
    
    # Signals
    entrySaved = pyqtSignal(str, str)  # date, type
    entryDeleted = pyqtSignal(str, str)  # date, type
    errorOccurred = pyqtSignal(str)  # error message
    conflictDetected = pyqtSignal(str, str, str)  # date, current_content, new_content
    
    def __new__(cls, *args, **kwargs):
        """Implement singleton pattern."""
        with QMutexLocker(cls._mutex):
            if cls._instance is None:
                cls._instance = super().__new__(cls)
            return cls._instance
            
    def __init__(self, data_access: Optional[DataAccess] = None):
        """Initialize the journal manager.
        
        Args:
            data_access: Optional data access object (for testing)
        """
        # Only initialize once
        if hasattr(self, '_initialized'):
            return
            
        super().__init__()
        self._initialized = True
        self.data_access = data_access or DataAccess()
        self.worker = JournalWorker()
        self.operation_callbacks: Dict[str, Callable] = {}
        self.operation_history: deque = deque(maxlen=100)
        self.conflict_handler: Optional[Callable] = None
        
        # Connect worker signals
        self.worker.operationComplete.connect(self._on_operation_complete)
        self.worker.operationFailed.connect(self._on_operation_failed)
        
        # Start worker thread
        self.worker.start()
        
        logger.info("JournalManager initialized")
        
    def save_entry(self, entry_date: QDate, entry_type: str, 
                   content: str, callback: Optional[Callable] = None,
                   expected_version: Optional[int] = None) -> str:
        """Save a journal entry with validation and error handling.
        
        Args:
            entry_date: The date for the entry
            entry_type: Type of entry ('daily', 'weekly', 'monthly')
            content: The journal content
            callback: Optional callback function(success: bool, entry_id: int)
            expected_version: Optional version for optimistic locking
            
        Returns:
            str: Operation ID for tracking
            
        Raises:
            ValidationError: If input validation fails
        """
        # Validate inputs
        if not content or not content.strip():
            self.errorOccurred.emit("Please enter some content before saving.")
            if callback:
                callback(False, None)
            return ""
            
        # Check character limit
        if len(content) > 10000:
            self.errorOccurred.emit("Content exceeds 10,000 character limit.")
            if callback:
                callback(False, None)
            return ""
            
        # Validate entry type
        if entry_type not in ['daily', 'weekly', 'monthly']:
            self.errorOccurred.emit(f"Invalid entry type: {entry_type}")
            if callback:
                callback(False, None)
            return ""
            
        # Validate date not in future
        if entry_date > QDate.currentDate():
            self.errorOccurred.emit("Cannot create entries for future dates.")
            if callback:
                callback(False, None)
            return ""
            
        # Convert QDate to Python date
        py_date = entry_date.toPython()
        
        # Calculate additional fields based on entry type
        week_start_date = None
        month_year = None
        
        if entry_type == 'weekly':
            # Calculate week start (Monday)
            week_start_date = py_date - timedelta(days=py_date.weekday())
        elif entry_type == 'monthly':
            # Format as YYYY-MM
            month_year = f"{py_date.year:04d}-{py_date.month:02d}"
            
        # Create operation
        operation = {
            'type': 'save',
            'id': f"save_{datetime.now().timestamp()}",
            'entry_date': py_date,
            'entry_type': entry_type,
            'content': content.strip(),
            'week_start_date': week_start_date,
            'month_year': month_year,
            'expected_version': expected_version,
            'timestamp': datetime.now()
        }
        
        # Store callback
        if callback:
            self.operation_callbacks[operation['id']] = callback
            
        # Add to history
        self.operation_history.append(operation)
        
        # Queue operation
        self.worker.add_operation(operation)
        
        return operation['id']
        
    def load_entry(self, entry_date: QDate, entry_type: str) -> Optional[Dict[str, Any]]:
        """Load a journal entry from the database.
        
        Args:
            entry_date: The date to load
            entry_type: The entry type to load
            
        Returns:
            Optional[Dict]: Entry data or None if not found
        """
        try:
            py_date = entry_date.toPython()
            
            # Get entries for the specific date
            entries = self.data_access.get_journal_entries(
                start_date=py_date,
                end_date=py_date,
                entry_type=entry_type
            )
            
            if entries:
                entry = entries[0]
                return {
                    'id': entry.id,
                    'content': entry.content,
                    'created_at': entry.created_at,
                    'updated_at': entry.updated_at,
                    'version': getattr(entry, 'version', 1)
                }
                
            return None
            
        except Exception as e:
            logger.error(f"Error loading entry: {e}")
            self.errorOccurred.emit(f"Failed to load entry: {str(e)}")
            return None
            
    def delete_entry(self, entry_date: QDate, entry_type: str, 
                     callback: Optional[Callable] = None) -> str:
        """Delete a journal entry with confirmation.
        
        Args:
            entry_date: The date of the entry to delete
            entry_type: The type of entry to delete
            callback: Optional callback function(success: bool)
            
        Returns:
            str: Operation ID for tracking
        """
        # Create operation
        operation = {
            'type': 'delete',
            'id': f"delete_{datetime.now().timestamp()}",
            'entry_date': entry_date.toPython(),
            'entry_type': entry_type,
            'timestamp': datetime.now()
        }
        
        # Store callback
        if callback:
            self.operation_callbacks[operation['id']] = callback
            
        # Add to history
        self.operation_history.append(operation)
        
        # Queue operation
        self.worker.add_operation(operation)
        
        return operation['id']
        
    def set_conflict_handler(self, handler: Callable[[str, str], str]):
        """Set the conflict resolution handler.
        
        Args:
            handler: Function that takes (current_content, new_content) and
                    returns 'keep_mine', 'keep_theirs', or 'cancel'
        """
        self.conflict_handler = handler
        
    def _on_operation_complete(self, op_id: str, success: bool, result: Any):
        """Handle operation completion.
        
        Args:
            op_id: Operation ID
            success: Whether operation succeeded
            result: Operation result
        """
        # Get callback if registered
        callback = self.operation_callbacks.pop(op_id, None)
        
        # Find operation in history
        operation = None
        for op in self.operation_history:
            if op['id'] == op_id:
                operation = op
                break
                
        if not operation:
            logger.warning(f"Operation {op_id} not found in history")
            return
            
        # Handle based on operation type
        if operation['type'] == 'save' and success:
            self.entrySaved.emit(
                operation['entry_date'].isoformat(),
                operation['entry_type']
            )
            logger.info(f"Saved {operation['entry_type']} entry for {operation['entry_date']}")
            
        elif operation['type'] == 'delete' and success:
            self.entryDeleted.emit(
                operation['entry_date'].isoformat(),
                operation['entry_type']
            )
            logger.info(f"Deleted {operation['entry_type']} entry for {operation['entry_date']}")
            
        # Call callback if provided
        if callback:
            callback(success, result)
            
    def _on_operation_failed(self, op_id: str, error_message: str):
        """Handle operation failure.
        
        Args:
            op_id: Operation ID
            error_message: Error message
        """
        # Get callback if registered
        callback = self.operation_callbacks.pop(op_id, None)
        
        # Find operation in history
        operation = None
        for op in self.operation_history:
            if op['id'] == op_id:
                operation = op
                break
                
        # Check if it's a version conflict
        if operation and "Version conflict" in error_message:
            # Get current content from database
            try:
                current_entry = self.load_entry(
                    QDate(operation['entry_date']),
                    operation['entry_type']
                )
                
                if current_entry and self.conflict_handler:
                    # Trigger conflict resolution
                    self.conflictDetected.emit(
                        operation['entry_date'].isoformat(),
                        current_entry['content'],
                        operation['content']
                    )
                    
                    # Let the conflict handler decide what to do
                    choice = self.conflict_handler(
                        current_entry['content'],
                        operation['content']
                    )
                    
                    if choice == 'keep_mine':
                        # Retry with current version
                        operation['expected_version'] = current_entry.get('version', 1)
                        operation['retry_count'] = 0
                        self.worker.add_operation(operation)
                        return
                    elif choice == 'keep_theirs':
                        # User chose to keep existing version
                        if callback:
                            callback(False, None)
                        return
                    # else: cancelled, fall through to normal error handling
                        
            except Exception as e:
                logger.error(f"Error handling conflict: {e}")
        
        # Emit error signal
        self.errorOccurred.emit(error_message)
        
        # Call callback if provided
        if callback:
            callback(False, None)
            
        logger.error(f"Operation {op_id} failed: {error_message}")
        
    def get_operation_history(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get recent operation history for debugging.
        
        Args:
            limit: Maximum number of operations to return
            
        Returns:
            List of recent operations
        """
        return list(self.operation_history)[-limit:]
        
    def cleanup(self):
        """Clean up resources."""
        if hasattr(self, 'worker'):
            self.worker.stop()
            self.worker = None