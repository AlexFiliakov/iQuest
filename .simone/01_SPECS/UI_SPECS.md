# UI/UX Specifications for Apple Health Monitor Dashboard

## Table of Contents
1. [Design Philosophy](#design-philosophy)
2. [Visual Design System](#visual-design-system)
3. [Component Architecture](#component-architecture)
4. [Layout Principles](#layout-principles)
5. [Interaction Patterns](#interaction-patterns)
6. [Accessibility Guidelines](#accessibility-guidelines)
7. [Performance Considerations](#performance-considerations)
8. [Implementation Guidelines](#implementation-guidelines)

---

## 1. Design Philosophy

### Core Principles
The Apple Health Monitor Dashboard follows a **Wall Street Journal-inspired** design aesthetic that prioritizes:

1. **Data Clarity**: Information is the hero - remove visual noise that doesn't enhance understanding
2. **Professional Sophistication**: Clean, authoritative presentation suitable for serious health tracking
3. **Efficient Space Usage**: Maximize information density without creating clutter
4. **Progressive Disclosure**: Show essential information first, details on demand
5. **Consistent Behavior**: Similar elements behave similarly throughout the application

### Design Inspiration
- **Wall Street Journal**: Clean typography, professional color palette, data-focused layouts
- **Modern Dashboard Design**: Card-based layouts, subtle shadows for depth, smooth animations
- **Healthcare Applications**: Clear visual hierarchy, accessibility-first approach

---

## 2. Visual Design System

### Color Palette

#### Primary Colors
```css
/* Core Brand Colors */
--primary-bg: #FFFFFF;        /* Clean white background */
--secondary-bg: #FAFBFC;      /* Very light gray for subtle contrast */
--tertiary-bg: #F3F4F6;       /* Light gray for hover states */
--surface-elevated: #FFFFFF;   /* Elevated surfaces */

/* Text Colors */
--text-primary: #0F172A;      /* Rich black for primary text */
--text-secondary: #64748B;    /* Slate gray for secondary text */
--text-muted: #94A3B8;        /* Light slate for muted text */
--text-inverse: #FFFFFF;      /* White text on dark backgrounds */
```

#### Accent Colors
```css
/* Action Colors */
--accent-primary: #0F172A;    /* Rich black - primary actions */
--accent-secondary: #2563EB;  /* Vibrant blue - CTAs and highlights */
--accent-success: #10B981;    /* Modern green - positive states */
--accent-warning: #F59E0B;    /* Modern amber - caution states */
--accent-error: #EF4444;      /* Modern red - error states */
--accent-light: #E5E7EB;      /* Light gray - subtle borders */

/* Data Visualization Colors */
--data-orange: #FB923C;       /* Warm orange for data points */
--data-purple: #A78BFA;       /* Soft purple for secondary data */
--data-teal: #2DD4BF;         /* Teal for tertiary data */
--data-pink: #F472B6;         /* Pink for quaternary data */
```

### Typography

#### Font Stack
```css
font-family: 'Inter', 'Segoe UI', -apple-system, BlinkMacSystemFont, sans-serif;
```

#### Type Scale
- **Display**: 28px, Bold (Major headings)
- **Title**: 22px, Bold (Section titles)
- **Heading**: 18px, SemiBold (Card titles)
- **Subheading**: 16px, Medium (Subsection titles)
- **Body**: 14px, Regular (Primary content)
- **Caption**: 12px, Regular (Supporting text)
- **Micro**: 11px, Regular (Labels, hints)

#### Font Weights
- Regular: 400
- Medium: 500
- SemiBold: 600
- Bold: 700

### Spacing System
Based on an 8px grid system:
- **xs**: 4px
- **sm**: 8px
- **md**: 12px
- **lg**: 16px
- **xl**: 20px
- **xxl**: 24px
- **xxxl**: 32px

### Shadow System
Modern elevation system for depth:
```css
/* Shadow Levels */
--shadow-sm: 0 1px 2px rgba(0, 0, 0, 0.05);
--shadow-md: 0 4px 6px rgba(0, 0, 0, 0.07);
--shadow-lg: 0 10px 15px rgba(0, 0, 0, 0.10);
--shadow-xl: 0 20px 25px rgba(0, 0, 0, 0.15);
--shadow-inner: inset 0 2px 4px rgba(0, 0, 0, 0.06);
```

### Border Radius
- **Small**: 6px (Buttons, inputs)
- **Medium**: 8px (Cards, dropdowns)
- **Large**: 12px (Modals, major containers)
- **XLarge**: 16px (Feature cards)
- **Full**: 9999px (Pills, circular elements)

---

## 3. Component Architecture

### Card Components

#### Base Card Structure
```
┌─────────────────────────────────┐
│ [Card Header]                   │ ← 16-20px padding
│ ┌─────────────────────────────┐ │
│ │                             │ │
│ │     [Card Content]          │ │ ← Main content area
│ │                             │ │
│ └─────────────────────────────┘ │
│ [Card Footer]                   │ ← Optional actions
└─────────────────────────────────┘
  ↑
  Shadow effect (no border)
```

#### Card Specifications
- **Background**: White (#FFFFFF)
- **Border**: None (use shadow instead)
- **Border Radius**: 12px
- **Padding**: 16-20px
- **Shadow**: shadow-md (default), shadow-lg (hover)
- **Hover Effect**: Subtle background change to tertiary-bg
- **Transition**: All 200ms ease-in-out

### Button Components

#### Button Types
1. **Primary Button**
   - Background: accent-secondary (#2563EB)
   - Text: white
   - Hover: Darker shade (#1D4ED8)
   - Used for: Primary actions (Import, Apply, Save)

2. **Secondary Button**
   - Background: transparent
   - Border: 1px solid accent-light
   - Text: text-primary
   - Hover: tertiary-bg background
   - Used for: Secondary actions (Cancel, Reset)

3. **Ghost Button**
   - Background: transparent
   - Border: none
   - Text: accent-secondary
   - Hover: Light background tint
   - Used for: Tertiary actions (Links, subtle actions)

#### Button Specifications
- **Height**: 36px (small), 40px (medium), 44px (large)
- **Padding**: 12px horizontal (small), 16px (medium), 20px (large)
- **Border Radius**: 8px
- **Font Weight**: 600 (SemiBold)
- **Transition**: All 150ms ease-in-out
- **Disabled State**: 50% opacity, cursor not-allowed

### Form Controls

#### Input Fields
- **Height**: 40px
- **Padding**: 12px horizontal
- **Border**: 1px solid accent-light
- **Border Radius**: 8px
- **Focus Border**: 2px solid accent-secondary
- **Background**: white (enabled), tertiary-bg (disabled)
- **Font Size**: 14px

#### Dropdowns/Selects
- **Same as input fields for consistency**
- **Dropdown Arrow**: Custom SVG, 4px triangle
- **Dropdown Menu**: Shadow-lg, 8px border radius
- **Menu Item Height**: 36px
- **Menu Item Hover**: tertiary-bg background

#### Date Pickers
- **Calendar Popup**: Shadow-xl, 12px border radius
- **Selected Date**: accent-secondary background
- **Today Marker**: Dotted border
- **Navigation Buttons**: Ghost button style

### Navigation Components

#### Tab Navigation
- **Tab Height**: 48px
- **Tab Padding**: 16px horizontal
- **Active Tab**: 2px bottom border, accent-primary color
- **Inactive Tab**: text-secondary color
- **Hover**: text-primary color
- **Transition**: Border 200ms, color 150ms

#### Navigation Buttons
- **Size**: 36x36px (compact), 40x40px (normal)
- **Style**: Ghost button with icon
- **Icon Size**: 14px (compact), 16px (normal)
- **Hover**: tertiary-bg background

### Data Visualization

#### Charts
- **Line Charts**: 2px stroke, smooth curves
- **Bar Charts**: 8px border radius on bars
- **Colors**: Use data visualization palette
- **Grid Lines**: Very subtle (5% opacity)
- **Axis Labels**: text-secondary color, 12px font

#### Progress Indicators
- **Linear Progress**: 8px height, rounded ends
- **Circular Progress**: 120px diameter, 12px stroke
- **Colors**: accent-success (complete), accent-secondary (in progress)
- **Background**: tertiary-bg
- **Animation**: Smooth transitions, easing curves

#### Metric Cards
- **Value Font**: 28px bold (large), 20px bold (medium)
- **Label Font**: 12px medium, text-secondary
- **Trend Indicators**: Colored arrows/icons
- **Spacing**: Consistent 12px between elements

---

## 4. Layout Principles

### Grid System
- **Base Grid**: 8px
- **Column System**: 12 columns with 16px gutters
- **Container Max Width**: 1440px
- **Responsive Breakpoints**:
  - Mobile: < 640px
  - Tablet: 640px - 1024px
  - Desktop: > 1024px

### Spacing Guidelines

#### Page Layout
- **Page Margins**: 16px (mobile), 24px (tablet), 32px (desktop)
- **Section Spacing**: 24px between major sections
- **Card Grid Gap**: 16px

#### Component Spacing
- **Card Internal Padding**: 16px (compact), 20px (normal), 24px (spacious)
- **Form Field Spacing**: 16px vertical
- **Button Group Spacing**: 8px
- **List Item Spacing**: 8px

### Visual Hierarchy

#### Z-Index Layers
1. **Base Content**: 0
2. **Sticky Headers**: 10
3. **Dropdowns**: 100
4. **Modals**: 1000
5. **Tooltips**: 1100
6. **Notifications**: 1200

#### Content Priority
1. **Primary Metrics**: Largest, bold, prominent color
2. **Secondary Information**: Medium size, regular weight
3. **Supporting Details**: Small size, muted color
4. **Actions**: Clear but not competing with content

---

## 5. Interaction Patterns

### Hover States
- **Cards**: Slight elevation (transform: translateY(-1px))
- **Buttons**: Background color change
- **Links**: Underline or color change
- **Transition Duration**: 150-200ms
- **Easing**: ease-in-out

### Click/Touch Feedback
- **Buttons**: Scale down slightly (0.98)
- **Cards**: Ripple effect or brief highlight
- **Response Time**: < 100ms
- **Touch Target Size**: Minimum 44x44px

### Loading States
- **Skeleton Screens**: For initial loads
- **Progress Bars**: For determinate operations
- **Spinners**: For indeterminate operations
- **Subtle Animations**: Pulsing for ongoing operations

### Animations
- **Duration**: 150ms (micro), 250ms (normal), 350ms (complex)
- **Easing Curves**:
  - ease-in-out: Default for most transitions
  - ease-out: For elements entering
  - ease-in: For elements exiting
  - spring: For playful interactions

### Focus Management
- **Visible Focus Indicators**: 2px outline, offset 2px
- **Focus Color**: accent-secondary with transparency
- **Tab Order**: Logical, top-to-bottom, left-to-right
- **Skip Links**: For keyboard navigation

---

## 6. Accessibility Guidelines

### Color Contrast
- **Normal Text**: Minimum 4.5:1 contrast ratio
- **Large Text**: Minimum 3:1 contrast ratio
- **Interactive Elements**: Minimum 3:1 against background
- **Focus Indicators**: Minimum 3:1 against adjacent colors

### Keyboard Navigation
- **All Interactive Elements**: Keyboard accessible
- **Tab Order**: Logical and predictable
- **Shortcuts**: Document and make discoverable
- **Focus Trap**: Prevent in modals and overlays

### Screen Reader Support
- **Semantic HTML**: Use appropriate elements
- **ARIA Labels**: For icon-only buttons
- **Live Regions**: For dynamic updates
- **Landmarks**: For page structure

### Motion and Animation
- **Respect prefers-reduced-motion**: Disable non-essential animations
- **Provide Controls**: For auto-playing content
- **Avoid Seizure Triggers**: No flashing > 3Hz

### Text and Readability
- **Minimum Font Size**: 12px (11px for labels)
- **Line Height**: 1.5 for body text
- **Maximum Line Length**: 80 characters
- **Text Scaling**: Support up to 200% zoom

---

## 7. Performance Considerations

### Rendering Performance
- **Shadow Effects**: Use sparingly, consider performance impact
- **Animations**: Use CSS transforms, avoid layout changes
- **Virtual Scrolling**: For large lists (>100 items)
- **Debouncing**: For search inputs (300ms)
- **Throttling**: For resize/scroll handlers (16ms)

### Asset Optimization
- **Icons**: SVG sprites or icon fonts
- **Images**: Lazy loading, appropriate formats
- **Fonts**: Subset, preload critical weights
- **Code Splitting**: Load features on demand

### State Management
- **Local State**: For UI-only state
- **Global State**: For shared data
- **Caching**: For expensive computations
- **Memoization**: For complex components

---

## 8. Implementation Guidelines

### Component Structure
```python
class ModernComponent(QWidget):
    """Modern component following UI specifications."""
    
    def __init__(self):
        super().__init__()
        self.style_manager = StyleManager()
        self._setup_ui()
        self._apply_modern_styling()
        
    def _setup_ui(self):
        """Create component structure."""
        # Layout with proper spacing
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)
        
    def _apply_modern_styling(self):
        """Apply modern styling from StyleManager."""
        self.setStyleSheet(self.style_manager.get_modern_card_style())
        
        # Add shadow effect
        shadow = self.style_manager.create_shadow_effect()
        self.setGraphicsEffect(shadow)
```

### Styling Best Practices

#### Use StyleManager Methods
```python
# Good - Centralized styling
self.setStyleSheet(self.style_manager.get_modern_card_style())

# Avoid - Inline styling
self.setStyleSheet("background: white; border: 1px solid #ccc;")
```

#### Consistent Spacing
```python
# Good - Using spacing constants
layout.setContentsMargins(SPACING_MD, SPACING_MD, SPACING_MD, SPACING_MD)
layout.setSpacing(SPACING_SM)

# Avoid - Magic numbers
layout.setContentsMargins(12, 12, 12, 12)
layout.setSpacing(8)
```

#### Shadow Effects
```python
# Good - Reusable shadow creation
shadow = self.style_manager.create_shadow_effect(
    blur_radius=15,
    y_offset=2,
    opacity=30
)
widget.setGraphicsEffect(shadow)

# Avoid - Creating shadows manually each time
```

### Responsive Design
```python
def _adjust_for_size(self, width: int):
    """Adjust layout based on available width."""
    if width < 640:  # Mobile
        self._apply_mobile_layout()
    elif width < 1024:  # Tablet
        self._apply_tablet_layout()
    else:  # Desktop
        self._apply_desktop_layout()
```

### Animation Implementation
```python
def _animate_value_change(self, new_value: float):
    """Animate value changes smoothly."""
    self.animation = QPropertyAnimation(self, b"value")
    self.animation.setDuration(250)
    self.animation.setEasingCurve(QEasingCurve.Type.OutCubic)
    self.animation.setStartValue(self.current_value)
    self.animation.setEndValue(new_value)
    self.animation.start()
```

### Accessibility Implementation
```python
def _setup_accessibility(self):
    """Configure accessibility features."""
    # Set accessible names and descriptions
    self.setAccessibleName("Health Metric Card")
    self.setAccessibleDescription(f"Shows {self.metric_name} data")
    
    # Ensure keyboard navigation
    self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
    
    # Add tooltips for additional context
    self.setToolTip(f"Click to view detailed {self.metric_name} analytics")
```

---

## Component Reference

### Key UI Components and Their Specifications

1. **MonthlyDashboardWidget**
   - Modern calendar heatmap with borderless cards
   - Tight 12px spacing throughout
   - Shadow effects for depth

2. **ConfigurationTab**
   - Two-column layout for efficient space use
   - Borderless sections with shadows
   - Compact form controls

3. **WeeklyDashboardWidget**
   - Metric cards with hover effects
   - Clean chart presentation
   - Week-over-week comparison

4. **DailyDashboardWidget**
   - Real-time metric updates
   - Activity timeline
   - Personal records integration

5. **GoalProgressWidget**
   - Circular progress indicators
   - Animated transitions
   - Status-based coloring

6. **TrophyCaseWidget**
   - Achievement cards with rarity borders
   - Celebration animations
   - Social sharing integration

---

## Future Considerations

### Planned Enhancements
1. **Dark Mode**: Full dark theme support
2. **Responsive Design**: Better mobile/tablet layouts
3. **Advanced Animations**: More sophisticated transitions
4. **Customization**: User-configurable themes
5. **Accessibility**: Enhanced screen reader support

### Design System Evolution
- Regular review and updates based on user feedback
- Performance monitoring and optimization
- New component patterns as features are added
- Consistency audits and refinements

---

## References
- [Material Design Guidelines](https://material.io/design)
- [Apple Human Interface Guidelines](https://developer.apple.com/design/)
- [Web Content Accessibility Guidelines (WCAG)](https://www.w3.org/WAI/WCAG21/quickref/)
- [PyQt6 Documentation](https://www.riverbankcomputing.com/static/Docs/PyQt6/)
- Good UI Examples:
  - `examples/wall street journal chart example 1.jpg`
  - `examples/wall street journal chart example 2.jpg`

---

*Last Updated: December 2024*
*Version: 1.0*