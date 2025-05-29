---
task_id: T085
status: open
complexity: Medium
last_updated: 2025-05-29 16:52
---

# Task: Redesign Tab Navigation with Modern Styling

## Description
Transform the current tab navigation from outdated rounded-top style to modern underline indicators. Implement clean, minimal tab design with bottom border indicators, proper hover states, and smooth transitions that align with WSJ's clean aesthetic.

## Goal / Objectives
Create a sophisticated tab navigation system by:
- Remove background colors from tabs in favor of transparent design
- Add bottom border indicators (2px) for selected state
- Implement smooth color transitions on hover
- Improve visual hierarchy with proper typography
- Ensure clear active/inactive state differentiation

## Acceptance Criteria
- [ ] Tab backgrounds removed (transparent)
- [ ] Selected tabs show 2px bottom border in primary color
- [ ] Hover states change text color smoothly
- [ ] Tab spacing and padding consistent (8px vertical, 16px horizontal)
- [ ] Icons properly aligned with text if present
- [ ] No visual jumping when switching tabs
- [ ] Keyboard navigation works properly

## Subtasks
- [ ] Update QTabWidget styling in main_window.py
- [ ] Remove rounded corners from tab headers
- [ ] Implement bottom border indicator for selected state
- [ ] Add hover state with color transition
- [ ] Update tab text colors (inactive: #6C757D, active: #5B6770)
- [ ] Ensure consistent spacing between tabs
- [ ] Test with all existing tabs (Config, Daily, Weekly, Monthly, etc.)
- [ ] Verify sub-tabs styling if applicable
- [ ] Test keyboard navigation (Tab/Shift+Tab)

## Technical Guidance

### Key Files to Modify
1. **src/ui/main_window.py**
   - Tab widget initialization (~line 300-400)
   - Look for QTabWidget styling
   
2. **src/ui/style_manager.py**
   - Add get_tab_style() method if not present

### Implementation Pattern
```python
tab_style = """
QTabWidget::pane {
    border: none;
    background: #FFFFFF;
}

QTabBar::tab {
    background: transparent;
    color: #6C757D;
    padding: 8px 16px;
    margin-right: 8px;
    border: none;
    border-bottom: 2px solid transparent;
}

QTabBar::tab:selected {
    color: #5B6770;
    border-bottom: 2px solid #5B6770;
}

QTabBar::tab:hover:!selected {
    color: #495057;
}

QTabBar::tab:first {
    margin-left: 0;
}
"""
```

### Current Implementation Reference
The tab widget uses:
- Main tabs: Configuration, Daily, Weekly, Monthly, Comparative, Trophy Case, Journal, Help
- Some tabs have sub-navigation (Trophy Case has Statistics/Streaks)
- Icons are used for visual identification

### Testing Approach
1. Visual testing with each tab
2. Ensure transitions are smooth
3. Verify no layout shifts
4. Test with keyboard navigation
5. Check sub-tab styling consistency

## Output Log
*(This section is populated as work progresses on the task)*

[2025-05-29 16:52] Task created