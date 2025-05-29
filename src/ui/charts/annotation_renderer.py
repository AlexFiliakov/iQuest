"""WSJ-styled annotation renderer for health visualizations"""

from typing import List, Dict, Optional, Tuple, Any
import numpy as np
from PyQt6.QtCore import Qt, QPointF, QRectF, pyqtSignal, QObject
from PyQt6.QtGui import QPainter, QBrush, QPen, QFont, QColor, QPainterPath, QPolygonF
from PyQt6.QtWidgets import QGraphicsItem, QGraphicsTextItem, QGraphicsPathItem, QGraphicsScene

from ...analytics.annotation_models import (
    HealthAnnotation, AnnotationType, AnnotationStyle,
    AnomalyAnnotation, AchievementAnnotation, TrendAnnotation,
    InsightAnnotation, MilestoneAnnotation, ComparisonAnnotation,
    GoalAnnotation
)
from .wsj_style_manager import WSJStyleManager


class AnnotationGraphicsItem(QGraphicsItem):
    """Custom graphics item for rendering health annotations"""
    
    def __init__(self, annotation: HealthAnnotation, style_manager: WSJStyleManager):
        super().__init__()
        self.annotation = annotation
        self.style_manager = style_manager
        self.expanded = False
        self.hover = False
        
        # Visual properties
        self.marker_size = 10
        self.padding = 8
        self.corner_radius = 4
        self.text_margin = 4
        
        # Get annotation style
        self.style = self._get_annotation_style()
        
        # Set up interactivity
        self.setAcceptHoverEvents(True)
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsSelectable, True)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        
        # Z-value based on priority
        self.setZValue(100 + annotation.priority.value * 10)
    
    def boundingRect(self) -> QRectF:
        """Calculate bounding rectangle for the annotation"""
        if self.expanded:
            # Include expanded content
            text_rect = self._calculate_expanded_bounds()
            return text_rect.adjusted(-self.padding, -self.padding, 
                                    self.padding, self.padding)
        else:
            # Just the marker with hover area
            size = self.marker_size * (1.5 if self.hover else 1.0)
            return QRectF(-size/2, -size/2, size, size)
    
    def paint(self, painter: QPainter, option, widget):
        """Paint the annotation with WSJ styling"""
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # Draw shadow if needed
        if self.style.shadow and (self.expanded or self.hover):
            self._draw_shadow(painter)
        
        # Draw marker
        self._draw_marker(painter)
        
        # Draw expanded content or hover preview
        if self.expanded:
            self._draw_expanded_content(painter)
        elif self.hover:
            self._draw_hover_preview(painter)
    
    def mousePressEvent(self, event):
        """Handle mouse press to toggle expansion"""
        if event.button() == Qt.MouseButton.LeftButton:
            self.expanded = not self.expanded
            self.prepareGeometryChange()
            self.update()
        super().mousePressEvent(event)
    
    def hoverEnterEvent(self, event):
        """Handle hover enter"""
        self.hover = True
        self.prepareGeometryChange()
        self.update()
        super().hoverEnterEvent(event)
    
    def hoverLeaveEvent(self, event):
        """Handle hover leave"""
        self.hover = False
        self.prepareGeometryChange()
        self.update()
        super().hoverLeaveEvent(event)
    
    def _get_annotation_style(self) -> AnnotationStyle:
        """Get style for this annotation type"""
        # Default styles based on annotation type
        styles = {
            AnnotationType.ACHIEVEMENT: AnnotationStyle(
                marker_symbol='star',
                marker_size=12,
                marker_color='#7CB342',  # Green
                text_color='#7CB342',
                background_color='#F5F9F3',
                border_color='#7CB342',
                font_weight='bold'
            ),
            AnnotationType.ANOMALY: AnnotationStyle(
                marker_symbol='exclamation',
                marker_size=10,
                marker_color='#F4511E',  # Red-orange
                text_color='#F4511E',
                background_color='#FFF5F2',
                border_color='#F4511E',
                font_weight='medium'
            ),
            AnnotationType.TREND: AnnotationStyle(
                marker_symbol='arrow',
                marker_size=10,
                marker_color='#FF8C42',  # Orange
                text_color='#6B4226',
                background_color='#FFF8F3',
                border_color='#FF8C42'
            ),
            AnnotationType.INSIGHT: AnnotationStyle(
                marker_symbol='lightbulb',
                marker_size=10,
                marker_color='#5C6BC0',  # Blue
                text_color='#5C6BC0',
                background_color='#F5F7FA',
                border_color='#5C6BC0'
            ),
            AnnotationType.MILESTONE: AnnotationStyle(
                marker_symbol='trophy',
                marker_size=12,
                marker_color='#FFD166',  # Yellow
                text_color='#6B4226',
                background_color='#FFFCF0',
                border_color='#FFD166',
                font_weight='bold'
            ),
            AnnotationType.COMPARISON: AnnotationStyle(
                marker_symbol='chart',
                marker_size=10,
                marker_color='#6B4226',  # Brown
                text_color='#6B4226',
                background_color='#FAF8F5',
                border_color='#D4B5A0'
            ),
            AnnotationType.GOAL: AnnotationStyle(
                marker_symbol='target',
                marker_size=11,
                marker_color='#7CB342',
                text_color='#7CB342',
                background_color='#F5F9F3',
                border_color='#7CB342'
            )
        }
        
        return styles.get(self.annotation.type, AnnotationStyle())
    
    def _draw_marker(self, painter: QPainter):
        """Draw the annotation marker"""
        # Marker color and size
        color = QColor(self.style.marker_color)
        size = self.style.marker_size
        
        if self.hover or self.expanded:
            color = color.lighter(110)
            size *= 1.2
        
        painter.setBrush(QBrush(color))
        painter.setPen(QPen(color.darker(120), 1.5))
        
        # Draw shape based on marker symbol
        if self.style.marker_symbol == 'star':
            self._draw_star(painter, size)
        elif self.style.marker_symbol == 'exclamation':
            self._draw_exclamation(painter, size)
        elif self.style.marker_symbol == 'arrow':
            self._draw_arrow(painter, size)
        elif self.style.marker_symbol == 'lightbulb':
            self._draw_lightbulb(painter, size)
        elif self.style.marker_symbol == 'trophy':
            self._draw_trophy(painter, size)
        elif self.style.marker_symbol == 'chart':
            self._draw_chart_icon(painter, size)
        elif self.style.marker_symbol == 'target':
            self._draw_target(painter, size)
        else:
            # Default circle
            painter.drawEllipse(QPointF(0, 0), size/2, size/2)
    
    def _draw_star(self, painter: QPainter, size: float):
        """Draw a star shape"""
        star = QPainterPath()
        # Create 5-pointed star
        points = []
        for i in range(10):
            angle = i * 3.14159 / 5
            if i % 2 == 0:
                r = size / 2
            else:
                r = size / 4
            x = r * np.cos(angle - 3.14159/2)
            y = r * np.sin(angle - 3.14159/2)
            points.append(QPointF(x, y))
        
        star.addPolygon(QPolygonF(points))
        painter.drawPath(star)
    
    def _draw_exclamation(self, painter: QPainter, size: float):
        """Draw an exclamation mark"""
        # Draw triangle background
        triangle = QPainterPath()
        triangle.moveTo(0, -size/2)
        triangle.lineTo(-size/2.5, size/2)
        triangle.lineTo(size/2.5, size/2)
        triangle.closeSubpath()
        painter.drawPath(triangle)
        
        # Draw exclamation mark
        painter.setPen(QPen(Qt.GlobalColor.white, size/5))
        painter.drawLine(QPointF(0, -size/4), QPointF(0, size/6))
        painter.drawEllipse(QPointF(0, size/3), size/8, size/8)
    
    def _draw_arrow(self, painter: QPainter, size: float):
        """Draw an arrow for trends"""
        arrow = QPainterPath()
        
        # Determine arrow direction based on trend
        if isinstance(self.annotation, TrendAnnotation):
            if self.annotation.trend_direction.value == "improving":
                # Upward arrow
                arrow.moveTo(0, size/2)
                arrow.lineTo(0, -size/3)
                arrow.lineTo(-size/4, -size/6)
                arrow.moveTo(0, -size/3)
                arrow.lineTo(size/4, -size/6)
            else:
                # Downward arrow
                arrow.moveTo(0, -size/2)
                arrow.lineTo(0, size/3)
                arrow.lineTo(-size/4, size/6)
                arrow.moveTo(0, size/3)
                arrow.lineTo(size/4, size/6)
        else:
            # Default right arrow
            arrow.moveTo(-size/2, 0)
            arrow.lineTo(size/3, 0)
            arrow.lineTo(size/6, -size/4)
            arrow.moveTo(size/3, 0)
            arrow.lineTo(size/6, size/4)
        
        painter.setPen(QPen(QColor(self.style.marker_color), 2))
        painter.drawPath(arrow)
    
    def _draw_lightbulb(self, painter: QPainter, size: float):
        """Draw a lightbulb for insights"""
        # Draw bulb
        painter.drawEllipse(QPointF(0, -size/4), size/3, size/2.5)
        
        # Draw base
        base_rect = QRectF(-size/5, size/6, size/2.5, size/4)
        painter.drawRect(base_rect)
        
        # Draw filament lines
        painter.setPen(QPen(QColor(self.style.marker_color), 1))
        painter.drawLine(QPointF(-size/6, size/6), QPointF(-size/6, size/3))
        painter.drawLine(QPointF(0, size/6), QPointF(0, size/3))
        painter.drawLine(QPointF(size/6, size/6), QPointF(size/6, size/3))
    
    def _draw_trophy(self, painter: QPainter, size: float):
        """Draw a trophy for achievements"""
        # Draw cup
        cup = QPainterPath()
        cup.moveTo(-size/3, -size/3)
        cup.quadTo(-size/2.5, 0, -size/4, size/3)
        cup.lineTo(size/4, size/3)
        cup.quadTo(size/2.5, 0, size/3, -size/3)
        cup.closeSubpath()
        painter.drawPath(cup)
        
        # Draw handles
        painter.drawArc(QRectF(-size/2, -size/4, size/4, size/3), 90*16, 180*16)
        painter.drawArc(QRectF(size/4, -size/4, size/4, size/3), -90*16, 180*16)
    
    def _draw_chart_icon(self, painter: QPainter, size: float):
        """Draw a chart icon for comparisons"""
        # Draw bars
        bar_width = size / 5
        painter.drawRect(QRectF(-size/3, 0, bar_width, size/3))
        painter.drawRect(QRectF(-size/10, -size/4, bar_width, size * 0.55))
        painter.drawRect(QRectF(size/7, -size/6, bar_width, size/2))
    
    def _draw_target(self, painter: QPainter, size: float):
        """Draw a target for goals"""
        # Draw concentric circles
        painter.drawEllipse(QPointF(0, 0), size/2, size/2)
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.drawEllipse(QPointF(0, 0), size/3, size/3)
        painter.setBrush(QBrush(QColor(self.style.marker_color)))
        painter.drawEllipse(QPointF(0, 0), size/6, size/6)
    
    def _draw_shadow(self, painter: QPainter):
        """Draw drop shadow"""
        shadow_color = QColor(0, 0, 0, 30)
        shadow_offset = 2
        
        if self.expanded:
            rect = self._calculate_expanded_bounds()
            shadow_rect = rect.translated(shadow_offset, shadow_offset)
            painter.setBrush(QBrush(shadow_color))
            painter.setPen(Qt.PenStyle.NoPen)
            painter.drawRoundedRect(shadow_rect, self.corner_radius, self.corner_radius)
        else:
            painter.setBrush(QBrush(shadow_color))
            painter.setPen(Qt.PenStyle.NoPen)
            painter.drawEllipse(QPointF(shadow_offset, shadow_offset), 
                              self.marker_size/2, self.marker_size/2)
    
    def _draw_hover_preview(self, painter: QPainter):
        """Draw hover preview with title"""
        # Calculate text bounds
        font = QFont(self.style_manager.get_font_family(), 9)
        font.setWeight(QFont.Weight.Medium)
        painter.setFont(font)
        
        text_rect = painter.fontMetrics().boundingRect(self.annotation.title)
        text_rect.moveCenter(QPointF(0, -self.marker_size - 10).toPoint())
        
        # Draw background
        bg_rect = text_rect.adjusted(-self.text_margin, -self.text_margin,
                                   self.text_margin, self.text_margin)
        painter.setBrush(QBrush(QColor(self.style.background_color)))
        painter.setPen(QPen(QColor(self.style.border_color), 1))
        painter.drawRoundedRect(QRectF(bg_rect), self.corner_radius/2, self.corner_radius/2)
        
        # Draw text
        painter.setPen(QPen(QColor(self.style.text_color)))
        painter.drawText(text_rect, Qt.AlignmentFlag.AlignCenter, self.annotation.title)
    
    def _draw_expanded_content(self, painter: QPainter):
        """Draw expanded annotation content"""
        # Calculate bounds
        bounds = self._calculate_expanded_bounds()
        
        # Draw background
        painter.setBrush(QBrush(QColor(self.style.background_color)))
        painter.setPen(QPen(QColor(self.style.border_color), 1.5))
        painter.drawRoundedRect(bounds, self.corner_radius, self.corner_radius)
        
        # Draw content
        content_rect = bounds.adjusted(self.padding, self.padding, 
                                     -self.padding, -self.padding)
        
        # Title
        title_font = QFont(self.style_manager.get_font_family(), 11)
        title_font.setWeight(QFont.Weight.Bold if self.style.font_weight == 'bold' 
                           else QFont.Weight.Normal)
        painter.setFont(title_font)
        painter.setPen(QPen(QColor(self.style.text_color)))
        
        title_rect = QRectF(content_rect)
        title_rect.setHeight(20)
        painter.drawText(title_rect, Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop,
                        self.annotation.title)
        
        # Description
        desc_font = QFont(self.style_manager.get_font_family(), 9)
        painter.setFont(desc_font)
        painter.setPen(QPen(QColor('#6B4226')))  # Brown text
        
        desc_rect = QRectF(content_rect)
        desc_rect.setTop(title_rect.bottom() + 4)
        painter.drawText(desc_rect, Qt.TextFlag.TextWordWrap | Qt.AlignmentFlag.AlignLeft,
                        self.annotation.description)
        
        # Additional details for specific annotation types
        self._draw_type_specific_details(painter, content_rect)
    
    def _draw_type_specific_details(self, painter: QPainter, content_rect: QRectF):
        """Draw additional details specific to annotation type"""
        detail_font = QFont(self.style_manager.get_font_family(), 8)
        painter.setFont(detail_font)
        painter.setPen(QPen(QColor('#999999')))
        
        detail_y = content_rect.bottom() - 20
        
        if isinstance(self.annotation, AchievementAnnotation):
            if self.annotation.previous_best:
                text = f"Previous best: {self.annotation.previous_best:.1f} "
                text += f"(+{self.annotation.improvement_percent:.0f}%)"
                painter.drawText(QPointF(content_rect.left(), detail_y), text)
                
        elif isinstance(self.annotation, TrendAnnotation):
            text = f"Confidence: {self.annotation.confidence * 100:.0f}% | "
            text += f"Change: {self.annotation.change_percent:+.0f}%"
            painter.drawText(QPointF(content_rect.left(), detail_y), text)
            
        elif isinstance(self.annotation, GoalAnnotation):
            text = f"Progress: {self.annotation.progress_percent:.0f}% | "
            text += f"Days left: {self.annotation.days_remaining}"
            painter.drawText(QPointF(content_rect.left(), detail_y), text)
    
    def _calculate_expanded_bounds(self) -> QRectF:
        """Calculate bounds for expanded content"""
        # Base size on content
        width = 250
        height = 120
        
        # Position relative to marker
        if self.pos().x() > self.scene().width() / 2:
            # Place on left
            x = -width - 20
        else:
            # Place on right
            x = 20
            
        y = -height / 2
        
        return QRectF(x, y, width, height)


class WSJAnnotationRenderer(QObject):
    """WSJ-styled annotation renderer for health visualizations"""
    
    # Signals
    annotation_clicked = pyqtSignal(str)  # annotation_id
    annotation_hovered = pyqtSignal(str, bool)  # annotation_id, entered
    
    def __init__(self, style_manager: Optional[WSJStyleManager] = None):
        super().__init__()
        self.style_manager = style_manager or WSJStyleManager()
        self.annotation_items: Dict[str, AnnotationGraphicsItem] = {}
        
    def render_annotations(self, 
                          scene: QGraphicsScene,
                          annotations: List[HealthAnnotation],
                          data_to_scene_transform) -> None:
        """Render annotations on the graphics scene
        
        Args:
            scene: QGraphicsScene to render on
            annotations: List of annotations to render
            data_to_scene_transform: Function to transform data coordinates to scene
        """
        # Clear existing annotations
        self.clear_annotations(scene)
        
        # Render each annotation
        for annotation in annotations:
            # Transform data position to scene coordinates
            scene_pos = data_to_scene_transform(annotation.data_point, annotation.value)
            
            # Create graphics item
            item = AnnotationGraphicsItem(annotation, self.style_manager)
            item.setPos(scene_pos)
            
            # Add to scene
            scene.addItem(item)
            self.annotation_items[annotation.id] = item
    
    def clear_annotations(self, scene: QGraphicsScene):
        """Clear all annotations from the scene"""
        for item in self.annotation_items.values():
            scene.removeItem(item)
        self.annotation_items.clear()
    
    def update_annotation_visibility(self, annotation_types: List[AnnotationType]):
        """Update which annotation types are visible"""
        for item in self.annotation_items.values():
            item.setVisible(item.annotation.type in annotation_types)
    
    def highlight_annotation(self, annotation_id: str):
        """Highlight a specific annotation"""
        if annotation_id in self.annotation_items:
            item = self.annotation_items[annotation_id]
            item.expanded = True
            item.update()