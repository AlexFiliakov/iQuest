"""Tests for main module."""

import pytest
import sys
from unittest.mock import Mock, patch, MagicMock
from PyQt6.QtWidgets import QApplication

from src.main import main, exception_hook
from src.utils.logging_config import setup_logging


class TestMain:
    """Test main application entry point."""
    
    @pytest.fixture
    def mock_app(self):
        """Mock QApplication."""
        with patch('src.main.QApplication') as mock_app_class:
            mock_app = Mock()
            mock_app_class.return_value = mock_app
            yield mock_app
    
    @pytest.fixture
    def mock_window(self):
        """Mock MainWindow."""
        with patch('src.main.MainWindow') as mock_window_class:
            mock_window = Mock()
            mock_window_class.return_value = mock_window
            yield mock_window
    
    def test_setup_logging(self):
        """Test logging setup."""
        # The setup_logging has already been called at module import time
        # Just verify that logger exists and is configured
        from src.main import logger
        assert logger is not None
        assert logger.name == 'apple_health_monitor.src.main'
        assert len(logger.handlers) > 0 or logger.parent.handlers  # Has handlers
    
    @pytest.mark.skip(reason="Exception hook test conflicts with pytest-qt's event loop")
    def test_exception_hook_installed(self):
        """Test that exception hook is installed."""
        # The exception hook should be set when the module is imported
        # pytest-qt wraps the exception hook, so we just check it's callable
        assert callable(sys.excepthook)
        
        # Test the error handler
        with patch('src.main.logger') as mock_logger:
            test_exception = Exception("Test error")
            sys.excepthook(Exception, test_exception, None)
            
            # Verify it was logged
            mock_logger.critical.assert_called()
    
    def test_main_application_creation(self, mock_app, mock_window):
        """Test main application creation."""
        with patch('sys.argv', ['test_app']):
            with patch('sys.exit') as mock_exit:
                main()
                
                # Verify QApplication was created
                mock_app.__class__.assert_called_once_with(['test_app'])
                
                # Verify MainWindow was created and shown
                mock_window.__class__.assert_called_once()
                mock_window.show.assert_called_once()
                
                # Verify app.exec was called
                mock_app.exec.assert_called_once()
    
    def test_main_with_arguments(self, mock_app, mock_window):
        """Test main with command line arguments."""
        test_args = ['test_app', '--debug', '--file', 'test.db']
        
        with patch('sys.argv', test_args):
            with patch('sys.exit') as mock_exit:
                main()
                
                # Verify args were passed to QApplication
                mock_app.__class__.assert_called_once_with(test_args)
    
    def test_main_exception_handling(self, mock_app):
        """Test exception handling in main."""
        # Make MainWindow raise an exception
        with patch('src.main.MainWindow') as mock_window_class:
            mock_window_class.side_effect = Exception("Window creation failed")
            
            with patch('sys.exit') as mock_exit:
                with patch('src.main.logger') as mock_logger:
                    # Should not raise, but log error and exit
                    main()
                    
                    # Verify error was logged
                    mock_logger.error.assert_called()
                    
                    # Verify clean exit
                    mock_exit.assert_called_with(1)
    
    def test_qapplication_singleton(self, mock_app):
        """Test QApplication singleton handling."""
        # Simulate existing QApplication
        with patch('src.main.QApplication.instance') as mock_instance:
            mock_instance.return_value = mock_app
            
            with patch('sys.exit') as mock_exit:
                main()
                
                # Should use existing instance, not create new one
                mock_app.__class__.assert_not_called()
    
    def test_logging_configuration(self):
        """Test detailed logging configuration."""
        with patch('logging.basicConfig') as mock_basic_config:
            with patch('pathlib.Path') as mock_path:
                # Mock log directory creation
                mock_path.return_value.mkdir.return_value = None
                
                setup_logging()
                
                # Verify logger configuration
                mock_basic_config.assert_called_once()
                
                # Verify log directory creation attempt
                mock_path.return_value.mkdir.assert_called()
    
    def test_high_dpi_scaling(self, mock_app):
        """Test high DPI scaling setup."""
        with patch('src.main.QApplication.setAttribute') as mock_set_attr:
            with patch('sys.exit') as mock_exit:
                main()
                
                # Verify high DPI scaling attributes were set
                assert mock_set_attr.called
    
    def test_application_metadata(self, mock_app):
        """Test application metadata setup."""
        with patch('sys.exit') as mock_exit:
            main()
            
            # Verify application metadata was set
            mock_app.setApplicationName.assert_called()
            mock_app.setOrganizationName.assert_called()


class TestErrorHandling:
    """Test error handling functionality."""
    
    def test_custom_exception_handler(self):
        """Test custom exception handler."""
        with patch('src.main.logger') as mock_logger:
            with patch('src.main.QMessageBox') as mock_msgbox:
                # Get the custom exception handler (already installed)
                handler = exception_hook
                
                # Test with various exceptions
                test_exception = ValueError("Test error")
                handler(ValueError, test_exception, None)
                
                # Verify logging
                mock_logger.critical.assert_called()
                
                # Verify error dialog (if GUI is available)
                if QApplication.instance():
                    mock_msgbox.critical.assert_called()
    
    def test_unhandled_exception_logging(self):
        """Test unhandled exception logging."""
        with patch('src.main.logger') as mock_logger:
            # Exception hook is already installed at module level
            
            # Simulate unhandled exception
            try:
                raise RuntimeError("Unhandled error")
            except RuntimeError as e:
                sys.excepthook(type(e), e, sys.exc_info()[2])
            
            # Verify critical error was logged
            mock_logger.critical.assert_called()
            call_args = mock_logger.critical.call_args[0][0]
            assert "Unhandled error" in call_args