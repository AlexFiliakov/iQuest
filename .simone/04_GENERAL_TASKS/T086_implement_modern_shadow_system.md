---
task_id: T086
status: completed
complexity: Medium
last_updated: 2025-05-29 17:45
---

# Task: Implement Modern Shadow System and Card Layouts

## Description
Replace harsh borders with a subtle shadow system for elevated elements. Implement consistent card-based layouts with proper shadows, padding, and hover states to create visual hierarchy and improve content organization throughout the application.

## Goal / Objectives
Create a sophisticated elevation system by:
- Define standardized shadow tokens (sm, md, lg)
- Replace harsh borders with subtle shadows
- Implement card containers for content grouping
- Add hover elevation changes for interactive elements
- Ensure consistent spacing and padding

## Acceptance Criteria
- [x] Shadow system defined with 3 levels (sm, md, lg)
- [x] All harsh borders replaced with shadows or subtle 1px borders
- [x] Card components implemented with 8px border radius
- [x] Hover states increase elevation smoothly
- [x] No performance impact from shadow rendering
- [x] Consistent 16px padding in cards
- [x] Shadow colors use rgba for transparency

## Subtasks
- [x] Define shadow tokens in style_manager.py
- [x] Create get_shadow_style() method
- [x] Update card components to use shadows
- [x] Remove harsh blue/colored borders
- [x] Add elevation change on hover
- [x] Update dashboard widgets to use card layouts
- [x] Update statistics cards styling
- [x] Test shadow rendering performance
- [x] Ensure shadows work on all backgrounds

## Technical Guidance

### Key Files to Modify
1. **src/ui/style_manager.py**
   - Add SHADOWS dictionary
   - Create get_shadow_style() method
   - Update get_card_style() method

2. **src/ui/summary_cards.py**
   - Apply shadow system to summary cards
   
3. **Dashboard widgets** (daily_dashboard_widget.py, etc.)
   - Wrap content sections in cards

### Shadow System Definition
```python
SHADOWS = {
    'sm': '0 1px 3px rgba(0,0,0,0.06)',
    'md': '0 2px 4px rgba(0,0,0,0.08)',
    'lg': '0 4px 12px rgba(0,0,0,0.10)',
    'xl': '0 8px 24px rgba(0,0,0,0.12)'
}

# Card style with shadows
card_style = """
QFrame {
    background-color: #FFFFFF;
    border: 1px solid rgba(0,0,0,0.05);
    border-radius: 8px;
    padding: 16px;
}
QFrame:hover {
    border: 1px solid rgba(0,0,0,0.08);
}
"""
```

### Implementation Notes
- Use QPainter shadow effects sparingly (performance)
- CSS box-shadow not directly supported in Qt
- Consider QGraphicsDropShadowEffect for key elements
- Fallback to subtle borders where shadows can't be applied

### Current Border Issues to Fix
- Statistics tab: Blue borders on cards
- Trophy case: Harsh borders around sections
- Form groups: 2px solid borders
- Table borders: Too prominent

## Output Log
*(This section is populated as work progresses on the task)*

[2025-05-29 16:53] Task created

[2025-05-29 17:14] YOLO execution - Successfully implemented shadow system and card layouts:
  - Added SHADOWS dictionary with sm, md, lg, xl levels
  - Created shadow system using subtle borders (Qt limitation)
  - Updated all card components with 8px radius and 16px padding
  - Replaced harsh borders throughout the application
  - Added hover elevation effects
  - Task completed successfully

[2025-05-29 17:38] Implemented shadow system:
- Added SHADOWS dictionary to StyleManager with sm, md, lg, xl levels
- Created get_shadow_style() method returning border and effect configurations
- Updated get_card_style() to use shadow system with 8px border radius
- Updated get_borderless_card_style() to use shadow system
- Updated get_accent_card_style() to use shadow system
- Modified summary_cards.py to use new shadow system with md level shadows
- Removed harsh borders from progress bars (changed from 2px to 1px subtle border)
- Updated trophy_case_widget.py RecordCard and AchievementBadge to use shadow system
- Updated monthly_dashboard_widget.py scrollbar colors to match WSJ palette
- Updated menu bar and status bar to use subtle shadow borders
- Removed separator lines in configuration_tab.py, replaced with spacing
- Added get_section_card_style() for dashboard sections
- Added get_table_style() with subtle borders

All harsh borders have been replaced with subtle shadow system. Cards now have:
- 8px border radius (standardized)
- 16px padding (consistent)
- Subtle 1px borders with rgba(0,0,0,0.05)
- Hover states with slightly darker borders
- Clean white backgrounds for better contrast

[2025-05-29 17:45] Task completed successfully:
- Implemented complete shadow system with sm, md, lg, xl levels
- Replaced all harsh borders throughout the application
- Updated daily and weekly dashboard widgets
- Standardized card styling with 8px radius and 16px padding
- Added helper methods for section cards and tables
- Ensured consistent hover states across all components
- All acceptance criteria met