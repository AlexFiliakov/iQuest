"""Example of using the multi-metric dashboard layout system."""

import sys

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QApplication, QComboBox, QMainWindow, QPushButton, QVBoxLayout, QWidget

# Add src to path for imports
sys.path.append('../src')

from ui.charts.base_chart import BaseChart
from ui.dashboards import (
    DashboardInteractionCoordinator,
    DashboardPersistence,
    HealthDashboardTemplates,
    ResponsiveGridManager,
    WSJDashboardLayout,
)


class DemoChart(BaseChart):
    """Simple demo chart for testing dashboard layouts."""
    
    def __init__(self, title: str, color: str = "#4ECDC4", parent=None):
        super().__init__(parent)
        self.title = title
        self.color = color
        self._setup_demo_ui()
        
    def _setup_demo_ui(self):
        """Create a simple demo chart visualization."""
        layout = QVBoxLayout(self)
        
        # Title
        title_label = QLabel(self.title)
        title_label.setStyleSheet(f"""
            QLabel {{
                font-size: 16px;
                font-weight: bold;
                color: #333;
                padding: 10px;
            }}
        """)
        layout.addWidget(title_label)
        
        # Placeholder for chart content
        chart_area = QWidget()
        chart_area.setStyleSheet(f"""
            QWidget {{
                background-color: {self.color};
                border-radius: 8px;
                min-height: 150px;
            }}
        """)
        layout.addWidget(chart_area, 1)
        
        # Add some interaction
        chart_area.mousePressEvent = lambda e: self.clicked.emit()


class DashboardDemoWindow(QMainWindow):
    """Demo window showing dashboard layout functionality."""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Health Dashboard Layout Demo")
        self.setGeometry(100, 100, 1400, 900)
        
        # Create central widget
        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)
        
        # Controls
        controls = self._create_controls()
        layout.addWidget(controls)
        
        # Dashboard
        self.dashboard = WSJDashboardLayout()
        self.coordinator = DashboardInteractionCoordinator()
        self.persistence = DashboardPersistence()
        
        layout.addWidget(self.dashboard, 1)
        
        # Connect coordinator
        self._setup_coordinator()
        
        # Load default template
        self._load_template('daily_overview')
        
    def _create_controls(self) -> QWidget:
        """Create control panel."""
        controls = QWidget()
        # controls.setMaximumHeight(50)
        layout = QHBoxLayout(controls)
        
        # Template selector
        layout.addWidget(QLabel("Template:"))
        self.template_combo = QComboBox()
        self.template_combo.addItems([
            'daily_overview',
            'weekly_trends',
            'monthly_analysis',
            'workout_focus',
            'health_monitoring'
        ])
        self.template_combo.currentTextChanged.connect(self._load_template)
        layout.addWidget(self.template_combo)
        
        layout.addStretch()
        
        # Save/Load buttons
        save_btn = QPushButton("Save Layout")
        save_btn.clicked.connect(self._save_layout)
        layout.addWidget(save_btn)
        
        load_btn = QPushButton("Load Layout")
        load_btn.clicked.connect(self._load_layout)
        layout.addWidget(load_btn)
        
        # Export button
        export_btn = QPushButton("Export")
        export_btn.clicked.connect(self._export_layout)
        layout.addWidget(export_btn)
        
        return controls
        
    def _setup_coordinator(self):
        """Setup interaction coordinator."""
        # Connect dashboard signals to coordinator
        self.dashboard.time_range_changed.connect(
            self.coordinator.synchronize_time_range
        )
        self.dashboard.chart_focused.connect(
            lambda chart_id: print(f"Chart focused: {chart_id}")
        )
        
        # Connect coordinator signals to dashboard
        self.coordinator.time_range_synchronized.connect(
            lambda start, end: print(f"Time range synchronized: {start} - {end}")
        )
        
    def _load_template(self, template_name: str):
        """Load a dashboard template."""
        template = HealthDashboardTemplates.get_template_by_name(template_name)
        
        # Clear existing charts
        self.dashboard._clear_layout()
        
        # Create demo charts for each config
        for config in template.chart_configs:
            # Create demo chart with the specified type
            color = config.config.get('color', '#4ECDC4')
            chart = DemoChart(config.config.get('title', config.chart_id), color)
            
            # Add to dashboard
            self.dashboard.add_chart(
                config.chart_id,
                chart,
                config.grid_spec,
                config
            )
            
        # Link all charts for synchronized interactions
        chart_ids = list(self.dashboard.charts.keys())
        if len(chart_ids) > 1:
            self.coordinator.create_link_group(chart_ids, template_name)
            
        print(f"Loaded template: {template_name}")
        
    def _save_layout(self):
        """Save current layout."""
        # Get current layout configuration
        layout_config = {}
        for chart_id, config in self.dashboard.chart_configs.items():
            layout_config[chart_id] = {
                'metric_type': config.metric_type,
                'chart_type': config.chart_type,
                'grid_spec': {
                    'row': config.grid_spec.row,
                    'col': config.grid_spec.col,
                    'row_span': config.grid_spec.row_span,
                    'col_span': config.grid_spec.col_span
                },
                'config': config.config
            }
            
        # Save with persistence manager
        layout_name = f"custom_{self.template_combo.currentText()}"
        success = self.persistence.save_layout(
            layout_name,
            layout_config,
            f"Custom layout based on {self.template_combo.currentText()}"
        )
        
        if success:
            print(f"Layout saved: {layout_name}")
        else:
            print("Failed to save layout")
            
    def _load_layout(self):
        """Load a saved layout."""
        # For demo, load the most recent custom layout
        layouts = self.persistence.list_layouts()
        custom_layouts = [l for l in layouts if l['name'].startswith('custom_')]
        
        if custom_layouts:
            latest = custom_layouts[-1]
            layout_data = self.persistence.load_layout(latest['name'])
            if layout_data:
                print(f"Loaded layout: {latest['name']}")
                # Would recreate charts from layout_data here
        else:
            print("No custom layouts found")
            
    def _export_layout(self):
        """Export current layout for sharing."""
        layout_name = f"custom_{self.template_combo.currentText()}"
        export_string = self.persistence.export_layout(layout_name)
        
        if export_string:
            print(f"Exported layout (copy this string):")
            print(export_string[:100] + "...")  # Show truncated for demo
            # In real app, would copy to clipboard or show in dialog
        else:
            print("Failed to export layout")
            
    def resizeEvent(self, event):
        """Handle window resize."""
        super().resizeEvent(event)
        # Dashboard handles its own responsive behavior


def main():
    """Run the dashboard demo."""
    app = QApplication(sys.argv)
    
    # Apply app-wide styling
    app.setStyleSheet("""
        QMainWindow {
            background-color: #F5F5F5;
        }
        QPushButton {
            background-color: #4ECDC4;
            color: white;
            border: none;
            padding: 8px 16px;
            border-radius: 4px;
            font-weight: bold;
        }
        QPushButton:hover {
            background-color: #45B7D1;
        }
        QComboBox {
            padding: 6px;
            border: 1px solid #D4B5A0;
            border-radius: 4px;
            background-color: white;
        }
    """)
    
    window = DashboardDemoWindow()
    window.show()
    
    sys.exit(app.exec())


if __name__ == "__main__":
    # Add missing import
    from PyQt6.QtWidgets import QHBoxLayout, QLabel
    main()