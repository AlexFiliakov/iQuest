"""Create a marker file to indicate portable mode fixes have been applied."""

import os
from datetime import datetime

marker_file = "portable_mode_fixed.txt"

with open(marker_file, 'w') as f:
    f.write(f"Portable mode fixes applied on {datetime.now()}\n")
    f.write("Fixed issues:\n")
    f.write("1. AttributeError: 'DailyDashboardWidget' object has no attribute '_current_date'\n")
    f.write("2. AttributeError: 'DailyMetricsCalculator' object has no attribute 'copy'\n")
    f.write("3. Added fallback support for data_access mode\n")
    f.write("4. TypeError: Invalid comparison between dtype=datetime64[ns, UTC] and Timestamp\n")

print(f"Created {marker_file}")
print("\nThe application needs to be restarted for the fixes to take effect.")