"""
Unit tests for Activity Timeline Insights components.

Tests the new user-friendly insights panels that transform technical
analytics data into understandable visualizations.
"""

import pytest
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import Qt

from src.ui.timeline_insights_panel import TimelineInsightsPanel
from src.ui.pattern_recognition_card import PatternRecognitionCard
from src.ui.anomaly_alert_card import AnomalyAlertCard
from src.ui.activity_heatmap_widget import ActivityHeatmapWidget


# Use qapp fixture from conftest.py instead of defining our own
    

@pytest.fixture
def sample_timeline_data():
    """Create sample hourly data for testing."""
    # Create 24 hours of data
    index = pd.date_range('2024-01-15 00:00', periods=24, freq='h')
    data = {
        'steps': np.random.normal(200, 50, 24),
        'heart_rate': np.random.normal(70, 10, 24),
        'active_calories': np.random.normal(10, 5, 24)
    }
    df = pd.DataFrame(data, index=index)
    
    # Create MultiIndex columns as expected by the component
    df.columns = pd.MultiIndex.from_tuples([
        ('steps', 'mean'),
        ('heart_rate', 'mean'),
        ('active_calories', 'mean')
    ])
    
    return df


@pytest.fixture
def sample_clusters():
    """Create sample cluster data."""
    # 24 hours assigned to 4 clusters
    clusters = np.array([0, 0, 0, 0, 0, 0,  # Early morning (cluster 0)
                        1, 1, 1, 1, 1, 1,   # Midday (cluster 1)
                        2, 2, 2, 2, 2, 2,   # Evening (cluster 2)
                        3, 3, 3, 3, 3, 3])  # Night (cluster 3)
    return clusters


@pytest.fixture
def sample_anomalies():
    """Create sample anomaly data."""
    # 24 hours with 3 anomalies
    anomalies = np.array([False] * 24)
    anomalies[3] = True   # Early morning anomaly
    anomalies[15] = True  # Afternoon anomaly
    anomalies[22] = True  # Late night anomaly
    return anomalies


class TestTimelineInsightsPanel:
    """Test the main Timeline Insights Panel."""
    
    def test_panel_creation(self, qapp):
        """Test that the panel can be created."""
        panel = TimelineInsightsPanel()
        assert panel is not None
        assert hasattr(panel, 'pattern_card')
        assert hasattr(panel, 'anomaly_card')
        assert hasattr(panel, 'heatmap_widget')
        
    def test_update_insights(self, qapp, sample_timeline_data, sample_clusters, sample_anomalies):
        """Test updating the panel with data."""
        panel = TimelineInsightsPanel()
        
        # Update with sample data
        panel.update_insights(
            sample_clusters,
            sample_anomalies,
            sample_timeline_data,
            ['steps', 'heart_rate', 'active_calories']
        )
        
        # Verify data was stored
        assert panel.clusters is not None
        assert panel.anomalies is not None
        assert panel.grouped_data is not None
        assert len(panel.selected_metrics) == 3
        
    def test_pattern_transformation(self, qapp, sample_timeline_data, sample_clusters):
        """Test that clusters are transformed into user-friendly patterns."""
        panel = TimelineInsightsPanel()
        panel.clusters = sample_clusters
        panel.grouped_data = sample_timeline_data
        panel.selected_metrics = ['steps', 'heart_rate']
        
        # Call pattern update
        panel.update_pattern_insights()
        
        # Verify patterns were created
        patterns = panel.pattern_card.patterns
        assert len(patterns) > 0
        assert all('name' in p for p in patterns)
        assert all('detail' in p for p in patterns)
        assert all('icon' in p for p in patterns)
        
        # Check pattern names are user-friendly
        pattern_names = [p['name'] for p in patterns]
        technical_terms = ['cluster', 'id', 'kmeans', 'dbscan']
        for name in pattern_names:
            assert not any(term in name.lower() for term in technical_terms)


class TestPatternRecognitionCard:
    """Test the Pattern Recognition Card widget."""
    
    def test_card_creation(self, qapp):
        """Test that the card can be created."""
        card = PatternRecognitionCard()
        assert card is not None
        assert card.windowTitle() == ""  # Frame has no title
        
    def test_update_patterns(self, qapp):
        """Test updating the card with pattern data."""
        card = PatternRecognitionCard()
        
        # Create test patterns
        patterns = [
            {
                'id': 0,
                'name': 'Early Bird Pattern',
                'detail': 'Most active between 5-9 AM (45% of the time)',
                'icon': '🌅',
                'frequency': 45,
                'intensity': 350
            },
            {
                'id': 1,
                'name': 'Evening Exerciser',
                'detail': 'Prefers 5-8 PM workouts (30% of the time)',
                'icon': '🌆',
                'frequency': 30,
                'intensity': 500
            }
        ]
        
        # Update card
        card.update_patterns(patterns)
        
        # Verify content was updated
        assert card.patterns == patterns
        # Check that placeholder is removed
        assert card.content_layout.count() > 0
        
    def test_empty_patterns(self, qapp):
        """Test card behavior with no patterns."""
        card = PatternRecognitionCard()
        card.update_patterns([])
        
        # Should show placeholder
        assert card.content_layout.count() == 1
        widget = card.content_layout.itemAt(0).widget()
        assert "No patterns detected" in widget.text()


class TestAnomalyAlertCard:
    """Test the Anomaly Alert Card widget."""
    
    def test_card_creation(self, qapp):
        """Test that the card can be created."""
        card = AnomalyAlertCard()
        assert card is not None
        assert hasattr(card, 'count_label')
        
    def test_update_anomalies(self, qapp):
        """Test updating the card with anomaly data."""
        card = AnomalyAlertCard()
        
        # Create test anomalies
        anomalies = [
            {
                'time': datetime.now() - timedelta(hours=2),
                'severity': 'high',
                'explanations': [
                    'Unusually high steps: 1500 (typical: 200)',
                    'Unusually high heart rate: 120 (typical: 70)'
                ],
                'data': {'steps': 1500, 'heart_rate': 120}
            },
            {
                'time': datetime.now() - timedelta(days=1, hours=3),
                'severity': 'medium',
                'explanations': ['Above average activity: 800 steps'],
                'data': {'steps': 800}
            }
        ]
        
        # Update card
        card.update_anomalies(anomalies)
        
        # Verify content
        assert card.anomalies == anomalies
        assert card.count_label.text() == "2"
        assert not card.count_label.isHidden()  # Check that it's not hidden rather than visible
        
    def test_anomaly_dismissal(self, qapp):
        """Test dismissing anomalies."""
        card = AnomalyAlertCard()
        
        # Create test anomaly
        anomaly = {
            'time': datetime.now(),
            'severity': 'low',
            'explanations': ['Minor variation detected'],
            'data': {'steps': 250}
        }
        
        # Update and then dismiss
        card.update_anomalies([anomaly])
        assert card.count_label.text() == "1"
        
        # Dismiss the anomaly
        card.dismiss_anomaly(anomaly)
        
        # Should be hidden now
        assert card.count_label.text() == "0"
        assert card.count_label.isHidden()
        
    def test_time_formatting(self, qapp):
        """Test relative time formatting."""
        card = AnomalyAlertCard()
        
        # Test various time differences
        now = datetime.now()
        
        # 30 minutes ago
        time1 = now - timedelta(minutes=30)
        assert "30 minutes ago" in card.format_time_relative(time1)
        
        # Yesterday
        time2 = now - timedelta(days=1)
        assert "Yesterday at" in card.format_time_relative(time2)
        
        # 3 days ago
        time3 = now - timedelta(days=3)
        assert time3.strftime('%A') in card.format_time_relative(time3)


class TestActivityHeatmapWidget:
    """Test the Activity Heatmap Widget."""
    
    def test_widget_creation(self, qapp):
        """Test that the widget can be created."""
        widget = ActivityHeatmapWidget()
        assert widget is not None
        assert hasattr(widget, 'grid_widget')
        
    def test_update_data(self, qapp):
        """Test updating the heatmap with data."""
        widget = ActivityHeatmapWidget()
        
        # Create test data
        data = {
            ('Mon', 6): 500,   # Monday 6 AM
            ('Mon', 12): 300,  # Monday noon
            ('Mon', 18): 800,  # Monday 6 PM
            ('Tue', 7): 450,
            ('Wed', 8): 600,
            ('Thu', 19): 900,
            ('Fri', 6): 400,
            ('Sat', 10): 200,
            ('Sun', 9): 350
        }
        
        # Update widget
        widget.update_data(data)
        
        # Verify data was stored
        assert widget.data == data
        assert widget.max_intensity == 900
        
    def test_empty_data(self, qapp):
        """Test heatmap with empty data."""
        widget = ActivityHeatmapWidget()
        widget.update_data({})
        
        # Should handle gracefully
        assert widget.data == {}
        assert widget.max_intensity == 0
        
    def test_grid_dimensions(self, qapp):
        """Test that the grid has correct dimensions."""
        widget = ActivityHeatmapWidget()
        
        # Grid should be 24 hours x 7 days
        grid = widget.grid_widget
        assert len(grid.days) == 7
        # Grid widget size should accommodate 24 hours
        expected_height = 24 * grid.cell_height + 23 * 2
        assert grid.height() == expected_height