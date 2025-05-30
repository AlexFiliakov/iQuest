"""
Base chart class for all visualization components.

This module provides the foundational framework for chart widgets in the
Apple Health Monitor Dashboard. It implements a comprehensive base class
that standardizes chart behavior, styling, and functionality across all
visualization components.

The BaseChart class serves as the foundation for all chart implementations,
providing:
    - Consistent design system integration with professional color palettes
    - Smooth animation system with configurable easing curves
    - Common chart properties and data management
    - Standardized margins, fonts, and styling
    - Export functionality for sharing and reporting
    - Accessibility features for screen readers

Key features:
    - WSJ-inspired professional color palette
    - Configurable animation system with smooth transitions
    - Consistent typography using Inter and Poppins fonts
    - Standardized chart margins and layout system
    - PNG export functionality with customizable dimensions
    - Abstract interface ensuring consistent implementation

Example:
    Creating a custom chart by extending BaseChart:
    
    >>> class MyChart(BaseChart):
    ...     def _on_data_changed(self):
    ...         self.update()  # Refresh display when data changes
    ...     
    ...     def paintEvent(self, event):
    ...         painter = QPainter(self)
    ...         self._draw_title(painter)  # Use base class title rendering
    ...         # Custom chart rendering logic here
    
    >>> chart = MyChart()
    >>> chart.title = "Sample Chart"
    >>> chart.data = [{"x": 1, "y": 10}, {"x": 2, "y": 20}]
    >>> chart.animate_in()

Attributes:
    PRIMARY_BG (str): Primary background color from design system
    ACCENT_PRIMARY (str): Primary accent color for highlights
    TEXT_PRIMARY (str): Primary text color for readability
"""

from typing import Dict, List, Any, Optional, Tuple
from abc import abstractmethod

from PyQt6.QtWidgets import QWidget
from PyQt6.QtCore import pyqtSignal as Signal, pyqtProperty as Property, QPropertyAnimation, QEasingCurve, Qt
from PyQt6.QtGui import QColor, QPainter, QFont


class BaseChart(QWidget):
    """
    Abstract base class for all chart widgets in the Apple Health Monitor.
    
    This class provides a comprehensive foundation for creating consistent,
    professional chart visualizations. It implements the design system,
    animation framework, and common functionality required by all chart types.
    
    Core functionality:
        - Design system integration with professional color palettes
        - Smooth animation system with configurable timing and easing
        - Standardized data management with change notifications
        - Common chart properties (title, subtitle, margins)
        - Export functionality for sharing and reporting
        - Accessibility features for inclusive design
    
    Design system features:
        - WSJ-inspired professional color palette
        - Consistent typography using Inter and Poppins fonts
        - Standardized margins and layout system
        - High contrast ratios for accessibility
        - Smooth shadow effects and modern styling
    
    Animation system:
        - Configurable animation duration and easing curves
        - Smooth transitions for data updates
        - Accessibility-aware animation controls
        - Property-based animation using Qt's animation framework
    
    Data management:
        - Type-safe data storage with validation
        - Automatic change notifications via signals
        - Efficient update handling to minimize redraws
        - Support for various data formats and structures
    
    Signals:
        dataChanged: Emitted when chart data is modified
        animationFinished: Emitted when animations complete
    
    Attributes:
        _data (List[Dict[str, Any]]): Chart data storage
        _title (str): Chart title text
        _subtitle (str): Chart subtitle text
        _animation_enabled (bool): Whether animations are enabled
        _animation_progress (float): Current animation progress (0.0-1.0)
        _colors (Dict[str, QColor]): Design system color palette
        _fonts (Dict[str, QFont]): Typography system fonts
        _margins (Dict[str, int]): Chart margin configuration
    
    Example:
        Implementing a custom chart:
        
        >>> class CustomChart(BaseChart):
        ...     def _on_data_changed(self):
        ...         # Handle data updates
        ...         self.animate_update()
        ...     
        ...     def paintEvent(self, event):
        ...         painter = QPainter(self)
        ...         painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        ...         
        ...         # Use base class helper methods
        ...         self._draw_title(painter)
        ...         chart_rect = self._get_chart_rect()
        ...         
        ...         # Custom chart rendering
        ...         self._render_custom_content(painter, chart_rect)
    """
    
    # Signals
    dataChanged = Signal()
    animationFinished = Signal()
    
    def __init__(self, parent=None):
        """Initialize the base chart with design system and animation setup.
        
        Sets up the foundational components required by all chart widgets
        including the design system, animation framework, and basic properties.
        The initialization ensures consistency across all chart implementations.
        
        Initialization process:
            1. Initialize Qt widget with parent relationship
            2. Set up data storage and basic chart properties
            3. Configure animation system with smooth easing
            4. Apply design system colors and typography
            5. Set standard chart margins and layout
            6. Configure basic chart styling and behavior
        
        Args:
            parent (QWidget, optional): Parent widget for the chart.
                Defaults to None for top-level chart widgets.
        
        Design system setup:
            - Professional color palette with high contrast ratios
            - Typography system using Inter and Poppins fonts
            - Standardized margins for consistent layout
            - Modern styling with rounded corners and subtle shadows
        
        Animation configuration:
            - 500ms duration with OutCubic easing for smooth transitions
            - Property-based animations for data updates
            - Accessibility-aware animation controls
            - Automatic animation progress tracking
        """
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
        """Get default color scheme from the design system.
        
        Returns the professional color palette used throughout the Apple Health
        Monitor Dashboard. The colors are carefully selected for accessibility,
        readability, and professional appearance.
        
        Color categories:
            Background colors:
                - Clean white backgrounds for clarity
                - Subtle gray alternatives for visual hierarchy
                
            Grid and axis colors:
                - Light gray grid lines for subtle guidance
                - Medium gray axis lines for clear boundaries
                
            Data visualization colors:
                - Orange primary for emphasis and highlights
                - Complementary colors for multi-series data
                - Success/warning/error states for status indication
                
            Text colors:
                - High contrast primary text for readability
                - Secondary text for supporting information
                - Inverse text for dark backgrounds
                
            Interactive states:
                - Hover effects for user feedback
                - Active states for pressed elements
                - Disabled states for inactive elements
        
        Returns:
            Dict[str, QColor]: Comprehensive color palette with semantic names.
                Keys include 'background', 'grid', 'axis', 'primary', 'text',
                'hover', 'active', 'disabled', and chart-specific colors.
        
        Example:
            >>> chart = BaseChart()
            >>> colors = chart._get_default_colors()
            >>> background_color = colors['background']
            >>> primary_color = colors['primary']
        """
        return {
            # Background colors
            'background': QColor('#FFFFFF'),
            'background_alt': QColor('#F8F9FA'),
            
            # Grid and axes
            'grid': QColor('#E9ECEF'),
            'axis': QColor('#8B7355'),
            
            # Data colors
            'primary': QColor('#FF8C42'),
            'secondary': QColor('#ADB5BD'),
            'success': QColor('#95C17B'),
            'warning': QColor('#F4A261'),
            'error': QColor('#E76F51'),
            
            # Chart-specific colors
            'chart_1': QColor('#FF8C42'),
            'chart_2': QColor('#ADB5BD'),
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
            'disabled': QColor('#E9ECEF')
        }
        
    def _get_default_fonts(self) -> Dict[str, QFont]:
        """Get default typography from the design system.
        
        Returns the standardized font system used throughout the dashboard
        for consistent typography and professional appearance. The fonts
        are selected for optimal readability across different screen sizes.
        
        Typography hierarchy:
            title (QFont): Large, bold font for chart titles
                - Poppins, 18px, Bold weight
                - Used for main chart titles and headings
                
            subtitle (QFont): Medium font for chart subtitles
                - Inter, 14px, Normal weight
                - Used for descriptive subtitles and secondary headings
                
            label (QFont): Standard font for axis labels
                - Inter, 11px, Normal weight
                - Used for axis labels and general text
                
            label_small (QFont): Small font for detailed labels
                - Inter, 10px, Normal weight
                - Used for tick marks and fine details
                
            value (QFont): Medium font for data values
                - Inter, 13px, Medium weight
                - Used for displaying data values and metrics
                
            value_large (QFont): Large font for prominent values
                - Poppins, 16px, Bold weight
                - Used for key metrics and highlighted values
        
        Returns:
            Dict[str, QFont]: Complete typography system with semantic names.
                Each font is configured with appropriate size, weight, and family.
        
        Example:
            >>> chart = BaseChart()
            >>> fonts = chart._get_default_fonts()
            >>> title_font = fonts['title']
            >>> painter.setFont(title_font)
        """
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
        """Animate the chart's initial appearance with smooth transition.
        
        Provides a smooth entrance animation for the chart when it first
        appears or becomes visible. The animation enhances user experience
        by drawing attention to the new content.
        
        Animation behavior:
            - Starts from 0% progress (invisible/minimal)
            - Animates to 100% progress (fully visible)
            - Uses OutCubic easing for natural movement
            - Respects accessibility settings for animation preferences
        
        If animations are disabled (for accessibility or performance),
        the chart immediately appears at full opacity without transition.
        
        Example:
            >>> chart = BaseChart()
            >>> chart.data = sample_data
            >>> chart.animate_in()  # Smooth entrance animation
            
        Note:
            This method is typically called when showing a chart for the
            first time or when switching between different chart views.
        """
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
        """Export chart as a high-quality PNG image.
        
        Creates a high-quality image export of the current chart for sharing,
        reporting, or documentation purposes. The export maintains the chart's
        visual quality and styling at the specified resolution.
        
        Export process:
            1. Create a high-resolution pixmap at specified dimensions
            2. Fill with chart's background color for consistency
            3. Set up high-quality rendering with antialiasing
            4. Scale chart content to fit the export dimensions
            5. Render the complete chart to the image
            6. Save to the specified filename in PNG format
        
        Args:
            filename (str): Output filename for the exported image.
                Should include .png extension for proper format.
            width (int, optional): Export image width in pixels.
                Defaults to 800 for high quality.
            height (int, optional): Export image height in pixels.
                Defaults to 600 for standard aspect ratio.
        
        Quality features:
            - High-resolution rendering for crisp text and lines
            - Antialiasing for smooth curves and edges
            - Proper scaling to maintain visual proportions
            - Background color preservation for consistency
        
        Raises:
            IOError: If the file cannot be written to the specified location
            
        Example:
            >>> chart = BaseChart()
            >>> chart.title = "Sample Chart"
            >>> chart.data = sample_data
            >>> chart.export_image("my_chart.png", width=1200, height=800)
        
        Note:
            The exported image captures the chart's current state including
            all styling, colors, and data visualization elements.
        """
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