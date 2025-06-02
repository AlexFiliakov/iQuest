"""Style management system for consistent UI theming.

This module provides centralized style management for the Apple Health Monitor
application, ensuring consistent visual design across all UI components. It
implements the Wall Street Journal-inspired design system with warm colors
and professional typography.

The StyleManager class provides:
    - Centralized color palette management
    - Component-specific style sheets
    - Typography settings and font management
    - Responsive sizing and spacing calculations
    - Theme variation support (light/dark)
    - Dynamic style generation based on component state

Key design principles:
    - Warm, inviting color palette (tans, oranges, browns)
    - Professional typography with clear hierarchy
    - Consistent spacing and padding across components
    - Subtle shadows and depth effects
    - Accessibility-compliant color contrasts

Example:
    Basic usage:
    
    >>> style_manager = StyleManager()
    >>> button_style = style_manager.get_button_style()
    >>> widget.setStyleSheet(button_style)
    
    Component-specific styles:
    
    >>> journal_style = style_manager.get_widget_style('journal_editor')
    >>> dialog_style = style_manager.get_dialog_style()
    
    Dynamic styling:
    
    >>> hover_style = style_manager.get_button_style(state='hover')
    >>> error_style = style_manager.get_input_style(state='error')
"""

from typing import Dict, Optional, Tuple
from dataclasses import dataclass
from PyQt6.QtGui import QFont, QColor

from ..utils.logging_config import get_logger

logger = get_logger(__name__)


@dataclass
class ColorPalette:
    """Application color palette following WSJ-inspired design.
    
    This dataclass defines all colors used throughout the application,
    organized by their purpose and following accessibility guidelines
    for proper contrast ratios.
    
    Attributes:
        # Primary colors
        primary: Main brand color (warm orange)
        primary_hover: Darker variant for hover states
        primary_light: Lighter variant for backgrounds
        
        # Background colors
        background: Main background (warm tan)
        surface: Card/panel background (white)
        surface_alt: Alternative surface (light tan)
        
        # Text colors
        text_primary: Main text color (dark brown)
        text_secondary: Secondary text (medium brown)
        text_disabled: Disabled text (light brown)
        
        # Accent colors
        success: Success state (green)
        warning: Warning state (yellow)
        error: Error state (red)
        info: Information state (blue)
        
        # Border colors
        border: Default border (light brown)
        border_hover: Border on hover (darker brown)
        border_focus: Border on focus (orange)
    """
    # Primary colors
    primary: str = "#FF8C42"          # Warm orange
    primary_hover: str = "#E67A32"    # Darker orange
    primary_light: str = "#FFB380"    # Light orange
    
    # Background colors
    background: str = "#FAF6F0"       # Warm tan background
    surface: str = "#FFFFFF"          # White surface
    surface_alt: str = "#FFF5E6"      # Light tan surface
    
    # Text colors
    text_primary: str = "#5D4E37"     # Dark brown
    text_secondary: str = "#8B7B65"   # Medium brown
    text_disabled: str = "#B5A595"    # Light brown
    text_white: str = "#FFFFFF"       # White text
    
    # Accent colors
    success: str = "#95C17B"          # Green
    warning: str = "#FFD166"          # Yellow
    error: str = "#E76F51"            # Red
    info: str = "#6C9BD1"             # Blue
    
    # Border colors
    border: str = "#E8DCC8"           # Light brown border
    border_hover: str = "#D5C5B0"     # Darker border
    border_focus: str = "#FF8C42"     # Orange focus border
    
    # Shadow colors
    shadow: str = "rgba(0, 0, 0, 0.1)"
    shadow_dark: str = "rgba(0, 0, 0, 0.2)"


@dataclass
class Typography:
    """Typography settings for consistent text styling.
    
    Defines font families, sizes, and weights used throughout
    the application following a clear hierarchy.
    
    Attributes:
        font_family: Primary font family
        font_family_mono: Monospace font for data
        
        # Font sizes
        size_xxs: Extra extra small (10px)
        size_xs: Extra small (11px)
        size_sm: Small (12px)
        size_base: Base size (14px)
        size_lg: Large (16px)
        size_xl: Extra large (18px)
        size_xxl: Extra extra large (24px)
        
        # Font weights
        weight_light: Light weight (300)
        weight_regular: Regular weight (400)
        weight_medium: Medium weight (500)
        weight_semibold: Semi-bold weight (600)
        weight_bold: Bold weight (700)
    """
    # Font families
    font_family: str = "Inter, -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif"
    font_family_mono: str = "'SF Mono', Monaco, 'Courier New', monospace"
    
    # Font sizes
    size_xxs: int = 10
    size_xs: int = 11
    size_sm: int = 12
    size_base: int = 14
    size_lg: int = 16
    size_xl: int = 18
    size_xxl: int = 24
    
    # Font weights
    weight_light: int = 300
    weight_regular: int = 400
    weight_medium: int = 500
    weight_semibold: int = 600
    weight_bold: int = 700


@dataclass
class Spacing:
    """Spacing system for consistent layout.
    
    Provides a consistent spacing scale for margins, padding,
    and gaps throughout the application.
    
    Attributes:
        xxs: 2px
        xs: 4px
        sm: 8px
        md: 12px
        lg: 16px
        xl: 24px
        xxl: 32px
        xxxl: 48px
    """
    xxs: int = 2
    xs: int = 4
    sm: int = 8
    md: int = 12
    lg: int = 16
    xl: int = 24
    xxl: int = 32
    xxxl: int = 48


class StyleManager:
    """Central style management for the application.
    
    This class provides methods to generate consistent styles for all
    UI components in the application. It ensures visual consistency
    and makes it easy to update the design system globally.
    
    The manager uses a template-based approach where component styles
    are generated dynamically based on the current theme and state.
    
    Attributes:
        colors: Color palette instance
        typography: Typography settings instance
        spacing: Spacing system instance
        _theme: Current theme ('light' or 'dark')
    """
    
    def __init__(self, theme: str = 'light'):
        """Initialize the style manager.
        
        Args:
            theme: Theme variant ('light' or 'dark'). Currently only 'light' is implemented.
        """
        self.colors = ColorPalette()
        self.typography = Typography()
        self.spacing = Spacing()
        self._theme = theme
        
        logger.info(f"StyleManager initialized with {theme} theme")
        
    def get_button_style(self, variant: str = 'primary', state: str = 'normal') -> str:
        """Generate button styles based on variant and state.
        
        Args:
            variant: Button variant ('primary', 'secondary', 'ghost', 'danger')
            state: Button state ('normal', 'hover', 'pressed', 'disabled')
            
        Returns:
            str: Complete stylesheet for QPushButton
        """
        base_style = f"""
            QPushButton {{
                font-family: {self.typography.font_family};
                font-size: {self.typography.size_base}px;
                font-weight: {self.typography.weight_medium};
                padding: {self.spacing.sm}px {self.spacing.lg}px;
                border-radius: 6px;
                border: 2px solid transparent;
                outline: none;
            }}
        """
        
        if variant == 'primary':
            return base_style + f"""
                QPushButton {{
                    background-color: {self.colors.primary};
                    color: {self.colors.text_white};
                    border-color: {self.colors.primary};
                }}
                QPushButton:hover {{
                    background-color: {self.colors.primary_hover};
                    border-color: {self.colors.primary_hover};
                }}
                QPushButton:pressed {{
                    background-color: {self.colors.primary_hover};
                    transform: translateY(1px);
                }}
                QPushButton:disabled {{
                    background-color: {self.colors.border};
                    color: {self.colors.text_disabled};
                    border-color: {self.colors.border};
                }}
            """
        elif variant == 'secondary':
            return base_style + f"""
                QPushButton {{
                    background-color: {self.colors.surface};
                    color: {self.colors.text_primary};
                    border-color: {self.colors.border};
                }}
                QPushButton:hover {{
                    background-color: {self.colors.surface_alt};
                    border-color: {self.colors.border_hover};
                }}
                QPushButton:pressed {{
                    background-color: {self.colors.surface_alt};
                    border-color: {self.colors.primary};
                }}
                QPushButton:disabled {{
                    background-color: {self.colors.background};
                    color: {self.colors.text_disabled};
                    border-color: {self.colors.border};
                }}
            """
        elif variant == 'danger':
            return base_style + f"""
                QPushButton {{
                    background-color: {self.colors.error};
                    color: {self.colors.text_white};
                    border-color: {self.colors.error};
                }}
                QPushButton:hover {{
                    background-color: #D65740;
                    border-color: #D65740;
                }}
                QPushButton:pressed {{
                    background-color: #C64635;
                    border-color: #C64635;
                }}
            """
        else:  # ghost
            return base_style + f"""
                QPushButton {{
                    background-color: transparent;
                    color: {self.colors.text_primary};
                    border-color: transparent;
                }}
                QPushButton:hover {{
                    background-color: {self.colors.surface_alt};
                }}
                QPushButton:pressed {{
                    background-color: {self.colors.border};
                }}
            """
            
    def get_input_style(self, state: str = 'normal') -> str:
        """Generate input field styles.
        
        Args:
            state: Input state ('normal', 'focus', 'error', 'disabled')
            
        Returns:
            str: Complete stylesheet for QLineEdit/QTextEdit
        """
        base_style = f"""
            QLineEdit, QTextEdit {{
                font-family: {self.typography.font_family};
                font-size: {self.typography.size_base}px;
                padding: {self.spacing.sm}px {self.spacing.md}px;
                background-color: {self.colors.surface};
                color: {self.colors.text_primary};
                border: 2px solid {self.colors.border};
                border-radius: 6px;
            }}
            QLineEdit:focus, QTextEdit:focus {{
                border-color: {self.colors.primary};
                outline: none;
            }}
            QLineEdit:disabled, QTextEdit:disabled {{
                background-color: {self.colors.background};
                color: {self.colors.text_disabled};
                border-color: {self.colors.border};
            }}
        """
        
        if state == 'error':
            base_style += f"""
                QLineEdit, QTextEdit {{
                    border-color: {self.colors.error};
                }}
            """
            
        return base_style
        
    def get_widget_style(self, widget_type: str) -> str:
        """Get style for specific widget types.
        
        Args:
            widget_type: Type of widget ('journal_editor', 'calendar', 'chart', etc.)
            
        Returns:
            str: Complete stylesheet for the widget
        """
        if widget_type == 'journal_editor':
            return f"""
                QWidget {{
                    background-color: {self.colors.background};
                }}
                QGroupBox {{
                    font-family: {self.typography.font_family};
                    font-size: {self.typography.size_lg}px;
                    font-weight: {self.typography.weight_semibold};
                    color: {self.colors.text_primary};
                    border: 2px solid {self.colors.border};
                    border-radius: 8px;
                    margin-top: 12px;
                    padding-top: 8px;
                }}
                QGroupBox::title {{
                    subcontrol-origin: margin;
                    left: 12px;
                    padding: 0 8px 0 8px;
                    background-color: {self.colors.background};
                }}
                QListWidget {{
                    background-color: {self.colors.surface};
                    border: 1px solid {self.colors.border};
                    border-radius: 6px;
                    padding: {self.spacing.xs}px;
                }}
                QListWidget::item {{
                    padding: {self.spacing.sm}px;
                    border-radius: 4px;
                    margin: {self.spacing.xxs}px;
                }}
                QListWidget::item:selected {{
                    background-color: {self.colors.primary_light};
                    color: {self.colors.text_primary};
                }}
                QListWidget::item:hover {{
                    background-color: {self.colors.surface_alt};
                }}
            """
        elif widget_type == 'calendar':
            return f"""
                QCalendarWidget {{
                    background-color: {self.colors.surface};
                    border: 2px solid {self.colors.border};
                    border-radius: 8px;
                }}
                QCalendarWidget QToolButton {{
                    color: {self.colors.text_primary};
                    background-color: transparent;
                    border: none;
                    border-radius: 4px;
                    padding: {self.spacing.xs}px;
                }}
                QCalendarWidget QToolButton:hover {{
                    background-color: {self.colors.surface_alt};
                }}
                QCalendarWidget QToolButton:pressed {{
                    background-color: {self.colors.primary_light};
                }}
                QCalendarWidget QMenu {{
                    background-color: {self.colors.surface};
                    border: 1px solid {self.colors.border};
                }}
                QCalendarWidget QSpinBox {{
                    background-color: {self.colors.surface};
                    border: 1px solid {self.colors.border};
                    border-radius: 4px;
                    padding: {self.spacing.xs}px;
                }}
                QCalendarWidget QTableView {{
                    background-color: {self.colors.surface};
                    selection-background-color: {self.colors.primary_light};
                    selection-color: {self.colors.text_primary};
                }}
            """
        else:
            # Default widget style
            return f"""
                QWidget {{
                    background-color: {self.colors.background};
                    color: {self.colors.text_primary};
                    font-family: {self.typography.font_family};
                    font-size: {self.typography.size_base}px;
                }}
            """
            
    def get_dialog_style(self) -> str:
        """Get style for dialog windows.
        
        Returns:
            str: Complete stylesheet for QDialog
        """
        return f"""
            QDialog {{
                background-color: {self.colors.background};
                color: {self.colors.text_primary};
                font-family: {self.typography.font_family};
            }}
            QDialogButtonBox QPushButton {{
                min-width: 80px;
                padding: {self.spacing.sm}px {self.spacing.lg}px;
            }}
        """
        
    def get_label_style(self, variant: str = 'normal') -> str:
        """Get style for labels.
        
        Args:
            variant: Label variant ('normal', 'heading', 'caption', 'error')
            
        Returns:
            str: Complete stylesheet for QLabel
        """
        base_style = f"""
            QLabel {{
                font-family: {self.typography.font_family};
                color: {self.colors.text_primary};
            }}
        """
        
        if variant == 'heading':
            return base_style + f"""
                QLabel {{
                    font-size: {self.typography.size_xl}px;
                    font-weight: {self.typography.weight_semibold};
                }}
            """
        elif variant == 'caption':
            return base_style + f"""
                QLabel {{
                    font-size: {self.typography.size_sm}px;
                    color: {self.colors.text_secondary};
                }}
            """
        elif variant == 'error':
            return base_style + f"""
                QLabel {{
                    color: {self.colors.error};
                    font-size: {self.typography.size_sm}px;
                }}
            """
        else:
            return base_style + f"""
                QLabel {{
                    font-size: {self.typography.size_base}px;
                }}
            """
            
    def get_card_style(self) -> str:
        """Get style for card/panel components.
        
        Returns:
            str: Complete stylesheet for card-like widgets
        """
        return f"""
            QFrame {{
                background-color: {self.colors.surface};
                border: 1px solid {self.colors.border};
                border-radius: 8px;
                padding: {self.spacing.lg}px;
            }}
            QFrame:hover {{
                border-color: {self.colors.border_hover};
                box-shadow: 0 2px 8px {self.colors.shadow};
            }}
        """
        
    def get_toolbar_style(self) -> str:
        """Get style for toolbars.
        
        Returns:
            str: Complete stylesheet for QToolBar
        """
        return f"""
            QToolBar {{
                background-color: {self.colors.surface};
                border: none;
                border-bottom: 1px solid {self.colors.border};
                padding: {self.spacing.sm}px;
                spacing: {self.spacing.sm}px;
            }}
            QToolBar QToolButton {{
                background-color: transparent;
                border: none;
                border-radius: 4px;
                padding: {self.spacing.sm}px;
                color: {self.colors.text_primary};
            }}
            QToolBar QToolButton:hover {{
                background-color: {self.colors.surface_alt};
            }}
            QToolBar QToolButton:pressed {{
                background-color: {self.colors.primary_light};
            }}
            QToolBar QToolButton:checked {{
                background-color: {self.colors.primary_light};
                color: {self.colors.primary};
            }}
        """
        
    def get_scrollbar_style(self) -> str:
        """Get style for scrollbars.
        
        Returns:
            str: Complete stylesheet for QScrollBar
        """
        return f"""
            QScrollBar:vertical {{
                background-color: {self.colors.background};
                width: 12px;
                border: none;
            }}
            QScrollBar::handle:vertical {{
                background-color: {self.colors.border};
                border-radius: 6px;
                min-height: 30px;
            }}
            QScrollBar::handle:vertical:hover {{
                background-color: {self.colors.border_hover};
            }}
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
                border: none;
                background: none;
                height: 0px;
            }}
            QScrollBar:horizontal {{
                background-color: {self.colors.background};
                height: 12px;
                border: none;
            }}
            QScrollBar::handle:horizontal {{
                background-color: {self.colors.border};
                border-radius: 6px;
                min-width: 30px;
            }}
            QScrollBar::handle:horizontal:hover {{
                background-color: {self.colors.border_hover};
            }}
            QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {{
                border: none;
                background: none;
                width: 0px;
            }}
        """
        
    def get_font(self, size: str = 'base', weight: str = 'regular') -> QFont:
        """Get a QFont object with specified size and weight.
        
        Args:
            size: Size variant ('xs', 'sm', 'base', 'lg', 'xl', 'xxl')
            weight: Weight variant ('light', 'regular', 'medium', 'semibold', 'bold')
            
        Returns:
            QFont: Configured font object
        """
        font = QFont()
        font.setFamily("Inter")
        
        # Set size
        size_map = {
            'xxs': self.typography.size_xxs,
            'xs': self.typography.size_xs,
            'sm': self.typography.size_sm,
            'base': self.typography.size_base,
            'lg': self.typography.size_lg,
            'xl': self.typography.size_xl,
            'xxl': self.typography.size_xxl
        }
        font.setPixelSize(size_map.get(size, self.typography.size_base))
        
        # Set weight
        weight_map = {
            'light': self.typography.weight_light,
            'regular': self.typography.weight_regular,
            'medium': self.typography.weight_medium,
            'semibold': self.typography.weight_semibold,
            'bold': self.typography.weight_bold
        }
        font.setWeight(weight_map.get(weight, self.typography.weight_regular))
        
        return font
        
    def get_color(self, color_name: str) -> QColor:
        """Get a QColor object for the specified color name.
        
        Args:
            color_name: Name of the color from the palette
            
        Returns:
            QColor: Color object
        """
        color_value = getattr(self.colors, color_name, self.colors.text_primary)
        return QColor(color_value)
        
    def apply_global_style(self, app) -> None:
        """Apply global application style.
        
        Sets the application-wide stylesheet with base styles for
        all widgets. Individual widgets can override these styles.
        
        Args:
            app: QApplication instance
        """
        global_style = f"""
            * {{
                font-family: {self.typography.font_family};
            }}
            QWidget {{
                background-color: {self.colors.background};
                color: {self.colors.text_primary};
            }}
            QToolTip {{
                background-color: {self.colors.text_primary};
                color: {self.colors.text_white};
                border: none;
                padding: {self.spacing.xs}px {self.spacing.sm}px;
                border-radius: 4px;
                font-size: {self.typography.size_sm}px;
            }}
            QMenu {{
                background-color: {self.colors.surface};
                border: 1px solid {self.colors.border};
                border-radius: 6px;
                padding: {self.spacing.xs}px;
            }}
            QMenu::item {{
                padding: {self.spacing.sm}px {self.spacing.lg}px;
                border-radius: 4px;
            }}
            QMenu::item:selected {{
                background-color: {self.colors.primary_light};
                color: {self.colors.text_primary};
            }}
        """
        
        app.setStyleSheet(global_style)
        logger.info("Applied global application style")