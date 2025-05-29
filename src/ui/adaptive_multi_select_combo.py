"""Adaptive multi-select combo box with data availability indicators."""

from typing import Optional, Dict, Set, Tuple, List
from datetime import date

from PyQt6.QtWidgets import QStyledItemDelegate, QStyleOptionViewItem, QStyle, QApplication
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QStandardItem, QPainter, QColor, QFont, QFontMetrics

from .multi_select_combo import CheckableComboBox
from ..data_availability_service import DataAvailabilityService, AvailabilityLevel
from src.utils.logging_config import get_logger

logger = get_logger(__name__)


class AvailabilityItemDelegate(QStyledItemDelegate):
    """Custom delegate to show availability indicators for combo box items."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
    def paint(self, painter: QPainter, option: QStyleOptionViewItem, index):
        """Custom paint method to add availability indicators."""
        # Paint the base item first
        super().paint(painter, option, index)
        
        # Get availability data from item
        item = index.model().itemFromIndex(index)
        if not item:
            return
            
        availability_level = item.data(Qt.ItemDataRole.UserRole + 1)
        record_count = item.data(Qt.ItemDataRole.UserRole + 2)
        
        if availability_level is None:
            return
            
        # Calculate positions
        rect = option.rect
        indicator_size = 12
        margin = 4
        
        # Position indicator on the right side
        indicator_rect = rect.adjusted(
            rect.width() - indicator_size - margin, 
            (rect.height() - indicator_size) // 2,
            -margin,
            -(rect.height() - indicator_size) // 2
        )
        
        # Choose color based on availability level
        if availability_level == AvailabilityLevel.FULL:
            color = QColor(50, 205, 50)  # Lime green
            symbol = "●"
        elif availability_level == AvailabilityLevel.PARTIAL:
            color = QColor(255, 215, 0)  # Gold
            symbol = "◐"
        elif availability_level == AvailabilityLevel.SPARSE:
            color = QColor(255, 165, 0)  # Orange
            symbol = "◯"
        else:  # NONE
            color = QColor(220, 20, 60)  # Crimson
            symbol = "○"
            
        # Draw availability indicator
        painter.save()
        painter.setPen(color)
        painter.setBrush(color)
        
        font = painter.font()
        font.setPointSize(10)
        font.setBold(True)
        painter.setFont(font)
        
        painter.drawText(indicator_rect, Qt.AlignmentFlag.AlignCenter, symbol)
        
        # Draw record count if available
        if record_count is not None and record_count > 0:
            count_font = painter.font()
            count_font.setPointSize(7)
            painter.setFont(count_font)
            
            count_text = f"{record_count:,}" if record_count < 10000 else f"{record_count//1000}k"
            count_rect = rect.adjusted(
                rect.width() - 40, 
                rect.height() - 15,
                -2,
                -2
            )
            
            painter.setPen(QColor(100, 100, 100))
            painter.drawText(count_rect, Qt.AlignmentFlag.AlignRight, count_text)
            
        painter.restore()


class AdaptiveMultiSelectCombo(CheckableComboBox):
    """Multi-select combo box with data availability indicators."""
    
    availabilityChanged = pyqtSignal()
    
    def __init__(self, parent=None, availability_service: Optional[DataAvailabilityService] = None):
        super().__init__(parent)
        
        self.availability_service = availability_service
        self.metric_availabilities: Dict[str, Tuple[AvailabilityLevel, int]] = {}
        self.date_range: Optional[Tuple[date, date]] = None
        
        # Set custom delegate for availability indicators
        self.delegate = AvailabilityItemDelegate()
        self.view().setItemDelegate(self.delegate)
        
        # Register for availability updates
        if self.availability_service:
            self.availability_service.register_callback(self._on_availability_updated)
            
        # Update placeholder and tooltip
        self.setPlaceholderText("Select metrics with data availability indicators...")
        self.setToolTip(
            "Select multiple metrics\n\n"
            "Availability Indicators:\n"
            "● Green: Full data available\n"
            "◐ Yellow: Partial data (some gaps)\n"
            "◯ Orange: Sparse data (limited points)\n"
            "○ Red: No/insufficient data\n\n"
            "Keyboard shortcuts:\n"
            "Space: Toggle selection\n"
            "Ctrl+A: Select all with data\n"
            "Ctrl+D: Deselect all\n"
            "Escape: Close dropdown"
        )
        
        logger.debug("AdaptiveMultiSelectCombo initialized")
        
    def addMetric(self, metric_name: str, data=None, checked=False):
        """Add a metric with availability checking.
        
        Args:
            metric_name: Name of the health metric
            data: Optional data associated with the metric
            checked: Whether the metric should be initially checked
        """
        item = QStandardItem(metric_name)
        item.setFlags(Qt.ItemFlag.ItemIsEnabled | Qt.ItemFlag.ItemIsUserCheckable)
        item.setData(Qt.CheckState.Checked if checked else Qt.CheckState.Unchecked, Qt.ItemDataRole.CheckStateRole)
        
        if data is not None:
            item.setData(data, Qt.ItemDataRole.UserRole)
            
        # Add availability data
        availability_level, record_count = self.metric_availabilities.get(metric_name, (AvailabilityLevel.NONE, 0))
        item.setData(availability_level, Qt.ItemDataRole.UserRole + 1)
        item.setData(record_count, Qt.ItemDataRole.UserRole + 2)
        
        # Set tooltip with detailed availability info
        tooltip = self._create_metric_tooltip(metric_name, availability_level, record_count)
        item.setToolTip(tooltip)
        
        self.model.appendRow(item)
        self._update_text()
        
    def addMetrics(self, metric_names: List[str]):
        """Add multiple metrics with availability checking.
        
        Args:
            metric_names: List of health metric names
        """
        for metric_name in metric_names:
            self.addMetric(metric_name)
            
    def set_date_range(self, start_date: date, end_date: date):
        """Set date range for availability calculations.
        
        Args:
            start_date: Start date for availability checking
            end_date: End date for availability checking
        """
        self.date_range = (start_date, end_date)
        self._update_metric_availability()
        
    def _update_metric_availability(self):
        """Update availability information for all metrics."""
        if not self.availability_service:
            return
            
        try:
            # Get available metric types
            available_metrics = self.availability_service.db.get_available_types()
            
            # Update availability for each metric
            for metric_type in available_metrics:
                data_range = self.availability_service.get_availability(metric_type)
                if data_range:
                    level = data_range.level
                    record_count = data_range.total_points
                else:
                    level = AvailabilityLevel.NONE
                    record_count = 0
                    
                self.metric_availabilities[metric_type] = (level, record_count)
                
            self._update_existing_items()
            
        except Exception as e:
            logger.error(f"Error updating metric availability: {e}")
            
    def _update_existing_items(self):
        """Update availability data for existing items in the model."""
        for i in range(self.model.rowCount()):
            item = self.model.item(i)
            if item:
                metric_name = item.text()
                availability_level, record_count = self.metric_availabilities.get(
                    metric_name, (AvailabilityLevel.NONE, 0)
                )
                
                # Update item data
                item.setData(availability_level, Qt.ItemDataRole.UserRole + 1)
                item.setData(record_count, Qt.ItemDataRole.UserRole + 2)
                
                # Update tooltip
                tooltip = self._create_metric_tooltip(metric_name, availability_level, record_count)
                item.setToolTip(tooltip)
                
                # Update enabled state based on availability
                if availability_level == AvailabilityLevel.NONE:
                    item.setEnabled(False)
                    item.setCheckState(Qt.CheckState.Unchecked)
                else:
                    item.setEnabled(True)
                    
        # Force view update
        self.view().update()
        
    def _create_metric_tooltip(self, metric_name: str, level: AvailabilityLevel, record_count: int) -> str:
        """Create detailed tooltip for a metric.
        
        Args:
            metric_name: Name of the metric
            level: Availability level
            record_count: Number of data records
            
        Returns:
            Formatted tooltip string
        """
        tooltip = f"{metric_name}\n\n"
        
        if level == AvailabilityLevel.FULL:
            tooltip += "✓ Full data available\n"
            tooltip += f"Records: {record_count:,}\n"
            tooltip += "Complete coverage for selected period"
        elif level == AvailabilityLevel.PARTIAL:
            tooltip += "⚠ Partial data available\n"
            tooltip += f"Records: {record_count:,}\n"
            tooltip += "Some gaps but usable for analysis"
        elif level == AvailabilityLevel.SPARSE:
            tooltip += "⚠ Limited data available\n"
            tooltip += f"Records: {record_count:,}\n"
            tooltip += "Sparse coverage, limited analysis possible"
        else:  # NONE
            tooltip += "✗ No data available\n"
            tooltip += "No records found for this metric"
            
        return tooltip
        
    def checkAll(self):
        """Check all items that have available data."""
        for i in range(self.model.rowCount()):
            item = self.model.item(i)
            if item and item.isEnabled():
                availability_level = item.data(Qt.ItemDataRole.UserRole + 1)
                # Only check items with some data
                if availability_level and availability_level != AvailabilityLevel.NONE:
                    item.setCheckState(Qt.CheckState.Checked)
        self._update_text()
        
    def checkFullDataOnly(self):
        """Check only items with full data availability."""
        for i in range(self.model.rowCount()):
            item = self.model.item(i)
            if item:
                availability_level = item.data(Qt.ItemDataRole.UserRole + 1)
                if availability_level == AvailabilityLevel.FULL:
                    item.setCheckState(Qt.CheckState.Checked)
                else:
                    item.setCheckState(Qt.CheckState.Unchecked)
        self._update_text()
        
    def getAvailabilityStats(self) -> Dict[str, int]:
        """Get statistics about data availability for current metrics.
        
        Returns:
            Dictionary with counts for each availability level
        """
        stats = {
            'full': 0,
            'partial': 0, 
            'sparse': 0,
            'none': 0,
            'total': self.model.rowCount()
        }
        
        for i in range(self.model.rowCount()):
            item = self.model.item(i)
            if item:
                availability_level = item.data(Qt.ItemDataRole.UserRole + 1)
                if availability_level == AvailabilityLevel.FULL:
                    stats['full'] += 1
                elif availability_level == AvailabilityLevel.PARTIAL:
                    stats['partial'] += 1
                elif availability_level == AvailabilityLevel.SPARSE:
                    stats['sparse'] += 1
                else:
                    stats['none'] += 1
                    
        return stats
        
    def getCheckedMetricsWithAvailability(self) -> List[Tuple[str, AvailabilityLevel, int]]:
        """Get checked metrics with their availability information.
        
        Returns:
            List of tuples (metric_name, availability_level, record_count)
        """
        checked_metrics = []
        
        for i in range(self.model.rowCount()):
            item = self.model.item(i)
            if item and item.checkState() == Qt.CheckState.Checked:
                metric_name = item.text()
                availability_level = item.data(Qt.ItemDataRole.UserRole + 1)
                record_count = item.data(Qt.ItemDataRole.UserRole + 2)
                checked_metrics.append((metric_name, availability_level, record_count))
                
        return checked_metrics
        
    def _on_availability_updated(self):
        """Handle availability service updates."""
        self._update_metric_availability()
        self.availabilityChanged.emit()
        
    def _update_text(self):
        """Update display text with availability summary."""
        checked_texts = self.checkedTexts()
        
        if not checked_texts:
            self.lineEdit().setText(self._placeholder)
            self.lineEdit().setStyleSheet("color: #ADB5BD;")
        else:
            count = len(checked_texts)
            total = self.model.rowCount()
            
            # Get availability stats for checked items
            checked_with_full_data = 0
            for i in range(self.model.rowCount()):
                item = self.model.item(i)
                if (item and item.checkState() == Qt.CheckState.Checked and 
                    item.data(Qt.ItemDataRole.UserRole + 1) == AvailabilityLevel.FULL):
                    checked_with_full_data += 1
                    
            if count == total and total > 0:
                display_text = f"All selected ({checked_with_full_data} with full data)"
            elif count <= 2:
                display_text = ", ".join(checked_texts)
                if checked_with_full_data < count:
                    display_text += f" ({checked_with_full_data} full)"
            else:
                display_text = f"{count} metrics ({checked_with_full_data} with full data)"
                
            self.lineEdit().setText(display_text)
            self.lineEdit().setStyleSheet("")
            
    def cleanup(self):
        """Cleanup when widget is destroyed."""
        if self.availability_service:
            self.availability_service.unregister_callback(self._on_availability_updated)