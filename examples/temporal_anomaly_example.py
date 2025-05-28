"""
Example script demonstrating LSTM-based temporal anomaly detection.

This example shows:
1. Using the hybrid temporal anomaly detector
2. Training the LSTM component
3. Detecting anomalies with ensemble voting
4. Visualizing results with WSJ-style clarity
"""

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime, timedelta
import sys
import os

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.analytics.temporal_anomaly_detector import (
    HybridTemporalAnomalyDetector, TENSORFLOW_AVAILABLE
)
from src.analytics.anomaly_models import Severity


def generate_sample_health_data(days=180):
    """Generate sample health data with patterns and anomalies."""
    dates = pd.date_range(start='2024-01-01', periods=days, freq='D')
    
    # Base pattern: daily activity with weekly rhythm
    t = np.arange(days)
    
    # Components
    trend = 50 + 0.1 * t  # Slight upward trend
    weekly = 20 * np.sin(2 * np.pi * t / 7)  # Weekly pattern
    daily_noise = np.random.normal(0, 5, days)
    
    # Combine
    values = trend + weekly + daily_noise
    
    # Add realistic anomalies
    # Sick days (low activity)
    values[45:48] -= 30
    values[120:123] -= 25
    
    # Exceptional activity days
    values[60] += 40  # Marathon
    values[90] += 35  # Hiking trip
    
    # Injury period (sustained low)
    values[150:160] -= 20
    
    # Data issues
    values[75] = 0  # Missing data recorded as 0
    values[105] = 200  # Sensor error
    
    return pd.Series(values, index=dates, name='Daily Activity Score')


def visualize_anomalies(data, anomalies, title="Temporal Anomaly Detection"):
    """Visualize data with detected anomalies in WSJ style."""
    plt.style.use('seaborn-v0_8-whitegrid')
    
    fig, axes = plt.subplots(2, 1, figsize=(12, 8), height_ratios=[3, 1])
    
    # Main plot
    ax1 = axes[0]
    
    # Plot normal data
    ax1.plot(data.index, data.values, 'o-', color='#1f77b4', 
             markersize=3, alpha=0.6, label='Daily Activity')
    
    # Highlight anomalies by severity
    severity_colors = {
        Severity.LOW: '#90EE90',
        Severity.MEDIUM: '#FFD700',
        Severity.HIGH: '#FF8C00',
        Severity.CRITICAL: '#DC143C'
    }
    
    for severity, color in severity_colors.items():
        severity_anomalies = [a for a in anomalies if a.severity == severity]
        if severity_anomalies:
            timestamps = [a.timestamp for a in severity_anomalies]
            values = [data[t] for t in timestamps if t in data.index]
            if values:
                ax1.scatter(timestamps[:len(values)], values, 
                          color=color, s=100, alpha=0.8, 
                          edgecolors='black', linewidth=1,
                          label=f'{severity.value.capitalize()} anomaly')
    
    ax1.set_title(title, fontsize=14, fontweight='bold')
    ax1.set_ylabel('Activity Score', fontsize=12)
    ax1.legend(loc='upper left')
    ax1.grid(True, alpha=0.3)
    
    # Anomaly score plot
    ax2 = axes[1]
    
    # Create continuous anomaly score series
    anomaly_scores = pd.Series(0, index=data.index)
    for anomaly in anomalies:
        if anomaly.timestamp in anomaly_scores.index:
            anomaly_scores[anomaly.timestamp] = anomaly.score
    
    ax2.bar(anomaly_scores.index, anomaly_scores.values, 
            color='#DC143C', alpha=0.6, width=1)
    ax2.set_xlabel('Date', fontsize=12)
    ax2.set_ylabel('Anomaly Score', fontsize=12)
    ax2.grid(True, alpha=0.3)
    
    plt.tight_layout()
    return fig


def print_anomaly_details(anomalies, top_n=5):
    """Print detailed information about top anomalies."""
    print(f"\n{'='*60}")
    print(f"Top {top_n} Anomalies Detected")
    print(f"{'='*60}\n")
    
    # Sort by score
    sorted_anomalies = sorted(anomalies, key=lambda a: abs(a.score), reverse=True)[:top_n]
    
    for i, anomaly in enumerate(sorted_anomalies, 1):
        print(f"Anomaly {i}:")
        print(f"  Date: {anomaly.timestamp.strftime('%Y-%m-%d')}")
        print(f"  Value: {anomaly.value:.2f}")
        print(f"  Severity: {anomaly.severity.value.upper()}")
        print(f"  Score: {anomaly.score:.2f}")
        print(f"  Confidence: {anomaly.confidence:.2%}")
        
        # Context details
        context = anomaly.context
        print(f"  Detection Agreement: {context.get('detection_agreement', 'N/A')}")
        
        if 'recent_trend' in context:
            print(f"  Recent Trend: {context['recent_trend'].replace('_', ' ').title()}")
        
        if 'percentile_in_data' in context:
            print(f"  Percentile Rank: {context['percentile_in_data']:.1f}%")
        
        # Pattern deviation for LSTM
        if 'ml_context' in context and 'pattern_deviation' in context['ml_context']:
            deviation = context['ml_context']['pattern_deviation']
            print(f"  Pattern Deviation:")
            print(f"    - MSE: {deviation['mse']:.2f}")
            print(f"    - Correlation: {deviation['correlation']:.2f}")
        
        print()


def main():
    """Run temporal anomaly detection example."""
    print("Temporal Anomaly Detection Example")
    print("==================================\n")
    
    # Generate sample data
    print("Generating sample health data...")
    data = generate_sample_health_data(180)
    print(f"Generated {len(data)} days of data")
    
    # Create hybrid detector
    print("\nInitializing hybrid temporal anomaly detector...")
    detector = HybridTemporalAnomalyDetector(
        enable_ml=True,
        seasonal=7,  # Weekly pattern
        sequence_length=14  # Two weeks of context
    )
    
    # Check if ML is available
    if TENSORFLOW_AVAILABLE and detector.ml_detector:
        print("TensorFlow available - using hybrid detection (Statistical + LSTM)")
        
        # Split data for training
        train_data = data[:120]  # First 4 months for training
        test_data = data[120:]   # Last 2 months for testing
        
        print(f"\nTraining LSTM model on {len(train_data)} days of data...")
        try:
            result = detector.train_ml_component(
                train_data,
                epochs=30,
                batch_size=16,
                validation_split=0.2
            )
            print(f"Training complete. Final loss: {result['final_loss']:.4f}")
            print(f"Anomaly threshold: {result['threshold']:.4f}")
        except Exception as e:
            print(f"ML training failed: {e}")
            print("Falling back to statistical detection only")
    else:
        print("TensorFlow not available - using statistical detection only")
        test_data = data
    
    # Detect anomalies
    print("\nDetecting anomalies...")
    anomalies = detector.detect(test_data)
    print(f"Found {len(anomalies)} anomalies")
    
    # Analyze anomaly distribution
    severity_counts = {}
    for anomaly in anomalies:
        severity_counts[anomaly.severity.value] = severity_counts.get(anomaly.severity.value, 0) + 1
    
    print("\nAnomaly Distribution by Severity:")
    for severity, count in sorted(severity_counts.items()):
        print(f"  {severity.capitalize()}: {count}")
    
    # Print details of top anomalies
    print_anomaly_details(anomalies)
    
    # Visualize results
    print("\nGenerating visualization...")
    fig = visualize_anomalies(
        test_data, 
        anomalies, 
        title="Health Activity: Temporal Anomaly Detection"
    )
    
    # Save or show plot
    output_path = "temporal_anomaly_detection.png"
    fig.savefig(output_path, dpi=150, bbox_inches='tight')
    print(f"Visualization saved to: {output_path}")
    
    # Show plot if in interactive mode
    try:
        plt.show()
    except:
        pass
    
    # Summary statistics
    print("\n" + "="*60)
    print("Detection Summary")
    print("="*60)
    print(f"Total data points: {len(test_data)}")
    print(f"Anomalies detected: {len(anomalies)}")
    print(f"Anomaly rate: {len(anomalies)/len(test_data)*100:.1f}%")
    
    if detector.ml_detector and detector.ml_detector.is_trained:
        print(f"Detection mode: Hybrid (Statistical + LSTM)")
    else:
        print(f"Detection mode: Statistical only")
    
    # Agreement analysis for hybrid mode
    if anomalies and 'detection_agreement' in anomalies[0].context:
        agreements = [a.context['detection_agreement'] for a in anomalies]
        print("\nDetection Agreement:")
        for agreement_type in set(agreements):
            count = agreements.count(agreement_type)
            print(f"  {agreement_type}: {count} ({count/len(agreements)*100:.1f}%)")


if __name__ == "__main__":
    main()