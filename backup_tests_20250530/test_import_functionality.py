#!/usr/bin/env python3
"""Test script to verify the import functionality works correctly."""

import sys
from PyQt6.QtWidgets import QApplication
from src.ui.main_window import MainWindow
from src.utils.logging_config import get_logger

logger = get_logger(__name__)

def main():
    """Test the import functionality."""
    app = QApplication(sys.argv)
    
    try:
        # Create main window
        logger.info("Creating main window...")
        window = MainWindow()
        logger.info("Main window created successfully!")
        
        # Check configuration tab
        if hasattr(window, 'config_tab'):
            logger.info("Configuration tab found")
            
            # Check if _on_browse_clicked method exists
            if hasattr(window.config_tab, '_on_browse_clicked'):
                logger.info("✓ _on_browse_clicked method exists in config tab")
            else:
                logger.error("✗ _on_browse_clicked method NOT found in config tab")
                
            # Check if necessary UI elements exist
            if hasattr(window.config_tab, 'file_path_input'):
                logger.info("✓ file_path_input exists")
            else:
                logger.warning("✗ file_path_input NOT found")
                
            if hasattr(window.config_tab, 'progress_bar'):
                logger.info("✓ progress_bar exists")
            else:
                logger.warning("✗ progress_bar NOT found")
        else:
            logger.error("Configuration tab NOT found!")
        
        # Show window
        window.show()
        logger.info("Window displayed successfully!")
        
        # Test complete message
        logger.info("""
        ========================================
        Import functionality test complete!
        
        To test manually:
        1. Click "Browse" button in Configuration tab
        2. Or use File > Import... from menu
        
        Both should open a file dialog.
        ========================================
        """)
        
        # Run the app
        sys.exit(app.exec())
        
    except Exception as e:
        logger.error(f"Failed during test: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())