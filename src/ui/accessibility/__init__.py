"""
Accessibility compliance system for Apple Health Monitor visualizations.

This module provides comprehensive accessibility features following WCAG 2.1 AA standards.
"""

from .accessibility_manager import (
    VisualizationAccessibilityManager,
    AccessibleChart,
    AccessibilityReport
)
from .wcag_validator import WCAGValidator, TestResult, WCAGLevel
from .screen_reader_support import ScreenReaderManager, HealthDataNarrator
from .keyboard_navigation import KeyboardNavigationManager
from .color_accessibility import ColorAccessibilityManager, ContrastResult
from .alternative_representations import (
    AlternativeRepresentationManager,
    DataSonification,
    AccessibleDataTable
)

__all__ = [
    'VisualizationAccessibilityManager',
    'AccessibleChart',
    'AccessibilityReport',
    'WCAGValidator',
    'TestResult',
    'WCAGLevel',
    'ScreenReaderManager',
    'HealthDataNarrator',
    'KeyboardNavigationManager',
    'ColorAccessibilityManager',
    'ContrastResult',
    'AlternativeRepresentationManager',
    'DataSonification',
    'AccessibleDataTable'
]