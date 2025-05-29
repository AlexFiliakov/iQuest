#!/usr/bin/env python3
"""
Generate visual baselines for visualization components.

This script creates baseline images for visual regression testing by rendering
each component in various states and saving the images.
"""

import sys
import os
from pathlib import Path
from datetime import datetime

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

# Set Qt to offscreen mode for headless environments
os.environ['QT_QPA_PLATFORM'] = 'offscreen'

from PyQt6.QtWidgets import QApplication
from PIL import Image
import pandas as pd
import numpy as np

from tests.visual.visualization_testing_framework import VisualizationTestDataGenerator
from tests.visual.baseline_manager import BaselineManager


def generate_baselines():
    """Generate baseline images for all visualization components"""
    print("Generating visual baselines for visualization components...")
    print("=" * 60)
    
    # Create baseline directory
    baseline_dir = Path("tests/visual_baselines")
    baseline_dir.mkdir(parents=True, exist_ok=True)
    
    # Initialize baseline manager
    baseline_manager = BaselineManager(base_path=str(baseline_dir))
    
    # Initialize data generator
    data_generator = VisualizationTestDataGenerator()
    
    # Generate different test datasets
    datasets = {
        'standard': data_generator.create_standard_time_series_data(),
        'small': data_generator.create_time_series_data(points=10),
        'large': data_generator.create_time_series_data(points=1000),
        'edge_cases': data_generator.create_edge_case_datasets()
    }
    
    generated_count = 0
    
    # Try to generate baselines for chart components
    try:
        from src.ui.charts.base_chart import BaseChart
        
        # Create a simple test chart
        class TestChart(BaseChart):
            def __init__(self, data=None):
                super().__init__()
                self.data = data
                
            def render_to_image(self, width=800, height=400, dpi=300):
                # Create a simple test image
                img = Image.new('RGB', (width, height), color='white')
                return img
        
        # Generate baseline for test chart
        chart = TestChart(datasets['standard'])
        img = chart.render_to_image()
        baseline_manager.save_baseline('TestChart_standard', img)
        print(f"✓ Generated baseline: TestChart_standard.png")
        generated_count += 1
        
    except ImportError as e:
        print(f"Could not import chart components: {e}")
    
    # Generate baselines for mock components
    print("\nGenerating baselines for mock components...")
    
    # Create mock visualizations with different themes
    themes = ['light', 'dark', 'high_contrast']
    sizes = [(800, 400), (400, 200), (1200, 600)]
    
    for theme in themes:
        for width, height in sizes:
            # Create a mock image with theme-specific colors
            if theme == 'light':
                bg_color = 'white'
                fg_color = '#333333'
            elif theme == 'dark':
                bg_color = '#1a1a1a'
                fg_color = '#e0e0e0'
            else:  # high_contrast
                bg_color = 'black'
                fg_color = 'white'
            
            img = Image.new('RGB', (width, height), color=bg_color)
            
            # Add some visual elements
            from PIL import ImageDraw
            draw = ImageDraw.Draw(img)
            
            # Draw a simple chart representation
            margin = 50
            draw.rectangle(
                [margin, margin, width-margin, height-margin],
                outline=fg_color,
                width=2
            )
            
            # Add grid lines
            for i in range(5):
                y = margin + (height - 2*margin) * i / 4
                draw.line([(margin, y), (width-margin, y)], fill=fg_color, width=1)
            
            # Save baseline
            baseline_name = f"MockChart_{theme}_{width}x{height}"
            baseline_manager.save_baseline(baseline_name, img)
            print(f"✓ Generated baseline: {baseline_name}.png")
            generated_count += 1
    
    # Generate baselines for different data scenarios
    print("\nGenerating baselines for data scenarios...")
    
    for scenario_name, scenario_data in datasets['edge_cases'].items():
        # Create a simple visualization for each scenario
        img = Image.new('RGB', (800, 400), color='#f5f5f5')
        draw = ImageDraw.Draw(img)
        
        # Add text to identify the scenario
        try:
            from PIL import ImageFont
            font = ImageFont.load_default()
        except:
            font = None
            
        text = f"Scenario: {scenario_name}"
        draw.text((10, 10), text, fill='black', font=font)
        
        # Save baseline
        baseline_name = f"DataScenario_{scenario_name}"
        baseline_manager.save_baseline(baseline_name, img)
        print(f"✓ Generated baseline: {baseline_name}.png")
        generated_count += 1
    
    print("\n" + "=" * 60)
    print(f"✓ Generated {generated_count} baseline images")
    print(f"✓ Baselines saved to: {baseline_dir.absolute()}")
    
    # Create baseline metadata
    metadata = {
        'generated_at': datetime.now().isoformat(),
        'baseline_count': generated_count,
        'themes': themes,
        'sizes': sizes,
        'scenarios': list(datasets['edge_cases'].keys())
    }
    
    import json
    metadata_path = baseline_dir / 'baseline_metadata.json'
    with open(metadata_path, 'w') as f:
        json.dump(metadata, f, indent=2)
    
    print(f"✓ Saved metadata to: {metadata_path.name}")
    

def main():
    """Main entry point"""
    # Initialize Qt application
    app = QApplication.instance()
    if app is None:
        app = QApplication(sys.argv)
    
    try:
        generate_baselines()
    except Exception as e:
        print(f"Error generating baselines: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0


if __name__ == '__main__':
    sys.exit(main())