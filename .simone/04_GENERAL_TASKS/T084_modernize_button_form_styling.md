---
task_id: T084
status: open
complexity: Low
last_updated: 2025-05-29 16:51
---

# Task: Modernize Button and Form Styling

## Description
Update all buttons and form elements to use modern styling patterns with proper border radius, padding, hover states, and focus indicators. Remove harsh borders and drop shadows in favor of subtle, professional styling that aligns with WSJ aesthetics.

## Goal / Objectives
Create a cohesive, modern form control system by:
- Add consistent 4px border radius to all buttons and inputs
- Implement smooth hover transitions (0.2s ease)
- Add proper focus states with subtle shadow rings
- Standardize padding and spacing (12px vertical, 24px horizontal for buttons)
- Remove outdated drop shadows and harsh borders

## Acceptance Criteria
- [ ] All button styles updated with modern properties
- [ ] Form inputs have consistent height (40px) and padding
- [ ] Focus states visible and accessible (3px shadow ring)
- [ ] Hover states implemented with smooth transitions
- [ ] No harsh borders (replace 2px solid with 1px #E9ECEF)
- [ ] All interactive elements meet 44x44px touch target minimum
- [ ] Consistent styling across all UI components

## Subtasks
- [ ] Update button styles in style_manager.py
- [ ] Update form input styles (text fields, dropdowns)
- [ ] Update multi-select combo box styling
- [ ] Add focus ring styles for accessibility
- [ ] Update date picker styling
- [ ] Remove harsh borders from all components
- [ ] Add hover state transitions
- [ ] Test keyboard navigation and focus visibility
- [ ] Verify touch target sizes

## Technical Guidance

### Key Files to Modify
1. **src/ui/style_manager.py**
   - get_button_style() method - Add border-radius, transitions
   - get_input_style() method - Standardize height and padding
   
2. **src/ui/multi_select_combo.py** (CheckableComboBox)
   - Update dropdown styling
   
3. **src/ui/enhanced_date_edit.py**
   - Apply consistent form styling

### Style Patterns to Apply
```python
# Button base style
"""
QPushButton {
    border: none;
    border-radius: 4px;
    padding: 12px 24px;
    font-weight: 500;
    transition: all 0.2s ease;
}
QPushButton:hover {
    transform: translateY(-1px);
    box-shadow: 0 4px 8px rgba(0,0,0,0.12);
}
QPushButton:focus {
    outline: none;
    box-shadow: 0 0 0 3px rgba(91,103,112,0.25);
}
"""

# Form input style
"""
QLineEdit, QComboBox {
    height: 40px;
    padding: 0 16px;
    border: 1px solid #E9ECEF;
    border-radius: 4px;
    background: white;
}
QLineEdit:focus, QComboBox:focus {
    border-color: #5B6770;
    box-shadow: 0 0 0 3px rgba(91,103,112,0.1);
}
"""
```

### Border Updates
Replace all instances of:
- `border: 2px solid <color>` → `border: 1px solid #E9ECEF`
- Remove `box-shadow` with large offsets
- Remove inline color styles

## Output Log
*(This section is populated as work progresses on the task)*

[2025-05-29 16:51] Task created