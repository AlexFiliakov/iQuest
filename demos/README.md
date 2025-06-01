# Apple Health Monitor - Demo Scripts

This directory contains demonstration scripts that showcase various features of the Apple Health Monitor Dashboard. These scripts are meant to be run independently and are not part of the main application.

## Available Demos

### 1. Month-over-Month Trends Demo
- **File**: `month_over_month_demo.py`
- **Description**: Demonstrates the month-over-month trends analysis system with sample data
- **Run**: `python demos/month_over_month_demo.py`

### 2. Line Chart Demo
- **File**: `line_chart_demo.py`
- **Description**: Shows how to use the EnhancedLineChart with WSJ-inspired styling
- **Run**: `python demos/line_chart_demo.py`

### 3. Accessible Line Chart Example
- **File**: `example_accessible_line_chart.py`
- **Description**: Demonstrates accessibility features in chart components
- **Run**: `python demos/example_accessible_line_chart.py`

### 4. Visualization Example
- **File**: `visualization_example.py`
- **Description**: Comprehensive visualization examples with various chart types
- **Run**: `python demos/visualization_example.py`

## Important Notes

- These demo scripts are **not** imported by the main application
- Each demo creates its own QApplication and window
- They use mock data for demonstration purposes
- Some demos may require the full application to be properly set up

## Running Demos

From the project root directory:

```bash
# Example: Run the month-over-month demo
python demos/month_over_month_demo.py
```

If you encounter import errors, ensure you're running from the project root directory where the `src/` folder is accessible.