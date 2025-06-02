"""Journal entry indicator widget for dashboard views.

This module provides visual indicators to show when journal entries exist for
specific time periods. It supports daily, weekly, and monthly indicators with
different icons, badge counts, and interactive tooltips.

The JournalIndicator widget is designed to be overlaid on existing date cells,
cards, or other UI elements to provide non-intrusive visual cues about journal
entries. It follows the warm color scheme and accessibility guidelines of the
Apple Health Monitor Dashboard.

Key features:
    - Different icons for daily, weekly, and monthly entries
    - Badge count for multiple entries
    - Interactive tooltips with entry preview
    - Smooth animations on hover/click
    - Keyboard navigation support
    - ARIA labels for accessibility

Example:
    Basic usage on a date cell:
    
    >>> indicator = JournalIndicator(entry_type='daily', count=1)
    >>> indicator.clicked.connect(self.open_journal_entry)
    >>> indicator.setParent(date_cell)
    >>> indicator.move(date_cell.width() - 24, 4)
    
    With preview tooltip:
    
    >>> indicator = JournalIndicator(
    ...     entry_type='weekly',
    ...     count=2,
    ...     preview_text="Started new exercise routine..."
    ... )
"""

from typing import Optional, List, Dict, Any
from datetime import date
from PyQt6.QtWidgets import (
    QWidget, QLabel, QToolTip, QGraphicsOpacityEffect,
    QVBoxLayout, QHBoxLayout
)
from PyQt6.QtCore import (
    Qt, pyqtSignal, QTimer, QPropertyAnimation, QEasingCurve,
    QRect, QSize, QPoint, pyqtProperty
)
from PyQt6.QtGui import (
    QPainter, QPen, QBrush, QColor, QFont, QPainterPath,
    QPolygonF, QPixmap, QIcon, QCursor
)
from PyQt6.QtSvgWidgets import QSvgWidget

from ..utils.logging_config import get_logger

logger = get_logger(__name__)


class JournalIndicator(QWidget):
    """Visual indicator for journal entries with interactive features.
    
    This widget displays an icon and optional badge count to indicate the
    presence of journal entries. It supports different visual styles for
    daily, weekly, and monthly entries.
    
    Attributes:
        clicked (pyqtSignal): Emitted when the indicator is clicked
        hovered (pyqtSignal): Emitted when mouse hovers over the indicator
        
    Args:
        entry_type (str): Type of entry ('daily', 'weekly', 'monthly')
        count (int): Number of entries for this period
        preview_text (Optional[str]): Preview text for tooltip
        parent (Optional[QWidget]): Parent widget
    """
    
    # Signals
    clicked = pyqtSignal()
    hovered = pyqtSignal(bool)  # True on enter, False on leave
    
    # Visual constants
    DEFAULT_SIZE = 20
    BADGE_SIZE = 12
    ANIMATION_DURATION = 200
    
    # Color constants (matching warm theme)
    ICON_COLOR = "#8B7355"  # Warm brown
    ICON_HOVER_COLOR = "#FF8C42"  # Warm orange
    BADGE_COLOR = "#FF8C42"
    BADGE_TEXT_COLOR = "#FFFFFF"
    
    def __init__(self, 
                 entry_type: str = 'daily',
                 count: int = 1,
                 preview_text: Optional[str] = None,
                 parent: Optional[QWidget] = None):
        """Initialize the journal indicator.
        
        Args:
            entry_type (str): Type of entry ('daily', 'weekly', 'monthly')
            count (int): Number of entries for this period
            preview_text (Optional[str]): Preview text for tooltip
            parent (Optional[QWidget]): Parent widget
        """
        super().__init__(parent)
        
        self.entry_type = entry_type
        self.count = count
        self.preview_text = preview_text
        self._is_hovered = False
        self._opacity = 1.0
        
        # Set up widget properties
        self.setFixedSize(self.DEFAULT_SIZE, self.DEFAULT_SIZE)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setMouseTracking(True)
        
        # Set up animations
        self._setup_animations()
        
        # Set accessibility
        self._setup_accessibility()
        
        # Enable hover events
        self.setAttribute(Qt.WidgetAttribute.WA_Hover)
        
    def _setup_animations(self):
        """Set up hover and click animations."""
        # Opacity animation for hover effect
        self.opacity_effect = QGraphicsOpacityEffect()
        self.setGraphicsEffect(self.opacity_effect)
        
        self.hover_animation = QPropertyAnimation(self.opacity_effect, b"opacity")
        self.hover_animation.setDuration(self.ANIMATION_DURATION)
        self.hover_animation.setEasingCurve(QEasingCurve.Type.InOutQuad)
        
        # Scale animation for click effect
        self._scale = 1.0
        self.scale_animation = QPropertyAnimation(self, b"scale")
        self.scale_animation.setDuration(150)
        self.scale_animation.setEasingCurve(QEasingCurve.Type.InOutQuad)
        
    def _setup_accessibility(self):
        """Set up accessibility features."""
        # Set accessible name and description
        entry_type_text = self.entry_type.title()
        if self.count > 1:
            accessible_text = f"{self.count} {entry_type_text} journal entries"
        else:
            accessible_text = f"{entry_type_text} journal entry"
            
        self.setAccessibleName(accessible_text)
        self.setAccessibleDescription(
            f"Click to view {entry_type_text.lower()} journal entries"
        )
        
        # Make focusable for keyboard navigation
        self.setFocusPolicy(Qt.FocusPolicy.TabFocus)
        
    @pyqtProperty(float)
    def scale(self):
        """Get the current scale factor."""
        return self._scale
        
    @scale.setter
    def scale(self, value: float):
        """Set the scale factor and trigger repaint."""
        self._scale = value
        self.update()
        
    def paintEvent(self, event):
        """Paint the indicator with icon and optional badge."""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # Apply scale transform for animations
        if self._scale != 1.0:
            center = self.rect().center()
            painter.translate(center)
            painter.scale(self._scale, self._scale)
            painter.translate(-center)
        
        # Draw the icon based on entry type
        self._draw_icon(painter)
        
        # Draw badge if count > 1
        if self.count > 1:
            self._draw_badge(painter)
            
    def _draw_icon(self, painter: QPainter):
        """Draw the appropriate icon for the entry type.
        
        Args:
            painter (QPainter): The painter to use for drawing
        """
        # Set color based on hover state
        color = QColor(self.ICON_HOVER_COLOR if self._is_hovered else self.ICON_COLOR)
        painter.setPen(QPen(color, 2))
        painter.setBrush(QBrush(color))
        
        # Calculate icon area (leaving space for badge if needed)
        icon_rect = self.rect()
        if self.count > 1:
            icon_rect.setWidth(icon_rect.width() - self.BADGE_SIZE // 2)
            icon_rect.setHeight(icon_rect.height() - self.BADGE_SIZE // 2)
        
        if self.entry_type == 'daily':
            self._draw_daily_icon(painter, icon_rect)
        elif self.entry_type == 'weekly':
            self._draw_weekly_icon(painter, icon_rect)
        else:  # monthly
            self._draw_monthly_icon(painter, icon_rect)
            
    def _draw_daily_icon(self, painter: QPainter, rect: QRect):
        """Draw a notebook/page icon for daily entries.
        
        Args:
            painter (QPainter): The painter to use
            rect (QRect): The rectangle to draw within
        """
        # Draw a simple page/document icon
        margin = 3
        page_rect = rect.adjusted(margin, margin, -margin, -margin)
        
        # Draw page outline
        painter.drawRoundedRect(page_rect, 2, 2)
        
        # Draw lines representing text
        line_margin = 2
        line_y = page_rect.top() + line_margin + 3
        line_height = 2
        line_spacing = 1
        
        painter.setPen(QPen(QColor(255, 255, 255), 1))
        for i in range(3):
            if line_y + line_height > page_rect.bottom() - line_margin:
                break
            painter.drawLine(
                page_rect.left() + line_margin,
                line_y,
                page_rect.right() - line_margin,
                line_y
            )
            line_y += line_height + line_spacing
            
    def _draw_weekly_icon(self, painter: QPainter, rect: QRect):
        """Draw a calendar week icon for weekly entries.
        
        Args:
            painter (QPainter): The painter to use
            rect (QRect): The rectangle to draw within
        """
        # Draw a simplified calendar grid
        margin = 3
        cal_rect = rect.adjusted(margin, margin, -margin, -margin)
        
        # Draw calendar outline
        painter.drawRoundedRect(cal_rect, 2, 2)
        
        # Draw header bar
        header_height = cal_rect.height() // 4
        header_rect = QRect(
            cal_rect.left(),
            cal_rect.top(),
            cal_rect.width(),
            header_height
        )
        painter.fillRect(header_rect, painter.pen().color())
        
        # Draw week indicator (horizontal bar)
        week_margin = 2
        week_y = cal_rect.center().y()
        week_rect = QRect(
            cal_rect.left() + week_margin,
            week_y - 1,
            cal_rect.width() - 2 * week_margin,
            3
        )
        painter.setPen(QPen(QColor(255, 255, 255), 1))
        painter.fillRect(week_rect, QColor(255, 255, 255))
        
    def _draw_monthly_icon(self, painter: QPainter, rect: QRect):
        """Draw a full calendar icon for monthly entries.
        
        Args:
            painter (QPainter): The painter to use
            rect (QRect): The rectangle to draw within
        """
        # Draw a calendar with grid
        margin = 3
        cal_rect = rect.adjusted(margin, margin, -margin, -margin)
        
        # Draw calendar outline
        painter.drawRoundedRect(cal_rect, 2, 2)
        
        # Draw header bar
        header_height = cal_rect.height() // 4
        header_rect = QRect(
            cal_rect.left(),
            cal_rect.top(),
            cal_rect.width(),
            header_height
        )
        painter.fillRect(header_rect, painter.pen().color())
        
        # Draw grid dots
        painter.setPen(QPen(painter.pen().color(), 1))
        dot_size = 2
        grid_margin = 2
        grid_rect = cal_rect.adjusted(grid_margin, header_height + grid_margin, -grid_margin, -grid_margin)
        
        for row in range(3):
            for col in range(3):
                x = grid_rect.left() + col * (grid_rect.width() // 2)
                y = grid_rect.top() + row * (grid_rect.height() // 2)
                painter.drawEllipse(QPoint(x, y), dot_size // 2, dot_size // 2)
                
    def _draw_badge(self, painter: QPainter):
        """Draw a badge with the entry count.
        
        Args:
            painter (QPainter): The painter to use
        """
        # Position badge in top-right corner
        badge_rect = QRect(
            self.width() - self.BADGE_SIZE,
            0,
            self.BADGE_SIZE,
            self.BADGE_SIZE
        )
        
        # Draw badge background
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QBrush(QColor(self.BADGE_COLOR)))
        painter.drawEllipse(badge_rect)
        
        # Draw badge text
        painter.setPen(QPen(QColor(self.BADGE_TEXT_COLOR)))
        font = QFont()
        font.setPixelSize(8)
        font.setBold(True)
        painter.setFont(font)
        
        # Draw count (max 99)
        count_text = str(min(self.count, 99))
        painter.drawText(badge_rect, Qt.AlignmentFlag.AlignCenter, count_text)
        
    def enterEvent(self, event):
        """Handle mouse enter event."""
        super().enterEvent(event)
        self._is_hovered = True
        self.hovered.emit(True)
        
        # Animate opacity
        self.hover_animation.setStartValue(1.0)
        self.hover_animation.setEndValue(0.8)
        self.hover_animation.start()
        
        # Show tooltip with preview
        if self.preview_text:
            self._show_preview_tooltip()
            
        self.update()
        
    def leaveEvent(self, event):
        """Handle mouse leave event."""
        super().leaveEvent(event)
        self._is_hovered = False
        self.hovered.emit(False)
        
        # Animate opacity back
        self.hover_animation.setStartValue(0.8)
        self.hover_animation.setEndValue(1.0)
        self.hover_animation.start()
        
        self.update()
        
    def mousePressEvent(self, event):
        """Handle mouse press event."""
        if event.button() == Qt.MouseButton.LeftButton:
            # Animate scale
            self.scale_animation.setStartValue(1.0)
            self.scale_animation.setEndValue(0.9)
            self.scale_animation.start()
            
    def mouseReleaseEvent(self, event):
        """Handle mouse release event."""
        if event.button() == Qt.MouseButton.LeftButton:
            # Animate scale back
            self.scale_animation.setStartValue(0.9)
            self.scale_animation.setEndValue(1.0)
            self.scale_animation.start()
            
            # Emit clicked signal
            self.clicked.emit()
            
    def keyPressEvent(self, event):
        """Handle keyboard events for accessibility."""
        if event.key() in (Qt.Key.Key_Return, Qt.Key.Key_Space):
            self.clicked.emit()
        else:
            super().keyPressEvent(event)
            
    def _show_preview_tooltip(self):
        """Show a rich tooltip with entry preview."""
        if not self.preview_text:
            return
            
        # Create tooltip content
        entry_type_text = self.entry_type.title()
        tooltip_html = f"""
        <div style='padding: 8px; max-width: 300px;'>
            <b>{entry_type_text} Journal Entry</b><br/>
            <div style='margin-top: 4px; color: #666;'>
                {self.preview_text[:100]}{'...' if len(self.preview_text) > 100 else ''}
            </div>
            <div style='margin-top: 4px; font-size: 11px; color: #999;'>
                Click to view full entry
            </div>
        </div>
        """
        
        QToolTip.showText(self.mapToGlobal(QPoint(self.width(), 0)), tooltip_html, self)
        
    def update_indicator(self, count: int, preview_text: Optional[str] = None):
        """Update the indicator with new data.
        
        Args:
            count (int): New entry count
            preview_text (Optional[str]): New preview text
        """
        self.count = count
        self.preview_text = preview_text
        
        # Update accessibility
        self._setup_accessibility()
        
        # Trigger repaint
        self.update()
        
        # Animate the change
        self.scale_animation.setStartValue(1.1)
        self.scale_animation.setEndValue(1.0)
        self.scale_animation.start()