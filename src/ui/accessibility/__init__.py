"""Comprehensive accessibility compliance system for Apple Health Monitor visualizations.

This module provides extensive accessibility features that ensure the Apple Health Monitor
Dashboard meets and exceeds WCAG 2.1 AA standards, making health data visualization
accessible to users with diverse abilities and assistive technology needs.

The accessibility system includes:

- **WCAG Compliance**: Automated validation and testing for WCAG 2.1 AA standards
- **Screen Reader Support**: Full narration and description of health data visualizations
- **Keyboard Navigation**: Complete keyboard-only navigation throughout the application
- **Color Accessibility**: High contrast themes and colorblind-friendly palettes
- **Alternative Representations**: Data sonification, tactile feedback, and structured tables
- **Assistive Technology Integration**: Compatibility with JAWS, NVDA, and VoiceOver

The system is designed to provide equal access to health insights for all users,
regardless of visual, auditory, motor, or cognitive abilities. All components
follow inclusive design principles and universal accessibility standards.

Features:
- Real-time accessibility validation during chart rendering
- Intelligent data narration with contextual health insights
- Multi-modal data representation (visual, auditory, tactile)
- Customizable accessibility preferences and user profiles
- Automated accessibility testing and compliance reporting

Example:
    Enabling comprehensive accessibility:
    
    >>> from ui.accessibility import VisualizationAccessibilityManager
    >>> accessibility = VisualizationAccessibilityManager()
    >>> accessibility.enable_screen_reader_support()
    >>> accessibility.enable_keyboard_navigation()
    >>> accessibility.set_high_contrast_mode(True)
    
    Validating WCAG compliance:
    
    >>> from ui.accessibility import WCAGValidator
    >>> validator = WCAGValidator()
    >>> report = validator.validate_chart(chart_widget)
    >>> print(f"Compliance Level: {report.compliance_level}")

Note:
    The accessibility system integrates seamlessly with the existing UI components
    and requires no changes to existing chart implementations. All accessibility
    features can be enabled/disabled based on user preferences.
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