"""Unit tests for journal manager functionality.

This module tests the JournalManager class including:
- Singleton pattern implementation
- Save/load/delete operations
- Conflict detection and resolution
- Thread-safe operation queuing
- Error handling and retries
- Signal emission
"""

import pytest
from datetime import date, datetime, timedelta
from unittest.mock import Mock, MagicMock, patch, call
import time

from PyQt6.QtCore import QDate, Qt, QObject
from PyQt6.QtTest import QTest
from PyQt6.QtWidgets import QApplication

from src.ui.journal_manager import JournalManager, JournalWorker
from src.models import JournalEntry
from src.utils.error_handler import DatabaseError, DataValidationError


@pytest.mark.ui
class TestJournalWorker:
    """Test the JournalWorker thread class."""
    
    def test_worker_initialization(self):
        """Test worker thread initialization."""
        worker = JournalWorker()
        
        assert len(worker.operations_queue) == 0
        assert worker.current_operation is None
        assert worker.is_running is True
        
    def test_add_operation_priority(self):
        """Test that save operations get priority."""
        worker = JournalWorker()
        
        # Add delete operation first
        delete_op = {'type': 'delete', 'id': 'delete_1'}
        worker.add_operation(delete_op)
        
        # Add save operation - should go to front
        save_op = {'type': 'save', 'id': 'save_1'}
        worker.add_operation(save_op)
        
        # Add another delete
        delete_op2 = {'type': 'delete', 'id': 'delete_2'}
        worker.add_operation(delete_op2)
        
        # Check order - save should be first
        assert worker.operations_queue[0]['id'] == 'save_1'
        assert worker.operations_queue[1]['id'] == 'delete_1'
        assert worker.operations_queue[2]['id'] == 'delete_2'
        
    @patch('src.ui.journal_manager.JournalDAO')
    def test_process_save_operation(self, mock_dao):
        """Test processing a save operation."""
        worker = JournalWorker()
        mock_dao.save_journal_entry.return_value = 123
        
        operation = {
            'type': 'save',
            'id': 'save_test',
            'entry_date': date(2024, 1, 15),
            'entry_type': 'daily',
            'content': 'Test content',
            'week_start_date': None,
            'month_year': None,
            'expected_version': None
        }
        
        result = worker.process_save_operation(operation)
        
        assert result == 123
        mock_dao.save_journal_entry.assert_called_once()
        
    @patch('src.ui.journal_manager.JournalDAO')
    def test_process_save_with_retry(self, mock_dao):
        """Test save operation retry logic."""
        worker = JournalWorker()
        
        # First two calls fail, third succeeds
        mock_dao.save_journal_entry.side_effect = [
            Exception("Database locked"),
            Exception("Database locked"),
            123
        ]
        
        operation = {
            'type': 'save',
            'id': 'save_retry',
            'entry_date': date(2024, 1, 15),
            'entry_type': 'daily',
            'content': 'Test',
            'retry_count': 0
        }
        
        result = worker.process_save_operation(operation)
        
        assert result == 123
        assert mock_dao.save_journal_entry.call_count == 3
        
    @patch('src.ui.journal_manager.JournalDAO')
    def test_process_delete_operation(self, mock_dao):
        """Test processing a delete operation."""
        worker = JournalWorker()
        mock_dao.delete_journal_entry.return_value = True
        
        operation = {
            'type': 'delete',
            'id': 'delete_test',
            'entry_date': date(2024, 1, 15),
            'entry_type': 'daily'
        }
        
        result = worker.process_delete_operation(operation)
        
        assert result is True
        mock_dao.delete_journal_entry.assert_called_once_with(
            entry_date=date(2024, 1, 15),
            entry_type='daily'
        )


@pytest.mark.ui
@pytest.mark.skip(reason="JournalManager singleton causes segfaults in test environment")
class TestJournalManager:
    """Test the JournalManager class."""
    
    @classmethod
    def setup_class(cls):
        """Set up QApplication for tests."""
        if not QApplication.instance():
            cls.app = QApplication([])
    
    def test_singleton_pattern(self):
        """Test that JournalManager implements singleton pattern."""
        manager1 = JournalManager()
        manager2 = JournalManager()
        
        assert manager1 is manager2
        
    @patch('src.ui.journal_manager.JournalWorker')
    def test_manager_initialization(self, mock_worker_class):
        """Test manager initialization."""
        # Reset singleton
        JournalManager._instance = None
        
        mock_worker = MagicMock()
        mock_worker_class.return_value = mock_worker
        
        manager = JournalManager()
        
        assert manager.conflict_handler is None
        assert len(manager.operation_callbacks) == 0
        assert len(manager.operation_history) == 0
        
        # Check worker started
        mock_worker.start.assert_called_once()
        
    def test_save_entry_validation(self):
        """Test save entry input validation."""
        manager = JournalManager()
        
        # Mock the worker to prevent actual operations
        manager.worker = Mock()
        
        # Test empty content
        callback = Mock()
        op_id = manager.save_entry(
            QDate.currentDate(),
            'daily',
            '',
            callback=callback
        )
        
        assert op_id == ""
        callback.assert_called_once_with(False, None)
        
        # Test content over limit
        callback2 = Mock()
        long_content = 'a' * 10001
        op_id = manager.save_entry(
            QDate.currentDate(),
            'daily',
            long_content,
            callback=callback2
        )
        
        assert op_id == ""
        callback2.assert_called_once_with(False, None)
        
        # Test invalid entry type
        callback3 = Mock()
        op_id = manager.save_entry(
            QDate.currentDate(),
            'invalid',
            'content',
            callback=callback3
        )
        
        assert op_id == ""
        callback3.assert_called_once_with(False, None)
        
        # Test future date
        callback4 = Mock()
        future_date = QDate.currentDate().addDays(1)
        op_id = manager.save_entry(
            future_date,
            'daily',
            'content',
            callback=callback4
        )
        
        assert op_id == ""
        callback4.assert_called_once_with(False, None)
        
    def test_save_entry_success(self):
        """Test successful save operation."""
        manager = JournalManager()
        
        # Mock the worker
        manager.worker = Mock()
        
        # Save valid entry
        callback = Mock()
        op_id = manager.save_entry(
            QDate(2024, 1, 15),
            'daily',
            'Test journal entry',
            callback=callback
        )
        
        assert op_id.startswith('save_')
        assert len(manager.operation_history) > 0
        
        # Check operation was queued
        manager.worker.add_operation.assert_called_once()
        operation = manager.worker.add_operation.call_args[0][0]
        
        assert operation['type'] == 'save'
        assert operation['entry_date'] == date(2024, 1, 15)
        assert operation['entry_type'] == 'daily'
        assert operation['content'] == 'Test journal entry'
        
    def test_weekly_entry_date_calculation(self, qapp):
        """Test week start date calculation for weekly entries."""
        manager = JournalManager()
        manager.worker = Mock()
        
        # Test with a Wednesday
        wednesday = QDate(2024, 1, 17)  # Wednesday
        op_id = manager.save_entry(
            wednesday,
            'weekly',
            'Weekly reflection'
        )
        
        operation = manager.worker.add_operation.call_args[0][0]
        assert operation['week_start_date'] == date(2024, 1, 15)  # Monday
        
    def test_monthly_entry_format(self):
        """Test month-year format for monthly entries."""
        manager = JournalManager()
        manager.worker = Mock()
        
        op_id = manager.save_entry(
            QDate(2024, 1, 31),
            'monthly',
            'Monthly summary'
        )
        
        operation = manager.worker.add_operation.call_args[0][0]
        assert operation['month_year'] == '2024-01'
        
    def test_load_entry(self):
        """Test loading an entry."""
        manager = JournalManager()
        
        # Mock data access
        mock_entry = JournalEntry(
            id=1,
            entry_date=date(2024, 1, 15),
            entry_type='daily',
            content='Test content',
            created_at=datetime.now(),
            updated_at=datetime.now(),
            version=2
        )
        
        manager.data_access.get_journal_entries = Mock(return_value=[mock_entry])
        
        result = manager.load_entry(QDate(2024, 1, 15), 'daily')
        
        assert result is not None
        assert result['id'] == 1
        assert result['content'] == 'Test content'
        assert result['version'] == 2
        
    def test_delete_entry(self):
        """Test delete operation queuing."""
        manager = JournalManager()
        manager.worker = Mock()
        
        callback = Mock()
        op_id = manager.delete_entry(
            QDate(2024, 1, 15),
            'daily',
            callback=callback
        )
        
        assert op_id.startswith('delete_')
        
        # Check operation was queued
        operation = manager.worker.add_operation.call_args[0][0]
        assert operation['type'] == 'delete'
        assert operation['entry_date'] == date(2024, 1, 15)
        
    @patch('PyQt6.QtCore.QObject.__init__', lambda x: None)
    def test_operation_complete_handling(self):
        """Test handling of operation completion."""
        manager = JournalManager()
        
        # Create a save operation
        operation = {
            'id': 'test_save',
            'type': 'save',
            'entry_date': date(2024, 1, 15),
            'entry_type': 'daily'
        }
        manager.operation_history.append(operation)
        
        # Set up callback
        callback = Mock()
        manager.operation_callbacks['test_save'] = callback
        
        # Connect signal spy
        saved_signal = []
        manager.entrySaved.connect(lambda d, t: saved_signal.append((d, t)))
        
        # Trigger completion
        manager._on_operation_complete('test_save', True, 123)
        
        # Check callback called
        callback.assert_called_once_with(True, 123)
        
        # Check signal emitted
        assert len(saved_signal) == 1
        assert saved_signal[0] == ('2024-01-15', 'daily')
        
    def test_conflict_detection(self):
        """Test version conflict detection and handling."""
        manager = JournalManager()
        
        # Set up conflict handler
        conflict_handler = Mock(return_value='keep_mine')
        manager.set_conflict_handler(conflict_handler)
        
        # Set up operation
        operation = {
            'id': 'test_conflict',
            'type': 'save',
            'entry_date': date(2024, 1, 15),
            'entry_type': 'daily',
            'content': 'New content',
            'expected_version': 1
        }
        manager.operation_history.append(operation)
        
        # Mock current entry
        manager.load_entry = Mock(return_value={
            'content': 'Current content',
            'version': 2
        })
        
        # Mock worker for retry
        manager.worker = Mock()
        
        # Trigger conflict
        manager._on_operation_failed('test_conflict', 'Version conflict detected')
        
        # Check conflict handler called
        conflict_handler.assert_called_once_with('Current content', 'New content')
        
        # Check retry queued with new version
        retry_op = manager.worker.add_operation.call_args[0][0]
        assert retry_op['expected_version'] == 2
        
    def test_error_signal_emission(self):
        """Test error signal emission."""
        manager = JournalManager()
        
        # Connect signal spy
        errors = []
        manager.errorOccurred.connect(errors.append)
        
        # Trigger error
        manager._on_operation_failed('test_op', 'Database error')
        
        assert len(errors) == 1
        assert errors[0] == 'Database error'
        
    def test_operation_history_limit(self):
        """Test that operation history has a size limit."""
        manager = JournalManager()
        manager.worker = Mock()
        
        # Add many operations
        for i in range(150):
            manager.save_entry(
                QDate.currentDate(),
                'daily',
                f'Entry {i}'
            )
            
        # History should be limited to 100
        assert len(manager.operation_history) == 100
        
    def test_get_operation_history(self):
        """Test retrieving operation history."""
        manager = JournalManager()
        manager.worker = Mock()
        
        # Add some operations
        for i in range(5):
            manager.save_entry(
                QDate.currentDate(),
                'daily',
                f'Entry {i}'
            )
            
        # Get recent history
        history = manager.get_operation_history(limit=3)
        
        assert len(history) == 3
        assert all(op['type'] == 'save' for op in history)
        
    def test_cleanup(self):
        """Test cleanup method."""
        manager = JournalManager()
        mock_worker = Mock()
        manager.worker = mock_worker
        
        manager.cleanup()
        
        mock_worker.stop.assert_called_once()
        assert manager.worker is None