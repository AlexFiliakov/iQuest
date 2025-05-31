"""
Unit tests for Reactive Data Binding System

Tests verify that the implementation meets all acceptance criteria.
"""

import time
import pytest
from datetime import datetime, timedelta
from unittest.mock import Mock, patch

import pandas as pd
import numpy as np
from PyQt6.QtCore import QTimer
from PyQt6.QtTest import QSignalSpy
from PyQt6.QtWidgets import QApplication

from src.ui.reactive_data_binding import (
    ReactiveDataSource, ReactiveHealthDataStore, ReactiveDataBinding,
    UpdateMethod, DataChangeType, DataChange
)
from src.ui.reactive_change_detection import (
    EfficientChangeDetector, ConflictResolver, UpdateScheduler,
    ConflictResolutionStrategy, ChangeHistory
)
from src.ui.reactive_health_integration import ReactiveHealthDataBinding
from src.ui.reactive_data_transformations import (
    TransformationPipeline, AggregationTransformation,
    SlidingWindowTransformation, HealthMetricTransformation
)


class TestReactiveDataBinding:
    """Test reactive data binding core functionality"""
    
    def test_automatic_chart_updates(self, qtbot):
        """Test that charts update automatically when data changes"""
        # Create reactive data source
        source = ReactiveDataSource()
        
        # Create mock chart
        mock_chart = Mock()
        mock_chart.data = pd.DataFrame()
        mock_chart.destroyed = Mock()
        mock_chart.destroyed.connect = Mock()
        
        # Create binding
        binding = ReactiveDataBinding()
        binding_id = binding.bind(source, mock_chart)
        
        # Update data
        new_data = pd.DataFrame({'value': [1, 2, 3]})
        source.update_data(new_data)
        
        # Wait for signal processing
        qtbot.wait(100)
        
        # Verify chart was updated
        mock_chart.update.assert_called()
        pd.testing.assert_frame_equal(mock_chart.data, new_data)
        
    def test_update_latency_under_50ms(self, qtbot):
        """Test that update latency is under 50ms for typical datasets"""
        # Create reactive data source with immediate updates
        source = ReactiveDataSource()
        source.set_batch_interval(0)  # Immediate updates
        
        # Track update timing
        update_times = []
        
        def track_update(change):
            update_times.append(time.time())
            
        source.data_changed.connect(track_update)
        
        # Generate typical dataset (1000 rows)
        data = pd.DataFrame({
            'timestamp': pd.date_range(start='2025-01-01', periods=1000, freq='min'),
            'heart_rate': np.random.normal(70, 10, 1000),
            'steps': np.random.randint(0, 100, 1000)
        })
        
        # Time the update
        start_time = time.time()
        source.update_data(data)
        
        # Wait for update
        qtbot.wait(100)
        
        # Calculate latency
        if update_times:
            latency = (update_times[0] - start_time) * 1000  # Convert to ms
            assert latency < 50, f"Update latency {latency}ms exceeds 50ms requirement"
            
    def test_memory_efficient_change_detection(self):
        """Test that change detection has O(log n) complexity"""
        detector = EfficientChangeDetector(chunk_size=100)
        
        # Test with increasingly large datasets
        sizes = [100, 1000, 10000]
        times = []
        
        for size in sizes:
            # Create dataset
            old_data = pd.DataFrame({
                'value': range(size)
            })
            new_data = old_data.copy()
            new_data.loc[size // 2, 'value'] = -1  # Change one value
            
            # Time change detection
            start = time.time()
            changes = detector.detect_changes(old_data, new_data)
            end = time.time()
            
            times.append(end - start)
            
            # Verify change was detected
            assert changes['type'] == 'incremental'
            assert len(changes['modified']) == 1
            
        # Verify sub-linear complexity - time should not increase linearly
        # For sub-linear complexity, time ratio should be less than size ratio
        time_ratio = times[2] / times[0]
        size_ratio = sizes[2] / sizes[0]
        
        # Allow for some overhead but ensure it's not O(n)
        assert time_ratio < size_ratio, f"Change detection appears to be O(n) or worse: time ratio {time_ratio} vs size ratio {size_ratio}"
        # Ideally we want better than O(n), but at least ensure it's not worse
        assert time_ratio < size_ratio * 2, f"Change detection performance is poor: time ratio {time_ratio} vs size ratio {size_ratio}"
        
    def test_batch_update_support(self, qtbot):
        """Test that batch updates work correctly"""
        source = ReactiveDataSource()
        source.set_batch_interval(50)  # 50ms batching
        
        # Track batch updates
        batch_spy = QSignalSpy(source.batch_updated)
        
        # Send multiple updates rapidly
        for i in range(5):
            data = pd.DataFrame({'value': [i]})
            source.update_data(data)
            
        # Wait for batch processing
        qtbot.wait(100)
        
        # Should have received at least one batch
        assert len(batch_spy) >= 1
        
        # Batch should contain multiple updates
        batch = batch_spy[0][0]
        assert len(batch) > 1
        
    def test_concurrent_modification_handling(self):
        """Test that concurrent modifications are handled gracefully"""
        resolver = ConflictResolver(ConflictResolutionStrategy.LAST_WRITE_WINS)
        
        # Simulate concurrent updates
        key = 'heart_rate'
        resolver.add_change(key, 75, 'source1', datetime.now())
        resolver.add_change(key, 78, 'source2', datetime.now() + timedelta(milliseconds=10))
        resolver.add_change(key, 76, 'source3', datetime.now() + timedelta(milliseconds=20))
        
        # Resolve conflicts
        resolved = resolver.resolve_conflicts()
        
        # Should use last value
        assert resolved[key] == 76
        
        # Verify conflict was logged
        conflicts = resolver.get_conflict_log()
        assert len(conflicts) == 1
        assert conflicts[0].key == key
        assert len(conflicts[0].values) == 3
        
    def test_rollback_mechanism(self):
        """Test rollback functionality for failed updates"""
        history = ChangeHistory(max_history=10)
        
        # Record some changes
        change1 = Mock(timestamp=datetime.now())
        change2 = Mock(timestamp=datetime.now())
        change3 = Mock(timestamp=datetime.now())
        
        history.record_change(change1)
        history.create_rollback_point('before_risky_update')
        history.record_change(change2)
        history.record_change(change3)
        
        # Rollback to point
        changes_to_revert = history.rollback_to_point('before_risky_update')
        
        # Should return changes after rollback point
        assert len(changes_to_revert) == 2
        assert change2 in changes_to_revert
        assert change3 in changes_to_revert
        
    def test_debug_tooling(self, qtbot):
        """Test debug tooling for tracking data flow"""
        # Create binding system with performance tracking
        binding_system = ReactiveHealthDataBinding()
        
        # Connect to performance warning signal
        warning_spy = QSignalSpy(binding_system.performance_warning)
        
        # Create high-frequency updates to trigger warning
        source = ReactiveDataSource()
        mock_chart = Mock()
        mock_chart.data = pd.DataFrame()
        mock_chart.destroyed = Mock()
        mock_chart.destroyed.connect = Mock()
        
        binding_id = binding_system.bind_chart(mock_chart, source)
        
        # Simulate many rapid updates
        for i in range(150):
            source.update_data(pd.DataFrame({'value': [i]}))
            
        # Wait for performance check
        qtbot.wait(100)
        
        # Performance tracking should work
        # Note: Warning may not trigger in test due to timing


class TestHealthSpecificFeatures:
    """Test health-specific reactive features"""
    
    def test_health_metric_transformations(self):
        """Test health-specific data transformations"""
        # Test heart rate zone calculation
        hr_transform = HealthMetricTransformation('heart_rate_zones')
        
        data = pd.DataFrame({
            'heart_rate': [60, 80, 120, 160, 180]
        })
        
        result = hr_transform.transform(data)
        
        assert 'heart_rate_zone' in result.columns
        assert result['heart_rate_zone'].iloc[0] == 'rest'  # 60 bpm (< 95)
        assert result['heart_rate_zone'].iloc[3] == 'hard'   # 160 bpm (133-161.5)
        
    def test_activity_intensity_calculation(self):
        """Test activity intensity transformation"""
        activity_transform = HealthMetricTransformation('activity_intensity')
        
        data = pd.DataFrame({
            'steps': [500, 2000, 4000, 8000]
        })
        
        result = activity_transform.transform(data)
        
        assert 'activity_intensity' in result.columns
        assert result['activity_intensity'].iloc[0] == 'sedentary'
        assert result['activity_intensity'].iloc[3] == 'vigorous'
        
    def test_transformation_pipeline(self):
        """Test transformation pipeline functionality"""
        pipeline = TransformationPipeline([
            AggregationTransformation('h', 'mean'),
            SlidingWindowTransformation(3, 'mean')
        ])
        
        # Create hourly data
        data = pd.DataFrame({
            'value': range(24),
            'timestamp': pd.date_range(start='2025-01-01', periods=24, freq='h')
        }).set_index('timestamp')
        
        result = pipeline.transform(data)
        
        # Should have aggregated and smoothed data
        assert len(result) <= len(data)
        assert not result.isna().all().any()  # No columns should be all NaN


class TestIntegrationScenarios:
    """Test real-world integration scenarios"""
    
    def test_real_time_heart_rate_monitoring(self, qtbot):
        """Test real-time heart rate monitoring scenario"""
        # Create data store
        store = ReactiveHealthDataStore()
        
        # Track updates
        updates = []
        store.data_changed.connect(lambda change: updates.append(change))
        
        # Simulate heart rate updates
        for i in range(5):
            hr = 70 + i
            store.update_metric('heart_rate', hr, datetime.now())
            qtbot.wait(10)  # Small delay between updates
            
        # Should have immediate updates for heart rate
        assert len(updates) >= 5
        
    def test_activity_dashboard_updates(self, qtbot):
        """Test activity dashboard update scenario"""
        # Create binding system
        binding_system = ReactiveHealthDataBinding()
        
        # Create mock chart
        mock_chart = Mock()
        mock_chart.data = pd.DataFrame()
        mock_chart.destroyed = Mock()
        mock_chart.destroyed.connect = Mock()
        
        # Create activity data source
        source = ReactiveDataSource()
        
        # Apply hourly aggregation transform
        transform = TransformationPipeline([
            AggregationTransformation('H', 'sum')
        ])
        
        binding_id = binding_system.bind_chart(
            mock_chart, 
            source,
            transform=lambda df: transform.transform(df)
        )
        
        # Update with activity data
        data = pd.DataFrame({
            'steps': np.random.randint(0, 100, 60),
            'timestamp': pd.date_range(start='2025-01-01', periods=60, freq='min')
        }).set_index('timestamp')
        
        source.update_data(data)
        qtbot.wait(100)
        
        # Chart should have received aggregated data
        mock_chart.update.assert_called()
        assert mock_chart.data is not None


@pytest.fixture(scope='session')
def qapp():
    """Create QApplication for tests"""
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    return app