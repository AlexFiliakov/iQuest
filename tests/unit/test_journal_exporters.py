"""Unit tests for journal export functionality.

This module tests the journal export system including JSON and PDF exporters,
export dialog, and integration with the journal editor widget.
"""

import unittest
from unittest.mock import Mock, patch, MagicMock
from datetime import date, datetime
from pathlib import Path
import json
import tempfile
import os

from PyQt6.QtCore import Qt, QDate
from PyQt6.QtWidgets import QApplication, QDialog

from src.models import JournalEntry
from src.exporters import JSONExporter, PDFExporter, ExportOptions, ExportResult
from src.ui.journal_export_dialog import JournalExportDialog, DateRangeSelector
from src.data_access import JournalDAO


class TestJSONExporter(unittest.TestCase):
    """Test cases for JSONExporter class."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.exporter = JSONExporter()
        
        # Create sample entries
        self.entries = [
            JournalEntry(
                id=1,
                entry_date=date(2024, 1, 1),
                entry_type='daily',
                content='New Year journal entry',
                created_at=datetime(2024, 1, 1, 20, 0),
                updated_at=datetime(2024, 1, 1, 20, 0)
            ),
            JournalEntry(
                id=2,
                entry_date=date(2024, 1, 7),
                entry_type='weekly',
                week_start_date=date(2024, 1, 1),
                content='First week of the year',
                created_at=datetime(2024, 1, 7, 19, 0),
                updated_at=datetime(2024, 1, 7, 19, 0)
            ),
            JournalEntry(
                id=3,
                entry_date=date(2024, 1, 31),
                entry_type='monthly',
                month_year='2024-01',
                content='January monthly reflection',
                created_at=datetime(2024, 1, 31, 21, 0),
                updated_at=datetime(2024, 1, 31, 21, 0)
            )
        ]
        
    def tearDown(self):
        """Clean up test files."""
        for file in Path(self.temp_dir).glob('*'):
            file.unlink()
        os.rmdir(self.temp_dir)
        
    def test_export_basic(self):
        """Test basic JSON export functionality."""
        output_path = os.path.join(self.temp_dir, 'test_export.json')
        
        result = self.exporter.export(self.entries, output_path)
        
        # Check result
        self.assertTrue(result.success)
        self.assertEqual(result.entries_exported, 3)
        self.assertEqual(result.file_path, output_path)
        self.assertGreater(result.file_size, 0)
        
        # Check file contents
        with open(output_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            
        self.assertIn('export_metadata', data)
        self.assertIn('entries', data)
        self.assertEqual(len(data['entries']), 3)
        
        # Check first entry
        first_entry = data['entries'][0]
        self.assertEqual(first_entry['id'], 1)
        self.assertEqual(first_entry['entry_date'], '2024-01-01')
        self.assertEqual(first_entry['entry_type'], 'daily')
        self.assertEqual(first_entry['content'], 'New Year journal entry')
        
    def test_export_with_options(self):
        """Test JSON export with custom options."""
        options = ExportOptions(
            include_metadata=False,
            pretty_print=False,
            include_statistics=False
        )
        exporter = JSONExporter(options)
        output_path = os.path.join(self.temp_dir, 'test_compact.json')
        
        result = exporter.export(self.entries, output_path)
        
        self.assertTrue(result.success)
        
        # Check file is compact (no pretty printing)
        with open(output_path, 'r') as f:
            content = f.read()
            self.assertNotIn('\n  ', content)  # No indentation
            
        # Check no metadata
        data = json.loads(content)
        self.assertNotIn('export_metadata', data)
        
    def test_export_empty_entries(self):
        """Test exporting empty entry list."""
        output_path = os.path.join(self.temp_dir, 'test_empty.json')
        
        result = self.exporter.export([], output_path)
        
        self.assertTrue(result.success)
        self.assertEqual(result.entries_exported, 0)
        self.assertIn('No entries', result.warnings)
        
    def test_export_with_max_entries(self):
        """Test export with maximum entry limit."""
        options = ExportOptions(max_entries=2)
        exporter = JSONExporter(options)
        output_path = os.path.join(self.temp_dir, 'test_limited.json')
        
        result = exporter.export(self.entries, output_path)
        
        self.assertTrue(result.success)
        self.assertEqual(result.entries_exported, 2)
        self.assertIn('Limited export to 2 entries', result.warnings)
        
    def test_export_statistics(self):
        """Test export with statistics included."""
        options = ExportOptions(include_statistics=True)
        exporter = JSONExporter(options)
        output_path = os.path.join(self.temp_dir, 'test_stats.json')
        
        result = exporter.export(self.entries, output_path)
        
        self.assertTrue(result.success)
        
        with open(output_path, 'r') as f:
            data = json.load(f)
            
        self.assertIn('statistics', data['export_metadata'])
        stats = data['export_metadata']['statistics']
        self.assertIn('total_words', stats)
        self.assertIn('entries_by_day_of_week', stats)


class TestPDFExporter(unittest.TestCase):
    """Test cases for PDFExporter class."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.exporter = PDFExporter()
        
        # Create sample entry
        self.entries = [
            JournalEntry(
                id=1,
                entry_date=date(2024, 1, 15),
                entry_type='daily',
                content='Test journal entry with **bold** and *italic* text.',
                created_at=datetime(2024, 1, 15, 20, 0),
                updated_at=datetime(2024, 1, 15, 20, 0)
            )
        ]
        
    def tearDown(self):
        """Clean up test files."""
        for file in Path(self.temp_dir).glob('*'):
            file.unlink()
        os.rmdir(self.temp_dir)
        
    def test_pdf_export_basic(self):
        """Test basic PDF export functionality."""
        output_path = os.path.join(self.temp_dir, 'test_export.pdf')
        
        result = self.exporter.export(self.entries, output_path)
        
        # Check result
        self.assertTrue(result.success)
        self.assertEqual(result.entries_exported, 1)
        self.assertEqual(result.file_path, output_path)
        self.assertGreater(result.file_size, 0)
        
        # Check file exists and is PDF
        self.assertTrue(os.path.exists(output_path))
        with open(output_path, 'rb') as f:
            header = f.read(4)
            self.assertEqual(header, b'%PDF')  # PDF header
            
    def test_pdf_export_with_options(self):
        """Test PDF export with custom options."""
        options = ExportOptions(
            extra_options={
                'include_cover': False,
                'include_toc': False,
                'parse_markdown': False,
                'page_size': 'a4'
            }
        )
        exporter = PDFExporter(options)
        output_path = os.path.join(self.temp_dir, 'test_custom.pdf')
        
        result = exporter.export(self.entries, output_path)
        
        self.assertTrue(result.success)
        # Metadata should reflect options
        self.assertFalse(result.metadata['include_cover'])
        self.assertFalse(result.metadata['include_toc'])
        
    def test_pdf_markdown_parsing(self):
        """Test PDF export with markdown content."""
        # Entry with rich markdown
        markdown_entry = JournalEntry(
            id=1,
            entry_date=date(2024, 1, 1),
            entry_type='daily',
            content="""# Health Journal

## Morning Routine
- **Exercise**: 30 minutes cardio
- *Breakfast*: Oatmeal with fruits

> Remember to stay hydrated!

### Evening Notes
1. Took medications
2. Early sleep""",
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        
        output_path = os.path.join(self.temp_dir, 'test_markdown.pdf')
        result = self.exporter.export([markdown_entry], output_path)
        
        self.assertTrue(result.success)
        self.assertTrue(os.path.exists(output_path))


class TestExportDialog(unittest.TestCase):
    """Test cases for JournalExportDialog."""
    
    @classmethod
    def setUpClass(cls):
        """Set up QApplication for Qt tests."""
        if not QApplication.instance():
            cls.app = QApplication([])
        else:
            cls.app = QApplication.instance()
            
    def setUp(self):
        """Set up test fixtures."""
        self.dialog = JournalExportDialog()
        
    def test_dialog_initialization(self):
        """Test dialog is properly initialized."""
        self.assertIsNotNone(self.dialog.date_range_selector)
        self.assertIsNotNone(self.dialog.json_options)
        self.assertIsNotNone(self.dialog.pdf_options)
        self.assertTrue(self.dialog.json_radio.isChecked())
        
    def test_format_switching(self):
        """Test switching between export formats."""
        # Initially JSON should be selected
        self.assertEqual(self.dialog.options_stack.currentIndex(), 0)
        
        # Switch to PDF
        self.dialog.pdf_radio.click()
        self.assertEqual(self.dialog.options_stack.currentIndex(), 1)
        
        # Switch back to JSON
        self.dialog.json_radio.click()
        self.assertEqual(self.dialog.options_stack.currentIndex(), 0)
        
    def test_json_options(self):
        """Test JSON export options."""
        options = self.dialog.json_options.get_options()
        
        self.assertIn('pretty_print', options)
        self.assertIn('include_metadata', options)
        self.assertIn('include_statistics', options)
        self.assertIn('add_bom', options)
        
        # Test changing options
        self.dialog.json_options.pretty_print_check.setChecked(False)
        options = self.dialog.json_options.get_options()
        self.assertFalse(options['pretty_print'])
        
    def test_pdf_options(self):
        """Test PDF export options."""
        options = self.dialog.pdf_options.get_options()
        
        self.assertIn('include_cover', options)
        self.assertIn('include_toc', options)
        self.assertIn('parse_markdown', options)
        self.assertIn('page_size', options)
        
        # Test changing page size
        self.dialog.pdf_options.page_size_combo.setCurrentText('A4')
        options = self.dialog.pdf_options.get_options()
        self.assertEqual(options['page_size'], 'a4')


class TestDateRangeSelector(unittest.TestCase):
    """Test cases for DateRangeSelector widget."""
    
    @classmethod
    def setUpClass(cls):
        """Set up QApplication for Qt tests."""
        if not QApplication.instance():
            cls.app = QApplication([])
        else:
            cls.app = QApplication.instance()
            
    def setUp(self):
        """Set up test fixtures."""
        self.selector = DateRangeSelector()
        
    def test_preset_selection(self):
        """Test preset date range selection."""
        # Test "This month" preset
        self.selector.preset_combo.setCurrentText("This month")
        start_date, end_date = self.selector.get_date_range()
        
        today = date.today()
        self.assertEqual(start_date.day, 1)
        self.assertEqual(start_date.month, today.month)
        self.assertEqual(end_date, today)
        
    def test_custom_range(self):
        """Test custom date range selection."""
        self.selector.preset_combo.setCurrentText("Custom range")
        self.assertTrue(self.selector.custom_widget.isVisible())
        
        # Set custom dates
        self.selector.from_date.setDate(QDate(2024, 1, 1))
        self.selector.to_date.setDate(QDate(2024, 1, 31))
        
        start_date, end_date = self.selector.get_date_range()
        self.assertEqual(start_date, date(2024, 1, 1))
        self.assertEqual(end_date, date(2024, 1, 31))
        
    @patch('src.data_access.JournalDAO.get_journal_entries')
    def test_entry_count_update(self, mock_get_entries):
        """Test entry count label update."""
        # Mock return value
        mock_get_entries.return_value = [Mock() for _ in range(5)]
        
        # Trigger count update
        self.selector._update_entry_count()
        
        # Check label text
        self.assertEqual(self.selector.count_label.text(), "5 entries will be exported")


if __name__ == '__main__':
    unittest.main()