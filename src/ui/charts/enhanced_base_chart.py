"""Enhanced base chart integrating all visualization architecture components."""

from typing import Dict, Any, Optional, List, Tuple
from abc import ABC, abstractmethod
import pandas as pd
from PyQt6.QtWidgets import QWidget
from PyQt6.QtCore import pyqtSignal, QSize, QTimer
from dataclasses import dataclass

from .base_chart import BaseChart as LegacyBaseChart
from .chart_renderer_factory import ChartRendererFactory, ChartRenderer
from .chart_performance_optimizer import ChartPerformanceOptimizer, PerformanceMetrics
from .chart_accessibility_manager import ChartAccessibilityManager, AccessibilityReport
from .responsive_chart_manager import ResponsiveChartManager, DeviceClass
from .wsj_style_manager import WSJStyleManager
from .interactions.chart_interaction_manager import ChartInteractionManager
from ...utils.logging_config import get_logger

logger = get_logger(__name__)


@dataclass
class EnhancedChartConfig:
    """Enhanced configuration incorporating all architectural components."""
    # Base configuration
    title: str = ""
    subtitle: str = ""
    x_label: str = ""
    y_label: str = ""
    
    # Rendering
    renderer_type: str = "auto"  # auto, matplotlib, qpainter, pyqtgraph, plotly
    render_quality: str = "balanced"  # performance, balanced, quality
    
    # Performance
    enable_optimization: bool = True
    max_data_points: Optional[int] = None
    enable_caching: bool = True
    progressive_loading: bool = True
    
    # Accessibility
    enforce_wcag_aa: bool = True
    high_contrast_mode: bool = False
    enable_sonification: bool = False
    screen_reader_verbose: bool = True
    
    # Responsiveness
    fluid_layout: bool = True
    adapt_to_device: bool = True
    min_size: QSize = QSize(300, 200)
    max_size: Optional[QSize] = None
    
    # Styling
    use_wsj_style: bool = True
    theme_name: str = "warm"  # warm, cool, monochrome, high_contrast
    custom_colors: Optional[Dict[str, str]] = None
    
    # Interactions
    enable_interactions: bool = True
    enable_zoom: bool = True
    enable_pan: bool = True
    enable_selection: bool = True
    enable_tooltips: bool = True
    enable_keyboard_nav: bool = True
    enable_drill_down: bool = True
    enable_crossfilter: bool = True


class EnhancedBaseChart(QWidget, ABC):
    """
    Enhanced base chart class integrating all architectural components.
    
    This class provides:
    - Multiple rendering backends via ChartRendererFactory
    - Performance optimization for large datasets
    - WCAG 2.1 AA accessibility compliance
    - Responsive design across all device types
    - WSJ-inspired styling
    """
    
    # Signals
    dataChanged = pyqtSignal()
    renderComplete = pyqtSignal(float)  # Render time in ms
    accessibilityReport = pyqtSignal(AccessibilityReport)
    performanceReport = pyqtSignal(PerformanceMetrics)
    deviceClassChanged = pyqtSignal(DeviceClass)
    
    def __init__(self, config: Optional[EnhancedChartConfig] = None,
                 parent: Optional[QWidget] = None):
        """Initialize enhanced base chart."""
        super().__init__(parent)
        
        # Configuration
        self.config = config or EnhancedChartConfig()
        
        # Core components
        self._renderer_factory = ChartRendererFactory()
        self._performance_optimizer = ChartPerformanceOptimizer()
        self._accessibility_manager = ChartAccessibilityManager()
        self._responsive_manager = ResponsiveChartManager()
        self._style_manager = WSJStyleManager()
        self._interaction_manager = ChartInteractionManager(self) if self.config.enable_interactions else None
        
        # State
        self._data: Optional[pd.DataFrame] = None
        self._optimized_data: Optional[pd.DataFrame] = None
        self._current_renderer: Optional[ChartRenderer] = None
        self._render_widget: Optional[QWidget] = None
        self._last_render_time: float = 0.0
        self._device_class: Optional[DeviceClass] = None
        
        # Setup
        self._setup_chart()
        self._setup_responsive_behavior()
        
        # Performance monitoring
        self._performance_timer = QTimer()
        self._performance_timer.timeout.connect(self._update_performance_metrics)
        self._performance_timer.start(5000)  # Update every 5 seconds
    
    def _setup_chart(self):
        """Setup initial chart configuration."""
        # Apply size constraints
        self.setMinimumSize(self.config.min_size)
        if self.config.max_size:
            self.setMaximumSize(self.config.max_size)
        
        # Determine initial renderer
        self._select_renderer()
        
        # Apply initial theme
        self._apply_theme()
    
    def _setup_responsive_behavior(self):
        """Setup responsive behavior monitoring."""
        # Register for orientation changes
        self._responsive_manager.register_orientation_listener(
            self._handle_orientation_change)
        
        # Initial device class
        self._update_device_class()
    
    def set_data(self, data: pd.DataFrame, **kwargs):
        """
        Set chart data with automatic optimization.
        
        Args:
            data: Input dataframe
            **kwargs: Additional parameters for specific chart types
        """
        self._data = data
        
        # Optimize if enabled
        if self.config.enable_optimization and data is not None:
            self._optimize_data()
        else:
            self._optimized_data = data
        
        # Update interaction manager with new data
        if self._interaction_manager and self._optimized_data is not None:
            self._update_interaction_data()
        
        self.dataChanged.emit()
        self._render_chart()
    
    def _optimize_data(self):
        """Optimize data based on current context."""
        if self._data is None:
            return
        
        # Get viewport for adaptive sampling
        viewport = self._get_current_viewport()
        
        # Get device-appropriate data limit
        data_limit = self._responsive_manager.get_data_density_limit(
            self.width(), self.height())
        
        if self.config.max_data_points:
            data_limit = min(data_limit, self.config.max_data_points)
        
        # Optimize data
        self._optimized_data = self._performance_optimizer.optimize_data(
            self._data,
            chart_type=self.get_chart_type(),
            viewport=viewport,
            quality=self.config.render_quality
        )
        
        logger.debug(f"Optimized {len(self._data)} to {len(self._optimized_data)} points")
    
    def _select_renderer(self):
        """Select appropriate renderer based on requirements."""
        if self.config.renderer_type != "auto":
            # Use specified renderer
            self._current_renderer = self._renderer_factory.create_renderer(
                self.config.renderer_type)
        else:
            # Auto-select based on requirements
            requirements = self._get_renderer_requirements()
            self._current_renderer = self._renderer_factory.get_optimal_renderer(
                requirements)
        
        logger.info(f"Selected renderer: {type(self._current_renderer).__name__}")
    
    def _get_renderer_requirements(self) -> Dict[str, bool]:
        """Determine renderer requirements based on context."""
        return {
            'real_time': self.requires_real_time(),
            'interactive': self.requires_interactivity(),
            'publication_quality': self.config.render_quality == 'quality',
            'performance': self.config.render_quality == 'performance',
            'scientific': self.is_scientific_chart(),
            'web_export': False  # Could be determined from export requirements
        }
    
    def _render_chart(self):
        """Render chart with current renderer."""
        if self._optimized_data is None or self._current_renderer is None:
            return
        
        import time
        start_time = time.time()
        
        # Adapt configuration for current device
        adapted_config = self._adapt_config_for_device()
        
        # Check accessibility before rendering
        if self.config.enforce_wcag_aa:
            self._ensure_accessibility(adapted_config)
        
        # Create render widget
        self._render_widget = self._current_renderer.render(
            self._optimized_data,
            adapted_config,
            self._get_current_theme()
        )
        
        # Apply to layout
        self._apply_render_widget()
        
        # Calculate render time
        self._last_render_time = (time.time() - start_time) * 1000
        self.renderComplete.emit(self._last_render_time)
        
        # Update accessibility report
        self._generate_accessibility_report()
    
    def _adapt_config_for_device(self):
        """Adapt configuration for current device."""
        if not self.config.adapt_to_device:
            return self.config
        
        # Create a copy of config
        import copy
        adapted = copy.deepcopy(self.config)
        
        # Apply responsive adaptations
        self._responsive_manager.adapt_chart_config(
            adapted, self.width(), self.height())
        
        return adapted
    
    def _ensure_accessibility(self, config):
        """Ensure configuration meets accessibility standards."""
        theme = self._get_current_theme()
        
        # Enhance configuration for accessibility
        self._accessibility_manager.enhance_config(config, theme)
        
        # Check compliance
        report = self._accessibility_manager.check_accessibility_compliance(
            config, theme)
        
        if not report.compliant and self.config.enforce_wcag_aa:
            logger.warning(f"Accessibility issues: {', '.join(report.issues)}")
            # Apply suggestions automatically
            for suggestion in report.suggestions:
                logger.info(f"Applying: {suggestion}")
    
    def _apply_theme(self):
        """Apply current theme settings."""
        if self.config.use_wsj_style:
            # WSJ style overrides theme
            self._apply_wsj_style()
        elif self.config.high_contrast_mode:
            # High contrast mode
            self._apply_high_contrast_theme()
        else:
            # Standard theme
            self._apply_standard_theme()
    
    def _apply_wsj_style(self):
        """Apply WSJ-inspired styling."""
        # This would integrate with the WSJStyleManager
        logger.debug("Applying WSJ style")
    
    def _apply_render_widget(self):
        """Apply rendered widget to the chart."""
        # This would handle layout management
        # For now, simplified implementation
        if self._render_widget and self.layout():
            # Clear existing widgets
            while self.layout().count():
                item = self.layout().takeAt(0)
                if item.widget():
                    item.widget().deleteLater()
            
            # Add new widget
            self.layout().addWidget(self._render_widget)
    
    def resizeEvent(self, event):
        """Handle resize events."""
        super().resizeEvent(event)
        
        # Update device class
        old_device_class = self._device_class
        self._update_device_class()
        
        if old_device_class != self._device_class:
            self.deviceClassChanged.emit(self._device_class)
        
        # Handle responsive changes
        self._responsive_manager.handle_resize(
            event.oldSize(), event.size())
        
        # Re-optimize and re-render if needed
        if self.config.fluid_layout and self._data is not None:
            self._optimize_data()
            self._render_chart()
    
    def _update_device_class(self):
        """Update current device class."""
        self._device_class = self._responsive_manager.get_device_class(
            self.width(), self.height())
    
    def _handle_orientation_change(self, is_portrait: bool):
        """Handle orientation changes."""
        logger.debug(f"Orientation changed to {'portrait' if is_portrait else 'landscape'}")
        
        # Re-render with new orientation
        if self._data is not None:
            self._render_chart()
    
    def _update_performance_metrics(self):
        """Update and emit performance metrics."""
        if self._optimized_data is None:
            return
        
        metrics = PerformanceMetrics(
            data_points=len(self._optimized_data),
            render_time_ms=self._last_render_time,
            memory_usage_mb=self._estimate_memory_usage(),
            fps=self._calculate_fps(),
            optimization_applied=self._get_applied_optimizations()
        )
        
        self.performanceReport.emit(metrics)
        
        # Get optimization suggestions
        suggestions = self._performance_optimizer.get_optimization_suggestions(metrics)
        if suggestions:
            logger.info(f"Performance suggestions: {'; '.join(suggestions)}")
    
    def _generate_accessibility_report(self):
        """Generate and emit accessibility report."""
        if not hasattr(self, '_accessibility_manager'):
            return
        
        report = self._accessibility_manager.check_accessibility_compliance(
            self.config, self._get_current_theme())
        
        self.accessibilityReport.emit(report)
    
    def export(self, format: str, path: str, dpi: Optional[int] = None) -> bool:
        """
        Export chart to file.
        
        Args:
            format: Export format (png, pdf, svg, etc.)
            path: Output file path
            dpi: Resolution for raster formats
            
        Returns:
            Success status
        """
        if self._current_renderer and self._render_widget:
            export_dpi = dpi or self.config.export_dpi or 300
            return self._current_renderer.export(
                self._render_widget, format, path, export_dpi)
        return False
    
    def get_accessibility_description(self) -> str:
        """Get accessibility description for screen readers."""
        if self._data is None:
            return "Empty chart"
        
        data_summary = self._get_data_summary()
        return self._accessibility_manager.generate_aria_description(
            self.get_chart_type(), data_summary)
    
    def enable_high_contrast_mode(self, enabled: bool = True):
        """Toggle high contrast mode."""
        self.config.high_contrast_mode = enabled
        self._apply_theme()
        
        if self._data is not None:
            self._render_chart()
    
    def set_renderer(self, renderer_type: str):
        """Change renderer type."""
        self.config.renderer_type = renderer_type
        self._select_renderer()
        
        if self._data is not None:
            self._render_chart()
    
    # Interaction methods
    def _update_interaction_data(self):
        """Update interaction manager with chart data."""
        if not self._interaction_manager or self._optimized_data is None:
            return
            
        # Convert DataFrame to interaction format
        interaction_data = self._convert_to_interaction_format(self._optimized_data)
        self._interaction_manager.set_chart_data(interaction_data)
        
        # Connect interaction signals
        self._connect_interaction_signals()
    
    def _convert_to_interaction_format(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Convert DataFrame to format expected by interaction manager."""
        # This is a basic implementation - subclasses can override for specific needs
        points = []
        
        # Assume first column is X (time/index) and second is Y (value)
        if len(df.columns) >= 2:
            x_col = df.columns[0]
            y_col = df.columns[1]
            
            for idx, row in df.iterrows():
                point = {
                    'index': idx,
                    'x': row[x_col],
                    'y': row[y_col],
                    'value': row[y_col],
                    'timestamp': str(row[x_col]) if pd.api.types.is_datetime64_any_dtype(df[x_col]) else None,
                    'metric': y_col,
                    'unit': self._get_unit_for_metric(y_col)
                }
                
                # Add additional columns as metadata
                for col in df.columns[2:]:
                    point[col] = row[col]
                    
                points.append(point)
        
        # Calculate bounds
        if points:
            x_values = [p['x'] for p in points]
            y_values = [p['y'] for p in points]
            bounds = {
                'x_min': min(x_values),
                'x_max': max(x_values),
                'y_min': min(y_values),
                'y_max': max(y_values)
            }
        else:
            bounds = {'x_min': 0, 'x_max': 1, 'y_min': 0, 'y_max': 1}
        
        return {
            'points': points,
            'bounds': bounds,
            'metadata': {
                'chart_type': self.get_chart_type(),
                'title': self.config.title,
                'x_label': self.config.x_label,
                'y_label': self.config.y_label
            }
        }
    
    def _get_unit_for_metric(self, metric: str) -> str:
        """Get unit for a metric - override in subclasses."""
        # Common health metric units
        unit_map = {
            'steps': 'steps',
            'distance': 'km',
            'calories': 'kcal',
            'heart_rate': 'bpm',
            'weight': 'kg',
            'sleep': 'hours'
        }
        
        metric_lower = metric.lower()
        for key, unit in unit_map.items():
            if key in metric_lower:
                return unit
                
        return ''
    
    def _connect_interaction_signals(self):
        """Connect interaction manager signals to chart handlers."""
        if not self._interaction_manager:
            return
            
        # Disconnect any existing connections
        try:
            self._interaction_manager.zoom_changed.disconnect()
            self._interaction_manager.range_selected.disconnect()
            self._interaction_manager.point_hovered.disconnect()
        except:
            pass
            
        # Connect new handlers
        self._interaction_manager.zoom_changed.connect(self._handle_zoom_changed)
        self._interaction_manager.range_selected.connect(self._handle_range_selected)
        self._interaction_manager.point_hovered.connect(self._handle_point_hovered)
        
        if self.config.enable_drill_down:
            self._interaction_manager.drill_down_requested.connect(self._handle_drill_down)
            
        if self.config.enable_crossfilter:
            self._interaction_manager.crossfilter_updated.connect(self._handle_crossfilter)
    
    def _handle_zoom_changed(self, zoom_level: float, center: Any):
        """Handle zoom change from interaction manager."""
        logger.debug(f"Zoom changed: {zoom_level} at {center}")
        # Re-render with new zoom level
        self._render_chart()
    
    def _handle_range_selected(self, start: float, end: float):
        """Handle range selection from interaction manager."""
        logger.debug(f"Range selected: {start} to {end}")
        # Filter data to selected range
        if self._data is not None and len(self._data) > 0:
            # Assume first column is the index/time column
            index_col = self._data.columns[0]
            mask = (self._data[index_col] >= start) & (self._data[index_col] <= end)
            filtered_data = self._data[mask]
            
            # Re-render with filtered data
            self.set_data(filtered_data)
    
    def _handle_point_hovered(self, index: int, data: Dict[str, Any]):
        """Handle point hover from interaction manager."""
        # Tooltip is handled by the interaction manager itself
        pass
    
    def _handle_drill_down(self, target_view: str, context: Dict[str, Any]):
        """Handle drill-down request."""
        logger.info(f"Drill-down requested: {target_view}")
        # This would typically emit a signal for the parent widget to handle
        # For now, just log it
    
    def _handle_crossfilter(self, filter_id: str, filter_value: Any):
        """Handle crossfilter update."""
        logger.debug(f"Crossfilter updated: {filter_id} = {filter_value}")
        # This would typically update the chart based on the filter
        # For now, just log it
    
    # Interaction API methods
    def enable_interactions(self, enable: bool = True):
        """Enable or disable interactions."""
        if self._interaction_manager:
            if enable:
                self._interaction_manager.enable_interactions()
            else:
                self._interaction_manager.disable_interactions()
    
    def set_zoom_level(self, level: float):
        """Set zoom level programmatically."""
        if self._interaction_manager:
            self._interaction_manager.zoom_controller.zoom_to_level(level)
    
    def reset_view(self):
        """Reset chart view to default."""
        if self._interaction_manager:
            self._interaction_manager.zoom_controller.reset_zoom()
            # Re-render with full data
            if self._data is not None:
                self.set_data(self._data)
    
    def screen_to_data(self, screen_pos: Any) -> Any:
        """Convert screen coordinates to data coordinates."""
        # This is a placeholder - subclasses should implement based on their rendering
        return screen_pos
    
    def data_to_screen(self, data_pos: Any) -> Any:
        """Convert data coordinates to screen coordinates."""
        # This is a placeholder - subclasses should implement based on their rendering
        return data_pos
    
    # Abstract methods to be implemented by subclasses
    @abstractmethod
    def get_chart_type(self) -> str:
        """Get the type of chart (line, bar, scatter, etc.)."""
        pass
    
    @abstractmethod
    def requires_real_time(self) -> bool:
        """Check if chart requires real-time updates."""
        pass
    
    @abstractmethod
    def requires_interactivity(self) -> bool:
        """Check if chart requires interactivity."""
        pass
    
    @abstractmethod
    def is_scientific_chart(self) -> bool:
        """Check if chart is for scientific visualization."""
        pass
    
    @abstractmethod
    def _get_current_viewport(self) -> Optional[Tuple[float, float, float, float]]:
        """Get current viewport bounds for adaptive sampling."""
        pass
    
    @abstractmethod
    def _get_data_summary(self) -> Dict[str, Any]:
        """Get summary of current data for accessibility."""
        pass
    
    @abstractmethod
    def _get_current_theme(self) -> Any:
        """Get current theme object."""
        pass
    
    # Helper methods
    def _estimate_memory_usage(self) -> float:
        """Estimate current memory usage in MB."""
        if self._optimized_data is None:
            return 0.0
        
        return self._optimized_data.memory_usage(deep=True).sum() / 1024 / 1024
    
    def _calculate_fps(self) -> float:
        """Calculate current FPS based on render time."""
        if self._last_render_time > 0:
            return 1000.0 / self._last_render_time
        return 60.0
    
    def _get_applied_optimizations(self) -> List[str]:
        """Get list of applied optimizations."""
        optimizations = []
        
        if self._data is not None and self._optimized_data is not None:
            if len(self._optimized_data) < len(self._data):
                optimizations.append('downsampling')
        
        if self.config.enable_caching:
            optimizations.append('caching')
        
        if self.config.progressive_loading:
            optimizations.append('progressive_loading')
        
        return optimizations
    
    def _apply_standard_theme(self):
        """Apply standard theme based on config."""
        # Implementation would apply the selected theme
        pass
    
    def _apply_high_contrast_theme(self):
        """Apply high contrast theme."""
        # Implementation would use accessibility manager's high contrast theme
        pass
    
    def cleanup(self):
        """Clean up resources."""
        if hasattr(self, '_performance_optimizer'):
            self._performance_optimizer.cleanup()
        
        if hasattr(self, '_performance_timer'):
            self._performance_timer.stop()