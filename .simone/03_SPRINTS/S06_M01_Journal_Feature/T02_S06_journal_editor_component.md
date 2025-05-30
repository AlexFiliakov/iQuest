---
task_id: T02_S06
sprint_sequence_id: S06
status: open
complexity: High
last_updated: 2025-01-28T00:00:00Z
dependencies: ["T01_S06"]
---

# Task: Journal Editor UI Component

## Description
Create the main journal editor component with rich text editing capabilities. This component will be the primary interface for users to create and edit journal entries with support for plain text initially, with consideration for rich text formatting in the future.

## Goal / Objectives
- Build reusable journal editor widget using PyQt6
- Implement character limit (10,000) with visual feedback
- Support daily, weekly, and monthly entry types
- Follow design system from `.simone/01_PROJECT_DOCS/UI_SPECS.md`
- Ensure keyboard accessibility and smooth UX

## Acceptance Criteria
- [ ] JournalEditor widget created as reusable component
- [ ] Character counter shows remaining characters
- [ ] Entry type selector (daily/weekly/monthly) implemented
- [ ] Date picker integrated for entry selection
- [ ] Save/Cancel buttons with proper styling
- [ ] Unsaved changes warning implemented
- [ ] Keyboard shortcuts work (Ctrl+S to save)
- [ ] Component follows design system from `.simone/01_PROJECT_DOCS/UI_SPECS.md`
- [ ] Tab navigation works correctly
- [ ] Widget is responsive to window resizing

## Implementation Analysis

### Text Editor Choice
**Options:**
1. **QTextEdit** - Standard rich text editor
   - Pros: Built-in formatting, familiar interface, undo/redo
   - Cons: Heavy for plain text, formatting complexity
2. **QPlainTextEdit** - Plain text focused
   - Pros: Lightweight, fast, simpler API
   - Cons: No rich text support if needed later
3. **Custom QTextEdit Subclass** - Enhanced plain text editor
   - Pros: Customizable, can add features progressively
   - Cons: More development effort

**Recommendation:** QPlainTextEdit (#2) initially with migration path to QTextEdit

### Entry Type Selection UI
**Options:**
1. **QComboBox** - Dropdown selector
   - Pros: Compact, familiar pattern
   - Cons: Extra click to see options
2. **QRadioButton Group** - Always visible options
   - Pros: Clear choices, one-click selection
   - Cons: Takes more space
3. **Segmented Control (Custom)** - Modern toggle buttons
   - Pros: Visual appeal, clear state
   - Cons: Custom implementation needed

**Recommendation:** Segmented Control (#3) - better UX, matches warm design

### Character Counter Display
**Options:**
1. **Status Bar** - Bottom of editor
   - Pros: Unobtrusive, standard location
   - Cons: May be missed by users
2. **Inline Label** - Next to editor
   - Pros: Always visible, clear association
   - Cons: Uses screen space
3. **Dynamic Color Coding** - Changes as limit approaches
   - Pros: Visual feedback, intuitive
   - Cons: Accessibility concerns

**Recommendation:** Inline Label with Color Coding (#2+#3) - best visibility

## Detailed Subtasks

### 1. Widget Structure Setup
- [ ] Create src/ui/journal_editor.py module
- [ ] Define JournalEditorWidget(QWidget) class
- [ ] Set up main vertical layout (QVBoxLayout)
- [ ] Create header section for date/type selection
- [ ] Create editor section with character counter
- [ ] Create footer section for action buttons

### 2. Entry Type Selector Implementation
- [ ] Create custom SegmentedControl widget:
  ```python
  class SegmentedControl(QWidget):
      # Toggle buttons: Daily | Weekly | Monthly
  ```
- [ ] Style with warm colors:
  - [ ] Inactive: #FFF8F0 background, #8B7355 text
  - [ ] Active: #FF8C42 background, white text
  - [ ] Hover effects with smooth transitions
- [ ] Emit entryTypeChanged signal on selection
- [ ] Add keyboard navigation (arrow keys)

### 3. Date Selection Integration
- [ ] Import and use EnhancedDateEdit from existing components
- [ ] Configure date picker for entry type:
  - [ ] Daily: Single date selection
  - [ ] Weekly: Week picker (Monday-Sunday)
  - [ ] Monthly: Month/Year picker
- [ ] Add date validation based on type
- [ ] Update date display format dynamically

### 4. Text Editor Implementation
- [ ] Create custom PlainTextEditor(QPlainTextEdit):
  - [ ] Override keyPressEvent for character limit
  - [ ] Add real-time character counting
  - [ ] Implement smooth scrolling
- [ ] Set editor properties:
  ```python
  self.setFont(QFont('Inter', 14))
  self.setStyleSheet("""
      QPlainTextEdit {
          background-color: #FFFFFF;
          border: 2px solid #E8DCC8;
          border-radius: 8px;
          padding: 16px;
          color: #5D4E37;
      }
      QPlainTextEdit:focus {
          border-color: #FF8C42;
      }
  """)
  ```

### 5. Character Counter Implementation
- [ ] Create CharacterCounter widget:
  - [ ] Display format: "2,456 / 10,000 characters"
  - [ ] Update on every text change
  - [ ] Color transitions:
    - Green (#95C17B): 0-7,000 chars
    - Yellow (#FFD166): 7,001-9,000 chars
    - Orange (#F4A261): 9,001-9,800 chars
    - Red (#E76F51): 9,801-10,000 chars
- [ ] Add progress bar visualization
- [ ] Implement character limit enforcement

### 6. Action Buttons
- [ ] Create button container with horizontal layout
- [ ] Implement Save button:
  - [ ] Primary style from ButtonStyle.PRIMARY
  - [ ] Ctrl+S shortcut
  - [ ] Loading state during save
- [ ] Implement Cancel button:
  - [ ] Secondary style
  - [ ] Escape key shortcut
- [ ] Add spacing and alignment

### 7. Unsaved Changes Detection
- [ ] Track original content on load
- [ ] Compare current content on:
  - [ ] Tab switch attempt
  - [ ] Window close
  - [ ] Date/type change
- [ ] Show confirmation dialog:
  ```python
  QMessageBox.warning(self, "Unsaved Changes",
      "You have unsaved changes. Save before leaving?",
      QMessageBox.Save | QMessageBox.Discard | QMessageBox.Cancel)
  ```

### 8. Keyboard Shortcuts
- [ ] Implement shortcut actions:
  - [ ] Ctrl+S: Save entry
  - [ ] Escape: Cancel/close editor
  - [ ] Ctrl+Z/Y: Undo/redo
  - [ ] F11: Toggle fullscreen editor
- [ ] Add tooltips showing shortcuts
- [ ] Create shortcut help overlay (F1)

### 9. Loading States
- [ ] Create LoadingOverlay widget
- [ ] Show spinner during:
  - [ ] Entry loading
  - [ ] Entry saving
  - [ ] Date validation
- [ ] Disable controls during operations
- [ ] Add smooth fade transitions

### 10. Focus Management
- [ ] Set tab order: Date → Type → Editor → Save → Cancel
- [ ] Auto-focus editor on load
- [ ] Trap focus within modal dialogs
- [ ] Highlight focused elements clearly

### 11. Responsive Design
- [ ] Implement minimum size constraints
- [ ] Create responsive breakpoints:
  - [ ] Compact: <800px width
  - [ ] Normal: 800-1200px
  - [ ] Wide: >1200px
- [ ] Adjust font sizes and spacing
- [ ] Test with various window sizes

### 12. Accessibility Features
- [ ] Add ARIA labels to all controls
- [ ] Implement high contrast mode support
- [ ] Ensure keyboard-only navigation
- [ ] Add screen reader announcements:
  - [ ] Character count changes
  - [ ] Save success/failure
  - [ ] Validation errors

### 13. Testing Implementation
- [ ] Create tests/unit/test_journal_editor.py:
  - [ ] Test character limit enforcement
  - [ ] Test unsaved changes detection
  - [ ] Test keyboard shortcuts
  - [ ] Test date/type selection
  - [ ] Test responsive behavior
  
- [ ] Create tests/ui/test_journal_editor_ui.py:
  - [ ] Test with pytest-qt
  - [ ] Simulate user interactions
  - [ ] Test focus management
  - [ ] Test loading states
  
- [ ] Accessibility testing:
  - [ ] Test with NVDA/JAWS
  - [ ] Verify keyboard navigation
  - [ ] Check color contrast ratios

### 14. Documentation
- [ ] Add comprehensive docstrings
- [ ] Create usage examples
- [ ] Document keyboard shortcuts
- [ ] Add inline code comments for complex logic

## Output Log
[2025-01-28 00:00:00] Task created - Main editor component for journal functionality