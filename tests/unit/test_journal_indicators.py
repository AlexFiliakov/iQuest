"""Unit tests for journal entry indicators.

This module tests the journal indicator functionality including:
    - JournalIndicator widget behavior
    - JournalIndicatorService caching and data management
    - JournalIndicatorMixin integration
    - EnhancedCalendarHeatmap indicator display
"""

import pytest
from datetime import date, datetime, timedelta
from unittest.mock import Mock, MagicMock, patch
from PyQt6.QtWidgets import QApplication, QWidget
from PyQt6.QtCore import Qt, QPoint
from PyQt6.QtTest import QTest

from src.ui.journal_indicator import JournalIndicator
from src.analytics.journal_indicator_service import JournalIndicatorService, IndicatorData
from src.ui.journal_indicator_mixin import JournalIndicatorMixin
from src.ui.charts.calendar_heatmap_enhanced import EnhancedCalendarHeatmap
from src.models import JournalEntry


@pytest.fixture
def app():
    """Create QApplication for tests."""
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    return app


@pytest.fixture
def mock_data_access():
    """Create mock data access object."""
    mock = Mock()
    
    # Sample journal entries
    sample_entries = [
        JournalEntry(
            id=1,
            entry_date=date(2024, 1, 15),
            entry_type='daily',
            content='Today was a good day for exercise.',
            created_at=datetime(2024, 1, 15, 20, 0),
            updated_at=datetime(2024, 1, 15, 20, 0)
        ),
        JournalEntry(
            id=2,
            entry_date=date(2024, 1, 15),
            entry_type='daily',
            content='Second entry for today.',
            created_at=datetime(2024, 1, 15, 21, 0),
            updated_at=datetime(2024, 1, 15, 21, 0)
        ),
        JournalEntry(
            id=3,
            entry_date=date(2024, 1, 8),
            entry_type='weekly',
            week_start_date=date(2024, 1, 8),
            content='Weekly reflection on health goals.',
            created_at=datetime(2024, 1, 14, 19, 0),
            updated_at=datetime(2024, 1, 14, 19, 0)
        ),
        JournalEntry(
            id=4,
            entry_date=date(2024, 1, 1),
            entry_type='monthly',
            month_year='2024-01',
            content='January health goals and resolutions.',
            created_at=datetime(2024, 1, 1, 10, 0),
            updated_at=datetime(2024, 1, 1, 10, 0)
        )
    ]
    
    def get_journal_entries(start_date, end_date):
        return [e for e in sample_entries 
                if start_date <= e.entry_date <= end_date]
    
    mock.get_journal_entries = Mock(side_effect=get_journal_entries)
    return mock


class TestJournalIndicator:
    """Test the JournalIndicator widget."""
    
    def test_indicator_creation(self, app):
        """Test creating a journal indicator."""
        indicator = JournalIndicator(
            entry_type='daily',
            count=1,
            preview_text='Test preview'
        )
        
        assert indicator.entry_type == 'daily'
        assert indicator.count == 1
        assert indicator.preview_text == 'Test preview'
        assert indicator.isVisible() is False  # Not shown until explicitly shown
        
    def test_indicator_with_multiple_entries(self, app):
        """Test indicator with badge count."""
        indicator = JournalIndicator(
            entry_type='weekly',
            count=3,
            preview_text='Multiple entries'
        )
        
        assert indicator.count == 3
        # Badge should be visible for count > 1
        
    def test_indicator_hover_effect(self, app):
        """Test hover interaction."""
        indicator = JournalIndicator(entry_type='daily', count=1)
        indicator.show()
        
        # Simulate hover
        indicator.enterEvent(None)
        assert indicator._is_hovered is True
        
        indicator.leaveEvent(None)
        assert indicator._is_hovered is False
        
    def test_indicator_click_signal(self, app):
        """Test click signal emission."""
        indicator = JournalIndicator(entry_type='monthly', count=1)
        indicator.show()
        
        # Connect signal spy
        clicked = False
        def on_clicked():
            nonlocal clicked
            clicked = True
            
        indicator.clicked.connect(on_clicked)
        
        # Simulate click
        QTest.mouseClick(indicator, Qt.MouseButton.LeftButton)
        assert clicked is True
        
    def test_indicator_accessibility(self, app):
        """Test accessibility features."""
        indicator = JournalIndicator(
            entry_type='weekly',
            count=2,
            preview_text='Test'
        )
        
        # Check accessible name
        assert 'weekly journal entries' in indicator.accessibleName().lower()
        assert '2' in indicator.accessibleName()
        
        # Check keyboard navigation
        assert indicator.focusPolicy() == Qt.FocusPolicy.TabFocus
        
    def test_indicator_update(self, app):
        """Test updating indicator data."""
        indicator = JournalIndicator(entry_type='daily', count=1)
        
        # Update with new data
        indicator.update_indicator(count=3, preview_text='Updated preview')
        
        assert indicator.count == 3
        assert indicator.preview_text == 'Updated preview'


class TestJournalIndicatorService:
    """Test the journal indicator service."""
    
    def test_service_initialization(self, mock_data_access):
        """Test service initialization."""
        service = JournalIndicatorService(mock_data_access)
        
        assert service.data_access == mock_data_access
        assert len(service._cache) == 0
        assert service._cache_timestamp is None
        
    def test_get_indicators_for_date_range(self, mock_data_access):
        """Test getting indicators for a date range."""
        service = JournalIndicatorService(mock_data_access)
        
        # Get indicators for January 2024
        indicators = service.get_indicators_for_date_range(
            date(2024, 1, 1),
            date(2024, 1, 31)
        )
        
        # Should have indicators for the dates with entries
        assert len(indicators) > 0
        
        # Check daily entry indicator
        daily_key = '2024-01-15'
        assert daily_key in indicators
        assert indicators[daily_key].count == 2  # Two daily entries
        assert indicators[daily_key].entry_type == 'daily'
        
        # Check weekly entry indicator
        weekly_key = '2024-01-08_weekly'
        assert weekly_key in indicators
        assert indicators[weekly_key].count == 1
        assert indicators[weekly_key].entry_type == 'weekly'
        
        # Check monthly entry indicator
        monthly_key = '2024-01-01_monthly'
        assert monthly_key in indicators
        assert indicators[monthly_key].count == 1
        assert indicators[monthly_key].entry_type == 'monthly'
        
    def test_get_indicator_for_specific_date(self, mock_data_access):
        """Test getting indicator for a specific date."""
        service = JournalIndicatorService(mock_data_access)
        
        # Get daily indicator
        indicator = service.get_indicator_for_date(date(2024, 1, 15), 'daily')
        assert indicator is not None
        assert indicator.count == 2
        
        # Get non-existent indicator
        indicator = service.get_indicator_for_date(date(2024, 1, 20), 'daily')
        assert indicator is None
        
    def test_cache_functionality(self, mock_data_access):
        """Test caching behavior."""
        service = JournalIndicatorService(mock_data_access)
        
        # First call should populate cache
        indicators1 = service.get_indicators_for_date_range(
            date(2024, 1, 1),
            date(2024, 1, 31)
        )
        assert mock_data_access.get_journal_entries.call_count == 1
        
        # Second call should use cache
        indicators2 = service.get_indicators_for_date_range(
            date(2024, 1, 1),
            date(2024, 1, 31)
        )
        assert mock_data_access.get_journal_entries.call_count == 1  # No new call
        assert indicators1 == indicators2
        
    def test_entry_saved_update(self, mock_data_access):
        """Test updating cache when entry is saved."""
        service = JournalIndicatorService(mock_data_access)
        
        # Populate cache
        service.get_indicators_for_date_range(date(2024, 1, 1), date(2024, 1, 31))
        
        # Simulate new entry saved
        new_entry = JournalEntry(
            id=5,
            entry_date=date(2024, 1, 20),
            entry_type='daily',
            content='New entry'
        )
        
        # Spy on signal
        signal_emitted = []
        service.indicators_updated.connect(lambda key: signal_emitted.append(key))
        
        service.on_entry_saved(new_entry)
        
        # Check signal was emitted
        assert len(signal_emitted) == 1
        assert signal_emitted[0] == '2024-01-20'
        
    def test_preview_text_extraction(self, mock_data_access):
        """Test preview text extraction."""
        service = JournalIndicatorService(mock_data_access)
        
        # Test normal text
        preview = service._extract_preview("This is a test entry with some content.")
        assert preview == "This is a test entry with some content."
        
        # Test long text truncation
        long_text = "A" * 200
        preview = service._extract_preview(long_text)
        assert len(preview) <= service.PREVIEW_LENGTH + 3  # +3 for "..."
        assert preview.endswith("...")
        
        # Test whitespace handling
        text_with_spaces = "This   has    extra     spaces"
        preview = service._extract_preview(text_with_spaces)
        assert preview == "This has extra spaces"


class TestDashboardWidget(QWidget, JournalIndicatorMixin):
    """Test widget that uses the journal indicator mixin."""
    
    def __init__(self, data_access):
        super().__init__()
        self.init_journal_indicators(data_access)


class TestJournalIndicatorMixin:
    """Test the journal indicator mixin."""
    
    def test_mixin_initialization(self, app, mock_data_access):
        """Test mixin initialization."""
        widget = TestDashboardWidget(mock_data_access)
        
        assert hasattr(widget, '_indicator_service')
        assert hasattr(widget, '_active_indicators')
        assert hasattr(widget, 'journal_entry_requested')
        
    def test_add_indicator_to_widget(self, app, mock_data_access):
        """Test adding indicator to a widget."""
        dashboard = TestDashboardWidget(mock_data_access)
        
        # Create a dummy widget to add indicator to
        cell_widget = QWidget()
        cell_widget.resize(100, 50)
        
        # Add indicator for a date with entries
        dashboard.add_journal_indicator_to_widget(
            cell_widget,
            date(2024, 1, 15),
            'daily'
        )
        
        # Check indicator was created
        assert len(dashboard._active_indicators) == 1
        
        # Check positioning
        indicator = list(dashboard._active_indicators.values())[0]
        assert indicator.parent() == cell_widget
        assert indicator.isVisible()
        
    def test_indicator_click_handling(self, app, mock_data_access):
        """Test handling indicator clicks."""
        dashboard = TestDashboardWidget(mock_data_access)
        
        # Track signal emission
        signal_data = []
        dashboard.journal_entry_requested.connect(
            lambda d, t: signal_data.append((d, t))
        )
        
        # Add indicator
        cell_widget = QWidget()
        cell_widget.resize(100, 50)
        dashboard.add_journal_indicator_to_widget(
            cell_widget,
            date(2024, 1, 15),
            'daily'
        )
        
        # Click the indicator
        indicator = list(dashboard._active_indicators.values())[0]
        QTest.mouseClick(indicator, Qt.MouseButton.LeftButton)
        
        # Check signal was emitted
        assert len(signal_data) == 1
        assert signal_data[0] == (date(2024, 1, 15), 'daily')
        
    def test_refresh_indicators(self, app, mock_data_access):
        """Test refreshing indicators."""
        dashboard = TestDashboardWidget(mock_data_access)
        
        # Add some indicators
        cell1 = QWidget()
        cell1.resize(100, 50)
        dashboard.add_journal_indicator_to_widget(cell1, date(2024, 1, 15), 'daily')
        
        initial_count = len(dashboard._active_indicators)
        
        # Refresh
        dashboard.refresh_journal_indicators()
        
        # Should recreate indicators
        assert len(dashboard._active_indicators) == initial_count


class TestEnhancedCalendarHeatmap:
    """Test the enhanced calendar heatmap with indicators."""
    
    def test_enhanced_heatmap_creation(self, app, mock_data_access):
        """Test creating enhanced heatmap."""
        heatmap = EnhancedCalendarHeatmap(
            monthly_calculator=None,
            data_access=mock_data_access
        )
        
        assert heatmap._has_journal_support is True
        assert hasattr(heatmap, '_indicator_service')
        assert hasattr(heatmap, 'journal_entry_requested')
        
    def test_heatmap_without_journal_support(self, app):
        """Test heatmap without journal support."""
        heatmap = EnhancedCalendarHeatmap(
            monthly_calculator=None,
            data_access=None  # No data access = no journal support
        )
        
        assert heatmap._has_journal_support is False
        
    @patch('src.ui.charts.calendar_heatmap_enhanced.JournalIndicator')
    def test_indicator_creation_on_paint(self, mock_indicator_class, app, mock_data_access):
        """Test that indicators are created during paint event."""
        heatmap = EnhancedCalendarHeatmap(
            monthly_calculator=None,
            data_access=mock_data_access
        )
        
        # Set up some cell rectangles
        heatmap._cell_rects = {
            date(2024, 1, 15): MagicMock(),
            date(2024, 1, 20): MagicMock()
        }
        
        # Trigger indicator painting
        heatmap._paint_journal_indicators()
        
        # Check that indicator was created for date with entry
        assert mock_indicator_class.called
        
    def test_journal_manager_connection(self, app, mock_data_access):
        """Test connecting to journal manager."""
        heatmap = EnhancedCalendarHeatmap(
            monthly_calculator=None,
            data_access=mock_data_access
        )
        
        # Mock journal manager
        journal_manager = Mock()
        journal_manager.entrySaved = Mock()
        journal_manager.entryDeleted = Mock()
        
        # Connect
        heatmap.connect_to_journal_manager(journal_manager)
        
        # Verify connections were made
        assert journal_manager.entrySaved.connect.called
        assert journal_manager.entryDeleted.connect.called