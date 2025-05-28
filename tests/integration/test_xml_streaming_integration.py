"""Integration tests for XML Streaming Processor."""

import pytest
import os
import tempfile
import time
import sys
from pathlib import Path
import sqlite3

# Add the project root to Python path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

try:
    from src.xml_streaming_processor import XMLStreamingProcessor, MemoryMonitor
except ImportError as e:
    pytest.skip(f"XML streaming processor not available: {e}", allow_module_level=True)


class TestXMLStreamingIntegration:
    """Test the XML streaming processor with real Apple Health data."""
    
    @pytest.fixture
    def sample_xml_path(self):
        """Get path to sample XML file if it exists."""
        # Try multiple possible locations
        possible_paths = [
            "raw data/apple_health_export_2024-11-3/export.xml",
            "raw data/AppleHealth-2025-05-24/apple_health_export/export.xml",
            "tests/fixtures/sample_export.xml"
        ]
        
        for path in possible_paths:
            if Path(path).exists():
                return path
        
        # If no real file exists, skip the test
        pytest.skip("No sample Apple Health XML file found")
    
    @pytest.fixture
    def temp_database(self):
        """Create a temporary database for testing."""
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as temp_db:
            db_path = temp_db.name
        
        yield db_path
        
        # Cleanup
        if Path(db_path).exists():
            os.unlink(db_path)
    
    def test_memory_monitor(self):
        """Test memory monitoring functionality."""
        monitor = MemoryMonitor(limit_mb=100)
        
        # Basic functionality tests
        current_usage = monitor.get_current_usage_mb()
        assert current_usage > 0
        assert isinstance(current_usage, float)
        
        percentage = monitor.get_usage_percentage()
        assert 0 <= percentage <= 1000  # Allow for systems using more than limit
        
        # Memory limit check
        is_over = monitor.is_over_limit()
        assert isinstance(is_over, bool)
    
    def test_chunk_size_calculation(self):
        """Test chunk size calculation for different file sizes."""
        processor = XMLStreamingProcessor()
        
        # Test small file (30MB)
        chunk_size_small = processor.calculate_chunk_size(30 * 1024 * 1024)
        assert chunk_size_small > 0
        assert chunk_size_small <= 10000  # Should be reasonable batch size
        
        # Test medium file (100MB)
        chunk_size_medium = processor.calculate_chunk_size(100 * 1024 * 1024)
        assert chunk_size_medium > 0
        assert chunk_size_medium <= chunk_size_small  # Larger files should have smaller chunks
        
        # Test large file (500MB)
        chunk_size_large = processor.calculate_chunk_size(500 * 1024 * 1024)
        assert chunk_size_large > 0
        assert chunk_size_large <= chunk_size_medium
        
        # Minimum chunk size
        assert chunk_size_large >= 100  # Never go below 100 records per chunk
    
    @pytest.mark.integration
    def test_streaming_processor_with_real_data(self, sample_xml_path, temp_database):
        """Test the streaming processor with a real XML file."""
        processor = XMLStreamingProcessor(memory_limit_mb=200)
        
        # Track progress
        progress_updates = []
        def progress_callback(percent, records):
            progress_updates.append((percent, records))
        
        # Get file size
        file_size_mb = Path(sample_xml_path).stat().st_size / (1024 * 1024)
        
        # Process the file
        start_time = time.time()
        record_count = processor.process_xml_file(
            sample_xml_path, 
            temp_database, 
            progress_callback
        )
        processing_time = time.time() - start_time
        
        # Verify results
        assert record_count > 0
        assert len(progress_updates) > 0
        
        # Verify database
        conn = sqlite3.connect(temp_database)
        cursor = conn.execute("SELECT COUNT(*) FROM health_records")
        db_count = cursor.fetchone()[0]
        conn.close()
        
        assert db_count == record_count
        
        # Performance checks (reasonable for XML processing)
        records_per_second = record_count / processing_time if processing_time > 0 else 0
        assert records_per_second > 100  # Should process at least 100 records/second
        
        # Memory check
        final_memory = processor.memory_monitor.get_current_usage_mb()
        assert final_memory < 500  # Should stay under 500MB even for large files
    
    def test_streaming_decision_logic(self):
        """Test the logic for deciding when to use streaming."""
        processor = XMLStreamingProcessor()
        
        # Mock file sizes
        class MockPath:
            def __init__(self, size_bytes):
                self.size_bytes = size_bytes
            
            def stat(self):
                class MockStat:
                    def __init__(self, size):
                        self.st_size = size
                return MockStat(self.size_bytes)
        
        # Small file should not stream
        with pytest.MonkeyPatch.context() as m:
            m.setattr(Path, '__new__', lambda cls, path: MockPath(10 * 1024 * 1024))
            assert not processor.should_use_streaming("dummy.xml")
        
        # Large file should stream
        with pytest.MonkeyPatch.context() as m:
            m.setattr(Path, '__new__', lambda cls, path: MockPath(100 * 1024 * 1024))
            assert processor.should_use_streaming("dummy.xml")
    
    @pytest.mark.integration
    def test_database_structure(self, sample_xml_path, temp_database):
        """Test that the created database has the correct structure."""
        processor = XMLStreamingProcessor()
        
        # Process a small portion of the file
        processor.process_xml_file(
            sample_xml_path, 
            temp_database,
            lambda p, r: None  # No progress callback needed
        )
        
        # Check database structure
        conn = sqlite3.connect(temp_database)
        
        # Check tables exist
        cursor = conn.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = [row[0] for row in cursor.fetchall()]
        assert 'health_records' in tables
        assert 'metadata' in tables
        
        # Check health_records columns
        cursor = conn.execute("PRAGMA table_info(health_records)")
        columns = {row[1] for row in cursor.fetchall()}
        expected_columns = {'type', 'sourceName', 'unit', 'creationDate', 'startDate', 'endDate', 'value'}
        assert expected_columns.issubset(columns)
        
        # Check indexes
        cursor = conn.execute("SELECT name FROM sqlite_master WHERE type='index'")
        indexes = [row[0] for row in cursor.fetchall()]
        assert any('creation_date' in idx for idx in indexes)
        assert any('type' in idx for idx in indexes)
        
        conn.close()
    
    def test_error_handling(self, temp_database):
        """Test error handling for invalid inputs."""
        processor = XMLStreamingProcessor()
        
        # Non-existent file
        with pytest.raises(FileNotFoundError):
            processor.process_xml_file("non_existent.xml", temp_database)
        
        # Invalid XML content
        with tempfile.NamedTemporaryFile(mode='w', suffix='.xml', delete=False) as f:
            f.write("This is not valid XML")
            invalid_xml = f.name
        
        try:
            with pytest.raises(Exception):  # Should raise some parsing error
                processor.process_xml_file(invalid_xml, temp_database)
        finally:
            os.unlink(invalid_xml)