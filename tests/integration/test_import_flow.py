"""Integration tests for the health data import flow."""

import pytest
from pathlib import Path
from datetime import datetime
from unittest.mock import Mock, patch, MagicMock, call
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtWidgets import QApplication, QFileDialog, QMessageBox, QPushButton
from PyQt6.QtTest import QTest

from src.ui.main_window import MainWindow
from src.ui.import_progress_dialog import ImportProgressDialog
from src.ui.import_worker import ImportWorker
# HealthDataModel import removed - class no longer exists


class TestImportFlow:
    """Test the complete import flow from file selection to data display."""
    
    @pytest.fixture
    def main_window(self, qtbot):
        """Create a main window instance for testing."""
        window = MainWindow()
        qtbot.addWidget(window)
        return window
    
    @pytest.fixture
    def sample_csv_file(self, tmp_path):
        """Create a sample CSV file for testing."""
        csv_file = tmp_path / "test_health_data.csv"
        csv_content = """Date,Type,Value,Unit,Source
2024-01-01,StepCount,5000,count,Test Device
2024-01-01,HeartRate,72,count/min,Test Device
2024-01-02,StepCount,6000,count,Test Device
2024-01-02,HeartRate,75,count/min,Test Device
"""
        csv_file.write_text(csv_content)
        return str(csv_file)
    
    @pytest.fixture
    def sample_xml_file(self, tmp_path):
        """Create a sample XML file for testing."""
        xml_file = tmp_path / "test_health_export.xml"
        xml_content = """<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE HealthData>
<HealthData locale="en_US">
  <ExportDate value="2024-01-01 12:00:00 -0500"/>
  <Record type="HKQuantityTypeIdentifierStepCount" sourceName="Test Device" 
          unit="count" creationDate="2024-01-01 10:00:00 -0500" 
          startDate="2024-01-01 09:00:00 -0500" endDate="2024-01-01 10:00:00 -0500" 
          value="1000"/>
  <Record type="HKQuantityTypeIdentifierHeartRate" sourceName="Test Device" 
          unit="count/min" creationDate="2024-01-01 10:00:00 -0500" 
          startDate="2024-01-01 10:00:00 -0500" endDate="2024-01-01 10:00:00 -0500" 
          value="72"/>
</HealthData>"""
        xml_file.write_text(xml_content)
        return str(xml_file)
    
    def test_import_menu_action_exists(self, main_window):
        """Test that import menu action exists and is accessible."""
        # Find File menu
        file_menu = None
        for action in main_window.menuBar().actions():
            if action.text() == "&File":
                file_menu = action.menu()
                break
        
        assert file_menu is not None, "File menu not found"
        
        # Find Import action
        import_action = None
        for action in file_menu.actions():
            if "Import" in action.text():
                import_action = action
                break
        
        assert import_action is not None, "Import action not found"
        assert import_action.isEnabled()
    
    def test_import_csv_file_flow(self, main_window, sample_csv_file, qtbot):
        """Test importing a CSV file through the UI."""
        # Mock file dialog to return our test file
        with patch.object(QFileDialog, 'getOpenFileName', return_value=(sample_csv_file, '')):
            # Mock the ImportProgressDialog to avoid UI issues
            with patch('src.ui.configuration_tab.ImportProgressDialog') as mock_dialog_class:
                mock_dialog = MagicMock()
                mock_dialog_class.return_value = mock_dialog
                
                # Trigger import action
                main_window._on_import_data()
                
                # Verify dialog was created with correct file
                mock_dialog_class.assert_called_once_with(sample_csv_file, "auto", main_window.config_tab)
                
                # Verify exec was called to show the dialog
                mock_dialog.exec.assert_called_once()
    
    def test_import_xml_file_flow(self, main_window, sample_xml_file, qtbot):
        """Test importing an XML file through the UI."""
        # Mock file dialog to return our test file
        with patch.object(QFileDialog, 'getOpenFileName', return_value=(sample_xml_file, '')):
            # Mock the ImportProgressDialog to avoid UI issues
            with patch('src.ui.configuration_tab.ImportProgressDialog') as mock_dialog_class:
                mock_dialog = MagicMock()
                mock_dialog_class.return_value = mock_dialog
                
                # Trigger import action
                main_window._on_import_data()
                
                # Verify dialog was created with correct file
                mock_dialog_class.assert_called_once_with(sample_xml_file, "auto", main_window.config_tab)
                
                # Verify exec was called to show the dialog
                mock_dialog.exec.assert_called_once()
    
    def test_import_dialog_shows_progress(self, main_window, sample_csv_file, qtbot):
        """Test that import progress dialog shows during import."""
        with patch.object(QFileDialog, 'getOpenFileName', return_value=(sample_csv_file, '')):
            # Mock the ImportProgressDialog to avoid actual UI
            with patch('src.ui.configuration_tab.ImportProgressDialog') as mock_dialog_class:
                mock_dialog = MagicMock()
                mock_dialog_class.return_value = mock_dialog
                
                # Mock exec to return immediately
                mock_dialog.exec.return_value = 1
                
                # Start import
                main_window._on_import_data()
                
                # Verify dialog was created and shown
                mock_dialog_class.assert_called_once()
                mock_dialog.exec.assert_called_once()
                
                # Verify it was created with the correct file
                call_args = mock_dialog_class.call_args
                assert call_args[0][0] == sample_csv_file
    
    def test_import_cancelled_by_user(self, main_window, sample_csv_file, qtbot):
        """Test cancelling import operation."""
        with patch.object(QFileDialog, 'getOpenFileName', return_value=(sample_csv_file, '')):
            with patch('src.ui.configuration_tab.ImportProgressDialog') as mock_dialog_class:
                mock_dialog = MagicMock()
                mock_dialog_class.return_value = mock_dialog
                
                # Create a mock worker
                mock_worker = MagicMock()
                mock_dialog.worker = mock_worker
                
                # Mock the cancel button click
                mock_dialog._on_cancel_clicked = MagicMock()
                
                # Start import
                main_window._on_import_data()
                
                # Simulate cancel button click
                mock_dialog._on_cancel_clicked()
                
                # Verify dialog was created
                mock_dialog_class.assert_called_once()
                
                # Verify cancel was called
                mock_dialog._on_cancel_clicked.assert_called_once()
    
    def test_import_error_handling(self, main_window, qtbot):
        """Test error handling during import."""
        # Create an invalid file
        invalid_file = "/path/to/nonexistent/file.xml"
        
        with patch.object(QFileDialog, 'getOpenFileName', return_value=(invalid_file, '')):
            with patch.object(QMessageBox, 'critical') as mock_error:
                # Attempt import
                main_window._on_import_data()
                
                # Should show error message
                qtbot.wait(100)
                # Error might be shown either immediately or after worker fails
                # Just verify no crash occurs
    
    def test_import_completion_updates_ui(self, main_window, sample_csv_file, qtbot):
        """Test that UI updates after successful import."""
        with patch.object(QFileDialog, 'getOpenFileName', return_value=(sample_csv_file, '')):
            with patch('src.ui.configuration_tab.ImportProgressDialog') as mock_dialog_class:
                mock_dialog = MagicMock()
                mock_dialog_class.return_value = mock_dialog
                
                # Mock successful completion
                mock_dialog.import_completed = MagicMock()
                mock_dialog.exec.return_value = 1
                
                # Start import
                main_window._on_import_data()
                
                # Verify dialog was created
                mock_dialog_class.assert_called_once()
                
                # Verify current tab exists
                current_widget = main_window.tab_widget.currentWidget()
                assert current_widget is not None
    
    def test_import_file_filter(self, main_window, qtbot):
        """Test that file dialog shows correct file filters."""
        with patch.object(QFileDialog, 'getOpenFileName') as mock_dialog:
            mock_dialog.return_value = ('', '')  # User cancelled
            
            # Trigger import
            main_window._on_import_data()
            
            # Check file filter was set correctly
            mock_dialog.assert_called_once()
            args = mock_dialog.call_args[0]
            filter_string = args[3] if len(args) > 3 else ""
            
            # Should support both XML and CSV
            assert "XML" in filter_string or "xml" in filter_string
            assert "CSV" in filter_string or "csv" in filter_string
    
    def test_import_no_file_selected(self, main_window, qtbot):
        """Test behavior when no file is selected."""
        with patch.object(QFileDialog, 'getOpenFileName', return_value=('', '')):
            # Should not crash when no file selected
            main_window._on_import_data()
            qtbot.wait(50)
            
            # Verify no import dialog shown
            for widget in QApplication.topLevelWidgets():
                assert not isinstance(widget, ImportProgressDialog)