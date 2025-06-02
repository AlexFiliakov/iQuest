"""Pytest configuration for the Apple Health Monitor test suite."""
import os
import sys
import tempfile
import shutil
from pathlib import Path

# Add the project root to the Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from unittest.mock import MagicMock, Mock
import pytest

# Set up headless mode for PyQt testing BEFORE importing PyQt
os.environ['QT_QPA_PLATFORM'] = 'offscreen'
os.environ['QT_LOGGING_RULES'] = '*.debug=false'  # Reduce Qt debug output

# Import PyQt after setting environment
try:
    from PyQt6.QtCore import Qt, QTimer
    from PyQt6.QtWidgets import QApplication
    
    # Global app instance to prevent multiple QApplication issues
    _qapp_instance = None
    
    @pytest.fixture(scope='session')
    def qapp():
        """Create a QApplication instance for the entire test session."""
        global _qapp_instance
        
        if _qapp_instance is None:
            # Check if an instance already exists
            app = QApplication.instance()
            if app is None:
                # Create new instance with minimal arguments
                app = QApplication([sys.argv[0], '-platform', 'offscreen'])
            _qapp_instance = app
            
        yield _qapp_instance
        # Don't quit the app - let pytest-qt handle cleanup
        
    @pytest.fixture(autouse=True)
    def qt_cleanup(qapp):
        """Ensure Qt cleanup after each test."""
        yield
        # Process any pending events
        QApplication.processEvents()
        
        # Clean up any widgets that weren't properly deleted
        for widget in QApplication.topLevelWidgets():
            if widget and not widget.isHidden():
                widget.close()
                widget.deleteLater()
        
        # Process deletion events
        QApplication.processEvents()
        
except ImportError:
    # PyQt6 not available, provide dummy fixtures
    @pytest.fixture(scope='session')
    def qapp():
        return None
        
    @pytest.fixture(autouse=True)
    def qt_cleanup():
        yield

# Fixture to provide isolated test database
@pytest.fixture
def test_db_path(tmp_path):
    """Provide a temporary database path for tests."""
    db_path = tmp_path / "test_health_monitor.db"
    yield str(db_path)
    # Cleanup
    if db_path.exists():
        try:
            db_path.unlink()
        except:
            pass

# Mock database for tests that don't need real DB
@pytest.fixture
def mock_db():
    """Provide a mock database connection."""
    mock = MagicMock()
    mock.get_connection.return_value.__enter__.return_value = MagicMock()
    return mock
