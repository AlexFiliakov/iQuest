---
task_id: T09_S06
sprint_sequence_id: S06
status: open
complexity: Medium
last_updated: 2025-01-28T00:00:00Z
dependencies: ["T02_S06", "T08_S06"]
---

# Task: Journal Tab Integration

## Description
Integrate all journal components into the main application by creating a dedicated Journal tab. This tab should provide access to the editor, search, history, and export features in a cohesive interface that follows the application's design patterns.

## Goal / Objectives
- Create complete Journal tab in main window
- Integrate all journal components seamlessly
- Follow existing tab navigation patterns
- Ensure consistent styling with other tabs
- Provide intuitive layout for all journal features

## Acceptance Criteria
- [ ] Journal tab appears in main navigation
- [ ] Tab contains editor and history sections
- [ ] Search bar prominently placed
- [ ] Export button easily accessible
- [ ] Layout responsive to window resizing
- [ ] Keyboard shortcuts work (Alt+J for tab)
- [ ] Tab state preserved on switch
- [ ] Loading states handled gracefully
- [ ] Help documentation accessible

## Implementation Analysis

### Layout Strategy
**Options:**
1. **Split View** - Editor left, history right
   - Pros: See both simultaneously, flexible
   - Cons: May feel cramped on small screens
2. **Stacked View** - Toggle between editor/history
   - Pros: Full space for each view
   - Cons: Can't reference while writing
3. **Master-Detail** - List left, editor right
   - Pros: Familiar pattern, efficient
   - Cons: Less space for editor

**Recommendation:** Split View with Collapsible Panels (#1) - Most flexible

### Navigation Integration
**Options:**
1. **Top-level Tab** - Equal to other main tabs
   - Pros: Easy discovery, prominent
   - Cons: Adds to tab clutter
2. **Sub-tab Under Health** - Nested navigation
   - Pros: Logical grouping
   - Cons: Less discoverable
3. **Floating Window** - Separate journal window
   - Pros: More space, focus mode
   - Cons: Window management complexity

**Recommendation:** Top-level Tab (#1) - Best discoverability

### State Management
**Options:**
1. **Local State** - Each component manages own state
   - Pros: Simple, decoupled
   - Cons: Hard to coordinate
2. **Centralized Store** - Redux-like pattern
   - Pros: Predictable, debuggable
   - Cons: More complex setup
3. **Context/Service** - Shared journal service
   - Pros: Clean API, testable
   - Cons: Service lifecycle management

**Recommendation:** Context/Service (#3) - Clean architecture

## Detailed Subtasks

### 1. Journal Tab Architecture
- [ ] Create src/ui/journal_tab_widget.py:
  ```python
  class JournalTabWidget(QWidget):
      def __init__(self, parent=None):
          super().__init__(parent)
          self.journal_service = JournalService()
          self.setup_ui()
          self.setup_connections()
  ```
- [ ] Define tab structure:
  - [ ] Top toolbar
  - [ ] Main content area (splitter)
  - [ ] Status bar
  - [ ] Floating action buttons
- [ ] Implement service layer:
  ```python
  class JournalService(QObject):
      entryChanged = pyqtSignal(int)
      
      def __init__(self):
          self.db = JournalDatabase()
          self.current_entry = None
  ```
- [ ] Add state management:
  - [ ] Current entry
  - [ ] View mode
  - [ ] Filter state
  - [ ] UI preferences

### 2. Layout Implementation
- [ ] Create main layout structure:
  ```python
  def setup_ui(self):
      # Main vertical layout
      main_layout = QVBoxLayout(self)
      
      # Toolbar
      self.toolbar = self.create_toolbar()
      main_layout.addWidget(self.toolbar)
      
      # Content splitter
      self.splitter = QSplitter(Qt.Horizontal)
      self.editor_panel = self.create_editor_panel()
      self.history_panel = self.create_history_panel()
      
      self.splitter.addWidget(self.editor_panel)
      self.splitter.addWidget(self.history_panel)
  ```
- [ ] Configure splitter:
  - [ ] Default sizes (60/40 split)
  - [ ] Minimum sizes
  - [ ] Collapsible panels
  - [ ] Save/restore position
- [ ] Add responsive breakpoints:
  - [ ] <1200px: Stack vertically
  - [ ] <800px: Hide history by default
  - [ ] Mobile: Full screen editor

### 3. Toolbar Design
- [ ] Create JournalToolbar:
  ```python
  class JournalToolbar(QToolBar):
      def __init__(self):
          super().__init__()
          self.setMovable(False)
          self.setStyleSheet(TOOLBAR_STYLE)
  ```
- [ ] Add primary actions:
  - [ ] New Entry button (prominent)
  - [ ] Save button (when editing)
  - [ ] Search toggle
  - [ ] View mode selector
  - [ ] Export menu
- [ ] Implement search integration:
  - [ ] Expandable search bar
  - [ ] Search scope selector
  - [ ] Clear search button
- [ ] Style with warm theme:
  ```css
  QToolBar {
      background-color: #FFF8F0;
      border-bottom: 2px solid #E8DCC8;
      padding: 8px 16px;
  }
  ```

### 4. Editor Panel Integration
- [ ] Create EditorPanel container:
  ```python
  class EditorPanel(QWidget):
      def __init__(self, journal_service):
          self.service = journal_service
          self.editor = JournalEditorWidget()
          self.setup_panel()
  ```
- [ ] Add panel header:
  - [ ] Current date display
  - [ ] Entry type selector
  - [ ] Quick actions menu
- [ ] Implement editor modes:
  - [ ] New entry mode
  - [ ] Edit mode
  - [ ] Read-only mode
  - [ ] Quick note mode
- [ ] Add panel controls:
  - [ ] Collapse/expand button
  - [ ] Fullscreen toggle
  - [ ] Settings menu

### 5. History Panel Integration
- [ ] Create HistoryPanel container:
  ```python
  class HistoryPanel(QWidget):
      def __init__(self, journal_service):
          self.service = journal_service
          self.history = JournalHistoryWidget()
          self.setup_panel()
  ```
- [ ] Add panel features:
  - [ ] Quick filters bar
  - [ ] View mode toggle
  - [ ] Sort options
- [ ] Connect to editor:
  - [ ] Click to load entry
  - [ ] Double-click to edit
  - [ ] Context menu actions
- [ ] Add panel states:
  - [ ] Normal view
  - [ ] Search results
  - [ ] Filtered view

### 6. View Mode Management
- [ ] Create ViewModeManager:
  ```python
  class ViewModeManager:
      MODES = {
          'split': {'editor': True, 'history': True},
          'editor': {'editor': True, 'history': False},
          'history': {'editor': False, 'history': True},
          'focus': {'editor': True, 'history': False, 'fullscreen': True}
      }
  ```
- [ ] Implement mode switching:
  - [ ] Smooth animations
  - [ ] Preserve content state
  - [ ] Update toolbar
- [ ] Add view shortcuts:
  - [ ] F6: Toggle split
  - [ ] F7: Editor only
  - [ ] F8: History only
  - [ ] F11: Focus mode
- [ ] Save preferences:
  - [ ] Last used mode
  - [ ] Panel sizes
  - [ ] Sort preferences

### 7. Search Integration
- [ ] Create unified search bar:
  ```python
  class JournalSearchBar(QWidget):
      def __init__(self):
          self.search_input = QLineEdit()
          self.scope_selector = QComboBox()
          self.setup_ui()
  ```
- [ ] Implement search scopes:
  - [ ] Current entry
  - [ ] All entries
  - [ ] Date range
  - [ ] Entry type
- [ ] Add search features:
  - [ ] Live preview
  - [ ] Search history
  - [ ] Advanced filters
  - [ ] Result count
- [ ] Connect to components:
  - [ ] Update history view
  - [ ] Highlight in editor
  - [ ] Show result summary

### 8. Export Integration
- [ ] Add export menu:
  ```python
  export_menu = QMenu("Export")
  export_menu.addAction("Export Current Entry...")
  export_menu.addAction("Export Selected...")
  export_menu.addAction("Export All...")
  export_menu.addSeparator()
  export_menu.addAction("Export Settings...")
  ```
- [ ] Implement quick export:
  - [ ] Current entry to PDF
  - [ ] Selection to JSON
  - [ ] Date range export
- [ ] Add export shortcuts:
  - [ ] Ctrl+E: Export current
  - [ ] Ctrl+Shift+E: Export dialog
- [ ] Track export history:
  - [ ] Recent exports
  - [ ] Repeat last export

### 9. Keyboard Navigation
- [ ] Implement tab shortcuts:
  - [ ] Alt+J: Focus journal tab
  - [ ] Ctrl+N: New entry
  - [ ] Ctrl+S: Save entry
  - [ ] Ctrl+F: Focus search
- [ ] Add navigation shortcuts:
  - [ ] Ctrl+Tab: Switch panels
  - [ ] Alt+Left/Right: Navigate history
  - [ ] PageUp/Down: Scroll entries
- [ ] Create command palette:
  ```python
  class CommandPalette(QDialog):
      commands = [
          ("New Daily Entry", "Ctrl+N"),
          ("Search Entries", "Ctrl+F"),
          ("Export to PDF", "Ctrl+E"),
      ]
  ```
- [ ] Implement focus management:
  - [ ] Tab order
  - [ ] Focus indicators
  - [ ] Trap focus in modals

### 10. State Persistence
- [ ] Create state manager:
  ```python
  class JournalStateManager:
      def save_state(self):
          return {
              'splitter_sizes': self.splitter.sizes(),
              'view_mode': self.current_mode,
              'search_query': self.search_bar.text(),
              'filter_state': self.get_filters()
          }
  ```
- [ ] Implement auto-save state:
  - [ ] On tab switch
  - [ ] On app close
  - [ ] Periodic backup
- [ ] Restore state:
  - [ ] On tab open
  - [ ] After crash
  - [ ] User preferences
- [ ] Handle state conflicts:
  - [ ] Version migration
  - [ ] Corrupt state
  - [ ] Reset option

### 11. Performance Optimization
- [ ] Implement lazy loading:
  ```python
  def showEvent(self, event):
      if not self.initialized:
          self.initialize_components()
          self.initialized = True
  ```
- [ ] Add component caching:
  - [ ] Cache rendered widgets
  - [ ] Preload common data
  - [ ] Defer heavy operations
- [ ] Optimize tab switching:
  - [ ] Suspend background updates
  - [ ] Cache last state
  - [ ] Quick resume
- [ ] Monitor performance:
  - [ ] Tab switch time
  - [ ] Memory usage
  - [ ] Component load time

### 12. Help System
- [ ] Create onboarding overlay:
  ```python
  class JournalOnboarding(QWidget):
      def __init__(self):
          self.steps = [
              "Welcome to your health journal!",
              "Create daily, weekly, or monthly entries",
              "Search and organize your thoughts",
              "Export your journal anytime"
          ]
  ```
- [ ] Add contextual help:
  - [ ] Tooltip hints
  - [ ] Feature callouts
  - [ ] Keyboard shortcut overlay
- [ ] Create help documentation:
  - [ ] Getting started guide
  - [ ] Feature overview
  - [ ] FAQ section
- [ ] Track help usage:
  - [ ] Onboarding completion
  - [ ] Help searches
  - [ ] Feature discovery

### 13. Integration Testing
- [ ] Test component integration:
  - [ ] Editor ↔ History sync
  - [ ] Search across components
  - [ ] State consistency
  - [ ] Event propagation
- [ ] Test user workflows:
  - [ ] Create → Edit → Save
  - [ ] Search → Select → Edit
  - [ ] Filter → Export
  - [ ] Navigate → Delete
- [ ] Test edge cases:
  - [ ] Empty states
  - [ ] Large datasets
  - [ ] Concurrent edits
  - [ ] Network issues

### 14. Accessibility
- [ ] Implement screen reader support:
  - [ ] Landmark regions
  - [ ] ARIA labels
  - [ ] Status announcements
- [ ] Add keyboard-only operation:
  - [ ] All features accessible
  - [ ] Clear focus indicators
  - [ ] Skip links
- [ ] Support high contrast:
  - [ ] Detect system theme
  - [ ] Provide toggle
  - [ ] Maintain readability
- [ ] Test with tools:
  - [ ] Screen readers
  - [ ] Keyboard navigation
  - [ ] Color contrast analyzer

### 15. Documentation
- [ ] Create integration guide:
  - [ ] Architecture overview
  - [ ] Component relationships
  - [ ] Event flow diagrams
- [ ] Add user documentation:
  - [ ] Tab overview
  - [ ] Feature guide
  - [ ] Tips and tricks
- [ ] Document customization:
  - [ ] Layout options
  - [ ] Keyboard shortcuts
  - [ ] Export templates

## Output Log
[2025-01-28 00:00:00] Task created - Journal tab provides unified interface for all journal features