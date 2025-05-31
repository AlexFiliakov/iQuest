"""
Unit tests for data loader validation and transaction handling functionality.
"""

import pytest
import tempfile
import os
import sqlite3
from pathlib import Path
from unittest.mock import patch, MagicMock

from src.data_loader import convert_xml_to_sqlite_with_validation, _convert_xml_with_transaction
from src.utils.error_handler import DataValidationError, DatabaseError, DataImportError


class TestXMLTransactionHandling:
    """Test transaction handling in XML import."""
    
    def create_test_xml_file(self, content: str) -> str:
        """Helper to create a temporary XML file for testing."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.xml', delete=False) as f:
            f.write(content)
            return f.name
    
    def create_valid_xml(self) -> str:
        """Create a valid test XML file."""
        valid_xml = '''<?xml version="1.0" encoding="UTF-8"?>
        <HealthData locale="en_US">
            <Record type="HKQuantityTypeIdentifierStepCount" 
                    sourceName="iPhone" 
                    creationDate="2024-01-01T10:00:00+00:00" 
                    value="1000"
                    unit="count"/>
            <Record type="HKQuantityTypeIdentifierHeartRate" 
                    sourceName="Apple Watch" 
                    creationDate="2024-01-01T10:01:00+00:00" 
                    value="65"
                    unit="count/min"/>
        </HealthData>'''
        return self.create_test_xml_file(valid_xml)
    
    def create_invalid_xml(self) -> str:
        """Create an invalid test XML file."""
        invalid_xml = '''<?xml version="1.0" encoding="UTF-8"?>
        <HealthData locale="en_US">
            <Record type="HKQuantityTypeIdentifierStepCount" 
                    sourceName="iPhone" 
                    creationDate="invalid-date" 
                    value="not-a-number"/>
        </HealthData>'''
        return self.create_test_xml_file(invalid_xml)
    
    def test_validation_success_with_valid_xml(self):
        """Test successful validation and import with valid XML."""
        xml_file = self.create_valid_xml()
        
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as db_file:
            db_path = db_file.name
        
        try:
            record_count, summary = convert_xml_to_sqlite_with_validation(xml_file, db_path)
            
            assert record_count == 2
            assert "✅ Validation successful" in summary
            
            # Verify database was created and contains data
            conn = sqlite3.connect(db_path)
            cursor = conn.execute("SELECT COUNT(*) FROM health_records")
            db_count = cursor.fetchone()[0]
            conn.close()
            
            assert db_count == 2
            
        finally:
            os.unlink(xml_file)
            if os.path.exists(db_path):
                os.unlink(db_path)
    
    def test_validation_failure_with_invalid_xml(self):
        """Test validation failure with invalid XML."""
        xml_file = self.create_invalid_xml()
        
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as db_file:
            db_path = db_file.name
        
        # Test that validation fails with expected error
        error_occurred = False
        error_message = ""
        
        try:
            convert_xml_to_sqlite_with_validation(xml_file, db_path)
        except DataValidationError as e:
            error_occurred = True
            error_message = str(e)
        
        # Verify the error occurred and contains expected content
        assert error_occurred, "Expected DataValidationError was not raised"
        assert "XML validation failed" in error_message
        assert "Invalid datetime format" in error_message
        assert "Invalid numeric value" in error_message
        
        # Verify database was not created or is empty
        assert not os.path.exists(db_path) or os.path.getsize(db_path) == 0
        
        # Cleanup
        os.unlink(xml_file)
        if os.path.exists(db_path):
            os.unlink(db_path)
    
    def test_skip_validation_option(self):
        """Test skipping validation when validate_first=False."""
        xml_file = self.create_invalid_xml()
        
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as db_file:
            db_path = db_file.name
        
        try:
            # When validation is skipped, the import should proceed but may succeed
            # with warnings (pandas converts bad dates to NaT and bad numbers to NaN)
            # The test should actually expect successful completion with warnings
            record_count, summary = convert_xml_to_sqlite_with_validation(xml_file, db_path, validate_first=False)
            
            # Should succeed but record may have invalid data converted to defaults
            assert record_count == 1
            assert summary == ""  # No validation summary when skipped
            
        finally:
            os.unlink(xml_file)
            if os.path.exists(db_path):
                os.unlink(db_path)
    
    @patch('src.data_loader.sqlite3.connect')
    def test_transaction_rollback_on_database_error(self, mock_connect):
        """Test that transaction is rolled back on database errors."""
        xml_file = self.create_valid_xml()
        
        # Mock database connection that fails during verification count query
        mock_conn = MagicMock()
        mock_connect.return_value = mock_conn
        
        # Mock execute to succeed for BEGIN IMMEDIATE but fail on COUNT query
        mock_conn.execute.side_effect = [
            None,  # BEGIN IMMEDIATE
            sqlite3.Error("Database error")  # SELECT COUNT(*) query
        ]
        
        # Test that error is raised and rollback is called
        error_occurred = False
        error_message = ""
        
        try:
            _convert_xml_with_transaction(xml_file, "test.db")
        except DatabaseError as e:
            error_occurred = True
            error_message = str(e)
        
        # Verify error occurred with expected message
        assert error_occurred, "Expected DatabaseError was not raised"
        assert "Database import failed and was rolled back" in error_message
        
        # Verify rollback was called
        mock_conn.rollback.assert_called_once()
        
        # Cleanup
        os.unlink(xml_file)
    
    @patch('src.data_loader.sqlite3.connect')
    def test_transaction_rollback_on_import_verification_failure(self, mock_connect):
        """Test rollback when database operation fails."""
        xml_file = self.create_valid_xml()
        
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as db_file:
            db_path = db_file.name
        
        # Mock connection to raise an exception during execute
        mock_conn = MagicMock()
        mock_connect.return_value = mock_conn
        # Make the execute method raise an exception after BEGIN
        mock_conn.execute.side_effect = [None, sqlite3.Error("Test error")]
        
        # Test that error is raised when database operation fails
        error_occurred = False
        error_message = ""
        
        try:
            _convert_xml_with_transaction(xml_file, db_path)
        except DatabaseError as e:
            error_occurred = True
            error_message = str(e)
        
        # Verify error occurred with expected message
        assert error_occurred, "Expected DatabaseError was not raised"
        assert "Database import failed and was rolled back" in error_message
        
        # Verify rollback was called
        mock_conn.rollback.assert_called_once()
        
        # Cleanup
        os.unlink(xml_file)
        if os.path.exists(db_path):
            os.unlink(db_path)
    
    def test_metadata_creation_during_import(self):
        """Test that metadata is correctly created during import."""
        xml_file = self.create_valid_xml()
        
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as db_file:
            db_path = db_file.name
        
        try:
            record_count, _ = convert_xml_to_sqlite_with_validation(xml_file, db_path)
            
            # Check metadata table
            conn = sqlite3.connect(db_path)
            cursor = conn.execute("SELECT key, value FROM metadata")
            metadata = dict(cursor.fetchall())
            conn.close()
            
            assert 'import_date' in metadata
            assert 'record_count' in metadata
            assert 'source_file' in metadata
            assert metadata['record_count'] == str(record_count)
            assert xml_file in metadata['source_file']
            
        finally:
            os.unlink(xml_file)
            if os.path.exists(db_path):
                os.unlink(db_path)
    
    def test_index_creation_during_import(self):
        """Test that indexes are created during import."""
        xml_file = self.create_valid_xml()
        
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as db_file:
            db_path = db_file.name
        
        try:
            convert_xml_to_sqlite_with_validation(xml_file, db_path)
            
            # Check that indexes were created
            conn = sqlite3.connect(db_path)
            cursor = conn.execute("SELECT name FROM sqlite_master WHERE type='index'")
            indexes = [row[0] for row in cursor.fetchall()]
            conn.close()
            
            expected_indexes = ['idx_creation_date', 'idx_type', 'idx_type_date']
            for expected_index in expected_indexes:
                assert expected_index in indexes
            
        finally:
            os.unlink(xml_file)
            if os.path.exists(db_path):
                os.unlink(db_path)
    
    def test_nonexistent_xml_file(self):
        """Test handling of non-existent XML file."""
        with pytest.raises(FileNotFoundError):
            _convert_xml_with_transaction("nonexistent.xml", "test.db")
    
    def test_empty_xml_file(self):
        """Test handling of XML file with no records."""
        empty_xml = '''<?xml version="1.0" encoding="UTF-8"?>
        <HealthData locale="en_US">
        </HealthData>'''
        
        xml_file = self.create_test_xml_file(empty_xml)
        
        # Test that error is raised for empty XML
        error_occurred = False
        error_message = ""
        
        try:
            _convert_xml_with_transaction(xml_file, "test.db")
        except DataValidationError as e:
            error_occurred = True
            error_message = str(e)
        
        # Verify error occurred with expected message
        assert error_occurred, "Expected DataValidationError was not raised"
        assert "No health records found" in error_message
        
        # Cleanup
        os.unlink(xml_file)
    
    def test_malformed_xml_file(self):
        """Test handling of malformed XML."""
        malformed_xml = '''<?xml version="1.0" encoding="UTF-8"?>
        <HealthData locale="en_US">
            <Record type="Test" unclosed_tag>
        </HealthData'''
        
        xml_file = self.create_test_xml_file(malformed_xml)
        
        # Test that error is raised for malformed XML
        error_occurred = False
        error_message = ""
        
        try:
            _convert_xml_with_transaction(xml_file, "test.db")
        except DataImportError as e:
            error_occurred = True
            error_message = str(e)
        
        # Verify error occurred with expected message
        assert error_occurred, "Expected DataImportError was not raised"
        assert "XML parsing failed" in error_message
        assert "not well-formed" in error_message
        
        # Cleanup
        os.unlink(xml_file)


class TestDataTypeConversion:
    """Test data type conversion during XML import."""
    
    def create_test_xml_file(self, content: str) -> str:
        """Helper to create a temporary XML file for testing."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.xml', delete=False) as f:
            f.write(content)
            return f.name
    
    def test_datetime_conversion(self):
        """Test conversion of datetime fields."""
        xml_with_dates = '''<?xml version="1.0" encoding="UTF-8"?>
        <HealthData locale="en_US">
            <Record type="HKQuantityTypeIdentifierStepCount" 
                    sourceName="iPhone" 
                    creationDate="2024-01-01T10:00:00+00:00"
                    startDate="2024-01-01T09:59:00+00:00"
                    endDate="2024-01-01T10:01:00+00:00"
                    value="1000"/>
        </HealthData>'''
        
        xml_file = self.create_test_xml_file(xml_with_dates)
        
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as db_file:
            db_path = db_file.name
        
        try:
            convert_xml_to_sqlite_with_validation(xml_file, db_path, validate_first=False)
            
            # Check that dates were converted properly
            conn = sqlite3.connect(db_path)
            cursor = conn.execute("SELECT creationDate, startDate, endDate FROM health_records LIMIT 1")
            row = cursor.fetchone()
            conn.close()
            
            # All should be datetime strings
            assert row[0] is not None
            assert row[1] is not None
            assert row[2] is not None
            
        finally:
            os.unlink(xml_file)
            if os.path.exists(db_path):
                os.unlink(db_path)
    
    def test_value_conversion_with_nulls(self):
        """Test conversion of value field with null handling."""
        xml_with_nulls = '''<?xml version="1.0" encoding="UTF-8"?>
        <HealthData locale="en_US">
            <Record type="HKCategoryTypeIdentifierSleepAnalysis" 
                    sourceName="Sleep App" 
                    creationDate="2024-01-01T10:00:00+00:00"
                    value="HKCategoryValueSleepAnalysisInBed"/>
        </HealthData>'''
        
        xml_file = self.create_test_xml_file(xml_with_nulls)
        
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as db_file:
            db_path = db_file.name
        
        try:
            convert_xml_to_sqlite_with_validation(xml_file, db_path, validate_first=False)
            
            # Check that non-numeric value was converted to 1.0
            conn = sqlite3.connect(db_path)
            cursor = conn.execute("SELECT value FROM health_records LIMIT 1")
            value = cursor.fetchone()[0]
            conn.close()
            
            assert value == 1.0
            
        finally:
            os.unlink(xml_file)
            if os.path.exists(db_path):
                os.unlink(db_path)
    
    def test_type_name_cleaning(self):
        """Test cleaning of Apple Health type names."""
        xml_with_long_types = '''<?xml version="1.0" encoding="UTF-8"?>
        <HealthData locale="en_US">
            <Record type="HKQuantityTypeIdentifierStepCount" 
                    sourceName="iPhone" 
                    creationDate="2024-01-01T10:00:00+00:00"
                    value="1000"/>
            <Record type="HKCategoryTypeIdentifierSleepAnalysis" 
                    sourceName="Sleep App" 
                    creationDate="2024-01-01T10:00:00+00:00"
                    value="1"/>
        </HealthData>'''
        
        xml_file = self.create_test_xml_file(xml_with_long_types)
        
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as db_file:
            db_path = db_file.name
        
        try:
            convert_xml_to_sqlite_with_validation(xml_file, db_path, validate_first=False)
            
            # Check that type names were cleaned
            conn = sqlite3.connect(db_path)
            cursor = conn.execute("SELECT DISTINCT type FROM health_records ORDER BY type")
            types = [row[0] for row in cursor.fetchall()]
            conn.close()
            
            assert "StepCount" in types
            assert "SleepAnalysis" in types
            assert "HKQuantityTypeIdentifierStepCount" not in types
            assert "HKCategoryTypeIdentifierSleepAnalysis" not in types
            
        finally:
            os.unlink(xml_file)
            if os.path.exists(db_path):
                os.unlink(db_path)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])