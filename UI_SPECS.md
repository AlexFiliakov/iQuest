# UI Design Specifications

## Overview
The Apple Health Monitor Dashboard follows a modern, professional design system inspired by Wall Street Journal aesthetics with emphasis on clarity, readability, and data-focused presentation.

## Color Palette

### Primary Colors
- **Background**: `#FFFFFF` (Clean white)
- **Secondary Background**: `#FAFBFC` (Very light gray for subtle contrast)
- **Tertiary Background**: `#F3F4F6` (Light gray for hover states)

### Accent Colors
- **Primary Accent**: `#0F172A` (Rich black for primary text)
- **Secondary Accent**: `#2563EB` (Vibrant blue for CTAs and highlights)
- **Success**: `#10B981` (Modern green for positive states)
- **Warning**: `#F59E0B` (Modern amber for caution)
- **Error**: `#EF4444` (Modern red for errors)

### Text Colors
- **Primary Text**: `#0F172A` (Rich black)
- **Secondary Text**: `#64748B` (Slate gray)
- **Muted Text**: `#94A3B8` (Light slate)
- **Inverse Text**: `#FFFFFF` (White on dark backgrounds)

### Data Visualization Colors
- **Primary Data**: `#2563EB` (Blue)
- **Secondary Data**: `#10B981` (Green)
- **Tertiary Data**: `#FB923C` (Orange)
- **Quaternary Data**: `#A78BFA` (Purple)

## Typography

### Font Families
- **Primary**: Inter, -apple-system, BlinkMacSystemFont, sans-serif
- **Display**: Poppins (for headings and emphasis)
- **Monospace**: JetBrains Mono (for code and data)

### Font Sizes
- **Display**: 32px
- **Heading 1**: 24px
- **Heading 2**: 20px
- **Heading 3**: 16px
- **Body**: 14px
- **Small**: 12px
- **Caption**: 10px

## Spacing & Layout

### Spacing Scale
- **xs**: 4px
- **sm**: 8px
- **md**: 16px
- **lg**: 24px
- **xl**: 32px
- **2xl**: 48px

### Border Radius
- **Small**: 4px (buttons, inputs)
- **Medium**: 8px (cards, dialogs)
- **Large**: 12px (large cards)

## Component Specifications

### Calendar Widget
- **Minimum Width**: 320px
- **Minimum Height**: 340px
- **Cell Padding**: 8px
- **Grid Gap**: 2px
- **Header Height**: 48px
- **Day Cell Size**: Flexible, minimum 40x40px

#### Calendar Features
- Hide days from adjacent months
- Show all 7 days of the week
- Display all 6 possible week rows
- Navigation controls with month/year display
- Data availability indicators with colors

### Buttons
- **Height**: 36px (standard), 32px (small), 40px (large)
- **Padding**: 12px horizontal, 8px vertical
- **Border Radius**: 4px
- **Font Weight**: 600

### Input Fields
- **Height**: 36px
- **Padding**: 8px 12px
- **Border**: 1px solid `#E5E7EB`
- **Border Radius**: 4px
- **Focus Border**: 2px solid `#0080C7`

### Cards
- **Background**: `#FFFFFF`
- **Border**: 1px solid `#E5E7EB`
- **Border Radius**: 8px
- **Padding**: 16px
- **Shadow**: 0 1px 3px rgba(0,0,0,0.1)

## Accessibility

### Focus Indicators
- **Color**: `#0080C7` (WSJ Blue)
- **Width**: 2px
- **Style**: Solid
- **Offset**: 2px

### Contrast Ratios
- **Normal Text**: Minimum 4.5:1
- **Large Text**: Minimum 3:1
- **Interactive Elements**: Minimum 3:1

### Keyboard Navigation
- All interactive elements must be keyboard accessible
- Clear focus indicators on all focusable elements
- Logical tab order
- Escape key to close popups/dialogs

## Animation & Transitions

### Duration
- **Fast**: 150ms (hover effects)
- **Normal**: 250ms (standard transitions)
- **Slow**: 350ms (complex animations)

### Easing
- **Default**: ease-in-out
- **Enter**: ease-out
- **Exit**: ease-in

## Shadow System
- **Small**: 0 1px 2px rgba(0,0,0,0.05)
- **Medium**: 0 4px 6px rgba(0,0,0,0.07)
- **Large**: 0 10px 15px rgba(0,0,0,0.10)
- **Extra Large**: 0 20px 25px rgba(0,0,0,0.15)