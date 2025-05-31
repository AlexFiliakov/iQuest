"""
XML Streaming Processor for Apple Health Data

This module implements memory-efficient XML processing for large Apple Health export files
following the hybrid approach defined in ADR-002. It provides:
- SAX-based streaming XML parser for large files (>50MB)
- Memory usage monitoring and adaptive processing
- Progress callback support for UI integration
- Chunked database insertion for optimal performance
"""

import xml.sax
import xml.sax.handler
import sqlite3
import psutil
import os
from pathlib import Path
from typing import Callable, Optional, Dict, Any, List
from datetime import datetime
import pandas as pd

from src.utils.logging_config import get_logger
from src.utils.error_handler import DataImportError
from src.config import MIN_MEMORY_LIMIT_MB, MAX_MEMORY_LIMIT_MB, DEFAULT_MEMORY_LIMIT_MB

# Get logger for this module
logger = get_logger(__name__)


class MemoryMonitor:
    """Monitor memory usage during processing."""
    
    def __init__(self, limit_mb: int = DEFAULT_MEMORY_LIMIT_MB):
        """Initialize memory monitor.
        
        Args:
            limit_mb: Memory limit in megabytes (must be between 50 and 8192)
        
        Raises:
            ValueError: If limit_mb is outside the valid range
        """
        if limit_mb < MIN_MEMORY_LIMIT_MB:
            raise ValueError(f"Memory limit must be at least {MIN_MEMORY_LIMIT_MB}MB, got {limit_mb}MB")
        if limit_mb > MAX_MEMORY_LIMIT_MB:
            raise ValueError(f"Memory limit must not exceed {MAX_MEMORY_LIMIT_MB}MB ({MAX_MEMORY_LIMIT_MB/1024:.0f}GB), got {limit_mb}MB")
        self.limit_mb = limit_mb
        self.process = psutil.Process()
        
    def get_current_usage_mb(self) -> float:
        """Get current memory usage in MB."""
        return self.process.memory_info().rss / 1024 / 1024
    
    def is_over_limit(self) -> bool:
        """Check if current usage exceeds limit."""
        return self.get_current_usage_mb() > self.limit_mb
    
    def get_usage_percentage(self) -> float:
        """Get memory usage as percentage of limit."""
        return (self.get_current_usage_mb() / self.limit_mb) * 100


class AppleHealthHandler(xml.sax.handler.ContentHandler):
    """SAX handler for processing Apple Health XML records."""
    
    def __init__(self, db_path: str, progress_callback: Optional[Callable] = None,
                 chunk_size: int = 10000, memory_monitor: Optional[MemoryMonitor] = None):
        """Initialize the SAX handler.
        
        Args:
            db_path: Path to SQLite database
            progress_callback: Optional callback for progress updates
            chunk_size: Number of records to batch before database insert
            memory_monitor: Optional memory monitoring instance
        """
        super().__init__()
        self.db_path = db_path
        self.progress_callback = progress_callback
        self.chunk_size = chunk_size
        self.memory_monitor = memory_monitor
        
        # Tracking variables
        self.records = []
        self.record_count = 0
        self.bytes_processed = 0
        self.file_size = 0
        self.in_record = False
        self.current_record = {}
        
        # Progress update optimization
        self.last_progress_update = 0
        self.progress_update_interval = 10000  # Update UI every 10,000 records
        
        # Database connection for batched inserts
        self.conn = None
        self._transaction_started = False
        self._initialize_database()
        
    def _initialize_database(self):
        """Initialize the SQLite database and create tables."""
        try:
            self.conn = sqlite3.connect(self.db_path)
            
            # Start a transaction for the entire import
            self.conn.execute('BEGIN IMMEDIATE')
            self._transaction_started = True
            
            # Create health_records table with unique constraint
            self.conn.execute('''
                CREATE TABLE IF NOT EXISTS health_records (
                    type TEXT,
                    sourceName TEXT,
                    sourceVersion TEXT,
                    device TEXT,
                    unit TEXT,
                    creationDate TEXT,
                    startDate TEXT,
                    endDate TEXT,
                    value REAL,
                    UNIQUE(type, sourceName, startDate, endDate, value)
                )
            ''')
            
            # Create indexes for performance
            self.conn.execute('CREATE INDEX IF NOT EXISTS idx_creation_date ON health_records(creationDate)')
            self.conn.execute('CREATE INDEX IF NOT EXISTS idx_type ON health_records(type)')
            self.conn.execute('CREATE INDEX IF NOT EXISTS idx_type_date ON health_records(type, creationDate)')
            
            # Create metadata table
            self.conn.execute('''
                CREATE TABLE IF NOT EXISTS metadata (
                    key TEXT PRIMARY KEY,
                    value TEXT
                )
            ''')
            
            self.conn.commit()
            logger.info("Database initialized successfully")
            
        except sqlite3.Error as e:
            logger.error(f"Failed to initialize database: {e}")
            raise DataImportError(f"Database initialization failed: {str(e)}")
    
    def set_file_size(self, file_size: int):
        """Set the total file size for progress calculation."""
        self.file_size = file_size
    
    def startElement(self, name: str, attrs: xml.sax.xmlreader.AttributesImpl):
        """Handle start of XML element."""
        # Track bytes for element name and attributes for progress calculation
        element_bytes = len(f"<{name}".encode('utf-8'))
        for attr_name, attr_value in attrs.items():
            element_bytes += len(f' {attr_name}="{attr_value}"'.encode('utf-8'))
        element_bytes += len('>'.encode('utf-8'))
        self.bytes_processed += element_bytes
        
        if name == 'Record':
            self.in_record = True
            self.current_record = dict(attrs.items())
    
    def endElement(self, name: str):
        """Handle end of XML element."""
        # Track bytes for closing element tag
        self.bytes_processed += len(f"</{name}>".encode('utf-8'))
        
        if name == 'Record' and self.in_record:
            self.in_record = False
            self._process_record(self.current_record)
            self.current_record = {}
    
    def _process_record(self, record: Dict[str, Any]):
        """Process a single health record."""
        # Clean and validate the record
        processed_record = self._clean_record(record)
        if processed_record:
            self.records.append(processed_record)
            self.record_count += 1
            
            # Check if we should flush to database
            if len(self.records) >= self.chunk_size:
                self._flush_to_database()
            
            # Update progress if callback provided (but only every N records for performance)
            if self.progress_callback and self.file_size > 0:
                # Only update progress every 10,000 records or when reaching 100%
                if (self.record_count - self.last_progress_update >= self.progress_update_interval or 
                    self.bytes_processed >= self.file_size):
                    progress_pct = (self.bytes_processed / self.file_size) * 100
                    # Check if callback returns False to signal cancellation
                    should_continue = self.progress_callback(progress_pct, self.record_count)
                    self.last_progress_update = self.record_count
                    if should_continue is False:
                        raise xml.sax.SAXException("Import cancelled by user")
            
            # Check memory usage
            if self.memory_monitor and self.memory_monitor.is_over_limit():
                logger.info(f"Memory usage reached {self.memory_monitor.get_current_usage_mb():.1f}MB (limit: {self.memory_monitor.limit_mb}MB) - flushing to disk (normal for large imports)")
                # Force flush to free memory
                self._flush_to_database()
    
    def _clean_record(self, record: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Clean and validate a health record."""
        try:
            # Extract required fields
            cleaned = {
                'type': record.get('type', '').replace('HKQuantityTypeIdentifier', '').replace('HKCategoryTypeIdentifier', ''),
                'sourceName': record.get('sourceName', ''),
                'sourceVersion': record.get('sourceVersion', ''),
                'device': record.get('device', ''),
                'unit': record.get('unit', ''),
                'creationDate': record.get('creationDate', ''),
                'startDate': record.get('startDate', ''),
                'endDate': record.get('endDate', ''),
                'value': self._parse_numeric_value(record.get('value'))
            }
            
            # Validate required fields
            if not cleaned['type'] or not cleaned['creationDate']:
                return None
                
            return cleaned
            
        except Exception as e:
            logger.warning(f"Failed to clean record: {e}")
            return None
    
    def _parse_numeric_value(self, value_str: Optional[str]) -> float:
        """Parse numeric value, returning 1.0 for categorical data."""
        if not value_str:
            return 1.0
        try:
            return float(value_str)
        except (ValueError, TypeError):
            return 1.0
    
    def _flush_to_database(self):
        """Flush accumulated records to the database."""
        if not self.records:
            return
            
        try:
            # Insert records using INSERT OR IGNORE to prevent duplicates
            records_inserted = 0
            cursor = self.conn.cursor()
            
            for record in self.records:
                try:
                    cursor.execute("""
                        INSERT OR IGNORE INTO health_records 
                        (type, sourceName, sourceVersion, device, unit, creationDate, startDate, endDate, value)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        record.get('type', ''),
                        record.get('sourceName', ''),
                        record.get('sourceVersion', ''),
                        record.get('device', ''),
                        record.get('unit', ''),
                        record.get('creationDate'),
                        record.get('startDate'),
                        record.get('endDate'),
                        record.get('value', 1.0)
                    ))
                    if cursor.rowcount > 0:
                        records_inserted += 1
                except Exception as e:
                    logger.warning(f"Failed to insert record: {e}")
            
            # Don't commit yet - wait until entire import is done
            logger.debug(f"Flushed {records_inserted} new records to database (skipped {len(self.records) - records_inserted} duplicates)")
            
            # Clear records from memory
            self.records.clear()
            
        except Exception as e:
            logger.error(f"Failed to flush records to database: {e}")
            raise DataImportError(f"Database write failed: {str(e)}")
    
    def characters(self, content: str):
        """Handle character data (not used for Apple Health XML)."""
        self.bytes_processed += len(content.encode('utf-8'))
    
    def startDocument(self):
        """Handle start of document."""
        self.bytes_processed = 0
        self.record_count = 0
    
    def ignorableWhitespace(self, whitespace):
        """Track whitespace for progress."""
        self.bytes_processed += len(whitespace.encode('utf-8'))
    
    def finalize(self, cancelled: bool = False) -> int:
        """Finalize processing and close database connection.
        
        Args:
            cancelled: Whether the import was cancelled
        """
        try:
            if cancelled:
                # Rollback the entire transaction if cancelled
                if self._transaction_started:
                    self.conn.rollback()
                    logger.info("Import cancelled - transaction rolled back")
                return 0
            else:
                # Flush any remaining records
                self._flush_to_database()
                
                # Send final progress update if we haven't already
                if self.progress_callback and self.record_count > self.last_progress_update:
                    self.progress_callback(100.0, self.record_count)
                
                # Update metadata
                self.conn.execute("INSERT OR REPLACE INTO metadata VALUES ('import_date', ?)", 
                                (datetime.now().isoformat(),))
                self.conn.execute("INSERT OR REPLACE INTO metadata VALUES ('record_count', ?)", 
                                (str(self.record_count),))
                
                # Commit the entire transaction
                if self._transaction_started:
                    self.conn.commit()
                    logger.info(f"Transaction committed: {self.record_count} records imported")
                
                return self.record_count
            
        except Exception as e:
            logger.error(f"Failed to finalize processing: {e}")
            if self._transaction_started:
                try:
                    self.conn.rollback()
                    logger.info("Transaction rolled back due to error")
                except:
                    pass
            raise
        finally:
            if self.conn:
                self.conn.close()


class XMLStreamingProcessor:
    """Main streaming processor for Apple Health XML files."""
    
    def __init__(self, memory_limit_mb: int = DEFAULT_MEMORY_LIMIT_MB):
        """Initialize the streaming processor.
        
        Args:
            memory_limit_mb: Memory limit in megabytes (must be between 50 and 8192)
        
        Raises:
            ValueError: If memory_limit_mb is outside the valid range
        """
        if memory_limit_mb < MIN_MEMORY_LIMIT_MB:
            raise ValueError(f"Memory limit must be at least {MIN_MEMORY_LIMIT_MB}MB, got {memory_limit_mb}MB")
        if memory_limit_mb > MAX_MEMORY_LIMIT_MB:
            raise ValueError(f"Memory limit must not exceed {MAX_MEMORY_LIMIT_MB}MB ({MAX_MEMORY_LIMIT_MB/1024:.0f}GB), got {memory_limit_mb}MB")
        self.memory_limit_mb = memory_limit_mb
        self.memory_monitor = MemoryMonitor(memory_limit_mb)
        
    def calculate_chunk_size(self, file_size_bytes: int) -> int:
        """Calculate optimal chunk size based on file size."""
        # Base chunk size on file size and available memory
        if file_size_bytes < 50 * 1024 * 1024:  # <50MB
            return 10000  # Reasonable batch size for small files
        elif file_size_bytes < 200 * 1024 * 1024:  # <200MB
            return 5000   # Medium chunks
        else:  # >200MB
            return 2500   # Smaller chunks for large files
    
    def should_use_streaming(self, file_path: str) -> bool:
        """Determine if streaming should be used based on file size and available memory."""
        file_size = os.path.getsize(file_path)
        estimated_memory_mb = (file_size * 2.5) / (1024 * 1024)  # XML typically expands 2.5x in memory
        
        return estimated_memory_mb > (self.memory_limit_mb * 0.8)  # Use 80% of limit as threshold
    
    def process_xml_file(self, xml_path: str, db_path: str, 
                        progress_callback: Optional[Callable] = None) -> int:
        """Process Apple Health XML file with optimal strategy.
        
        Args:
            xml_path: Path to XML file
            db_path: Path to output SQLite database
            progress_callback: Optional progress callback function
            
        Returns:
            Number of records processed
        """
        if not Path(xml_path).exists():
            raise FileNotFoundError(f"XML file not found: {xml_path}")
        
        file_size = os.path.getsize(xml_path)
        logger.info(f"Processing XML file: {xml_path} ({file_size / (1024*1024):.1f} MB)")
        
        # Determine processing strategy
        if self.should_use_streaming(xml_path):
            logger.info("Using streaming processor for large file")
            return self._stream_process(xml_path, db_path, progress_callback)
        else:
            logger.info("Using memory-based processor for small file")
            # Fall back to existing memory-based approach for small files
            from .data_loader import convert_xml_to_sqlite
            return convert_xml_to_sqlite(xml_path, db_path)
    
    def _stream_process(self, xml_path: str, db_path: str,
                       progress_callback: Optional[Callable] = None) -> int:
        """Process XML file using streaming SAX parser."""
        handler = None
        cancelled = False
        try:
            file_size = os.path.getsize(xml_path)
            chunk_size = self.calculate_chunk_size(file_size)
            
            # Create SAX parser and handler
            parser = xml.sax.make_parser()
            handler = AppleHealthHandler(
                db_path=db_path,
                progress_callback=progress_callback,
                chunk_size=chunk_size,
                memory_monitor=self.memory_monitor
            )
            handler.set_file_size(file_size)
            parser.setContentHandler(handler)
            
            # Process the file
            logger.info(f"Starting streaming parse with chunk size: {chunk_size}")
            with open(xml_path, 'r', encoding='utf-8') as xml_file:
                parser.parse(xml_file)
            
            # Finalize and get record count
            record_count = handler.finalize(cancelled=False)
            
            # Log memory usage statistics
            final_memory = self.memory_monitor.get_current_usage_mb()
            logger.info(f"Processing complete. Final memory usage: {final_memory:.1f} MB")
            
            return record_count
            
        except xml.sax.SAXException as e:
            # Check if this is a cancellation
            if "cancelled by user" in str(e).lower():
                logger.info("Import cancelled by user")
                cancelled = True
                if handler:
                    handler.finalize(cancelled=True)
                raise DataImportError("Import cancelled by user")
            else:
                logger.error(f"XML parsing error: {e}")
                if handler:
                    handler.finalize(cancelled=True)
                raise DataImportError(f"Failed to parse XML: {str(e)}")
        except Exception as e:
            logger.error(f"Streaming processing error: {e}")
            if handler:
                handler.finalize(cancelled=True)
            raise DataImportError(f"Streaming processing failed: {str(e)}")


# Example usage
if __name__ == "__main__":
    # Example: Process large XML file with streaming
    processor = XMLStreamingProcessor(memory_limit_mb=DEFAULT_MEMORY_LIMIT_MB)
    
    def progress_callback(percent: float, records: int):
        print(f"Progress: {percent:.1f}% - {records} records processed")
    
    # record_count = processor.process_xml_file(
    #     "large_export.xml", 
    #     "health_data.db",
    #     progress_callback
    # )
    # print(f"Imported {record_count} records")