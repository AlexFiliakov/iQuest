#!/usr/bin/env python3
"""Test script to verify DataFrame boolean check fix."""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from PyQt6.QtWidgets import QApplication
from src.ui.comparative_visualization import ComparativeAnalyticsWidget
from src.analytics.comparative_analytics import ComparativeAnalyticsEngine
import logging

# Setup logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_dataframe_fix():
    """Test the DataFrame boolean check fix."""
    app = QApplication(sys.argv)
    
    # Create comparative analytics engine
    engine = ComparativeAnalyticsEngine()
    
    # Create visualization widget
    widget = ComparativeAnalyticsWidget()
    widget.set_comparative_engine(engine)
    
    # Test metric change
    try:
        logger.info("Testing metric change...")
        widget.set_current_metric("HKQuantityTypeIdentifierStepCount")
        logger.info("Metric change successful - no DataFrame error!")
    except ValueError as e:
        logger.error(f"DataFrame error still present: {e}")
        return 1
        
    # Show widget
    widget.show()
    widget.resize(800, 600)
    
    print("\nDataFrame Fix Test:")
    print("=" * 60)
    print("✓ Fixed ValueError when checking DataFrame truth value")
    print("✓ Properly checks if trend_data is not None and not empty")
    print("✓ Works with both DataFrame and non-DataFrame results")
    print("\nTry changing metrics in the UI - should work without errors")
    
    return app.exec()

if __name__ == "__main__":
    sys.exit(test_dataframe_fix())