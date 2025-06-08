#!/usr/bin/env python3
"""Direct test of the advanced_trend_engine module"""

import logging

# Set up a basic logger to prevent any issues
logging.basicConfig(level=logging.DEBUG)

# Read and execute the file content directly to test
with open('src/analytics/advanced_trend_engine.py', 'r') as f:
    content = f.read()

# Check if logger is defined before use
logger_def_index = content.find('logger = logging.getLogger(__name__)')
prophet_use_index = content.find('logger.debug(f"Prophet not available')
stl_use_index = content.find('logger.debug(f"STL not available')

print("Checking logger definition order...")
print(f"Logger defined at position: {logger_def_index}")
print(f"First logger use (Prophet) at position: {prophet_use_index}")
print(f"Second logger use (STL) at position: {stl_use_index}")

if logger_def_index < 0:
    print("❌ ERROR: Logger not defined!")
elif prophet_use_index < 0 and stl_use_index < 0:
    print("✅ Logger uses removed or not found (OK)")
elif logger_def_index < prophet_use_index and logger_def_index < stl_use_index:
    print("✅ SUCCESS: Logger is defined before being used!")
else:
    print("❌ ERROR: Logger is used before being defined!")
    print("This will cause NameError when Prophet import fails.")

# Also check the order visually
print("\nChecking import structure...")
if "# Set up logger first" in content:
    print("✅ Found comment indicating logger is set up first")
else:
    print("⚠️  Missing comment marker for logger setup")