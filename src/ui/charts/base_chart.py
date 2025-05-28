"""
Base chart class for all visualization components.

This module provides the foundation for chart widgets in the Apple Health Monitor.
"""

from typing import Dict, List, Any, Optional, Tuple
from abc import abstractmethod

from PyQt6.QtWidgets import QWidget
from PyQt6.QtCore import pyqtSignal as Signal, pyqtProperty as Property, QPropertyAnimation, QEasingCurve, Qt
from PyQt6.QtGui import QColor, QPainter, QFont


class BaseChart(QWidget):
    """
    Abstract base class for all chart widgets.
    
    Provides common functionality for:
    - Color management using design system
    - Animation support
    - Data management
    - Common chart properties
    """
    
    # Signals
    dataChanged = Signal()
    animationFinished = Signal()
    
    def __init__(self, parent=None):
        """Initialize the base chart."""
        super().__init__(parent)
        
        # Data storage
        self._data: List[Dict[str, Any]] = []
        self._title: str = ""
        self._subtitle: str = ""
        
        # Animation
        self._animation_enabled = True
        self._animation_progress = 0.0
        self._animation = QPropertyAnimation(self, b"animationProgress")
        self._animation.setDuration(500)
        self._animation.setEasingCurve(QEasingCurve.OutCubic)
        self._animation.finished.connect(self.animationFinished.emit)
        
        # Design system colors
        self._colors = self._get_default_colors()
        
        # Fonts
        self._fonts = self._get_default_fonts()
        
        # Chart margins
        self._margins = {
            'top': 40,
            'right': 20,
            'bottom': 60,
            'left': 80
        }
        
        # Initialize
        self._setup_chart()
        
    def _get_default_colors(self) -> Dict[str, QColor]:
        """Get default color scheme from design system."""
        return {
            # Background colors
            'background': QColor('#FFFFFF'),
            'background_alt': QColor('#FFF8F0'),
            
            # Grid and axes
            'grid': QColor('#E8DCC8'),
            'axis': QColor('#8B7355'),
            
            # Data colors
            'primary': QColor('#FF8C42'),
            'secondary': QColor('#FFD166'),
            'success': QColor('#95C17B'),
            'warning': QColor('#F4A261'),
            'error': QColor('#E76F51'),
            
            # Chart-specific colors
            'chart_1': QColor('#FF8C42'),
            'chart_2': QColor('#FFD166'),
            'chart_3': QColor('#95C17B'),
            'chart_4': QColor('#6C9BD1'),
            'chart_5': QColor('#B79FCB'),
            
            # Text colors
            'text': QColor('#5D4E37'),
            'text_secondary': QColor('#8B7355'),
            'text_muted': QColor('#A69583'),
            'text_inverse': QColor('#FFFFFF'),
            
            # Interactive states
            'hover': QColor('#E67A35'),
            'active': QColor('#D56F2B'),
            'disabled': QColor('#E8DCC8')
        }
        
    def _get_default_fonts(self) -> Dict[str, QFont]:
        """Get default fonts from design system."""
        return {
            'title': QFont('Poppins', 18, QFont.Weight.Bold),
            'subtitle': QFont('Inter', 14, QFont.Weight.Normal),
            'label': QFont('Inter', 11, QFont.Weight.Normal),
            'label_small': QFont('Inter', 10, QFont.Weight.Normal),
            'value': QFont('Inter', 13, QFont.Weight.Medium),
            'value_large': QFont('Poppins', 16, QFont.Weight.Bold)
        }
        
    def _setup_chart(self):
        """Set up basic chart properties."""
        self.setMinimumSize(400, 300)
        self.setMouseTracking(True)
        
        # Apply base styling
        self.setStyleSheet(f"""
            QWidget {{
                background-color: {self._colors['background'].name()};
                border-radius: 12px;
                border: 1px solid rgba(139, 115, 85, 0.1);
            }}
        """)
        
    # Properties
    def getAnimationProgress(self):
        """Get animation progress (0.0 to 1.0)."""
        return self._animation_progress
        
    def setAnimationProgress(self, value: float):
        """Set animation progress."""
        self._animation_progress = value
        self.update()
        
    animationProgress = Property(float, getAnimationProgress, setAnimationProgress)
        
    @property
    def data(self) -> List[Dict[str, Any]]:
        """Get chart data."""
        return self._data
        
    @data.setter
    def data(self, value: List[Dict[str, Any]]):
        """Set chart data."""
        self._data = value
        self.dataChanged.emit()
        self._on_data_changed()
        
    @property
    def title(self) -> str:
        """Get chart title."""
        return self._title
        
    @title.setter
    def title(self, value: str):
        """Set chart title."""
        self._title = value
        self.update()
        
    @property
    def subtitle(self) -> str:
        """Get chart subtitle."""
        return self._subtitle
        
    @subtitle.setter
    def subtitle(self, value: str):
        """Set chart subtitle."""
        self._subtitle = value
        self.update()
        
    @property
    def margins(self) -> Dict[str, int]:
        """Get chart margins."""
        return self._margins.copy()
        
    def set_margin(self, side: str, value: int):
        """Set a specific margin."""
        if side in self._margins:
            self._margins[side] = value
            self.update()
            
    @property
    def colors(self) -> Dict[str, QColor]:
        """Get color scheme."""
        return self._colors.copy()
        
    def set_color(self, key: str, color: QColor):
        """Set a specific color."""
        if key in self._colors:
            self._colors[key] = color
            self.update()
            
    @property
    def animation_enabled(self) -> bool:
        """Check if animations are enabled."""
        return self._animation_enabled
        
    @animation_enabled.setter
    def animation_enabled(self, value: bool):
        """Enable or disable animations."""
        self._animation_enabled = value
        
    # Public methods
    def animate_in(self):
        """Animate the chart appearance."""
        if self._animation_enabled:
            self._animation.setStartValue(0.0)
            self._animation.setEndValue(1.0)
            self._animation.start()
        else:
            self.animationProgress = 1.0
            
    def animate_update(self):
        """Animate a data update."""
        if self._animation_enabled:
            # Quick fade out and in
            self._animation.setStartValue(1.0)
            self._animation.setEndValue(0.0)
            self._animation.setDuration(200)
            self._animation.finished.connect(self._reverse_animation)
            self._animation.start()
        else:
            self.update()
            
    def _reverse_animation(self):
        """Reverse animation for update effect."""
        self._animation.finished.disconnect(self._reverse_animation)
        self._animation.setStartValue(0.0)
        self._animation.setEndValue(1.0)
        self._animation.setDuration(300)
        self._animation.start()
        
    def clear_data(self):
        """Clear all chart data."""
        self._data = []
        self.dataChanged.emit()
        self.update()
        
    def export_image(self, filename: str, width: int = 800, height: int = 600):
        """Export chart as an image."""
        from PyQt6.QtGui import QPixmap
        
        pixmap = QPixmap(width, height)
        pixmap.fill(self._colors['background'])
        
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # Scale to fit
        scale = min(width / self.width(), height / self.height())
        painter.scale(scale, scale)
        
        # Render the widget
        self.render(painter)
        painter.end()
        
        pixmap.save(filename)
        
    # Abstract methods
    @abstractmethod
    def _on_data_changed(self):
        """Handle data changes. Must be implemented by subclasses."""
        pass
        
    @abstractmethod
    def paintEvent(self, event):
        """Paint the chart. Must be implemented by subclasses."""
        pass
        
    # Protected helper methods
    def _draw_title(self, painter: QPainter):
        """Draw chart title and subtitle."""
        if not self._title:
            return
            
        painter.setFont(self._fonts['title'])
        painter.setPen(self._colors['text'])
        
        # Title
        title_rect = self.rect().adjusted(
            self._margins['left'], 
            10, 
            -self._margins['right'], 
            -self.height() + self._margins['top']
        )
        painter.drawText(title_rect, Qt.AlignmentFlag.AlignCenter, self._title)
        
        # Subtitle
        if self._subtitle:
            painter.setFont(self._fonts['subtitle'])
            painter.setPen(self._colors['text_secondary'])
            
            subtitle_rect = title_rect.adjusted(0, 25, 0, 25)
            painter.drawText(subtitle_rect, Qt.AlignmentFlag.AlignCenter, self._subtitle)
            
    def _get_chart_rect(self):
        """Get the drawable chart area excluding margins."""
        return self.rect().adjusted(
            self._margins['left'],
            self._margins['top'],
            -self._margins['right'],
            -self._margins['bottom']
        )
        
    def _format_number(self, value: float, decimals: int = 0) -> str:
        """Format a number for display."""
        if decimals == 0:
            return f"{int(value):,}"
        else:
            return f"{value:,.{decimals}f}"
            
    def _get_data_color(self, index: int) -> QColor:
        """Get color for data series by index."""
        color_keys = ['chart_1', 'chart_2', 'chart_3', 'chart_4', 'chart_5']
        key = color_keys[index % len(color_keys)]
        return self._colors[key]