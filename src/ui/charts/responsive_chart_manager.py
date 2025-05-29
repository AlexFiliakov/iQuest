"""Responsive design manager for charts across different screen sizes."""

from typing import Dict, Any, Tuple, Optional, List
from dataclasses import dataclass
from enum import Enum
from PyQt6.QtCore import QSize, QRect

from ...utils.logging_config import get_logger

logger = get_logger(__name__)


class DeviceClass(Enum):
    """Device classification based on screen size."""
    PHONE = "phone"  # < 768px
    TABLET = "tablet"  # 768px - 1024px
    SMALL_DESKTOP = "small_desktop"  # 1024px - 1440px
    STANDARD_DESKTOP = "standard_desktop"  # 1440px - 2560px
    LARGE_DESKTOP = "large_desktop"  # > 2560px
    ULTRA_WIDE = "ultra_wide"  # Aspect ratio > 2.0


@dataclass
class ResponsiveConfig:
    """Configuration for responsive chart behavior."""
    # Layout
    margins: Dict[str, int]
    padding: int
    
    # Typography
    title_size: int
    subtitle_size: int
    label_size: int
    tick_size: int
    
    # Data display
    max_data_points: int
    point_size: float
    line_width: float
    
    # Interactivity
    enable_zoom: bool
    enable_pan: bool
    enable_tooltips: bool
    
    # Legend
    legend_position: str
    legend_columns: int
    
    # Grid
    show_grid: bool
    grid_density: str  # 'sparse', 'normal', 'dense'


class ResponsiveChartManager:
    """Manages responsive behavior for charts."""
    
    # Breakpoints in pixels
    BREAKPOINTS = {
        'phone': 768,
        'tablet': 1024,
        'small_desktop': 1440,
        'standard_desktop': 2560
    }
    
    # Responsive configurations for each device class
    RESPONSIVE_CONFIGS = {
        DeviceClass.PHONE: ResponsiveConfig(
            margins={'left': 40, 'right': 20, 'top': 40, 'bottom': 40},
            padding=10,
            title_size=14,
            subtitle_size=12,
            label_size=10,
            tick_size=8,
            max_data_points=100,
            point_size=3.0,
            line_width=1.5,
            enable_zoom=False,
            enable_pan=True,
            enable_tooltips=True,
            legend_position='bottom',
            legend_columns=1,
            show_grid=True,
            grid_density='sparse'
        ),
        
        DeviceClass.TABLET: ResponsiveConfig(
            margins={'left': 60, 'right': 30, 'top': 50, 'bottom': 50},
            padding=15,
            title_size=16,
            subtitle_size=13,
            label_size=11,
            tick_size=9,
            max_data_points=500,
            point_size=4.0,
            line_width=2.0,
            enable_zoom=True,
            enable_pan=True,
            enable_tooltips=True,
            legend_position='top',
            legend_columns=2,
            show_grid=True,
            grid_density='normal'
        ),
        
        DeviceClass.SMALL_DESKTOP: ResponsiveConfig(
            margins={'left': 80, 'right': 40, 'top': 60, 'bottom': 60},
            padding=20,
            title_size=18,
            subtitle_size=14,
            label_size=12,
            tick_size=10,
            max_data_points=1000,
            point_size=4.5,
            line_width=2.5,
            enable_zoom=True,
            enable_pan=True,
            enable_tooltips=True,
            legend_position='right',
            legend_columns=1,
            show_grid=True,
            grid_density='normal'
        ),
        
        DeviceClass.STANDARD_DESKTOP: ResponsiveConfig(
            margins={'left': 100, 'right': 60, 'top': 80, 'bottom': 80},
            padding=25,
            title_size=20,
            subtitle_size=16,
            label_size=14,
            tick_size=12,
            max_data_points=5000,
            point_size=5.0,
            line_width=3.0,
            enable_zoom=True,
            enable_pan=True,
            enable_tooltips=True,
            legend_position='right',
            legend_columns=1,
            show_grid=True,
            grid_density='normal'
        ),
        
        DeviceClass.LARGE_DESKTOP: ResponsiveConfig(
            margins={'left': 120, 'right': 80, 'top': 100, 'bottom': 100},
            padding=30,
            title_size=24,
            subtitle_size=18,
            label_size=16,
            tick_size=14,
            max_data_points=10000,
            point_size=6.0,
            line_width=3.5,
            enable_zoom=True,
            enable_pan=True,
            enable_tooltips=True,
            legend_position='right',
            legend_columns=2,
            show_grid=True,
            grid_density='dense'
        )
    }
    
    def __init__(self):
        """Initialize responsive chart manager."""
        self._current_device_class = DeviceClass.STANDARD_DESKTOP
        self._custom_breakpoints: Dict[str, int] = {}
        self._orientation_listeners: List[callable] = []
    
    def get_device_class(self, width: int, height: int) -> DeviceClass:
        """
        Determine device class based on screen dimensions.
        
        Args:
            width: Screen width in pixels
            height: Screen height in pixels
            
        Returns:
            DeviceClass enum value
        """
        # Check for ultra-wide
        aspect_ratio = width / height if height > 0 else 1
        if aspect_ratio > 2.0:
            return DeviceClass.ULTRA_WIDE
        
        # Check standard breakpoints
        if width < self.BREAKPOINTS['phone']:
            return DeviceClass.PHONE
        elif width < self.BREAKPOINTS['tablet']:
            return DeviceClass.TABLET
        elif width < self.BREAKPOINTS['small_desktop']:
            return DeviceClass.SMALL_DESKTOP
        elif width < self.BREAKPOINTS['standard_desktop']:
            return DeviceClass.STANDARD_DESKTOP
        else:
            return DeviceClass.LARGE_DESKTOP
    
    def get_responsive_config(self, device_class: DeviceClass) -> ResponsiveConfig:
        """
        Get responsive configuration for device class.
        
        Args:
            device_class: Device classification
            
        Returns:
            ResponsiveConfig for the device
        """
        # Handle ultra-wide by using large desktop config with modifications
        if device_class == DeviceClass.ULTRA_WIDE:
            config = self.RESPONSIVE_CONFIGS[DeviceClass.LARGE_DESKTOP]
            # Modify for ultra-wide
            config.legend_position = 'right'
            config.margins['left'] = 140
            config.margins['right'] = 140
            return config
        
        return self.RESPONSIVE_CONFIGS.get(device_class, 
                                         self.RESPONSIVE_CONFIGS[DeviceClass.STANDARD_DESKTOP])
    
    def adapt_chart_config(self, base_config: Any, width: int, height: int) -> Any:
        """
        Adapt chart configuration based on screen size.
        
        Args:
            base_config: Base chart configuration
            width: Available width
            height: Available height
            
        Returns:
            Adapted configuration
        """
        device_class = self.get_device_class(width, height)
        responsive_config = self.get_responsive_config(device_class)
        
        logger.debug(f"Adapting chart for {device_class.value}: {width}x{height}")
        
        # Apply responsive settings
        if hasattr(base_config, 'title_font_size'):
            base_config.title_font_size = responsive_config.title_size
        if hasattr(base_config, 'subtitle_font_size'):
            base_config.subtitle_font_size = responsive_config.subtitle_size
        if hasattr(base_config, 'label_font_size'):
            base_config.label_font_size = responsive_config.label_size
        
        # Update data display settings
        if hasattr(base_config, 'line_width'):
            base_config.line_width = responsive_config.line_width
        if hasattr(base_config, 'point_size'):
            base_config.point_size = responsive_config.point_size
        
        # Update interactivity
        if hasattr(base_config, 'enable_zoom'):
            base_config.enable_zoom = responsive_config.enable_zoom
        if hasattr(base_config, 'enable_pan'):
            base_config.enable_pan = responsive_config.enable_pan
        
        # Update legend
        if hasattr(base_config, 'legend_position'):
            base_config.legend_position = responsive_config.legend_position
        
        # Adjust for orientation
        if self._is_portrait(width, height):
            self._adapt_for_portrait(base_config)
        
        return base_config
    
    def calculate_optimal_layout(self, num_charts: int, container_size: QSize) -> List[QRect]:
        """
        Calculate optimal layout for multiple charts.
        
        Args:
            num_charts: Number of charts to display
            container_size: Available container size
            
        Returns:
            List of QRect for each chart position
        """
        width = container_size.width()
        height = container_size.height()
        device_class = self.get_device_class(width, height)
        
        # Determine grid layout based on device class
        if device_class == DeviceClass.PHONE:
            cols = 1
            rows = num_charts
        elif device_class == DeviceClass.TABLET:
            cols = 2 if num_charts > 1 else 1
            rows = (num_charts + cols - 1) // cols
        elif device_class == DeviceClass.ULTRA_WIDE:
            cols = min(4, num_charts)
            rows = (num_charts + cols - 1) // cols
        else:
            # Desktop layouts
            if num_charts <= 2:
                cols = num_charts
                rows = 1
            elif num_charts <= 4:
                cols = 2
                rows = 2
            elif num_charts <= 6:
                cols = 3
                rows = 2
            else:
                cols = 3
                rows = (num_charts + cols - 1) // cols
        
        # Calculate chart positions
        chart_positions = []
        padding = 20
        chart_width = (width - (cols + 1) * padding) // cols
        chart_height = (height - (rows + 1) * padding) // rows
        
        for i in range(num_charts):
            row = i // cols
            col = i % cols
            
            x = padding + col * (chart_width + padding)
            y = padding + row * (chart_height + padding)
            
            chart_positions.append(QRect(x, y, chart_width, chart_height))
        
        return chart_positions
    
    def get_data_density_limit(self, width: int, height: int) -> int:
        """
        Get recommended maximum data points for screen size.
        
        Args:
            width: Screen width
            height: Screen height
            
        Returns:
            Maximum recommended data points
        """
        device_class = self.get_device_class(width, height)
        config = self.get_responsive_config(device_class)
        
        # Adjust based on actual pixels available
        pixels_available = width * height
        base_limit = config.max_data_points
        
        # Scale based on resolution
        if pixels_available < 500000:  # Low res
            return base_limit // 2
        elif pixels_available < 2000000:  # Medium res
            return base_limit
        else:  # High res
            return base_limit * 2
    
    def should_simplify_visuals(self, width: int, height: int) -> bool:
        """
        Determine if visual complexity should be reduced.
        
        Args:
            width: Screen width
            height: Screen height
            
        Returns:
            True if visuals should be simplified
        """
        device_class = self.get_device_class(width, height)
        return device_class in [DeviceClass.PHONE, DeviceClass.TABLET]
    
    def get_touch_target_size(self, width: int, height: int) -> int:
        """
        Get appropriate touch target size for device.
        
        Args:
            width: Screen width
            height: Screen height
            
        Returns:
            Touch target size in pixels
        """
        device_class = self.get_device_class(width, height)
        
        # WCAG 2.1 minimum is 44px
        if device_class == DeviceClass.PHONE:
            return 48  # Larger for phone
        elif device_class == DeviceClass.TABLET:
            return 44  # Standard for tablet
        else:
            return 32  # Smaller for desktop (mouse precision)
    
    def register_orientation_listener(self, callback: callable):
        """Register callback for orientation changes."""
        self._orientation_listeners.append(callback)
    
    def handle_resize(self, old_size: QSize, new_size: QSize):
        """
        Handle window resize events.
        
        Args:
            old_size: Previous size
            new_size: New size
        """
        old_class = self.get_device_class(old_size.width(), old_size.height())
        new_class = self.get_device_class(new_size.width(), new_size.height())
        
        if old_class != new_class:
            logger.info(f"Device class changed from {old_class.value} to {new_class.value}")
            self._current_device_class = new_class
        
        # Check for orientation change
        old_portrait = self._is_portrait(old_size.width(), old_size.height())
        new_portrait = self._is_portrait(new_size.width(), new_size.height())
        
        if old_portrait != new_portrait:
            for listener in self._orientation_listeners:
                listener(new_portrait)
    
    def _is_portrait(self, width: int, height: int) -> bool:
        """Check if orientation is portrait."""
        return height > width
    
    def _adapt_for_portrait(self, config: Any):
        """Adapt configuration for portrait orientation."""
        # Move legend to bottom in portrait
        if hasattr(config, 'legend_position') and config.legend_position == 'right':
            config.legend_position = 'bottom'
        
        # Reduce margins for more chart space
        if hasattr(config, 'margins'):
            config.margins['left'] = int(config.margins['left'] * 0.8)
            config.margins['right'] = int(config.margins['right'] * 0.8)


class FluidChartContainer:
    """Container that provides fluid responsiveness for charts."""
    
    def __init__(self, responsive_manager: ResponsiveChartManager):
        """Initialize fluid container."""
        self.responsive_manager = responsive_manager
        self._min_chart_size = QSize(300, 200)
        self._max_chart_size = QSize(1200, 800)
        self._aspect_ratio = 16 / 9
    
    def calculate_fluid_size(self, container_size: QSize, 
                           preferred_aspect_ratio: float = None) -> QSize:
        """
        Calculate fluid size that fits container while maintaining aspect ratio.
        
        Args:
            container_size: Available container size
            preferred_aspect_ratio: Preferred width/height ratio
            
        Returns:
            Calculated chart size
        """
        if preferred_aspect_ratio:
            self._aspect_ratio = preferred_aspect_ratio
        
        # Start with container size
        width = container_size.width()
        height = container_size.height()
        
        # Apply aspect ratio constraint
        if width / height > self._aspect_ratio:
            # Container is wider than desired ratio
            width = int(height * self._aspect_ratio)
        else:
            # Container is taller than desired ratio
            height = int(width / self._aspect_ratio)
        
        # Apply size constraints
        width = max(self._min_chart_size.width(), 
                   min(width, self._max_chart_size.width()))
        height = max(self._min_chart_size.height(), 
                    min(height, self._max_chart_size.height()))
        
        return QSize(width, height)
    
    def get_responsive_spacing(self, container_size: QSize) -> Dict[str, int]:
        """Get responsive spacing values based on container size."""
        device_class = self.responsive_manager.get_device_class(
            container_size.width(), container_size.height())
        
        base_spacing = {
            DeviceClass.PHONE: 8,
            DeviceClass.TABLET: 12,
            DeviceClass.SMALL_DESKTOP: 16,
            DeviceClass.STANDARD_DESKTOP: 20,
            DeviceClass.LARGE_DESKTOP: 24
        }
        
        spacing = base_spacing.get(device_class, 20)
        
        return {
            'small': spacing // 2,
            'medium': spacing,
            'large': spacing * 2,
            'extra_large': spacing * 3
        }