"""
Import Worker Thread for non-blocking XML/CSV import operations.

This module provides threaded import functionality to keep the UI responsive
during long-running import operations.
"""

import os
import shutil
import time
import uuid
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any

from PyQt6.QtCore import QThread, pyqtSignal, QMutex
from PyQt6.QtWidgets import QApplication

try:
    from ..utils.logging_config import get_logger
    from ..data_loader import convert_xml_to_sqlite_with_validation, DataLoader, migrate_csv_to_sqlite
    from ..database import db_manager
    from ..config import DATA_DIR, DEFAULT_MEMORY_LIMIT_MB
    from ..xml_streaming_processor import XMLStreamingProcessor
    from ..analytics.summary_calculator import SummaryCalculator
    from ..analytics.cache_manager import AnalyticsCacheManager
    from ..data_access import DataAccess
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
    from src.data_loader import convert_xml_to_sqlite_with_validation, DataLoader, migrate_csv_to_sqlite
    from src.database import db_manager
    from src.config import DATA_DIR, DEFAULT_MEMORY_LIMIT_MB
    from src.xml_streaming_processor import XMLStreamingProcessor
    from src.analytics.summary_calculator import SummaryCalculator
    from src.analytics.cache_manager import AnalyticsCacheManager
    from src.data_access import DataAccess

logger = get_logger(__name__)


class ImportWorker(QThread):
    """Worker thread for handling import operations with progress updates."""
    
    # Signals for progress communication
    progress_updated = pyqtSignal(int, str, int)  # (percentage, message, record_count)
    import_completed = pyqtSignal(dict)           # {success, message, stats}
    import_error = pyqtSignal(str, str)           # (title, message)
    
    def __init__(self, file_path: str, import_type: str = "auto", include_summaries: bool = True):
        """
        Initialize the import worker.
        
        Args:
            file_path: Path to the file to import
            import_type: Type of import ("xml", "csv", or "auto")
            include_summaries: Whether to calculate and cache summaries during import
        """
        super().__init__()
        self.file_path = file_path
        self.import_type = import_type
        self.include_summaries = include_summaries
        self._is_cancelled = False
        self._mutex = QMutex()
        self.data_loader = DataLoader()
        self.record_count = 0
        self.db_path = None
        self.import_id = None
        self._backup_db_path = None  # For rollback support
        
        # Auto-detect import type if needed
        if import_type == "auto":
            self.import_type = self._detect_file_type()
        
        logger.info(f"ImportWorker initialized for {import_type} import: {file_path}, include_summaries={include_summaries}")
    
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
            
            # Create database backup for rollback
            self._create_database_backup()
            
            # Invalidate existing cache before import
            try:
                from ..analytics.cache_manager import invalidate_all_cache
                invalidate_all_cache()
                logger.info("Invalidated cache before import")
            except Exception as e:
                logger.warning(f"Could not invalidate cache before import: {e}")
            
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
                # Clean up backup on success
                self._cleanup_backup()
            else:
                # Rollback on cancellation or failure
                self._rollback_database()
                if self.is_cancelled():
                    self.import_error.emit(
                        "Import Cancelled",
                        "Import was cancelled. All changes have been rolled back."
                    )
            
        except Exception as e:
            logger.error(f"Import failed with exception: {e}")
            # Rollback on any exception
            self._rollback_database()
            self.import_error.emit(
                "Import Error",
                f"An unexpected error occurred during import:\n{str(e)}\n\nAll changes have been rolled back."
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
        # Use the correct database filename from database.py
        DB_FILE_NAME = 'health_monitor.db'
        db_path = os.path.join(DATA_DIR, DB_FILE_NAME)
        os.makedirs(DATA_DIR, exist_ok=True)
        
        if self.is_cancelled():
            return {'success': False, 'message': 'Import cancelled'}
        
        self.progress_updated.emit(15, "Analyzing file size...", 0)
        
        # Get file size for progress tracking
        file_size = os.path.getsize(self.file_path)
        file_size_mb = file_size / (1024 * 1024)
        
        # Initialize streaming processor with configured memory limit
        from src.config import DEFAULT_MEMORY_LIMIT_MB
        processor = XMLStreamingProcessor(memory_limit_mb=DEFAULT_MEMORY_LIMIT_MB)
        
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
            
            # Store values for summary calculation
            self.record_count = record_count
            self.db_path = db_path
            self.import_id = str(uuid.uuid4())
            
            # Calculate and cache summaries if requested
            if self.include_summaries and record_count > 0:
                try:
                    self._calculate_and_cache_summaries()
                except Exception as e:
                    logger.warning(f"Summary caching failed (non-fatal): {e}")
                    # Don't fail the import if summary caching fails
            
            self.progress_updated.emit(100, "Import completed successfully!", record_count)
            
            return {
                'success': True,
                'message': 'XML import completed successfully',
                'record_count': record_count,
                'file_path': self.file_path,
                'import_type': 'xml',
                'file_size_mb': round(file_size_mb, 1),
                'import_id': self.import_id
            }
            
        except Exception as e:
            logger.error(f"XML import failed: {e}")
            raise
    
    def _import_csv(self) -> Dict[str, Any]:
        """Import CSV file with progress updates."""
        self.progress_updated.emit(10, "Preparing database...", 0)
        
        if self.is_cancelled():
            return {'success': False, 'message': 'Import cancelled'}
        
        try:
            # Prepare database path (same as XML import)
            DB_FILE_NAME = 'health_monitor.db'
            db_path = os.path.join(DATA_DIR, DB_FILE_NAME)
            os.makedirs(DATA_DIR, exist_ok=True)
            
            if self.is_cancelled():
                return {'success': False, 'message': 'Import cancelled'}
            
            self.progress_updated.emit(20, "Converting CSV to database format...", 0)
            
            # Create progress callback for CSV import
            def csv_progress_callback(percentage: float, record_count: int):
                if self.is_cancelled():
                    return False  # Signal cancellation
                self.progress_updated.emit(int(20 + percentage * 0.6), "Converting CSV data...", record_count)
                QApplication.processEvents()  # Keep UI responsive
                return True  # Continue processing
            
            # Use migrate_csv_to_sqlite to import CSV data into the database
            record_count = migrate_csv_to_sqlite(self.file_path, db_path, csv_progress_callback)
            
            if self.is_cancelled():
                return {'success': False, 'message': 'Import cancelled'}
            
            self.progress_updated.emit(80, "Processing complete", record_count)
            
            # Initialize database manager
            db_manager.initialize_database()
            
            # Store values for summary calculation
            self.record_count = record_count
            self.db_path = db_path
            self.import_id = str(uuid.uuid4())
            
            # Calculate and cache summaries if requested
            if self.include_summaries and record_count > 0:
                try:
                    self._calculate_and_cache_summaries()
                except Exception as e:
                    logger.warning(f"Summary caching failed (non-fatal): {e}")
                    # Don't fail the import if summary caching fails
            
            self.progress_updated.emit(100, "CSV import completed!", record_count)
            
            return {
                'success': True,
                'message': 'CSV import completed successfully',
                'record_count': record_count,
                'file_path': self.file_path,
                'import_type': 'csv',
                'import_id': self.import_id
            }
            
        except Exception as e:
            logger.error(f"CSV import failed: {e}")
            raise
    
    def _calculate_and_cache_summaries(self) -> None:
        """Calculate and cache metric summaries after import."""
        self.progress_updated.emit(91, "Calculating metric summaries...", self.record_count)
        
        try:
            # Create calculator with database access
            data_access = DataAccess()
            calculator = SummaryCalculator(data_access)
            
            # Define progress callback
            def progress_callback(percentage: float, message: str):
                # Map calculator progress (0-100) to import progress (91-98)
                import_progress = 91 + int(percentage * 7 / 100)
                self.progress_updated.emit(import_progress, message, self.record_count)
            
            # Calculate all summaries
            summaries = calculator.calculate_all_summaries(
                progress_callback=progress_callback,
                months_back=12  # Default to 12 months of history
            )
            
            # Cache the summaries
            self.progress_updated.emit(98, "Caching summaries...", self.record_count)
            from ..analytics.cache_manager import get_cache_manager
            cache_manager = get_cache_manager()
            cache_manager.cache_import_summaries(summaries, self.import_id)
            
            self.progress_updated.emit(99, "Summary caching complete", self.record_count)
            logger.info(f"Successfully cached {summaries['metadata']['metrics_processed']} metrics")
            
        except Exception as e:
            logger.error(f"Error calculating summaries: {e}")
            raise
    
    def _create_database_backup(self):
        """Create a backup of the current database for rollback."""
        try:
            # Prepare database path
            DB_FILE_NAME = 'health_monitor.db'
            self.db_path = os.path.join(DATA_DIR, DB_FILE_NAME)
            
            if Path(self.db_path).exists():
                # Create backup with timestamp
                import shutil
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                self._backup_db_path = os.path.join(DATA_DIR, f'health_monitor_backup_{timestamp}.db')
                
                shutil.copy2(self.db_path, self._backup_db_path)
                logger.info(f"Created database backup: {self._backup_db_path}")
            else:
                logger.info("No existing database to backup")
                self._backup_db_path = None
        except Exception as e:
            logger.error(f"Failed to create database backup: {e}")
            # Continue without backup - new imports will still work
            self._backup_db_path = None
    
    def _rollback_database(self):
        """Rollback database to the backup state."""
        try:
            if self._backup_db_path and Path(self._backup_db_path).exists():
                import shutil
                # Close any open connections first
                if hasattr(self, 'db_connection'):
                    self.db_connection.close()
                
                # Restore from backup
                shutil.move(self._backup_db_path, self.db_path)
                logger.info("Database rolled back successfully")
            elif self.db_path and Path(self.db_path).exists():
                # If no backup but database exists (new import), remove it
                os.remove(self.db_path)
                logger.info("Removed partially imported database")
        except Exception as e:
            logger.error(f"Failed to rollback database: {e}")
    
    def _cleanup_backup(self):
        """Remove the backup file after successful import."""
        try:
            if self._backup_db_path and Path(self._backup_db_path).exists():
                os.remove(self._backup_db_path)
                logger.info("Cleaned up database backup")
        except Exception as e:
            logger.warning(f"Failed to cleanup backup: {e}")