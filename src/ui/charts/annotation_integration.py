"""Integration layer for adding annotations to existing chart types"""

from typing import Optional, List, Dict, Any, Callable
import pandas as pd
from PyQt6.QtCore import QObject, pyqtSignal, QPointF
from PyQt6.QtWidgets import QWidget

from ...analytics.health_annotation_system import HealthAnnotationSystem
from ...analytics.annotation_models import AnnotationType, HealthAnnotation
from .annotation_renderer import WSJAnnotationRenderer
from .annotation_layout_manager import AnnotationLayoutManager
from .base_chart import BaseChart


class ChartAnnotationMixin:
    """Mixin to add annotation capabilities to any chart"""
    
    def __init__(self):
        # Initialize annotation components
        self._annotation_system = HealthAnnotationSystem()
        self._annotation_renderer = WSJAnnotationRenderer()
        self._layout_manager = AnnotationLayoutManager()
        
        # Annotation state
        self._annotations_enabled = True
        self._annotations: List[HealthAnnotation] = []
        self._annotation_types = list(AnnotationType)
        
    def enable_annotations(self, enabled: bool = True):
        """Enable or disable annotations"""
        self._annotations_enabled = enabled
        if not enabled:
            self.clear_annotations()
        else:
            self.refresh_annotations()
    
    def set_annotation_types(self, types: List[AnnotationType]):
        """Set which annotation types to display"""
        self._annotation_types = types
        self.refresh_annotations()
    
    def refresh_annotations(self):
        """Refresh annotations based on current data"""
        if not self._annotations_enabled or not hasattr(self, 'data'):
            return
            
        # Generate annotations
        self._annotations = self._annotation_system.generate_annotations(
            data=self.data,
            metric_type=getattr(self, 'metric_type', 'generic'),
            annotation_types=self._annotation_types
        )
        
        # Render annotations
        self._render_annotations()
    
    def _render_annotations(self):
        """Render annotations on the chart"""
        if not hasattr(self, 'scene'):
            return
            
        scene = self.scene()
        
        # Clear existing annotations
        self._annotation_renderer.clear_annotations(scene)
        
        if not self._annotations:
            return
        
        # Get data transformation function
        transform_func = self._get_data_transform_function()
        
        # Render new annotations
        self._annotation_renderer.render_annotations(
            scene=scene,
            annotations=self._annotations,
            data_to_scene_transform=transform_func
        )
    
    def _get_data_transform_function(self) -> Callable:
        """Get function to transform data coordinates to scene coordinates"""
        # This should be implemented by the specific chart class
        if hasattr(self, 'data_to_scene'):
            return self.data_to_scene
        else:
            # Default implementation
            def default_transform(date, value):
                # Simple linear transformation
                x = 0  # Would be calculated based on date
                y = 0  # Would be calculated based on value
                return QPointF(x, y)
            return default_transform
    
    def clear_annotations(self):
        """Clear all annotations"""
        if hasattr(self, 'scene'):
            self._annotation_renderer.clear_annotations(self.scene())
        self._annotations.clear()
    
    def get_annotations(self) -> List[HealthAnnotation]:
        """Get current annotations"""
        return self._annotations.copy()


class AnnotationIntegrator(QObject):
    """Integrates annotation system with existing charts"""
    
    annotation_clicked = pyqtSignal(str, str)  # chart_id, annotation_id
    
    def __init__(self):
        super().__init__()
        self.annotation_system = HealthAnnotationSystem()
        self.registered_charts: Dict[str, QWidget] = {}
        
    def register_chart(self, chart_id: str, chart: QWidget):
        """Register a chart for annotation support"""
        self.registered_charts[chart_id] = chart
        
        # Add annotation capabilities if not already present
        if not hasattr(chart, '_annotation_system'):
            self._add_annotation_support(chart)
    
    def _add_annotation_support(self, chart: QWidget):
        """Add annotation support to a chart"""
        # Inject annotation system
        chart._annotation_system = HealthAnnotationSystem()
        chart._annotation_renderer = WSJAnnotationRenderer()
        chart._layout_manager = AnnotationLayoutManager()
        chart._annotations = []
        
        # Add methods
        chart.refresh_annotations = lambda: self._refresh_chart_annotations(chart)
        chart.clear_annotations = lambda: self._clear_chart_annotations(chart)
        chart.get_annotations = lambda: chart._annotations.copy()
    
    def _refresh_chart_annotations(self, chart: QWidget):
        """Refresh annotations for a specific chart"""
        if not hasattr(chart, 'get_data'):
            return
            
        data = chart.get_data()
        if data is None or data.empty:
            return
            
        # Get metric type
        metric_type = getattr(chart, 'metric_type', 'generic')
        
        # Generate annotations
        annotations = chart._annotation_system.generate_annotations(
            data=data,
            metric_type=metric_type
        )
        
        chart._annotations = annotations
        
        # Render if chart has scene
        if hasattr(chart, 'scene'):
            self._render_chart_annotations(chart)
    
    def _render_chart_annotations(self, chart: QWidget):
        """Render annotations on a chart"""
        scene = chart.scene()
        
        # Get transformation function
        if hasattr(chart, 'data_to_scene'):
            transform = chart.data_to_scene
        else:
            # Create default transform based on chart type
            transform = self._create_default_transform(chart)
        
        # Render annotations
        chart._annotation_renderer.render_annotations(
            scene=scene,
            annotations=chart._annotations,
            data_to_scene_transform=transform
        )
    
    def _clear_chart_annotations(self, chart: QWidget):
        """Clear annotations from a chart"""
        if hasattr(chart, 'scene'):
            chart._annotation_renderer.clear_annotations(chart.scene())
        chart._annotations.clear()
    
    def _create_default_transform(self, chart: QWidget) -> Callable:
        """Create default coordinate transform for chart"""
        def transform(date, value):
            # This would need to be customized based on chart type
            # For now, return a dummy position
            return QPointF(100, 100)
        return transform
    
    def update_all_annotations(self):
        """Update annotations on all registered charts"""
        for chart_id, chart in self.registered_charts.items():
            if hasattr(chart, 'refresh_annotations'):
                chart.refresh_annotations()
    
    def set_global_annotation_types(self, types: List[AnnotationType]):
        """Set annotation types for all charts"""
        for chart in self.registered_charts.values():
            if hasattr(chart, '_annotation_system'):
                # Update annotation types
                chart._annotation_types = types
                chart.refresh_annotations()


def add_annotations_to_chart(chart: BaseChart) -> BaseChart:
    """Factory function to add annotation support to a chart
    
    Args:
        chart: Base chart instance
        
    Returns:
        Chart with annotation capabilities
    """
    # Create annotated version of the chart
    class AnnotatedChart(chart.__class__, ChartAnnotationMixin):
        def __init__(self, *args, **kwargs):
            chart.__class__.__init__(self, *args, **kwargs)
            ChartAnnotationMixin.__init__(self)
            
        def set_data(self, data: pd.DataFrame, **kwargs):
            """Override to add annotation generation"""
            super().set_data(data, **kwargs)
            self.data = data
            if self._annotations_enabled:
                self.refresh_annotations()
        
        def data_to_scene(self, date, value) -> QPointF:
            """Transform data coordinates to scene coordinates"""
            # This needs to be implemented based on specific chart type
            if hasattr(super(), 'data_to_scene'):
                return super().data_to_scene(date, value)
            else:
                # Fallback implementation
                x = self.date_to_x(date) if hasattr(self, 'date_to_x') else 0
                y = self.value_to_y(value) if hasattr(self, 'value_to_y') else 0
                return QPointF(x, y)
    
    # Create new instance with same parameters
    annotated = AnnotatedChart()
    
    # Copy relevant attributes
    for attr in ['title', 'metric_type', 'data']:
        if hasattr(chart, attr):
            setattr(annotated, attr, getattr(chart, attr))
    
    return annotated