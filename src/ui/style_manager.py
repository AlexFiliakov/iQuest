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
    
    This is now a singleton to prevent excessive instantiations.
    
    Attributes:
        colors: Color palette instance
        typography: Typography settings instance
        spacing: Spacing system instance
        _theme: Current theme ('light' or 'dark')
    """
    
    _instance = None
    _initialized = False
    
    def __new__(cls, theme: str = 'light'):
        """Implement singleton pattern."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self, theme: str = 'light'):
        """Initialize the style manager.
        
        Args:
            theme: Theme variant ('light' or 'dark'). Currently only 'light' is implemented.
        """
        # Only initialize once for singleton
        if StyleManager._initialized:
            return
        StyleManager._initialized = True
        self.colors = ColorPalette()
        self.typography = Typography()
        self.spacing = Spacing()
        self._theme = theme
        
        # Legacy attribute aliases for backward compatibility
        self.PRIMARY_COLOR = self.colors.primary
        self.PRIMARY_BG = self.colors.background
        self.SECONDARY_BG = self.colors.surface
        self.TERTIARY_BG = self.colors.surface_alt
        self.TEXT_COLOR = self.colors.text_primary
        self.SECONDARY_TEXT = self.colors.text_secondary
        self.BORDER_COLOR = self.colors.border
        self.SHADOW_COLOR = self.colors.shadow
        self.SUCCESS_COLOR = self.colors.success
        self.ERROR_COLOR = self.colors.error
        self.WARNING_COLOR = self.colors.warning
        self.INFO_COLOR = self.colors.info
        self.ACCENT_COLOR = self.colors.primary_light
        self.HOVER_COLOR = self.colors.primary_hover
        
        # Additional legacy attributes
        self.ACCENT_ERROR = self.colors.error
        self.ACCENT_LIGHT = self.colors.primary_light
        self.ACCENT_PRIMARY = self.colors.primary
        self.ACCENT_SECONDARY = self.colors.info
        self.ACCENT_SUCCESS = self.colors.success
        self.ACCENT_WARNING = self.colors.warning
        
        # Data visualization colors
        self.DATA_ORANGE = '#FF8C42'
        self.DATA_PURPLE = '#9B5DE5'
        self.DATA_TEAL = '#4ECDC4'
        
        # Text color variants
        self.TEXT_INVERSE = self.colors.text_white
        self.TEXT_MUTED = self.colors.text_disabled
        self.TEXT_PRIMARY = self.colors.text_primary
        self.TEXT_SECONDARY = self.colors.text_secondary
        
        # Layout constants
        self.RADIUS = 8  # Default border radius
        self.SPACING = {
            'xxs': self.spacing.xxs,
            'xs': self.spacing.xs,
            'sm': self.spacing.sm,
            'md': self.spacing.md,
            'lg': self.spacing.lg,
            'xl': self.spacing.xl,
            'xxl': self.spacing.xxl,
            'xxxl': self.spacing.xxxl,
        }
        
        # Typography dictionary
        self.TYPOGRAPHY = {
            'family': self.typography.font_family,
            'sizes': {
                'xxs': self.typography.size_xxs,
                'xs': self.typography.size_xs,
                'sm': self.typography.size_sm,
                'base': self.typography.size_base,
                'lg': self.typography.size_lg,
                'xl': self.typography.size_xl,
                'xxl': self.typography.size_xxl,
            },
            'weights': {
                'light': self.typography.weight_light,
                'regular': self.typography.weight_regular,
                'medium': self.typography.weight_medium,
                'semibold': self.typography.weight_semibold,
                'bold': self.typography.weight_bold,
            }
        }
        
        # Warm palette dictionary
        self.WARM_PALETTE = {
            'orange': '#FF8C42',
            'yellow': '#FFD166',
            'red': '#E76F51',
            'pink': '#FF6B6B',
            'light_orange': '#FFB380',
            'sandy': '#F4A261',
            'gold': '#E9C46A',
            'peach': '#F9DCC4',
        }
        
        logger.info(f"StyleManager singleton initialized with {theme} theme")
        
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
        
    def get_main_window_style(self) -> str:
        """Get style for the main application window.
        
        Returns:
            str: Complete stylesheet for MainWindow
        """
        return f"""
            QMainWindow {{
                background-color: {self.colors.background};
            }}
            QMainWindow::separator {{
                background-color: {self.colors.border};
                width: 1px;
                height: 1px;
            }}
        """
        
    def get_menu_bar_style(self) -> str:
        """Get style for menu bars.
        
        Returns:
            str: Complete stylesheet for QMenuBar
        """
        return f"""
            QMenuBar {{
                background-color: {self.colors.surface};
                color: {self.colors.text_primary};
                border-bottom: 1px solid {self.colors.border};
                padding: {self.spacing.xs}px;
            }}
            QMenuBar::item {{
                padding: {self.spacing.xs}px {self.spacing.md}px;
                background-color: transparent;
                border-radius: 4px;
            }}
            QMenuBar::item:selected {{
                background-color: {self.colors.surface_alt};
            }}
            QMenuBar::item:pressed {{
                background-color: {self.colors.primary_light};
            }}
        """
        
    def get_tab_widget_style(self) -> str:
        """Get style for tab widgets.
        
        Returns:
            str: Complete stylesheet for QTabWidget
        """
        return f"""
            QTabWidget::pane {{
                background-color: {self.colors.surface};
                border: 1px solid {self.colors.border};
                border-radius: 8px;
            }}
            QTabBar::tab {{
                background-color: {self.colors.background};
                color: {self.colors.text_secondary};
                padding: {self.spacing.sm}px {self.spacing.lg}px;
                margin-right: {self.spacing.xs}px;
                border-top-left-radius: 6px;
                border-top-right-radius: 6px;
                font-weight: {self.typography.weight_medium};
            }}
            QTabBar::tab:selected {{
                background-color: {self.colors.surface};
                color: {self.colors.text_primary};
                font-weight: {self.typography.weight_semibold};
            }}
            QTabBar::tab:hover {{
                background-color: {self.colors.surface_alt};
            }}
        """
        
    def get_status_bar_style(self) -> str:
        """Get style for status bars.
        
        Returns:
            str: Complete stylesheet for QStatusBar
        """
        return f"""
            QStatusBar {{
                background-color: {self.colors.surface};
                color: {self.colors.text_secondary};
                border-top: 1px solid {self.colors.border};
                font-size: {self.typography.size_sm}px;
            }}
            QStatusBar::item {{
                border: none;
            }}
        """
        
    def get_combo_style(self) -> str:
        """Get style for combo boxes.
        
        Returns:
            str: Complete stylesheet for QComboBox
        """
        return f"""
            QComboBox {{
                background-color: {self.colors.surface};
                color: {self.colors.text_primary};
                border: 2px solid {self.colors.border};
                border-radius: 6px;
                padding: {self.spacing.sm}px {self.spacing.md}px;
                font-size: {self.typography.size_base}px;
                min-height: 24px;
            }}
            QComboBox:hover {{
                border-color: {self.colors.border_hover};
            }}
            QComboBox:focus {{
                border-color: {self.colors.primary};
            }}
            QComboBox::drop-down {{
                border: none;
                width: 20px;
            }}
            QComboBox::down-arrow {{
                image: none;
                border-left: 5px solid transparent;
                border-right: 5px solid transparent;
                border-top: 5px solid {self.colors.text_secondary};
                margin-right: 5px;
            }}
            QComboBox QAbstractItemView {{
                background-color: {self.colors.surface};
                border: 1px solid {self.colors.border};
                selection-background-color: {self.colors.primary_light};
                selection-color: {self.colors.text_primary};
            }}
        """
        
    def get_modern_dialog_style(self) -> str:
        """Get modern style for dialog windows.
        
        Returns:
            str: Complete stylesheet for modern dialogs
        """
        return f"""
            QDialog {{
                background-color: {self.colors.background};
                color: {self.colors.text_primary};
                font-family: {self.typography.font_family};
            }}
            QDialog QLabel {{
                color: {self.colors.text_primary};
            }}
            QDialog QPushButton {{
                min-width: 100px;
                padding: {self.spacing.sm}px {self.spacing.lg}px;
            }}
            QDialog QGroupBox {{
                font-weight: {self.typography.weight_semibold};
                border: 2px solid {self.colors.border};
                border-radius: 8px;
                margin-top: 12px;
                padding-top: 8px;
            }}
        """
        
    def get_modern_card_style(self) -> str:
        """Get modern card style for panels.
        
        Returns:
            str: Complete stylesheet for modern card widgets
        """
        return f"""
            QFrame {{
                background-color: {self.colors.surface};
                border: none;
                border-radius: 12px;
                padding: {self.spacing.xl}px;
            }}
            QFrame:hover {{
                box-shadow: 0 4px 12px {self.colors.shadow};
            }}
        """
        
    def get_modern_progress_bar_style(self) -> str:
        """Get modern progress bar style.
        
        Returns:
            str: Complete stylesheet for modern progress bars
        """
        return f"""
            QProgressBar {{
                background-color: {self.colors.background};
                border: 2px solid {self.colors.border};
                border-radius: 8px;
                text-align: center;
                font-weight: {self.typography.weight_medium};
                color: {self.colors.text_primary};
                min-height: 24px;
            }}
            QProgressBar::chunk {{
                background-color: {self.colors.primary};
                border-radius: 6px;
            }}
        """
        
    def get_form_label_style(self) -> str:
        """Get style for form labels.
        
        Returns:
            str: Complete stylesheet for form labels
        """
        return f"""
            QLabel {{
                font-family: {self.typography.font_family};
                font-size: {self.typography.size_sm}px;
                font-weight: {self.typography.weight_medium};
                color: {self.colors.text_secondary};
                margin-bottom: {self.spacing.xs}px;
            }}
        """
        
    def get_heading_style(self, level: int = 1) -> str:
        """Get style for heading labels.
        
        Args:
            level: Heading level (1-6)
            
        Returns:
            str: Complete stylesheet for heading
        """
        size_map = {
            1: self.typography.size_xxl,
            2: self.typography.size_xl,
            3: self.typography.size_lg,
            4: self.typography.size_base,
            5: self.typography.size_sm,
            6: self.typography.size_xs
        }
        
        return f"""
            QLabel {{
                font-family: {self.typography.font_family};
                font-size: {size_map.get(level, self.typography.size_lg)}px;
                font-weight: {self.typography.weight_bold};
                color: {self.colors.text_primary};
                margin-bottom: {self.spacing.md}px;
            }}
        """
        
    def get_error_message_style(self) -> str:
        """Get style for error messages.
        
        Returns:
            str: Complete stylesheet for error messages
        """
        return f"""
            QLabel {{
                color: {self.colors.error};
                font-size: {self.typography.size_sm}px;
                font-weight: {self.typography.weight_medium};
                padding: {self.spacing.sm}px;
                background-color: rgba(231, 111, 81, 0.1);
                border: 1px solid {self.colors.error};
                border-radius: 4px;
            }}
        """
        
    def get_success_message_style(self) -> str:
        """Get style for success messages.
        
        Returns:
            str: Complete stylesheet for success messages
        """
        return f"""
            QLabel {{
                color: {self.colors.success};
                font-size: {self.typography.size_sm}px;
                font-weight: {self.typography.weight_medium};
                padding: {self.spacing.sm}px;
                background-color: rgba(149, 193, 123, 0.1);
                border: 1px solid {self.colors.success};
                border-radius: 4px;
            }}
        """
        
    def get_info_message_style(self) -> str:
        """Get style for info messages.
        
        Returns:
            str: Complete stylesheet for info messages
        """
        return f"""
            QLabel {{
                color: {self.colors.info};
                font-size: {self.typography.size_sm}px;
                font-weight: {self.typography.weight_medium};
                padding: {self.spacing.sm}px;
                background-color: rgba(108, 155, 209, 0.1);
                border: 1px solid {self.colors.info};
                border-radius: 4px;
            }}
        """
        
    def create_shadow_effect(self, color: str = None, blur_radius: int = 10, 
                           offset: Tuple[int, int] = None, x_offset: int = 0, 
                           y_offset: int = 2, opacity: int = None) -> 'QGraphicsDropShadowEffect':
        """Create a drop shadow effect.
        
        Args:
            color: Shadow color (defaults to shadow color from palette)
            blur_radius: Shadow blur radius
            offset: Shadow offset as (x, y) tuple (overrides x_offset/y_offset)
            x_offset: Horizontal shadow offset (default: 0)
            y_offset: Vertical shadow offset (default: 2)
            opacity: Shadow opacity percentage (0-100, optional)
            
        Returns:
            QGraphicsDropShadowEffect: Configured shadow effect
        """
        from PyQt6.QtWidgets import QGraphicsDropShadowEffect
        
        shadow = QGraphicsDropShadowEffect()
        
        # Handle color with optional opacity
        shadow_color = QColor(color or self.colors.shadow)
        if opacity is not None:
            # Convert percentage to 0-255 range
            alpha = int((opacity / 100.0) * 255)
            shadow_color.setAlpha(alpha)
        
        shadow.setColor(shadow_color)
        shadow.setBlurRadius(blur_radius)
        
        # Handle offset - prefer tuple if provided, otherwise use x/y offsets
        if offset is not None:
            shadow.setOffset(*offset)
        else:
            shadow.setOffset(x_offset, y_offset)
        
        return shadow
        
    def get_shadow_style(self, size: str = 'md') -> str:
        """Get CSS shadow style string.
        
        Args:
            size: Shadow size variant ('sm', 'md', 'lg', 'xl')
        
        Returns:
            str: CSS box-shadow property value
        """
        shadow_configs = {
            'sm': f"0 1px 3px {self.colors.shadow}",
            'md': f"0 2px 10px {self.colors.shadow}",
            'lg': f"0 4px 20px {self.colors.shadow}",
            'xl': f"0 8px 30px {self.colors.shadow}",
        }
        
        return shadow_configs.get(size, shadow_configs['md'])
        
    def get_font_family(self) -> str:
        """Get the primary font family string.
        
        Returns:
            str: Font family string
        """
        return self.typography.font_family
        
    def get_metric_color(self, metric_type: str, index: int = 0) -> str:
        """Get color for a specific metric type.
        
        Args:
            metric_type: Type of metric (e.g., 'steps', 'heart_rate')
            index: Color index for charts with multiple series
            
        Returns:
            str: Hex color code
        """
        # Define metric-specific colors
        metric_colors = {
            'steps': '#FF8C42',           # Orange
            'heart_rate': '#E76F51',      # Red
            'energy': '#FFD166',          # Yellow
            'distance': '#95C17B',        # Green
            'flights_climbed': '#6C9BD1', # Blue
            'sleep': '#9B5DE5',           # Purple
            'weight': '#FF6B6B',          # Pink
            'water': '#4ECDC4',           # Cyan
        }
        
        # Default color palette for generic metrics
        default_colors = [
            self.colors.primary,
            self.colors.info,
            self.colors.success,
            self.colors.warning,
            self.colors.error,
            '#9B5DE5',  # Purple
            '#4ECDC4',  # Cyan
            '#FF6B6B',  # Pink
        ]
        
        if metric_type in metric_colors:
            return metric_colors[metric_type]
        else:
            return default_colors[index % len(default_colors)]
            
    def format_metric_name(self, metric_name: str) -> str:
        """Format metric name for display.
        
        Args:
            metric_name: Raw metric name
            
        Returns:
            str: Formatted metric name
        """
        # Common metric name mappings
        name_map = {
            'steps': 'Steps',
            'heart_rate': 'Heart Rate',
            'energy': 'Active Energy',
            'distance': 'Distance',
            'flights_climbed': 'Flights Climbed',
            'sleep': 'Sleep',
            'weight': 'Weight',
            'water': 'Water',
            'walking_running_distance': 'Walking + Running Distance',
            'resting_heart_rate': 'Resting Heart Rate',
            'walking_heart_rate_average': 'Walking Heart Rate',
            'vo2max': 'VO₂ Max',
            'body_mass_index': 'BMI',
        }
        
        if metric_name in name_map:
            return name_map[metric_name]
        else:
            # Convert snake_case to Title Case
            return metric_name.replace('_', ' ').title()
            
    def format_number(self, value: float, metric_type: str = None) -> str:
        """Format number for display based on metric type.
        
        Args:
            value: Numeric value to format
            metric_type: Type of metric for context-specific formatting
            
        Returns:
            str: Formatted number string
        """
        if metric_type == 'heart_rate':
            return f"{int(value)} bpm"
        elif metric_type == 'distance':
            if value >= 1000:
                return f"{value/1000:.1f} km"
            else:
                return f"{int(value)} m"
        elif metric_type == 'weight':
            return f"{value:.1f} kg"
        elif metric_type == 'energy':
            return f"{int(value)} cal"
        elif metric_type == 'water':
            return f"{int(value)} ml"
        elif metric_type == 'sleep':
            hours = int(value // 60)
            minutes = int(value % 60)
            return f"{hours}h {minutes}m"
        else:
            # Default formatting
            if value >= 1000000:
                return f"{value/1000000:.1f}M"
            elif value >= 1000:
                return f"{value/1000:.1f}K"
            elif value < 1 and value > 0:
                return f"{value:.2f}"
            else:
                return f"{int(value)}"
                
    def get_typography_config(self) -> dict:
        """Get typography configuration as dictionary.
        
        Returns:
            dict: Typography settings
        """
        return {
            'font_family': self.typography.font_family,
            'font_family_mono': self.typography.font_family_mono,
            'sizes': {
                'xxs': self.typography.size_xxs,
                'xs': self.typography.size_xs,
                'sm': self.typography.size_sm,
                'base': self.typography.size_base,
                'lg': self.typography.size_lg,
                'xl': self.typography.size_xl,
                'xxl': self.typography.size_xxl,
            },
            'weights': {
                'light': self.typography.weight_light,
                'regular': self.typography.weight_regular,
                'medium': self.typography.weight_medium,
                'semibold': self.typography.weight_semibold,
                'bold': self.typography.weight_bold,
            }
        }
        
    def get_spacing_config(self) -> dict:
        """Get spacing configuration as dictionary.
        
        Returns:
            dict: Spacing settings
        """
        return {
            'xxs': self.spacing.xxs,
            'xs': self.spacing.xs,
            'sm': self.spacing.sm,
            'md': self.spacing.md,
            'lg': self.spacing.lg,
            'xl': self.spacing.xl,
            'xxl': self.spacing.xxl,
            'xxxl': self.spacing.xxxl,
        }
        
    def get_grid_spacing(self) -> int:
        """Get standard grid spacing value.
        
        Returns:
            int: Grid spacing in pixels
        """
        return self.spacing.sm  # 8px grid
        
    def apply_theme(self, widget) -> None:
        """Apply theme to a widget.
        
        Args:
            widget: QWidget to theme
        """
        widget.setStyleSheet(self.get_widget_style('default'))
        
    def get_export_styles(self) -> str:
        """Get styles for export dialogs and features.
        
        Returns:
            str: Export-specific styles
        """
        return self.get_dialog_style()
        
    def get_warm_palette(self) -> list:
        """Get warm color palette for visualizations.
        
        Returns:
            list: List of warm colors
        """
        return [
            '#FF8C42',  # Orange
            '#FFD166',  # Yellow
            '#E76F51',  # Red
            '#FF6B6B',  # Pink
            '#FFB380',  # Light Orange
            '#F4A261',  # Sandy
            '#E9C46A',  # Gold
            '#F9DCC4',  # Peach
        ]
        
    def get_correlation_colormap(self) -> str:
        """Get colormap name for correlation visualizations.
        
        Returns:
            str: Matplotlib colormap name
        """
        return 'RdYlBu_r'  # Red-Yellow-Blue reversed (warm colors for positive)