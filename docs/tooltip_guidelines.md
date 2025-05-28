# Tooltip Style Guidelines for Apple Health Monitor

## Overview
This document provides guidelines for implementing consistent, helpful tooltips throughout the Apple Health Monitor Dashboard application.

## Visual Style
Tooltips in the application follow the warm color theme:
- **Background**: Dark brown (#5D4E37)
- **Text**: White (#FFFFFF)
- **Padding**: 8px
- **Border Radius**: 4px
- **Font Size**: 14px
- **Delay**: 700ms before showing
- **Duration**: 10 seconds visible time

## Content Guidelines

### 1. Be Concise
- Keep tooltips under 80 characters when possible
- Use clear, simple language
- Avoid technical jargon

### 2. Be Helpful
- Explain what the element does, not just what it is
- Include keyboard shortcuts when applicable
- Provide context for complex features

### 3. Be Consistent
- Use sentence case for tooltip text
- Include keyboard shortcuts in parentheses: "Browse for file (Alt+B)"
- Use active voice: "Import data" not "Data will be imported"

## Examples

### Good Tooltips
✅ "Browse for Apple Health export file on your computer (Alt+B)"
✅ "Filter data from this date (inclusive)"
✅ "Click to select multiple items. Use Space to toggle, Ctrl+A to select all"

### Poor Tooltips
❌ "Button" - Not helpful
❌ "This button allows you to browse for files on your computer system" - Too verbose
❌ "Alt+B" - Missing context

## Implementation

### Buttons
```python
button.setToolTip("Action description (Shortcut)")
# Example:
browse_button.setToolTip("Browse for Apple Health export file (Alt+B)")
```

### Input Fields
```python
input_field.setToolTip("What this field is for and any constraints")
# Example:
date_edit.setToolTip("Filter data from this date (inclusive)")
```

### Complex Controls
```python
multi_select.setToolTip("Brief explanation. Key shortcuts for common actions")
# Example:
device_dropdown.setToolTip("Select which devices to include. Use Ctrl+A to select all")
```

## Accessibility Considerations

1. **Screen Readers**: Tooltips should complement, not duplicate, accessible names and descriptions
2. **Keyboard Users**: Always include keyboard shortcuts in tooltips where applicable
3. **Focus Indicators**: Ensure tooltips don't obscure focus indicators

## Testing Checklist

- [ ] All interactive elements have tooltips
- [ ] Tooltips appear after 700ms delay
- [ ] Tooltips are readable and helpful
- [ ] Keyboard shortcuts are included where applicable
- [ ] Tooltips don't obstruct user interaction
- [ ] Tooltips follow the visual style guide
- [ ] Content is concise and clear