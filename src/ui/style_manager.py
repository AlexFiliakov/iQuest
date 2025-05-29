"""Style manager for consistent theming across the application."""

from ..utils.logging_config import get_logger

logger = get_logger(__name__)


class StyleManager:
    """Manages application styling and themes."""
    
    # Color palette constants
    PRIMARY_BG = "#F5E6D3"      # Warm tan background
    SECONDARY_BG = "#FFFFFF"    # White for cards
    TERTIARY_BG = "#FFF8F0"     # Light cream for sections
    
    ACCENT_PRIMARY = "#FF8C42"   # Warm orange - CTAs
    ACCENT_SECONDARY = "#FFD166" # Soft yellow - highlights
    ACCENT_SUCCESS = "#95C17B"   # Soft green - positive
    ACCENT_WARNING = "#F4A261"   # Amber - caution
    ACCENT_ERROR = "#E76F51"     # Coral - errors
    
    TEXT_PRIMARY = "#5D4E37"     # Dark brown
    TEXT_SECONDARY = "#8B7355"   # Medium brown
    TEXT_MUTED = "#A69583"       # Light brown
    TEXT_INVERSE = "#FFFFFF"     # White on dark
    
    # Focus indicator color
    FOCUS_COLOR = "#FF8C42"      # Orange for focus indicators
    FOCUS_SHADOW = "rgba(255, 140, 66, 0.3)"  # Orange shadow for focus
    
    # Chart colors
    CHART_COLORS = ["#FF8C42", "#FFD166", "#95C17B", "#6C9BD1", "#B79FCB"]
    
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
                font-size: 14px;
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
                    padding: 6px 12px;
                    border-radius: 8px;
                    font-weight: 600;
                    font-size: 14px;
                }}
                
                QPushButton:hover {{
                    background-color: #E67A35;
                }}
                
                QPushButton:pressed {{
                    background-color: #D06928;
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
                    padding: 5px 11px;
                    border-radius: 8px;
                    font-weight: 600;
                    font-size: 14px;
                }}
                
                QPushButton:hover {{
                    background-color: {self.TERTIARY_BG};
                    border-color: #E67A35;
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
                padding: 12px;
                border: 1px solid rgba(139, 115, 85, 0.1);
            }}
            
            QWidget:hover {{
                border: 1px solid rgba(139, 115, 85, 0.2);
            }}
        """
    
    def get_input_style(self):
        """Get input field stylesheet."""
        return f"""
            QLineEdit, QTextEdit, QSpinBox, QComboBox {{
                background-color: {self.SECONDARY_BG};
                border: 2px solid #E8DCC8;
                border-radius: 8px;
                padding: 6px 8px;
                font-size: 14px;
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