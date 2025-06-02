"""JSON exporter for journal entries.

This module implements JSON export functionality for journal entries, providing
a portable and machine-readable format for data backup, transfer, and integration
with other systems. The exporter supports both compact and pretty-printed output,
streaming for large datasets, and comprehensive metadata inclusion.

The JSONExporter class provides:
    - Standards-compliant JSON output with proper encoding
    - Streaming export for memory-efficient large dataset handling
    - Flexible formatting options (compact vs. pretty-printed)
    - Rich metadata including export info and statistics
    - Proper date/time serialization in ISO format
    - UTF-8 encoding with BOM for Excel compatibility

Example:
    Basic JSON export:
    
    >>> from src.exporters import JSONExporter
    >>> from src.data_access import JournalDAO
    >>> 
    >>> exporter = JSONExporter()
    >>> entries = JournalDAO.get_journal_entries(start_date, end_date)
    >>> result = exporter.export(entries, 'backup.json')
    >>> print(f"Exported {result.entries_exported} entries")
    
    Streaming export for large datasets:
    
    >>> options = ExportOptions(
    ...     pretty_print=False,  # Compact for smaller file size
    ...     extra_options={'streaming': True, 'chunk_size': 100}
    ... )
    >>> exporter = JSONExporter(options)
    >>> result = exporter.export_streaming(entries_query, 'large_export.json')
"""

import json
import logging
from datetime import datetime, date
from typing import List, Dict, Any, Optional, Iterator
import time
from pathlib import Path

from .base_exporter import BaseExporter, ExportOptions, ExportResult
from ..models import JournalEntry
from ..version import VERSION
from ..utils.error_handler import ValidationError

logger = logging.getLogger(__name__)


class JSONExporter(BaseExporter):
    """JSON format exporter for journal entries.
    
    Exports journal entries to JSON format with support for both standard
    and streaming export modes. The exported JSON follows a consistent
    schema that includes metadata, version information, and properly
    formatted entries.
    
    The JSON schema structure:
    {
        "export_metadata": {
            "version": "1.0",
            "app_version": "2.0.0",
            "export_date": "2024-01-15T10:30:00",
            "export_range": "2024-01-01 to 2024-01-31",
            "total_entries": 31,
            "entry_types": {"daily": 28, "weekly": 2, "monthly": 1}
        },
        "entries": [
            {
                "id": 123,
                "entry_date": "2024-01-15",
                "entry_type": "daily",
                "content": "Journal content...",
                "word_count": 250,
                "created_at": "2024-01-15T20:30:00",
                "updated_at": "2024-01-15T20:45:00"
            }
        ]
    }
    """
    
    JSON_VERSION = "1.0"
    
    def __init__(self, options: Optional[ExportOptions] = None):
        """Initialize JSON exporter with options.
        
        Args:
            options: Export configuration options.
        """
        super().__init__(options)
        self.indent = 2 if self.options.pretty_print else None
        
    def export(self, entries: List[JournalEntry], output_path: str) -> ExportResult:
        """Export journal entries to JSON file.
        
        Exports all provided entries to a JSON file with metadata and
        proper formatting. For large datasets, consider using export_streaming.
        
        Args:
            entries: List of journal entries to export.
            output_path: Path where the JSON file should be saved.
            
        Returns:
            ExportResult: Export operation results and statistics.
            
        Raises:
            ValidationError: If entries are invalid.
            IOError: If file cannot be written.
        """
        self._start_time = time.time()
        
        # Validate entries
        warnings = self.validate_entries(entries)
        
        # Ensure output directory exists
        self.ensure_output_directory(output_path)
        
        # Apply max entries limit if specified
        if self.options.max_entries and len(entries) > self.options.max_entries:
            entries = entries[:self.options.max_entries]
            warnings.append(f"Limited export to {self.options.max_entries} entries")
        
        try:
            # Build export data structure
            export_data = self._build_export_data(entries)
            
            # Write to file with UTF-8 encoding
            with open(output_path, 'w', encoding='utf-8') as f:
                # Add UTF-8 BOM for Excel compatibility if requested
                if self.options.extra_options.get('add_bom', False):
                    f.write('\ufeff')
                    
                json.dump(export_data, f, indent=self.indent, ensure_ascii=False)
                
            # Calculate final statistics
            duration = time.time() - self._start_time
            file_size = self.calculate_file_size(output_path)
            
            logger.info(f"Exported {len(entries)} entries to {output_path}")
            
            return ExportResult(
                success=True,
                entries_exported=len(entries),
                file_path=output_path,
                file_size=file_size,
                export_duration=duration,
                warnings=warnings,
                metadata={
                    'json_version': self.JSON_VERSION,
                    'pretty_printed': self.options.pretty_print
                }
            )
            
        except Exception as e:
            logger.error(f"JSON export failed: {e}")
            return ExportResult(
                success=False,
                error_message=str(e),
                warnings=warnings,
                export_duration=time.time() - self._start_time
            )
    
    def export_streaming(self, entries_iterator: Iterator[JournalEntry], 
                        output_path: str, total_count: Optional[int] = None) -> ExportResult:
        """Export journal entries using streaming for large datasets.
        
        Streams entries to JSON file without loading all entries into memory,
        suitable for exporting large numbers of entries.
        
        Args:
            entries_iterator: Iterator providing journal entries.
            output_path: Path where the JSON file should be saved.
            total_count: Optional total count for progress tracking.
            
        Returns:
            ExportResult: Export operation results and statistics.
        """
        self._start_time = time.time()
        warnings = []
        entries_exported = 0
        
        # Ensure output directory exists
        self.ensure_output_directory(output_path)
        
        try:
            with open(output_path, 'w', encoding='utf-8') as f:
                # Add UTF-8 BOM if requested
                if self.options.extra_options.get('add_bom', False):
                    f.write('\ufeff')
                
                # Write opening structure
                f.write('{\n')
                
                # Write metadata (will be updated at the end)
                if self.options.include_metadata:
                    f.write('  "export_metadata": ')
                    metadata = self._create_metadata_placeholder()
                    json.dump(metadata, f, indent=2 if self.indent else None)
                    f.write(',\n')
                
                # Start entries array
                f.write('  "entries": [')
                
                # Stream entries
                first_entry = True
                entry_type_counts = {'daily': 0, 'weekly': 0, 'monthly': 0}
                
                for entry in entries_iterator:
                    if not first_entry:
                        f.write(',')
                    else:
                        first_entry = False
                    
                    f.write('\n')
                    
                    # Convert entry to dict
                    entry_dict = self._entry_to_dict(entry)
                    
                    # Write entry with proper indentation
                    if self.indent:
                        f.write('    ')
                        json.dump(entry_dict, f, indent=self.indent, ensure_ascii=False)
                    else:
                        json.dump(entry_dict, f, ensure_ascii=False)
                    
                    # Update statistics
                    entries_exported += 1
                    entry_type_counts[entry.entry_type] = entry_type_counts.get(entry.entry_type, 0) + 1
                    
                    # Update progress
                    if total_count:
                        progress = (entries_exported / total_count) * 100
                        self.update_progress(progress)
                
                # Close entries array
                f.write('\n  ]\n')
                
                # Close main object
                f.write('}\n')
            
            # Update metadata file with actual counts (requires file rewrite)
            if self.options.include_metadata:
                self._update_streaming_metadata(output_path, entries_exported, entry_type_counts)
            
            # Calculate final statistics
            duration = time.time() - self._start_time
            file_size = self.calculate_file_size(output_path)
            
            logger.info(f"Streamed {entries_exported} entries to {output_path}")
            
            return ExportResult(
                success=True,
                entries_exported=entries_exported,
                file_path=output_path,
                file_size=file_size,
                export_duration=duration,
                warnings=warnings,
                metadata={
                    'json_version': self.JSON_VERSION,
                    'streaming_mode': True,
                    'entry_type_counts': entry_type_counts
                }
            )
            
        except Exception as e:
            logger.error(f"Streaming JSON export failed: {e}")
            return ExportResult(
                success=False,
                entries_exported=entries_exported,
                error_message=str(e),
                warnings=warnings,
                export_duration=time.time() - self._start_time
            )
    
    def _build_export_data(self, entries: List[JournalEntry]) -> Dict[str, Any]:
        """Build the complete export data structure.
        
        Args:
            entries: List of journal entries to include.
            
        Returns:
            Dict containing the complete export structure.
        """
        export_data = {}
        
        # Add metadata if requested
        if self.options.include_metadata:
            export_data['export_metadata'] = self._create_metadata(entries)
        
        # Convert entries
        export_data['entries'] = [self._entry_to_dict(entry) for entry in entries]
        
        # Update progress
        self.update_progress(100)
        
        return export_data
    
    def _create_metadata(self, entries: List[JournalEntry]) -> Dict[str, Any]:
        """Create export metadata.
        
        Args:
            entries: List of entries being exported.
            
        Returns:
            Dict containing export metadata.
        """
        if not entries:
            date_range = "No entries"
        else:
            min_date = min(e.entry_date for e in entries)
            max_date = max(e.entry_date for e in entries)
            date_range = f"{self.format_date(min_date)} to {self.format_date(max_date)}"
        
        # Count entries by type
        entry_type_counts = {}
        for entry in entries:
            entry_type_counts[entry.entry_type] = entry_type_counts.get(entry.entry_type, 0) + 1
        
        metadata = {
            'version': self.JSON_VERSION,
            'app_version': VERSION,
            'export_date': datetime.now().isoformat(),
            'export_range': date_range,
            'total_entries': len(entries),
            'entry_types': entry_type_counts
        }
        
        # Add statistics if requested
        if self.options.include_statistics:
            metadata['statistics'] = self._calculate_statistics(entries)
        
        return metadata
    
    def _create_metadata_placeholder(self) -> Dict[str, Any]:
        """Create placeholder metadata for streaming export.
        
        Returns:
            Dict containing placeholder metadata.
        """
        return {
            'version': self.JSON_VERSION,
            'app_version': VERSION,
            'export_date': datetime.now().isoformat(),
            'export_range': 'To be determined',
            'total_entries': 0,
            'entry_types': {}
        }
    
    def _entry_to_dict(self, entry: JournalEntry) -> Dict[str, Any]:
        """Convert JournalEntry to dictionary for JSON serialization.
        
        Args:
            entry: Journal entry to convert.
            
        Returns:
            Dict representation of the entry.
        """
        entry_dict = {
            'id': entry.id,
            'entry_date': entry.entry_date.isoformat(),
            'entry_type': entry.entry_type,
            'content': entry.content,
            'word_count': len(entry.content.split()),
            'created_at': entry.created_at.isoformat() if entry.created_at else None,
            'updated_at': entry.updated_at.isoformat() if entry.updated_at else None
        }
        
        # Add optional fields
        if entry.week_start_date:
            entry_dict['week_start_date'] = entry.week_start_date.isoformat()
        if entry.month_year:
            entry_dict['month_year'] = entry.month_year
            
        return entry_dict
    
    def _calculate_statistics(self, entries: List[JournalEntry]) -> Dict[str, Any]:
        """Calculate statistics about the entries.
        
        Args:
            entries: List of entries to analyze.
            
        Returns:
            Dict containing various statistics.
        """
        if not entries:
            return {}
            
        word_counts = [len(e.content.split()) for e in entries]
        
        return {
            'total_words': sum(word_counts),
            'average_words_per_entry': sum(word_counts) // len(entries) if entries else 0,
            'shortest_entry_words': min(word_counts) if word_counts else 0,
            'longest_entry_words': max(word_counts) if word_counts else 0,
            'entries_by_day_of_week': self._count_by_day_of_week(entries)
        }
    
    def _count_by_day_of_week(self, entries: List[JournalEntry]) -> Dict[str, int]:
        """Count entries by day of the week.
        
        Args:
            entries: List of entries to count.
            
        Returns:
            Dict mapping day names to counts.
        """
        days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
        counts = {day: 0 for day in days}
        
        for entry in entries:
            if entry.entry_type == 'daily':
                day_name = days[entry.entry_date.weekday()]
                counts[day_name] += 1
                
        return counts
    
    def _update_streaming_metadata(self, file_path: str, total_entries: int, 
                                  entry_type_counts: Dict[str, int]) -> None:
        """Update metadata in streamed file (requires file modification).
        
        Note: This is a simplified implementation. In production, you might
        want to use a more sophisticated approach or accept the placeholder.
        
        Args:
            file_path: Path to the exported file.
            total_entries: Total number of entries exported.
            entry_type_counts: Count of entries by type.
        """
        # For now, we'll leave the metadata as-is since updating a JSON file
        # in place is complex. In a production system, you might want to:
        # 1. Use a temporary file and rename
        # 2. Keep metadata at the end of the file
        # 3. Use a different format that supports streaming better
        pass