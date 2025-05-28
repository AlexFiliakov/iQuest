"""Unit tests for the statistics calculator."""

import pytest
import pandas as pd
from datetime import datetime
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'src'))

from statistics_calculator import BasicStatistics, StatisticsCalculator


class TestBasicStatistics:
    """Test the BasicStatistics dataclass."""
    
    def test_basic_statistics_creation(self):
        """Test creating a BasicStatistics object."""
        stats = BasicStatistics(
            total_records=100,
            date_range=(datetime(2024, 1, 1), datetime(2024, 12, 31)),
            records_by_type={'HeartRate': 50, 'Steps': 50},
            records_by_source={'iPhone': 60, 'Apple Watch': 40},
            types_by_source={'iPhone': ['Steps'], 'Apple Watch': ['HeartRate', 'Steps']}
        )
        
        assert stats.total_records == 100
        assert stats.date_range[0] == datetime(2024, 1, 1)
        assert stats.date_range[1] == datetime(2024, 12, 31)
        assert stats.records_by_type['HeartRate'] == 50
        assert stats.records_by_source['iPhone'] == 60
        assert 'HeartRate' in stats.types_by_source['Apple Watch']
    
    def test_to_dict(self):
        """Test converting BasicStatistics to dictionary."""
        stats = BasicStatistics(
            total_records=10,
            date_range=(datetime(2024, 1, 1), datetime(2024, 1, 31)),
            records_by_type={'HeartRate': 10},
            records_by_source={'iPhone': 10},
            types_by_source={'iPhone': ['HeartRate']}
        )
        
        result = stats.to_dict()
        
        assert result['total_records'] == 10
        assert result['date_range']['start'] == '2024-01-01T00:00:00'
        assert result['date_range']['end'] == '2024-01-31T00:00:00'
        assert result['records_by_type']['HeartRate'] == 10
        assert result['records_by_source']['iPhone'] == 10
        assert result['types_by_source']['iPhone'] == ['HeartRate']
    
    def test_to_dict_with_none_dates(self):
        """Test to_dict with None date values."""
        stats = BasicStatistics(
            total_records=0,
            date_range=(None, None),
            records_by_type={},
            records_by_source={},
            types_by_source={}
        )
        
        result = stats.to_dict()
        
        assert result['date_range']['start'] is None
        assert result['date_range']['end'] is None


class TestStatisticsCalculator:
    """Test the StatisticsCalculator class."""
    
    @pytest.fixture
    def sample_dataframe(self):
        """Create a sample DataFrame for testing."""
        data = {
            'creationDate': [
                '2024-01-01 10:00:00',
                '2024-01-02 11:00:00',
                '2024-01-03 12:00:00',
                '2024-01-04 13:00:00',
                '2024-01-05 14:00:00'
            ],
            'type': ['HeartRate', 'Steps', 'HeartRate', 'Steps', 'Sleep'],
            'sourceName': ['Apple Watch', 'iPhone', 'Apple Watch', 'iPhone', 'iPhone'],
            'value': [70, 5000, 75, 6000, 8.5],
            'unit': ['bpm', 'count', 'bpm', 'count', 'hr']
        }
        return pd.DataFrame(data)
    
    @pytest.fixture
    def calculator(self):
        """Create a StatisticsCalculator instance."""
        return StatisticsCalculator()
    
    def test_calculate_from_empty_dataframe(self, calculator):
        """Test calculating statistics from empty DataFrame."""
        df = pd.DataFrame()
        stats = calculator.calculate_from_dataframe(df)
        
        assert stats.total_records == 0
        assert stats.date_range == (None, None)
        assert stats.records_by_type == {}
        assert stats.records_by_source == {}
        assert stats.types_by_source == {}
    
    def test_calculate_from_dataframe(self, calculator, sample_dataframe):
        """Test calculating statistics from a sample DataFrame."""
        stats = calculator.calculate_from_dataframe(sample_dataframe)
        
        # Check total records
        assert stats.total_records == 5
        
        # Check date range
        assert stats.date_range[0].strftime('%Y-%m-%d') == '2024-01-01'
        assert stats.date_range[1].strftime('%Y-%m-%d') == '2024-01-05'
        
        # Check records by type
        assert stats.records_by_type['HeartRate'] == 2
        assert stats.records_by_type['Steps'] == 2
        assert stats.records_by_type['Sleep'] == 1
        
        # Check records by source
        assert stats.records_by_source['Apple Watch'] == 2
        assert stats.records_by_source['iPhone'] == 3
        
        # Check types by source
        assert set(stats.types_by_source['Apple Watch']) == {'HeartRate'}
        assert set(stats.types_by_source['iPhone']) == {'Steps', 'Sleep'}
    
    def test_types_by_source_sorted(self, calculator, sample_dataframe):
        """Test that types within each source are sorted."""
        stats = calculator.calculate_from_dataframe(sample_dataframe)
        
        # iPhone has Sleep and Steps - should be sorted alphabetically
        assert stats.types_by_source['iPhone'] == ['Sleep', 'Steps']
    
    def test_get_quick_summary(self, calculator, sample_dataframe):
        """Test generating a quick summary."""
        stats = calculator.calculate_from_dataframe(sample_dataframe)
        summary = calculator.get_quick_summary(stats)
        
        # Check that summary contains expected information
        assert "Total Records: 5" in summary
        assert "Date Range: 2024-01-01 to 2024-01-05" in summary
        assert "HeartRate: 2" in summary
        assert "Steps: 2" in summary
        assert "Sleep: 1" in summary
        assert "Apple Watch: 2 records" in summary
        assert "iPhone: 3 records" in summary
        assert "Data Sources (2):" in summary
    
    def test_get_quick_summary_empty(self, calculator):
        """Test generating summary for empty data."""
        stats = BasicStatistics(
            total_records=0,
            date_range=(None, None),
            records_by_type={},
            records_by_source={},
            types_by_source={}
        )
        summary = calculator.get_quick_summary(stats)
        
        assert summary == "No health records found."
    
    def test_large_dataset_top_5_types(self, calculator):
        """Test that only top 5 types are shown in summary."""
        # Create DataFrame with many types
        data = {
            'creationDate': ['2024-01-01'] * 10,
            'type': ['Type1', 'Type2', 'Type3', 'Type4', 'Type5', 
                    'Type6', 'Type7', 'Type8', 'Type9', 'Type10'],
            'sourceName': ['iPhone'] * 10,
            'value': [1] * 10,
            'unit': ['count'] * 10
        }
        df = pd.DataFrame(data)
        
        stats = calculator.calculate_from_dataframe(df)
        summary = calculator.get_quick_summary(stats)
        
        # Check that only 5 types are shown
        type_lines = [line for line in summary.split('\n') if line.strip().startswith('- Type')]
        assert len(type_lines) == 5
    
    def test_calculate_from_database_no_loader(self, calculator):
        """Test that calculate_from_database raises error without data_loader."""
        with pytest.raises(ValueError, match="DataLoader not provided"):
            calculator.calculate_from_database()
    
    def test_date_parsing(self, calculator):
        """Test that various date formats are handled correctly."""
        data = {
            'creationDate': [
                '2024-01-01T10:00:00Z',
                '2024-01-02 11:00:00',
                '2024-01-03'
            ],
            'type': ['HeartRate'] * 3,
            'sourceName': ['iPhone'] * 3,
            'value': [70] * 3,
            'unit': ['bpm'] * 3
        }
        df = pd.DataFrame(data)
        
        stats = calculator.calculate_from_dataframe(df)
        
        # Should successfully parse all date formats
        assert stats.total_records == 3
        assert stats.date_range[0].strftime('%Y-%m-%d') == '2024-01-01'
        assert stats.date_range[1].strftime('%Y-%m-%d') == '2024-01-03'