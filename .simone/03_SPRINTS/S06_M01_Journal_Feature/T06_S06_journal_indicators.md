---
task_id: T06_S06
sprint_sequence_id: S06
status: open
complexity: Medium
last_updated: 2025-01-28T00:00:00Z
dependencies: ["T01_S06", "T03_S06"]
---

# Task: Journal Entry Indicators on Dashboards

## Description
Add visual indicators to daily, weekly, and monthly dashboard views to show which time periods have associated journal entries. This helps users quickly identify dates with contextual notes and navigate to them.

## Goal / Objectives
- Add journal indicators to all dashboard views
- Make indicators clickable to open journal entries
- Use consistent visual design across views
- Ensure indicators don't clutter the interface
- Support different indicator styles based on entry type

## Acceptance Criteria
- [ ] Daily view shows journal icons on dates with entries
- [ ] Weekly view indicates weeks with journal entries
- [ ] Monthly view shows journal indicators
- [ ] Clicking indicator opens journal entry
- [ ] Different icons for daily/weekly/monthly entries
- [ ] Tooltip shows entry preview on hover
- [ ] Indicators follow warm color scheme
- [ ] Performance impact <100ms on view load
- [ ] Indicators update when entries added/removed

## Implementation Analysis

### Indicator UI Pattern
**Options:**
1. **Icon Overlay** - Small icon in corner of date/card
   - Pros: Minimal space usage, clear association
   - Cons: May be missed, overlap concerns
2. **Badge System** - Colored dot with count
   - Pros: Very compact, shows quantity
   - Cons: Less descriptive, needs legend
3. **Integrated Symbols** - Journal icon within date display
   - Pros: Natural integration, accessible
   - Cons: May affect layout, needs careful design

**Recommendation:** Icon Overlay with Badge Count (#1+#2) - Best of both

### Performance Strategy
**Options:**
- **Smart Caching** - Preload visible + nearby dates
   - Pros: Balanced performance, good UX
   - Cons: Cache management needed

### Animation Approach
**Options:**
- **CSS Transitions** - Pure CSS hover effects
   - Pros: Performant, smooth, GPU accelerated
   - Cons: Limited to simple animations

## Detailed Subtasks

### 1. JournalIndicator Widget Design
- [ ] Create src/ui/journal_indicator.py:
  ```python
  class JournalIndicator(QWidget):
      clicked = pyqtSignal(date, str)  # date, entry_type
      
      def __init__(self, entry_types: List[str], parent=None):
          super().__init__(parent)
          self.entry_types = entry_types
          self.setup_ui()
  ```
- [ ] Define indicator properties:
  - [ ] Size modes: Compact (16px), Normal (24px), Large (32px)
  - [ ] Display modes: Icon only, Icon + badge, Text
  - [ ] States: Default, Hover, Active, Disabled
- [ ] Implement state management:
  - [ ] Track entry types present
  - [ ] Handle multiple entries per date
  - [ ] Update visual state dynamically

### 2. Icon Design System
- [ ] Create SVG icons for entry types:
  - [ ] Daily: 📓 Notebook icon
  - [ ] Weekly: 📅 Calendar week icon  
  - [ ] Monthly: 📊 Calendar month icon
  - [ ] Multiple: Stack/layer effect
- [ ] Design icon variations:
  ```python
  ICON_PATHS = {
      'daily': 'assets/icons/journal_daily.svg',
      'weekly': 'assets/icons/journal_weekly.svg',
      'monthly': 'assets/icons/journal_monthly.svg',
      'multiple': 'assets/icons/journal_multiple.svg'
  }
  ```
- [ ] Create color variations:
  - [ ] Default: #8B7355 (warm brown)
  - [ ] Hover: #FF8C42 (warm orange)
  - [ ] Has content: #95C17B (success green)
- [ ] Export icons in multiple resolutions

### 3. Indicator Positioning System
- [ ] Create IndicatorPositioner class:
  ```python
  class IndicatorPositioner:
      def calculate_position(self, parent_rect: QRect, 
                           indicator_size: QSize,
                           anchor: AnchorPoint) -> QPoint:
          # Smart positioning to avoid overlaps
  ```
- [ ] Define anchor points:
  - [ ] TOP_RIGHT: Default for daily view
  - [ ] BOTTOM_RIGHT: For cards/tiles
  - [ ] CENTER: For empty states
- [ ] Implement collision detection:
  - [ ] Check for overlapping indicators
  - [ ] Adjust position if needed
  - [ ] Maintain visual hierarchy

### 4. Daily View Integration
- [ ] Modify DailyTrendIndicator to support indicators:
  - [ ] Add indicator container layer
  - [ ] Position indicators in date headers
  - [ ] Handle date cell sizing
- [ ] Implement indicator data loading:
  ```python
  def load_journal_indicators(self, start_date, end_date):
      entries = self.journal_db.get_entry_dates(start_date, end_date)
      self.indicator_cache.update(entries)
  ```
- [ ] Add click handling:
  - [ ] Connect indicator clicks to journal editor
  - [ ] Pass date and entry type
  - [ ] Handle missing entries gracefully

### 5. Weekly View Integration
- [ ] Update WeekOverWeekWidget:
  - [ ] Add indicator to week summary cards
  - [ ] Show count of entries in week
  - [ ] Different icon for week vs daily entries
- [ ] Create weekly indicator aggregation:
  ```python
  def aggregate_weekly_entries(self, week_start):
      daily_count = self.count_entries(week_start, week_start + 6, 'daily')
      has_weekly = self.has_entry(week_start, 'weekly')
      return WeeklyIndicatorData(daily_count, has_weekly)
  ```
- [ ] Style for card integration:
  - [ ] Position in card header
  - [ ] Subtle appearance
  - [ ] Clear hover state

### 6. Monthly View Integration  
- [ ] Enhance MonthOverMonthWidget:
  - [ ] Add indicators to calendar cells
  - [ ] Show in monthly summary section
  - [ ] Handle month-level entries
- [ ] Create calendar cell renderer:
  ```python
  class CalendarCellRenderer:
      def paint(self, painter, cell_rect, date, has_journal):
          # Draw date number
          # Draw journal indicator if present
          if has_journal:
              self.draw_indicator(painter, cell_rect)
  ```
- [ ] Implement heatmap overlay:
  - [ ] Combine health metrics with journal presence
  - [ ] Use opacity for layering
  - [ ] Maintain readability

### 7. Preview Tooltip System
- [ ] Create JournalPreviewTooltip(QToolTip):
  ```python
  class JournalPreviewTooltip(QWidget):
      def __init__(self):
          self.preview_text = QLabel()
          self.entry_date = QLabel()
          self.entry_type = QLabel()
  ```
- [ ] Implement preview generation:
  - [ ] Load first 200 characters
  - [ ] Format with ellipsis
  - [ ] Show entry metadata
- [ ] Add rich formatting:
  - [ ] Entry type badge
  - [ ] Date formatting
  - [ ] Word count
- [ ] Handle async loading:
  - [ ] Show loading state
  - [ ] Cancel on mouse leave
  - [ ] Cache loaded previews

### 8. Animation Implementation
- [ ] Define CSS animations:
  ```css
  .journal-indicator {
      transition: all 0.2s ease;
      opacity: 0.8;
  }
  .journal-indicator:hover {
      transform: scale(1.1);
      opacity: 1.0;
      filter: drop-shadow(0 2px 4px rgba(0,0,0,0.1));
  }
  ```
- [ ] Add pulse animation for new entries:
  ```python
  @keyframes pulse {
      0% { transform: scale(1); }
      50% { transform: scale(1.05); }
      100% { transform: scale(1); }
  }
  ```
- [ ] Implement entrance animations:
  - [ ] Fade in when view loads
  - [ ] Stagger for multiple indicators
  - [ ] Smooth transitions

### 9. Caching System
- [ ] Create IndicatorCache class:
  ```python
  class IndicatorCache:
      def __init__(self, max_size=1000):
          self.cache = OrderedDict()
          self.max_size = max_size
          
      def get_indicators(self, date_range):
          # Check cache first, load missing
  ```
- [ ] Implement cache strategies:
  - [ ] LRU eviction
  - [ ] Preload adjacent months
  - [ ] Background refresh
- [ ] Add cache warming:
  - [ ] Load current month on startup
  - [ ] Predictive loading based on navigation
  - [ ] Batch database queries

### 10. Real-time Updates
- [ ] Create IndicatorUpdateService:
  ```python
  class IndicatorUpdateService(QObject):
      indicatorsChanged = pyqtSignal(list)  # Changed dates
      
      def on_journal_saved(self, date, entry_type):
          self.update_indicator(date, entry_type)
          self.indicatorsChanged.emit([date])
  ```
- [ ] Connect to journal events:
  - [ ] Entry created
  - [ ] Entry updated  
  - [ ] Entry deleted
- [ ] Implement efficient updates:
  - [ ] Batch multiple changes
  - [ ] Debounce rapid updates
  - [ ] Update only visible indicators

### 11. Accessibility Implementation
- [ ] Add ARIA labels:
  ```python
  self.indicator.setAccessibleName(
      f"Journal entry available for {date.toString('MMMM d, yyyy')}"
  )
  ```
- [ ] Implement keyboard navigation:
  - [ ] Tab to focus indicators
  - [ ] Enter/Space to activate
  - [ ] Escape to close tooltip

### 12. Performance Optimization
- [ ] Implement viewport culling:
  ```python
  def update_visible_indicators(self):
      visible_dates = self.get_visible_date_range()
      self.hide_indicators_outside(visible_dates)
      self.show_indicators_inside(visible_dates)
  ```
- [ ] Add render batching:
  - [ ] Group indicator updates
  - [ ] Use single repaint
  - [ ] Minimize layout recalculations
- [ ] Profile and optimize:
  - [ ] Measure render time
  - [ ] Track memory usage
  - [ ] Optimize icon loading

### 13. Testing Implementation
- [ ] Create tests/unit/test_journal_indicators.py:
  - [ ] Test indicator positioning
  - [ ] Test state management
  - [ ] Test tooltip content
  - [ ] Test animations
  - [ ] Test cache behavior

### 14. Documentation
- [ ] Create indicator style guide:
  - [ ] Visual examples
  - [ ] Usage guidelines
  - [ ] Accessibility notes
- [ ] Add user documentation:
  - [ ] What indicators mean
  - [ ] How to interact
  - [ ] Keyboard shortcuts
- [ ] Create developer docs:
  - [ ] API reference
  - [ ] Integration guide
  - [ ] Performance tips

## Output Log
[2025-01-28 00:00:00] Task created - Visual indicators connect journal entries to health data