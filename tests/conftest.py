"""Pytest configuration for the Apple Health Monitor test suite."""
import os
import sys
from pathlib import Path

# Add the project root to the Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Import shared fixtures and configurations
# Note: We don't have generators module in this fresh test setup
# If needed, create tests/fixtures/ and tests/generators/ directories

from unittest.mock import MagicMock, Mock

import pytest

# Set up headless mode for PyQt testing
os.environ['QT_QPA_PLATFORM'] = 'offscreen'

# Import PyQt after setting environment
try:
    from PyQt6.QtCore import Qt
    from PyQt6.QtWidgets import QApplication
    
    @pytest.fixture(scope='session', autouse=True)
    def qapp():
        """Create a QApplication instance for the entire test session."""
        app = QApplication.instance()
        if app is None:
            app = QApplication(sys.argv)
        yield app
        # Don't quit the app here as pytest-qt will handle it
        
except ImportError:
    # PyQt6 not available, skip fixture
    pass