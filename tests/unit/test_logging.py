"""Tests for logging configuration."""

import unittest
import tempfile
import logging
import sys
from pathlib import Path

# Add the project root to Python path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.utils.logging_config import setup_logging, get_logger


class TestLoggingConfig(unittest.TestCase):
    """Test logging configuration functionality."""
    
    def setUp(self):
        """Set up test environment."""
        self.temp_dir = tempfile.mkdtemp()
        
    def test_setup_logging_creates_files(self):
        """Test that setup_logging creates log files."""
        logger = setup_logging(
            log_level="DEBUG",
            log_dir=self.temp_dir,
            app_name="test_app"
        )
        
        # Log some messages
        logger.debug("Debug message")
        logger.info("Info message")
        logger.error("Error message")
        
        # Check that log files were created
        log_file = Path(self.temp_dir) / "test_app.log"
        error_log_file = Path(self.temp_dir) / "test_app_errors.log"
        
        self.assertTrue(log_file.exists())
        self.assertTrue(error_log_file.exists())
        
        # Check that main log has all messages
        with open(log_file, 'r') as f:
            content = f.read()
            self.assertIn("Debug message", content)
            self.assertIn("Info message", content)
            self.assertIn("Error message", content)
            
        # Check that error log only has error messages
        with open(error_log_file, 'r') as f:
            content = f.read()
            self.assertNotIn("Debug message", content)
            self.assertNotIn("Info message", content)
            self.assertIn("Error message", content)
    
    def test_get_logger(self):
        """Test get_logger returns proper module logger."""
        logger = get_logger("test_module")
        self.assertEqual(logger.name, "apple_health_monitor.test_module")
    
    def test_log_levels(self):
        """Test that log levels work correctly."""
        logger = setup_logging(
            log_level="WARNING",
            log_dir=self.temp_dir,
            app_name="test_levels"
        )
        
        # The logger itself should accept all levels
        self.assertEqual(logger.level, logging.WARNING)
        
        # Console handler should be INFO level
        console_handler = next(h for h in logger.handlers if isinstance(h, logging.StreamHandler))
        self.assertEqual(console_handler.level, logging.INFO)
        
        # File handlers should have appropriate levels
        for handler in logger.handlers:
            if isinstance(handler, logging.handlers.RotatingFileHandler):
                if "errors" in str(handler.baseFilename):
                    self.assertEqual(handler.level, logging.ERROR)
                else:
                    self.assertEqual(handler.level, logging.DEBUG)
    
    def tearDown(self):
        """Clean up test environment."""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)


if __name__ == "__main__":
    unittest.main()