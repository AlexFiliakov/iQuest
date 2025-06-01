"""Demo script to showcase the UI improvements made to the Apple Health Monitor Dashboard.

This script demonstrates the improvements made to:
1. Tab navigation styling with better contrast
2. Form layout with consistent grid system
3. Enhanced color contrast for better readability
4. Proper spacing using 8px grid system
"""

import sys
from PyQt6.QtWidgets import QApplication, QMainWindow, QTabWidget, QVBoxLayout, QWidget
from src.ui.configuration_tab_improved import ConfigurationTabImproved
from src.ui.style_manager import StyleManager
from src.utils.logging_config import setup_logging

# Setup logging
setup_logging()


class UIImprovementDemo(QMainWindow):
    """Demo window to showcase UI improvements."""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Apple Health Monitor - UI Improvements Demo")
        self.setGeometry(100, 100, 1400, 900)
        
        # Initialize style manager
        self.style_manager = StyleManager()
        
        # Create central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Main layout
        layout = QVBoxLayout(central_widget)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Create tab widget with improved styling
        self.tab_widget = QTabWidget()
        self.tab_widget.setStyleSheet(self.style_manager.get_tab_widget_style())
        
        # Add improved configuration tab
        config_tab = ConfigurationTabImproved()
        self.tab_widget.addTab(config_tab, "Configuration")
        
        # Add placeholder tabs to show tab styling
        placeholder_tab1 = QWidget()
        placeholder_layout1 = QVBoxLayout(placeholder_tab1)
        placeholder_layout1.addStretch()
        self.tab_widget.addTab(placeholder_tab1, "Daily")
        
        placeholder_tab2 = QWidget()
        placeholder_layout2 = QVBoxLayout(placeholder_tab2)
        placeholder_layout2.addStretch()
        self.tab_widget.addTab(placeholder_tab2, "Weekly")
        
        placeholder_tab3 = QWidget()
        placeholder_layout3 = QVBoxLayout(placeholder_tab3)
        placeholder_layout3.addStretch()
        self.tab_widget.addTab(placeholder_tab3, "Monthly")
        
        placeholder_tab4 = QWidget()
        placeholder_layout4 = QVBoxLayout(placeholder_tab4)
        placeholder_layout4.addStretch()
        self.tab_widget.addTab(placeholder_tab4, "Health Score")
        
        layout.addWidget(self.tab_widget)
        
        # Apply global styling
        self.style_manager.apply_global_style(app)
        
        # Set window styling
        self.setStyleSheet(self.style_manager.get_main_window_style())


def main():
    """Run the UI improvements demo."""
    global app
    app = QApplication(sys.argv)
    
    # Set application metadata
    app.setApplicationName("Apple Health Monitor")
    app.setOrganizationName("Health Analytics")
    
    # Create and show demo window
    demo = UIImprovementDemo()
    demo.show()
    
    sys.exit(app.exec())


if __name__ == "__main__":
    main()