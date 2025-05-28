"""
Unit tests for the Data Filter Engine
"""

import pytest
import pandas as pd
from datetime import date, datetime, timedelta
import sqlite3
import tempfile
import os
from pathlib import Path

from src.data_filter_engine import DataFilterEngine, FilterCriteria, QueryBuilder
from src.database import DatabaseManager


class TestQueryBuilder:
    """Test the QueryBuilder class."""
    
    def test_empty_query(self):
        """Test building a query with no filters."""
        builder = QueryBuilder()
        query, params = builder.build()
        
        assert query == "SELECT * FROM health_records ORDER BY creationDate DESC"
        assert params == []
    
    def test_date_range_filter(self):
        """Test date range filtering."""
        builder = QueryBuilder()
        start_date = date(2024, 1, 1)
        end_date = date(2024, 12, 31)
        
        builder.add_date_range(start_date, end_date)
        query, params = builder.build()
        
        assert "creationDate BETWEEN ? AND ?" in query
        assert len(params) == 2
        assert params[0].startswith("2024-01-01")
        assert params[1].startswith("2024-12-31")
    
    def test_start_date_only(self):
        """Test filtering with only start date."""
        builder = QueryBuilder()
        start_date = date(2024, 1, 1)
        
        builder.add_date_range(start_date, None)
        query, params = builder.build()
        
        assert "creationDate >= ?" in query
        assert len(params) == 1
        assert params[0].startswith("2024-01-01")
    
    def test_end_date_only(self):
        """Test filtering with only end date."""
        builder = QueryBuilder()
        end_date = date(2024, 12, 31)
        
        builder.add_date_range(None, end_date)
        query, params = builder.build()
        
        assert "creationDate <= ?" in query
        assert len(params) == 1
        assert params[0].startswith("2024-12-31")
    
    def test_source_filter(self):
        """Test source name filtering."""
        builder = QueryBuilder()
        sources = ["iPhone", "Apple Watch"]
        
        builder.add_source_filter(sources)
        query, params = builder.build()
        
        assert "sourceName IN (?,?)" in query
        assert params == ["iPhone", "Apple Watch"]
    
    def test_type_filter(self):
        """Test health type filtering."""
        builder = QueryBuilder()
        types = ["StepCount", "HeartRate", "DistanceWalkingRunning"]
        
        builder.add_type_filter(types)
        query, params = builder.build()
        
        assert "type IN (?,?,?)" in query
        assert params == ["StepCount", "HeartRate", "DistanceWalkingRunning"]
    
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


class TestDataFilterEngine:
    """Test the DataFilterEngine class."""
    
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
    
    def test_filter_by_source(self, temp_db):
        """Test filtering by source name."""
        engine = DataFilterEngine(db_path=temp_db)
        criteria = FilterCriteria(source_names=["iPhone"])
        
        result = engine.filter_data(criteria)
        
        assert len(result) == 30  # Only iPhone records
        assert all(result['sourceName'] == "iPhone")
    
    def test_filter_by_multiple_sources(self, temp_db):
        """Test filtering by multiple source names."""
        engine = DataFilterEngine(db_path=temp_db)
        criteria = FilterCriteria(source_names=["iPhone", "Apple Watch"])
        
        result = engine.filter_data(criteria)
        
        assert len(result) == 50  # iPhone + Apple Watch records
        assert set(result['sourceName'].unique()) == {"iPhone", "Apple Watch"}
    
    def test_filter_by_type(self, temp_db):
        """Test filtering by health type."""
        engine = DataFilterEngine(db_path=temp_db)
        criteria = FilterCriteria(health_types=["StepCount"])
        
        result = engine.filter_data(criteria)
        
        assert len(result) == 30  # Only StepCount records
        assert all(result['type'] == "StepCount")
    
    def test_filter_by_multiple_types(self, temp_db):
        """Test filtering by multiple health types."""
        engine = DataFilterEngine(db_path=temp_db)
        criteria = FilterCriteria(health_types=["StepCount", "HeartRate"])
        
        result = engine.filter_data(criteria)
        
        assert len(result) == 50  # StepCount + HeartRate records
        assert set(result['type'].unique()) == {"StepCount", "HeartRate"}
    
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