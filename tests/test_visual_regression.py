"""
Visual regression tests for chart and UI components.
Ensures visual consistency across changes and different environments.
"""

import pytest
import numpy as np
import pandas as pd
from PIL import Image, ImageChops
import io
import os
from pathlib import Path
from typing import Tuple, Dict, Any

from tests.test_data_generator import TestDataGenerator


class VisualRegressionTester:
    """Handles visual regression testing for charts and UI components."""
    
    def __init__(self, baseline_dir: str = "tests/visual/baselines"):
        self.baseline_dir = Path(baseline_dir)
        self.baseline_dir.mkdir(parents=True, exist_ok=True)
        self.tolerance = 0.02  # 2% RMSE tolerance
    
    def compare_images(self, baseline_path: Path, test_image: Image.Image) -> Dict[str, float]:
        """Compare test image with baseline and return difference metrics."""
        if not baseline_path.exists():
            # Save as new baseline if none exists
            test_image.save(baseline_path)
            return {'rmse': 0.0, 'mae': 0.0, 'is_new_baseline': True}
        
        # Load baseline image
        baseline_image = Image.open(baseline_path)
        
        # Ensure images are same size
        if baseline_image.size != test_image.size:
            test_image = test_image.resize(baseline_image.size)
        
        # Convert to same mode
        if baseline_image.mode != test_image.mode:
            test_image = test_image.convert(baseline_image.mode)
        
        # Calculate differences
        diff = ImageChops.difference(baseline_image, test_image)
        
        # Convert to numpy for calculations
        baseline_array = np.array(baseline_image, dtype=np.float32)
        test_array = np.array(test_image, dtype=np.float32)
        diff_array = np.array(diff, dtype=np.float32)
        
        # Calculate metrics
        mse = np.mean((baseline_array - test_array) ** 2)
        rmse = np.sqrt(mse) / 255.0  # Normalize to [0,1]
        mae = np.mean(np.abs(baseline_array - test_array)) / 255.0
        
        return {
            'rmse': rmse,
            'mae': mae,
            'is_new_baseline': False
        }
    
    def save_failure_artifacts(self, test_name: str, test_image: Image.Image, 
                             baseline_image: Image.Image, diff_image: Image.Image):
        """Save failure artifacts for debugging."""
        artifacts_dir = Path("tests/visual/failures") / test_name
        artifacts_dir.mkdir(parents=True, exist_ok=True)
        
        test_image.save(artifacts_dir / "test.png")
        baseline_image.save(artifacts_dir / "baseline.png")
        diff_image.save(artifacts_dir / "diff.png")


class TestVisualRegression:
    """Visual regression tests for charts and UI components."""
    
    @pytest.fixture
    def visual_tester(self):
        """Create visual regression tester."""
        return VisualRegressionTester()
    
    @pytest.fixture
    def sample_data(self):
        """Create sample data for chart testing."""
        generator = TestDataGenerator(seed=42)
        return generator.generate_synthetic_data(30)  # 30 days of data
    
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

    # Line Chart Visual Tests
    @pytest.mark.visual
    def test_line_chart_steps_rendering(self, visual_tester, sample_data, chart_config):
        """Test line chart rendering for steps data."""
        from src.ui.charts.line_chart import LineChart
        
        chart = LineChart()
        chart.configure(**chart_config)
        chart.set_data(sample_data['date'], sample_data['steps'])
        chart.set_title("Daily Steps")
        chart.set_labels("Date", "Steps")
        
        # Render to image
        image = chart.render_to_image()
        
        # Compare with baseline
        baseline_path = visual_tester.baseline_dir / "line_chart_steps.png"
        diff = visual_tester.compare_images(baseline_path, image)
        
        if diff['rmse'] > visual_tester.tolerance:
            pytest.fail(f"Visual regression detected: RMSE {diff['rmse']:.4f} > {visual_tester.tolerance}")

    @pytest.mark.visual
    def test_line_chart_heart_rate_rendering(self, visual_tester, sample_data, chart_config):
        """Test line chart rendering for heart rate data."""
        from src.ui.charts.line_chart import LineChart
        
        chart = LineChart()
        chart.configure(**chart_config)
        chart.set_data(sample_data['date'], sample_data['heart_rate_avg'])
        chart.set_title("Average Heart Rate")
        chart.set_labels("Date", "BPM")
        
        image = chart.render_to_image()
        
        baseline_path = visual_tester.baseline_dir / "line_chart_heart_rate.png"
        diff = visual_tester.compare_images(baseline_path, image)
        
        assert diff['rmse'] <= visual_tester.tolerance, f"Visual regression: RMSE {diff['rmse']:.4f}"

    # Bar Chart Visual Tests
    @pytest.mark.visual
    def test_bar_chart_weekly_summary(self, visual_tester, sample_data, chart_config):
        """Test bar chart rendering for weekly summaries."""
        from src.ui.charts.bar_chart import BarChart
        
        # Create weekly summary data
        weekly_data = sample_data.groupby(sample_data['date'].dt.week).agg({
            'steps': 'mean',
            'exercise_minutes': 'sum'
        }).reset_index()
        
        chart = BarChart()
        chart.configure(**chart_config)
        chart.set_data(weekly_data['week'], weekly_data['steps'])
        chart.set_title("Weekly Average Steps")
        chart.set_labels("Week", "Average Steps")
        
        image = chart.render_to_image()
        
        baseline_path = visual_tester.baseline_dir / "bar_chart_weekly.png"
        diff = visual_tester.compare_images(baseline_path, image)
        
        assert diff['rmse'] <= visual_tester.tolerance

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
        from tests.test_data_generator import TestDataGenerator
        
        generator = TestDataGenerator(seed=42)
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
        from tests.test_data_generator import TestDataGenerator
        
        generator = TestDataGenerator(seed=42)
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