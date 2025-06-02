#!/usr/bin/env python3
"""Integration test for auto-save functionality in journal editor.

This script tests the complete auto-save integration including:
- Auto-save triggering after 3 seconds of inactivity
- Manual save with Ctrl+S
- Save status indicator updates
- Character limit enforcement
- Modified flag tracking
"""

import sys
import time
from datetime import datetime
from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import QTimer, Qt, QDate
from PyQt6.QtTest import QTest

# Add src to path
sys.path.insert(0, 'src')

from src.data_access import DataAccess
from src.ui.journal_editor_widget import JournalEditorWidget
from src.utils.logging_config import setup_logging, get_logger

# Setup logging
setup_logging()
logger = get_logger(__name__)


def test_auto_save_integration():
    """Test the complete auto-save integration."""
    logger.info("=== Testing Auto-Save Integration ===")
    
    # Create application
    app = QApplication(sys.argv)
    
    # Initialize data access
    data_access = DataAccess()
    
    # Create journal editor widget
    editor = JournalEditorWidget(data_access)
    editor.show()
    
    # Test 1: Initial state
    logger.info("\nTest 1: Checking initial state...")
    assert not editor.is_modified, "Editor should not be modified initially"
    assert editor.char_count_label.text() == "Characters: 0 / 10,000", "Character count should be 0"
    assert editor.word_count_label.text() == "Words: 0", "Word count should be 0"
    logger.info("✓ Initial state correct")
    
    # Test 2: Type some text and verify auto-save triggers
    logger.info("\nTest 2: Testing auto-save trigger...")
    test_text = "This is a test journal entry for auto-save functionality."
    
    # Type text
    editor.text_editor.setPlainText(test_text)
    app.processEvents()
    
    # Verify modified state
    assert editor.is_modified, "Editor should be marked as modified"
    assert editor.auto_save_manager.pending_save, "Auto-save should be pending"
    logger.info("✓ Text change detected, auto-save pending")
    
    # Check character count update
    char_count = len(test_text)
    expected_char_text = f"Characters: {char_count:,} / 10,000"
    assert editor.char_count_label.text() == expected_char_text, f"Character count should be {expected_char_text}"
    logger.info(f"✓ Character count updated: {char_count}")
    
    # Test 3: Wait for debounce and verify save triggers
    logger.info("\nTest 3: Waiting for auto-save to trigger (3 seconds)...")
    
    # Monitor save status
    save_triggered = False
    def on_save_requested(date, type, content):
        nonlocal save_triggered
        save_triggered = True
        logger.info(f"✓ Auto-save triggered for {type} entry on {date}")
        assert content == test_text, "Saved content should match typed text"
    
    editor.auto_save_manager.saveRequested.connect(on_save_requested)
    
    # Wait for debounce period (3 seconds)
    start_time = time.time()
    while time.time() - start_time < 4 and not save_triggered:
        app.processEvents()
        time.sleep(0.1)
    
    assert save_triggered, "Auto-save should have triggered after 3 seconds"
    
    # Test 4: Test rapid typing (max wait enforcement)
    logger.info("\nTest 4: Testing max wait enforcement with rapid typing...")
    editor.text_editor.clear()
    app.processEvents()
    
    save_count = 0
    def count_saves(date, type, content):
        nonlocal save_count
        save_count += 1
        logger.info(f"Save #{save_count} triggered")
    
    # Disconnect previous handler and connect counter
    editor.auto_save_manager.saveRequested.disconnect()
    editor.auto_save_manager.saveRequested.connect(count_saves)
    
    # Type continuously for 5 seconds
    logger.info("Typing continuously...")
    for i in range(50):
        editor.text_editor.insertPlainText(f"Text {i} ")
        app.processEvents()
        time.sleep(0.1)
    
    # Should have triggered at least once due to max wait
    assert save_count >= 1, "Auto-save should trigger due to max wait time"
    logger.info(f"✓ Max wait enforcement working - {save_count} saves triggered")
    
    # Test 5: Test manual save (Ctrl+S)
    logger.info("\nTest 5: Testing manual save...")
    editor.text_editor.setPlainText("Manual save test")
    editor.is_modified = True
    app.processEvents()
    
    # Trigger manual save
    editor.save_entry()
    app.processEvents()
    
    logger.info("✓ Manual save triggered successfully")
    
    # Test 6: Test auto-save toggle
    logger.info("\nTest 6: Testing auto-save toggle...")
    
    # Disable auto-save
    editor.auto_save_checkbox.setChecked(False)
    app.processEvents()
    assert not editor.auto_save_manager.enabled, "Auto-save should be disabled"
    logger.info("✓ Auto-save disabled")
    
    # Enable auto-save
    editor.auto_save_checkbox.setChecked(True)
    app.processEvents()
    assert editor.auto_save_manager.enabled, "Auto-save should be enabled"
    logger.info("✓ Auto-save re-enabled")
    
    # Test 7: Test character limit
    logger.info("\nTest 7: Testing character limit enforcement...")
    
    # Create text that exceeds limit
    long_text = "x" * 10001  # One character over limit
    editor.text_editor.setPlainText(long_text)
    app.processEvents()
    
    # Should be truncated to limit
    actual_length = len(editor.text_editor.toPlainText())
    assert actual_length == 10000, f"Text should be truncated to 10,000 characters, but is {actual_length}"
    logger.info("✓ Character limit enforced")
    
    # Test 8: Test save status indicator
    logger.info("\nTest 8: Testing save status indicator...")
    
    # Check that status indicator exists and is visible
    assert hasattr(editor, 'save_status_indicator'), "Save status indicator should exist"
    assert editor.save_status_indicator.isVisible(), "Save status indicator should be visible"
    
    # Test different states
    editor.save_status_indicator.set_modified_status()
    app.processEvents()
    logger.info("✓ Modified status set")
    
    editor.save_status_indicator.set_saving_status()
    app.processEvents()
    logger.info("✓ Saving status set")
    
    editor.save_status_indicator.set_saved_status(QDateTime.currentDateTime())
    app.processEvents()
    logger.info("✓ Saved status set")
    
    editor.save_status_indicator.set_error_status("Test error", "Error details")
    app.processEvents()
    logger.info("✓ Error status set")
    
    # Clean up
    editor.close()
    
    logger.info("\n=== All Auto-Save Integration Tests Passed! ===")


def main():
    """Run auto-save integration tests."""
    try:
        test_auto_save_integration()
        logger.info("\n✅ Auto-save integration test completed successfully!")
    except AssertionError as e:
        logger.error(f"\n❌ Test failed: {e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"\n❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()