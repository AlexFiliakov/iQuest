"""
Comprehensive accessibility management for health visualizations.

Implements WCAG 2.1 AA compliance for all chart components.
"""

from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from PyQt6.QtCore import QObject, pyqtSignal, Qt
from PyQt6.QtWidgets import QWidget
import pandas as pd

from ..charts.wsj_style_manager import WSJStyleManager
from .screen_reader_support import ScreenReaderManager
from .keyboard_navigation import KeyboardNavigationManager
from .color_accessibility import ColorAccessibilityManager
from .alternative_representations import AlternativeRepresentationManager
from .wcag_validator import WCAGValidator, AccessibilityReport
from ...utils.logging_config import get_logger

logger = get_logger(__name__)


@dataclass
class AccessibleChart:
    """Wrapper for charts with accessibility enhancements."""
    
    chart: QWidget
    chart_type: str
    title: str
    description: Optional[str] = None
    data_table: Optional[Any] = None
    keyboard_shortcuts: Optional[Dict[str, str]] = None
    aria_attributes: Optional[Dict[str, Any]] = None
    alternative_representations: Optional[Dict[str, Any]] = None
    
    def get_accessible_title(self) -> str:
        """Get accessible title for the chart."""
        return self.title
    
    def get_description_id(self) -> str:
        """Get ID for description element."""
        return f"{id(self.chart)}_description"
    
    def supports_real_time_updates(self) -> bool:
        """Check if chart supports real-time updates."""
        return hasattr(self.chart, 'real_time_enabled') and self.chart.real_time_enabled
    
    def get_data_summary(self) -> str:
        """Get summary of chart data."""
        if hasattr(self.chart, 'get_data_summary'):
            return self.chart.get_data_summary()
        return "Chart data summary not available"
    
    def get_key_insights(self) -> List[str]:
        """Get key insights from the chart."""
        if hasattr(self.chart, 'get_key_insights'):
            return self.chart.get_key_insights()
        return []


class VisualizationAccessibilityManager(QObject):
    """Comprehensive accessibility management for health visualizations."""
    
    # Signals
    accessibility_enabled = pyqtSignal(str)  # chart_id
    validation_complete = pyqtSignal(str, dict)  # chart_id, results
    
    def __init__(self, theme_manager: WSJStyleManager):
        super().__init__()
        self.theme_manager = theme_manager
        self.screen_reader_manager = ScreenReaderManager()
        self.keyboard_navigation = KeyboardNavigationManager()
        self.color_accessibility = ColorAccessibilityManager()
        self.alternative_representations = AlternativeRepresentationManager()
        self.wcag_validator = WCAGValidator()
        
        # Cache for accessibility configurations
        self._accessibility_cache = {}
        
        logger.info("Initialized VisualizationAccessibilityManager")
    
    def make_chart_accessible(self, chart: QWidget, chart_config: Dict[str, Any]) -> AccessibleChart:
        """Apply comprehensive accessibility features to chart."""
        try:
            # Create accessible chart wrapper
            accessible_chart = AccessibleChart(
                chart=chart,
                chart_type=chart_config.get('type', 'unknown'),
                title=chart_config.get('title', 'Chart')
            )
            
            # Apply accessibility enhancements
            self._enhance_chart_accessibility(accessible_chart)
            
            # Validate accessibility
            report = self.validate_accessibility(accessible_chart)
            
            if not report.is_compliant():
                logger.warning(
                    f"Chart '{accessible_chart.title}' has accessibility issues: "
                    f"{report.get_failure_summary()}"
                )
            
            # Cache configuration
            chart_id = str(id(chart))
            self._accessibility_cache[chart_id] = accessible_chart
            
            # Emit signal
            self.accessibility_enabled.emit(chart_id)
            
            return accessible_chart
            
        except Exception as e:
            logger.error(f"Error making chart accessible: {e}")
            raise
    
    def validate_accessibility(self, chart: AccessibleChart) -> AccessibilityReport:
        """Validate chart accessibility compliance."""
        try:
            report = self.wcag_validator.validate(chart)
            
            # Emit validation results
            self.validation_complete.emit(
                str(id(chart.chart)),
                report.to_dict()
            )
            
            return report
            
        except Exception as e:
            logger.error(f"Error validating accessibility: {e}")
            raise
    
    def _enhance_chart_accessibility(self, chart: AccessibleChart) -> None:
        """Apply comprehensive accessibility enhancements."""
        try:
            # 1. Screen reader support
            self._add_screen_reader_support(chart)
            
            # 2. Keyboard navigation
            self._enable_keyboard_navigation(chart)
            
            # 3. Color accessibility
            self._ensure_color_accessibility(chart)
            
            # 4. Alternative representations
            self._add_alternative_representations(chart)
            
            # 5. ARIA attributes
            self._add_aria_attributes(chart)
            
            logger.debug(f"Enhanced accessibility for chart: {chart.title}")
            
        except Exception as e:
            logger.error(f"Error enhancing chart accessibility: {e}")
            raise
    
    def _add_screen_reader_support(self, chart: AccessibleChart) -> None:
        """Add comprehensive screen reader support."""
        try:
            # Create chart description
            description = self.screen_reader_manager.create_chart_description(
                chart_type=chart.chart_type,
                data_summary=chart.get_data_summary(),
                key_insights=chart.get_key_insights()
            )
            chart.description = description
            
            # Add accessible name and description
            if hasattr(chart.chart, 'setAccessibleName'):
                chart.chart.setAccessibleName(chart.get_accessible_title())
            
            if hasattr(chart.chart, 'setAccessibleDescription'):
                chart.chart.setAccessibleDescription(description)
            
            # Enable announcements for dynamic updates
            if chart.supports_real_time_updates():
                self.screen_reader_manager.enable_live_region(chart.chart)
            
        except Exception as e:
            logger.error(f"Error adding screen reader support: {e}")
            raise
    
    def _enable_keyboard_navigation(self, chart: AccessibleChart) -> None:
        """Enable comprehensive keyboard navigation."""
        try:
            # Configure keyboard shortcuts
            shortcuts = self.keyboard_navigation.get_default_shortcuts()
            chart.keyboard_shortcuts = shortcuts
            
            # Install keyboard handler
            self.keyboard_navigation.install_handler(chart.chart, shortcuts)
            
            # Make chart focusable
            chart.chart.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
            
            # Enable tab navigation
            chart.chart.setTabletTracking(True)
            
        except Exception as e:
            logger.error(f"Error enabling keyboard navigation: {e}")
            raise
    
    def _ensure_color_accessibility(self, chart: AccessibleChart) -> None:
        """Ensure color accessibility for all users."""
        try:
            # Check current color scheme
            if hasattr(chart.chart, 'get_color_scheme'):
                current_colors = chart.chart.get_color_scheme()
                
                # Validate contrast ratios
                issues = self.color_accessibility.check_contrast_issues(current_colors)
                
                if issues:
                    # Apply high contrast colors
                    high_contrast = self.theme_manager.get_high_contrast_palette()
                    if hasattr(chart.chart, 'set_color_scheme'):
                        chart.chart.set_color_scheme(high_contrast)
            
            # Add pattern alternatives
            if hasattr(chart.chart, 'add_pattern_coding'):
                patterns = self.color_accessibility.get_accessibility_patterns()
                chart.chart.add_pattern_coding(patterns)
            
        except Exception as e:
            logger.error(f"Error ensuring color accessibility: {e}")
            raise
    
    def _add_alternative_representations(self, chart: AccessibleChart) -> None:
        """Add alternative representations for chart data."""
        try:
            representations = {}
            
            # 1. Data table
            if hasattr(chart.chart, 'get_data'):
                data = chart.chart.get_data()
                table = self.alternative_representations.create_data_table(
                    data, 
                    chart.title
                )
                representations['data_table'] = table
                chart.data_table = table
            
            # 2. Text summary
            summary = self.alternative_representations.create_text_summary(
                chart_data=chart.get_data_summary(),
                insights=chart.get_key_insights()
            )
            representations['text_summary'] = summary
            
            # 3. Sonification (if applicable)
            if hasattr(chart.chart, 'get_time_series_data'):
                sonification = self.alternative_representations.create_sonification(
                    chart.chart.get_time_series_data()
                )
                representations['sonification'] = sonification
            
            # 4. Haptic feedback (for touch devices)
            if hasattr(chart.chart, 'get_data') or hasattr(chart.chart, 'get_time_series_data'):
                data = (chart.chart.get_time_series_data() 
                       if hasattr(chart.chart, 'get_time_series_data')
                       else chart.chart.get_data())
                if isinstance(data, pd.Series):
                    haptic_patterns = self.alternative_representations.create_haptic_feedback(data)
                    representations['haptic'] = haptic_patterns
            
            chart.alternative_representations = representations
            
        except Exception as e:
            logger.error(f"Error adding alternative representations: {e}")
            raise
    
    def _add_aria_attributes(self, chart: AccessibleChart) -> None:
        """Add comprehensive ARIA attributes."""
        try:
            aria_attrs = {
                'role': 'img',
                'aria-label': chart.get_accessible_title(),
                'aria-describedby': chart.get_description_id()
            }
            
            # Add live region for dynamic charts
            if chart.supports_real_time_updates():
                aria_attrs['aria-live'] = 'polite'
                aria_attrs['aria-atomic'] = 'true'
            
            # Apply attributes
            chart.aria_attributes = aria_attrs
            
            # Set on widget if supported
            if hasattr(chart.chart, 'setProperty'):
                for key, value in aria_attrs.items():
                    chart.chart.setProperty(key, value)
            
        except Exception as e:
            logger.error(f"Error adding ARIA attributes: {e}")
            raise
    
    def get_accessibility_report(self, chart_id: str) -> Optional[AccessibilityReport]:
        """Get accessibility report for a chart."""
        if chart_id in self._accessibility_cache:
            chart = self._accessibility_cache[chart_id]
            return self.validate_accessibility(chart)
        return None
    
    def clear_cache(self) -> None:
        """Clear accessibility configuration cache."""
        self._accessibility_cache.clear()
        logger.debug("Cleared accessibility cache")