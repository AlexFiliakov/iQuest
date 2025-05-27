# ADR-001: UI Framework Selection

## Status
Accepted

## Context
We need to select a UI framework for building a Windows desktop application that:
- Provides a warm, inviting visual design with custom theming
- Supports complex data visualizations and charts
- Can be packaged as a standalone Windows executable
- Offers good performance with large datasets
- Is accessible to developers familiar with Python

## Decision
We will use **PyQt6** as our UI framework.

## Rationale

### Options Considered

#### 1. Tkinter
**Pros:**
- Built into Python (no additional dependencies)
- Simple to learn and use
- Lightweight

**Cons:**
- Limited theming capabilities
- Basic widget set
- Poor support for modern UI patterns
- Difficult to achieve the desired warm aesthetic

#### 2. Kivy
**Pros:**
- Modern, touch-friendly UI
- Good animation support
- Cross-platform including mobile

**Cons:**
- Steep learning curve
- Non-native look and feel
- Limited desktop-specific widgets
- Harder to integrate with matplotlib

#### 3. PyQt6
**Pros:**
- Extensive widget library
- Excellent theming with QSS (Qt Style Sheets)
- Native performance and look
- Great matplotlib integration
- Strong documentation and community
- Professional appearance

**Cons:**
- Larger executable size
- GPL/Commercial licensing
- More complex than Tkinter

#### 4. Dear PyGui
**Pros:**
- Very fast rendering
- Good for data visualization
- Modern immediate-mode GUI

**Cons:**
- Less mature ecosystem
- Limited widget variety
- Harder to achieve traditional desktop UI patterns

### Decision Factors

1. **Theming Capability**: PyQt6's QSS allows us to fully customize the appearance to match our warm color scheme
2. **Chart Integration**: PyQt6 has excellent matplotlib integration through matplotlib.backends.backend_qt5agg
3. **Widget Variety**: Provides all necessary widgets (tabs, date pickers, tables, etc.)
4. **Performance**: Native C++ performance for smooth interactions with large datasets
5. **Packaging**: Well-supported by PyInstaller for creating executables
6. **Accessibility**: Built-in accessibility features for screen readers

## Consequences

### Positive
- Can achieve the exact visual design specified in requirements
- Professional, polished appearance
- Excellent performance with large datasets
- Rich set of pre-built widgets reduces development time
- Good documentation and community support

### Negative
- Larger executable size (estimated 50-80MB)
- Need to comply with GPL or purchase commercial license
- Steeper learning curve than Tkinter
- More complex debugging compared to simpler frameworks

### Mitigation
- Use UPX compression to reduce executable size
- Ensure GPL compliance for open-source distribution
- Create reusable component library to simplify development
- Invest in proper Qt debugging tools and logging

## References
- [PyQt6 Documentation](https://www.riverbankcomputing.com/static/Docs/PyQt6/)
- [Qt Style Sheets Reference](https://doc.qt.io/qt-6/stylesheet-reference.html)
- [Matplotlib Qt Backend](https://matplotlib.org/stable/users/explain/backends.html)