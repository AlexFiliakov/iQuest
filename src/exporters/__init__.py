"""Journal export functionality for Apple Health Monitor.

This package provides export capabilities for journal entries in multiple formats
including JSON and PDF. It implements a flexible export architecture that allows
for easy extension to additional formats in the future.

The package includes:
    - Base exporter abstract class defining the export interface
    - JSON exporter for data portability and backup
    - PDF exporter for professional, printable reports
    - Export utilities for common operations

Example:
    Basic export usage:
    
    >>> from src.exporters import JSONExporter, PDFExporter
    >>> from src.data_access import JournalDAO
    >>> 
    >>> # Export to JSON
    >>> json_exporter = JSONExporter()
    >>> entries = JournalDAO.get_journal_entries(start_date, end_date)
    >>> json_exporter.export(entries, 'journal_backup.json')
    >>> 
    >>> # Export to PDF
    >>> pdf_exporter = PDFExporter()
    >>> pdf_exporter.export(entries, 'journal_report.pdf')
"""

from .base_exporter import BaseExporter, ExportOptions, ExportResult
from .json_exporter import JSONExporter
from .pdf_exporter import PDFExporter

__all__ = [
    'BaseExporter',
    'ExportOptions',
    'ExportResult',
    'JSONExporter',
    'PDFExporter'
]