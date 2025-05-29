"""Dashboard customization with drag-and-drop support."""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, 
    QLabel, QFrame, QGridLayout, QSizePolicy
)
from PyQt6.QtCore import (
    Qt, QMimeData, QPoint, pyqtSignal, 
    QPropertyAnimation, QRect, QEasingCurve
)
from PyQt6.QtGui import (
    QDrag, QPainter, QPixmap, QColor, 
    QPen, QBrush, QFont
)
from typing import Optional, Dict, List
import json
import logging

from .dashboard_models import GridSpec, ChartConfig

logger = logging.getLogger(__name__)


class DraggableChartWidget(QFrame):
    """A draggable chart widget for dashboard customization."""
    
    # Signals
    position_changed = pyqtSignal(str, GridSpec)  # chart_id, new_position
    remove_requested = pyqtSignal(str)  # chart_id
    
    def __init__(self, chart_id: str, chart_widget: QWidget, 
                 grid_spec: GridSpec, parent=None):
        super().__init__(parent)
        self.chart_id = chart_id
        self.chart_widget = chart_widget
        self.grid_spec = grid_spec
        self._drag_start_position = None
        self._is_dragging = False
        
        self._setup_ui()
        
    def _setup_ui(self):
        """Setup the draggable widget UI."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Header for dragging
        self.header = QFrame()
        self.header.setFixedHeight(30)
        self.header.setStyleSheet("""
            QFrame {
                background-color: #F5E6D3;
                border: 1px solid #D4B5A0;
                border-radius: 4px 4px 0 0;
            }
        """)
        self.header.setCursor(Qt.CursorShape.OpenHandCursor)
        
        header_layout = QHBoxLayout(self.header)
        header_layout.setContentsMargins(8, 4, 8, 4)
        
        # Drag handle icon
        drag_icon = QLabel("☰")
        drag_icon.setStyleSheet("color: #8B6F47; font-size: 16px;")
        header_layout.addWidget(drag_icon)
        
        # Chart title
        self.title_label = QLabel(self.chart_id)
        self.title_label.setStyleSheet("color: #333; font-weight: bold;")
        header_layout.addWidget(self.title_label)
        header_layout.addStretch()
        
        # Remove button
        remove_btn = QPushButton("×")
        remove_btn.setFixedSize(20, 20)
        remove_btn.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                border: none;
                color: #666;
                font-size: 18px;
                font-weight: bold;
            }
            QPushButton:hover {
                color: #FF6B6B;
            }
        """)
        remove_btn.clicked.connect(lambda: self.remove_requested.emit(self.chart_id))
        header_layout.addWidget(remove_btn)
        
        layout.addWidget(self.header)
        layout.addWidget(self.chart_widget)
        
        # Set frame style
        self.setFrameStyle(QFrame.Shape.Box)
        self.setStyleSheet("""
            DraggableChartWidget {
                background-color: white;
                border: 2px solid transparent;
                border-radius: 4px;
            }
            DraggableChartWidget:hover {
                border: 2px solid #FFD166;
            }
        """)
        
    def mousePressEvent(self, event):
        """Handle mouse press for drag initiation."""
        if event.button() == Qt.MouseButton.LeftButton:
            # Check if click is on header
            if self.header.geometry().contains(event.pos()):
                self._drag_start_position = event.pos()
                self.header.setCursor(Qt.CursorShape.ClosedHandCursor)
                
    def mouseMoveEvent(self, event):
        """Handle mouse move for dragging."""
        if event.buttons() == Qt.MouseButton.LeftButton and self._drag_start_position:
            distance = (event.pos() - self._drag_start_position).manhattanLength()
            if distance >= 10:  # Start drag after minimum distance
                self._start_drag()
                
    def mouseReleaseEvent(self, event):
        """Handle mouse release."""
        self._drag_start_position = None
        self.header.setCursor(Qt.CursorShape.OpenHandCursor)
        
    def _start_drag(self):
        """Start the drag operation."""
        self._is_dragging = True
        
        # Create drag object
        drag = QDrag(self)
        
        # Create mime data with chart info
        mime_data = QMimeData()
        chart_data = {
            'chart_id': self.chart_id,
            'grid_spec': {
                'row': self.grid_spec.row,
                'col': self.grid_spec.col,
                'row_span': self.grid_spec.row_span,
                'col_span': self.grid_spec.col_span
            }
        }
        mime_data.setText(json.dumps(chart_data))
        drag.setMimeData(mime_data)
        
        # Create drag pixmap
        pixmap = self._create_drag_pixmap()
        drag.setPixmap(pixmap)
        drag.setHotSpot(QPoint(pixmap.width() // 2, pixmap.height() // 2))
        
        # Execute drag
        drag.exec(Qt.DropAction.MoveAction)
        self._is_dragging = False
        
    def _create_drag_pixmap(self) -> QPixmap:
        """Create a pixmap for the drag operation."""
        # Create a semi-transparent version of the widget
        pixmap = QPixmap(self.size())
        pixmap.fill(Qt.GlobalColor.transparent)
        
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # Draw background
        painter.fillRect(pixmap.rect(), QColor(255, 255, 255, 180))
        
        # Draw border
        painter.setPen(QPen(QColor("#FF8C42"), 2))
        painter.drawRect(pixmap.rect().adjusted(1, 1, -1, -1))
        
        # Draw title
        painter.setPen(QColor("#333"))
        painter.setFont(QFont("Arial", 10, QFont.Weight.Bold))
        painter.drawText(pixmap.rect(), Qt.AlignmentFlag.AlignCenter, self.chart_id)
        
        painter.end()
        return pixmap


class DashboardCustomizationPanel(QWidget):
    """Panel for customizing dashboard layout with drag-and-drop."""
    
    # Signals
    layout_changed = pyqtSignal(dict)  # New layout configuration
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.chart_widgets: Dict[str, DraggableChartWidget] = {}
        self.grid_cells: Dict[tuple, QFrame] = {}  # (row, col) -> cell widget
        self.grid_rows = 4
        self.grid_cols = 12
        
        self._setup_ui()
        
    def _setup_ui(self):
        """Setup the customization panel UI."""
        layout = QVBoxLayout(self)
        
        # Grid preview
        self.grid_preview = QWidget()
        self.grid_preview.setMinimumHeight(400)
        self.grid_layout = QGridLayout(self.grid_preview)
        self.grid_layout.setSpacing(4)
        
        # Create grid cells
        self._create_grid_cells()
        
        layout.addWidget(self.grid_preview)
        
        # Control buttons
        controls = QHBoxLayout()
        
        self.save_btn = QPushButton("Save Layout")
        self.save_btn.setStyleSheet("""
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
        """)
        self.save_btn.clicked.connect(self._save_layout)
        
        self.reset_btn = QPushButton("Reset")
        self.reset_btn.setStyleSheet("""
            QPushButton {
                background-color: #95A5A6;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #7F8C8D;
            }
        """)
        self.reset_btn.clicked.connect(self._reset_layout)
        
        controls.addStretch()
        controls.addWidget(self.reset_btn)
        controls.addWidget(self.save_btn)
        
        layout.addLayout(controls)
        
    def _create_grid_cells(self):
        """Create grid cells for drop targets."""
        for row in range(self.grid_rows):
            for col in range(self.grid_cols):
                cell = GridDropZone(row, col)
                cell.chart_dropped.connect(self._handle_chart_drop)
                self.grid_layout.addWidget(cell, row, col)
                self.grid_cells[(row, col)] = cell
                
    def _handle_chart_drop(self, row: int, col: int, chart_data: dict):
        """Handle chart drop on grid cell."""
        chart_id = chart_data['chart_id']
        
        # Update chart position
        if chart_id in self.chart_widgets:
            widget = self.chart_widgets[chart_id]
            old_spec = widget.grid_spec
            
            # Remove from old position
            self._clear_grid_area(old_spec)
            
            # Update to new position
            new_spec = GridSpec(row, col, 
                              old_spec.row_span, 
                              old_spec.col_span)
            widget.grid_spec = new_spec
            
            # Update grid display
            self._update_grid_display()
            
    def _clear_grid_area(self, grid_spec: GridSpec):
        """Clear grid area occupied by a chart."""
        for r in range(grid_spec.row, grid_spec.row + grid_spec.row_span):
            for c in range(grid_spec.col, grid_spec.col + grid_spec.col_span):
                if (r, c) in self.grid_cells:
                    self.grid_cells[(r, c)].set_occupied(False)
                    
    def _update_grid_display(self):
        """Update grid display to show current layout."""
        # Clear all cells
        for cell in self.grid_cells.values():
            cell.set_occupied(False)
            
        # Mark occupied cells
        for widget in self.chart_widgets.values():
            spec = widget.grid_spec
            for r in range(spec.row, spec.row + spec.row_span):
                for c in range(spec.col, spec.col + spec.col_span):
                    if (r, c) in self.grid_cells:
                        self.grid_cells[(r, c)].set_occupied(True)
                        
    def _save_layout(self):
        """Save the current layout configuration."""
        layout_config = {}
        for chart_id, widget in self.chart_widgets.items():
            layout_config[chart_id] = {
                'row': widget.grid_spec.row,
                'col': widget.grid_spec.col,
                'row_span': widget.grid_spec.row_span,
                'col_span': widget.grid_spec.col_span
            }
        
        self.layout_changed.emit(layout_config)
        logger.info(f"Layout saved: {layout_config}")
        
    def _reset_layout(self):
        """Reset to default layout."""
        # This would reset to original positions
        pass


class GridDropZone(QFrame):
    """Drop zone for grid cells."""
    
    chart_dropped = pyqtSignal(int, int, dict)  # row, col, chart_data
    
    def __init__(self, row: int, col: int, parent=None):
        super().__init__(parent)
        self.row = row
        self.col = col
        self._is_occupied = False
        self._is_hover = False
        
        self.setAcceptDrops(True)
        self.setMinimumSize(40, 40)
        self._update_style()
        
    def set_occupied(self, occupied: bool):
        """Set whether this cell is occupied."""
        self._is_occupied = occupied
        self._update_style()
        
    def _update_style(self):
        """Update cell style based on state."""
        if self._is_occupied:
            color = "#FFE66D"  # Yellow for occupied
        elif self._is_hover:
            color = "#4ECDC4"  # Teal for hover
        else:
            color = "#E8E8E8"  # Light gray for empty
            
        self.setStyleSheet(f"""
            GridDropZone {{
                background-color: {color};
                border: 1px solid #CCC;
                border-radius: 2px;
            }}
        """)
        
    def dragEnterEvent(self, event):
        """Handle drag enter."""
        if event.mimeData().hasText():
            event.acceptProposedAction()
            self._is_hover = True
            self._update_style()
            
    def dragLeaveEvent(self, event):
        """Handle drag leave."""
        self._is_hover = False
        self._update_style()
        
    def dropEvent(self, event):
        """Handle drop event."""
        if event.mimeData().hasText():
            try:
                chart_data = json.loads(event.mimeData().text())
                self.chart_dropped.emit(self.row, self.col, chart_data)
                event.acceptProposedAction()
            except json.JSONDecodeError:
                logger.error("Invalid drop data")
        
        self._is_hover = False
        self._update_style()