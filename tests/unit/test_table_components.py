"""Unit tests for table components."""

import pytest
import pandas as pd
import numpy as np
from unittest.mock import Mock, patch, MagicMock
from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import Qt
from PyQt6.QtTest import QTest

from src.ui.table_components import MetricTable, TableConfig, PaginationWidget, FilterWidget, ExportWorker


@pytest.fixture
def sample_data():
    """Create sample health data for testing."""
    np.random.seed(42)
    
    data = {
        'date': pd.date_range('2024-01-01', periods=100, freq='D'),
        'heart_rate': np.random.normal(70, 10, 100).astype(int),
        'steps': np.random.normal(8000, 2000, 100).astype(int),
        'sleep_hours': np.random.normal(7.5, 1, 100).round(1),
        'weight': np.random.normal(70, 5, 100).round(1),
        'source': np.random.choice(['iPhone', 'Apple Watch', 'Other'], 100)
    }
    
    return pd.DataFrame(data)


@pytest.fixture
def app():
    """Create QApplication instance for testing."""
    import sys
    if not QApplication.instance():
        return QApplication(sys.argv)
    return QApplication.instance()


class TestTableConfig:
    """Test TableConfig dataclass."""
    
    def test_default_config(self):
        """Test default configuration values."""
        config = TableConfig()
        
        assert config.page_size == 25
        assert config.alternating_rows is True
        assert config.grid_style == 'dotted'
        assert config.resizable_columns is True
        assert config.movable_columns is True
        assert config.hidden_columns == []
        assert config.selection_mode == 'row'
        assert config.multi_select is True
        assert config.export_formats == ['csv', 'excel', 'json']
        assert config.header_background == '#FF8C42'
        assert config.header_foreground == '#FFFFFF'
        assert config.selection_color == '#FFE5CC'
    
    def test_custom_config(self):
        """Test custom configuration values."""
        config = TableConfig(
            page_size=50,
            alternating_rows=False,
            grid_style='solid',
            export_formats=['csv', 'json']
        )
        
        assert config.page_size == 50
        assert config.alternating_rows is False
        assert config.grid_style == 'solid'
        assert config.export_formats == ['csv', 'json']


class TestExportWorker:
    """Test ExportWorker functionality."""
    
    def test_csv_export(self, sample_data, tmp_path):
        """Test CSV export functionality."""
        output_file = tmp_path / "test_export.csv"
        
        worker = ExportWorker(sample_data, str(output_file), 'csv')
        worker.run()
        
        # Check file was created
        assert output_file.exists()
        
        # Check file contents
        exported_data = pd.read_csv(output_file)
        assert len(exported_data) == len(sample_data)
        assert list(exported_data.columns) == list(sample_data.columns)
    
    def test_json_export(self, sample_data, tmp_path):
        """Test JSON export functionality."""
        output_file = tmp_path / "test_export.json"
        
        worker = ExportWorker(sample_data, str(output_file), 'json')
        worker.run()
        
        # Check file was created
        assert output_file.exists()
        
        # Check file is valid JSON
        import json
        with open(output_file, 'r') as f:
            data = json.load(f)
        
        assert len(data) == len(sample_data)
        assert 'date' in data[0]
        assert 'heart_rate' in data[0]
    
    @patch('pandas.ExcelWriter')
    def test_excel_export(self, mock_excel_writer, sample_data, tmp_path):
        """Test Excel export functionality."""
        output_file = tmp_path / "test_export.xlsx"
        
        worker = ExportWorker(sample_data, str(output_file), 'excel')
        worker.run()
        
        # Check that ExcelWriter was called
        mock_excel_writer.assert_called_once()


class TestFilterWidget:
    """Test FilterWidget functionality."""
    
    def test_filter_widget_creation(self, app):
        """Test filter widget creation with columns."""
        columns = ['date', 'heart_rate', 'steps']
        widget = FilterWidget(columns)
        
        assert len(widget.column_filters) == 3
        assert 'date' in widget.column_filters
        assert 'heart_rate' in widget.column_filters
        assert 'steps' in widget.column_filters
    
    def test_filter_signal_emission(self, app):
        """Test that filter changes emit correct signals."""
        columns = ['date', 'heart_rate', 'steps']
        widget = FilterWidget(columns)
        
        # Connect signal to mock
        signal_mock = Mock()
        widget.filter_changed.connect(signal_mock)
        
        # Simulate filter change
        widget.column_filters['heart_rate'].setText('70')
        
        # Verify signal was emitted
        signal_mock.assert_called()
        
        # Get the last call arguments
        args = signal_mock.call_args[0]
        assert 'heart_rate' in args[0]
        assert args[0]['heart_rate'] == '70'
    
    def test_clear_all_filters(self, app):
        """Test clearing all filters."""
        columns = ['date', 'heart_rate', 'steps']
        widget = FilterWidget(columns)
        
        # Set some filter values
        widget.column_filters['heart_rate'].setText('70')
        widget.column_filters['steps'].setText('8000')
        
        # Clear all filters
        widget._clear_all_filters()
        
        # Verify all inputs are empty
        for filter_input in widget.column_filters.values():
            assert filter_input.text() == ''


class TestPaginationWidget:
    """Test PaginationWidget functionality."""
    
    def test_pagination_widget_creation(self, app):
        """Test pagination widget creation."""
        table_mock = Mock()
        table_mock.current_page = 0
        table_mock.total_rows = 100
        table_mock.page_size = 25
        
        widget = PaginationWidget(table_mock)
        
        assert widget.table_widget == table_mock
        assert widget.prev_button is not None
        assert widget.next_button is not None
        assert widget.page_label is not None
        assert widget.page_size_combo is not None
        assert widget.page_input is not None
    
    def test_page_info_update(self, app):
        """Test page information update."""
        table_mock = Mock()
        table_mock.current_page = 0
        table_mock.total_rows = 100
        table_mock.page_size = 25
        
        widget = PaginationWidget(table_mock)
        widget.update_page_info()
        
        # Check page label text
        expected_text = "Showing 1-25 of 100 records"
        assert expected_text in widget.page_label.text()
        
        # Check button states
        assert not widget.prev_button.isEnabled()  # First page
        assert widget.next_button.isEnabled()  # More pages available
    
    def test_pagination_signals(self, app):
        """Test pagination signal emission."""
        table_mock = Mock()
        table_mock.current_page = 0
        table_mock.total_rows = 100
        table_mock.page_size = 25
        
        widget = PaginationWidget(table_mock)
        
        # Connect signals to mocks
        page_signal_mock = Mock()
        size_signal_mock = Mock()
        widget.page_changed.connect(page_signal_mock)
        widget.page_size_changed.connect(size_signal_mock)
        
        # Simulate next button click
        widget._go_next()
        page_signal_mock.assert_called_with(1)
        
        # Simulate page size change
        widget.page_size_combo.setCurrentText('50')
        widget._change_page_size('50')
        size_signal_mock.assert_called_with(50)


class TestMetricTable:
    """Test MetricTable functionality."""
    
    def test_table_creation(self, app):
        """Test table creation with default config."""
        table = MetricTable()
        
        assert table.config is not None
        assert table.table is not None
        assert table.pagination_widget is not None
        assert table.current_page == 0
        assert table.page_size == 25
    
    def test_table_creation_with_config(self, app):
        """Test table creation with custom config."""
        config = TableConfig(page_size=50, alternating_rows=False)
        table = MetricTable(config)
        
        assert table.config.page_size == 50
        assert table.config.alternating_rows is False
        assert table.page_size == 50
    
    def test_load_data(self, app, sample_data):
        """Test loading data into table."""
        table = MetricTable()
        table.load_data(sample_data)
        
        assert table.data is not None
        assert len(table.data) == len(sample_data)
        assert table.total_rows == len(sample_data)
        assert table.table.columnCount() == len(sample_data.columns)
        assert table.table.rowCount() == min(25, len(sample_data))  # Page size
    
    def test_pagination(self, app, sample_data):
        """Test pagination functionality."""
        config = TableConfig(page_size=10)
        table = MetricTable(config)
        table.load_data(sample_data)
        
        # Check initial state
        assert table.current_page == 0
        assert table.total_pages == 10  # 100 rows / 10 per page
        assert table.table.rowCount() == 10
        
        # Go to next page
        table._go_to_page(1)
        assert table.current_page == 1
        assert table.table.rowCount() == 10
        
        # Go to last page
        table._go_to_page(9)
        assert table.current_page == 9
        assert table.table.rowCount() == 10
    
    def test_sorting(self, app, sample_data):
        """Test sorting functionality."""
        table = MetricTable()
        table.load_data(sample_data)
        
        # Sort by heart_rate column (column 1)
        heart_rate_col = 1
        table._handle_sort(heart_rate_col)
        
        assert table.sort_column == heart_rate_col
        assert table.sort_order == Qt.SortOrder.AscendingOrder
        
        # Sort again to test descending
        table._handle_sort(heart_rate_col)
        assert table.sort_order == Qt.SortOrder.DescendingOrder
    
    def test_filtering(self, app, sample_data):
        """Test filtering functionality."""
        table = MetricTable()
        table.load_data(sample_data)
        
        initial_rows = table.total_rows
        
        # Apply filter
        filters = {'source': 'iPhone'}
        table._apply_filters(filters)
        
        # Should have fewer rows after filtering
        assert table.total_rows <= initial_rows
        assert table.active_filters == filters
        
        # Clear filters
        table._apply_filters({})
        assert table.total_rows == initial_rows
        assert table.active_filters == {}
    
    def test_page_size_change(self, app, sample_data):
        """Test changing page size."""
        table = MetricTable()
        table.load_data(sample_data)
        
        initial_page_size = table.page_size
        assert initial_page_size == 25
        
        # Change page size
        table._change_page_size(50)
        
        assert table.page_size == 50
        assert table.config.page_size == 50
        assert table.table.rowCount() == min(50, len(sample_data))
    
    def test_empty_data_handling(self, app):
        """Test handling of empty data."""
        table = MetricTable()
        empty_data = pd.DataFrame()
        table.load_data(empty_data)
        
        assert table.total_rows == 0
        assert table.table.rowCount() == 0
        assert table.table.columnCount() == 0
    
    def test_clear_data(self, app, sample_data):
        """Test clearing table data."""
        table = MetricTable()
        table.load_data(sample_data)
        
        # Verify data is loaded
        assert table.data is not None
        assert table.total_rows > 0
        
        # Clear data
        table.clear_data()
        
        # Verify data is cleared
        assert table.data is None
        assert table.total_rows == 0
        assert table.table.rowCount() == 0
        assert table.table.columnCount() == 0
    
    @patch('PyQt6.QtWidgets.QFileDialog.getSaveFileName')
    def test_export_data_csv(self, mock_file_dialog, app, sample_data, tmp_path):
        """Test CSV export functionality."""
        output_file = tmp_path / "test_export.csv"
        mock_file_dialog.return_value = (str(output_file), "CSV Files (*.csv)")
        
        table = MetricTable()
        table.load_data(sample_data)
        
        # Mock the export worker to avoid threading in tests
        with patch.object(table, 'export_worker') as mock_worker:
            table._export_data('csv', False)
            # Verify export was initiated
            assert mock_file_dialog.called
    
    def test_selected_data_retrieval(self, app, sample_data):
        """Test getting selected data."""
        table = MetricTable()
        table.load_data(sample_data)
        
        # Initially no selection
        selected = table.get_selected_data()
        assert selected is None
        
        # Simulate selection (would require more complex mocking in real test)
        # For now, just verify the method exists and handles no selection
        assert hasattr(table, 'get_selected_data')


class TestIntegration:
    """Integration tests for table components."""
    
    def test_table_with_large_dataset(self, app):
        """Test table performance with large dataset."""
        # Create large dataset
        np.random.seed(42)
        large_data = pd.DataFrame({
            'id': range(10000),
            'value': np.random.random(10000),
            'category': np.random.choice(['A', 'B', 'C'], 10000),
            'timestamp': pd.date_range('2020-01-01', periods=10000, freq='H')
        })
        
        config = TableConfig(page_size=100)
        table = MetricTable(config)
        table.load_data(large_data)
        
        assert table.total_rows == 10000
        assert table.total_pages == 100
        assert table.table.rowCount() == 100  # One page worth
    
    def test_table_filter_and_sort_combination(self, app, sample_data):
        """Test combining filters and sorting."""
        table = MetricTable()
        table.load_data(sample_data)
        
        # Apply filter first
        filters = {'source': 'iPhone'}
        table._apply_filters(filters)
        filtered_count = table.total_rows
        
        # Then sort
        table._handle_sort(1)  # Sort by heart_rate
        
        # Data should still be filtered and sorted
        assert table.total_rows == filtered_count
        assert table.sort_column == 1
        assert table.active_filters == filters
    
    def test_table_pagination_with_filters(self, app, sample_data):
        """Test pagination working correctly with filters."""
        config = TableConfig(page_size=10)
        table = MetricTable(config)
        table.load_data(sample_data)
        
        # Apply filter
        filters = {'source': 'iPhone'}
        table._apply_filters(filters)
        
        # Check pagination updated
        assert table.current_page == 0  # Reset to first page
        assert table.total_pages <= 10  # Should be fewer pages than original
        
        # Navigate pages
        if table.total_pages > 1:
            table._go_to_page(1)
            assert table.current_page == 1


# Performance and stress tests
class TestPerformance:
    """Performance tests for table components."""
    
    def test_sorting_performance(self, app):
        """Test sorting performance with medium dataset."""
        # Create medium dataset
        np.random.seed(42)
        data = pd.DataFrame({
            'numeric': np.random.random(5000),
            'text': [f"item_{i}" for i in range(5000)],
            'date': pd.date_range('2020-01-01', periods=5000, freq='D')
        })
        
        table = MetricTable()
        table.load_data(data)
        
        import time
        start_time = time.time()
        
        # Sort by numeric column
        table._handle_sort(0)
        
        sort_time = time.time() - start_time
        
        # Sorting should be reasonably fast (less than 1 second)
        assert sort_time < 1.0
        assert table.sort_column == 0
    
    def test_filtering_performance(self, app):
        """Test filtering performance with medium dataset."""
        # Create medium dataset with searchable text
        np.random.seed(42)
        data = pd.DataFrame({
            'category': np.random.choice(['apple', 'banana', 'cherry', 'date'], 5000),
            'value': np.random.random(5000),
            'id': range(5000)
        })
        
        table = MetricTable()
        table.load_data(data)
        
        import time
        start_time = time.time()
        
        # Apply filter
        filters = {'category': 'apple'}
        table._apply_filters(filters)
        
        filter_time = time.time() - start_time
        
        # Filtering should be reasonably fast (less than 1 second)
        assert filter_time < 1.0
        assert table.total_rows < 5000  # Should have filtered results


if __name__ == '__main__':
    pytest.main([__file__])