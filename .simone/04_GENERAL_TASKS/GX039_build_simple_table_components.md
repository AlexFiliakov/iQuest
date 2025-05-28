---
task_id: GX039
status: completed
created: 2025-01-27
completed: 2025-05-28
complexity: medium
sprint_ref: S03
---

# Task G039: Build Simple Table Components

## Description
Create sortable metric tables with pagination for large datasets, export functionality, and clear table layouts. Build reusable table components that can display various types of health data efficiently.

## Goals
- [x] Create sortable metric tables
- [x] Implement pagination for large datasets
- [x] Add export functionality
- [x] Design clear table layouts
- [x] Support column customization
- [x] Add filtering capabilities
- [x] Implement row selection
- [x] Create responsive design

## Acceptance Criteria
- [x] Tables sort correctly by all columns
- [x] Pagination works smoothly with large datasets
- [x] Export functions for CSV/Excel work
- [x] Table layouts are clear and readable
- [x] Column widths adjust appropriately
- [x] Filtering is intuitive and fast
- [x] Row selection works correctly
- [x] Integration tests pass
- [x] Performance good with 10k+ rows

## Technical Details

### Table Features
1. **Sorting**:
   - Click column headers to sort
   - Visual indicators for sort direction
   - Multi-column sorting support
   - Stable sort algorithm

2. **Pagination**:
   - Configurable page sizes
   - Page navigation controls
   - Jump to page option
   - Total records display

3. **Export Options**:
   - CSV export
   - Excel export
   - JSON export
   - Selected rows only option

4. **Customization**:
   - Show/hide columns
   - Reorder columns
   - Resize columns
   - Save preferences

### Component Structure
```python
# Example structure
class MetricTable(QWidget):
    def __init__(self, config: TableConfig = None):
        super().__init__()
        self.config = config or TableConfig()
        self.current_page = 0
        self.sort_column = None
        self.sort_order = Qt.AscendingOrder
        self.setup_ui()
        
    def setup_ui(self):
        """Setup table UI with controls"""
        layout = QVBoxLayout()
        
        # Table widget
        self.table = QTableWidget()
        self.table.setSortingEnabled(True)
        self.table.setAlternatingRowColors(True)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        
        # Pagination controls
        self.pagination_widget = self.create_pagination_controls()
        
        # Export button
        self.export_button = QPushButton("Export")
        self.export_button.clicked.connect(self.show_export_dialog)
        
        layout.addWidget(self.table)
        layout.addWidget(self.pagination_widget)
        layout.addWidget(self.export_button)
        
        self.setLayout(layout)
        
    def load_data(self, data: pd.DataFrame):
        """Load data into table with pagination"""
        self.data = data
        self.total_rows = len(data)
        self.total_pages = (self.total_rows + self.config.page_size - 1) // self.config.page_size
        
        self.update_table()
```

### Sorting Implementation
```python
class SortableTable(MetricTable):
    def setup_sorting(self):
        """Setup custom sorting logic"""
        self.table.horizontalHeader().sectionClicked.connect(self.handle_sort)
        
    def handle_sort(self, column: int):
        """Handle column header click for sorting"""
        if self.sort_column == column:
            # Toggle sort order
            self.sort_order = (Qt.DescendingOrder 
                             if self.sort_order == Qt.AscendingOrder 
                             else Qt.AscendingOrder)
        else:
            # New column, default to ascending
            self.sort_column = column
            self.sort_order = Qt.AscendingOrder
            
        self.apply_sort()
        self.update_sort_indicators()
        
    def apply_sort(self):
        """Apply sorting to data"""
        if self.sort_column is not None:
            column_name = self.get_column_name(self.sort_column)
            ascending = self.sort_order == Qt.AscendingOrder
            
            self.data = self.data.sort_values(
                by=column_name,
                ascending=ascending,
                na_position='last'
            )
            
        self.update_table()
        
    def update_sort_indicators(self):
        """Update visual sort indicators"""
        header = self.table.horizontalHeader()
        
        # Clear all indicators
        for i in range(header.count()):
            header.setSortIndicator(i, Qt.AscendingOrder)
            header.setSortIndicatorShown(False)
            
        # Show current sort indicator
        if self.sort_column is not None:
            header.setSortIndicator(self.sort_column, self.sort_order)
            header.setSortIndicatorShown(True)
```

### Pagination Controls
```python
class PaginationWidget(QWidget):
    def __init__(self, table: MetricTable):
        super().__init__()
        self.table = table
        self.setup_ui()
        
    def setup_ui(self):
        """Create pagination controls"""
        layout = QHBoxLayout()
        
        # Previous button
        self.prev_button = QPushButton("Previous")
        self.prev_button.clicked.connect(self.go_previous)
        
        # Page info
        self.page_label = QLabel()
        self.update_page_label()
        
        # Next button
        self.next_button = QPushButton("Next")
        self.next_button.clicked.connect(self.go_next)
        
        # Page size selector
        self.page_size_combo = QComboBox()
        self.page_size_combo.addItems(["10", "25", "50", "100"])
        self.page_size_combo.currentTextChanged.connect(self.change_page_size)
        
        # Jump to page
        self.page_input = QSpinBox()
        self.page_input.setMinimum(1)
        self.page_input.valueChanged.connect(self.jump_to_page)
        
        layout.addWidget(self.prev_button)
        layout.addWidget(self.page_label)
        layout.addWidget(self.next_button)
        layout.addStretch()
        layout.addWidget(QLabel("Page size:"))
        layout.addWidget(self.page_size_combo)
        layout.addWidget(QLabel("Go to:"))
        layout.addWidget(self.page_input)
        
        self.setLayout(layout)
        
    def update_page_label(self):
        """Update page information label"""
        start = self.table.current_page * self.table.config.page_size + 1
        end = min(start + self.table.config.page_size - 1, self.table.total_rows)
        
        self.page_label.setText(
            f"Showing {start}-{end} of {self.table.total_rows} records"
        )
        
        # Update button states
        self.prev_button.setEnabled(self.table.current_page > 0)
        self.next_button.setEnabled(
            self.table.current_page < self.table.total_pages - 1
        )
```

### Export Functionality
```python
class ExportManager:
    def __init__(self, table: MetricTable):
        self.table = table
        
    def export_to_csv(self, filename: str, selected_only: bool = False):
        """Export table data to CSV"""
        data = self.get_export_data(selected_only)
        data.to_csv(filename, index=False)
        
    def export_to_excel(self, filename: str, selected_only: bool = False):
        """Export table data to Excel with formatting"""
        data = self.get_export_data(selected_only)
        
        with pd.ExcelWriter(filename, engine='openpyxl') as writer:
            data.to_excel(writer, index=False, sheet_name='Health Metrics')
            
            # Apply formatting
            worksheet = writer.sheets['Health Metrics']
            self.apply_excel_formatting(worksheet)
            
    def apply_excel_formatting(self, worksheet):
        """Apply formatting to Excel worksheet"""
        from openpyxl.styles import Font, PatternFill, Alignment
        
        # Header formatting
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
```

### Filtering
```python
class FilterableTable(MetricTable):
    def add_filtering(self):
        """Add filtering capability to table"""
        self.filter_row = QWidget()
        filter_layout = QHBoxLayout(self.filter_row)
        
        self.column_filters = {}
        
        for col in range(self.table.columnCount()):
            filter_input = QLineEdit()
            filter_input.setPlaceholderText("Filter...")
            filter_input.textChanged.connect(
                lambda text, c=col: self.apply_filter(c, text)
            )
            self.column_filters[col] = filter_input
            filter_layout.addWidget(filter_input)
            
        # Insert filter row below header
        self.layout().insertWidget(1, self.filter_row)
        
    def apply_filter(self, column: int, text: str):
        """Apply filter to specific column"""
        if not text:
            # Clear filter for this column
            self.active_filters.pop(column, None)
        else:
            self.active_filters[column] = text
            
        self.update_filtered_data()
        self.update_table()
```

### Table Configuration
```python
@dataclass
class TableConfig:
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
```

## Testing Requirements
- Unit tests for sorting logic
- Pagination edge case tests
- Export format validation
- Performance tests with large datasets
- Filter functionality tests
- Column operation tests
- Integration tests

## Notes
- Consider virtual scrolling for very large datasets
- Implement lazy loading for performance
- Provide keyboard navigation
- Consider accessibility requirements
- Document filtering syntax
- Plan for real-time data updates

## Claude Output Log
[2025-05-28 00:22]: Task status set to in_progress, beginning implementation of table components
[2025-05-28 00:26]: Created comprehensive table_components.py with MetricTable, PaginationWidget, FilterWidget, and ExportWorker classes
[2025-05-28 00:29]: Created test_table_components.py with comprehensive unit tests and table_usage_example.py for demonstration
[2025-05-28 00:32]: CODE REVIEW RESULT: **FAIL** - Sprint scope mismatch detected. Task references S03_UI_Framework but current sprint is S03_basic_analytics. Implementation quality is high but work is outside current sprint scope. Severity 8 issue requires user clarification on sprint alignment.
[2025-05-28 00:40]: Task completed by user directive. Renamed to GX039 and marked as completed. Sprint scope concerns overridden by user.