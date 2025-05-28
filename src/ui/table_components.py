"""Table components for displaying and managing health metrics data."""

from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional, Union
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTableWidget, QTableWidgetItem,
    QPushButton, QLabel, QComboBox, QSpinBox, QLineEdit, QHeaderView,
    QFileDialog, QMessageBox, QProgressDialog, QMenu, QCheckBox,
    QFrame, QSplitter, QGroupBox, QScrollArea, QToolButton, QButtonGroup
)
from PyQt6.QtCore import Qt, pyqtSignal, QThread, QTimer, QPropertyAnimation, QEasingCurve
from PyQt6.QtGui import QAction, QFont, QIcon, QCursor
import pandas as pd
import numpy as np
import json
import csv
from datetime import datetime
from pathlib import Path

from src.utils.logging_config import get_logger
from .style_manager import StyleManager

logger = get_logger(__name__)


@dataclass
class TableConfig:
    """Configuration for table display and behavior."""
    # Display
    page_size: int = 25
    alternating_rows: bool = True
    grid_style: str = 'dotted'  # 'solid', 'dotted', 'none'
    
    # Columns
    resizable_columns: bool = True
    movable_columns: bool = True
    hidden_columns: List[str] = field(default_factory=list)
    
    # Selection
    selection_mode: str = 'row'  # 'row', 'cell', 'column'
    multi_select: bool = True
    
    # Export
    export_formats: List[str] = field(default_factory=lambda: ['csv', 'excel', 'json'])
    
    # Styling
    header_background: str = '#FF8C42'
    header_foreground: str = '#FFFFFF'
    selection_color: str = '#FFE5CC'


class ExportWorker(QThread):
    """Worker thread for exporting table data."""
    
    progress_updated = pyqtSignal(int)
    export_completed = pyqtSignal(str)
    export_failed = pyqtSignal(str)
    
    def __init__(self, data: pd.DataFrame, filename: str, format_type: str, selected_only: bool = False):
        super().__init__()
        self.data = data
        self.filename = filename
        self.format_type = format_type
        self.selected_only = selected_only
    
    def run(self):
        """Export data in background thread."""
        try:
            logger.info(f"Starting export to {self.filename} in {self.format_type} format")
            
            if self.format_type == 'csv':
                self._export_csv()
            elif self.format_type == 'excel':
                self._export_excel()
            elif self.format_type == 'json':
                self._export_json()
            
            self.export_completed.emit(self.filename)
            logger.info(f"Export completed successfully: {self.filename}")
            
        except Exception as e:
            error_msg = f"Export failed: {str(e)}"
            logger.error(error_msg)
            self.export_failed.emit(error_msg)
    
    def _export_csv(self):
        """Export data to CSV format."""
        total_rows = len(self.data)
        chunk_size = max(1000, total_rows // 100)
        
        with open(self.filename, 'w', newline='', encoding='utf-8') as f:
            self.data.to_csv(f, index=False)
            self.progress_updated.emit(100)
    
    def _export_excel(self):
        """Export data to Excel format with formatting."""
        try:
            import openpyxl
            from openpyxl.styles import Font, PatternFill, Alignment
        except ImportError:
            logger.warning("openpyxl not available, falling back to basic Excel export")
            with pd.ExcelWriter(self.filename, engine='xlsxwriter') as writer:
                self.data.to_excel(writer, index=False, sheet_name='Health Metrics')
            return
        
        with pd.ExcelWriter(self.filename, engine='openpyxl') as writer:
            self.data.to_excel(writer, index=False, sheet_name='Health Metrics')
            
            worksheet = writer.sheets['Health Metrics']
            
            # Apply formatting
            header_font = Font(bold=True, color="FFFFFF")
            header_fill = PatternFill(start_color="FF8C42", end_color="FF8C42", fill_type="solid")
            
            for cell in worksheet[1]:
                cell.font = header_font
                cell.fill = header_fill
                cell.alignment = Alignment(horizontal="center")
            
            # Auto-adjust column widths
            for column in worksheet.columns:
                max_length = 0
                column_letter = column[0].column_letter
                
                for cell in column:
                    if cell.value:
                        max_length = max(max_length, len(str(cell.value)))
                
                adjusted_width = min(max_length + 2, 50)
                worksheet.column_dimensions[column_letter].width = adjusted_width
        
        self.progress_updated.emit(100)
    
    def _export_json(self):
        """Export data to JSON format."""
        data_dict = self.data.to_dict(orient='records')
        
        with open(self.filename, 'w', encoding='utf-8') as f:
            json.dump(data_dict, f, indent=2, default=str)
        
        self.progress_updated.emit(100)


class PaginationWidget(QWidget):
    """Pagination controls for large datasets."""
    
    page_changed = pyqtSignal(int)
    page_size_changed = pyqtSignal(int)
    
    def __init__(self, table_widget):
        super().__init__()
        self.table_widget = table_widget
        self.style_manager = StyleManager()
        self.setup_ui()
        self.apply_style()
    
    def setup_ui(self):
        """Create pagination controls."""
        layout = QHBoxLayout()
        layout.setContentsMargins(16, 8, 16, 8)
        layout.setSpacing(12)
        
        # Previous button
        self.prev_button = QPushButton("◀ Previous")
        self.prev_button.clicked.connect(self._go_previous)
        self.prev_button.setFixedWidth(120)
        
        # Next button
        self.next_button = QPushButton("Next ▶")
        self.next_button.clicked.connect(self._go_next)
        self.next_button.setFixedWidth(120)
        
        # Page info
        self.page_label = QLabel()
        self.page_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.page_label.setMinimumWidth(200)
        
        # Page size selector
        size_label = QLabel("Rows per page:")
        self.page_size_combo = QComboBox()
        self.page_size_combo.addItems(["10", "25", "50", "100"])
        self.page_size_combo.setCurrentText("25")
        self.page_size_combo.currentTextChanged.connect(self._change_page_size)
        self.page_size_combo.setFixedWidth(80)
        
        # Jump to page
        jump_label = QLabel("Go to page:")
        self.page_input = QSpinBox()
        self.page_input.setMinimum(1)
        self.page_input.valueChanged.connect(self._jump_to_page)
        self.page_input.setFixedWidth(80)
        
        # Layout
        layout.addWidget(self.prev_button)
        layout.addWidget(self.page_label)
        layout.addWidget(self.next_button)
        layout.addStretch()
        layout.addWidget(size_label)
        layout.addWidget(self.page_size_combo)
        layout.addWidget(jump_label)
        layout.addWidget(self.page_input)
        
        self.setLayout(layout)
        self.update_page_info()
    
    def apply_style(self):
        """Apply styling to pagination controls."""
        self.setStyleSheet(f"""
            QWidget {{
                background-color: {self.style_manager.SECONDARY_BG};
                border-top: 1px solid rgba(139, 115, 85, 0.1);
            }}
            QLabel {{
                color: {self.style_manager.TEXT_SECONDARY};
                font-weight: 500;
            }}
        """)
        
        button_style = self.style_manager.get_button_style("secondary")
        self.prev_button.setStyleSheet(button_style)
        self.next_button.setStyleSheet(button_style)
        
        input_style = self.style_manager.get_input_style()
        self.page_size_combo.setStyleSheet(input_style)
        self.page_input.setStyleSheet(input_style)
    
    def update_page_info(self):
        """Update page information display."""
        if not hasattr(self.table_widget, 'current_page'):
            return
        
        total_rows = getattr(self.table_widget, 'total_rows', 0)
        page_size = getattr(self.table_widget, 'page_size', 25)
        current_page = getattr(self.table_widget, 'current_page', 0)
        total_pages = max(1, (total_rows + page_size - 1) // page_size)
        
        start = current_page * page_size + 1
        end = min(start + page_size - 1, total_rows)
        
        if total_rows == 0:
            self.page_label.setText("No records")
        else:
            self.page_label.setText(f"Showing {start:,}-{end:,} of {total_rows:,} records")
        
        # Update button states
        self.prev_button.setEnabled(current_page > 0)
        self.next_button.setEnabled(current_page < total_pages - 1)
        
        # Update page input
        self.page_input.setMaximum(total_pages)
        self.page_input.setValue(current_page + 1)
    
    def _go_previous(self):
        """Go to previous page."""
        if hasattr(self.table_widget, 'current_page') and self.table_widget.current_page > 0:
            self.page_changed.emit(self.table_widget.current_page - 1)
    
    def _go_next(self):
        """Go to next page."""
        if hasattr(self.table_widget, 'current_page'):
            total_pages = max(1, (self.table_widget.total_rows + self.table_widget.page_size - 1) // self.table_widget.page_size)
            if self.table_widget.current_page < total_pages - 1:
                self.page_changed.emit(self.table_widget.current_page + 1)
    
    def _change_page_size(self, text):
        """Change page size."""
        try:
            page_size = int(text)
            self.page_size_changed.emit(page_size)
        except ValueError:
            pass
    
    def _jump_to_page(self, page_number):
        """Jump to specific page."""
        if page_number > 0:
            self.page_changed.emit(page_number - 1)


class FilterWidget(QWidget):
    """Filtering controls for table columns."""
    
    filter_changed = pyqtSignal(dict)
    
    def __init__(self, columns: List[str]):
        super().__init__()
        self.columns = columns
        self.column_filters = {}
        self.style_manager = StyleManager()
        self.setup_ui()
        self.apply_style()
    
    def setup_ui(self):
        """Create filter controls."""
        layout = QHBoxLayout()
        layout.setContentsMargins(16, 8, 16, 8)
        layout.setSpacing(8)
        
        # Filter label
        filter_label = QLabel("Filters:")
        filter_label.setFont(QFont("Inter", 10, QFont.Weight.Bold))
        layout.addWidget(filter_label)
        
        # Create filter inputs for each column
        for i, column in enumerate(self.columns):
            filter_input = QLineEdit()
            filter_input.setPlaceholderText(f"Filter {column}...")
            filter_input.textChanged.connect(lambda text, col=column: self._filter_changed(col, text))
            filter_input.setMaximumWidth(150)
            
            self.column_filters[column] = filter_input
            layout.addWidget(filter_input)
        
        # Clear filters button
        clear_button = QPushButton("Clear All")
        clear_button.clicked.connect(self._clear_all_filters)
        clear_button.setMaximumWidth(80)
        layout.addWidget(clear_button)
        
        layout.addStretch()
        self.setLayout(layout)
    
    def apply_style(self):
        """Apply styling to filter controls."""
        self.setStyleSheet(f"""
            QWidget {{
                background-color: {self.style_manager.TERTIARY_BG};
                border-bottom: 1px solid rgba(139, 115, 85, 0.1);
            }}
            QLabel {{
                color: {self.style_manager.TEXT_PRIMARY};
                font-weight: 600;
            }}
        """)
        
        input_style = self.style_manager.get_input_style()
        for filter_input in self.column_filters.values():
            filter_input.setStyleSheet(input_style)
    
    def _filter_changed(self, column: str, text: str):
        """Handle filter text change."""
        active_filters = {}
        for col, input_widget in self.column_filters.items():
            if input_widget.text().strip():
                active_filters[col] = input_widget.text().strip()
        
        self.filter_changed.emit(active_filters)
    
    def _clear_all_filters(self):
        """Clear all filter inputs."""
        for filter_input in self.column_filters.values():
            filter_input.clear()
        self.filter_changed.emit({})


class MetricTable(QWidget):
    """Advanced table widget for displaying health metrics with sorting, pagination, and export."""
    
    # Signals
    row_selected = pyqtSignal(int)
    data_exported = pyqtSignal(str)
    
    def __init__(self, config: Optional[TableConfig] = None):
        super().__init__()
        self.config = config or TableConfig()
        self.style_manager = StyleManager()
        
        # Data management
        self.data = None
        self.filtered_data = None
        self.displayed_data = None
        self.current_page = 0
        self.page_size = self.config.page_size
        self.total_rows = 0
        self.total_pages = 0
        
        # Sorting
        self.sort_column = None
        self.sort_order = Qt.SortOrder.AscendingOrder
        
        # Filtering
        self.active_filters = {}
        
        self.setup_ui()
        self.apply_style()
        logger.info("MetricTable initialized")
    
    def setup_ui(self):
        """Setup table UI with controls."""
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # Create toolbar
        self.toolbar = self._create_toolbar()
        layout.addWidget(self.toolbar)
        
        # Create filter widget (initially hidden)
        self.filter_widget = None
        
        # Create table widget
        self.table = QTableWidget()
        self.table.setSortingEnabled(False)  # We'll handle sorting manually
        self.table.setAlternatingRowColors(self.config.alternating_rows)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setSelectionMode(QTableWidget.SelectionMode.ExtendedSelection if self.config.multi_select else QTableWidget.SelectionMode.SingleSelection)
        self.table.verticalHeader().hide()
        self.table.horizontalHeader().sectionClicked.connect(self._handle_sort)
        self.table.itemSelectionChanged.connect(self._handle_selection_change)
        
        # Configure header
        header = self.table.horizontalHeader()
        header.setStretchLastSection(True)
        if self.config.resizable_columns:
            header.setSectionResizeMode(QHeaderView.ResizeMode.Interactive)
        if self.config.movable_columns:
            header.setSectionsMovable(True)
        
        layout.addWidget(self.table)
        
        # Create pagination controls
        self.pagination_widget = PaginationWidget(self)
        self.pagination_widget.page_changed.connect(self._go_to_page)
        self.pagination_widget.page_size_changed.connect(self._change_page_size)
        layout.addWidget(self.pagination_widget)
        
        self.setLayout(layout)
    
    def _create_toolbar(self):
        """Create toolbar with export and filter controls."""
        toolbar = QFrame()
        toolbar.setFrameStyle(QFrame.Shape.NoFrame)
        
        layout = QHBoxLayout()
        layout.setContentsMargins(16, 12, 16, 12)
        layout.setSpacing(8)
        
        # Export button
        self.export_button = QPushButton("📤 Export")
        self.export_button.clicked.connect(self._show_export_menu)
        
        # Filter toggle button
        self.filter_button = QPushButton("🔍 Filters")
        self.filter_button.setCheckable(True)
        self.filter_button.clicked.connect(self._toggle_filters)
        
        # Column visibility button
        self.columns_button = QPushButton("📋 Columns")
        self.columns_button.clicked.connect(self._show_column_menu)
        
        # Refresh button
        self.refresh_button = QPushButton("🔄 Refresh")
        self.refresh_button.clicked.connect(self._refresh_data)
        
        # Info label
        self.info_label = QLabel()
        self.info_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        layout.addWidget(self.export_button)
        layout.addWidget(self.filter_button)
        layout.addWidget(self.columns_button)
        layout.addWidget(self.refresh_button)
        layout.addStretch()
        layout.addWidget(self.info_label)
        
        toolbar.setLayout(layout)
        return toolbar
    
    def apply_style(self):
        """Apply styling to table and controls."""
        # Main widget styling
        self.setStyleSheet(f"""
            QWidget {{
                background-color: {self.style_manager.SECONDARY_BG};
                border-radius: 12px;
                border: 1px solid rgba(139, 115, 85, 0.1);
            }}
        """)
        
        # Toolbar styling
        self.toolbar.setStyleSheet(f"""
            QFrame {{
                background-color: {self.style_manager.SECONDARY_BG};
                border-bottom: 1px solid rgba(139, 115, 85, 0.1);
                border-top-left-radius: 12px;
                border-top-right-radius: 12px;
            }}
            QLabel {{
                color: {self.style_manager.TEXT_SECONDARY};
                font-weight: 500;
            }}
        """)
        
        # Table styling
        self.table.setStyleSheet(f"""
            QTableWidget {{
                background-color: {self.style_manager.SECONDARY_BG};
                alternate-background-color: {self.style_manager.TERTIARY_BG};
                gridline-color: rgba(139, 115, 85, 0.1);
                border: none;
                selection-background-color: {self.config.selection_color};
                selection-color: {self.style_manager.TEXT_PRIMARY};
            }}
            
            QTableWidget::item {{
                padding: 12px 16px;
                border-bottom: 1px solid rgba(139, 115, 85, 0.05);
            }}
            
            QTableWidget::item:selected {{
                background-color: {self.config.selection_color};
                color: {self.style_manager.TEXT_PRIMARY};
            }}
            
            QHeaderView::section {{
                background-color: {self.config.header_background};
                color: {self.config.header_foreground};
                padding: 12px 16px;
                border: none;
                border-right: 1px solid rgba(255, 255, 255, 0.2);
                font-weight: 600;
                font-size: 14px;
            }}
            
            QHeaderView::section:hover {{
                background-color: #E67A35;
            }}
            
            QHeaderView::section:pressed {{
                background-color: #D06928;
            }}
            
            QHeaderView::down-arrow {{
                image: url(data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iMTIiIGhlaWdodD0iOCIgdmlld0JveD0iMCAwIDEyIDgiIGZpbGw9Im5vbmUiIHhtbG5zPSJodHRwOi8vd3d3LnczLm9yZy8yMDAwL3N2ZyI+CjxwYXRoIGQ9Ik02IDhMMCAwSDEyTDYgOFoiIGZpbGw9IndoaXRlIi8+Cjwvc3ZnPgo=);
            }}
            
            QHeaderView::up-arrow {{
                image: url(data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iMTIiIGhlaWdodD0iOCIgdmlld0JveD0iMCAwIDEyIDgiIGZpbGw9Im5vbmUiIHhtbG5zPSJodHRwOi8vd3d3LnczLm9yZy8yMDAwL3N2ZyI+CjxwYXRoIGQ9Ik02IDBMMTI4SDBMNiAwWiIgZmlsbD0id2hpdGUiLz4KPC9zdmc+Cg==);
            }}
        """)
        
        # Button styling
        button_style = self.style_manager.get_button_style("secondary")
        for button in [self.export_button, self.filter_button, self.columns_button, self.refresh_button]:
            button.setStyleSheet(button_style)
        
        # Scroll bar styling
        scroll_style = self.style_manager.get_scroll_bar_style()
        self.table.setStyleSheet(self.table.styleSheet() + scroll_style)
    
    def load_data(self, data: pd.DataFrame):
        """Load data into table with pagination."""
        logger.info(f"Loading data with {len(data)} rows into table")
        
        self.data = data.copy()
        self.filtered_data = data.copy()
        self.total_rows = len(data)
        self.total_pages = max(1, (self.total_rows + self.page_size - 1) // self.page_size)
        self.current_page = 0
        
        # Setup columns
        if len(data) > 0:
            self.table.setColumnCount(len(data.columns))
            self.table.setHorizontalHeaderLabels(data.columns.tolist())
            
            # Create filter widget if not exists
            if self.filter_widget is None:
                self.filter_widget = FilterWidget(data.columns.tolist())
                self.filter_widget.filter_changed.connect(self._apply_filters)
                # Initially hidden
                self.filter_widget.hide()
                self.layout().insertWidget(1, self.filter_widget)
        
        self._update_table()
        self._update_info_label()
        logger.info("Data loaded successfully")
    
    def _update_table(self):
        """Update table display with current page data."""
        if self.filtered_data is None or len(self.filtered_data) == 0:
            self.table.setRowCount(0)
            self.pagination_widget.update_page_info()
            return
        
        # Calculate page bounds
        start_idx = self.current_page * self.page_size
        end_idx = min(start_idx + self.page_size, len(self.filtered_data))
        
        # Get page data
        page_data = self.filtered_data.iloc[start_idx:end_idx]
        self.displayed_data = page_data
        
        # Update table
        self.table.setRowCount(len(page_data))
        
        for row_idx, (_, row) in enumerate(page_data.iterrows()):
            for col_idx, value in enumerate(row):
                # Format value for display
                if pd.isna(value):
                    display_value = ""
                elif isinstance(value, float):
                    display_value = f"{value:.2f}" if value != int(value) else str(int(value))
                else:
                    display_value = str(value)
                
                item = QTableWidgetItem(display_value)
                item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEditable)  # Make read-only
                self.table.setItem(row_idx, col_idx, item)
        
        # Update pagination
        self.pagination_widget.update_page_info()
        
        # Update sort indicators
        self._update_sort_indicators()
    
    def _update_info_label(self):
        """Update info label with data statistics."""
        if self.filtered_data is not None:
            total = len(self.data) if self.data is not None else 0
            filtered = len(self.filtered_data)
            
            if total == filtered:
                self.info_label.setText(f"{total:,} records")
            else:
                self.info_label.setText(f"{filtered:,} of {total:,} records")
        else:
            self.info_label.setText("No data")
    
    def _handle_sort(self, column: int):
        """Handle column header click for sorting."""
        if self.data is None or len(self.data) == 0:
            return
        
        column_name = self.data.columns[column]
        
        # Toggle sort order if same column, otherwise default to ascending
        if self.sort_column == column:
            self.sort_order = (Qt.SortOrder.DescendingOrder 
                             if self.sort_order == Qt.SortOrder.AscendingOrder 
                             else Qt.SortOrder.AscendingOrder)
        else:
            self.sort_column = column
            self.sort_order = Qt.SortOrder.AscendingOrder
        
        # Apply sort
        ascending = self.sort_order == Qt.SortOrder.AscendingOrder
        
        try:
            self.filtered_data = self.filtered_data.sort_values(
                by=column_name,
                ascending=ascending,
                na_position='last'
            )
            
            # Reset to first page after sorting
            self.current_page = 0
            self._update_table()
            
            logger.debug(f"Sorted by column '{column_name}' ({'asc' if ascending else 'desc'})")
            
        except Exception as e:
            logger.error(f"Error sorting column '{column_name}': {e}")
            QMessageBox.warning(self, "Sort Error", f"Unable to sort by column '{column_name}'")
    
    def _update_sort_indicators(self):
        """Update visual sort indicators in header."""
        header = self.table.horizontalHeader()
        
        # Clear all indicators
        for i in range(header.count()):
            header.setSortIndicatorShown(False)
        
        # Show current sort indicator
        if self.sort_column is not None:
            header.setSortIndicator(self.sort_column, self.sort_order)
            header.setSortIndicatorShown(True)
    
    def _apply_filters(self, filters: Dict[str, str]):
        """Apply column filters to data."""
        if self.data is None:
            return
        
        self.active_filters = filters
        
        if not filters:
            # No filters, use original data
            self.filtered_data = self.data.copy()
        else:
            # Apply filters
            filtered = self.data.copy()
            
            for column, filter_text in filters.items():
                if column in filtered.columns:
                    # Case-insensitive string contains filter
                    mask = filtered[column].astype(str).str.lower().str.contains(
                        filter_text.lower(), na=False, regex=False
                    )
                    filtered = filtered[mask]
            
            self.filtered_data = filtered
        
        # Update totals and reset to first page
        self.total_rows = len(self.filtered_data)
        self.total_pages = max(1, (self.total_rows + self.page_size - 1) // self.page_size)
        self.current_page = 0
        
        self._update_table()
        self._update_info_label()
        
        logger.debug(f"Applied filters: {filters}, resulting in {self.total_rows} rows")
    
    def _go_to_page(self, page: int):
        """Go to specific page."""
        if 0 <= page < self.total_pages:
            self.current_page = page
            self._update_table()
    
    def _change_page_size(self, page_size: int):
        """Change page size and update display."""
        self.page_size = page_size
        self.config.page_size = page_size
        
        # Recalculate pages and adjust current page
        self.total_pages = max(1, (self.total_rows + self.page_size - 1) // self.page_size)
        
        # Ensure current page is still valid
        if self.current_page >= self.total_pages:
            self.current_page = max(0, self.total_pages - 1)
        
        self._update_table()
    
    def _handle_selection_change(self):
        """Handle table selection change."""
        selected_rows = self.table.selectionModel().selectedRows()
        if selected_rows:
            # Emit signal with the first selected row index (relative to displayed data)
            row = selected_rows[0].row()
            self.row_selected.emit(row)
    
    def _toggle_filters(self):
        """Toggle filter widget visibility."""
        if self.filter_widget:
            if self.filter_widget.isVisible():
                self.filter_widget.hide()
                self.filter_button.setText("🔍 Show Filters")
            else:
                self.filter_widget.show()
                self.filter_button.setText("🔍 Hide Filters")
    
    def _show_export_menu(self):
        """Show export options menu."""
        menu = QMenu()
        
        # Export all data
        csv_action = QAction("📄 Export as CSV", self)
        csv_action.triggered.connect(lambda: self._export_data('csv', False))
        menu.addAction(csv_action)
        
        excel_action = QAction("📊 Export as Excel", self)
        excel_action.triggered.connect(lambda: self._export_data('excel', False))
        menu.addAction(excel_action)
        
        json_action = QAction("🗄️ Export as JSON", self)
        json_action.triggered.connect(lambda: self._export_data('json', False))
        menu.addAction(json_action)
        
        # Separator
        menu.addSeparator()
        
        # Export selected only (if selection exists)
        if self.table.selectionModel().hasSelection():
            csv_selected = QAction("📄 Export Selected as CSV", self)
            csv_selected.triggered.connect(lambda: self._export_data('csv', True))
            menu.addAction(csv_selected)
            
            excel_selected = QAction("📊 Export Selected as Excel", self)
            excel_selected.triggered.connect(lambda: self._export_data('excel', True))
            menu.addAction(excel_selected)
        
        # Show menu
        menu.exec(self.export_button.mapToGlobal(self.export_button.rect().bottomLeft()))
    
    def _export_data(self, format_type: str, selected_only: bool = False):
        """Export table data to file."""
        if self.filtered_data is None or len(self.filtered_data) == 0:
            QMessageBox.information(self, "No Data", "No data available to export.")
            return
        
        # Determine export data
        if selected_only and self.table.selectionModel().hasSelection():
            selected_rows = [index.row() for index in self.table.selectionModel().selectedRows()]
            if self.displayed_data is not None:
                export_data = self.displayed_data.iloc[selected_rows]
            else:
                QMessageBox.warning(self, "Export Error", "Unable to determine selected data.")
                return
        else:
            export_data = self.filtered_data
        
        # Get filename
        file_extensions = {
            'csv': 'CSV Files (*.csv)',
            'excel': 'Excel Files (*.xlsx)',
            'json': 'JSON Files (*.json)'
        }
        
        filename, _ = QFileDialog.getSaveFileName(
            self,
            f"Export {format_type.upper()}",
            f"health_metrics.{format_type if format_type != 'excel' else 'xlsx'}",
            file_extensions[format_type]
        )
        
        if not filename:
            return
        
        # Start export in background
        self.export_worker = ExportWorker(export_data, filename, format_type, selected_only)
        self.export_worker.export_completed.connect(self._on_export_completed)
        self.export_worker.export_failed.connect(self._on_export_failed)
        
        # Show progress dialog
        self.export_progress = QProgressDialog("Exporting data...", "Cancel", 0, 100, self)
        self.export_progress.setWindowModality(Qt.WindowModality.WindowModal)
        self.export_progress.canceled.connect(self.export_worker.terminate)
        self.export_worker.progress_updated.connect(self.export_progress.setValue)
        
        self.export_worker.start()
        self.export_progress.show()
    
    def _on_export_completed(self, filename: str):
        """Handle export completion."""
        self.export_progress.close()
        QMessageBox.information(self, "Export Complete", f"Data exported successfully to:\n{filename}")
        self.data_exported.emit(filename)
    
    def _on_export_failed(self, error_msg: str):
        """Handle export failure."""
        self.export_progress.close()
        QMessageBox.critical(self, "Export Failed", error_msg)
    
    def _show_column_menu(self):
        """Show column visibility menu."""
        if self.data is None:
            return
        
        menu = QMenu()
        
        for i, column in enumerate(self.data.columns):
            action = QAction(column, self)
            action.setCheckable(True)
            action.setChecked(not self.table.isColumnHidden(i))
            action.triggered.connect(lambda checked, col=i: self.table.setColumnHidden(col, not checked))
            menu.addAction(action)
        
        menu.exec(self.columns_button.mapToGlobal(self.columns_button.rect().bottomLeft()))
    
    def _refresh_data(self):
        """Refresh table display."""
        if self.data is not None:
            # Reapply filters and update display
            self._apply_filters(self.active_filters)
            logger.info("Table data refreshed")
    
    def get_selected_data(self) -> Optional[pd.DataFrame]:
        """Get currently selected rows as DataFrame."""
        if not self.table.selectionModel().hasSelection() or self.displayed_data is None:
            return None
        
        selected_rows = [index.row() for index in self.table.selectionModel().selectedRows()]
        return self.displayed_data.iloc[selected_rows]
    
    def clear_data(self):
        """Clear all data from table."""
        self.data = None
        self.filtered_data = None
        self.displayed_data = None
        self.table.setRowCount(0)
        self.table.setColumnCount(0)
        self.total_rows = 0
        self.total_pages = 0
        self.current_page = 0
        self.pagination_widget.update_page_info()
        self._update_info_label()
        logger.info("Table data cleared")