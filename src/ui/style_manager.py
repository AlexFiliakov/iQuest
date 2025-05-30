"""Style manager for consistent theming across the application."""

from ..utils.logging_config import get_logger

logger = get_logger(__name__)


class StyleManager:
    """Manages application styling and themes."""
    
    # Color palette constants - Modern WSJ-inspired professional palette
    PRIMARY_BG = "#FFFFFF"       # Clean white background
    SECONDARY_BG = "#FAFBFC"     # Very light gray for subtle contrast
    TERTIARY_BG = "#F3F4F6"      # Light gray for hover states
    SURFACE_ELEVATED = "#FFFFFF" # Elevated surface with shadow
    
    ACCENT_PRIMARY = "#0F172A"   # Rich black - primary text
    ACCENT_SECONDARY = "#2563EB" # Vibrant blue - CTAs and highlights
    ACCENT_SUCCESS = "#10B981"   # Modern green - positive states
    ACCENT_WARNING = "#F59E0B"   # Modern amber - caution
    ACCENT_ERROR = "#EF4444"     # Modern red - errors
    ACCENT_LIGHT = "#E5E7EB"     # Light gray - subtle borders
    
    TEXT_PRIMARY = "#0F172A"     # Rich black
    TEXT_SECONDARY = "#64748B"   # Slate gray
    TEXT_MUTED = "#94A3B8"       # Light slate
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
    
    def __init__(self):
        """Initialize the style manager."""
        logger.debug("Initializing StyleManager")
    
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
        """Get the tab widget stylesheet with modern underline indicators."""
        return f"""
            QTabWidget::pane {{
                background-color: {self.PRIMARY_BG};
                border: none;
                top: 0px;
            }}
            
            QTabBar {{
                background-color: transparent;
                border-bottom: 1px solid {self.ACCENT_LIGHT};
            }}
            
            QTabBar::tab {{
                background: transparent;
                color: {self.TEXT_SECONDARY};
                padding: 8px 16px;
                margin-right: 8px;
                border: none;
                border-bottom: 2px solid transparent;
                font-weight: 500;
            }}
            
            QTabBar::tab:selected {{
                color: {self.ACCENT_PRIMARY};
                border-bottom: 2px solid {self.ACCENT_PRIMARY};
                font-weight: 600;
            }}
            
            QTabBar::tab:hover:!selected {{
                color: {self.TEXT_PRIMARY};
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
        """Get button stylesheet based on type."""
        if button_type == "primary":
            return f"""
                QPushButton {{
                    background-color: {self.ACCENT_SECONDARY};
                    color: {self.TEXT_INVERSE};
                    border: none;
                    padding: 8px 20px;
                    border-radius: 6px;
                    font-weight: 600;
                    font-size: 13px;
                    min-height: 32px;
                    letter-spacing: 0.3px;
                }}
                
                QPushButton:hover {{
                    background-color: #1D4ED8;
                }}
                
                QPushButton:pressed {{
                    background-color: #1E40AF;
                }}
                
                QPushButton:disabled {{
                    background-color: {self.TEXT_MUTED};
                    color: {self.SECONDARY_BG};
                }}
                
                QPushButton:focus {{
                    outline: none;
                    border: 2px solid {self.FOCUS_SHADOW};
                }}
            """
        elif button_type == "secondary":
            return f"""
                QPushButton {{
                    background-color: {self.PRIMARY_BG};
                    color: {self.TEXT_PRIMARY};
                    border: 1px solid {self.ACCENT_LIGHT};
                    padding: 8px 20px;
                    border-radius: 6px;
                    font-weight: 500;
                    font-size: 13px;
                    min-height: 32px;
                    letter-spacing: 0.3px;
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
                    border: 2px solid {self.FOCUS_SHADOW};
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
                border-radius: 4px;
                padding: 0 16px;
                height: 40px;
                font-size: 13px;
                color: {self.TEXT_PRIMARY};
            }}
            
            QTextEdit {{
                padding: 12px 16px;
                height: auto;
                min-height: 80px;
            }}
            
            QLineEdit:hover, QTextEdit:hover, QSpinBox:hover, QComboBox:hover, QDateEdit:hover {{
                border-color: {self.ACCENT_SECONDARY};
            }}
            
            QLineEdit:focus, QTextEdit:focus, QSpinBox:focus, QComboBox:focus, QDateEdit:focus {{
                border-color: {self.ACCENT_PRIMARY};
                outline: none;
                border: 1px solid {self.ACCENT_PRIMARY};
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
    
    def apply_global_style(self, app):
        """Apply global application styling."""
        logger.info("Applying global application style")
        
        # Set application style sheet
        global_style = f"""
            * {{
                font-family: 'Inter', 'Segoe UI', -apple-system, sans-serif;
            }}
            
            QToolTip {{
                background-color: {self.TEXT_PRIMARY};
                color: {self.TEXT_INVERSE};
                border: none;
                padding: 8px;
                border-radius: 4px;
                font-size: 14px;
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