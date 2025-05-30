#!/usr/bin/env python3
import sys
sys.path.insert(0, '.')

from PyQt6.QtWidgets import QApplication
from src.ui.comparative_visualization import ComparativeAnalyticsWidget

app = QApplication([])

widget = ComparativeAnalyticsWidget()
print('Widget created')
print('historical_widget:', hasattr(widget, 'historical_widget'))
print('personal_btn:', hasattr(widget, 'personal_btn'))
print('seasonal_btn:', hasattr(widget, 'seasonal_btn'))
print('group_widget:', hasattr(widget, 'group_widget'))

# Check buttons
print('\nButton states:')
print('personal_btn checked:', widget.personal_btn.isChecked())
print('seasonal_btn checked:', widget.seasonal_btn.isChecked())

# Check for any property that might access group_widget
print('\nWidget attributes:')
for attr in dir(widget):
    if 'group' in attr.lower():
        print(f'  Found: {attr}')