"""Annotated chart widget that integrates health insights with visualizations"""

from typing import List, Optional, Dict, Any
import pandas as pd
from PyQt6.QtCore import Qt, pyqtSignal, QPointF
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QCheckBox,
                           QGroupBox, QPushButton, QLabel, QSlider)
from PyQt6.QtGui import QPainter, QPen, QColor

from ...analytics.health_annotation_system import HealthAnnotationSystem
from ...analytics.annotation_models import AnnotationType, HealthAnnotation
from .enhanced_line_chart import EnhancedLineChart
from .annotation_renderer import WSJAnnotationRenderer
from .annotation_layout_manager import AnnotationLayoutManager
from .wsj_style_manager import WSJStyleManager


class AnnotatedHealthChart(QWidget):
    """Health chart with intelligent annotations"""
    
    # Signals
    annotation_clicked = pyqtSignal(str)  # annotation_id
    annotation_types_changed = pyqtSignal(list)  # List[AnnotationType]
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        # Initialize components
        self.annotation_system = HealthAnnotationSystem()
        self.style_manager = WSJStyleManager()
        self.annotation_renderer = WSJAnnotationRenderer(self.style_manager)
        self.layout_manager = AnnotationLayoutManager()
        
        # Chart widget
        self.chart = EnhancedLineChart()
        
        # Annotation settings
        self.enabled_annotation_types = list(AnnotationType)
        self.annotations: List[HealthAnnotation] = []
        self.annotation_positions: Dict[str, Any] = {}
        
        # UI setup
        self._setup_ui()
        self._connect_signals()
    
    def _setup_ui(self):
        """Set up the user interface"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Chart
        layout.addWidget(self.chart)
        
        # Annotation controls
        controls = self._create_annotation_controls()
        layout.addWidget(controls)
    
    def _create_annotation_controls(self) -> QWidget:
        """Create annotation control panel"""
        controls = QGroupBox("Annotation Settings")
        layout = QVBoxLayout(controls)
        
        # Annotation type toggles
        type_label = QLabel("Show Annotations:")
        layout.addWidget(type_label)
        
        type_layout = QHBoxLayout()
        self.type_checkboxes = {}
        
        for ann_type in AnnotationType:
            checkbox = QCheckBox(ann_type.value.capitalize())
            checkbox.setChecked(True)
            checkbox.toggled.connect(lambda: self._on_annotation_types_changed())
            self.type_checkboxes[ann_type] = checkbox
            type_layout.addWidget(checkbox)
        
        layout.addLayout(type_layout)
        
        # Annotation density control
        density_layout = QHBoxLayout()
        density_layout.addWidget(QLabel("Annotation Density:"))
        
        self.density_slider = QSlider(Qt.Orientation.Horizontal)
        self.density_slider.setRange(1, 20)
        self.density_slider.setValue(10)
        self.density_slider.setTickPosition(QSlider.TickPosition.TicksBelow)
        self.density_slider.setTickInterval(5)
        self.density_slider.valueChanged.connect(self._on_density_changed)
        density_layout.addWidget(self.density_slider)
        
        self.density_label = QLabel("10")
        density_layout.addWidget(self.density_label)
        
        layout.addLayout(density_layout)
        
        # Action buttons
        button_layout = QHBoxLayout()
        
        clear_btn = QPushButton("Clear All")
        clear_btn.clicked.connect(self.clear_annotations)
        button_layout.addWidget(clear_btn)
        
        layout.addLayout(button_layout)
        
        return controls
    
    def _connect_signals(self):
        """Connect internal signals"""
        # Connect annotation system signals
        self.annotation_system.annotations_generated.connect(self._on_annotations_generated)
        self.annotation_system.annotation_clicked.connect(self.annotation_clicked.emit)
        
        # Connect renderer signals
        self.annotation_renderer.annotation_clicked.connect(self.annotation_clicked.emit)
    
    def set_data(self, data: pd.DataFrame, metric_type: str):
        """Set chart data and generate annotations
        
        Args:
            data: DataFrame with 'date' and 'value' columns
            metric_type: Type of health metric
        """
        # Set chart data
        self.chart.set_data(data, title=metric_type.replace('_', ' ').title())
        
        # Store data for annotation generation
        self.data = data
        self.metric_type = metric_type
        
        # Annotations will be generated automatically when data changes
    
    def _render_annotations(self):
        """Render annotations on the chart"""
        if not self.annotations:
            return
        
        # Get chart scene
        scene = self.chart.scene()
        
        # Define transform function
        def data_to_scene_transform(date, value):
            # Convert data coordinates to scene coordinates
            # This would use the chart's actual coordinate transformation
            x = self.chart.date_to_x(date)
            y = self.chart.value_to_y(value)
            return QPointF(x, y)
        
        # Optimize annotation layout
        self.annotation_positions = self.layout_manager.optimize_layout(
            annotations=self.annotations,
            data_to_scene_transform=data_to_scene_transform,
            scene_bounds=scene.sceneRect()
        )
        
        # Render annotations with optimized positions
        self.annotation_renderer.render_annotations(
            scene=scene,
            annotations=self.annotations,
            data_to_scene_transform=data_to_scene_transform
        )
        
        # Draw leader lines if needed
        self._draw_leader_lines()
    
    def _draw_leader_lines(self):
        """Draw leader lines for annotations that need them"""
        scene = self.chart.scene()
        
        for ann_id, bounds in self.annotation_positions.items():
            if bounds.needs_leader and bounds.leader_path:
                # Create leader line
                pen = QPen(QColor('#D4B5A0'), 1, Qt.PenStyle.DashLine)
                
                for i in range(len(bounds.leader_path) - 1):
                    scene.addLine(
                        bounds.leader_path[i].x(),
                        bounds.leader_path[i].y(),
                        bounds.leader_path[i + 1].x(),
                        bounds.leader_path[i + 1].y(),
                        pen
                    )
    
    def clear_annotations(self):
        """Clear all annotations from the chart"""
        self.annotations.clear()
        self.annotation_positions.clear()
        self.annotation_renderer.clear_annotations(self.chart.scene())
    
    def _on_annotation_types_changed(self):
        """Handle annotation type toggle changes"""
        enabled_types = [
            ann_type for ann_type, checkbox in self.type_checkboxes.items()
            if checkbox.isChecked()
        ]
        
        # Update visibility of existing annotations
        self.annotation_renderer.update_annotation_visibility(enabled_types)
        
        # Emit signal
        self.annotation_types_changed.emit(enabled_types)
    
    def _on_density_changed(self, value: int):
        """Handle annotation density change"""
        self.density_label.setText(str(value))
        # Refresh annotations with new density
        self.refresh_annotations()
    
    def _on_annotations_generated(self, annotations: List[HealthAnnotation]):
        """Handle annotations generated signal"""
        # Update annotation count in controls
        count_text = f"({len(annotations)} annotations)"
        self.findChild(QGroupBox).setTitle(f"Annotation Settings {count_text}")
    
    def highlight_annotation(self, annotation_id: str):
        """Highlight a specific annotation"""
        self.annotation_renderer.highlight_annotation(annotation_id)
    
    def get_annotation_by_id(self, annotation_id: str) -> Optional[HealthAnnotation]:
        """Get annotation by ID"""
        return self.annotation_system.get_annotation_by_id(annotation_id)
    
    def export_annotations(self) -> List[Dict[str, Any]]:
        """Export annotations as list of dictionaries"""
        return [
            {
                'id': ann.id,
                'type': ann.type.value,
                'date': ann.data_point.isoformat(),
                'value': ann.value,
                'title': ann.title,
                'description': ann.description,
                'priority': ann.priority.value,
                'metadata': ann.metadata
            }
            for ann in self.annotations
        ]


class AnnotationPreferencesWidget(QWidget):
    """Widget for managing annotation preferences"""
    
    preferences_changed = pyqtSignal(dict)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._setup_ui()
    
    def _setup_ui(self):
        """Set up preferences UI"""
        layout = QVBoxLayout(self)
        
        # Annotation type preferences
        type_group = QGroupBox("Annotation Types")
        type_layout = QVBoxLayout(type_group)
        
        self.type_preferences = {}
        for ann_type in AnnotationType:
            pref_layout = QHBoxLayout()
            
            # Enable checkbox
            enable_check = QCheckBox(f"Show {ann_type.value} annotations")
            enable_check.setChecked(True)
            pref_layout.addWidget(enable_check)
            
            # Priority slider
            priority_slider = QSlider(Qt.Orientation.Horizontal)
            priority_slider.setRange(1, 4)
            priority_slider.setValue(2)
            priority_slider.setFixedWidth(100)
            pref_layout.addWidget(QLabel("Priority:"))
            pref_layout.addWidget(priority_slider)
            
            pref_layout.addStretch()
            type_layout.addLayout(pref_layout)
            
            self.type_preferences[ann_type] = {
                'enabled': enable_check,
                'priority': priority_slider
            }
        
        layout.addWidget(type_group)
        
        # Display preferences
        display_group = QGroupBox("Display Settings")
        display_layout = QVBoxLayout(display_group)
        
        self.show_leaders = QCheckBox("Show leader lines")
        self.show_leaders.setChecked(True)
        display_layout.addWidget(self.show_leaders)
        
        self.auto_expand = QCheckBox("Auto-expand on hover")
        self.auto_expand.setChecked(False)
        display_layout.addWidget(self.auto_expand)
        
        self.group_nearby = QCheckBox("Group nearby annotations")
        self.group_nearby.setChecked(True)
        display_layout.addWidget(self.group_nearby)
        
        layout.addWidget(display_group)
        
        # Apply button
        apply_btn = QPushButton("Apply Preferences")
        apply_btn.clicked.connect(self._apply_preferences)
        layout.addWidget(apply_btn)
        
        layout.addStretch()
    
    def _apply_preferences(self):
        """Apply current preferences"""
        prefs = {
            'annotation_types': {},
            'display': {
                'show_leaders': self.show_leaders.isChecked(),
                'auto_expand': self.auto_expand.isChecked(),
                'group_nearby': self.group_nearby.isChecked()
            }
        }
        
        # Collect annotation type preferences
        for ann_type, widgets in self.type_preferences.items():
            prefs['annotation_types'][ann_type.value] = {
                'enabled': widgets['enabled'].isChecked(),
                'priority': widgets['priority'].value()
            }
        
        self.preferences_changed.emit(prefs)
    
    def load_preferences(self, prefs: Dict[str, Any]):
        """Load preferences from dictionary"""
        if 'annotation_types' in prefs:
            for ann_type, widgets in self.type_preferences.items():
                if ann_type.value in prefs['annotation_types']:
                    type_prefs = prefs['annotation_types'][ann_type.value]
                    widgets['enabled'].setChecked(type_prefs.get('enabled', True))
                    widgets['priority'].setValue(type_prefs.get('priority', 2))
        
        if 'display' in prefs:
            display_prefs = prefs['display']
            self.show_leaders.setChecked(display_prefs.get('show_leaders', True))
            self.auto_expand.setChecked(display_prefs.get('auto_expand', False))
            self.group_nearby.setChecked(display_prefs.get('group_nearby', True))