#!/usr/bin/env python3
"""
Test script to verify the menu bar overlay fix.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from PyQt6.QtWidgets import QApplication, QMainWindow, QMenuBar, QMenu, QTabWidget, QWidget, QVBoxLayout, QLabel
from PyQt6.QtCore import Qt
from src.ui.style_manager import StyleManager

class TestWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Menu Bar Test")
        self.setGeometry(100, 100, 800, 600)
        
        # Apply style manager
        self.style_manager = StyleManager()
        self.setStyleSheet(self.style_manager.get_main_window_style())
        
        # Create menu bar
        menu_bar = self.menuBar()
        menu_bar.setStyleSheet(self.style_manager.get_menu_bar_style())
        menu_bar.setNativeMenuBar(False)
        menu_bar.setFixedHeight(30)
        
        # Add File menu
        file_menu = menu_bar.addMenu("&File")
        file_menu.addAction("&Open")
        file_menu.addAction("&Save")
        file_menu.addSeparator()
        file_menu.addAction("E&xit")
        
        # Add Help menu
        help_menu = menu_bar.addMenu("&Help")
        help_menu.addAction("&About")
        
        # Create tab widget
        tab_widget = QTabWidget()
        tab_widget.setStyleSheet(self.style_manager.get_tab_widget_style())
        tab_widget.setDocumentMode(True)
        
        # Add some tabs
        for i in range(3):
            tab = QWidget()
            layout = QVBoxLayout(tab)
            label = QLabel(f"Tab {i+1} Content")
            label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            layout.addWidget(label)
            tab_widget.addTab(tab, f"Tab {i+1}")
        
        self.setCentralWidget(tab_widget)
        self.centralWidget().setContentsMargins(0, 0, 0, 0)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = TestWindow()
    window.show()
    
    print("Menu bar overlay test window opened.")
    print("Check if File and Help menus are clickable and not covered by any rectangle.")
    print("The menu bar should be clearly visible at the top of the window.")
    
    sys.exit(app.exec())