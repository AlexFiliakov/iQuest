"""Performance tests for auto-save functionality.

This module tests that the auto-save feature meets the performance requirement
of having less than 5% impact on typing performance.
"""

import time
import pytest
from unittest.mock import Mock, patch, MagicMock
from PyQt6.QtCore import QTimer, Qt
from PyQt6.QtTest import QTest
from PyQt6.QtWidgets import QApplication, QTextEdit

from src.ui.journal_editor_widget import JournalEditorWidget
from src.ui.auto_save_manager import AutoSaveManager
from src.data_access import DataAccess


class TypingPerformanceMonitor:
    """Monitor typing performance metrics."""
    
    def __init__(self):
        self.keystroke_times = []
        self.save_times = []
        self.total_keystrokes = 0
        self.saves_triggered = 0
        
    def record_keystroke(self, duration):
        """Record keystroke processing time."""
        self.keystroke_times.append(duration)
        self.total_keystrokes += 1
        
    def record_save(self, duration):
        """Record save operation time."""
        self.save_times.append(duration)
        self.saves_triggered += 1
        
    def get_metrics(self):
        """Get performance metrics."""
        avg_keystroke = sum(self.keystroke_times) / len(self.keystroke_times) if self.keystroke_times else 0
        avg_save = sum(self.save_times) / len(self.save_times) if self.save_times else 0
        max_keystroke = max(self.keystroke_times) if self.keystroke_times else 0
        
        return {
            'average_keystroke_ms': avg_keystroke * 1000,
            'average_save_ms': avg_save * 1000,
            'max_keystroke_ms': max_keystroke * 1000,
            'total_keystrokes': self.total_keystrokes,
            'saves_triggered': self.saves_triggered,
            'keystroke_overhead_percent': 0  # Will be calculated
        }


@pytest.fixture
def app(qtbot):
    """Create QApplication for testing."""
    return QApplication.instance() or QApplication([])


@pytest.fixture
def mock_data_access():
    """Create mock data access."""
    mock = Mock(spec=DataAccess)
    mock.get_journal_entries.return_value = []
    mock.search_journal_entries.return_value = []
    return mock


@pytest.fixture
def journal_editor(qtbot, mock_data_access):
    """Create journal editor widget for testing."""
    widget = JournalEditorWidget(mock_data_access)
    qtbot.addWidget(widget)
    widget.show()
    return widget


@pytest.mark.performance
class TestAutoSavePerformance:
    """Test auto-save performance impact."""
    
    def test_typing_performance_without_autosave(self, qtbot, journal_editor):
        """Measure baseline typing performance without auto-save."""
        # Disable auto-save
        journal_editor.auto_save_manager.set_enabled(False)
        
        monitor = TypingPerformanceMonitor()
        text_editor = journal_editor.text_editor
        
        # Type 100 characters
        test_text = "The quick brown fox jumps over the lazy dog. " * 2
        
        for char in test_text[:100]:
            start_time = time.time()
            QTest.keyClick(text_editor, char)
            qtbot.wait(1)  # Small wait to simulate realistic typing
            duration = time.time() - start_time
            monitor.record_keystroke(duration)
            
        metrics = monitor.get_metrics()
        
        # Baseline should be fast (typically < 5ms per keystroke)
        assert metrics['average_keystroke_ms'] < 10
        assert metrics['total_keystrokes'] == 100
        assert metrics['saves_triggered'] == 0
        
        return metrics
        
    def test_typing_performance_with_autosave(self, qtbot, journal_editor):
        """Measure typing performance with auto-save enabled."""
        # Enable auto-save with 3-second delay
        journal_editor.auto_save_manager.set_enabled(True)
        journal_editor.auto_save_manager.set_debounce_delay(3000)
        
        monitor = TypingPerformanceMonitor()
        text_editor = journal_editor.text_editor
        
        # Mock the save operation to track when it happens
        original_perform_save = journal_editor._perform_auto_save
        
        def mock_perform_save(*args, **kwargs):
            save_start = time.time()
            original_perform_save(*args, **kwargs)
            monitor.record_save(time.time() - save_start)
            
        journal_editor._perform_auto_save = mock_perform_save
        
        # Type 100 characters with pauses to trigger auto-save
        test_text = "The quick brown fox jumps over the lazy dog. " * 2
        
        # Type first 50 characters
        for i, char in enumerate(test_text[:50]):
            start_time = time.time()
            QTest.keyClick(text_editor, char)
            qtbot.wait(1)
            duration = time.time() - start_time
            monitor.record_keystroke(duration)
            
        # Pause for 3.5 seconds to trigger auto-save
        qtbot.wait(3500)
        
        # Type next 50 characters
        for char in test_text[50:100]:
            start_time = time.time()
            QTest.keyClick(text_editor, char)
            qtbot.wait(1)
            duration = time.time() - start_time
            monitor.record_keystroke(duration)
            
        # Wait for any pending saves
        qtbot.wait(1000)
        
        metrics = monitor.get_metrics()
        
        # Performance should still be good
        assert metrics['average_keystroke_ms'] < 15  # Allow some overhead
        assert metrics['total_keystrokes'] == 100
        assert metrics['saves_triggered'] >= 1  # At least one save should trigger
        
        return metrics
        
    def test_performance_impact_percentage(self, qtbot, journal_editor):
        """Test that auto-save has less than 5% performance impact."""
        # Run baseline test
        journal_editor.auto_save_manager.set_enabled(False)
        baseline_avg = self._measure_typing_speed(qtbot, journal_editor, enabled=False)
        
        # Run with auto-save
        journal_editor.auto_save_manager.set_enabled(True)
        autosave_avg = self._measure_typing_speed(qtbot, journal_editor, enabled=True)
        
        # Calculate percentage increase
        if baseline_avg > 0:
            overhead_percent = ((autosave_avg - baseline_avg) / baseline_avg) * 100
        else:
            overhead_percent = 0
            
        print(f"Baseline: {baseline_avg:.2f}ms, With auto-save: {autosave_avg:.2f}ms")
        print(f"Performance overhead: {overhead_percent:.2f}%")
        
        # Must be less than 5% overhead
        assert overhead_percent < 5.0, f"Auto-save overhead {overhead_percent:.2f}% exceeds 5% limit"
        
    def test_rapid_typing_performance(self, qtbot, journal_editor):
        """Test performance during rapid continuous typing."""
        journal_editor.auto_save_manager.set_enabled(True)
        journal_editor.auto_save_manager.set_debounce_delay(3000)
        journal_editor.auto_save_manager.set_max_wait_time(30000)
        
        text_editor = journal_editor.text_editor
        monitor = TypingPerformanceMonitor()
        
        # Simulate very fast typing (no pauses)
        test_text = "a" * 500  # 500 characters
        
        start_time = time.time()
        for char in test_text:
            char_start = time.time()
            QTest.keyClick(text_editor, char)
            # No wait - simulate fast typing
            monitor.record_keystroke(time.time() - char_start)
            
        total_time = time.time() - start_time
        
        metrics = monitor.get_metrics()
        
        # Even with rapid typing, performance should be good
        assert metrics['average_keystroke_ms'] < 5  # Very fast
        assert total_time < 2.0  # 500 chars in under 2 seconds
        
        # Auto-save should not interfere with rapid typing
        typed_text = text_editor.toPlainText()
        assert len(typed_text) == 500  # All characters captured
        
    def test_memory_usage_during_typing(self, qtbot, journal_editor):
        """Test that memory usage doesn't grow excessively during typing."""
        import psutil
        import os
        
        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss / 1024 / 1024  # MB
        
        # Enable auto-save
        journal_editor.auto_save_manager.set_enabled(True)
        
        # Type a large amount of text
        text_editor = journal_editor.text_editor
        large_text = "Lorem ipsum dolor sit amet. " * 100  # ~2800 characters
        
        for i, char in enumerate(large_text):
            QTest.keyClick(text_editor, char)
            if i % 100 == 0:
                qtbot.wait(10)  # Brief pause every 100 chars
                
        # Wait for any pending operations
        qtbot.wait(2000)
        
        final_memory = process.memory_info().rss / 1024 / 1024  # MB
        memory_increase = final_memory - initial_memory
        
        print(f"Memory increase: {memory_increase:.2f} MB")
        
        # Memory increase should be reasonable (less than 50MB for this test)
        assert memory_increase < 50, f"Excessive memory usage: {memory_increase:.2f} MB"
        
    def _measure_typing_speed(self, qtbot, journal_editor, enabled=True):
        """Measure average keystroke processing time."""
        journal_editor.auto_save_manager.set_enabled(enabled)
        text_editor = journal_editor.text_editor
        text_editor.clear()
        
        keystroke_times = []
        test_text = "The quick brown fox jumps over the lazy dog."
        
        for char in test_text:
            start = time.time()
            QTest.keyClick(text_editor, char)
            qtbot.wait(1)  # Minimal wait
            keystroke_times.append((time.time() - start) * 1000)  # Convert to ms
            
        return sum(keystroke_times) / len(keystroke_times) if keystroke_times else 0


@pytest.mark.performance
class TestAutoSaveConcurrency:
    """Test auto-save behavior under concurrent operations."""
    
    def test_multiple_saves_queued(self, qtbot, journal_editor):
        """Test that multiple save requests are properly queued."""
        save_count = 0
        
        def count_saves(*args, **kwargs):
            nonlocal save_count
            save_count += 1
            
        with patch.object(journal_editor, '_perform_auto_save', side_effect=count_saves):
            # Type text with multiple pauses
            text_editor = journal_editor.text_editor
            
            for i in range(3):
                QTest.keyClicks(text_editor, f"Paragraph {i}. ")
                qtbot.wait(3500)  # Trigger auto-save
                
        # Should have triggered 3 saves
        assert save_count == 3
        
    def test_save_during_typing_doesnt_block(self, qtbot, journal_editor):
        """Test that save operations don't block typing."""
        text_editor = journal_editor.text_editor
        
        # Mock a slow save operation
        def slow_save(*args, **kwargs):
            time.sleep(0.5)  # 500ms save
            
        with patch.object(journal_editor.save_worker, 'run', side_effect=slow_save):
            # Start typing
            start_time = time.time()
            QTest.keyClicks(text_editor, "Testing typing during save")
            typing_time = time.time() - start_time
            
            # Typing should complete quickly despite slow save
            assert typing_time < 0.5  # Should not wait for save


if __name__ == "__main__":
    pytest.main([__file__, "-v"])