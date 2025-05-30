#!/usr/bin/env python3
"""Debug script to investigate why Daily tab isn't loading data."""

import sys
from datetime import date, timedelta
import pandas as pd
from PyQt6.QtWidgets import QApplication
from src.ui.main_window import MainWindow
from src.utils.logging_config import get_logger

logger = get_logger(__name__)

def debug_daily_data():
    """Debug the Daily tab data loading."""
    app = QApplication(sys.argv)
    
    # Create main window
    window = MainWindow()
    window.show()
    
    # Switch to config tab
    window.tab_widget.setCurrentIndex(0)
    QApplication.processEvents()
    
    print("\n" + "="*50)
    print("Daily Tab Data Debug")
    print("="*50)
    
    # Check if data is loaded
    if hasattr(window, 'config_tab'):
        data = None
        if hasattr(window.config_tab, 'get_filtered_data'):
            data = window.config_tab.get_filtered_data()
        elif hasattr(window.config_tab, 'filtered_data'):
            data = window.config_tab.filtered_data
            
        if data is not None and not data.empty:
            print(f"\n✓ Data loaded: {len(data)} records")
            
            # Check data structure
            print(f"\nColumns: {list(data.columns)}")
            print(f"\nData types:")
            print(data.dtypes)
            
            # Check sample data
            print(f"\nFirst 5 records:")
            print(data.head())
            
            # Check unique metric types
            if 'type' in data.columns:
                unique_types = data['type'].unique()
                print(f"\nUnique metric types: {len(unique_types)}")
                for i, metric_type in enumerate(unique_types[:10]):
                    print(f"  {i+1}. {metric_type}")
                if len(unique_types) > 10:
                    print(f"  ... and {len(unique_types) - 10} more")
            
            # Check date range
            if 'creationDate' in data.columns:
                dates = pd.to_datetime(data['creationDate'])
                print(f"\nDate range: {dates.min()} to {dates.max()}")
                
                # Check data for today
                today = date.today()
                today_start = pd.Timestamp(today)
                today_end = pd.Timestamp(today) + pd.Timedelta(days=1)
                
                today_data = data[(pd.to_datetime(data['creationDate']) >= today_start) & 
                                (pd.to_datetime(data['creationDate']) < today_end)]
                print(f"\nData for today ({today}): {len(today_data)} records")
                
                # Check data for yesterday
                yesterday = today - timedelta(days=1)
                yesterday_start = pd.Timestamp(yesterday)
                yesterday_end = pd.Timestamp(yesterday) + pd.Timedelta(days=1)
                
                yesterday_data = data[(pd.to_datetime(data['creationDate']) >= yesterday_start) & 
                                    (pd.to_datetime(data['creationDate']) < yesterday_end)]
                print(f"Data for yesterday ({yesterday}): {len(yesterday_data)} records")
            
            # Test daily calculator
            print("\n" + "-"*30)
            print("Testing DailyMetricsCalculator")
            print("-"*30)
            
            from src.analytics.daily_metrics_calculator import DailyMetricsCalculator
            
            try:
                calculator = DailyMetricsCalculator(data)
                print("✓ Calculator created successfully")
                
                # Check prepared data
                if hasattr(calculator, 'data'):
                    print(f"\nCalculator data shape: {calculator.data.shape}")
                    
                    # Check if date column exists
                    if 'date' in calculator.data.columns:
                        print("✓ Date column exists")
                        
                        # Check date values
                        unique_dates = calculator.data['date'].unique()
                        print(f"Unique dates: {len(unique_dates)}")
                        
                        # Check today's data in calculator
                        today_calc_data = calculator.data[calculator.data['date'] == today]
                        print(f"\nData for today in calculator: {len(today_calc_data)} records")
                        
                        if len(today_calc_data) > 0:
                            print("Sample today's data:")
                            print(today_calc_data[['type', 'value', 'date']].head())
                        
                        # Test calculate_daily_statistics
                        if 'type' in data.columns and len(unique_types) > 0:
                            test_metric = unique_types[0]
                            print(f"\nTesting calculate_daily_statistics for '{test_metric}' on {today}")
                            
                            stats = calculator.calculate_daily_statistics(test_metric, today)
                            if stats:
                                print(f"✓ Stats calculated: count={stats.count}, mean={stats.mean}")
                            else:
                                print("✗ No stats returned")
                                
                                # Debug: Check data for this metric and date
                                metric_today_data = calculator.data[
                                    (calculator.data['type'] == test_metric) & 
                                    (calculator.data['date'] == today)
                                ]
                                print(f"Debug: Found {len(metric_today_data)} records for {test_metric} on {today}")
                    else:
                        print("✗ Date column NOT found in calculator data")
                        
            except Exception as e:
                print(f"✗ Error creating calculator: {e}")
                import traceback
                traceback.print_exc()
            
        else:
            print("\n✗ No data loaded")
            print("Please go to Configuration tab and import data first")
    else:
        print("\n✗ config_tab not found")
    
    # Switch to Daily tab
    print("\n" + "-"*30)
    print("Switching to Daily tab")
    print("-"*30)
    
    window.tab_widget.setCurrentIndex(1)
    QApplication.processEvents()
    
    if hasattr(window, 'daily_dashboard'):
        dashboard = window.daily_dashboard
        print("✓ Daily dashboard exists")
        
        # Check calculator
        if dashboard.daily_calculator:
            print("✓ Daily calculator is set")
        else:
            print("✗ Daily calculator is NOT set")
        
        # Check metric cards
        if hasattr(dashboard, '_metric_cards'):
            print(f"✓ Metric cards: {len(dashboard._metric_cards)}")
        else:
            print("✗ No metric cards")
    else:
        print("✗ Daily dashboard not found")
    
    print("\n" + "="*50 + "\n")
    
    return app.exec()

if __name__ == "__main__":
    sys.exit(debug_daily_data())