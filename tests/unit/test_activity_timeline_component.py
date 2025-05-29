"""
Unit tests for the ActivityTimelineComponent.
"""

import pytest
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from PyQt6.QtCore import Qt
from PyQt6.QtTest import QTest
from PyQt6.QtWidgets import QApplication
from unittest.mock import Mock, patch

from src.ui.activity_timeline_component import ActivityTimelineComponent, TimelineVisualizationWidget


@pytest.fixture
def app(qapp):
    """Create QApplication for testing."""
    return qapp


@pytest.fixture
def sample_data():
    """Create sample health data for testing."""
    # Generate hourly data for 24 hours
    times = pd.date_range(start='2024-01-01', periods=24, freq='h')
    
    # Create sample metrics with patterns
    data = pd.DataFrame({
        'heart_rate': np.random.normal(70, 10, 24) + 10 * np.sin(np.linspace(0, 2*np.pi, 24)),
        'steps': np.random.poisson(100, 24) * (np.sin(np.linspace(0, 2*np.pi, 24)) + 1.5),
        'calories': np.random.normal(80, 20, 24) + 20 * np.sin(np.linspace(0, 2*np.pi, 24))
    }, index=times)
    
    # Add some missing values
    data.iloc[5:7] = np.nan
    
    return data


@pytest.fixture
def timeline_component(qtbot, qapp):
    """Create ActivityTimelineComponent instance."""
    # Ensure we have a QApplication instance
    assert qapp is not None
    
    # Create the component directly without a parent for now
    component = ActivityTimelineComponent()
    
    # Let qtbot manage the widget lifecycle
    qtbot.addWidget(component)
    
    # Make sure the widget is visible
    component.show()
    qtbot.waitExposed(component, timeout=1000)
    
    yield component
    
    # Explicit cleanup
    if component and not component.isHidden():
        component.hide()


class TestActivityTimelineComponent:
    """Test suite for ActivityTimelineComponent."""
    
    def test_initialization(self, timeline_component):
        """Test component initialization."""
        assert timeline_component.view_mode == 'linear'
        assert timeline_component.time_grouping == 60
        assert timeline_component.selected_metrics == []
        assert not timeline_component.clustering_enabled
        assert timeline_component.show_patterns
        assert not timeline_component.show_correlations
        
    def test_view_mode_switching(self, timeline_component):
        """Test switching between linear and radial views."""
        # Switch to radial
        timeline_component.set_view_mode('radial')
        assert timeline_component.view_mode == 'radial'
        
        # Switch back to linear
        timeline_component.set_view_mode('linear')
        assert timeline_component.view_mode == 'linear'
        
        # Invalid mode should be ignored
        timeline_component.set_view_mode('invalid')
        assert timeline_component.view_mode == 'linear'
        
    def test_time_grouping_changes(self, timeline_component, qtbot):
        """Test changing time grouping intervals."""
        # Test 15 minutes
        timeline_component.time_combo.setCurrentIndex(0)
        assert timeline_component.time_grouping == 15
        
        # Test 30 minutes
        timeline_component.time_combo.setCurrentIndex(1)
        assert timeline_component.time_grouping == 30
        
        # Test 60 minutes
        timeline_component.time_combo.setCurrentIndex(2)
        assert timeline_component.time_grouping == 60
        
    def test_data_update(self, timeline_component, sample_data):
        """Test updating component with new data."""
        metrics = ['heart_rate', 'steps']
        timeline_component.update_data(sample_data, metrics)
        
        assert timeline_component.data is not None
        assert timeline_component.selected_metrics == metrics
        assert timeline_component.grouped_data is not None
        
    def test_activity_pattern_detection(self, timeline_component, sample_data):
        """Test activity vs rest period detection."""
        metrics = ['steps', 'calories']
        timeline_component.update_data(sample_data, metrics)
        
        # Should have detected active and rest periods
        assert hasattr(timeline_component, 'active_periods')
        assert hasattr(timeline_component, 'rest_periods')
        assert len(timeline_component.active_periods) > 0
        assert len(timeline_component.rest_periods) > 0
        
    def test_clustering_toggle(self, timeline_component, sample_data, qtbot):
        """Test enabling/disabling ML clustering."""
        metrics = ['heart_rate', 'steps']
        timeline_component.update_data(sample_data, metrics)
        
        # Enable clustering
        timeline_component.cluster_check.setChecked(True)
        assert timeline_component.clustering_enabled
        
        # Should have performed clustering
        assert timeline_component.clusters is not None
        assert len(timeline_component.clusters) == len(timeline_component.grouped_data)
        
        # Disable clustering
        timeline_component.cluster_check.setChecked(False)
        assert not timeline_component.clustering_enabled
        
    def test_correlation_calculation(self, timeline_component, sample_data):
        """Test correlation calculation between metrics."""
        metrics = ['heart_rate', 'steps', 'calories']
        timeline_component.show_correlations = True
        timeline_component.update_data(sample_data, metrics)
        
        # Should have calculated correlations
        assert hasattr(timeline_component, 'correlations')
        assert timeline_component.correlations is not None
        assert timeline_component.correlations.shape == (3, 3)
        
        # Check lagged correlations
        assert hasattr(timeline_component, 'lagged_correlations')
        assert len(timeline_component.lagged_correlations) > 0
        
    def test_info_panel_updates(self, timeline_component, sample_data):
        """Test info panel updates with insights."""
        metrics = ['steps']
        timeline_component.update_data(sample_data, metrics)
        
        # Check info panel labels
        assert "Active Periods:" in timeline_component.active_periods_label.text()
        assert "Rest Periods:" in timeline_component.rest_periods_label.text()
        assert "Peak Activity:" in timeline_component.peak_activity_label.text()
        
    def test_empty_data_handling(self, timeline_component):
        """Test handling of empty data."""
        empty_data = pd.DataFrame()
        timeline_component.update_data(empty_data, [])
        
        # Should handle gracefully
        assert timeline_component.data.empty
        assert timeline_component.grouped_data is None or timeline_component.grouped_data.empty
        
    def test_sparse_data_handling(self, timeline_component, qtbot):
        """Test handling of sparse data with many missing values."""
        # Create very sparse data
        times = pd.date_range(start='2024-01-01', periods=24, freq='h')
        sparse_data = pd.DataFrame({
            'metric1': [np.nan] * 20 + [100, 200, 150, 120]
        }, index=times)
        
        # Process events to ensure widget is ready
        qtbot.wait(50)
        
        timeline_component.update_data(sparse_data, ['metric1'])
        
        # Should process without errors
        assert timeline_component.grouped_data is not None
        
    def test_time_range_signal(self, timeline_component, qtbot):
        """Test time range selection signal emission."""
        # Set up signal spy
        with qtbot.waitSignal(timeline_component.time_range_selected, timeout=1000) as blocker:
            # Emit test signal
            start_time = datetime.now()
            end_time = start_time + timedelta(hours=2)
            timeline_component.time_range_selected.emit(start_time, end_time)
            
        # Check signal was emitted with correct values
        assert len(blocker.args) == 2
        assert isinstance(blocker.args[0], datetime)
        assert isinstance(blocker.args[1], datetime)
        
    def test_ml_clustering_edge_cases(self, timeline_component):
        """Test ML clustering with edge cases."""
        # Single data point
        single_point = pd.DataFrame({
            'metric': [100]
        }, index=[datetime.now()])
        
        timeline_component.clustering_enabled = True
        timeline_component.update_data(single_point, ['metric'])
        
        # Should handle gracefully
        assert timeline_component.clusters is None or len(timeline_component.clusters) <= 1
        
    def test_color_interpolation(self, timeline_component):
        """Test color interpolation for heat gradient."""
        viz_widget = timeline_component.viz_widget
        
        # Test interpolation
        color1 = "#FF0000"  # Red
        color2 = "#0000FF"  # Blue
        
        # At 0% should be color1
        result = viz_widget.interpolate_color(color1, color2, 0.0)
        assert result.upper() == color1
        
        # At 100% should be color2
        result = viz_widget.interpolate_color(color1, color2, 1.0)
        assert result.upper() == color2
        
        # At 50% should be purple-ish
        result = viz_widget.interpolate_color(color1, color2, 0.5)
        assert result.upper() != color1 and result.upper() != color2


class TestTimelineVisualizationWidget:
    """Test suite for TimelineVisualizationWidget."""
    
    def test_paint_event_switching(self, timeline_component):
        """Test paint event switches between linear and radial."""
        viz_widget = timeline_component.viz_widget
        
        # Linear mode should call show on canvas
        timeline_component.set_view_mode('linear')
        with patch.object(viz_widget.canvas, 'show') as mock_show:
            viz_widget.paintEvent(None)
            mock_show.assert_called_once()
        
        # Radial mode should call hide on canvas
        timeline_component.set_view_mode('radial')
        with patch.object(viz_widget.canvas, 'hide') as mock_hide:
            with patch.object(viz_widget, 'draw_radial_timeline'):
                viz_widget.paintEvent(None)
                mock_hide.assert_called_once()
            
    def test_mouse_interaction(self, timeline_component, qtbot):
        """Test mouse interaction for brushing."""
        viz_widget = timeline_component.viz_widget
        
        # Simulate mouse press
        qtbot.mousePress(viz_widget, Qt.MouseButton.LeftButton, pos=viz_widget.rect().center())
        assert timeline_component.is_brushing
        assert timeline_component.brush_start is not None
        
        # Simulate mouse release
        qtbot.mouseRelease(viz_widget, Qt.MouseButton.LeftButton, pos=viz_widget.rect().bottomRight())
        assert not timeline_component.is_brushing
        assert timeline_component.brush_end is not None


class TestWSJStyling:
    """Test Wall Street Journal-inspired styling."""
    
    def test_color_palette(self, timeline_component):
        """Test WSJ color palette is properly defined."""
        expected_colors = ['background', 'grid', 'text', 'primary', 
                          'secondary', 'accent', 'heat_low', 'heat_high']
        
        for color in expected_colors:
            assert color in timeline_component.COLORS
            assert timeline_component.COLORS[color].startswith('#')
            
    def test_stylesheet_application(self, timeline_component):
        """Test stylesheet is applied to component."""
        stylesheet = timeline_component.styleSheet()
        
        # Check key style elements
        assert timeline_component.COLORS['background'] in stylesheet
        assert timeline_component.COLORS['grid'] in stylesheet
        assert 'QGroupBox' in stylesheet
        assert 'border-radius' in stylesheet