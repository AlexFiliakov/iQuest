# UI/UX Specifications
## Apple Health Monitor Dashboard - M01

### 1. Design Philosophy

#### 1.1 Core Principles
- **Warm & Inviting:** Use earth tones and soft colors to create a welcoming experience
- **Clarity First:** Prioritize readability and understanding over density
- **Progressive Disclosure:** Show essential information first, details on demand
- **Consistent Feedback:** Every action should have clear visual feedback
- **Accessibility:** Design for users of all abilities

#### 1.2 Target User Profile
- Age: 25-65 years
- Technical skill: Basic computer literacy
- Context: Personal health tracking
- Goals: Understand health trends, identify patterns, document context

### 2. Visual Design System

#### 2.1 Color Palette
```css
/* Primary Colors */
--color-primary-bg: #F5E6D3;      /* Warm tan background */
--color-secondary-bg: #FFFFFF;     /* White for cards */
--color-tertiary-bg: #FFF8F0;      /* Light cream for sections */

/* Accent Colors */
--color-accent-primary: #FF8C42;   /* Warm orange - CTAs */
--color-accent-secondary: #FFD166; /* Soft yellow - highlights */
--color-accent-success: #95C17B;   /* Soft green - positive */
--color-accent-warning: #F4A261;   /* Amber - caution */
--color-accent-error: #E76F51;     /* Coral - errors */

/* Text Colors */
--color-text-primary: #5D4E37;     /* Dark brown */
--color-text-secondary: #8B7355;   /* Medium brown */
--color-text-muted: #A69583;      /* Light brown */
--color-text-inverse: #FFFFFF;     /* White on dark */

/* Chart Colors */
--color-chart-1: #FF8C42;          /* Orange */
--color-chart-2: #FFD166;          /* Yellow */
--color-chart-3: #95C17B;          /* Green */
--color-chart-4: #6C9BD1;          /* Blue */
--color-chart-5: #B79FCB;          /* Purple */
```

#### 2.2 Typography
```css
/* Font Stack */
--font-primary: 'Inter', 'Segoe UI', -apple-system, sans-serif;
--font-display: 'Poppins', 'Segoe UI', sans-serif;
--font-mono: 'JetBrains Mono', 'Consolas', monospace;

/* Type Scale */
--text-xs: 12px;     /* Captions */
--text-sm: 14px;     /* Secondary text */
--text-base: 16px;   /* Body text */
--text-lg: 18px;     /* Emphasized text */
--text-xl: 22px;     /* Section headers */
--text-2xl: 28px;    /* Page titles */
--text-3xl: 36px;    /* Dashboard values */

/* Font Weights */
--font-normal: 400;
--font-medium: 500;
--font-semibold: 600;
--font-bold: 700;
```

#### 2.3 Spacing System
```css
/* 8px Grid System */
--space-1: 8px;
--space-2: 16px;
--space-3: 24px;
--space-4: 32px;
--space-5: 40px;
--space-6: 48px;
--space-8: 64px;
--space-10: 80px;
```

### 3. Component Library

#### 3.1 Buttons
```python
# Button styles
class ButtonStyle:
    PRIMARY = {
        'background': '#FF8C42',
        'color': '#FFFFFF',
        'border': 'none',
        'padding': '12px 24px',
        'border_radius': '8px',
        'font_weight': '600',
        'hover': {
            'background': '#E67A35',
            'transform': 'translateY(-1px)',
            'box_shadow': '0 4px 12px rgba(255, 140, 66, 0.3)'
        }
    }
    
    SECONDARY = {
        'background': 'transparent',
        'color': '#FF8C42',
        'border': '2px solid #FF8C42',
        'padding': '10px 22px',
        'hover': {
            'background': '#FFF5ED',
            'border_color': '#E67A35'
        }
    }
```

#### 3.2 Cards
```python
# Card component
class Card(QWidget):
    def __init__(self):
        self.setStyleSheet("""
            QWidget {
                background-color: #FFFFFF;
                border-radius: 12px;
                padding: 24px;
                border: 1px solid rgba(139, 115, 85, 0.1);
            }
            QWidget:hover {
                box-shadow: 0 8px 24px rgba(93, 78, 55, 0.08);
            }
        """)
```

#### 3.3 Input Fields
```css
/* Text input styling */
.text-input {
    background: #FFFFFF;
    border: 2px solid #E8DCC8;
    border-radius: 8px;
    padding: 12px 16px;
    font-size: 16px;
    color: #5D4E37;
    transition: all 0.2s ease;
}

.text-input:focus {
    border-color: #FF8C42;
    outline: none;
    box-shadow: 0 0 0 3px rgba(255, 140, 66, 0.1);
}
```

### 4. Layout Specifications

#### 4.1 Main Window Layout
```
┌─────────────────────────────────────────────────────┐
│  Header Bar                                         │
│  ┌─────────────────────────────────────────────┐   │
│  │ Logo | App Title          [Min][Max][Close] │   │
│  └─────────────────────────────────────────────┘   │
├─────────────────────────────────────────────────────┤
│  Navigation Tabs                                    │
│  ┌──────┬────────┬────────┬────────┬──────────┐    │
│  │Config│ Daily  │ Weekly │Monthly │  Journal  │    │
│  └──────┴────────┴────────┴────────┴──────────┘    │
├─────────────────────────────────────────────────────┤
│                                                     │
│              Main Content Area                      │
│                                                     │
│  ┌─────────────────────────────────────────────┐   │
│  │                                             │   │
│  │         Dynamic Dashboard Content           │   │
│  │                                             │   │
│  └─────────────────────────────────────────────┘   │
│                                                     │
├─────────────────────────────────────────────────────┤
│  Status Bar                                         │
│  [Ready] [Data: 50,000 records] [Last update: ...] │
└─────────────────────────────────────────────────────┘
```

#### 4.2 Configuration Tab Layout
```
Configuration Settings
─────────────────────

┌─ Import Data ────────────────────────────┐
│                                          │
│  📁 Select CSV File    [Browse...]       │
│                                          │
│  Progress: ████████░░░░ 75%             │
│                                          │
└──────────────────────────────────────────┘

┌─ Filter Data ────────────────────────────┐
│                                          │
│  Date Range:                             │
│  [📅 Start Date] to [📅 End Date]        │
│                                          │
│  Source Devices:                         │
│  ☑ iPhone    ☑ Apple Watch              │
│  ☐ iPad      ☐ Other Apps               │
│                                          │
│  Metric Types:                           │
│  ☑ Heart Rate    ☑ Steps                │
│  ☑ Sleep         ☐ Workouts             │
│                                          │
│         [Reset] [Apply Filters]          │
│                                          │
└──────────────────────────────────────────┘
```

#### 4.3 Daily Dashboard Layout
```
Daily Metrics - March 15, 2024
─────────────────────────────

[◀ Previous] [📅 Select Date] [Next ▶]

┌─ Heart Rate ─────────────────────────────┐
│  Average     Min        Max              │
│  72 bpm     58 bpm    110 bpm           │
│                                          │
│  📊 [Line chart showing hourly data]     │
│                                          │
│  vs Yesterday: ↑ 3%  vs Week Avg: ↓ 2%  │
└──────────────────────────────────────────┘

┌─ Steps ──────────────────────────────────┐
│  Total: 8,542 steps                      │
│                                          │
│  📊 [Bar chart showing hourly steps]     │
│                                          │
│  Goal Progress: ████████░░ 85%           │
└──────────────────────────────────────────┘

┌─ Journal Entry ──────────────────────────┐
│                                          │
│  [Add your notes for today...]           │
│                                          │
│                            [Save Entry]   │
└──────────────────────────────────────────┘
```

### 5. Interaction Design

#### 5.1 Micro-interactions
- **Hover Effects:** Subtle elevation and color shifts
- **Click Feedback:** Brief scale animation (0.95x) 
- **Loading States:** Skeleton screens with pulsing animation
- **Success Feedback:** Green checkmark with fade-in
- **Error States:** Red border with shake animation

#### 5.2 Transitions
```css
/* Standard transition timing */
.transition-fast { transition: all 0.15s ease-out; }
.transition-normal { transition: all 0.3s ease-out; }
.transition-slow { transition: all 0.5s ease-out; }

/* Easing functions */
--ease-out: cubic-bezier(0.0, 0.0, 0.2, 1);
--ease-in-out: cubic-bezier(0.4, 0.0, 0.2, 1);
--ease-spring: cubic-bezier(0.5, 1.5, 0.5, 1);
```

#### 5.3 Navigation Patterns
- **Tab Navigation:** Keyboard accessible (Tab, Shift+Tab)
- **Date Navigation:** Arrow keys for day/week/month changes
- **Chart Interaction:** Hover for details, click to zoom
- **Shortcuts:** Ctrl+O (Open), Ctrl+S (Save), F5 (Refresh)

### 6. Responsive Design

#### 6.1 Window Size Adaptations
- **Minimum Size:** 1024x768px
- **Optimal Size:** 1440x900px
- **Maximum useful:** 1920x1080px

#### 6.2 Scaling Behavior
```python
# DPI-aware scaling
class ResponsiveLayout:
    def adapt_to_size(self, width, height):
        if width < 1200:
            # Compact mode: Stack cards vertically
            self.set_layout('vertical')
        else:
            # Normal mode: Grid layout
            self.set_layout('grid')
            
    def scale_fonts(self, dpi_ratio):
        # Scale all fonts based on system DPI
        base_size = 16 * dpi_ratio
        return {
            'body': base_size,
            'header': base_size * 1.5,
            'small': base_size * 0.875
        }
```

### 7. Icon System

#### 7.1 Icon Style
- **Type:** Outlined icons with 2px stroke
- **Size:** 24x24px standard, 16x16px small, 32x32px large
- **Color:** Inherit from parent text color

#### 7.2 Common Icons
```
📁 Import      ⚙️ Settings     📊 Charts
📅 Calendar    💾 Save         🔄 Refresh
❤️ Heart Rate  👣 Steps        😴 Sleep
✏️ Edit        🗑️ Delete       ℹ️ Info
⚠️ Warning     ✅ Success      ❌ Error
```

### 8. Empty States

#### 8.1 No Data
```
┌─────────────────────────────────────┐
│                                     │
│         📊                          │
│                                     │
│    No data available yet            │
│                                     │
│    Import your Apple Health         │
│    CSV to get started              │
│                                     │
│       [Import Data]                 │
│                                     │
└─────────────────────────────────────┘
```

#### 8.2 No Results
```
┌─────────────────────────────────────┐
│                                     │
│         🔍                          │
│                                     │
│    No data matches your filters     │
│                                     │
│    Try adjusting your date range    │
│    or selected metrics              │
│                                     │
│       [Reset Filters]               │
│                                     │
└─────────────────────────────────────┘
```

### 9. Error Handling UI

#### 9.1 Error Message Design
```python
class ErrorMessage(QWidget):
    def __init__(self, title, message, recoverable=True):
        self.setStyleSheet("""
            background: #FFF5F5;
            border: 2px solid #E76F51;
            border-radius: 8px;
            padding: 16px;
        """)
        
        if recoverable:
            self.add_action_button("Try Again")
        else:
            self.add_action_button("View Details")
```

#### 9.2 Validation Feedback
- **Invalid Input:** Red border + error text below
- **Warning State:** Orange border + warning icon
- **Success State:** Green checkmark + fade out

### 10. Accessibility Features

#### 10.1 Keyboard Navigation
- All interactive elements reachable via Tab
- Arrow keys for list/grid navigation
- Enter/Space for activation
- Escape for cancel/close

#### 10.2 Screen Reader Support
- Semantic HTML structure
- ARIA labels for icons
- Alt text for charts
- Role attributes for custom widgets

#### 10.3 Visual Accessibility
- Minimum contrast ratio: 4.5:1 (WCAG AA)
- Focus indicators: 3px orange outline
- No color-only information
- Adjustable font sizes

### 11. Animation Guidelines

#### 11.1 Performance Budget
- Total animation time: <300ms
- CPU usage during animation: <30%
- Frame rate target: 60fps
- Disable on low-performance mode

#### 11.2 Animation Types
```python
# Fade in animation
def fade_in(widget, duration=300):
    effect = QGraphicsOpacityEffect()
    widget.setGraphicsEffect(effect)
    
    animation = QPropertyAnimation(effect, b"opacity")
    animation.setDuration(duration)
    animation.setStartValue(0)
    animation.setEndValue(1)
    animation.setEasingCurve(QEasingCurve.OutCubic)
    animation.start()
```

### 12. Platform Integration

#### 12.1 Windows Native Features
- System tray integration
- Native file dialogs
- Windows notifications
- Jump list shortcuts
- Taskbar progress

#### 12.2 Theme Adaptation
```python
# Detect and adapt to Windows theme
def adapt_to_system_theme():
    if is_dark_mode():
        # Adjust colors for dark mode
        return DarkThemeColors()
    else:
        return LightThemeColors()
```