"""
Unit tests for XML Streaming Processor

Tests the memory-efficient XML processing functionality for Apple Health data.
"""

import pytest
import tempfile
import sqlite3
import os
from pathlib import Path
from unittest.mock import Mock, patch
import xml.etree.ElementTree as ET

from src.xml_streaming_processor import (
    XMLStreamingProcessor, 
    AppleHealthHandler, 
    MemoryMonitor
)


class TestMemoryMonitor:
    """Test memory monitoring functionality."""
    
    def test_initialization(self):
        """Test memory monitor initialization."""
        monitor = MemoryMonitor(limit_mb=500)
        assert monitor.limit_mb == 500
        assert monitor.process is not None
    
    def test_memory_usage_calculation(self):
        """Test memory usage calculations."""
        monitor = MemoryMonitor(limit_mb=100)
        
        # Memory usage should be positive
        usage = monitor.get_current_usage_mb()
        assert usage > 0
        
        # Usage percentage calculation
        percentage = monitor.get_usage_percentage()
        assert percentage > 0
        assert percentage == (usage / 100) * 100
    
    def test_over_limit_detection(self):
        """Test over-limit detection."""
        # Test with very low limit to trigger over-limit
        monitor = MemoryMonitor(limit_mb=1)  # 1MB limit
        assert monitor.is_over_limit() is True
        
        # Test with very high limit
        monitor = MemoryMonitor(limit_mb=10000)  # 10GB limit
        assert monitor.is_over_limit() is False


class TestXMLStreamingProcessor:
    """Test XML streaming processor functionality."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.processor = XMLStreamingProcessor(memory_limit_mb=500)
        self.temp_dir = tempfile.mkdtemp()
    
    def teardown_method(self):
        """Clean up test fixtures."""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_initialization(self):
        """Test processor initialization."""
        assert self.processor.memory_limit_mb == 500
        assert self.processor.memory_monitor is not None
    
    def test_chunk_size_calculation(self):
        """Test chunk size calculation based on file size."""
        # Small file (<50MB)
        small_size = 30 * 1024 * 1024  # 30MB
        chunk_size = self.processor.calculate_chunk_size(small_size)
        assert chunk_size == 10000
        
        # Medium file (<200MB)
        medium_size = 100 * 1024 * 1024  # 100MB
        chunk_size = self.processor.calculate_chunk_size(medium_size)
        assert chunk_size == 5000
        
        # Large file (>200MB)
        large_size = 500 * 1024 * 1024  # 500MB
        chunk_size = self.processor.calculate_chunk_size(large_size)
        assert chunk_size == 2500
    
    def test_streaming_decision(self):
        """Test decision logic for using streaming vs memory processing."""
        # Create a small test file
        small_file = Path(self.temp_dir) / "small.xml"
        small_file.write_text("<HealthData></HealthData>")
        
        # Small file should not use streaming
        assert self.processor.should_use_streaming(str(small_file)) is False
        
        # Mock a large file size
        with patch('os.path.getsize', return_value=500 * 1024 * 1024):  # 500MB
            assert self.processor.should_use_streaming(str(small_file)) is True
    
    def create_sample_xml(self, record_count: int = 100) -> str:
        """Create a sample Apple Health XML file for testing."""
        xml_path = Path(self.temp_dir) / "test_export.xml"
        
        # Create XML content
        root = ET.Element("HealthData", locale="en_US")
        
        # Add export date
        export_date = ET.SubElement(root, "ExportDate")
        export_date.set("value", "2024-01-01 12:00:00 -0500")
        
        # Add sample records
        for i in range(record_count):
            record = ET.SubElement(root, "Record")
            record.set("type", "HKQuantityTypeIdentifierStepCount")
            record.set("sourceName", "iPhone")
            record.set("sourceVersion", "17.0")
            record.set("unit", "count")
            record.set("creationDate", f"2024-01-{(i % 30) + 1:02d} 10:00:00 -0500")
            record.set("startDate", f"2024-01-{(i % 30) + 1:02d} 09:00:00 -0500")
            record.set("endDate", f"2024-01-{(i % 30) + 1:02d} 10:00:00 -0500")
            record.set("value", str(1000 + i))
        
        # Write to file
        tree = ET.ElementTree(root)
        tree.write(xml_path, encoding="utf-8", xml_declaration=True)
        
        return str(xml_path)
    
    def test_small_file_processing(self):
        """Test processing of small XML files (memory-based)."""
        # Create small test file
        xml_path = self.create_sample_xml(record_count=50)
        db_path = Path(self.temp_dir) / "test.db"
        
        # Mock the convert_xml_to_sqlite function by patching the data_loader module
        with patch('src.data_loader.convert_xml_to_sqlite') as mock_convert:
            mock_convert.return_value = 50
            
            record_count = self.processor.process_xml_file(
                xml_path, str(db_path)
            )
            
            assert record_count == 50
            mock_convert.assert_called_once_with(xml_path, str(db_path))
    
    def test_progress_callback(self):
        """Test progress callback functionality."""
        xml_path = self.create_sample_xml(record_count=100)
        db_path = Path(self.temp_dir) / "test.db"
        
        # Mock file size to force streaming
        with patch('os.path.getsize', return_value=500 * 1024 * 1024):
            progress_calls = []
            
            def progress_callback(percent, records):
                progress_calls.append((percent, records))
            
            # This would normally process the file, but we'll mock the handler
            with patch.object(self.processor, '_stream_process') as mock_stream:
                mock_stream.return_value = 100
                
                record_count = self.processor.process_xml_file(
                    xml_path, str(db_path), progress_callback
                )
                
                assert record_count == 100
                mock_stream.assert_called_once()
    
    def test_file_not_found_error(self):
        """Test error handling for missing files."""
        with pytest.raises(FileNotFoundError):
            self.processor.process_xml_file(
                "nonexistent.xml", 
                "test.db"
            )


class TestAppleHealthHandler:
    """Test SAX handler functionality."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.db_path = Path(self.temp_dir) / "test.db"
    
    def teardown_method(self):
        """Clean up test fixtures."""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_handler_initialization(self):
        """Test handler initialization."""
        handler = AppleHealthHandler(str(self.db_path))
        
        assert handler.db_path == str(self.db_path)
        assert handler.record_count == 0
        assert handler.records == []
        assert handler.conn is not None
        
        # Verify database tables were created
        cursor = handler.conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table'"
        )
        tables = [row[0] for row in cursor.fetchall()]
        assert 'health_records' in tables
        assert 'metadata' in tables
        
        handler.finalize()
    
    def test_record_cleaning(self):
        """Test record cleaning and validation."""
        handler = AppleHealthHandler(str(self.db_path))
        
        # Test valid record
        valid_record = {
            'type': 'HKQuantityTypeIdentifierStepCount',
            'sourceName': 'iPhone',
            'creationDate': '2024-01-01 10:00:00 -0500',
            'value': '1000'
        }
        
        cleaned = handler._clean_record(valid_record)
        assert cleaned is not None
        assert cleaned['type'] == 'StepCount'  # Prefix removed
        assert cleaned['value'] == 1000.0
        
        # Test invalid record (missing required fields)
        invalid_record = {
            'sourceName': 'iPhone'
            # Missing type and creationDate
        }
        
        cleaned = handler._clean_record(invalid_record)
        assert cleaned is None
        
        handler.finalize()
    
    def test_numeric_value_parsing(self):
        """Test numeric value parsing."""
        handler = AppleHealthHandler(str(self.db_path))
        
        # Test valid numeric values
        assert handler._parse_numeric_value("123.45") == 123.45
        assert handler._parse_numeric_value("0") == 0.0
        
        # Test invalid/empty values
        assert handler._parse_numeric_value("") == 1.0
        assert handler._parse_numeric_value(None) == 1.0
        assert handler._parse_numeric_value("invalid") == 1.0
        
        handler.finalize()
    
    def test_progress_callback_integration(self):
        """Test progress callback integration."""
        progress_calls = []
        
        def progress_callback(percent, records):
            progress_calls.append((percent, records))
        
        handler = AppleHealthHandler(
            str(self.db_path), 
            progress_callback=progress_callback,
            chunk_size=2  # Small chunk for testing
        )
        handler.set_file_size(1000)  # Mock file size
        
        # Simulate processing records
        test_record = {
            'type': 'HKQuantityTypeIdentifierStepCount',
            'sourceName': 'iPhone',
            'creationDate': '2024-01-01 10:00:00 -0500',
            'value': '1000'
        }
        
        # Process a few records
        handler._process_record(test_record)
        # Simulate bytes processed to trigger progress callback
        handler.bytes_processed = 1000  # Reached end of file
        handler._process_record(test_record)
        
        # Should have triggered progress callbacks
        assert len(progress_calls) >= 1
        
        handler.finalize()
    
    def test_database_batch_insertion(self):
        """Test batched database insertion."""
        handler = AppleHealthHandler(
            str(self.db_path),
            chunk_size=3  # Small chunk for testing
        )
        
        # Create test records
        test_records = []
        for i in range(5):
            record = {
                'type': f'HKQuantityTypeIdentifierStepCount',
                'sourceName': 'iPhone',
                'creationDate': f'2024-01-{i+1:02d} 10:00:00 -0500',
                'value': str(1000 + i)
            }
            test_records.append(record)
        
        # Process records (should trigger flush at chunk_size=3)
        for record in test_records:
            handler._process_record(record)
        
        # Finalize to flush remaining records
        total_records = handler.finalize()
        
        # Verify records in database
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.execute("SELECT COUNT(*) FROM health_records")
        db_count = cursor.fetchone()[0]
        conn.close()
        
        assert total_records == 5
        assert db_count == 5


# Integration tests
class TestIntegration:
    """Integration tests for the complete streaming processor."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.processor = XMLStreamingProcessor(memory_limit_mb=100)  # Low limit for testing
    
    def teardown_method(self):
        """Clean up test fixtures."""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def create_large_xml(self, record_count: int = 1000) -> str:
        """Create a larger XML file for integration testing."""
        xml_path = Path(self.temp_dir) / "large_export.xml"
        
        with open(xml_path, 'w', encoding='utf-8') as f:
            f.write('<?xml version="1.0" encoding="UTF-8"?>\n')
            f.write('<HealthData locale="en_US">\n')
            f.write('  <ExportDate value="2024-01-01 12:00:00 -0500"/>\n')
            
            # Write records
            for i in range(record_count):
                f.write(f'  <Record type="HKQuantityTypeIdentifierStepCount" ')
                f.write(f'sourceName="iPhone" sourceVersion="17.0" ')
                f.write(f'unit="count" ')
                f.write(f'creationDate="2024-01-{(i % 30) + 1:02d} 10:{i % 60:02d}:00 -0500" ')
                f.write(f'startDate="2024-01-{(i % 30) + 1:02d} 09:{i % 60:02d}:00 -0500" ')
                f.write(f'endDate="2024-01-{(i % 30) + 1:02d} 10:{i % 60:02d}:00 -0500" ')
                f.write(f'value="{1000 + i}"/>\n')
            
            f.write('</HealthData>\n')
        
        return str(xml_path)
    
    @pytest.mark.integration
    def test_end_to_end_streaming_processing(self):
        """Test complete end-to-end streaming processing."""
        # Create test XML file
        xml_path = self.create_large_xml(record_count=500)
        db_path = Path(self.temp_dir) / "integration_test.db"
        
        # Force streaming by mocking file size
        with patch.object(self.processor, 'should_use_streaming', return_value=True):
            progress_updates = []
            
            def progress_callback(percent, records):
                progress_updates.append((percent, records))
            
            # Process the file
            record_count = self.processor.process_xml_file(
                xml_path, str(db_path), progress_callback
            )
            
            # Verify results
            assert record_count == 500
            assert len(progress_updates) > 0
            
            # Verify database content
            conn = sqlite3.connect(str(db_path))
            cursor = conn.execute("SELECT COUNT(*) FROM health_records")
            db_count = cursor.fetchone()[0]
            
            cursor = conn.execute("SELECT DISTINCT type FROM health_records")
            types = [row[0] for row in cursor.fetchall()]
            
            conn.close()
            
            assert db_count == 500
            assert 'StepCount' in types  # Type prefix should be removed
    
    @pytest.mark.integration  
    def test_memory_monitoring_during_processing(self):
        """Test memory monitoring during actual processing."""
        # Create test file
        xml_path = self.create_large_xml(record_count=200)
        db_path = Path(self.temp_dir) / "memory_test.db"
        
        # Use low memory limit to test monitoring
        processor = XMLStreamingProcessor(memory_limit_mb=50)
        
        with patch.object(processor, 'should_use_streaming', return_value=True):
            # Process and verify no memory errors
            record_count = processor.process_xml_file(xml_path, str(db_path))
            assert record_count == 200
            
            # Verify final memory usage is reasonable
            final_memory = processor.memory_monitor.get_current_usage_mb()
            assert final_memory > 0  # Should have some memory usage


if __name__ == "__main__":
    pytest.main([__file__, "-v"])