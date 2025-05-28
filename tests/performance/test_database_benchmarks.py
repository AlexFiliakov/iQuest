"""
Database performance benchmarks.

Tests for database operations including bulk inserts, queries, and indexing.
"""

import pytest
import pandas as pd
import sqlite3
from pathlib import Path
from tests.performance.benchmark_base import PerformanceBenchmark
from tests.performance.adaptive_thresholds import AdaptiveThresholds
from tests.generators.health_data import HealthDataGenerator


@pytest.mark.performance
class TestDatabasePerformance(PerformanceBenchmark):
    """Performance tests for database operations."""
    
    def setup_method(self):
        """Set up test environment."""
        super().__init__()
        self.thresholds = AdaptiveThresholds()
        
    @pytest.fixture
    def data_generator(self):
        """Create data generator."""
        return HealthDataGenerator(seed=42)
    
    @pytest.fixture
    def small_dataset(self, data_generator):
        """Generate small dataset (30 days)."""
        return data_generator.generate_dataframe(days=30, records_per_day=100)
    
    @pytest.fixture  
    def medium_dataset(self, data_generator):
        """Generate medium dataset (365 days)."""
        return data_generator.generate_dataframe(days=365, records_per_day=100)
        
    @pytest.fixture
    def large_dataset(self, data_generator):
        """Generate large dataset (5 years)."""
        return data_generator.generate_dataframe(days=1825, records_per_day=100)
    
    @pytest.fixture
    def temp_db(self, tmp_path):
        """Create temporary database."""
        db_path = tmp_path / "test.db"
        return str(db_path)
        
    def test_bulk_insert_performance(self, benchmark, medium_dataset, temp_db):
        """Test bulk insert performance."""
        from src.health_database import HealthDatabase
        
        def bulk_insert():
            db = HealthDatabase(temp_db)
            db.bulk_insert_records(medium_dataset)
            db.close()
            
        # Use pytest-benchmark
        result = benchmark.pedantic(
            bulk_insert,
            rounds=5,
            warmup_rounds=2
        )
        
        # Custom assertions with adaptive thresholds
        max_time = self.thresholds.get_threshold(
            'database_bulk_insert', 
            'duration',
            margin=1.5  # 50% margin for database operations
        )
        
        assert result['mean'] < max_time
        assert result['stddev'] < 0.5  # Consistent performance
        
    def test_indexed_query_performance(self, benchmark, temp_db):
        """Test performance of indexed queries."""
        from src.health_database import HealthDatabase
        
        # Setup: Create and populate database
        db = HealthDatabase(temp_db)
        generator = HealthDataGenerator(seed=42)
        data = generator.generate_dataframe(days=365, records_per_day=100)
        db.bulk_insert_records(data)
        
        def indexed_query():
            return db.query_date_range(
                start_date='2023-01-01',
                end_date='2023-12-31',
                metric_types=['steps', 'heart_rate']
            )
        
        # Benchmark the query
        result = benchmark.pedantic(
            indexed_query,
            rounds=10,
            warmup_rounds=3
        )
        
        # Clean up
        db.close()
        
        # Assertions
        assert result['mean'] < 0.1  # <100ms for indexed query
        assert result['stddev'] < 0.02  # Low variance
        
    def test_aggregation_query_performance(self, benchmark, temp_db):
        """Test performance of aggregation queries."""
        from src.health_database import HealthDatabase
        
        # Setup database with data
        db = HealthDatabase(temp_db)
        generator = HealthDataGenerator(seed=42)
        data = generator.generate_dataframe(days=730, records_per_day=100)  # 2 years
        db.bulk_insert_records(data)
        
        def aggregation_query():
            return db.execute_query("""
                SELECT 
                    date(timestamp) as date,
                    metric_type,
                    AVG(value) as avg_value,
                    MIN(value) as min_value,
                    MAX(value) as max_value,
                    COUNT(*) as count
                FROM health_records
                WHERE metric_type IN ('steps', 'heart_rate', 'sleep_hours')
                GROUP BY date(timestamp), metric_type
                ORDER BY date DESC
            """)
        
        # Benchmark
        result = benchmark(aggregation_query)
        
        db.close()
        
        # Performance assertions
        assert result.stats['mean'] < 0.5  # <500ms for 2 years aggregation
        
    def test_concurrent_read_performance(self, benchmark, temp_db):
        """Test performance under concurrent reads."""
        from src.health_database import HealthDatabase
        import concurrent.futures
        
        # Setup
        db = HealthDatabase(temp_db)
        generator = HealthDataGenerator(seed=42)
        data = generator.generate_dataframe(days=180, records_per_day=100)
        db.bulk_insert_records(data)
        db.close()
        
        def concurrent_reads():
            """Simulate multiple concurrent database reads."""
            def read_operation(thread_id):
                thread_db = HealthDatabase(temp_db)
                result = thread_db.query_date_range(
                    start_date='2023-06-01',
                    end_date='2023-06-30'
                )
                thread_db.close()
                return len(result)
            
            with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
                futures = [executor.submit(read_operation, i) for i in range(10)]
                results = [f.result() for f in concurrent.futures.as_completed(futures)]
                
            return results
        
        # Benchmark concurrent operations
        result = benchmark(concurrent_reads)
        
        # Should handle concurrent reads efficiently
        assert result.stats['mean'] < 2.0  # <2s for 10 concurrent operations
        
    @pytest.mark.slow
    def test_large_dataset_memory_efficiency(self, large_dataset, temp_db):
        """Test memory efficiency with large datasets."""
        from src.health_database import HealthDatabase
        import tracemalloc
        
        tracemalloc.start()
        
        # Perform database operations
        db = HealthDatabase(temp_db)
        db.bulk_insert_records(large_dataset)
        
        # Get memory usage
        current, peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()
        
        db.close()
        
        # Convert to MB
        peak_mb = peak / 1024 / 1024
        
        # Should use reasonable memory even for large datasets
        assert peak_mb < 500  # Less than 500MB for 5 years of data
        
    def test_transaction_performance(self, benchmark, medium_dataset, temp_db):
        """Test transaction commit performance."""
        from src.health_database import HealthDatabase
        
        def transaction_test():
            db = HealthDatabase(temp_db)
            
            # Test transaction performance
            with db.transaction():
                # Insert records in batches
                batch_size = 1000
                for i in range(0, len(medium_dataset), batch_size):
                    batch = medium_dataset.iloc[i:i+batch_size]
                    db.insert_batch(batch)
                    
            db.close()
        
        # Benchmark transaction performance
        result = benchmark(transaction_test)
        
        # Transactions should be efficient
        assert result.stats['mean'] < 3.0  # <3s for full year with transactions
        
    def test_index_creation_performance(self, benchmark, temp_db):
        """Test index creation performance."""
        from src.health_database import HealthDatabase
        
        # Setup: Create database with data but no indexes
        db = HealthDatabase(temp_db, create_indexes=False)
        generator = HealthDataGenerator(seed=42)
        data = generator.generate_dataframe(days=365, records_per_day=100)
        db.bulk_insert_records(data)
        
        def create_indexes():
            db.create_indexes()
            
        # Benchmark index creation
        result = benchmark(create_indexes)
        
        db.close()
        
        # Index creation should be reasonably fast
        assert result.stats['mean'] < 5.0  # <5s to create all indexes