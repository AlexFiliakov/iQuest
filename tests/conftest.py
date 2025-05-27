"""
pytest configuration file for test suite
"""

import sys
import os
from pathlib import Path

# Add src directory to Python path for imports
src_path = Path(__file__).parent.parent / "src"
sys.path.insert(0, str(src_path))

def pytest_configure(config):
    """
    Configure pytest with custom markers and settings
    """
    config.addinivalue_line(
        "markers", "slow: marks tests as slow (deselect with '-m \"not slow\"')"
    )
    config.addinivalue_line(
        "markers", "integration: marks tests as integration tests"
    )
    config.addinivalue_line(
        "markers", "ui: marks tests as UI tests"
    )