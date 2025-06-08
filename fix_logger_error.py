#!/usr/bin/env python3
"""Quick fix for the logger error in advanced_trend_engine.py"""

import os
import shutil
from datetime import datetime

# Path to the file that needs fixing
file_path = "src/analytics/advanced_trend_engine.py"

# Create backup
backup_path = f"{file_path}.backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
shutil.copy2(file_path, backup_path)
print(f"Created backup: {backup_path}")

# Read the file
with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

# Check if the fix is already applied
if "# Set up logger first" in content:
    print("Fix already applied!")
else:
    # Apply the fix - move logger definition before the try/except blocks
    content = content.replace(
        """from .advanced_trend_models import (
    TrendAnalysis, AdvancedTrendAnalysis, TrendClassification, EvidenceQuality,
    PredictionQuality, ChangePoint, PredictionPoint, SeasonalComponent,
    TrendComponent, TrendDecomposition, ValidationResult, EnsembleResult,
    WSJVisualizationConfig
)

# Try to import optional dependencies""",
        """from .advanced_trend_models import (
    TrendAnalysis, AdvancedTrendAnalysis, TrendClassification, EvidenceQuality,
    PredictionQuality, ChangePoint, PredictionPoint, SeasonalComponent,
    TrendComponent, TrendDecomposition, ValidationResult, EnsembleResult,
    WSJVisualizationConfig
)

# Set up logger first
logger = logging.getLogger(__name__)

# Try to import optional dependencies"""
    )
    
    # Remove the duplicate logger definition later in the file
    content = content.replace("\nlogger = logging.getLogger(__name__)", "", 1)
    
    # Write the fixed content
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print(f"Fixed {file_path}")
    print("Logger is now defined before being used in exception handlers.")

print("\nDone! You can now rebuild with:")
print("python build.py --incremental")