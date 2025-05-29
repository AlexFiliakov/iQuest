---
task_id: T086
status: open
complexity: Medium
last_updated: 2025-05-29 16:53
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
- [ ] Shadow system defined with 3 levels (sm, md, lg)
- [ ] All harsh borders replaced with shadows or subtle 1px borders
- [ ] Card components implemented with 8px border radius
- [ ] Hover states increase elevation smoothly
- [ ] No performance impact from shadow rendering
- [ ] Consistent 16px padding in cards
- [ ] Shadow colors use rgba for transparency

## Subtasks
- [ ] Define shadow tokens in style_manager.py
- [ ] Create get_shadow_style() method
- [ ] Update card components to use shadows
- [ ] Remove harsh blue/colored borders
- [ ] Add elevation change on hover
- [ ] Update dashboard widgets to use card layouts
- [ ] Update statistics cards styling
- [ ] Test shadow rendering performance
- [ ] Ensure shadows work on all backgrounds

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