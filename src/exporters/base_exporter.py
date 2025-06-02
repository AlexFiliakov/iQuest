"""Base exporter abstract class for journal export functionality.

This module provides the foundation for all journal exporters, defining the common
interface and shared utilities for exporting journal entries to various formats.
It implements progress tracking, error handling, and common export operations.

The BaseExporter class serves as an abstract base that must be inherited by
specific format exporters (JSON, PDF, etc.). It provides:
    - Common export interface with progress callbacks
    - Shared utilities for file naming and validation
    - Error handling and recovery mechanisms
    - Progress tracking for long-running exports
    - Export statistics and result reporting

Example:
    Creating a custom exporter:
    
    >>> class CustomExporter(BaseExporter):
    ...     def export(self, entries, output_path):
    ...         self.progress = 0
    ...         total = len(entries)
    ...         
    ...         with open(output_path, 'w') as f:
    ...             for i, entry in enumerate(entries):
    ...                 # Export logic here
    ...                 self.update_progress((i + 1) / total * 100)
    ...         
    ...         return ExportResult(
    ...             success=True,
    ...             entries_exported=total,
    ...             file_path=output_path
    ...         )
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime, date
from pathlib import Path
from typing import List, Optional, Callable, Dict, Any
import logging
import os

from ..models import JournalEntry
from ..utils.error_handler import ValidationError

logger = logging.getLogger(__name__)


@dataclass
class ExportOptions:
    """Configuration options for journal export operations.
    
    Provides a comprehensive set of options to customize the export process
    for different formats and use cases. Options can be extended by specific
    exporters as needed.
    
    Attributes:
        include_metadata: Whether to include export metadata (timestamps, version).
        date_format: Format string for date display (default: ISO format).
        pretty_print: Whether to format output for readability (JSON).
        include_statistics: Whether to include export statistics summary.
        custom_filename: Optional custom filename (without extension).
        max_entries: Maximum number of entries to export (None for all).
        progress_callback: Optional callback for progress updates.
        extra_options: Format-specific options as key-value pairs.
    
    Example:
        >>> options = ExportOptions(
        ...     include_metadata=True,
        ...     pretty_print=True,
        ...     date_format="%B %d, %Y",
        ...     progress_callback=lambda p: print(f"Progress: {p}%")
        ... )
    """
    include_metadata: bool = True
    date_format: str = "%Y-%m-%d"
    pretty_print: bool = True
    include_statistics: bool = True
    custom_filename: Optional[str] = None
    max_entries: Optional[int] = None
    progress_callback: Optional[Callable[[float], None]] = None
    extra_options: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ExportResult:
    """Result information from an export operation.
    
    Contains comprehensive information about the export operation including
    success status, statistics, and any warnings or errors encountered.
    
    Attributes:
        success: Whether the export completed successfully.
        entries_exported: Number of entries successfully exported.
        file_path: Full path to the exported file.
        file_size: Size of the exported file in bytes.
        export_duration: Time taken for export in seconds.
        warnings: List of non-fatal warnings encountered.
        error_message: Error message if export failed.
        metadata: Additional metadata about the export.
    
    Example:
        >>> result = ExportResult(
        ...     success=True,
        ...     entries_exported=150,
        ...     file_path="/path/to/export.json",
        ...     file_size=45678,
        ...     export_duration=2.5
        ... )
    """
    success: bool
    entries_exported: int = 0
    file_path: Optional[str] = None
    file_size: int = 0
    export_duration: float = 0.0
    warnings: List[str] = field(default_factory=list)
    error_message: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


class BaseExporter(ABC):
    """Abstract base class for journal entry exporters.
    
    Provides the common interface and shared functionality for all journal
    export formats. Subclasses must implement the export method to handle
    specific format requirements.
    
    The base class handles:
        - Progress tracking and reporting
        - File naming conventions
        - Common validation logic
        - Error handling framework
        - Export statistics collection
    
    Attributes:
        progress: Current export progress (0-100).
        options: Export configuration options.
        _start_time: Export operation start timestamp.
    """
    
    def __init__(self, options: Optional[ExportOptions] = None):
        """Initialize the exporter with optional configuration.
        
        Args:
            options: Export configuration options. Uses defaults if not provided.
        """
        self.progress = 0.0
        self.options = options or ExportOptions()
        self._start_time: Optional[float] = None
        
    @abstractmethod
    def export(self, entries: List[JournalEntry], output_path: str) -> ExportResult:
        """Export journal entries to the specified file.
        
        This method must be implemented by all subclasses to handle the
        specific export format requirements.
        
        Args:
            entries: List of journal entries to export.
            output_path: Path where the exported file should be saved.
            
        Returns:
            ExportResult: Result information including success status and statistics.
            
        Raises:
            ValidationError: If entries or output path are invalid.
            IOError: If file cannot be written.
        """
        pass
    
    def update_progress(self, progress: float) -> None:
        """Update and report export progress.
        
        Updates the internal progress tracking and calls the progress callback
        if one was provided in the export options.
        
        Args:
            progress: Current progress percentage (0-100).
        """
        self.progress = min(100.0, max(0.0, progress))
        if self.options.progress_callback:
            try:
                self.options.progress_callback(self.progress)
            except Exception as e:
                logger.warning(f"Progress callback error: {e}")
    
    def generate_filename(self, base_name: str, extension: str, 
                         date_range: Optional[tuple] = None) -> str:
        """Generate a standardized filename for exports.
        
        Creates a filename following the convention:
        {base_name}_{date_range}_{timestamp}.{extension}
        
        Args:
            base_name: Base name for the file (e.g., 'journal_export').
            extension: File extension without dot (e.g., 'json', 'pdf').
            date_range: Optional tuple of (start_date, end_date) for filename.
            
        Returns:
            str: Generated filename with extension.
            
        Example:
            >>> exporter.generate_filename('journal', 'pdf', (date(2024,1,1), date(2024,1,31)))
            'journal_20240101_20240131_20240215_143052.pdf'
        """
        if self.options.custom_filename:
            return f"{self.options.custom_filename}.{extension}"
            
        parts = [base_name]
        
        if date_range and len(date_range) == 2:
            start_date, end_date = date_range
            parts.append(f"{start_date.strftime('%Y%m%d')}_{end_date.strftime('%Y%m%d')}")
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        parts.append(timestamp)
        
        filename = "_".join(parts) + f".{extension}"
        return filename
    
    def validate_entries(self, entries: List[JournalEntry]) -> List[str]:
        """Validate journal entries before export.
        
        Performs validation checks on the entries to export and returns
        any warnings about potential issues.
        
        Args:
            entries: List of journal entries to validate.
            
        Returns:
            List[str]: List of warning messages (empty if no issues).
        """
        warnings = []
        
        if not entries:
            warnings.append("No entries to export")
            return warnings
            
        # Check for empty content
        empty_entries = sum(1 for e in entries if not e.content.strip())
        if empty_entries > 0:
            warnings.append(f"{empty_entries} entries have empty content")
            
        # Check for very long entries
        long_entries = sum(1 for e in entries if len(e.content) > 5000)
        if long_entries > 0:
            warnings.append(f"{long_entries} entries exceed 5000 characters")
            
        # Check for future dates
        today = date.today()
        future_entries = sum(1 for e in entries if e.entry_date > today)
        if future_entries > 0:
            warnings.append(f"{future_entries} entries have future dates")
            
        return warnings
    
    def ensure_output_directory(self, output_path: str) -> None:
        """Ensure the output directory exists.
        
        Creates the directory path if it doesn't exist.
        
        Args:
            output_path: Full path to the output file.
            
        Raises:
            IOError: If directory cannot be created.
        """
        directory = os.path.dirname(output_path)
        if directory and not os.path.exists(directory):
            try:
                os.makedirs(directory, exist_ok=True)
                logger.info(f"Created output directory: {directory}")
            except Exception as e:
                raise IOError(f"Failed to create output directory: {e}")
    
    def calculate_file_size(self, file_path: str) -> int:
        """Calculate the size of the exported file.
        
        Args:
            file_path: Path to the exported file.
            
        Returns:
            int: File size in bytes, or 0 if file doesn't exist.
        """
        try:
            return os.path.getsize(file_path)
        except Exception:
            return 0
    
    def format_date(self, entry_date: date) -> str:
        """Format a date according to export options.
        
        Args:
            entry_date: Date to format.
            
        Returns:
            str: Formatted date string.
        """
        try:
            return entry_date.strftime(self.options.date_format)
        except Exception:
            return entry_date.isoformat()
    
    def get_entry_type_display(self, entry_type: str) -> str:
        """Get display name for entry type.
        
        Args:
            entry_type: Entry type code ('daily', 'weekly', 'monthly').
            
        Returns:
            str: Human-readable entry type.
        """
        type_map = {
            'daily': 'Daily Entry',
            'weekly': 'Weekly Summary',
            'monthly': 'Monthly Reflection'
        }
        return type_map.get(entry_type, entry_type.title())