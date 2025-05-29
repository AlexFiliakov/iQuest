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

logger = get_logger(__name__)


class ImportWorker(QThread):
    """Worker thread for handling import operations with progress updates."""
    
    # Signals for progress communication
    progress_updated = pyqtSignal(int, str)  # (percentage, message)
    import_completed = pyqtSignal(dict)      # {success, message, stats}
    import_error = pyqtSignal(str, str)      # (title, message)
    
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
        self.progress_updated.emit(5, "Validating XML file...")
        
        # Check if file exists and is readable
        if not Path(self.file_path).exists():
            raise FileNotFoundError(f"File not found: {self.file_path}")
        
        if self.is_cancelled():
            return {'success': False, 'message': 'Import cancelled'}
        
        self.progress_updated.emit(10, "Preparing database...")
        
        # Prepare database path
        # Use a hardcoded filename to avoid import issues in thread
        DB_FILE_NAME = 'health_data.db'
        db_path = os.path.join(DATA_DIR, DB_FILE_NAME)
        os.makedirs(DATA_DIR, exist_ok=True)
        
        if self.is_cancelled():
            return {'success': False, 'message': 'Import cancelled'}
        
        self.progress_updated.emit(20, "Parsing XML file...")
        
        # Parse and convert XML to SQLite
        # Note: The actual convert_xml_to_sqlite function doesn't support progress callbacks yet
        # For now, we'll simulate progress and enhance the function later
        record_count = 0
        
        try:
            # Simulate parsing progress
            for i in range(20, 70, 10):
                if self.is_cancelled():
                    return {'success': False, 'message': 'Import cancelled'}
                
                self.progress_updated.emit(i, f"Processing XML data... ({i}%)")
                time.sleep(0.1)  # Small delay to show progress
                QApplication.processEvents()  # Keep UI responsive
            
            self.progress_updated.emit(70, "Converting to database format...")
            
            # Actual conversion with validation
            record_count, validation_summary = convert_xml_to_sqlite_with_validation(
                self.file_path, db_path, validate_first=True
            )
            
            if self.is_cancelled():
                return {'success': False, 'message': 'Import cancelled'}
            
            self.progress_updated.emit(90, "Finalizing import...")
            
            # Initialize database manager
            db_manager.initialize_database()
            
            self.progress_updated.emit(100, "Import completed successfully!")
            
            return {
                'success': True,
                'message': 'XML import completed successfully',
                'record_count': record_count,
                'file_path': self.file_path,
                'import_type': 'xml',
                'validation_summary': validation_summary
            }
            
        except Exception as e:
            logger.error(f"XML import failed: {e}")
            raise
    
    def _import_csv(self) -> Dict[str, Any]:
        """Import CSV file with progress updates."""
        self.progress_updated.emit(10, "Reading CSV file...")
        
        if self.is_cancelled():
            return {'success': False, 'message': 'Import cancelled'}
        
        try:
            # Load CSV data
            data = self.data_loader.load_csv(self.file_path)
            
            if self.is_cancelled():
                return {'success': False, 'message': 'Import cancelled'}
            
            self.progress_updated.emit(50, "Processing CSV data...")
            time.sleep(0.1)  # Small delay to show progress
            
            if self.is_cancelled():
                return {'success': False, 'message': 'Import cancelled'}
            
            self.progress_updated.emit(100, "CSV import completed!")
            
            return {
                'success': True,
                'message': 'CSV import completed successfully',
                'record_count': len(data) if data is not None else 0,
                'file_path': self.file_path,
                'import_type': 'csv',
                'data': data
            }
            
        except Exception as e:
            logger.error(f"CSV import failed: {e}")
            raise