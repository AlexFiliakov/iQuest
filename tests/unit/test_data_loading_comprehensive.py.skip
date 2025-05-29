"""Comprehensive tests for data loading modules."""

import pytest
from datetime import datetime, date, timedelta
from unittest.mock import Mock, patch, MagicMock, mock_open
import pandas as pd
import numpy as np
from pathlib import Path
import xml.etree.ElementTree as ET

from src.data_loader import DataLoader
from src.xml_streaming_processor import XMLStreamingProcessor
from src.data_filter_engine import DataFilterEngine
from src.data_availability_service import DataAvailabilityService


@pytest.fixture
def mock_database():
    """Create mock database."""
    db = Mock()
    db.execute_query = Mock()
    db.insert_data = Mock()
    db.get_available_types = Mock(return_value=['steps', 'heart_rate'])
    return db


@pytest.fixture
def data_loader(mock_database):
    """Create data loader instance."""
    return DataLoader(mock_database)


@pytest.fixture
def xml_processor():
    """Create XML streaming processor instance."""
    return XMLStreamingProcessor()


@pytest.fixture
def filter_engine():
    """Create data filter engine instance."""
    return DataFilterEngine()


@pytest.fixture
def availability_service(mock_database):
    """Create data availability service instance."""
    return DataAvailabilityService(mock_database)


class TestDataLoader:
    """Test DataLoader class."""
    
    def test_initialization(self, data_loader, mock_database):
        """Test data loader initialization."""
        assert data_loader.database == mock_database
        assert data_loader.supported_types is not None
        
    def test_load_csv_data(self, data_loader):
        """Test loading CSV data."""
        csv_content = """date,type,value
2023-01-01,steps,5000
2023-01-02,steps,6000
2023-01-03,heart_rate,72"""
        
        with patch('builtins.open', mock_open(read_data=csv_content)):
            with patch('pandas.read_csv') as mock_read:
                mock_read.return_value = pd.DataFrame({
                    'date': ['2023-01-01', '2023-01-02', '2023-01-03'],
                    'type': ['steps', 'steps', 'heart_rate'],
                    'value': [5000, 6000, 72]
                })
                
                result = data_loader.load_csv("test.csv")
                
        assert len(result) == 3
        assert 'date' in result.columns
        assert 'type' in result.columns
        assert 'value' in result.columns
        
    def test_load_json_data(self, data_loader):
        """Test loading JSON data."""
        json_data = {
            "records": [
                {"date": "2023-01-01", "type": "steps", "value": 5000},
                {"date": "2023-01-02", "type": "steps", "value": 6000}
            ]
        }
        
        with patch('builtins.open', mock_open()):
            with patch('json.load', return_value=json_data):
                result = data_loader.load_json("test.json")
                
        assert len(result) == 2
        
    def test_validate_data(self, data_loader):
        """Test data validation."""
        valid_data = pd.DataFrame({
            'date': pd.date_range('2023-01-01', periods=3),
            'type': ['steps', 'steps', 'heart_rate'],
            'value': [5000, 6000, 72]
        })
        
        # Should not raise exception
        validated = data_loader.validate_data(valid_data)
        assert len(validated) == 3
        
    def test_validate_data_missing_columns(self, data_loader):
        """Test validation with missing columns."""
        invalid_data = pd.DataFrame({
            'date': ['2023-01-01'],
            'value': [5000]
            # Missing 'type' column
        })
        
        with pytest.raises(ValueError, match="Missing required columns"):
            data_loader.validate_data(invalid_data)
            
    def test_validate_data_invalid_types(self, data_loader):
        """Test validation with invalid data types."""
        invalid_data = pd.DataFrame({
            'date': ['invalid_date'],
            'type': ['steps'],
            'value': ['not_a_number']
        })
        
        with pytest.raises(ValueError, match="Invalid data types"):
            data_loader.validate_data(invalid_data)
            
    def test_process_and_store(self, data_loader, mock_database):
        """Test processing and storing data."""
        data = pd.DataFrame({
            'date': pd.date_range('2023-01-01', periods=3),
            'type': ['steps', 'steps', 'heart_rate'],
            'value': [5000, 6000, 72]
        })
        
        data_loader.process_and_store(data)
        
        # Verify database methods were called
        mock_database.insert_data.assert_called()
        
    def test_batch_processing(self, data_loader):
        """Test batch processing of large datasets."""
        # Create large dataset
        large_data = pd.DataFrame({
            'date': pd.date_range('2023-01-01', periods=10000),
            'type': ['steps'] * 10000,
            'value': np.random.randint(0, 10000, 10000)
        })
        
        batches = list(data_loader.process_in_batches(large_data, batch_size=1000))
        
        assert len(batches) == 10
        assert all(len(batch) == 1000 for batch in batches)


class TestXMLStreamingProcessor:
    """Test XMLStreamingProcessor class."""
    
    def test_initialization(self, xml_processor):
        """Test XML processor initialization."""
        assert xml_processor.chunk_size > 0
        assert xml_processor.memory_threshold > 0
        
    def test_parse_health_record(self, xml_processor):
        """Test parsing a health record element."""
        xml_string = '''<Record type="HKQuantityTypeIdentifierStepCount" 
                                sourceName="iPhone" 
                                unit="count" 
                                creationDate="2023-01-01 10:00:00 +0000" 
                                startDate="2023-01-01 09:00:00 +0000" 
                                endDate="2023-01-01 10:00:00 +0000" 
                                value="1000"/>'''
        
        element = ET.fromstring(xml_string)
        record = xml_processor.parse_record(element)
        
        assert record['type'] == 'HKQuantityTypeIdentifierStepCount'
        assert record['value'] == 1000
        assert 'date' in record
        
    def test_stream_large_file(self, xml_processor):
        """Test streaming large XML file."""
        # Mock XML content
        xml_content = '''<?xml version="1.0" encoding="UTF-8"?>
        <HealthData>
            <Record type="HKQuantityTypeIdentifierStepCount" value="1000"/>
            <Record type="HKQuantityTypeIdentifierStepCount" value="2000"/>
            <Record type="HKQuantityTypeIdentifierHeartRate" value="72"/>
        </HealthData>'''
        
        with patch('builtins.open', mock_open(read_data=xml_content)):
            records = list(xml_processor.stream_process("test.xml"))
            
        assert len(records) >= 3
        
    def test_memory_monitoring(self, xml_processor):
        """Test memory monitoring during processing."""
        with patch('psutil.Process') as mock_process:
            mock_memory = Mock()
            mock_memory.rss = 100 * 1024 * 1024  # 100 MB
            mock_process.return_value.memory_info.return_value = mock_memory
            
            memory_usage = xml_processor.get_memory_usage()
            assert memory_usage > 0
            
    def test_error_handling(self, xml_processor):
        """Test error handling for invalid XML."""
        invalid_xml = '''<Invalid XML'''
        
        with patch('builtins.open', mock_open(read_data=invalid_xml)):
            with pytest.raises(Exception):
                list(xml_processor.stream_process("invalid.xml"))


class TestDataFilterEngine:
    """Test DataFilterEngine class."""
    
    def test_initialization(self, filter_engine):
        """Test filter engine initialization."""
        assert filter_engine.filters == {}
        
    def test_add_date_filter(self, filter_engine):
        """Test adding date filter."""
        start_date = date(2023, 1, 1)
        end_date = date(2023, 12, 31)
        
        filter_engine.add_date_filter(start_date, end_date)
        
        assert 'date' in filter_engine.filters
        assert filter_engine.filters['date']['start'] == start_date
        assert filter_engine.filters['date']['end'] == end_date
        
    def test_add_type_filter(self, filter_engine):
        """Test adding type filter."""
        types = ['steps', 'heart_rate']
        
        filter_engine.add_type_filter(types)
        
        assert 'type' in filter_engine.filters
        assert filter_engine.filters['type'] == types
        
    def test_add_value_filter(self, filter_engine):
        """Test adding value filter."""
        filter_engine.add_value_filter(min_value=1000, max_value=10000)
        
        assert 'value' in filter_engine.filters
        assert filter_engine.filters['value']['min'] == 1000
        assert filter_engine.filters['value']['max'] == 10000
        
    def test_apply_filters(self, filter_engine):
        """Test applying filters to data."""
        data = pd.DataFrame({
            'date': pd.date_range('2023-01-01', periods=10),
            'type': ['steps'] * 5 + ['heart_rate'] * 5,
            'value': range(1000, 11000, 1000)
        })
        
        # Add filters
        filter_engine.add_date_filter(date(2023, 1, 1), date(2023, 1, 5))
        filter_engine.add_type_filter(['steps'])
        filter_engine.add_value_filter(min_value=2000)
        
        filtered = filter_engine.apply(data)
        
        assert len(filtered) < len(data)
        assert all(filtered['type'] == 'steps')
        assert all(filtered['value'] >= 2000)
        
    def test_clear_filters(self, filter_engine):
        """Test clearing filters."""
        filter_engine.add_type_filter(['steps'])
        filter_engine.clear_filters()
        
        assert filter_engine.filters == {}
        
    def test_complex_filter_combination(self, filter_engine):
        """Test complex filter combinations."""
        data = pd.DataFrame({
            'date': pd.date_range('2023-01-01', periods=100),
            'type': ['steps', 'heart_rate', 'calories'] * 33 + ['steps'],
            'value': np.random.randint(0, 10000, 100),
            'source': ['iPhone'] * 50 + ['Apple Watch'] * 50
        })
        
        # Add multiple filters
        filter_engine.add_date_filter(date(2023, 1, 1), date(2023, 1, 31))
        filter_engine.add_type_filter(['steps', 'heart_rate'])
        filter_engine.add_value_filter(min_value=5000)
        filter_engine.add_custom_filter('source', lambda x: x == 'iPhone')
        
        filtered = filter_engine.apply(data)
        
        assert all(filtered['source'] == 'iPhone')
        assert all(filtered['value'] >= 5000)
        assert all(filtered['type'].isin(['steps', 'heart_rate']))


class TestDataAvailabilityService:
    """Test DataAvailabilityService class."""
    
    def test_initialization(self, availability_service, mock_database):
        """Test availability service initialization."""
        assert availability_service.database == mock_database
        assert availability_service._cache is not None
        
    def test_get_available_metrics(self, availability_service, mock_database):
        """Test getting available metrics."""
        mock_database.get_available_types.return_value = ['steps', 'heart_rate', 'calories']
        
        metrics = availability_service.get_available_metrics()
        
        assert len(metrics) == 3
        assert 'steps' in metrics
        
    def test_get_date_range(self, availability_service, mock_database):
        """Test getting date range for metric."""
        mock_database.execute_query.return_value = pd.DataFrame({
            'min_date': [datetime(2023, 1, 1)],
            'max_date': [datetime(2023, 12, 31)]
        })
        
        start, end = availability_service.get_date_range('steps')
        
        assert start == date(2023, 1, 1)
        assert end == date(2023, 12, 31)
        
    def test_get_data_density(self, availability_service, mock_database):
        """Test getting data density."""
        mock_database.execute_query.return_value = pd.DataFrame({
            'date': pd.date_range('2023-01-01', periods=30),
            'count': np.random.randint(1, 100, 30)
        })
        
        density = availability_service.get_data_density('steps', date(2023, 1, 1), date(2023, 1, 31))
        
        assert len(density) == 30
        assert all(density['count'] > 0)
        
    def test_check_data_quality(self, availability_service, mock_database):
        """Test checking data quality."""
        mock_database.execute_query.return_value = pd.DataFrame({
            'total_records': [10000],
            'missing_values': [100],
            'duplicate_records': [50]
        })
        
        quality = availability_service.check_data_quality('steps')
        
        assert 'total_records' in quality
        assert 'missing_rate' in quality
        assert 'duplicate_rate' in quality
        
    def test_cache_functionality(self, availability_service, mock_database):
        """Test caching functionality."""
        # First call
        mock_database.get_available_types.return_value = ['steps']
        metrics1 = availability_service.get_available_metrics()
        
        # Second call should use cache
        metrics2 = availability_service.get_available_metrics()
        
        # Database should only be called once
        assert mock_database.get_available_types.call_count == 1
        assert metrics1 == metrics2


class TestDataIntegration:
    """Test integration between data loading components."""
    
    def test_load_filter_process_pipeline(self, data_loader, filter_engine, mock_database):
        """Test complete data pipeline."""
        # Mock data
        raw_data = pd.DataFrame({
            'date': pd.date_range('2023-01-01', periods=100),
            'type': ['steps'] * 50 + ['heart_rate'] * 50,
            'value': np.random.randint(0, 10000, 100)
        })
        
        # Apply filters
        filter_engine.add_type_filter(['steps'])
        filter_engine.add_value_filter(min_value=5000)
        
        filtered_data = filter_engine.apply(raw_data)
        
        # Process and store
        data_loader.process_and_store(filtered_data)
        
        # Verify data was processed correctly
        assert mock_database.insert_data.called
        call_args = mock_database.insert_data.call_args[0][0]
        assert all(call_args['type'] == 'steps')
        assert all(call_args['value'] >= 5000)