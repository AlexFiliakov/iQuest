"""Apple Health Monitor Dashboard - Comprehensive Health Data Analysis Platform.

A sophisticated PyQt6-based desktop application for analyzing, visualizing, and gaining
insights from Apple Health data exports. The application provides advanced analytics,
professional-quality visualizations, and comprehensive health tracking capabilities.

The Apple Health Monitor Dashboard features:

- **Data Import & Processing**: XML and CSV import with validation and streaming processing
- **Advanced Analytics**: Daily, weekly, monthly metrics with trend analysis and anomaly detection
- **Professional Visualizations**: WSJ-inspired charts with interactive features and accessibility
- **Health Scoring**: Comprehensive health assessment system with personalized insights
- **Performance Optimization**: Multi-level caching, background processing, and optimized engines
- **Accessibility Compliance**: WCAG 2.1 AA compliant interface with screen reader support

The application is designed for health enthusiasts, researchers, and medical professionals
who need powerful tools for analyzing personal health data while maintaining complete
privacy with local-only data storage.

Attributes:
    __version__ (str): Current version of the Apple Health Monitor Dashboard.
    __author__ (str): Development team identifier.

Example:
    Basic application startup:
    
    >>> import sys
    >>> from PyQt6.QtWidgets import QApplication
    >>> from src.main import main
    >>> if __name__ == "__main__":
    ...     sys.exit(main())

Note:
    All health data remains local to the user's machine. No data is transmitted
    to external servers, ensuring complete privacy and HIPAA-like data protection.
"""

__version__ = "0.1.0"
__author__ = "Apple Health Monitor Team"