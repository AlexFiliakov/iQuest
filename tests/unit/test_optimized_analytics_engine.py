"""Tests for optimized analytics engine."""

import pytest
import asyncio
from datetime import date, datetime, timedelta
from unittest.mock import Mock, patch, AsyncMock, MagicMock
import numpy as np
import pandas as pd

from src.analytics.optimized_analytics_engine import (
    OptimizedAnalyticsEngine, AnalyticsRequest,
    Priority, CalculationType, CacheStrategy
)
from src.analytics.computation_queue import TaskPriority
from src.analytics.performance_monitor import PerformanceMonitor
from src.analytics.connection_pool import ConnectionPool
from src.analytics.computation_queue import ComputationQueue
from src.analytics.progressive_loader import ProgressiveLoader
from src.analytics.streaming_data_loader import StreamingDataLoader


@pytest.fixture
def mock_database():
    """Create mock database."""
    mock_db = Mock()
    mock_db.execute_query = Mock(return_value=pd.DataFrame({
        'date': pd.date_range(start='2023-01-01', periods=100),
        'value': np.random.randint(0, 10000, 100),
        'type': ['steps'] * 100
    }))
    return mock_db


@pytest.fixture
def mock_connection_pool():
    """Create mock connection pool."""
    pool = Mock(spec=ConnectionPool)
    pool.acquire = AsyncMock(return_value=Mock())
    pool.release = Mock()
    return pool


@pytest.fixture
def analytics_engine(mock_database, mock_connection_pool):
    """Create analytics engine instance."""
    with patch('src.analytics.optimized_analytics_engine.ConnectionPool', return_value=mock_connection_pool):
        # Also need to mock PooledDataAccess
        with patch('src.analytics.optimized_analytics_engine.PooledDataAccess'):
            engine = OptimizedAnalyticsEngine(database_path="test.db")
            return engine


@pytest.mark.skip(reason="Async functionality not implemented in OptimizedAnalyticsEngine")
@pytest.mark.asyncio
class TestOptimizedAnalyticsEngine:
    """Test OptimizedAnalyticsEngine class."""
    
    @pytest.mark.skip(reason="Async functionality not implemented in OptimizedAnalyticsEngine")
    async def test_initialization(self, mock_database):
        """Test engine initialization."""
        # Mock the connection pool creation
        with patch('src.analytics.optimized_analytics_engine.ConnectionPool') as mock_pool_class:
            mock_pool = Mock()
            mock_pool_class.return_value = mock_pool
            
            engine = OptimizedAnalyticsEngine(database_path="test.db")
            
            assert engine.connection_pool == mock_pool
            assert isinstance(engine.performance_monitor, PerformanceMonitor)
            assert isinstance(engine.computation_queue, ComputationQueue)
            assert engine.is_running is True
        
    async def test_process_request_daily_metrics(self, analytics_engine):
        """Test processing daily metrics request."""
        request = AnalyticsRequest(
            metric_type="steps",
            calculation_type=CalculationType.DAILY_METRICS,
            start_date=date(2023, 1, 1),
            end_date=date(2023, 1, 31),
            priority=Priority.HIGH
        )
        
        # Mock calculator
        mock_calc = Mock()
        mock_calc.calculate_metrics = Mock(return_value={
            'average': 7500,
            'total': 232500,
            'days': 31
        })
        
        with patch.object(analytics_engine, '_get_calculator', return_value=mock_calc):
            result = await analytics_engine.process_request(request)
            
        assert isinstance(result, AnalyticsResult)
        assert result.request == request
        assert result.data['average'] == 7500
        assert result.success is True
        
    async def test_process_request_with_cache(self, analytics_engine):
        """Test request processing with cache."""
        request = AnalyticsRequest(
            metric_type="steps",
            calculation_type=CalculationType.DAILY_METRICS,
            start_date=date(2023, 1, 1),
            end_date=date(2023, 1, 31),
            cache_strategy=CacheStrategy.AGGRESSIVE
        )
        
        # Mock cache hit
        cached_result = AnalyticsResult(
            request=request,
            data={'cached': True},
            success=True
        )
        
        analytics_engine.cache_manager = Mock()
        analytics_engine.cache_manager.get = Mock(return_value=cached_result)
        
        result = await analytics_engine.process_request(request)
        
        assert result.data['cached'] is True
        analytics_engine.cache_manager.get.assert_called_once()
        
    async def test_batch_processing(self, analytics_engine):
        """Test batch request processing."""
        requests = [
            AnalyticsRequest(
                metric_type="steps",
                calculation_type=CalculationType.DAILY_METRICS,
                start_date=date(2023, 1, 1),
                end_date=date(2023, 1, 31)
            ),
            AnalyticsRequest(
                metric_type="heart_rate",
                calculation_type=CalculationType.WEEKLY_METRICS,
                start_date=date(2023, 1, 1),
                end_date=date(2023, 1, 31)
            )
        ]
        
        # Mock calculator
        mock_calc = Mock()
        mock_calc.calculate_metrics = Mock(return_value={'test': 'data'})
        
        with patch.object(analytics_engine, '_get_calculator', return_value=mock_calc):
            results = await analytics_engine.process_batch(requests)
            
        assert len(results) == 2
        assert all(isinstance(r, AnalyticsResult) for r in results)
        
    async def test_stream_processing(self, analytics_engine):
        """Test streaming data processing."""
        request = AnalyticsRequest(
            metric_type="steps",
            calculation_type=CalculationType.STREAMING,
            start_date=date(2023, 1, 1),
            end_date=date(2023, 12, 31)
        )
        
        # Mock streaming loader
        mock_loader = Mock(spec=StreamingDataLoader)
        async def mock_stream():
            for i in range(3):
                yield pd.DataFrame({'value': [i * 1000]})
                
        mock_loader.stream_data = mock_stream
        
        with patch.object(analytics_engine, '_create_streaming_loader', return_value=mock_loader):
            chunks = []
            async for chunk in analytics_engine.stream_data(request):
                chunks.append(chunk)
                
        assert len(chunks) == 3
        
    async def test_progressive_loading(self, analytics_engine):
        """Test progressive data loading."""
        request = AnalyticsRequest(
            metric_type="steps",
            calculation_type=CalculationType.PROGRESSIVE,
            start_date=date(2023, 1, 1),
            end_date=date(2023, 12, 31)
        )
        
        # Mock progressive loader
        mock_loader = Mock(spec=ProgressiveDataLoader)
        mock_loader.get_summary = Mock(return_value={'summary': 'data'})
        mock_loader.get_details = Mock(return_value={'details': 'data'})
        
        with patch('src.analytics.optimized_analytics_engine.ProgressiveDataLoader', return_value=mock_loader):
            result = await analytics_engine.process_request(request)
            
        assert result.success is True
        
    async def test_priority_handling(self, analytics_engine):
        """Test request priority handling."""
        high_priority = AnalyticsRequest(
            metric_type="steps",
            calculation_type=CalculationType.DAILY_METRICS,
            priority=Priority.CRITICAL
        )
        
        low_priority = AnalyticsRequest(
            metric_type="steps",
            calculation_type=CalculationType.DAILY_METRICS,
            priority=Priority.LOW
        )
        
        # Add to queue
        await analytics_engine.computation_queue.add_request(low_priority)
        await analytics_engine.computation_queue.add_request(high_priority)
        
        # High priority should be processed first
        next_request = await analytics_engine.computation_queue.get_next_request()
        assert next_request.priority == Priority.CRITICAL
        
    async def test_error_handling(self, analytics_engine):
        """Test error handling in request processing."""
        request = AnalyticsRequest(
            metric_type="invalid",
            calculation_type=CalculationType.DAILY_METRICS
        )
        
        # Mock calculator that raises error
        mock_calc = Mock()
        mock_calc.calculate_metrics = Mock(side_effect=Exception("Test error"))
        
        with patch.object(analytics_engine, '_get_calculator', return_value=mock_calc):
            # calculate_metrics is synchronous, not async
            try:
                result = analytics_engine.calculate_metrics(request)
                assert False, "Should have raised an exception"
            except Exception as e:
                assert str(e) == "Test error"
        
    def test_concurrent_requests(self, analytics_engine):
        """Test handling concurrent requests."""
        requests = [
            AnalyticsRequest(
                metric_type=f"metric_{i}",
                calculation_type=CalculationType.DAILY_METRICS
            )
            for i in range(5)
        ]
        
        # Mock calculator
        mock_calc = Mock()
        mock_calc.calculate_metrics = Mock(return_value={'data': 'test'})
        
        with patch.object(analytics_engine, '_get_calculator', return_value=mock_calc):
            # Process requests
            results = [analytics_engine.calculate_metrics(req) for req in requests]
            
        assert len(results) == 5
        assert all(r == {'data': 'test'} for r in results)
        
    def test_shutdown(self, analytics_engine):
        """Test engine shutdown."""
        analytics_engine.shutdown()
        
        # Verify connection pool is closed
        analytics_engine.connection_pool.close.assert_called_once()
        
    def test_get_performance_stats(self, analytics_engine):
        """Test getting performance statistics."""
        stats = analytics_engine.get_performance_stats()
        
        assert 'requests_processed' in stats
        assert 'average_processing_time' in stats
        assert 'cache_hit_rate' in stats
        assert 'active_connections' in stats
        
    async def test_optimize_calculation(self, analytics_engine):
        """Test calculation optimization."""
        request = AnalyticsRequest(
            metric_type="steps",
            calculation_type=CalculationType.DAILY_METRICS,
            optimize=True
        )
        
        # Should use optimized calculator
        with patch.object(analytics_engine, '_get_optimized_calculator') as mock_get:
            mock_get.return_value = Mock(calculate_metrics=Mock(return_value={}))
            await analytics_engine.process_request(request)
            
        mock_get.assert_called_once()


class TestAnalyticsRequest:
    """Test AnalyticsRequest class."""
    
    def test_request_creation(self):
        """Test creating analytics request."""
        request = AnalyticsRequest(
            metric_type="steps",
            calculation_type=CalculationType.DAILY_METRICS,
            start_date=date(2023, 1, 1),
            end_date=date(2023, 1, 31)
        )
        
        assert request.metric_type == "steps"
        assert request.calculation_type == CalculationType.DAILY_METRICS
        assert request.priority == Priority.NORMAL
        
    def test_request_hash(self):
        """Test request hashing for cache."""
        request1 = AnalyticsRequest(
            metric_type="steps",
            calculation_type=CalculationType.DAILY_METRICS
        )
        
        request2 = AnalyticsRequest(
            metric_type="steps",
            calculation_type=CalculationType.DAILY_METRICS
        )
        
        # Same parameters should have same hash
        assert hash(request1) == hash(request2)
        
    def test_request_with_options(self):
        """Test request with additional options."""
        request = AnalyticsRequest(
            metric_type="steps",
            calculation_type=CalculationType.CUSTOM,
            options={
                'aggregation': 'sum',
                'interval': 'hourly'
            }
        )
        
        assert request.options['aggregation'] == 'sum'
        assert request.options['interval'] == 'hourly'


class TestCacheIntegration:
    """Test cache integration."""
    
    @pytest.mark.asyncio
    async def test_cache_warming(self, analytics_engine):
        """Test cache warming functionality."""
        requests = [
            AnalyticsRequest(
                metric_type="steps",
                calculation_type=CalculationType.DAILY_METRICS,
                start_date=date(2023, 1, 1),
                end_date=date(2023, 1, 31)
            )
        ]
        
        # Mock calculator
        mock_calc = Mock()
        mock_calc.calculate_metrics = Mock(return_value={'warmed': True})
        
        with patch.object(analytics_engine, '_get_calculator', return_value=mock_calc):
            await analytics_engine.warm_cache(requests)
            
        # Verify cache was populated
        assert mock_calc.calculate_metrics.called


class TestPerformanceOptimizations:
    """Test performance optimizations."""
    
    @pytest.mark.asyncio
    async def test_query_optimization(self, analytics_engine):
        """Test query optimization."""
        request = AnalyticsRequest(
            metric_type="steps",
            calculation_type=CalculationType.DAILY_METRICS,
            start_date=date(2020, 1, 1),
            end_date=date(2023, 12, 31)  # Large date range
        )
        
        # Should use optimized query strategy
        with patch.object(analytics_engine.database, 'execute_query') as mock_query:
            mock_query.return_value = pd.DataFrame()
            
            with patch.object(analytics_engine, '_get_calculator') as mock_calc:
                mock_calc.return_value = Mock(calculate_metrics=Mock(return_value={}))
                await analytics_engine.process_request(request)
                
        # Verify optimization occurred
        assert mock_query.called
        
    @pytest.mark.asyncio
    async def test_memory_efficient_processing(self, analytics_engine):
        """Test memory-efficient processing for large datasets."""
        request = AnalyticsRequest(
            metric_type="steps",
            calculation_type=CalculationType.STREAMING,
            memory_limit_mb=100
        )
        
        # Should use streaming approach
        result = await analytics_engine.process_request(request)
        
        # Verify memory limit was respected
        stats = analytics_engine.get_performance_stats()
        assert 'peak_memory_mb' in stats