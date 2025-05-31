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

import pytest
from unittest.mock import Mock, MagicMock