"""Style manager for consistent theming across the application."""

from ..utils.logging_config import get_logger

logger = get_logger(__name__)


class StyleManager:
    """Manages application styling and themes."""
    
    # Color palette constants - WSJ-inspired professional palette
    PRIMARY_BG = "#FFFFFF"       # Clean white background
    SECONDARY_BG = "#F8F9FA"     # Light gray for cards
    TERTIARY_BG = "#F8F9FA"      # Light gray for sections
    
    ACCENT_PRIMARY = "#5B6770"   # Sophisticated slate - CTAs
    ACCENT_SECONDARY = "#ADB5BD" # Medium gray - highlights
    ACCENT_SUCCESS = "#28A745"   # Professional green - positive
    ACCENT_WARNING = "#FFC107"   # Standard amber - caution
    ACCENT_ERROR = "#DC3545"     # Standard red - errors
    ACCENT_LIGHT = "#E9ECEF"     # Light gray - selections
    
    TEXT_PRIMARY = "#212529"     # Near black
    TEXT_SECONDARY = "#6C757D"   # Medium gray
    TEXT_MUTED = "#ADB5BD"       # Light gray
    TEXT_INVERSE = "#FFFFFF"     # White on dark
    
    # Focus indicator color
    FOCUS_COLOR = "#5B6770"      # Slate for focus indicators
    FOCUS_SHADOW = "rgba(91, 103, 112, 0.3)"  # Slate shadow for focus
    
    # Chart colors - Professional palette
    CHART_COLORS = ["#5B6770", "#6C757D", "#ADB5BD", "#495057", "#868E96"]
    
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
        return f"""
            QMenuBar {{
                background-color: {self.SECONDARY_BG};
                border-bottom: 1px solid rgba(139, 115, 85, 0.1);
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
                background-color: {self.SECONDARY_BG};
                border: 1px solid rgba(139, 115, 85, 0.2);
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
                background-color: rgba(139, 115, 85, 0.2);
                margin: 4px 0;
            }}
        """
    
    def get_tab_widget_style(self):
        """Get the tab widget stylesheet."""
        return f"""
            QTabWidget::pane {{
                background-color: {self.SECONDARY_BG};
                border: 1px solid rgba(139, 115, 85, 0.1);
                border-radius: 8px;
                top: -1px;
            }}
            
            QTabBar {{
                background-color: transparent;
            }}
            
            QTabBar::tab {{
                background-color: {self.TERTIARY_BG};
                color: {self.TEXT_SECONDARY};
                padding: 6px 12px;
                margin-right: 4px;
                border-top-left-radius: 8px;
                border-top-right-radius: 8px;
                border: 1px solid rgba(139, 115, 85, 0.1);
                border-bottom: none;
                font-weight: 500;
            }}
            
            QTabBar::tab:selected {{
                background-color: {self.SECONDARY_BG};
                color: {self.ACCENT_PRIMARY};
                font-weight: 600;
            }}
            
            QTabBar::tab:hover:!selected {{
                background-color: {self.SECONDARY_BG};
                color: {self.TEXT_PRIMARY};
            }}
            
            QTabWidget > QWidget {{
                background-color: {self.SECONDARY_BG};
                border-radius: 8px;
            }}
        """
    
    def get_button_style(self, button_type="primary"):
        """Get button stylesheet based on type."""
        if button_type == "primary":
            return f"""
                QPushButton {{
                    background-color: {self.ACCENT_PRIMARY};
                    color: {self.TEXT_INVERSE};
                    border: none;
                    padding: 4px 10px;
                    border-radius: 6px;
                    font-weight: 600;
                    font-size: 13px;
                }}
                
                QPushButton:hover {{
                    background-color: #4A5560;
                }}
                
                QPushButton:pressed {{
                    background-color: #3A4550;
                }}
                
                QPushButton:disabled {{
                    background-color: {self.TEXT_MUTED};
                    color: {self.SECONDARY_BG};
                }}
                
                QPushButton:focus {{
                    outline: 3px solid {self.FOCUS_COLOR};
                    outline-offset: 2px;
                }}
            """
        elif button_type == "secondary":
            return f"""
                QPushButton {{
                    background-color: transparent;
                    color: {self.ACCENT_PRIMARY};
                    border: 2px solid {self.ACCENT_PRIMARY};
                    padding: 3px 9px;
                    border-radius: 6px;
                    font-weight: 600;
                    font-size: 13px;
                }}
                
                QPushButton:hover {{
                    background-color: {self.TERTIARY_BG};
                    border-color: #4A5560;
                }}
                
                QPushButton:pressed {{
                    background-color: {self.ACCENT_PRIMARY};
                    color: {self.TEXT_INVERSE};
                }}
                
                QPushButton:disabled {{
                    border-color: {self.TEXT_MUTED};
                    color: {self.TEXT_MUTED};
                }}
                
                QPushButton:focus {{
                    outline: 3px solid {self.FOCUS_COLOR};
                    outline-offset: 2px;
                }}
            """
    
    def get_card_style(self):
        """Get card widget stylesheet."""
        return f"""
            QWidget {{
                background-color: {self.SECONDARY_BG};
                border-radius: 12px;
                padding: 16px;
                border: 1px solid rgba(0, 0, 0, 0.05);
            }}
            
            QWidget:hover {{
                border: 1px solid rgba(0, 0, 0, 0.1);
            }}
        """
    
    def get_borderless_card_style(self, padding: int = 16, radius: int = 12):
        """Get borderless card widget stylesheet with subtle shadow."""
        return f"""
            QFrame {{
                background-color: {self.SECONDARY_BG};
                border-radius: {radius}px;
                padding: {padding}px;
                border: 1px solid rgba(0, 0, 0, 0.05);
            }}
            
            QFrame:hover {{
                background-color: {self.TERTIARY_BG};
                border: 1px solid rgba(0, 0, 0, 0.1);
            }}
            
            QLabel {{
                background: transparent;
                border: none;
                color: {self.TEXT_PRIMARY};
            }}
        """
    
    def get_accent_card_style(self, accent_color: str = None, padding: int = 16, radius: int = 8):
        """Get accent-colored card widget stylesheet (for records, achievements, etc.)."""
        if accent_color is None:
            accent_color = self.ACCENT_PRIMARY
        
        return f"""
            QFrame {{
                background-color: {self.PRIMARY_BG};
                border-radius: {radius}px;
                padding: {padding}px;
                border: 1px solid rgba(0, 0, 0, 0.05);
            }}
            
            QFrame:hover {{
                background-color: {self.TERTIARY_BG};
                border: 1px solid rgba(0, 0, 0, 0.1);
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
            QLineEdit, QTextEdit, QSpinBox, QComboBox {{
                background-color: {self.SECONDARY_BG};
                border: 2px solid #E9ECEF;
                border-radius: 6px;
                padding: 4px 6px;
                font-size: 13px;
                color: {self.TEXT_PRIMARY};
            }}
            
            QLineEdit:focus, QTextEdit:focus, QSpinBox:focus, QComboBox:focus, QDateEdit:focus {{
                border: 2px solid {self.ACCENT_PRIMARY};
                outline: none;
            }}
            
            QLineEdit:disabled, QTextEdit:disabled, QSpinBox:disabled, QComboBox:disabled {{
                background-color: {self.TERTIARY_BG};
                color: {self.TEXT_MUTED};
                border-color: rgba(139, 115, 85, 0.1);
            }}
        """
    
    def get_status_bar_style(self):
        """Get status bar stylesheet."""
        return f"""
            QStatusBar {{
                background-color: {self.SECONDARY_BG};
                border-top: 1px solid rgba(139, 115, 85, 0.1);
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
                border: 2px solid {self.FOCUS_COLOR};
                outline: 3px solid {self.FOCUS_SHADOW};
                outline-offset: 1px;
            }}
            
            QTabBar::tab:focus {{
                border: 2px solid {self.FOCUS_COLOR};
                outline: 3px solid {self.FOCUS_SHADOW};
                outline-offset: 1px;
            }}
            
            QCheckBox:focus, QRadioButton:focus {{
                outline: 3px solid {self.FOCUS_COLOR};
                outline-offset: 2px;
                border-radius: 4px;
            }}
        """
        
        app.setStyleSheet(global_style)