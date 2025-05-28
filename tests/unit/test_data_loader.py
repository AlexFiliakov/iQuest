"""
Unit tests for the data_loader module
"""

import unittest
import tempfile
import sqlite3
import pandas as pd
from pathlib import Path
import xml.etree.ElementTree as ET
import os
import sys
import gc
import shutil
import time

# Add the src directory to the path so we can import the data_loader module
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from src.data_loader import (
    convert_xml_to_sqlite,
    query_date_range,
    get_daily_summary,
    get_weekly_summary,
    get_monthly_summary,
    get_available_types,
    get_date_range,
    migrate_csv_to_sqlite,
    validate_database
)


class TestDataLoader(unittest.TestCase):
    
    def setUp(self):
        """Create temporary files for testing"""
        # Create a temporary directory
        self.test_dir = tempfile.mkdtemp()
        
        # Create sample XML content
        self.sample_xml = """<?xml version="1.0" encoding="UTF-8"?>
<HealthData>
    <Record type="HKQuantityTypeIdentifierStepCount" 
            sourceName="iPhone" 
            sourceVersion="13.0" 
            unit="count" 
            creationDate="2024-01-01 10:00:00 +0000" 
            startDate="2024-01-01 09:00:00 +0000" 
            endDate="2024-01-01 10:00:00 +0000" 
            value="1000"/>
    <Record type="HKQuantityTypeIdentifierHeartRate" 
            sourceName="Apple Watch" 
            sourceVersion="7.0" 
            unit="count/min" 
            creationDate="2024-01-01 11:00:00 +0000" 
            startDate="2024-01-01 10:30:00 +0000" 
            endDate="2024-01-01 10:31:00 +0000" 
            value="75"/>
    <Record type="HKQuantityTypeIdentifierStepCount" 
            sourceName="iPhone" 
            sourceVersion="13.0" 
            unit="count" 
            creationDate="2024-01-02 10:00:00 +0000" 
            startDate="2024-01-02 09:00:00 +0000" 
            endDate="2024-01-02 10:00:00 +0000" 
            value="1500"/>
</HealthData>"""
        
        # Write sample XML file
        self.xml_path = Path(self.test_dir) / "test_export.xml"
        with open(self.xml_path, 'w') as f:
            f.write(self.sample_xml)
            
        # Create sample CSV data
        self.sample_csv_data = pd.DataFrame({
            'type': ['StepCount', 'HeartRate', 'StepCount'],
            'sourceName': ['iPhone', 'Apple Watch', 'iPhone'],
            'sourceVersion': ['13.0', '7.0', '13.0'],
            'unit': ['count', 'count/min', 'count'],
            'creationDate': pd.to_datetime(['2024-01-01 10:00:00', '2024-01-01 11:00:00', '2024-01-02 10:00:00']),
            'startDate': pd.to_datetime(['2024-01-01 09:00:00', '2024-01-01 10:30:00', '2024-01-02 09:00:00']),
            'endDate': pd.to_datetime(['2024-01-01 10:00:00', '2024-01-01 10:31:00', '2024-01-02 10:00:00']),
            'value': [1000.0, 75.0, 1500.0],
            'device': ['', '', '']
        })
        
        # Write sample CSV file
        self.csv_path = Path(self.test_dir) / "test_data.csv"
        self.sample_csv_data.to_csv(self.csv_path, index=False)
        
        # Database paths
        self.db_path = Path(self.test_dir) / "test_health.db"
        
    def tearDown(self):
        """Clean up temporary files"""
        # Force garbage collection to close any lingering database connections
        gc.collect()
        
        # Give Windows time to release file handles
        time.sleep(0.1)
        
        # Try to remove the directory, with retry on Windows
        max_attempts = 3
        for attempt in range(max_attempts):
            try:
                shutil.rmtree(self.test_dir)
                break
            except PermissionError:
                if attempt < max_attempts - 1:
                    time.sleep(0.2)
                else:
                    # If we can't delete, at least try to clean up the files
                    try:
                        for file in Path(self.test_dir).glob('*'):
                            try:
                                file.unlink()
                            except:
                                pass
                    except:
                        pass
        
    def test_convert_xml_to_sqlite(self):
        """Test XML to SQLite conversion"""
        record_count = convert_xml_to_sqlite(str(self.xml_path), str(self.db_path))
        
        # Check that records were imported
        self.assertEqual(record_count, 3)
        
        # Verify database structure
        with sqlite3.connect(self.db_path) as conn:
            # Check tables exist
            tables = conn.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()
            table_names = [t[0] for t in tables]
            self.assertIn('health_records', table_names)
            self.assertIn('metadata', table_names)
            
            # Check indexes exist
            indexes = conn.execute("SELECT name FROM sqlite_master WHERE type='index'").fetchall()
            index_names = [i[0] for i in indexes]
            self.assertIn('idx_creation_date', index_names)
            self.assertIn('idx_type', index_names)
            self.assertIn('idx_type_date', index_names)
            
            # Check data
            records = conn.execute("SELECT COUNT(*) FROM health_records").fetchone()[0]
            self.assertEqual(records, 3)
            
            # Check type cleaning
            types = conn.execute("SELECT DISTINCT type FROM health_records ORDER BY type").fetchall()
            type_names = [t[0] for t in types]
            self.assertIn('StepCount', type_names)
            self.assertIn('HeartRate', type_names)
            
    def test_query_date_range(self):
        """Test date range queries"""
        # First convert XML to SQLite
        convert_xml_to_sqlite(str(self.xml_path), str(self.db_path))
        
        # Query all records (need to include the full day)
        df = query_date_range(str(self.db_path), '2024-01-01', '2024-01-02 23:59:59')
        self.assertEqual(len(df), 3)
        
        # Query specific type
        df_steps = query_date_range(str(self.db_path), '2024-01-01', '2024-01-02 23:59:59', 'StepCount')
        self.assertEqual(len(df_steps), 2)
        
        # Query with no results
        df_empty = query_date_range(str(self.db_path), '2023-01-01', '2023-12-31')
        self.assertEqual(len(df_empty), 0)
        
    def test_get_daily_summary(self):
        """Test daily summary generation"""
        # First convert XML to SQLite
        convert_xml_to_sqlite(str(self.xml_path), str(self.db_path))
        
        # Get daily summary for steps
        df_summary = get_daily_summary(str(self.db_path), 'StepCount')
        
        self.assertEqual(len(df_summary), 2)  # Two days of data
        self.assertEqual(df_summary.iloc[0]['total_value'], 1000.0)
        self.assertEqual(df_summary.iloc[1]['total_value'], 1500.0)
        
    def test_get_weekly_summary(self):
        """Test weekly summary generation"""
        # First convert XML to SQLite
        convert_xml_to_sqlite(str(self.xml_path), str(self.db_path))
        
        # Get weekly summary for steps
        df_summary = get_weekly_summary(str(self.db_path), 'StepCount')
        
        self.assertEqual(len(df_summary), 1)  # All data in same week
        self.assertEqual(df_summary.iloc[0]['total_value'], 2500.0)
        self.assertEqual(df_summary.iloc[0]['avg_value'], 1250.0)
        
    def test_get_monthly_summary(self):
        """Test monthly summary generation"""
        # First convert XML to SQLite
        convert_xml_to_sqlite(str(self.xml_path), str(self.db_path))
        
        # Get monthly summary for steps
        df_summary = get_monthly_summary(str(self.db_path), 'StepCount')
        
        self.assertEqual(len(df_summary), 1)  # All data in same month
        self.assertEqual(df_summary.iloc[0]['total_value'], 2500.0)
        self.assertEqual(df_summary.iloc[0]['count'], 2)
        
    def test_get_available_types(self):
        """Test getting available record types"""
        # First convert XML to SQLite
        convert_xml_to_sqlite(str(self.xml_path), str(self.db_path))
        
        types = get_available_types(str(self.db_path))
        
        self.assertEqual(len(types), 2)
        self.assertIn('StepCount', types)
        self.assertIn('HeartRate', types)
        
    def test_get_date_range(self):
        """Test getting date range of data"""
        # First convert XML to SQLite
        convert_xml_to_sqlite(str(self.xml_path), str(self.db_path))
        
        min_date, max_date = get_date_range(str(self.db_path))
        
        self.assertIsNotNone(min_date)
        self.assertIsNotNone(max_date)
        self.assertTrue(min_date <= max_date)
        
    def test_migrate_csv_to_sqlite(self):
        """Test CSV to SQLite migration"""
        record_count = migrate_csv_to_sqlite(str(self.csv_path), str(self.db_path))
        
        self.assertEqual(record_count, 3)
        
        # Verify database
        with sqlite3.connect(self.db_path) as conn:
            records = conn.execute("SELECT COUNT(*) FROM health_records").fetchone()[0]
            self.assertEqual(records, 3)
            
            # Check that dates are properly stored
            dates = conn.execute("SELECT creationDate FROM health_records").fetchall()
            self.assertEqual(len(dates), 3)
            
    def test_validate_database(self):
        """Test database validation"""
        # Test non-existent database
        result = validate_database(str(self.db_path))
        self.assertFalse(result['exists'])
        self.assertIn('Database file does not exist', result['errors'])
        
        # Create valid database
        convert_xml_to_sqlite(str(self.xml_path), str(self.db_path))
        
        # Test valid database
        result = validate_database(str(self.db_path))
        self.assertTrue(result['exists'])
        self.assertTrue(result['has_health_records'])
        self.assertTrue(result['has_indexes'])
        self.assertTrue(result['has_metadata'])
        self.assertEqual(result['record_count'], 3)
        self.assertEqual(len(result['errors']), 0)
        
    def test_error_handling(self):
        """Test error handling for invalid inputs"""
        # Test with non-existent XML file
        with self.assertRaises(Exception):
            convert_xml_to_sqlite("non_existent.xml", str(self.db_path))
            
        # Test with invalid XML content
        invalid_xml_path = Path(self.test_dir) / "invalid.xml"
        with open(invalid_xml_path, 'w') as f:
            f.write("This is not valid XML")
            
        with self.assertRaises(ET.ParseError):
            convert_xml_to_sqlite(str(invalid_xml_path), str(self.db_path))
            
    def test_value_conversion(self):
        """Test that values are properly converted to numeric"""
        # Create XML with non-numeric value
        xml_with_nan = """<?xml version="1.0" encoding="UTF-8"?>
<HealthData>
    <Record type="HKCategoryTypeIdentifierSleepAnalysis" 
            sourceName="iPhone" 
            sourceVersion="13.0" 
            unit="" 
            creationDate="2024-01-01 10:00:00 +0000" 
            startDate="2024-01-01 09:00:00 +0000" 
            endDate="2024-01-01 10:00:00 +0000" 
            value="HKCategoryValueSleepAnalysisAsleep"/>
</HealthData>"""
        
        xml_path = Path(self.test_dir) / "test_nan.xml"
        with open(xml_path, 'w') as f:
            f.write(xml_with_nan)
            
        convert_xml_to_sqlite(str(xml_path), str(self.db_path))
        
        # Check that non-numeric value was converted to 1.0
        with sqlite3.connect(self.db_path) as conn:
            value = conn.execute("SELECT value FROM health_records").fetchone()[0]
            self.assertEqual(value, 1.0)
            
    def test_input_validation(self):
        """Test input validation for query functions"""
        # Create valid database first
        convert_xml_to_sqlite(str(self.xml_path), str(self.db_path))
        
        # Test invalid record_type
        with self.assertRaises(ValueError):
            get_daily_summary(str(self.db_path), "")
            
        with self.assertRaises(ValueError):
            get_daily_summary(str(self.db_path), None)
            
        with self.assertRaises(ValueError):
            get_weekly_summary(str(self.db_path), "")
            
        with self.assertRaises(ValueError):
            get_monthly_summary(str(self.db_path), "")
            
    def test_file_not_found_errors(self):
        """Test proper FileNotFoundError handling"""
        # Test XML file not found
        with self.assertRaises(FileNotFoundError) as cm:
            convert_xml_to_sqlite("non_existent.xml", str(self.db_path))
        self.assertIn("XML file not found", str(cm.exception))
        
        # Test CSV file not found
        with self.assertRaises(FileNotFoundError) as cm:
            migrate_csv_to_sqlite("non_existent.csv", str(self.db_path))
        self.assertIn("CSV file not found", str(cm.exception))


if __name__ == '__main__':
    unittest.main()