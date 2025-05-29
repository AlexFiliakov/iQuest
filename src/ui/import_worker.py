"""
Import Worker Thread for non-blocking XML/CSV import operations.

This module provides threaded import functionality to keep the UI responsive
during long-running import operations.
"""

import os
import time
from pathlib import Path
from typing import Optional, Dict, Any

from PyQt6.QtCore import QThread, pyqtSignal, QMutex
from PyQt6.QtWidgets import QApplication

try:
    from ..utils.logging_config import get_logger
    from ..data_loader import convert_xml_to_sqlite_with_validation, DataLoader
    from ..database import db_manager
    from ..config import DATA_DIR
    from ..xml_streaming_processor import XMLStreamingProcessor
except (ImportError, ValueError) as e:
    # Fallback for when running in a thread context
    # ValueError catches "attempted relative import with no known parent package"
    import sys
    from pathlib import Path
    # Add the project root to sys.path
    project_root = Path(__file__).parent.parent.parent
    if str(project_root) not in sys.path:
        sys.path.insert(0, str(project_root))
    
    # Now use absolute imports
    from src.utils.logging_config import get_logger
    from src.data_loader import convert_xml_to_sqlite_with_validation, DataLoader
    from src.database import db_manager
    from src.config import DATA_DIR
    from src.xml_streaming_processor import XMLStreamingProcessor

logger = get_logger(__name__)


class ImportWorker(QThread):
    """Worker thread for handling import operations with progress updates."""
    
    # Signals for progress communication
    progress_updated = pyqtSignal(int, str, int)  # (percentage, message, record_count)
    import_completed = pyqtSignal(dict)           # {success, message, stats}
    import_error = pyqtSignal(str, str)           # (title, message)
    
    def __init__(self, file_path: str, import_type: str = "auto"):
        """
        Initialize the import worker.
        
        Args:
            file_path: Path to the file to import
            import_type: Type of import ("xml", "csv", or "auto")
        """
        super().__init__()
        self.file_path = file_path
        self.import_type = import_type
        self._is_cancelled = False
        self._mutex = QMutex()
        self.data_loader = DataLoader()
        
        # Auto-detect import type if needed
        if import_type == "auto":
            self.import_type = self._detect_file_type()
        
        logger.info(f"ImportWorker initialized for {import_type} import: {file_path}")
    
    def _detect_file_type(self) -> str:
        """Detect file type based on extension."""
        file_ext = Path(self.file_path).suffix.lower()
        if file_ext == '.xml':
            return 'xml'
        elif file_ext == '.csv':
            return 'csv'
        else:
            return 'unknown'
    
    def cancel_import(self):
        """Cancel the import operation."""
        self._mutex.lock()
        self._is_cancelled = True
        self._mutex.unlock()
        logger.info("Import cancellation requested")
    
    def is_cancelled(self) -> bool:
        """Check if import has been cancelled."""
        self._mutex.lock()
        cancelled = self._is_cancelled
        self._mutex.unlock()
        return cancelled
    
    def run(self):
        """Execute the import operation in a separate thread."""
        try:
            start_time = time.time()
            
            if self.import_type == 'xml':
                result = self._import_xml()
            elif self.import_type == 'csv':
                result = self._import_csv()
            else:
                self.import_error.emit(
                    "Unsupported File Type",
                    f"Cannot import file type: {Path(self.file_path).suffix}"
                )
                return
            
            if not self.is_cancelled() and result['success']:
                end_time = time.time()
                result['import_time'] = round(end_time - start_time, 2)
                self.import_completed.emit(result)
            
        except Exception as e:
            logger.error(f"Import failed with exception: {e}")
            self.import_error.emit(
                "Import Error",
                f"An unexpected error occurred during import:\n{str(e)}"
            )
    
    def _import_xml(self) -> Dict[str, Any]:
        """Import XML file with progress updates."""
        self.progress_updated.emit(5, "Validating XML file...", 0)
        
        # Check if file exists and is readable
        if not Path(self.file_path).exists():
            raise FileNotFoundError(f"File not found: {self.file_path}")
        
        if self.is_cancelled():
            return {'success': False, 'message': 'Import cancelled'}
        
        self.progress_updated.emit(10, "Preparing database...", 0)
        
        # Prepare database path
        # Use a hardcoded filename to avoid import issues in thread
        DB_FILE_NAME = 'health_data.db'
        db_path = os.path.join(DATA_DIR, DB_FILE_NAME)
        os.makedirs(DATA_DIR, exist_ok=True)
        
        if self.is_cancelled():
            return {'success': False, 'message': 'Import cancelled'}
        
        self.progress_updated.emit(15, "Analyzing file size...", 0)
        
        # Get file size for progress tracking
        file_size = os.path.getsize(self.file_path)
        file_size_mb = file_size / (1024 * 1024)
        
        # Initialize streaming processor
        processor = XMLStreamingProcessor(memory_limit_mb=500)
        
        # Determine if we should use streaming based on file size
        use_streaming = processor.should_use_streaming(self.file_path)
        
        try:
            if use_streaming:
                logger.info(f"Using streaming processor for large file ({file_size_mb:.1f}MB)")
                self.progress_updated.emit(20, f"Processing large file ({file_size_mb:.1f}MB)...", 0)
                
                # Track records processed
                self.current_record_count = 0
                
                # Create progress callback
                def progress_callback(percentage: float, record_count: int):
                    if self.is_cancelled():
                        return False  # Signal cancellation
                    
                    self.current_record_count = record_count
                    # Scale progress from 20% to 90%
                    scaled_progress = int(20 + (percentage * 0.7))
                    message = f"Processing records... ({percentage:.1f}%)"
                    self.progress_updated.emit(scaled_progress, message, record_count)
                    QApplication.processEvents()  # Keep UI responsive
                    return True  # Continue processing
                
                # Process with streaming
                record_count = processor.process_xml_file(
                    self.file_path, 
                    db_path, 
                    progress_callback=progress_callback
                )
                
            else:
                logger.info(f"Using standard processor for file ({file_size_mb:.1f}MB)")
                self.progress_updated.emit(20, "Loading XML file...", 0)
                
                # For smaller files, show periodic updates during conversion
                self.current_record_count = 0
                last_update_time = time.time()
                
                def update_progress():
                    # Simulate progress for standard loading
                    if time.time() - last_update_time > 0.5:  # Update every 0.5 seconds
                        self.progress_updated.emit(50, "Converting to database format...", self.current_record_count)
                        QApplication.processEvents()
                
                # Use standard conversion with validation
                record_count, validation_summary = convert_xml_to_sqlite_with_validation(
                    self.file_path, db_path, validate_first=True
                )
                
                # Update with final count
                self.progress_updated.emit(80, "Processing complete", record_count)
            
            if self.is_cancelled():
                return {'success': False, 'message': 'Import cancelled'}
            
            self.progress_updated.emit(90, "Finalizing import...", record_count)
            
            # Initialize database manager
            db_manager.initialize_database()
            
            self.progress_updated.emit(100, "Import completed successfully!", record_count)
            
            return {
                'success': True,
                'message': 'XML import completed successfully',
                'record_count': record_count,
                'file_path': self.file_path,
                'import_type': 'xml',
                'file_size_mb': round(file_size_mb, 1)
            }
            
        except Exception as e:
            logger.error(f"XML import failed: {e}")
            raise
    
    def _import_csv(self) -> Dict[str, Any]:
        """Import CSV file with progress updates."""
        self.progress_updated.emit(10, "Reading CSV file...", 0)
        
        if self.is_cancelled():
            return {'success': False, 'message': 'Import cancelled'}
        
        try:
            # Load CSV data
            data = self.data_loader.load_csv(self.file_path)
            record_count = len(data) if data is not None else 0
            
            if self.is_cancelled():
                return {'success': False, 'message': 'Import cancelled'}
            
            self.progress_updated.emit(50, "Processing CSV data...", record_count)
            time.sleep(0.1)  # Small delay to show progress
            
            if self.is_cancelled():
                return {'success': False, 'message': 'Import cancelled'}
            
            self.progress_updated.emit(100, "CSV import completed!", record_count)
            
            return {
                'success': True,
                'message': 'CSV import completed successfully',
                'record_count': record_count,
                'file_path': self.file_path,
                'import_type': 'csv',
                'data': data
            }
            
        except Exception as e:
            logger.error(f"CSV import failed: {e}")
            raise