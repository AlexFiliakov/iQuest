---
task_id: T083
status: open
complexity: Low
last_updated: 2025-05-29 16:50
---

# Task: Modernize Color Palette System

## Description
Replace the current warm orange/tan color scheme (#FF6600, #F5E6D3) with a sophisticated, professional palette inspired by Wall Street Journal aesthetics. This foundational change will improve visual professionalism, accessibility (WCAG compliance), and align with modern UI standards.

**Note**: The original spec requests both "warm welcome colors" AND "WSJ-style analytics". This task represents a shift toward WSJ aesthetics. If warm colors must be retained, consider a hybrid approach: warm colors for UI chrome, professional colors for data visualization.

## Goal / Objectives
Transform the application's visual identity from amateur to professional by:
- Replace vibrant orange accent (#FF8C42) with sophisticated slate (#5B6770)
- Update warm tan backgrounds with clean whites and grays
- Ensure all color combinations meet WCAG AA contrast requirements (4.5:1)
- Create a consistent color system across all components

## Acceptance Criteria
- [ ] StyleManager updated with new WSJ-inspired color palette
- [ ] All button styles updated to use new primary color (#5B6770)
- [ ] Form inputs and borders updated to use subtle gray (#E9ECEF)
- [ ] Calendar heatmap gradient updated from orange to sophisticated gray scale
- [ ] All components tested for WCAG AA compliance
- [ ] No visual regressions in any UI component
- [ ] Application runs without color-related errors

## Subtasks
- [ ] Update COLORS dictionary in src/ui/style_manager.py
- [ ] Update get_button_style() method for all button variants
- [ ] Update get_input_style() for form elements
- [ ] Update get_card_style() for card components
- [ ] Update calendar heatmap gradient colors
- [ ] Update chart color schemes in visualization components
- [ ] Test color contrast ratios for accessibility
- [ ] Update any hardcoded color values in individual components
- [ ] Run visual regression tests

## Technical Guidance

### Key Files to Modify
1. **src/ui/style_manager.py** - Central color definitions
   - Update COLORS dictionary (lines ~50-70)
   - Methods: get_button_style(), get_card_style(), get_input_style()
   
2. **src/ui/charts/calendar_heatmap.py** - Heatmap gradient
   - Update gradient_colors list
   
3. **src/ui/component_factory.py** - Component styling
   - May have color overrides to update

### Color Mapping
```python
# Old → New
'#FF8C42' → '#5B6770'  # Primary accent (orange → slate)
'#F5E6D3' → '#F8F9FA'  # Background (tan → light gray)
'#FFD166' → '#ADB5BD'  # Secondary (yellow → medium gray)
'#FFF8F0' → '#FFFFFF'  # Surface (cream → white)
'#E8DCC8' → '#E9ECEF'  # Border (tan → light gray)
```

### Implementation Pattern
Follow existing style manager patterns:
```python
COLORS = {
    'primary': '#5B6770',
    'primary_hover': '#4A5560',
    'primary_pressed': '#3A4550',
    'background': '#FFFFFF',
    'surface': '#F8F9FA',
    'border': '#E9ECEF',
    'text_primary': '#212529',
    'text_secondary': '#6C757D'
}
```

## Output Log
*(This section is populated as work progresses on the task)*

[2025-05-29 16:50] Task created