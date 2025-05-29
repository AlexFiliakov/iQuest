"""
UI package for Apple Health Monitor Dashboard.

This module provides the user interface components for the health monitoring application,
including accessibility features for WCAG 2.1 AA compliance.
"""

from .main_window import MainWindow

# Import accessibility module
from . import accessibility

__all__ = ['MainWindow', 'accessibility']