"""
Visual regression tests for chart and UI components.
Ensures visual consistency across changes and different environments.
"""

import pytest
import numpy as np
import pandas as pd
import os
from pathlib import Path

try:
    from tests.visual.visual_test_base import VisualTestBase
    VISUAL_FRAMEWORK_AVAILABLE = True
except ImportError:
    VISUAL_FRAMEWORK_AVAILABLE = False
    
from tests.test_data_generator import HealthDataGenerator


class TestVisualRegression(VisualTestBase if VISUAL_FRAMEWORK_AVAILABLE else object):
    """Visual regression tests for charts and UI components."""
    
    @pytest.fixture
    def sample_data(self):
        """Create sample data for chart testing."""
        generator = HealthDataGenerator(seed=42)
        return generator.generate(30)  # 30 days of data
    
    @pytest.fixture
    def chart_config(self):
        """Standard chart configuration for consistent testing."""
        return {
            'width': 800,
            'height': 600,
            'dpi': 100,
            'style': 'default',
            'animate': False,  # Disable animations for testing
            'theme': 'light'
        }
    
    # Simple framework validation test
    @pytest.mark.visual
    def test_framework_validation(self):
        """Test that the visual framework is working."""
        if not VISUAL_FRAMEWORK_AVAILABLE:
            pytest.skip("Visual framework not available")
        
        # Create a simple widget for testing
        from PyQt6.QtWidgets import QLabel
        
        widget = QLabel("Test Framework")
        widget.resize(200, 100)
        widget.setStyleSheet("background-color: white; color: black; font-size: 14px;")
        
        # This should create a baseline or compare against existing
        self.assert_visual_match(
            widget,
            'framework_validation',
            threshold=0.98
        )

    # Line Chart Visual Tests
    @pytest.mark.visual
    def test_line_chart_steps_rendering(self, sample_data, chart_config):
        """Test line chart rendering for steps data."""
        if not VISUAL_FRAMEWORK_AVAILABLE:
            pytest.skip("Visual framework not available")
            
        try:
            from src.ui.charts.line_chart import LineChart
        except ImportError:
            pytest.skip("LineChart module not available")
        
        chart = LineChart()
        chart.configure(**chart_config)
        chart.set_data(sample_data['date'], sample_data['steps'])
        chart.set_title("Daily Steps")
        chart.set_labels("Date", "Steps")
        
        # Use new visual assertion framework
        self.assert_visual_match(
            chart, 
            'line_chart_steps',
            threshold=0.95,
            comparison_method='ssim'
        )

    @pytest.mark.visual
    def test_line_chart_heart_rate_rendering(self, sample_data, chart_config):
        """Test line chart rendering for heart rate data."""
        if not VISUAL_FRAMEWORK_AVAILABLE:
            pytest.skip("Visual framework not available")
            
        try:
            from src.ui.charts.line_chart import LineChart
        except ImportError:
            pytest.skip("LineChart module not available")
        
        chart = LineChart()
        chart.configure(**chart_config)
        chart.set_data(sample_data['date'], sample_data['heart_rate'])
        chart.set_title("Average Heart Rate")
        chart.set_labels("Date", "BPM")
        
        self.assert_visual_match(
            chart, 
            'line_chart_heart_rate',
            threshold=0.95
        )

    # Bar Chart Visual Tests
    @pytest.mark.visual
    def test_bar_chart_weekly_summary(self, sample_data, chart_config):
        """Test bar chart rendering for weekly summaries."""
        if not VISUAL_FRAMEWORK_AVAILABLE:
            pytest.skip("Visual framework not available")
            
        try:
            from src.ui.charts.bar_chart import BarChart
        except ImportError:
            pytest.skip("BarChart module not available")
        
        # Create weekly summary data
        weekly_data = sample_data.groupby(sample_data['date'].dt.week).agg({
            'steps': 'mean'
        }).reset_index()
        
        chart = BarChart()
        chart.configure(**chart_config)
        chart.set_data(weekly_data['week'], weekly_data['steps'])
        chart.set_title("Weekly Average Steps")
        chart.set_labels("Week", "Average Steps")
        
        self.assert_visual_match(
            chart,
            'bar_chart_weekly_summary',
            threshold=0.95
        )

    # Scatter Plot Visual Tests
    @pytest.mark.visual
    def test_scatter_plot_correlation(self, visual_tester, sample_data, chart_config):
        """Test scatter plot for correlation analysis."""
        from src.ui.charts.scatter_chart import ScatterChart
        
        chart = ScatterChart()
        chart.configure(**chart_config)
        chart.set_data(sample_data['steps'], sample_data['exercise_minutes'])
        chart.set_title("Steps vs Exercise Minutes")
        chart.set_labels("Daily Steps", "Exercise Minutes")
        
        image = chart.render_to_image()
        
        baseline_path = visual_tester.baseline_dir / "scatter_plot_correlation.png"
        diff = visual_tester.compare_images(baseline_path, image)
        
        assert diff['rmse'] <= visual_tester.tolerance

    # Heatmap Visual Tests
    @pytest.mark.visual
    def test_calendar_heatmap_rendering(self, visual_tester, sample_data, chart_config):
        """Test calendar heatmap rendering."""
        from src.ui.charts.calendar_heatmap import CalendarHeatmap
        
        chart = CalendarHeatmap()
        chart.configure(**chart_config)
        chart.set_data(sample_data['date'], sample_data['steps'])
        chart.set_title("Daily Steps Heatmap")
        
        image = chart.render_to_image()
        
        baseline_path = visual_tester.baseline_dir / "calendar_heatmap.png"
        diff = visual_tester.compare_images(baseline_path, image)
        
        assert diff['rmse'] <= visual_tester.tolerance

    # Multi-chart Dashboard Tests
    @pytest.mark.visual
    def test_dashboard_layout(self, visual_tester, sample_data):
        """Test complete dashboard layout rendering."""
        from src.ui.charts.dashboard import HealthDashboard
        
        dashboard = HealthDashboard()
        dashboard.configure(width=1200, height=800, dpi=100)
        dashboard.set_data(sample_data)
        dashboard.create_layout([
            'line_chart_steps',
            'bar_chart_weekly',
            'scatter_correlation',
            'summary_stats'
        ])
        
        image = dashboard.render_to_image()
        
        baseline_path = visual_tester.baseline_dir / "dashboard_layout.png"
        diff = visual_tester.compare_images(baseline_path, image)
        
        assert diff['rmse'] <= visual_tester.tolerance

    # Responsive Design Tests
    @pytest.mark.visual
    @pytest.mark.parametrize("size", [
        (400, 300),   # Small
        (800, 600),   # Medium  
        (1200, 900),  # Large
        (1920, 1080)  # XL
    ])
    def test_responsive_chart_rendering(self, visual_tester, sample_data, size):
        """Test chart rendering at different sizes."""
        from src.ui.charts.line_chart import LineChart
        
        width, height = size
        chart = LineChart()
        chart.configure(width=width, height=height, dpi=100, animate=False)
        chart.set_data(sample_data['date'], sample_data['steps'])
        chart.set_title("Daily Steps - Responsive Test")
        
        image = chart.render_to_image()
        
        # Verify image dimensions
        assert image.size == (width, height)
        
        baseline_name = f"line_chart_responsive_{width}x{height}.png"
        baseline_path = visual_tester.baseline_dir / baseline_name
        diff = visual_tester.compare_images(baseline_path, image)
        
        # Allow slightly more tolerance for responsive tests
        assert diff['rmse'] <= visual_tester.tolerance * 1.5

    # Color Theme Tests
    @pytest.mark.visual
    @pytest.mark.parametrize("theme", ["light", "dark", "warm", "cool"])
    def test_color_theme_consistency(self, visual_tester, sample_data, theme):
        """Test color theme consistency across charts."""
        from src.ui.charts.line_chart import LineChart
        from src.ui.style_manager import StyleManager
        
        style_manager = StyleManager()
        style_manager.set_theme(theme)
        
        chart = LineChart()
        chart.configure(width=800, height=600, theme=theme, animate=False)
        chart.set_data(sample_data['date'], sample_data['steps'])
        chart.set_title(f"Daily Steps - {theme.title()} Theme")
        
        image = chart.render_to_image()
        
        baseline_name = f"line_chart_theme_{theme}.png"
        baseline_path = visual_tester.baseline_dir / baseline_name
        diff = visual_tester.compare_images(baseline_path, image)
        
        assert diff['rmse'] <= visual_tester.tolerance

    # Animation Consistency Tests
    @pytest.mark.visual
    def test_animation_frame_consistency(self, visual_tester, sample_data):
        """Test that animation frames are visually consistent."""
        from src.ui.charts.animated_line_chart import AnimatedLineChart
        
        chart = AnimatedLineChart()
        chart.configure(width=800, height=600, dpi=100)
        chart.set_data(sample_data['date'], sample_data['steps'])
        chart.set_title("Daily Steps - Animation Test")
        
        # Capture multiple animation frames
        frames = chart.render_animation_frames(num_frames=5)
        
        # Test each frame
        for i, frame in enumerate(frames):
            baseline_name = f"animation_frame_{i}.png"
            baseline_path = visual_tester.baseline_dir / baseline_name
            diff = visual_tester.compare_images(baseline_path, frame)
            
            assert diff['rmse'] <= visual_tester.tolerance

    # UI Component Visual Tests
    @pytest.mark.visual
    def test_summary_cards_rendering(self, visual_tester, sample_data):
        """Test summary cards visual consistency."""
        from src.ui.summary_cards import SummaryCards
        
        cards = SummaryCards()
        cards.configure(width=400, height=200)
        
        # Calculate summary metrics
        metrics = {
            'avg_steps': sample_data['steps'].mean(),
            'avg_heart_rate': sample_data['heart_rate_avg'].mean(),
            'total_exercise': sample_data['exercise_minutes'].sum(),
            'avg_sleep': sample_data['sleep_hours'].mean()
        }
        
        cards.set_metrics(metrics)
        image = cards.render_to_image()
        
        baseline_path = visual_tester.baseline_dir / "summary_cards.png"
        diff = visual_tester.compare_images(baseline_path, image)
        
        assert diff['rmse'] <= visual_tester.tolerance

    # Data Quality Visualization Tests
    @pytest.mark.visual
    def test_data_quality_indicators(self, visual_tester):
        """Test data quality visualization components."""
        from src.ui.data_quality_widget import DataQualityWidget
        from tests.test_data_generator import HealthDataGenerator
        
        generator = HealthDataGenerator(seed=42)
        edge_cases = generator.generate_edge_cases()
        
        widget = DataQualityWidget()
        widget.configure(width=600, height=400)
        widget.set_data(edge_cases['missing_dates'])  # Data with gaps
        
        image = widget.render_to_image()
        
        baseline_path = visual_tester.baseline_dir / "data_quality_indicators.png"
        diff = visual_tester.compare_images(baseline_path, image)
        
        assert diff['rmse'] <= visual_tester.tolerance

    # Cross-platform Consistency Tests
    @pytest.mark.visual
    @pytest.mark.skipif(os.name != 'nt', reason="Windows-specific test")
    def test_windows_rendering_consistency(self, visual_tester, sample_data):
        """Test rendering consistency on Windows."""
        from src.ui.charts.line_chart import LineChart
        
        chart = LineChart()
        chart.configure(width=800, height=600, dpi=96)  # Windows DPI
        chart.set_data(sample_data['date'], sample_data['steps'])
        chart.set_title("Daily Steps - Windows")
        
        image = chart.render_to_image()
        
        baseline_path = visual_tester.baseline_dir / "line_chart_windows.png"
        diff = visual_tester.compare_images(baseline_path, image)
        
        assert diff['rmse'] <= visual_tester.tolerance

    # Stress Test Visual Consistency
    @pytest.mark.visual
    @pytest.mark.slow
    def test_large_dataset_visual_consistency(self, visual_tester):
        """Test visual consistency with large datasets."""
        from src.ui.charts.line_chart import LineChart
        from tests.test_data_generator import HealthDataGenerator
        
        generator = HealthDataGenerator(seed=42)
        large_data = generator.generate_performance_data('large')
        
        # Sample down to reasonable size for visualization
        sampled_data = large_data.sample(n=1000, random_state=42).sort_values('date')
        
        chart = LineChart()
        chart.configure(width=800, height=600, animate=False)
        chart.set_data(sampled_data['date'], sampled_data['steps'])
        chart.set_title("Daily Steps - Large Dataset Sample")
        
        image = chart.render_to_image()
        
        baseline_path = visual_tester.baseline_dir / "line_chart_large_dataset.png"
        diff = visual_tester.compare_images(baseline_path, image)
        
        assert diff['rmse'] <= visual_tester.tolerance


# Utility functions for visual testing
def regenerate_baselines():
    """Utility function to regenerate all visual baselines."""
    # This would be called manually when intentional visual changes are made
    baseline_dir = Path("tests/visual/baselines")
    if baseline_dir.exists():
        import shutil
        shutil.rmtree(baseline_dir)
    
    # Re-run all visual tests to generate new baselines
    pytest.main(["-m", "visual", "--tb=short"])


# Custom pytest markers for visual tests
pytestmark = pytest.mark.visual