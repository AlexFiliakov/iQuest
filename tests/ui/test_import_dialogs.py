"""UI tests for import dialogs."""

import pytest
from unittest.mock import Mock, patch, MagicMock
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtWidgets import QApplication, QPushButton, QProgressBar, QLabel, QDialogButtonBox
from PyQt6.QtTest import QTest

from src.ui.import_progress_dialog import ImportProgressDialog, ImportSummaryDialog
from src.ui.style_manager import StyleManager


class TestImportProgressDialog:
    """Test the import progress dialog UI."""
    
    @pytest.fixture
    def progress_dialog(self, qtbot):
        """Create an import progress dialog for testing."""
        dialog = ImportProgressDialog("test_file.xml", "xml", None)
        qtbot.addWidget(dialog)
        return dialog
    
    def test_dialog_initialization(self, progress_dialog):
        """Test that dialog initializes with correct elements."""
        # Check title
        assert progress_dialog.windowTitle() == "Importing Health Data"
        
        # Check for progress bar
        progress_bar = progress_dialog.findChild(QProgressBar)
        assert progress_bar is not None
        assert progress_bar.value() == 0
        
        # Check for status label
        status_label = progress_dialog.findChild(QLabel, "statusLabel")
        assert status_label is not None
        
        # Check for cancel button
        button_box = progress_dialog.findChild(QDialogButtonBox)
        assert button_box is not None
        cancel_button = button_box.button(QDialogButtonBox.StandardButton.Cancel)
        assert cancel_button is not None
    
    def test_progress_updates(self, progress_dialog, qtbot):
        """Test that progress updates are reflected in UI."""
        # Update progress
        progress_dialog._on_progress_updated(50, "Processing records...", 5000)
        qtbot.wait(50)
        
        # Check progress bar
        progress_bar = progress_dialog.findChild(QProgressBar)
        assert progress_bar.value() == 50
        
        # Check status text
        status_label = progress_dialog.findChild(QLabel, "statusLabel")
        assert "Processing records..." in status_label.text()
        
        # Check record count if displayed
        if hasattr(progress_dialog, 'record_label'):
            assert "5000" in progress_dialog.record_label.text() or "5,000" in progress_dialog.record_label.text()
    
    def test_completion_handling(self, progress_dialog, qtbot):
        """Test dialog behavior on completion."""
        result = {
            'record_count': 10000,
            'import_type': 'xml',
            'import_time': 12.5,
            'file_path': 'test_file.xml'
        }
        
        # Complete the import
        progress_dialog._on_import_completed(result)
        qtbot.wait(600)  # Wait for auto-close timer (500ms + buffer)
        
        # Progress should be at 100%
        progress_bar = progress_dialog.findChild(QProgressBar)
        assert progress_bar.value() == 100
        
        # Dialog should close or show completion
        # Check if summary dialog is shown
        summary_shown = False
        for widget in QApplication.topLevelWidgets():
            if isinstance(widget, ImportSummaryDialog):
                summary_shown = True
                break
        
        # Either summary is shown or dialog is accepted
        assert summary_shown or progress_dialog.result() == ImportProgressDialog.DialogCode.Accepted
    
    def test_cancel_functionality(self, progress_dialog, qtbot):
        """Test cancelling the import."""
        # Mock the worker
        mock_worker = MagicMock()
        progress_dialog.worker = mock_worker
        
        # Find and click cancel button
        button_box = progress_dialog.findChild(QDialogButtonBox)
        cancel_button = button_box.button(QDialogButtonBox.StandardButton.Cancel)
        
        QTest.mouseClick(cancel_button, Qt.MouseButton.LeftButton)
        qtbot.wait(50)
        
        # Worker should be stopped
        mock_worker.stop.assert_called_once()
        
        # Dialog should be rejected
        assert progress_dialog.result() == ImportProgressDialog.DialogCode.Rejected
    
    def test_error_handling(self, progress_dialog, qtbot):
        """Test error display in dialog."""
        error_title = "Import Error"
        error_message = "Failed to parse XML file"
        
        # Trigger error
        progress_dialog._on_import_error(error_title, error_message)
        qtbot.wait(50)
        
        # Should show error in status
        status_label = progress_dialog.findChild(QLabel, "statusLabel")
        assert "Error" in status_label.text() or error_message in status_label.text()
        
        # Dialog should allow closing
        button_box = progress_dialog.findChild(QDialogButtonBox)
        assert button_box.isEnabled()


class TestImportSummaryDialog:
    """Test the import summary dialog UI."""
    
    @pytest.fixture
    def summary_result(self):
        """Create a sample import result."""
        return {
            'record_count': 10000,
            'import_type': 'xml',
            'import_time': 12.5,
            'file_path': 'health_export.xml'
        }
    
    @pytest.fixture
    def summary_dialog(self, summary_result, qtbot):
        """Create an import summary dialog for testing."""
        dialog = ImportSummaryDialog(summary_result, None)
        qtbot.addWidget(dialog)
        return dialog
    
    def test_summary_display(self, summary_dialog, summary_result):
        """Test that summary shows correct information."""
        # Check window title
        assert "Import Complete" in summary_dialog.windowTitle() or "Success" in summary_dialog.windowTitle()
        
        # Check for record count display
        content = summary_dialog.findChildren(QLabel)
        labels_text = " ".join([label.text() for label in content])
        
        # Should show record count
        assert "10000" in labels_text or "10,000" in labels_text
        
        # Should show time taken
        assert "12.5" in labels_text or "12 seconds" in labels_text or "13 seconds" in labels_text
        
        # Should show file type
        assert "xml" in labels_text.lower() or "XML" in labels_text
    
    def test_ok_button(self, summary_dialog, qtbot):
        """Test that OK button closes dialog."""
        # Find OK button
        button_box = summary_dialog.findChild(QDialogButtonBox)
        ok_button = button_box.button(QDialogButtonBox.StandardButton.Ok)
        
        assert ok_button is not None
        assert ok_button.isEnabled()
        
        # Click OK
        QTest.mouseClick(ok_button, Qt.MouseButton.LeftButton)
        qtbot.wait(50)
        
        # Dialog should be accepted
        assert summary_dialog.result() == ImportSummaryDialog.DialogCode.Accepted
    
    def test_summary_dialog_styling(self, summary_dialog):
        """Test that summary dialog has appropriate styling."""
        # Should have style applied
        assert summary_dialog.styleSheet() != ""
        
        # Check for success styling elements
        style = summary_dialog.styleSheet()
        # Should have some indication of success (green color, etc.)
        assert "#" in style  # Has color definitions
    
    def test_large_import_summary(self, qtbot):
        """Test summary display for large imports."""
        large_result = {
            'record_count': 1000000,
            'import_type': 'xml',
            'import_time': 300.5,  # 5 minutes
            'file_path': 'large_export.xml'
        }
        
        dialog = ImportSummaryDialog(large_result, None)
        qtbot.addWidget(dialog)
        
        # Check formatting of large numbers
        content = dialog.findChildren(QLabel)
        labels_text = " ".join([label.text() for label in content])
        
        # Should format large numbers nicely
        assert "1,000,000" in labels_text or "1000000" in labels_text or "1M" in labels_text
        
        # Should format time appropriately (minutes)
        assert "5" in labels_text and ("minute" in labels_text.lower() or "min" in labels_text.lower())
    
    def test_csv_import_summary(self, qtbot):
        """Test summary for CSV imports."""
        csv_result = {
            'record_count': 5000,
            'import_type': 'csv',
            'import_time': 2.3,
            'file_path': 'health_data.csv'
        }
        
        dialog = ImportSummaryDialog(csv_result, None)
        qtbot.addWidget(dialog)
        
        # Check CSV-specific display
        content = dialog.findChildren(QLabel)
        labels_text = " ".join([label.text() for label in content])
        
        assert "csv" in labels_text.lower() or "CSV" in labels_text