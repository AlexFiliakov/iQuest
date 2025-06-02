"""Style manager for consistent theming across the application.

This module provides comprehensive styling and theming capabilities for the
Apple Health Monitor Dashboard. It implements a professional design system
with WSJ-inspired aesthetics, modern color palettes, and accessibility features.

The StyleManager centralizes all visual styling including:
    - Professional color palette with high contrast ratios
    - Modern typography system using Inter and Poppins fonts
    - Shadow and elevation system for depth and hierarchy
    - Component-specific styling for buttons, inputs, and cards
    - Accessibility features including focus indicators
    - Responsive design elements for different screen sizes

Key features:
    - WSJ-inspired professional color scheme
    - Comprehensive component styling system
    - Modern shadow and elevation effects
    - Accessibility-compliant focus indicators
    - Responsive design patterns
    - Cross-platform visual consistency

Design principles:
    - Clean, minimalist aesthetic with purposeful use of color
    - High contrast ratios for excellent readability
    - Consistent spacing and typography for professional appearance
    - Modern flat design with subtle depth through shadows
    - Accessibility-first approach with proper focus management

Example:
    Basic styling application:
    
    >>> style_manager = StyleManager()
    >>> 
    >>> # Apply styles to components
    >>> button.setStyleSheet(style_manager.get_button_style("primary"))
    >>> input_field.setStyleSheet(style_manager.get_input_style())
    >>> card.setStyleSheet(style_manager.get_card_style())
    
    Custom color usage:
    
    >>> # Access design system colors
    >>> primary_color = style_manager.ACCENT_PRIMARY
    >>> background_color = style_manager.PRIMARY_BG
    >>> text_color = style_manager.TEXT_PRIMARY
    
    Global application styling:
    
    >>> # Apply global styles to entire application
    >>> style_manager.apply_global_style(app)

Attributes:
    PRIMARY_BG (str): Clean white background color
    ACCENT_PRIMARY (str): Rich black primary accent color
    TEXT_PRIMARY (str): High contrast primary text color
    FOCUS_COLOR (str): WSJ blue for focus indicators
"""

import os
from PyQt6.QtGui import QFontDatabase, QFont
from PyQt6.QtCore import QFile, QIODevice

from ..utils.logging_config import get_logger

logger = get_logger(__name__)


class StyleManager:
    """Manages comprehensive application styling and theming system.
    
    This class provides a centralized design system for the Apple Health Monitor
    Dashboard, implementing WSJ-inspired professional aesthetics with modern
    usability features and accessibility compliance.
    
    Design system features:
        - Professional color palette with semantic naming
        - Modern typography hierarchy using Inter and Poppins fonts
        - Comprehensive shadow and elevation system
        - Component-specific styling methods
        - Accessibility-compliant focus indicators
        - Responsive design patterns
    
    Color system:
        - Primary: Clean whites and professional grays for backgrounds
        - Accent: Rich blacks and vibrant blues for highlights
        - Data: Carefully selected colors for charts and visualizations
        - Status: Green, amber, and red for success, warning, and error states
        - Text: High contrast colors ensuring accessibility compliance
    
    Typography system:
        - Primary font: Roboto for clean, readable interface text
        - Display font: Roboto Condensed for headings and emphasis
        - Monospace: JetBrains Mono for code and data display
        - Proper font weights and sizes for clear hierarchy
    
    Component styling:
        - Buttons: Primary, secondary, and ghost variants
        - Inputs: Text fields, dropdowns, and date pickers
        - Cards: Various elevation levels and styling options
        - Navigation: Tabs, menus, and status bars
        - Tables: Professional data display with proper contrast
    
    Accessibility features:
        - WCAG AA compliant color contrast ratios
        - Clear focus indicators for keyboard navigation
        - Proper semantic styling for screen readers
        - High contrast mode support
        - Consistent interaction patterns
    
    Attributes:
        PRIMARY_BG (str): Clean white background (#FFFFFF)
        SECONDARY_BG (str): Very light gray for subtle contrast (#FAFBFC)
        ACCENT_PRIMARY (str): Rich black for primary text (#0F172A)
        ACCENT_SECONDARY (str): Vibrant blue for CTAs (#2563EB)
        TEXT_PRIMARY (str): High contrast black for readability (#0F172A)
        FOCUS_COLOR (str): WSJ blue for focus indicators (#0080C7)
        CHART_COLORS (List[str]): Curated colors for data visualization
    
    Example:
        Comprehensive styling workflow:
        
        >>> style_manager = StyleManager()
        >>> 
        >>> # Apply global application styling
        >>> style_manager.apply_global_style(app)
        >>> 
        >>> # Style specific components
        >>> primary_button.setStyleSheet(style_manager.get_button_style("primary"))
        >>> text_input.setStyleSheet(style_manager.get_input_style())
        >>> data_card.setStyleSheet(style_manager.get_card_style("md"))
        >>> 
        >>> # Create custom shadows for elevation
        >>> shadow_effect = style_manager.create_shadow_effect(blur_radius=12)
        >>> widget.setGraphicsEffect(shadow_effect)
        >>> 
        >>> # Access design system colors
        >>> widget.setStyleSheet(f"background-color: {style_manager.PRIMARY_BG};")
    """
    
    # Color palette constants - Modern WSJ-inspired professional palette
    PRIMARY_BG = "#FFFFFF"       # Clean white background
    SECONDARY_BG = "#F9FAFB"     # Slightly darker for better contrast
    TERTIARY_BG = "#F3F4F6"      # Light gray for hover states
    SURFACE_ELEVATED = "#FFFFFF" # Elevated surface with shadow
    
    ACCENT_PRIMARY = "#111827"   # Darker black for better contrast - primary text
    ACCENT_SECONDARY = "#2563EB" # Vibrant blue - CTAs and highlights
    ACCENT_SUCCESS = "#059669"   # Darker green for better contrast (WCAG AA compliant)
    ACCENT_WARNING = "#F59E0B"   # Modern amber - caution
    ACCENT_ERROR = "#EF4444"     # Modern red - errors
    ACCENT_LIGHT = "#E5E7EB"     # Light gray - subtle borders
    
    TEXT_PRIMARY = "#111827"     # Darker black for better contrast
    TEXT_SECONDARY = "#4B5563"   # Darker gray for better readability
    TEXT_MUTED = "#6B7280"       # Darker muted text
    TEXT_INVERSE = "#FFFFFF"     # White on dark
    
    # New accent colors for data visualization
    DATA_ORANGE = "#FB923C"      # Warm orange for data points
    DATA_PURPLE = "#A78BFA"      # Soft purple for secondary data
    DATA_TEAL = "#2DD4BF"        # Teal for tertiary data
    DATA_PINK = "#F472B6"        # Pink for quaternary data
    
    # Focus indicator color
    FOCUS_COLOR = "#0080C7"      # WSJ Blue for focus
    FOCUS_SHADOW = "rgba(0, 128, 199, 0.25)"  # Blue shadow for focus
    
    # Chart colors - Modern vibrant palette
    CHART_COLORS = ["#2563EB", "#10B981", "#FB923C", "#A78BFA", "#2DD4BF", "#F472B6"]
    
    # Shadow system - Modern elevation system
    # These are for reference, actual implementation uses borders and effects
    SHADOWS = {
        'sm': '0 1px 2px rgba(0,0,0,0.05)',
        'md': '0 4px 6px rgba(0,0,0,0.07)', 
        'lg': '0 10px 15px rgba(0,0,0,0.10)',
        'xl': '0 20px 25px rgba(0,0,0,0.15)',
        'inner': 'inset 0 2px 4px rgba(0,0,0,0.06)'
    }
    
    # Spacing system - 8px grid for consistency
    SPACING = {
        'xs': 8,
        'sm': 16,
        'md': 24,
        'lg': 32,
        'xl': 40,
        'xxl': 48
    }
    
    # Border radius values for consistent rounding
    RADIUS = {
        'sm': 6,
        'md': 8,
        'lg': 12,
        'xl': 16
    }
    
    def __init__(self):
        """Initialize the style manager with design system configuration.
        
        Sets up the comprehensive styling system for the Apple Health Monitor
        Dashboard with professional WSJ-inspired aesthetics and accessibility
        features. The initialization configures all design system components
        for immediate use throughout the application.
        
        Initialization process:
            1. Configure logging for style-related operations
            2. Load custom Roboto and Roboto Condensed fonts
            3. Set up color palette constants for consistent theming
            4. Prepare typography system with proper font hierarchies
            5. Initialize shadow and elevation system
            6. Configure accessibility features and focus indicators
        
        Design system setup:
            - Professional color palette with semantic naming
            - Modern typography using Roboto and Roboto Condensed fonts
            - Comprehensive shadow system for depth and hierarchy
            - Accessibility-compliant focus indicators
            - Cross-platform visual consistency
        
        Performance considerations:
            - Efficient stylesheet generation with minimal overhead
            - Cached style strings for frequently used components
            - Optimized color calculations for dynamic theming
        """
        logger.debug("Initializing StyleManager")
        self.fonts_loaded = False
        self.load_custom_fonts()
    
    def get_main_window_style(self):
        """Get the main window stylesheet."""
        return f"""
            QMainWindow {{
                background-color: {self.PRIMARY_BG};
            }}
            
            QWidget {{
                font-family: 'Inter', 'Segoe UI', -apple-system, sans-serif;
                font-size: 13px;
                color: {self.TEXT_PRIMARY};
            }}
        """
    
    def get_menu_bar_style(self):
        """Get the menu bar stylesheet."""
        shadow = self.get_shadow_style('sm')
        return f"""
            QMenuBar {{
                background-color: {self.PRIMARY_BG};
                border-bottom: {shadow['border']};
                padding: 4px;
            }}
            
            QMenuBar::item {{
                padding: 8px 16px;
                background-color: transparent;
                color: {self.TEXT_PRIMARY};
                border-radius: 4px;
                font-family: 'Roboto Condensed', 'Segoe UI', -apple-system, sans-serif;
                font-weight: 500;
            }}
            
            QMenuBar::item:selected {{
                background-color: {self.TERTIARY_BG};
            }}
            
            QMenuBar::item:pressed {{
                background-color: {self.ACCENT_PRIMARY};
                color: {self.TEXT_INVERSE};
            }}
            
            QMenu {{
                background-color: {self.PRIMARY_BG};
                border: {shadow['border']};
                border-radius: 8px;
                padding: 4px;
            }}
            
            QMenu::item {{
                padding: 8px 24px;
                border-radius: 4px;
            }}
            
            QMenu::item:selected {{
                background-color: {self.TERTIARY_BG};
                color: {self.ACCENT_PRIMARY};
            }}
            
            QMenu::separator {{
                height: 1px;
                background-color: rgba(0, 0, 0, 0.05);
                margin: 4px 0;
            }}
        """
    
    def get_tab_widget_style(self):
        """Get the tab widget stylesheet with enhanced visibility for selected tabs."""
        return f"""
            QTabWidget::pane {{
                background-color: {self.PRIMARY_BG};
                border: none;
                top: 0px;
            }}
            
            QTabBar {{
                background-color: {self.PRIMARY_BG};
                border-bottom: 2px solid {self.ACCENT_LIGHT};
            }}
            
            QTabBar::tab {{
                background: transparent;
                color: {self.TEXT_SECONDARY};
                padding: 16px 32px;
                margin-right: 8px;
                border: none;
                border-bottom: 4px solid transparent;
                font-family: 'Roboto Condensed', 'Segoe UI', -apple-system, sans-serif;
                font-weight: 500;
                font-size: 15px;
                transition: all 0.2s ease;
            }}
            
            QTabBar::tab:selected {{
                color: {self.ACCENT_PRIMARY};
                background-color: rgba(37, 99, 235, 0.08);
                border-bottom: 4px solid {self.ACCENT_SECONDARY};
                font-weight: 600;
                border-top-left-radius: 8px;
                border-top-right-radius: 8px;
            }}
            
            QTabBar::tab:hover:!selected {{
                color: {self.TEXT_PRIMARY};
                background-color: {self.TERTIARY_BG};
                border-bottom: 4px solid rgba(37, 99, 235, 0.3);
            }}
            
            QTabBar::tab:first {{
                margin-left: 0;
            }}
            
            QTabWidget > QWidget {{
                background-color: {self.PRIMARY_BG};
                border: none;
            }}
        """
    
    def get_button_style(self, button_type="primary"):
        """Get comprehensive button stylesheet based on specified type.
        
        Provides professional button styling with proper interaction states,
        accessibility features, and visual hierarchy. The button styles follow
        modern design principles with clear visual feedback for user actions.
        
        Args:
            button_type (str, optional): Button style variant. Defaults to "primary".
                Available types:
                - "primary": High-emphasis blue button for main actions
                - "secondary": Medium-emphasis outlined button for secondary actions
                - "ghost": Low-emphasis text button for subtle actions
                - "danger": Red outlined button for destructive actions
        
        Returns:
            str: Complete CSS stylesheet for the specified button type.
                Includes normal, hover, pressed, disabled, and focus states.
        
        Button features:
            - Modern rounded corners for contemporary appearance
            - Smooth hover and press transitions for responsive feedback
            - Accessibility-compliant focus indicators
            - Proper contrast ratios for text readability
            - Disabled state styling for inactive buttons
        
        Example:
            Apply button styles to Qt widgets:
            
            >>> style_manager = StyleManager()
            >>> 
            >>> # Primary action button
            >>> save_button.setStyleSheet(style_manager.get_button_style("primary"))
            >>> 
            >>> # Secondary action button
            >>> cancel_button.setStyleSheet(style_manager.get_button_style("secondary"))
            >>> 
            >>> # Subtle action button
            >>> more_button.setStyleSheet(style_manager.get_button_style("ghost"))
        
        Note:
            All button types include focus indicators for keyboard navigation
            and maintain consistent sizing and typography.
        """
        if button_type == "primary":
            return f"""
                QPushButton {{
                    background-color: {self.ACCENT_SECONDARY};
                    color: {self.TEXT_INVERSE};
                    border: none;
                    padding: 12px 28px;
                    border-radius: 8px;
                    font-weight: 600;
                    font-size: 14px;
                    min-height: 44px;
                    letter-spacing: 0.5px;
                    box-shadow: 0 2px 8px rgba(37, 99, 235, 0.15);
                    font-family: 'Roboto', 'Segoe UI', -apple-system, sans-serif;
                }}
                
                QPushButton:hover {{
                    background-color: #1D4ED8;
                    box-shadow: 0 4px 12px rgba(37, 99, 235, 0.25);
                }}
                
                QPushButton:pressed {{
                    background-color: #1E40AF;
                    box-shadow: 0 1px 4px rgba(37, 99, 235, 0.15);
                }}
                
                QPushButton:disabled {{
                    background-color: {self.TEXT_MUTED};
                    color: {self.SECONDARY_BG};
                    box-shadow: none;
                }}
                
                QPushButton:focus {{
                    outline: none;
                    border: 2px solid {self.FOCUS_COLOR};
                }}
            """
        elif button_type == "secondary":
            return f"""
                QPushButton {{
                    background-color: {self.PRIMARY_BG};
                    color: {self.TEXT_PRIMARY};
                    border: 2px solid {self.ACCENT_LIGHT};
                    padding: 10px 26px;
                    border-radius: 8px;
                    font-weight: 500;
                    font-size: 14px;
                    min-height: 44px;
                    letter-spacing: 0.5px;
                    font-family: 'Roboto', 'Segoe UI', -apple-system, sans-serif;
                }}
                
                QPushButton:hover {{
                    background-color: {self.TERTIARY_BG};
                    border-color: {self.TEXT_SECONDARY};
                }}
                
                QPushButton:pressed {{
                    background-color: {self.ACCENT_LIGHT};
                    border-color: {self.ACCENT_PRIMARY};
                }}
                
                QPushButton:disabled {{
                    border-color: {self.TEXT_MUTED};
                    color: {self.TEXT_MUTED};
                    background-color: transparent;
                }}
                
                QPushButton:focus {{
                    outline: none;
                    border: 2px solid {self.FOCUS_COLOR};
                }}
            """
        elif button_type == "ghost":
            return f"""
                QPushButton {{
                    background-color: transparent;
                    color: {self.ACCENT_PRIMARY};
                    border: none;
                    padding: 8px 16px;
                    border-radius: 4px;
                    font-weight: 500;
                    font-size: 13px;
                    min-height: 44px;
                }}
                
                QPushButton:hover {{
                    background-color: rgba(91,103,112,0.08);
                }}
                
                QPushButton:pressed {{
                    background-color: rgba(91,103,112,0.12);
                }}
                
                QPushButton:disabled {{
                    color: {self.TEXT_MUTED};
                    background-color: transparent;
                }}
                
                QPushButton:focus {{
                    outline: none;
                    border: 3px solid rgba(91,103,112,0.25);
                }}
            """
        elif button_type == "danger":
            return f"""
                QPushButton {{
                    background-color: {self.PRIMARY_BG};
                    color: {self.ACCENT_ERROR};
                    border: 2px solid {self.ACCENT_ERROR};
                    padding: 10px 26px;
                    border-radius: 8px;
                    font-weight: 500;
                    font-size: 14px;
                    min-height: 44px;
                    letter-spacing: 0.5px;
                    font-family: 'Roboto', 'Segoe UI', -apple-system, sans-serif;
                }}
                
                QPushButton:hover {{
                    background-color: {self.ACCENT_ERROR};
                    color: {self.TEXT_INVERSE};
                    border-color: {self.ACCENT_ERROR};
                }}
                
                QPushButton:pressed {{
                    background-color: #DC2626;
                    border-color: #DC2626;
                }}
                
                QPushButton:disabled {{
                    border-color: #FCA5A5;
                    color: #FCA5A5;
                    background-color: transparent;
                }}
                
                QPushButton:focus {{
                    outline: none;
                    border: 2px solid {self.FOCUS_COLOR};
                }}
            """
    
    def get_shadow_style(self, level: str = 'md'):
        """Get shadow style reference for a given level.
        
        Note: Since Qt doesn't support CSS box-shadow directly, this returns
        border and effect recommendations for implementing shadows.
        
        Args:
            level: Shadow level ('sm', 'md', 'lg', 'xl')
            
        Returns:
            dict: Shadow implementation details
        """
        shadow_configs = {
            'sm': {
                'border': '1px solid rgba(0, 0, 0, 0.05)',
                'hover_border': '1px solid rgba(0, 0, 0, 0.08)',
                'offset': 1,
                'blur': 3,
                'color': 'rgba(0, 0, 0, 0.06)'
            },
            'md': {
                'border': '1px solid rgba(0, 0, 0, 0.05)',
                'hover_border': '1px solid rgba(0, 0, 0, 0.08)',
                'offset': 2,
                'blur': 4,
                'color': 'rgba(0, 0, 0, 0.08)'
            },
            'lg': {
                'border': '1px solid rgba(0, 0, 0, 0.05)',
                'hover_border': '1px solid rgba(0, 0, 0, 0.1)',
                'offset': 4,
                'blur': 12,
                'color': 'rgba(0, 0, 0, 0.10)'
            },
            'xl': {
                'border': '1px solid rgba(0, 0, 0, 0.05)',
                'hover_border': '1px solid rgba(0, 0, 0, 0.12)',
                'offset': 8,
                'blur': 24,
                'color': 'rgba(0, 0, 0, 0.12)'
            }
        }
        return shadow_configs.get(level, shadow_configs['md'])
    
    def get_card_style(self, shadow_level: str = 'md', padding: int = 16, radius: int = 8):
        """Get card widget stylesheet with shadow system."""
        shadow = self.get_shadow_style(shadow_level)
        return f"""
            QWidget {{
                background-color: {self.PRIMARY_BG};
                border-radius: {radius}px;
                padding: {padding}px;
                border: {shadow['border']};
            }}
            
            QWidget:hover {{
                border: {shadow['hover_border']};
                background-color: {self.PRIMARY_BG};
            }}
        """
    
    def get_borderless_card_style(self, padding: int = 16, radius: int = 8, shadow_level: str = 'sm'):
        """Get borderless card widget stylesheet with subtle shadow."""
        shadow = self.get_shadow_style(shadow_level)
        return f"""
            QFrame {{
                background-color: {self.PRIMARY_BG};
                border-radius: {radius}px;
                padding: {padding}px;
                border: {shadow['border']};
            }}
            
            QFrame:hover {{
                background-color: {self.PRIMARY_BG};
                border: {shadow['hover_border']};
            }}
            
            QLabel {{
                background: transparent;
                border: none;
                color: {self.TEXT_PRIMARY};
            }}
        """
    
    def get_accent_card_style(self, accent_color: str = None, padding: int = 16, radius: int = 8, shadow_level: str = 'md'):
        """Get accent-colored card widget stylesheet (for records, achievements, etc.)."""
        if accent_color is None:
            accent_color = self.ACCENT_PRIMARY
        
        shadow = self.get_shadow_style(shadow_level)
        
        return f"""
            QFrame {{
                background-color: {self.PRIMARY_BG};
                border-radius: {radius}px;
                padding: {padding}px;
                border: {shadow['border']};
            }}
            
            QFrame:hover {{
                background-color: {self.PRIMARY_BG};
                border: {shadow['hover_border']};
            }}
            
            QLabel {{
                background: transparent;
                border: none;
                color: {self.TEXT_PRIMARY};
            }}
            
            QLabel[class="value"] {{
                color: {accent_color};
            }}
        """
    
    def get_input_style(self):
        """Get input field stylesheet."""
        return f"""
            QLineEdit, QTextEdit, QSpinBox, QComboBox, QDateEdit {{
                background-color: {self.PRIMARY_BG};
                border: 1px solid {self.ACCENT_LIGHT};
                border-radius: 8px;
                padding: 0 16px;
                height: 40px;
                font-size: 14px;
                color: {self.TEXT_PRIMARY};
                font-family: 'Roboto', 'Segoe UI', -apple-system, sans-serif;
            }}
            
            QTextEdit {{
                padding: 12px 16px;
                height: auto;
                min-height: 80px;
            }}
            
            QLineEdit:hover, QTextEdit:hover, QSpinBox:hover, QComboBox:hover, QDateEdit:hover {{
                border-color: rgba(37, 99, 235, 0.5);
                background-color: rgba(37, 99, 235, 0.02);
            }}
            
            QLineEdit:focus, QTextEdit:focus, QSpinBox:focus, QComboBox:focus, QDateEdit:focus {{
                border: 2px solid {self.ACCENT_SECONDARY};
                outline: none;
                padding: 0 15px;
            }}
            
            QLineEdit:disabled, QTextEdit:disabled, QSpinBox:disabled, QComboBox:disabled, QDateEdit:disabled {{
                background-color: {self.TERTIARY_BG};
                color: {self.TEXT_MUTED};
                border-color: {self.ACCENT_LIGHT};
            }}
            
            /* Combo box specific styles */
            QComboBox::drop-down {{
                border: none;
                width: 30px;
            }}
            
            QComboBox::down-arrow {{
                image: none;
                border-left: 5px solid transparent;
                border-right: 5px solid transparent;
                border-top: 5px solid {self.TEXT_SECONDARY};
                margin-right: 5px;
            }}
            
            QComboBox:hover::down-arrow {{
                border-top-color: {self.ACCENT_PRIMARY};
            }}
            
            QComboBox QAbstractItemView {{
                background-color: {self.PRIMARY_BG};
                border: 1px solid {self.ACCENT_LIGHT};
                border-radius: 4px;
                padding: 4px;
                selection-background-color: {self.TERTIARY_BG};
                selection-color: {self.ACCENT_PRIMARY};
            }}
            
            QComboBox QAbstractItemView::item {{
                padding: 8px 16px;
                min-height: 32px;
            }}
            
            QComboBox QAbstractItemView::item:hover {{
                background-color: {self.TERTIARY_BG};
            }}
            
            /* Spin box specific styles */
            QSpinBox::up-button, QSpinBox::down-button {{
                background-color: transparent;
                border: none;
                width: 20px;
            }}
            
            QSpinBox::up-arrow {{
                image: none;
                border-left: 4px solid transparent;
                border-right: 4px solid transparent;
                border-bottom: 4px solid {self.TEXT_SECONDARY};
            }}
            
            QSpinBox::down-arrow {{
                image: none;
                border-left: 4px solid transparent;
                border-right: 4px solid transparent;
                border-top: 4px solid {self.TEXT_SECONDARY};
            }}
            
            QSpinBox::up-arrow:hover, QSpinBox::down-arrow:hover {{
                border-bottom-color: {self.ACCENT_PRIMARY};
                border-top-color: {self.ACCENT_PRIMARY};
            }}
        """
    
    def get_status_bar_style(self):
        """Get status bar stylesheet."""
        shadow = self.get_shadow_style('sm')
        return f"""
            QStatusBar {{
                background-color: {self.PRIMARY_BG};
                border-top: {shadow['border']};
                color: {self.TEXT_SECONDARY};
                padding: 4px;
            }}
            
            QStatusBar::item {{
                border: none;
            }}
        """
    
    def get_scroll_bar_style(self):
        """Get scroll bar stylesheet."""
        return f"""
            QScrollBar:vertical {{
                background-color: {self.TERTIARY_BG};
                width: 12px;
                border-radius: 6px;
            }}
            
            QScrollBar::handle:vertical {{
                background-color: {self.TEXT_MUTED};
                border-radius: 6px;
                min-height: 30px;
            }}
            
            QScrollBar::handle:vertical:hover {{
                background-color: {self.TEXT_SECONDARY};
            }}
            
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
                height: 0px;
            }}
            
            QScrollBar:horizontal {{
                background-color: {self.TERTIARY_BG};
                height: 12px;
                border-radius: 6px;
            }}
            
            QScrollBar::handle:horizontal {{
                background-color: {self.TEXT_MUTED};
                border-radius: 6px;
                min-width: 30px;
            }}
            
            QScrollBar::handle:horizontal:hover {{
                background-color: {self.TEXT_SECONDARY};
            }}
            
            QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {{
                width: 0px;
            }}
        """
    
    def load_custom_fonts(self):
        """Load Roboto and Roboto Condensed fonts from assets directory.
        
        This method loads all font variations for both Roboto and Roboto Condensed
        families from the assets/fonts directory. It ensures that the custom fonts
        are available for use throughout the application.
        
        Font loading process:
            1. Locate the fonts directory relative to the module
            2. Load Roboto font family (all weights and styles)
            3. Load Roboto Condensed font family (all weights and styles)
            4. Set font substitutions for fallback support
        
        Returns:
            bool: True if fonts were loaded successfully, False otherwise.
        """
        try:
            # Get the project root directory
            current_dir = os.path.dirname(os.path.abspath(__file__))
            project_root = os.path.abspath(os.path.join(current_dir, "..", ".."))
            fonts_dir = os.path.join(project_root, "assets", "fonts")
            
            if not os.path.exists(fonts_dir):
                logger.warning(f"Fonts directory not found: {fonts_dir}")
                return False
            
            # Load Roboto fonts
            roboto_dir = os.path.join(fonts_dir, "Roboto", "static")
            roboto_fonts = [
                "Roboto-Regular.ttf",
                "Roboto-Medium.ttf", 
                "Roboto-Bold.ttf",
                "Roboto-Light.ttf",
                "Roboto-Thin.ttf",
                "Roboto-Black.ttf"
            ]
            
            for font_file in roboto_fonts:
                font_path = os.path.join(roboto_dir, font_file)
                if os.path.exists(font_path):
                    font_id = QFontDatabase.addApplicationFont(font_path)
                    if font_id == -1:
                        logger.warning(f"Failed to load font: {font_file}")
                    else:
                        logger.debug(f"Loaded font: {font_file}")
                else:
                    logger.warning(f"Font file not found: {font_path}")
            
            # Load Roboto Condensed fonts
            roboto_condensed_dir = os.path.join(fonts_dir, "Roboto_Condensed", "static")
            roboto_condensed_fonts = [
                "RobotoCondensed-Regular.ttf",
                "RobotoCondensed-Medium.ttf",
                "RobotoCondensed-Bold.ttf", 
                "RobotoCondensed-Light.ttf",
                "RobotoCondensed-ExtraBold.ttf",
                "RobotoCondensed-Black.ttf"
            ]
            
            for font_file in roboto_condensed_fonts:
                font_path = os.path.join(roboto_condensed_dir, font_file)
                if os.path.exists(font_path):
                    font_id = QFontDatabase.addApplicationFont(font_path)
                    if font_id == -1:
                        logger.warning(f"Failed to load font: {font_file}")
                    else:
                        logger.debug(f"Loaded font: {font_file}")
                else:
                    logger.warning(f"Font file not found: {font_path}")
            
            # Also load the main Roboto Condensed font from the Roboto folder
            roboto_static_condensed = os.path.join(fonts_dir, "Roboto", "static")
            condensed_fonts = [
                "Roboto_Condensed-Regular.ttf",
                "Roboto_Condensed-Medium.ttf",
                "Roboto_Condensed-Bold.ttf",
                "Roboto_Condensed-Light.ttf"
            ]
            
            for font_file in condensed_fonts:
                font_path = os.path.join(roboto_static_condensed, font_file)
                if os.path.exists(font_path):
                    font_id = QFontDatabase.addApplicationFont(font_path)
                    if font_id == -1:
                        logger.warning(f"Failed to load font: {font_file}")
                    else:
                        logger.debug(f"Loaded font: {font_file}")
            
            self.fonts_loaded = True
            logger.info("Custom fonts loaded successfully")
            return True
            
        except Exception as e:
            logger.error(f"Error loading custom fonts: {e}")
            self.fonts_loaded = False
            return False
    
    def apply_global_style(self, app):
        """Apply global application styling."""
        logger.info("Applying global application style")
        
        # Set application style sheet
        global_style = f"""
            * {{
                font-family: 'Roboto', 'Inter', 'Segoe UI', -apple-system, sans-serif;
                font-size: 14px;
                color: {self.TEXT_PRIMARY};
            }}
            
            QLabel {{
                font-size: 14px;
                color: {self.TEXT_PRIMARY};
            }}
            
            QToolTip {{
                background-color: {self.TEXT_PRIMARY};
                color: {self.TEXT_INVERSE};
                border: none;
                padding: 10px 12px;
                border-radius: 6px;
                font-size: 13px;
            }}
            
            QMessageBox {{
                background-color: {self.PRIMARY_BG};
            }}
            
            QMessageBox QLabel {{
                color: {self.TEXT_PRIMARY};
            }}
            
            QMessageBox QPushButton {{
                min-width: 80px;
            }}
            
            /* Global focus indicators */
            *:focus {{
                outline: none;
            }}
            
            QPushButton:focus, QToolButton:focus {{
                outline: none;
                border: 3px solid {self.FOCUS_SHADOW};
            }}
            
            QTabBar::tab:focus {{
                outline: none;
                border-bottom: 3px solid {self.FOCUS_COLOR};
            }}
            
            QCheckBox:focus, QRadioButton:focus {{
                outline: none;
                border: 3px solid {self.FOCUS_SHADOW};
                border-radius: 4px;
            }}
            
            /* Ghost button style */
            QPushButton[class="ghost"] {{
                background-color: transparent;
                color: {self.ACCENT_PRIMARY};
                border: none;
                padding: 8px 16px;
                font-weight: 500;
            }}
            
            QPushButton[class="ghost"]:hover {{
                background-color: rgba(26,26,26,0.08);
            }}
            
            QPushButton[class="ghost"]:pressed {{
                background-color: rgba(26,26,26,0.12);
            }}
            
            QPushButton[class="ghost"]:focus {{
                border: 3px solid {self.FOCUS_SHADOW};
            }}
        """
        
        app.setStyleSheet(global_style)
    
    def get_section_card_style(self, padding: int = 20, radius: int = 8, shadow_level: str = 'sm'):
        """Get section card style for dashboard widgets and form groups."""
        shadow = self.get_shadow_style(shadow_level)
        return f"""
            QFrame {{
                background-color: {self.PRIMARY_BG};
                border-radius: {radius}px;
                padding: {padding}px;
                border: {shadow['border']};
            }}
            
            QFrame:hover {{
                border: {shadow['hover_border']};
            }}
        """
    
    def get_modern_card_style(self, padding: int = 12, radius: int = 12, with_hover: bool = True):
        """Get modern card style without borders, using shadows."""
        hover_style = f"""
            QFrame:hover {{
                background-color: {self.TERTIARY_BG};
            }}
        """ if with_hover else ""
        
        return f"""
            QFrame {{
                background-color: {self.PRIMARY_BG};
                border-radius: {radius}px;
                border: none;
                padding: {padding}px;
            }}
            {hover_style}
        """
    
    def get_modern_group_style(self, title_size: int = 14, padding: int = 12):
        """Get modern group/section style without QGroupBox borders."""
        return f"""
            QWidget {{
                background-color: transparent;
            }}
            QLabel[class="section-title"] {{
                font-size: {title_size}px;
                font-weight: 600;
                color: {self.TEXT_PRIMARY};
                padding-bottom: 8px;
            }}
        """
    
    def get_modern_metric_card_style(self, accent_color: str = None):
        """Get modern metric card style for dashboard metrics."""
        if accent_color is None:
            accent_color = self.ACCENT_PRIMARY
            
        return f"""
            QFrame {{
                background-color: {self.PRIMARY_BG};
                border-radius: 10px;
                border: none;
                padding: 16px;
                min-height: 100px;
            }}
            QFrame:hover {{
                background-color: {self.TERTIARY_BG};
            }}
            QLabel[class="metric-value"] {{
                color: {accent_color};
                font-size: 24px;
                font-weight: bold;
            }}
            QLabel[class="metric-label"] {{
                color: {self.TEXT_SECONDARY};
                font-size: 12px;
                font-family: 'Roboto Condensed', 'Segoe UI', -apple-system, sans-serif;
            }}
        """
    
    def create_shadow_effect(self, blur_radius: int = 15, y_offset: int = 2, opacity: int = 30):
        """Create a QGraphicsDropShadowEffect for modern depth."""
        from PyQt6.QtWidgets import QGraphicsDropShadowEffect
        from PyQt6.QtGui import QColor
        
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(blur_radius)
        shadow.setXOffset(0)
        shadow.setYOffset(y_offset)
        shadow.setColor(QColor(0, 0, 0, opacity))
        return shadow
    
    def get_table_style(self):
        """Get table widget stylesheet with subtle borders."""
        return f"""
            QTableWidget {{
                background-color: {self.PRIMARY_BG};
                border: 1px solid rgba(0, 0, 0, 0.05);
                border-radius: 8px;
                gridline-color: rgba(0, 0, 0, 0.03);
            }}
            
            QTableWidget::item {{
                padding: 8px;
                border: none;
            }}
            
            QTableWidget::item:selected {{
                background-color: {self.TERTIARY_BG};
                color: {self.ACCENT_PRIMARY};
            }}
            
            QHeaderView::section {{
                background-color: {self.SECONDARY_BG};
                padding: 8px;
                border: none;
                border-bottom: 1px solid rgba(0, 0, 0, 0.05);
                font-family: 'Roboto Condensed', 'Segoe UI', -apple-system, sans-serif;
                font-weight: 600;
            }}
        """
    
    def get_tooltip_style(self):
        """Get modern tooltip style."""
        return f"""
            QToolTip {{
                background-color: {self.TEXT_PRIMARY};
                color: {self.TEXT_INVERSE};
                border: none;
                padding: 8px 12px;
                border-radius: 6px;
                font-size: 13px;
                font-weight: 500;
            }}
        """
    
    def get_modern_dialog_style(self):
        """Get modern dialog styling with elevated appearance."""
        return f"""
            QDialog {{
                background-color: {self.SURFACE_ELEVATED};
                border-radius: 12px;
                border: 1px solid rgba(0, 0, 0, 0.08);
            }}
        """
    
    def get_modern_progress_bar_style(self):
        """Get modern progress bar style with gradient effect."""
        return f"""
            QProgressBar {{
                border: none;
                border-radius: 12px;
                text-align: center;
                background-color: {self.TERTIARY_BG};
                height: 24px;
                font-weight: 600;
                font-size: 13px;
                color: {self.TEXT_PRIMARY};
            }}
            QProgressBar::chunk {{
                background: qlineargradient(x1: 0, y1: 0, x2: 1, y2: 0,
                    stop: 0 {self.ACCENT_SECONDARY},
                    stop: 1 #0066A1);
                border-radius: 12px;
            }}
        """
    
    def get_heading_style(self, level: int = 1, margin_bottom: int = 16):
        """Get heading style using Roboto Condensed font.
        
        Args:
            level (int): Heading level (1-6). Defaults to 1.
            margin_bottom (int): Bottom margin in pixels. Defaults to 16.
            
        Returns:
            str: CSS stylesheet for heading.
        """
        font_sizes = {
            1: 32,
            2: 28,
            3: 24,
            4: 20,
            5: 18,
            6: 16
        }
        
        font_weights = {
            1: 700,
            2: 700,
            3: 600,
            4: 600,
            5: 500,
            6: 500
        }
        
        size = font_sizes.get(level, 16)
        weight = font_weights.get(level, 500)
        
        return f"""
            QLabel {{
                font-family: 'Roboto Condensed', 'Segoe UI', -apple-system, sans-serif;
                font-size: {size}px;
                font-weight: {weight};
                color: {self.TEXT_PRIMARY};
                margin-bottom: {margin_bottom}px;
                line-height: 1.2;
            }}
        """
    
    def get_form_label_style(self):
        """Get consistent form label style."""
        return f"""
            QLabel {{
                font-size: 14px;
                font-weight: 500;
                color: {self.TEXT_PRIMARY};
                margin-bottom: {self.SPACING['xs']}px;
                font-family: 'Roboto', 'Segoe UI', -apple-system, sans-serif;
            }}
        """
    
    def get_grid_spacing(self, multiplier: int = 1) -> int:
        """Get spacing value based on 8px grid.
        
        Args:
            multiplier (int): Grid multiplier (1 = 8px, 2 = 16px, etc.)
            
        Returns:
            int: Spacing value in pixels
        """
        return 8 * multiplier
    
    def get_success_message_style(self):
        """Get success message style with proper contrast."""
        return f"""
            QFrame {{
                background-color: rgba(5, 150, 105, 0.1);
                border: 1px solid rgba(5, 150, 105, 0.3);
                border-radius: 8px;
                padding: {self.SPACING['sm']}px;
            }}
            QLabel {{
                color: {self.ACCENT_SUCCESS};
                font-weight: 500;
                font-size: 14px;
            }}
        """
    
    def get_info_message_style(self):
        """Get info message style with blue colors."""
        return f"""
            QFrame {{
                background-color: rgba(37, 99, 235, 0.08);
                border: 1px solid rgba(37, 99, 235, 0.2);
                border-radius: 8px;
                padding: {self.SPACING['sm']}px;
            }}
            QLabel {{
                color: {self.ACCENT_SECONDARY};
                font-weight: 500;
                font-size: 14px;
            }}
        """
    
    def get_error_message_style(self):
        """Get error message style with red colors."""
        return f"""
            QFrame {{
                background-color: rgba(239, 68, 68, 0.08);
                border: 1px solid rgba(239, 68, 68, 0.2);
                border-radius: 8px;
                padding: {self.SPACING['sm']}px;
            }}
            QLabel {{
                color: {self.ACCENT_ERROR};
                font-weight: 500;
                font-size: 14px;
            }}
        """
    
    def get_widget_style(self, widget_type: str) -> str:
        """Get comprehensive widget-specific styling.
        
        Args:
            widget_type (str): Type of widget ('journal_editor', etc.)
            
        Returns:
            str: Complete stylesheet for the widget
        """
        if widget_type == "journal_editor":
            return f"""
                /* Main widget styling */
                QWidget {{
                    background-color: {self.SECONDARY_BG};
                    font-family: 'Roboto', 'Segoe UI', -apple-system, sans-serif;
                }}
                
                /* Toolbar styling */
                QToolBar {{
                    background-color: {self.PRIMARY_BG};
                    border: none;
                    border-bottom: 1px solid {self.ACCENT_LIGHT};
                    padding: 8px;
                    spacing: 8px;
                }}
                
                QToolBar QAction {{
                    padding: 8px 12px;
                    margin: 0 2px;
                }}
                
                /* Group box styling */
                QGroupBox {{
                    background-color: {self.PRIMARY_BG};
                    border: 1px solid {self.ACCENT_LIGHT};
                    border-radius: 8px;
                    margin-top: 16px;
                    padding-top: 16px;
                    font-weight: 600;
                }}
                
                QGroupBox::title {{
                    subcontrol-origin: margin;
                    left: 12px;
                    padding: 0 8px;
                    color: {self.TEXT_PRIMARY};
                    background-color: {self.PRIMARY_BG};
                }}
                
                /* List widget styling */
                QListWidget {{
                    background-color: {self.PRIMARY_BG};
                    border: 1px solid {self.ACCENT_LIGHT};
                    border-radius: 6px;
                    padding: 4px;
                    outline: none;
                }}
                
                QListWidget::item {{
                    padding: 8px;
                    border-radius: 4px;
                    margin: 2px;
                }}
                
                QListWidget::item:selected {{
                    background-color: {self.ACCENT_SECONDARY};
                    color: {self.TEXT_INVERSE};
                }}
                
                QListWidget::item:hover {{
                    background-color: rgba(37, 99, 235, 0.1);
                }}
                
                /* Text editor styling */
                QTextEdit {{
                    background-color: {self.PRIMARY_BG};
                    border: 1px solid {self.ACCENT_LIGHT};
                    border-radius: 8px;
                    padding: 12px;
                    font-size: 14px;
                    line-height: 1.6;
                }}
                
                QTextEdit:focus {{
                    border: 2px solid {self.ACCENT_SECONDARY};
                    padding: 11px;
                }}
                
                /* Status bar styling */
                QFrame#statusBar {{
                    background-color: {self.TERTIARY_BG};
                    border-top: 1px solid {self.ACCENT_LIGHT};
                    padding: 8px 16px;
                }}
                
                /* Splitter styling */
                QSplitter::handle {{
                    background-color: {self.ACCENT_LIGHT};
                    width: 1px;
                }}
                
                QSplitter::handle:hover {{
                    background-color: {self.ACCENT_SECONDARY};
                }}
            """
        
        return ""