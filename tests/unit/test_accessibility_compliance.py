"""
Tests for accessibility compliance system.

Verifies WCAG 2.1 AA compliance and accessibility features.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from PyQt6.QtCore import Qt
from PyQt6.QtTest import QTest
from PyQt6.QtWidgets import QApplication
import pandas as pd

# Mark all tests in this module as requiring Qt
pytestmark = pytest.mark.ui

from src.ui.accessibility import (
    VisualizationAccessibilityManager,
    WCAGValidator,
    ScreenReaderManager,
    KeyboardNavigationManager,
    ColorAccessibilityManager,
    AccessibleChart,
    WCAGLevel,
    ContrastResult
)
from src.ui.accessibility.accessible_chart_mixin import AccessibleChartMixin
from src.ui.charts.wsj_style_manager import WSJStyleManager


@pytest.fixture
def accessibility_manager():
    """Create accessibility manager instance."""
    theme_manager = WSJStyleManager()
    return VisualizationAccessibilityManager(theme_manager)


@pytest.fixture
def mock_chart():
    """Create mock chart widget."""
    chart = Mock()
    chart.get_data_summary = Mock(return_value="Test data summary")
    chart.get_key_insights = Mock(return_value=["Insight 1", "Insight 2"])
    chart.setAccessibleName = Mock()
    chart.setAccessibleDescription = Mock()
    chart.setFocusPolicy = Mock()
    chart.setProperty = Mock()
    chart.get_color_scheme = Mock(return_value={
        'background': '#FFFFFF',
        'text': '#000000',
        'primary': '#2196F3',
        'secondary': '#FF5722',
        'surface': '#F5F5F5'
    })
    return chart


@pytest.fixture
def accessible_chart_instance(qtbot):
    """Create accessible chart instance for testing."""
    from PyQt6.QtWidgets import QWidget
    
    class TestChart(QWidget, AccessibleChartMixin):
        def __init__(self):
            QWidget.__init__(self)
            AccessibleChartMixin.__init__(self)
            self._data = [
                {'value': 10, 'label': 'Point 1'},
                {'value': 20, 'label': 'Point 2'},
                {'value': 15, 'label': 'Point 3'}
            ]
            self._title = "Test Chart"
    
    chart = TestChart()
    qtbot.addWidget(chart)
    return chart


class TestVisualizationAccessibilityManager:
    """Test VisualizationAccessibilityManager."""
    
    def test_initialization(self, accessibility_manager):
        """Test manager initialization."""
        assert accessibility_manager.screen_reader_manager is not None
        assert accessibility_manager.keyboard_navigation is not None
        assert accessibility_manager.color_accessibility is not None
        assert accessibility_manager.wcag_validator is not None
    
    def test_make_chart_accessible(self, accessibility_manager, mock_chart):
        """Test making chart accessible."""
        chart_config = {
            'type': 'line',
            'title': 'Test Chart'
        }
        
        # Mock the create_data_table method to avoid Qt widget creation
        with patch('src.ui.accessibility.alternative_representations.AlternativeRepresentations.create_data_table') as mock_create_table:
            mock_create_table.return_value = MagicMock()
            
            accessible_chart = accessibility_manager.make_chart_accessible(
                mock_chart, chart_config
            )
            
            assert isinstance(accessible_chart, AccessibleChart)
            assert accessible_chart.chart == mock_chart
            assert accessible_chart.chart_type == 'line'
            assert accessible_chart.title == 'Test Chart'
            
            # Verify accessibility methods were called
            mock_chart.setAccessibleName.assert_called()
            mock_chart.setFocusPolicy.assert_called_with(Qt.FocusPolicy.StrongFocus)
    
    def test_accessibility_validation(self, accessibility_manager, mock_chart):
        """Test accessibility validation."""
        accessible_chart = AccessibleChart(
            chart=mock_chart,
            chart_type='line',
            title='Test Chart',
            description='Test description'
        )
        
        report = accessibility_manager.validate_accessibility(accessible_chart)
        
        assert report is not None
        assert hasattr(report, 'is_compliant')
        assert hasattr(report, 'get_failure_summary')


class TestWCAGValidator:
    """Test WCAG compliance validator."""
    
    def test_wcag_validation(self):
        """Test WCAG validation process."""
        validator = WCAGValidator()
        
        mock_chart = AccessibleChart(
            chart=Mock(),
            chart_type='line',
            title='Test Chart',
            description='Test description',
            keyboard_shortcuts={'Tab': 'Next element'}
        )
        
        report = validator.validate(mock_chart)
        
        assert report is not None
        assert len(report.test_results) > 0
        
        # Check for specific tests
        test_names = [r.name for r in report.test_results]
        assert 'Non-text Content' in test_names
        assert 'Keyboard' in test_names
        assert 'Contrast (Minimum)' in test_names
    
    def test_contrast_requirements(self):
        """Test contrast ratio requirements."""
        validator = WCAGValidator()
        
        assert validator.contrast_requirements['normal_text'] == 4.5
        assert validator.contrast_requirements['large_text'] == 3.0
        assert validator.contrast_requirements['graphics'] == 3.0


class TestColorAccessibilityManager:
    """Test color accessibility features."""
    
    def test_contrast_calculation(self):
        """Test color contrast calculation."""
        manager = ColorAccessibilityManager()
        
        # Test known contrast ratios
        result = manager.calculate_contrast('#000000', '#FFFFFF')
        assert result.ratio == pytest.approx(21.0, 0.1)
        assert result.passes_aa
        assert result.passes_aaa
        
        # Test insufficient contrast
        result = manager.calculate_contrast('#777777', '#999999')
        assert result.ratio < 4.5
        assert not result.passes_aa
    
    def test_colorblind_palettes(self):
        """Test colorblind-friendly palettes."""
        manager = ColorAccessibilityManager()
        
        # Test available palettes
        for palette_type in ['deuteranopia', 'protanopia', 'tritanopia']:
            palette = manager.get_colorblind_palette(palette_type)
            assert isinstance(palette, list)
            assert len(palette) >= 5
            
            # All colors should be hex strings
            for color in palette:
                assert color.startswith('#')
                assert len(color) == 7
    
    def test_high_contrast_palette(self):
        """Test high contrast palette generation."""
        manager = ColorAccessibilityManager()
        
        base_colors = {
            'background': '#F5E6D3',
            'text_primary': '#6B4226',
            'primary': '#FF8C42'
        }
        
        high_contrast = manager.create_high_contrast_palette(base_colors)
        
        # Check contrast improvements
        assert high_contrast['background'] == '#FFFFFF'
        assert high_contrast['text_primary'] == '#000000'
        
        # Verify all text colors have sufficient contrast
        bg = high_contrast['background']
        for key, color in high_contrast.items():
            if 'text' in key:
                result = manager.calculate_contrast(color, bg)
                assert result.passes_aa
    
    def test_color_enhancement(self):
        """Test color enhancement for contrast."""
        manager = ColorAccessibilityManager()
        
        # Test enhancing a color that doesn't meet contrast
        enhanced = manager.enhance_color_for_contrast(
            '#CCCCCC', '#FFFFFF', target_ratio=4.5
        )
        
        # Enhanced color should meet target ratio
        result = manager.calculate_contrast(enhanced, '#FFFFFF')
        assert result.ratio >= 4.5


class TestScreenReaderSupport:
    """Test screen reader functionality."""
    
    def test_chart_description_creation(self):
        """Test creation of chart descriptions."""
        manager = ScreenReaderManager()
        
        description = manager.create_chart_description(
            chart_type="line",
            data_summary="10 data points from Jan to Dec",
            key_insights=["Upward trend", "Peak in July"]
        )
        
        assert "line chart" in description
        assert "10 data points" in description
        assert "Upward trend" in description
    
    def test_announcement_queue(self):
        """Test announcement queuing system."""
        manager = ScreenReaderManager()
        
        # Queue announcements
        manager.announce("First announcement")
        manager.announce("Second announcement")
        manager.announce("Priority announcement", priority=True)
        
        # Priority announcement should be first
        assert manager.announcement_queue[0] == "Priority announcement"
        assert len(manager.announcement_queue) == 3


class TestKeyboardNavigation:
    """Test keyboard navigation features."""
    
    def test_default_shortcuts(self):
        """Test default keyboard shortcuts."""
        manager = KeyboardNavigationManager()
        shortcuts = manager.get_default_shortcuts()
        
        # Check essential shortcuts exist
        assert 'Tab' in shortcuts
        assert 'Left Arrow' in shortcuts
        assert 'Right Arrow' in shortcuts
        assert 'Enter' in shortcuts
        assert 'A' in shortcuts  # Announce
        assert 'H' in shortcuts  # Help
    
    def test_shortcut_descriptions(self):
        """Test shortcut descriptions."""
        manager = KeyboardNavigationManager()
        
        desc = manager.get_shortcut_description('navigate_left')
        assert 'left' in desc.lower() or 'previous' in desc.lower()
        
        desc = manager.get_shortcut_description('announce_current')
        assert 'announce' in desc.lower()


class TestAccessibleChartMixin:
    """Test AccessibleChartMixin functionality."""
    
    def test_basic_accessibility_setup(self, accessible_chart_instance):
        """Test basic accessibility setup."""
        chart = accessible_chart_instance
        
        assert chart.get_accessible_name() == "Test Chart"
        assert "3 data points" in chart.get_accessible_description()
        assert chart.supports_high_contrast()
    
    def test_keyboard_navigation(self, accessible_chart_instance):
        """Test keyboard navigation through data points."""
        chart = accessible_chart_instance
        chart.enable_accessibility()
        
        # Test navigation
        assert chart.navigate_next()
        assert chart._current_focus_index == 1
        
        assert chart.navigate_next()
        assert chart._current_focus_index == 2
        
        assert not chart.navigate_next()  # At end
        
        assert chart.navigate_previous()
        assert chart._current_focus_index == 1
        
        assert chart.navigate_first()
        assert chart._current_focus_index == 0
        
        assert chart.navigate_last()
        assert chart._current_focus_index == 2
    
    def test_high_contrast_toggle(self, accessible_chart_instance):
        """Test high contrast mode toggle."""
        chart = accessible_chart_instance
        
        assert not chart._high_contrast_mode
        
        chart.toggle_high_contrast()
        assert chart._high_contrast_mode
        
        chart.toggle_high_contrast()
        assert not chart._high_contrast_mode
    
    def test_announcements(self, accessible_chart_instance):
        """Test accessibility announcements."""
        chart = accessible_chart_instance
        chart.enable_accessibility()
        
        # Test announcement creation
        announcement = chart._create_element_announcement(0)
        assert "Data point 1 of 3" in announcement


class TestAlternativeRepresentations:
    """Test alternative representations."""
    
    def test_data_table_creation(self, qtbot):
        """Test accessible data table creation."""
        from src.ui.accessibility.alternative_representations import (
            AccessibleDataTable
        )
        
        # Create sample data
        data = pd.DataFrame({
            'Date': pd.date_range('2024-01-01', periods=5),
            'Heart Rate': [72, 75, 71, 78, 74],
            'Steps': [8000, 10000, 7500, 9000, 8500]
        })
        
        table = AccessibleDataTable(data, "Health Metrics")
        qtbot.addWidget(table)
        
        assert table.rowCount() == 5
        assert table.columnCount() == 3
        assert table.accessibleName() == "Health Metrics"
    
    def test_sonification_basic(self):
        """Test basic sonification functionality."""
        from src.ui.accessibility.alternative_representations import (
            DataSonification
        )
        
        sonification = DataSonification()
        
        # Create simple data series
        data = pd.Series([1, 2, 3, 4, 5], name="Test Data")
        
        audio_bytes = sonification.sonify_series(data)
        
        assert isinstance(audio_bytes, bytes)
        assert len(audio_bytes) > 0
        
        # Audio should be valid WAV format
        assert audio_bytes.startswith(b'RIFF')
        assert b'WAVE' in audio_bytes[:12]
    
    def test_haptic_feedback_generation(self):
        """Test haptic feedback pattern generation."""
        from src.ui.accessibility.alternative_representations import (
            HapticFeedbackGenerator, HapticPattern
        )
        
        generator = HapticFeedbackGenerator()
        
        # Test single value pattern
        pattern = generator.generate_pattern_for_value(5.0, 0.0, 10.0)
        assert isinstance(pattern, HapticPattern)
        assert pattern.intensity == 0.6  # Medium value
        
        # Test pattern sequence
        data = pd.Series([1, 5, 10, 2, 8])
        patterns = generator.generate_pattern_sequence(data)
        
        assert len(patterns) == 5
        assert all(isinstance(p, HapticPattern) for p in patterns)
        
        # Test encoding
        encoded = generator.encode_for_device(patterns)
        assert 'format' in encoded
        assert 'patterns' in encoded
        assert 'total_duration' in encoded
        assert len(encoded['patterns']) == 5


class TestIntegration:
    """Integration tests for accessibility system."""
    
    def test_full_accessibility_workflow(self, accessibility_manager, qtbot):
        """Test complete accessibility workflow."""
        # Create a mock chart widget
        chart = Mock()
        chart.get_data_summary = Mock(return_value="Test summary")
        chart.get_key_insights = Mock(return_value=["Insight 1"])
        chart.setProperty = Mock()
        chart.setAccessibleName = Mock()
        chart.setAccessibleDescription = Mock()
        chart.setFocusPolicy = Mock()
        
        # Mock get_colors to return a dict
        chart.get_colors = Mock(return_value={
            'foreground': '#212121',
            'background': '#FFFFFF'
        })
        
        # Mock the create_data_table method to avoid Qt widget creation
        with patch('src.ui.accessibility.alternative_representations.AlternativeRepresentations.create_data_table') as mock_create_table:
            mock_create_table.return_value = MagicMock()
            
            # Make it accessible
            config = {'type': 'line', 'title': 'Test Chart'}
            accessible_chart = accessibility_manager.make_chart_accessible(chart, config)
            
            # Validate accessibility
            report = accessibility_manager.validate_accessibility(accessible_chart)
            
            # Check results
            assert accessible_chart is not None
            assert report is not None
            
            # Verify methods were called
            chart.setAccessibleName.assert_called()
            chart.setFocusPolicy.assert_called()
    
    def test_wcag_compliance_reporting(self):
        """Test WCAG compliance reporting."""
        from src.ui.accessibility import AccessibilityReport, TestResult
        
        report = AccessibilityReport()
        
        # Add passing tests
        report.add_test_result(TestResult(
            criterion="1.1.1",
            name="Non-text Content", 
            level=WCAGLevel.A,
            passed=True
        ))
        
        # Add failing test
        report.add_test_result(TestResult(
            criterion="1.4.3",
            name="Contrast (Minimum)",
            level=WCAGLevel.AA,
            passed=False,
            details="Insufficient contrast ratio"
        ))
        
        assert not report.is_compliant(WCAGLevel.AA)
        assert len(report.get_failures()) == 1
        assert "Contrast" in report.get_failure_summary()