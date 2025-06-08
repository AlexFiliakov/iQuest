#!/usr/bin/env python3
"""Test that the logger fix works correctly"""

import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

try:
    # This should not raise NameError anymore
    from analytics.advanced_trend_engine import AdvancedTrendAnalysisEngine
    print("✅ SUCCESS: Module imported without logger error!")
    print(f"Prophet available: {hasattr(sys.modules.get('analytics.advanced_trend_engine'), 'PROPHET_AVAILABLE')}")
    if hasattr(sys.modules.get('analytics.advanced_trend_engine'), 'PROPHET_AVAILABLE'):
        print(f"Prophet status: {sys.modules['analytics.advanced_trend_engine'].PROPHET_AVAILABLE}")
except NameError as e:
    if "logger" in str(e):
        print("❌ FAILED: Logger error still present!")
        print(f"Error: {e}")
    else:
        raise
except Exception as e:
    print(f"Other error (this is OK if it's about missing dependencies): {e}")