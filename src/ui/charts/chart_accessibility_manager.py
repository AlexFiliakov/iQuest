"""Accessibility manager for ensuring WCAG 2.1 AA compliance in charts."""

from typing import Dict, List, Tuple, Optional, Any
from dataclasses import dataclass
import colorsys
from PyQt6.QtGui import QColor
from PyQt6.QtCore import Qt

from ...utils.logging_config import get_logger

logger = get_logger(__name__)


@dataclass
class AccessibilityReport:
    """Report of accessibility compliance for a chart."""
    compliant: bool
    contrast_ratio: float
    issues: List[str]
    suggestions: List[str]
    wcag_level: str  # 'A', 'AA', 'AAA', or 'Fail'


class ColorAccessibility:
    """Color accessibility utilities."""
    
    @staticmethod
    def calculate_contrast_ratio(color1: str, color2: str) -> float:
        """
        Calculate WCAG contrast ratio between two colors.
        
        Args:
            color1: Hex color string (e.g., '#FF8C42')
            color2: Hex color string
            
        Returns:
            Contrast ratio (1-21)
        """
        def get_luminance(color: str) -> float:
            """Calculate relative luminance of a color."""
            # Convert hex to RGB
            color = color.lstrip('#')
            r, g, b = tuple(int(color[i:i+2], 16) / 255.0 for i in (0, 2, 4))
            
            # Apply gamma correction
            def adjust(c):
                return c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4
            
            r, g, b = adjust(r), adjust(g), adjust(b)
            
            # Calculate luminance
            return 0.2126 * r + 0.7152 * g + 0.0722 * b
        
        lum1 = get_luminance(color1)
        lum2 = get_luminance(color2)
        
        # Ensure lum1 is the lighter color
        if lum1 < lum2:
            lum1, lum2 = lum2, lum1
        
        return (lum1 + 0.05) / (lum2 + 0.05)
    
    @staticmethod
    def check_contrast_compliance(foreground: str, background: str, 
                                 text_size: int = 12) -> Tuple[bool, str]:
        """
        Check if color combination meets WCAG standards.
        
        Returns:
            Tuple of (is_compliant, wcag_level)
        """
        ratio = ColorAccessibility.calculate_contrast_ratio(foreground, background)
        
        # WCAG 2.1 standards
        if text_size >= 18 or (text_size >= 14 and text_size < 18):  # Large text
            if ratio >= 3:
                return True, 'AA'
            elif ratio >= 4.5:
                return True, 'AAA'
        else:  # Normal text
            if ratio >= 4.5:
                return True, 'AA'
            elif ratio >= 7:
                return True, 'AAA'
        
        return False, 'Fail'
    
    @staticmethod
    def suggest_accessible_color(original: str, background: str, 
                               min_ratio: float = 4.5) -> str:
        """
        Suggest an accessible alternative to a color.
        
        Args:
            original: Original color hex string
            background: Background color hex string
            min_ratio: Minimum contrast ratio required
            
        Returns:
            Suggested color hex string
        """
        current_ratio = ColorAccessibility.calculate_contrast_ratio(original, background)
        
        if current_ratio >= min_ratio:
            return original
        
        # Convert to HSL for easier manipulation
        original = original.lstrip('#')
        r, g, b = tuple(int(original[i:i+2], 16) / 255.0 for i in (0, 2, 4))
        h, l, s = colorsys.rgb_to_hls(r, g, b)
        
        # Try adjusting lightness
        step = 0.05
        for direction in [1, -1]:
            new_l = l
            while 0 <= new_l <= 1:
                new_l += step * direction
                if 0 <= new_l <= 1:
                    new_r, new_g, new_b = colorsys.hls_to_rgb(h, new_l, s)
                    new_color = f"#{int(new_r*255):02x}{int(new_g*255):02x}{int(new_b*255):02x}"
                    
                    if ColorAccessibility.calculate_contrast_ratio(new_color, background) >= min_ratio:
                        return new_color
        
        # If lightness adjustment doesn't work, try black or white
        white_ratio = ColorAccessibility.calculate_contrast_ratio('#FFFFFF', background)
        black_ratio = ColorAccessibility.calculate_contrast_ratio('#000000', background)
        
        return '#FFFFFF' if white_ratio > black_ratio else '#000000'
    
    @staticmethod
    def get_colorblind_safe_palette(num_colors: int = 5) -> List[str]:
        """
        Get a colorblind-safe color palette.
        
        Based on research by Paul Tol and others.
        """
        palettes = {
            2: ['#EE8866', '#44BB99'],
            3: ['#EE8866', '#EEDD88', '#44BB99'],
            4: ['#EE8866', '#EEDD88', '#77AADD', '#44BB99'],
            5: ['#EE8866', '#EEDD88', '#77AADD', '#44BB99', '#FFAABB'],
            6: ['#EE8866', '#EEDD88', '#77AADD', '#44BB99', '#FFAABB', '#99DDFF'],
            7: ['#EE8866', '#EEDD88', '#77AADD', '#44BB99', '#FFAABB', '#99DDFF', '#BBCC33'],
            8: ['#332288', '#88CCEE', '#44AA99', '#117733', '#999933', '#DDCC77', '#CC6677', '#882255']
        }
        
        if num_colors in palettes:
            return palettes[num_colors]
        elif num_colors < 2:
            return ['#EE8866']
        else:
            # For more colors, cycle through the 8-color palette
            base_palette = palettes[8]
            return [base_palette[i % len(base_palette)] for i in range(num_colors)]


class ChartAccessibilityManager:
    """Manages accessibility features for charts."""
    
    def __init__(self):
        """Initialize accessibility manager."""
        self.color_checker = ColorAccessibility()
        self._aria_templates = self._load_aria_templates()
        self._min_touch_target = 44  # pixels, WCAG 2.1 AA standard
        self._min_contrast_ratio = 4.5  # WCAG AA for normal text
    
    def enhance_config(self, config: Any, theme: Any) -> Any:
        """
        Enhance chart configuration for accessibility.
        
        Args:
            config: Chart configuration object
            theme: Chart theme object
            
        Returns:
            Enhanced configuration
        """
        # Check and fix color contrasts
        if hasattr(theme, 'text_color') and hasattr(theme, 'background_color'):
            is_compliant, _ = self.color_checker.check_contrast_compliance(
                theme.text_color, theme.background_color)
            
            if not is_compliant:
                theme.text_color = self.color_checker.suggest_accessible_color(
                    theme.text_color, theme.background_color)
                logger.warning("Adjusted text color for accessibility compliance")
        
        # Ensure minimum font sizes
        if hasattr(theme, 'label_font_size') and theme.label_font_size < 12:
            theme.label_font_size = 12
            logger.warning("Increased font size to meet accessibility standards")
        
        # Add accessibility label if missing
        if hasattr(config, 'accessibility_label') and not config.accessibility_label:
            config.accessibility_label = self._generate_default_label(config)
        
        return config
    
    def generate_aria_description(self, chart_type: str, data_summary: Dict[str, Any]) -> str:
        """
        Generate ARIA description for screen readers.
        
        Args:
            chart_type: Type of chart (line, bar, scatter, etc.)
            data_summary: Summary statistics of the data
            
        Returns:
            ARIA description string
        """
        template = self._aria_templates.get(chart_type, self._aria_templates['default'])
        
        # Fill in template with data
        description = template.format(
            title=data_summary.get('title', 'Chart'),
            data_points=data_summary.get('data_points', 0),
            min_value=data_summary.get('min_value', 'N/A'),
            max_value=data_summary.get('max_value', 'N/A'),
            average=data_summary.get('average', 'N/A'),
            trend=data_summary.get('trend', 'stable'),
            time_range=data_summary.get('time_range', 'all time')
        )
        
        return description
    
    def create_keyboard_navigation(self, chart_widget) -> Dict[str, Any]:
        """
        Create keyboard navigation handlers for charts.
        
        Returns:
            Dictionary of keyboard shortcuts and their handlers
        """
        navigation = {
            'Tab': 'Navigate to next data point',
            'Shift+Tab': 'Navigate to previous data point',
            'Enter': 'Select/deselect data point',
            'Space': 'Toggle data series visibility',
            'Arrow Keys': 'Pan chart view',
            '+/-': 'Zoom in/out',
            'H': 'Read help information',
            'D': 'Describe current data point',
            'S': 'Summarize visible data',
            'Escape': 'Exit chart interaction'
        }
        
        return navigation
    
    def check_accessibility_compliance(self, chart_config: Any, 
                                     theme: Any) -> AccessibilityReport:
        """
        Check if chart meets accessibility standards.
        
        Returns:
            AccessibilityReport with compliance details
        """
        issues = []
        suggestions = []
        
        # Check color contrasts
        contrast_checks = [
            (theme.text_color, theme.background_color, 'Text'),
            (theme.primary_color, theme.background_color, 'Primary data'),
            (theme.grid_color, theme.background_color, 'Grid lines')
        ]
        
        min_ratio = 21.0
        for fg, bg, element in contrast_checks:
            ratio = self.color_checker.calculate_contrast_ratio(fg, bg)
            min_ratio = min(min_ratio, ratio)
            
            if ratio < self._min_contrast_ratio:
                issues.append(f"{element} contrast ratio ({ratio:.2f}) below WCAG AA standard")
                suggestions.append(f"Increase contrast for {element} to at least 4.5:1")
        
        # Check font sizes
        if hasattr(theme, 'label_font_size') and theme.label_font_size < 12:
            issues.append("Font size below recommended minimum")
            suggestions.append("Use at least 12pt font for labels")
        
        # Check interactive elements
        if hasattr(chart_config, 'point_size'):
            touch_target = chart_config.point_size * 2  # Approximate
            if touch_target < self._min_touch_target:
                issues.append("Interactive elements below minimum touch target size")
                suggestions.append(f"Increase point size to at least {self._min_touch_target/2}px")
        
        # Check for alternative text
        if not hasattr(chart_config, 'accessibility_label') or not chart_config.accessibility_label:
            issues.append("Missing accessibility description")
            suggestions.append("Add descriptive text for screen readers")
        
        # Determine WCAG level
        if not issues:
            wcag_level = 'AA' if min_ratio >= 4.5 else 'A'
        else:
            wcag_level = 'Fail'
        
        return AccessibilityReport(
            compliant=len(issues) == 0,
            contrast_ratio=min_ratio,
            issues=issues,
            suggestions=suggestions,
            wcag_level=wcag_level
        )
    
    def create_high_contrast_theme(self, base_theme: Any) -> Any:
        """Create a high contrast version of a theme."""
        high_contrast_theme = base_theme.__class__()
        
        # Copy base theme
        for attr in dir(base_theme):
            if not attr.startswith('_'):
                setattr(high_contrast_theme, attr, getattr(base_theme, attr))
        
        # Apply high contrast colors
        high_contrast_theme.background_color = '#000000'
        high_contrast_theme.text_color = '#FFFFFF'
        high_contrast_theme.primary_color = '#FFFF00'
        high_contrast_theme.secondary_color = '#00FFFF'
        high_contrast_theme.grid_color = '#666666'
        high_contrast_theme.border_color = '#FFFFFF'
        
        return high_contrast_theme
    
    def add_pattern_overlays(self, colors: List[str]) -> List[Tuple[str, str]]:
        """
        Add pattern overlays to colors for better distinction.
        Useful for colorblind users.
        
        Returns:
            List of (color, pattern) tuples
        """
        patterns = ['solid', 'diagonal', 'horizontal', 'vertical', 'dots', 'cross']
        
        return [(color, patterns[i % len(patterns)]) for i, color in enumerate(colors)]
    
    def generate_sonification_data(self, data_values: List[float]) -> List[int]:
        """
        Convert data values to sound frequencies for audio representation.
        
        Args:
            data_values: List of data values
            
        Returns:
            List of frequencies in Hz
        """
        if not data_values:
            return []
        
        # Map data range to frequency range (200Hz - 2000Hz)
        min_val = min(data_values)
        max_val = max(data_values)
        
        if max_val == min_val:
            return [440] * len(data_values)  # A4 note
        
        frequencies = []
        for value in data_values:
            # Normalize to 0-1
            normalized = (value - min_val) / (max_val - min_val)
            # Map to frequency range
            freq = 200 + (normalized * 1800)
            frequencies.append(int(freq))
        
        return frequencies
    
    def _load_aria_templates(self) -> Dict[str, str]:
        """Load ARIA description templates."""
        return {
            'line': "Line chart titled '{title}' showing {data_points} data points. "
                   "Values range from {min_value} to {max_value} with an average of {average}. "
                   "The overall trend is {trend} over {time_range}.",
            
            'bar': "Bar chart titled '{title}' comparing {data_points} categories. "
                   "The highest value is {max_value} and the lowest is {min_value}. "
                   "Average value across all categories is {average}.",
            
            'scatter': "Scatter plot titled '{title}' displaying {data_points} data points. "
                      "X-axis ranges from {min_x} to {max_x}, Y-axis from {min_y} to {max_y}. "
                      "The correlation appears to be {correlation}.",
            
            'heatmap': "Heat map titled '{title}' showing intensity across {rows} rows and {cols} columns. "
                      "Intensity ranges from {min_value} to {max_value}. "
                      "The highest concentration is in {hot_spot}.",
            
            'default': "Chart titled '{title}' containing {data_points} data points. "
                      "Values range from {min_value} to {max_value}."
        }
    
    def _generate_default_label(self, config: Any) -> str:
        """Generate a default accessibility label."""
        label = "Chart"
        
        if hasattr(config, 'title') and config.title:
            label = f"Chart: {config.title}"
        
        if hasattr(config, 'subtitle') and config.subtitle:
            label += f" - {config.subtitle}"
        
        return label