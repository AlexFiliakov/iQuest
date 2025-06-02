#!/usr/bin/env python3
"""Test script for auto-save functionality in journal editor.

This script tests the auto-save implementation including:
- Debounced timer behavior
- Save status indicator updates
- Draft storage and recovery
- Performance impact measurement
"""

import sys
import time
from datetime import datetime
from PyQt6.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget, QPushButton, QTextEdit
from PyQt6.QtCore import QTimer, Qt

# Add src to path
sys.path.insert(0, 'src')

from src.ui.auto_save_manager import AutoSaveManager, DebouncedTimer
from src.ui.save_status_indicator import SaveStatusIndicator
from src.data_access import DataAccess
from src.utils.logging_config import setup_logging, get_logger

# Setup logging
setup_logging()
logger = get_logger(__name__)


class AutoSaveTestWindow(QMainWindow):
    """Test window for auto-save functionality."""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Auto-Save Test")
        self.setGeometry(100, 100, 800, 600)
        
        # Initialize data access
        self.data_access = DataAccess()
        
        # Create central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)
        
        # Create text editor
        self.text_edit = QTextEdit()
        self.text_edit.setPlaceholderText("Type here to test auto-save...")
        layout.addWidget(self.text_edit)
        
        # Create save status indicator
        self.status_indicator = SaveStatusIndicator()
        layout.addWidget(self.status_indicator)
        
        # Create auto-save manager
        self.auto_save_manager = AutoSaveManager(self.data_access, self)
        self.auto_save_manager.statusChanged.connect(self.status_indicator.set_status)
        self.auto_save_manager.saveRequested.connect(self.on_save_requested)
        self.auto_save_manager.saveCompleted.connect(self.on_save_completed)
        
        # Connect text changes
        self.text_edit.textChanged.connect(self.on_text_changed)
        
        # Add test buttons
        button_layout = QVBoxLayout()
        
        # Force save button
        force_save_btn = QPushButton("Force Save Now")
        force_save_btn.clicked.connect(self.auto_save_manager.force_save)
        button_layout.addWidget(force_save_btn)
        
        # Test status buttons
        test_modified_btn = QPushButton("Test Modified Status")
        test_modified_btn.clicked.connect(lambda: self.status_indicator.set_modified_status())
        button_layout.addWidget(test_modified_btn)
        
        test_saving_btn = QPushButton("Test Saving Status")
        test_saving_btn.clicked.connect(lambda: self.status_indicator.set_saving_status())
        button_layout.addWidget(test_saving_btn)
        
        test_saved_btn = QPushButton("Test Saved Status")
        test_saved_btn.clicked.connect(lambda: self.status_indicator.set_saved_status(QDateTime.currentDateTime()))
        button_layout.addWidget(test_saved_btn)
        
        test_error_btn = QPushButton("Test Error Status")
        test_error_btn.clicked.connect(
            lambda: self.status_indicator.set_error_status("Save failed", "Database connection error")
        )
        button_layout.addWidget(test_error_btn)
        
        # Performance stats button
        stats_btn = QPushButton("Show Performance Stats")
        stats_btn.clicked.connect(self.show_performance_stats)
        button_layout.addWidget(stats_btn)
        
        layout.addLayout(button_layout)
        
        # Track performance
        self.type_start_time = None
        self.char_count = 0
        
    def on_text_changed(self):
        """Handle text changes."""
        # Track typing performance
        if self.type_start_time is None:
            self.type_start_time = time.time()
            
        text = self.text_edit.toPlainText()
        self.char_count = len(text)
        
        # Notify auto-save manager
        self.auto_save_manager.on_content_changed(
            datetime.now().date().isoformat(),
            "daily",
            text
        )
        
    def on_save_requested(self, entry_date: str, entry_type: str, content: str):
        """Handle save request from auto-save manager."""
        logger.info(f"Save requested for {entry_type} entry on {entry_date}")
        logger.info(f"Content length: {len(content)} characters")
        
        # Simulate save operation
        QTimer.singleShot(1000, lambda: self.simulate_save_complete(True))
        
    def on_save_completed(self, success: bool, message: str):
        """Handle save completion."""
        logger.info(f"Save completed: {success} - {message}")
        
    def simulate_save_complete(self, success: bool):
        """Simulate save completion after delay."""
        self.auto_save_manager._on_save_finished(success, "Test save completed")
        
    def show_performance_stats(self):
        """Show performance statistics."""
        stats = self.auto_save_manager.get_performance_stats()
        
        if self.type_start_time and self.char_count > 0:
            elapsed = time.time() - self.type_start_time
            chars_per_second = self.char_count / elapsed if elapsed > 0 else 0
            
            logger.info("=== Performance Statistics ===")
            logger.info(f"Characters typed: {self.char_count}")
            logger.info(f"Time elapsed: {elapsed:.2f} seconds")
            logger.info(f"Typing speed: {chars_per_second:.1f} chars/second")
            logger.info(f"Saves triggered: {stats['saves_triggered']}")
            logger.info(f"Saves completed: {stats['saves_completed']}")
            logger.info(f"Saves failed: {stats['saves_failed']}")
            logger.info("============================")
        else:
            logger.info("No typing statistics available yet")
            

def test_debounced_timer():
    """Test the debounced timer behavior."""
    logger.info("\n=== Testing DebouncedTimer ===")
    
    app = QApplication([])
    
    # Track timer fires
    fires = []
    
    def on_timer_fired():
        fires.append(time.time())
        logger.info(f"Timer fired at {time.time()}")
    
    # Create timer with 1 second debounce, 3 second max wait
    timer = DebouncedTimer(1000, 3000)
    timer.set_parent(QWidget())  # Need a parent for Qt timers
    timer.connect(on_timer_fired)
    
    # Test rapid resets
    logger.info("Testing rapid resets...")
    start_time = time.time()
    
    # Reset every 500ms for 2.5 seconds
    for i in range(5):
        timer.reset()
        logger.info(f"Reset {i+1} at {time.time() - start_time:.1f}s")
        app.processEvents()
        time.sleep(0.5)
    
    # Wait for timer to fire
    app.processEvents()
    time.sleep(2)
    app.processEvents()
    
    # Check results
    if len(fires) == 1:
        logger.info("✓ Timer fired once after debounce period")
    else:
        logger.error(f"✗ Timer fired {len(fires)} times, expected 1")
    
    # Test max wait enforcement
    logger.info("\nTesting max wait enforcement...")
    fires.clear()
    timer.stop()
    
    # Reset continuously for 4 seconds (exceeds 3 second max)
    start_time = time.time()
    for i in range(8):
        timer.reset()
        logger.info(f"Reset at {time.time() - start_time:.1f}s")
        app.processEvents()
        time.sleep(0.5)
        
        if len(fires) > 0:
            logger.info(f"✓ Max wait enforced - timer fired at {fires[0] - start_time:.1f}s")
            break
    
    if len(fires) == 0:
        logger.error("✗ Max wait not enforced - timer never fired")
    
    logger.info("=== DebouncedTimer test complete ===\n")


def main():
    """Run auto-save tests."""
    # Run timer tests first
    test_debounced_timer()
    
    # Run UI tests
    app = QApplication(sys.argv)
    window = AutoSaveTestWindow()
    window.show()
    
    logger.info("Auto-save test window opened. Try typing to test auto-save behavior.")
    logger.info("The auto-save should trigger 3 seconds after you stop typing.")
    logger.info("Maximum wait time is 30 seconds if you keep typing continuously.")
    
    sys.exit(app.exec())


if __name__ == "__main__":
    main()