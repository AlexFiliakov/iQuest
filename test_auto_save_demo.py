#!/usr/bin/env python3
"""Demo script to test and validate auto-save functionality.

This script demonstrates all aspects of the auto-save implementation:
- Debounced saving after 3 seconds of inactivity
- Maximum wait time enforcement
- Save status indicator updates
- Draft recovery dialog
- Settings panel integration
- Performance monitoring
"""

import sys
import time
from datetime import datetime, date
from PyQt6.QtWidgets import QApplication, QMainWindow, QTabWidget, QVBoxLayout, QWidget, QPushButton, QTextEdit, QHBoxLayout, QLabel
from PyQt6.QtCore import QTimer, Qt, QDate
from PyQt6.QtGui import QFont

# Add project root to path
sys.path.insert(0, '/mnt/c/Users/alexf/OneDrive/Documents/Projects/Apple Health Exports')

from src.ui.journal_editor_widget import JournalEditorWidget
from src.ui.auto_save_settings_panel import AutoSaveSettingsPanel
from src.ui.draft_recovery_dialog import DraftRecoveryDialog
from src.ui.settings_manager import SettingsManager
from src.data_access import DataAccess
from src import config
from src.utils.logging_config import setup_logging

# Setup logging
logger = setup_logging()


class AutoSaveDemo(QMainWindow):
    """Demo application for testing auto-save functionality."""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Auto-Save Demo - Journal Editor")
        self.setGeometry(100, 100, 1200, 800)
        
        # Initialize components
        self.data_access = DataAccess()
        self.settings_manager = SettingsManager()
        
        self.setup_ui()
        self.setup_demo_controls()
        
    def setup_ui(self):
        """Set up the user interface."""
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)
        
        # Demo controls at the top
        self.demo_controls = QWidget()
        self.demo_layout = QHBoxLayout(self.demo_controls)
        layout.addWidget(self.demo_controls)
        
        # Tab widget
        self.tabs = QTabWidget()
        
        # Journal editor tab
        self.journal_editor = JournalEditorWidget(self.data_access)
        self.tabs.addTab(self.journal_editor, "Journal Editor")
        
        # Auto-save settings tab
        self.settings_panel = AutoSaveSettingsPanel(self.settings_manager)
        self.settings_panel.settingsChanged.connect(self.journal_editor.update_auto_save_settings)
        self.tabs.addTab(self.settings_panel, "Auto-Save Settings")
        
        # Performance monitor tab
        self.performance_widget = PerformanceMonitor(self.journal_editor.auto_save_manager)
        self.tabs.addTab(self.performance_widget, "Performance Monitor")
        
        layout.addWidget(self.tabs)
        
    def setup_demo_controls(self):
        """Set up demo control buttons."""
        # Simulate crash button
        crash_btn = QPushButton("Simulate Crash (Create Draft)")
        crash_btn.clicked.connect(self.simulate_crash)
        self.demo_layout.addWidget(crash_btn)
        
        # Show recovery dialog button
        recovery_btn = QPushButton("Show Recovery Dialog")
        recovery_btn.clicked.connect(self.show_recovery_dialog)
        self.demo_layout.addWidget(recovery_btn)
        
        # Force save button
        force_save_btn = QPushButton("Force Save Now")
        force_save_btn.clicked.connect(self.force_save)
        self.demo_layout.addWidget(force_save_btn)
        
        # Type test text button
        type_test_btn = QPushButton("Type Test Text")
        type_test_btn.clicked.connect(self.type_test_text)
        self.demo_layout.addWidget(type_test_btn)
        
        # Performance test button
        perf_test_btn = QPushButton("Run Performance Test")
        perf_test_btn.clicked.connect(self.run_performance_test)
        self.demo_layout.addWidget(perf_test_btn)
        
        self.demo_layout.addStretch()
        
        # Status label
        self.status_label = QLabel("Ready")
        self.demo_layout.addWidget(self.status_label)
        
    def simulate_crash(self):
        """Simulate a crash by creating an orphaned draft."""
        # Create a fake draft that would be recovered
        draft_data = {
            'id': 999,
            'entry_date': date.today().isoformat(),
            'entry_type': 'daily',
            'content': 'This is a test draft that was not saved due to a simulated crash.\n\n'
                      'It contains important information that should be recovered.\n\n'
                      '- Item 1: Important health note\n'
                      '- Item 2: Medication reminder\n'
                      '- Item 3: Exercise observations\n\n'
                      'This draft was created for testing the recovery functionality.',
            'saved_at': datetime.now().isoformat(),
            'session_id': 'old-session-123'
        }
        
        # In a real implementation, this would be saved to the database
        self.orphaned_draft = draft_data
        self.status_label.setText("Crash simulated - draft created")
        
    def show_recovery_dialog(self):
        """Show the draft recovery dialog."""
        if hasattr(self, 'orphaned_draft'):
            drafts = [self.orphaned_draft]
        else:
            # Create sample drafts
            drafts = [
                {
                    'id': 1,
                    'entry_date': '2025-01-27',
                    'entry_type': 'daily',
                    'content': 'Morning: Felt energetic after 8 hours of sleep...',
                    'saved_at': '2025-01-27T09:30:00',
                    'session_id': 'session-1'
                },
                {
                    'id': 2,
                    'entry_date': '2025-01-26',
                    'entry_type': 'weekly',
                    'content': 'Weekly reflection: This week was challenging...',
                    'saved_at': '2025-01-26T20:15:00',
                    'session_id': 'session-2'
                }
            ]
            
        dialog = DraftRecoveryDialog(drafts, self)
        dialog.drafts_recovered.connect(self.on_drafts_recovered)
        result = dialog.exec()
        
        if result:
            self.status_label.setText("Drafts recovered")
        else:
            self.status_label.setText("Recovery postponed")
            
    def on_drafts_recovered(self, drafts):
        """Handle recovered drafts."""
        count = len(drafts)
        self.status_label.setText(f"Recovered {count} draft(s)")
        
        # In real implementation, these would be restored to the editor
        if drafts:
            self.journal_editor._restore_draft(drafts[0])
            
    def force_save(self):
        """Force an immediate save."""
        self.journal_editor.auto_save_manager.force_save()
        self.status_label.setText("Force save triggered")
        
    def type_test_text(self):
        """Simulate typing to test auto-save."""
        text_editor = self.journal_editor.text_editor
        test_text = ("This is a test of the auto-save functionality. "
                    "As I type this text, the auto-save manager monitors changes "
                    "and triggers saves after 3 seconds of inactivity. "
                    "The maximum wait time ensures saves happen even during continuous typing.")
        
        # Clear existing text
        text_editor.clear()
        
        # Type one character at a time
        self.typing_index = 0
        self.typing_text = test_text
        self.typing_timer = QTimer()
        self.typing_timer.timeout.connect(self.type_next_character)
        self.typing_timer.start(50)  # 50ms between characters
        
    def type_next_character(self):
        """Type the next character in the test text."""
        if self.typing_index < len(self.typing_text):
            text_editor = self.journal_editor.text_editor
            text_editor.insertPlainText(self.typing_text[self.typing_index])
            self.typing_index += 1
        else:
            self.typing_timer.stop()
            self.status_label.setText("Test text typed - watch for auto-save")
            
    def run_performance_test(self):
        """Run a performance test."""
        self.status_label.setText("Running performance test...")
        
        # Get current stats
        stats = self.journal_editor.auto_save_manager.get_performance_stats()
        
        # Type rapidly
        text_editor = self.journal_editor.text_editor
        start_time = time.time()
        
        for i in range(100):
            text_editor.insertPlainText(f"Character {i} ")
            
        elapsed = time.time() - start_time
        chars_per_second = 100 / elapsed if elapsed > 0 else 0
        
        self.status_label.setText(f"Performance: {chars_per_second:.1f} chars/sec")
        
        # Update performance monitor
        self.performance_widget.update_stats()


class PerformanceMonitor(QWidget):
    """Widget to monitor auto-save performance."""
    
    def __init__(self, auto_save_manager):
        super().__init__()
        self.auto_save_manager = auto_save_manager
        self.setup_ui()
        
        # Update stats every second
        self.update_timer = QTimer()
        self.update_timer.timeout.connect(self.update_stats)
        self.update_timer.start(1000)
        
    def setup_ui(self):
        """Set up the performance monitor UI."""
        layout = QVBoxLayout(self)
        
        # Stats display
        self.stats_text = QTextEdit()
        self.stats_text.setReadOnly(True)
        self.stats_text.setFont(QFont('Consolas', 10))
        layout.addWidget(self.stats_text)
        
        # Refresh button
        refresh_btn = QPushButton("Refresh Stats")
        refresh_btn.clicked.connect(self.update_stats)
        layout.addWidget(refresh_btn)
        
    def update_stats(self):
        """Update the performance statistics display."""
        stats = self.auto_save_manager.get_performance_stats()
        
        text = f"""Auto-Save Performance Statistics
================================

Saves Triggered: {stats['saves_triggered']}
Saves Completed: {stats['saves_completed']}
Saves Failed: {stats['saves_failed']}

Success Rate: {stats['saves_completed'] / stats['saves_triggered'] * 100 if stats['saves_triggered'] > 0 else 0:.1f}%

Current Status:
- Enabled: {self.auto_save_manager.enabled}
- Debounce Delay: {self.auto_save_manager.debounce_delay}ms
- Max Wait Time: {self.auto_save_manager.max_wait_time}ms
- Save in Progress: {self.auto_save_manager.save_in_progress}
- Pending Save: {self.auto_save_manager.pending_save}

Session ID: {self.auto_save_manager.session_id}
Last Save: {self.auto_save_manager.last_save_time.strftime('%H:%M:%S')}
"""
        
        self.stats_text.setPlainText(text)


def main():
    """Run the auto-save demo application."""
    app = QApplication(sys.argv)
    
    # Apply application style
    app.setStyle('Fusion')
    
    demo = AutoSaveDemo()
    demo.show()
    
    # Show initial message
    demo.status_label.setText("Auto-save demo ready - try typing in the journal editor!")
    
    sys.exit(app.exec())


if __name__ == "__main__":
    main()