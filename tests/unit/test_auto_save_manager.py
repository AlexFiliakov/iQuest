"""Unit tests for auto-save manager functionality.

This module tests the AutoSaveManager class including:
    - Debouncing logic with max wait enforcement
    - Content change detection and hashing
    - Save request emission and handling
    - Performance monitoring
    - Configuration management
    - Draft storage operations
"""

import unittest
from unittest.mock import Mock, MagicMock, patch, call
import time
from datetime import datetime, timedelta
from PyQt6.QtCore import QTimer, Qt
from PyQt6.QtWidgets import QApplication, QWidget
from PyQt6.QtTest import QTest
import sys

# Ensure src is in path
sys.path.insert(0, 'src')

from src.ui.auto_save_manager import AutoSaveManager, DebouncedTimer, SaveWorker
from src.data_access import DataAccess


class TestDebouncedTimer(unittest.TestCase):
    """Test cases for DebouncedTimer class."""
    
    @classmethod
    def setUpClass(cls):
        """Create QApplication for Qt tests."""
        if not QApplication.instance():
            cls.app = QApplication([])
    
    def setUp(self):
        """Set up test fixtures."""
        self.timer = DebouncedTimer(100, 500)  # 100ms delay, 500ms max wait
        self.parent = QWidget()
        self.timer.set_parent(self.parent)
        self.triggered_count = 0
        
        def on_triggered():
            self.triggered_count += 1
            
        self.timer.connect(on_triggered)
    
    def tearDown(self):
        """Clean up after tests."""
        self.timer.stop()
        self.timer.disconnect()
        if hasattr(self, 'parent'):
            self.parent.deleteLater()
    
    def test_single_reset_triggers_after_delay(self):
        """Test that a single reset triggers after the delay period."""
        self.timer.reset()
        self.assertEqual(self.triggered_count, 0)
        
        # Wait for slightly more than delay
        QTest.qWait(150)
        self.assertEqual(self.triggered_count, 1)
    
    def test_rapid_resets_debounce_properly(self):
        """Test that rapid resets properly debounce."""
        # Reset multiple times rapidly
        for _ in range(5):
            self.timer.reset()
            QTest.qWait(50)  # Half the delay time
        
        # Should not have triggered yet
        self.assertEqual(self.triggered_count, 0)
        
        # Wait for delay to expire
        QTest.qWait(150)
        self.assertEqual(self.triggered_count, 1)
    
    def test_max_wait_enforcement(self):
        """Test that max wait time is enforced."""
        start_time = time.time()
        
        # Keep resetting for longer than max wait
        while time.time() - start_time < 0.6:  # 600ms > 500ms max wait
            self.timer.reset()
            QTest.qWait(50)
            
            if self.triggered_count > 0:
                break
        
        # Should have triggered due to max wait
        self.assertEqual(self.triggered_count, 1)
        elapsed = time.time() - start_time
        self.assertLess(elapsed, 0.6)  # Should trigger before 600ms
    
    def test_force_trigger(self):
        """Test force trigger bypasses timers."""
        self.timer.reset()
        self.timer.force_trigger()
        
        # Should trigger immediately
        self.assertEqual(self.triggered_count, 1)
    
    def test_stop_cancels_pending_triggers(self):
        """Test that stop cancels pending triggers."""
        self.timer.reset()
        self.timer.stop()
        
        # Wait for what would be the trigger time
        QTest.qWait(150)
        self.assertEqual(self.triggered_count, 0)


class TestAutoSaveManager(unittest.TestCase):
    """Test cases for AutoSaveManager class."""
    
    @classmethod
    def setUpClass(cls):
        """Create QApplication for Qt tests."""
        if not QApplication.instance():
            cls.app = QApplication([])
    
    def setUp(self):
        """Set up test fixtures."""
        self.mock_data_access = Mock(spec=DataAccess)
        self.manager = AutoSaveManager(self.mock_data_access)
        
        # Track emitted signals
        self.save_requests = []
        self.save_completes = []
        self.status_changes = []
        
        self.manager.saveRequested.connect(
            lambda d, t, c: self.save_requests.append((d, t, c))
        )
        self.manager.saveCompleted.connect(
            lambda s, m: self.save_completes.append((s, m))
        )
        self.manager.statusChanged.connect(
            lambda s: self.status_changes.append(s)
        )
    
    def tearDown(self):
        """Clean up after tests."""
        self.manager.cleanup()
    
    def test_initial_state(self):
        """Test initial state of auto-save manager."""
        self.assertTrue(self.manager.enabled)
        self.assertTrue(self.manager.save_drafts)
        self.assertEqual(self.manager.debounce_delay, 3000)
        self.assertEqual(self.manager.max_wait_time, 30000)
        self.assertFalse(self.manager.pending_save)
        self.assertFalse(self.manager.save_in_progress)
    
    def test_content_change_triggers_debounce(self):
        """Test that content changes trigger debounced save."""
        # Simulate content change
        self.manager.on_content_changed(
            "2024-01-15",
            "daily",
            "Test content"
        )
        
        # Should mark as pending and emit modified status
        self.assertTrue(self.manager.pending_save)
        self.assertIn("Modified", self.status_changes)
        self.assertEqual(len(self.save_requests), 0)  # Not saved yet
    
    def test_identical_content_ignored(self):
        """Test that identical content doesn't trigger save."""
        content = "Test content"
        
        # First change
        self.manager.on_content_changed("2024-01-15", "daily", content)
        initial_status_count = len(self.status_changes)
        
        # Same content again
        self.manager.on_content_changed("2024-01-15", "daily", content)
        
        # Should not add another status change
        self.assertEqual(len(self.status_changes), initial_status_count)
    
    def test_empty_content_ignored(self):
        """Test that empty content is ignored."""
        self.manager.on_content_changed("2024-01-15", "daily", "")
        
        self.assertFalse(self.manager.pending_save)
        self.assertEqual(len(self.status_changes), 0)
    
    def test_force_save(self):
        """Test force save bypasses debounce."""
        # Set up pending content
        self.manager.on_content_changed("2024-01-15", "daily", "Test content")
        
        # Force save
        self.manager.force_save()
        
        # Wait for processing
        QTest.qWait(100)
        
        # Should have triggered save
        self.assertEqual(len(self.save_requests), 1)
        self.assertEqual(self.save_requests[0], ("2024-01-15", "daily", "Test content"))
    
    def test_disabled_auto_save(self):
        """Test that disabled auto-save doesn't trigger."""
        self.manager.set_enabled(False)
        
        # Try to trigger auto-save
        self.manager.on_content_changed("2024-01-15", "daily", "Test content")
        
        self.assertFalse(self.manager.pending_save)
        self.assertIn("Auto-save disabled", self.status_changes)
    
    def test_configuration_methods(self):
        """Test configuration setter methods."""
        # Test debounce delay
        self.manager.set_debounce_delay(5000)
        self.assertEqual(self.manager.debounce_delay, 5000)
        
        # Test invalid delay (too low)
        self.manager.set_debounce_delay(500)
        self.assertEqual(self.manager.debounce_delay, 5000)  # Unchanged
        
        # Test max wait time
        self.manager.set_max_wait_time(45000)
        self.assertEqual(self.manager.max_wait_time, 45000)
        
        # Test invalid max wait (too high)
        self.manager.set_max_wait_time(70000)
        self.assertEqual(self.manager.max_wait_time, 45000)  # Unchanged
    
    def test_performance_stats(self):
        """Test performance statistics tracking."""
        initial_stats = self.manager.get_performance_stats()
        self.assertEqual(initial_stats['saves_triggered'], 0)
        self.assertEqual(initial_stats['saves_completed'], 0)
        self.assertEqual(initial_stats['saves_failed'], 0)
        
        # Trigger a save
        self.manager.on_content_changed("2024-01-15", "daily", "Test")
        self.manager.force_save()
        QTest.qWait(100)
        
        # Stats should update
        stats = self.manager.get_performance_stats()
        self.assertEqual(stats['saves_triggered'], 1)
    
    def test_content_hash_calculation(self):
        """Test content hash calculation."""
        content1 = "Test content"
        content2 = "Different content"
        
        hash1 = self.manager._calculate_hash(content1)
        hash2 = self.manager._calculate_hash(content2)
        hash1_again = self.manager._calculate_hash(content1)
        
        # Same content should produce same hash
        self.assertEqual(hash1, hash1_again)
        
        # Different content should produce different hash
        self.assertNotEqual(hash1, hash2)
        
        # Hash should be 64 characters (SHA-256)
        self.assertEqual(len(hash1), 64)
    
    @patch('src.ui.auto_save_manager.SaveWorker')
    def test_draft_saving(self, mock_worker_class):
        """Test draft saving functionality."""
        mock_worker = Mock()
        mock_worker_class.return_value = mock_worker
        
        # Create manager with mocked worker
        manager = AutoSaveManager(self.mock_data_access)
        manager.save_worker = mock_worker
        
        # Trigger save with drafts enabled
        manager.save_drafts = True
        manager.on_content_changed("2024-01-15", "daily", "Draft content")
        manager.force_save()
        
        # Should set save data and start worker
        mock_worker.set_save_data.assert_called_once()
        mock_worker.start.assert_called_once()
    
    def test_save_completion_handling(self):
        """Test save completion handling."""
        # Simulate successful save
        self.manager._on_save_finished(True, "Save successful")
        
        self.assertFalse(self.manager.save_in_progress)
        self.assertEqual(len(self.save_completes), 1)
        self.assertTrue(self.save_completes[0][0])  # Success
        self.assertIn("Saved at", self.status_changes[-1])
        
        # Simulate failed save
        self.manager._on_save_finished(False, "Database error")
        
        self.assertEqual(len(self.save_completes), 2)
        self.assertFalse(self.save_completes[1][0])  # Failure
        self.assertIn("Save failed", self.status_changes[-1])


class TestSaveWorker(unittest.TestCase):
    """Test cases for SaveWorker thread."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.mock_data_access = Mock(spec=DataAccess)
        self.worker = SaveWorker(self.mock_data_access)
        
        # Track signals
        self.progress_updates = []
        self.finish_results = []
        self.errors = []
        
        self.worker.progress.connect(self.progress_updates.append)
        self.worker.finished.connect(
            lambda s, m: self.finish_results.append((s, m))
        )
        self.worker.error.connect(self.errors.append)
    
    def test_save_data_setting(self):
        """Test setting save data."""
        self.worker.set_save_data(
            "2024-01-15",
            "daily",
            "Test content",
            "hash123",
            "session123"
        )
        
        self.assertEqual(self.worker.save_data['entry_date'], "2024-01-15")
        self.assertEqual(self.worker.save_data['entry_type'], "daily")
        self.assertEqual(self.worker.save_data['content'], "Test content")
        self.assertEqual(self.worker.save_data['content_hash'], "hash123")
        self.assertEqual(self.worker.save_data['session_id'], "session123")
        self.assertEqual(self.worker.retry_count, 0)
    
    def test_no_data_error(self):
        """Test error when no save data is set."""
        # Don't set save data
        self.worker.run()
        
        self.assertEqual(len(self.errors), 1)
        self.assertIn("No data to save", self.errors[0])
    
    @patch('src.ui.auto_save_manager.SaveWorker._save_draft')
    def test_successful_save(self, mock_save_draft):
        """Test successful save operation."""
        mock_save_draft.return_value = True
        
        self.worker.set_save_data(
            "2024-01-15", "daily", "Test", "hash", "session"
        )
        self.worker.run()
        
        # Should emit progress and success
        self.assertIn(20, self.progress_updates)
        self.assertIn(100, self.progress_updates)
        self.assertEqual(len(self.finish_results), 1)
        self.assertTrue(self.finish_results[0][0])  # Success
    
    @patch('src.ui.auto_save_manager.SaveWorker._save_draft')
    def test_retry_logic(self, mock_save_draft):
        """Test retry logic on failure."""
        # Fail twice, then succeed
        mock_save_draft.side_effect = [False, False, True]
        
        self.worker.set_save_data(
            "2024-01-15", "daily", "Test", "hash", "session"
        )
        self.worker.max_retries = 3  # Allow enough retries
        
        # Mock sleep to speed up test
        with patch.object(self.worker, 'msleep'):
            self.worker.run()
        
        # Should have called save_draft 3 times
        self.assertEqual(mock_save_draft.call_count, 3)
        
        # Should succeed eventually
        self.assertEqual(len(self.finish_results), 1)
        self.assertTrue(self.finish_results[0][0])
    
    @patch('src.ui.auto_save_manager.SaveWorker._save_draft')
    def test_max_retries_exceeded(self, mock_save_draft):
        """Test behavior when max retries exceeded."""
        mock_save_draft.return_value = False  # Always fail
        
        self.worker.set_save_data(
            "2024-01-15", "daily", "Test", "hash", "session"
        )
        self.worker.max_retries = 2
        
        # Mock sleep to speed up test
        with patch.object(self.worker, 'msleep'):
            self.worker.run()
        
        # Should have tried max_retries times
        self.assertEqual(mock_save_draft.call_count, 2)
        
        # Should emit error
        self.assertEqual(len(self.errors), 1)
        self.assertIn("Failed to save after 2 attempts", self.errors[0])


if __name__ == '__main__':
    unittest.main()