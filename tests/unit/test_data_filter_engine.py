"""
Unit tests for the Data Filter Engine using BaseDataProcessingTest patterns.
"""

import pytest
import pandas as pd
from datetime import date, datetime, timedelta
import sqlite3
import tempfile
import os
from pathlib import Path

from tests.base_test_classes import BaseDataProcessingTest, ParametrizedCalculatorTests
from src.data_filter_engine import DataFilterEngine, FilterCriteria, QueryBuilder
from src.database import DatabaseManager


class TestQueryBuilder(BaseDataProcessingTest):
    """Test the QueryBuilder class."""
    
    def get_processor_class(self):
        """Return QueryBuilder class for base test compatibility."""
        class QueryBuilderProcessor:
            def process(self, data):
                builder = QueryBuilder()
                if not data:
                    return {"query": "SELECT * FROM health_records ORDER BY creationDate DESC", "params": []}
                return {"processed": True, "builder": builder}
        return QueryBuilderProcessor
    
    def test_empty_query(self):
        """Test building a query with no filters."""
        builder = QueryBuilder()
        query, params = builder.build()
        
        assert query == "SELECT * FROM health_records ORDER BY creationDate DESC"
        assert params == []
    
    @pytest.mark.parametrize("start_date,end_date,expected_condition,expected_param_count", [
        (date(2024, 1, 1), date(2024, 12, 31), "BETWEEN ? AND ?", 2),
        (date(2024, 1, 1), None, "creationDate >= ?", 1),
        (None, date(2024, 12, 31), "creationDate <= ?", 1),
    ])
    def test_date_range_filters_parametrized(self, start_date, end_date, expected_condition, expected_param_count):
        """Parametrized test for date range filtering."""
        builder = QueryBuilder()
        builder.add_date_range(start_date, end_date)
        query, params = builder.build()
        
        assert expected_condition in query
        assert len(params) == expected_param_count
        
        if start_date:
            assert any(param.startswith("2024-01-01") for param in params)
        if end_date:
            assert any(param.startswith("2024-12-31") for param in params)
    
    @pytest.mark.parametrize("filter_values,filter_method,expected_placeholders", [
        (["iPhone", "Apple Watch"], "add_source_filter", "sourceName IN (?,?)"),
        (["StepCount", "HeartRate"], "add_type_filter", "type IN (?,?)"),
        (["StepCount"], "add_type_filter", "type IN (?)"),
        (["iPhone"], "add_source_filter", "sourceName IN (?)"),
    ])
    def test_list_filters_parametrized(self, filter_values, filter_method, expected_placeholders):
        """Parametrized test for source and type filtering."""
        builder = QueryBuilder()
        method = getattr(builder, filter_method)
        method(filter_values)
        query, params = builder.build()
        
        assert expected_placeholders in query
        assert params == filter_values
    
    def test_combined_filters(self):
        """Test combining multiple filters."""
        builder = QueryBuilder()
        start_date = date(2024, 1, 1)
        end_date = date(2024, 12, 31)
        sources = ["iPhone"]
        types = ["StepCount"]
        
        builder.add_date_range(start_date, end_date)
        builder.add_source_filter(sources)
        builder.add_type_filter(types)
        
        query, params = builder.build()
        
        assert "WHERE" in query
        assert "AND" in query
        assert "creationDate BETWEEN ? AND ?" in query
        assert "sourceName IN (?)" in query
        assert "type IN (?)" in query
        assert len(params) == 4
    
    def test_query_with_limit(self):
        """Test query with limit."""
        builder = QueryBuilder()
        query, params = builder.build(limit=100)
        
        assert "LIMIT 100" in query


class TestDataFilterEngine(BaseDataProcessingTest):
    """Test the DataFilterEngine class using BaseDataProcessingTest patterns."""
    
    def get_processor_class(self):
        """Return DataFilterEngine class for base test compatibility."""
        class FilterEngineProcessor:
            def __init__(self, db_path=None):
                self.db_path = db_path or ":memory:"
            
            def process(self, data):
                if not data:
                    return pd.DataFrame()
                # Mock processing for base test compatibility
                return {"processed": True, "record_count": len(data)}
        
        return FilterEngineProcessor
    
    @pytest.fixture
    def temp_db(self):
        """Create a temporary database with test data."""
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
        db_path = temp_file.name
        temp_file.close()
        
        # Create test database
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Create health_records table
        cursor.execute("""
            CREATE TABLE health_records (
                id INTEGER PRIMARY KEY,
                creationDate TEXT,
                startDate TEXT,
                endDate TEXT,
                type TEXT,
                sourceName TEXT,
                value REAL,
                unit TEXT
            )
        """)
        
        # Insert test data
        test_data = []
        base_date = datetime(2024, 1, 1)
        
        # Add StepCount data
        for i in range(30):
            date_str = (base_date + timedelta(days=i)).isoformat()
            test_data.append((
                date_str, date_str, date_str,
                "StepCount", "iPhone", 5000 + i * 100, "count"
            ))
        
        # Add HeartRate data
        for i in range(20):
            date_str = (base_date + timedelta(days=i)).isoformat()
            test_data.append((
                date_str, date_str, date_str,
                "HeartRate", "Apple Watch", 60 + i, "count/min"
            ))
        
        # Add different source data
        for i in range(10):
            date_str = (base_date + timedelta(days=i+30)).isoformat()
            test_data.append((
                date_str, date_str, date_str,
                "ActiveEnergyBurned", "Fitness App", 200 + i * 10, "kcal"
            ))
        
        cursor.executemany("""
            INSERT INTO health_records 
            (creationDate, startDate, endDate, type, sourceName, value, unit)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, test_data)
        
        # Create indexes
        cursor.execute("CREATE INDEX idx_creation_date ON health_records(creationDate)")
        cursor.execute("CREATE INDEX idx_type ON health_records(type)")
        
        conn.commit()
        conn.close()
        
        yield db_path
        
        # Cleanup - ensure all connections are closed first
        try:
            # Force garbage collection to close any lingering connections
            import gc
            gc.collect()
            
            # Try to remove the file, retry if locked
            import time
            for attempt in range(5):
                try:
                    os.unlink(db_path)
                    break
                except PermissionError:
                    if attempt < 4:
                        time.sleep(0.1)
                        continue
                    else:
                        # If still locked after retries, just leave it for OS cleanup
                        pass
        except FileNotFoundError:
            # File already deleted, that's fine
            pass
    
    def test_filter_all_data(self, temp_db):
        """Test filtering without any criteria (return all data)."""
        engine = DataFilterEngine(db_path=temp_db)
        criteria = FilterCriteria()
        
        result = engine.filter_data(criteria)
        
        assert isinstance(result, pd.DataFrame)
        assert len(result) == 60  # Total records inserted
    
    def test_filter_by_date_range(self, temp_db):
        """Test filtering by date range."""
        engine = DataFilterEngine(db_path=temp_db)
        criteria = FilterCriteria(
            start_date=date(2024, 1, 1),
            end_date=date(2024, 1, 15)
        )
        
        result = engine.filter_data(criteria)
        
        assert isinstance(result, pd.DataFrame)
        assert len(result) == 30  # 15 days of StepCount + 15 days of HeartRate
        assert all(result['creationDate'] >= pd.Timestamp('2024-01-01'))
        assert all(result['creationDate'] <= pd.Timestamp('2024-01-15 23:59:59'))
    
    @pytest.mark.parametrize("filter_criteria,expected_count,field_to_check", [
        ({"source_names": ["iPhone"]}, 30, "sourceName"),
        ({"source_names": ["iPhone", "Apple Watch"]}, 50, "sourceName"),
        ({"health_types": ["StepCount"]}, 30, "type"),
        ({"health_types": ["StepCount", "HeartRate"]}, 50, "type"),
    ])
    def test_filter_by_criteria_parametrized(self, temp_db, filter_criteria, expected_count, field_to_check):
        """Parametrized test for filtering by different criteria."""
        engine = DataFilterEngine(db_path=temp_db)
        criteria = FilterCriteria(**filter_criteria)
        
        result = engine.filter_data(criteria)
        
        assert isinstance(result, pd.DataFrame)
        assert len(result) == expected_count
        
        # Verify filter was applied correctly
        if "source_names" in filter_criteria:
            expected_values = set(filter_criteria["source_names"])
            actual_values = set(result[field_to_check].unique())
            assert actual_values.issubset(expected_values)
        
        if "health_types" in filter_criteria:
            expected_values = set(filter_criteria["health_types"])
            actual_values = set(result[field_to_check].unique())
            assert actual_values.issubset(expected_values)
    
    def test_combined_filters(self, temp_db):
        """Test combining multiple filter criteria."""
        engine = DataFilterEngine(db_path=temp_db)
        criteria = FilterCriteria(
            start_date=date(2024, 1, 1),
            end_date=date(2024, 1, 10),
            source_names=["iPhone"],
            health_types=["StepCount"]
        )
        
        result = engine.filter_data(criteria)
        
        assert len(result) == 10  # 10 days of iPhone StepCount data
        assert all(result['sourceName'] == "iPhone")
        assert all(result['type'] == "StepCount")
        assert all(result['creationDate'] >= pd.Timestamp('2024-01-01'))
        assert all(result['creationDate'] <= pd.Timestamp('2024-01-10 23:59:59'))
    
    def test_filter_with_limit(self, temp_db):
        """Test filtering with result limit."""
        engine = DataFilterEngine(db_path=temp_db)
        criteria = FilterCriteria()
        
        result = engine.filter_data(criteria, limit=10)
        
        assert len(result) == 10
    
    def test_get_distinct_sources(self, temp_db):
        """Test getting distinct source names."""
        engine = DataFilterEngine(db_path=temp_db)
        sources = engine.get_distinct_sources()
        
        assert set(sources) == {"Apple Watch", "Fitness App", "iPhone"}
        assert sources == sorted(sources)  # Should be sorted
    
    def test_get_distinct_types(self, temp_db):
        """Test getting distinct health types."""
        engine = DataFilterEngine(db_path=temp_db)
        types = engine.get_distinct_types()
        
        assert set(types) == {"ActiveEnergyBurned", "HeartRate", "StepCount"}
        assert types == sorted(types)  # Should be sorted
    
    def test_get_data_date_range(self, temp_db):
        """Test getting min/max dates from database."""
        engine = DataFilterEngine(db_path=temp_db)
        min_date, max_date = engine.get_data_date_range()
        
        assert min_date == date(2024, 1, 1)
        assert max_date == date(2024, 2, 9)  # 30 days + 10 days from Jan 31
    
    def test_performance_metrics(self, temp_db):
        """Test performance metrics tracking."""
        engine = DataFilterEngine(db_path=temp_db)
        
        # Initial metrics
        metrics = engine.get_performance_metrics()
        assert metrics['total_queries'] == 0
        assert metrics['average_query_time'] == 0
        
        # Run a query
        criteria = FilterCriteria()
        engine.filter_data(criteria)
        
        # Check updated metrics
        metrics = engine.get_performance_metrics()
        assert metrics['total_queries'] == 1
        assert metrics['last_query_time'] >= 0  # Can be 0 on very fast systems
        assert metrics['average_query_time'] >= 0  # Can be 0 on very fast systems
        
        # Run another query
        engine.filter_data(criteria)
        
        metrics = engine.get_performance_metrics()
        assert metrics['total_queries'] == 2
    
    def test_empty_filter_results(self, temp_db):
        """Test handling of filters that return no results."""
        engine = DataFilterEngine(db_path=temp_db)
        criteria = FilterCriteria(
            health_types=["NonExistentType"]
        )
        
        result = engine.filter_data(criteria)
        
        assert isinstance(result, pd.DataFrame)
        assert len(result) == 0
        assert list(result.columns) == ['creationDate', 'type', 'value', 'sourceName']
    
    def test_performance_threshold(self, temp_db):
        """Test that queries complete within performance threshold."""
        engine = DataFilterEngine(db_path=temp_db)
        criteria = FilterCriteria(
            start_date=date(2024, 1, 1),
            end_date=date(2024, 1, 31),
            source_names=["iPhone", "Apple Watch"],
            health_types=["StepCount", "HeartRate"]
        )
        
        # Run the query
        result = engine.filter_data(criteria)
        
        # Check performance
        metrics = engine.get_performance_metrics()
        assert metrics['last_query_time'] < 200  # Should be under 200ms
    
    def test_optimize_for_filters(self, temp_db):
        """Test filter optimization suggestions."""
        engine = DataFilterEngine(db_path=temp_db)
        criteria = FilterCriteria(
            start_date=date(2024, 1, 1),
            source_names=["iPhone"],
            health_types=["StepCount"]
        )
        
        suggestions = engine.optimize_for_filters(criteria)
        
        assert isinstance(suggestions, list)
        assert len(suggestions) > 0
        assert any("optimized" in s.lower() for s in suggestions)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])