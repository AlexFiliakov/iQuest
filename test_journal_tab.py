"""Test script for journal tab integration."""

import sys
import os
from PyQt6.QtWidgets import QApplication, QMainWindow, QTabWidget
from PyQt6.QtCore import Qt

# Add src to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.ui.journal_tab_widget import JournalTabWidget
from src.data_access import DataAccess


def test_journal_tab():
    """Test the journal tab widget."""
    app = QApplication(sys.argv)
    
    # Create main window
    window = QMainWindow()
    window.setWindowTitle("Journal Tab Test")
    window.resize(1200, 800)
    
    # Create tab widget
    tab_widget = QTabWidget()
    window.setCentralWidget(tab_widget)
    
    # Create data access
    data_access = DataAccess()
    
    # Create journal tab
    journal_tab = JournalTabWidget(data_access)
    tab_widget.addTab(journal_tab, "Journal")
    
    # Show window
    window.show()
    
    print("Journal tab created successfully!")
    print("Features integrated:")
    print("- Journal editor widget")
    print("- Journal history widget") 
    print("- Journal search widget")
    print("- Export functionality")
    print("\nKeyboard shortcuts:")
    print("- Alt+J: Switch to Journal tab")
    print("- Ctrl+8: Switch to Journal tab (by number)")
    
    # Run app
    sys.exit(app.exec())


if __name__ == "__main__":
    test_journal_tab()