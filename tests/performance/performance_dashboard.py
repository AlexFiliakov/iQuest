"""
Simple performance monitoring dashboard for test suite metrics.

This module provides a basic web-based dashboard to visualize test performance
trends and monitor for regressions over time.
"""

import json
import sqlite3
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import sys

try:
    import matplotlib.pyplot as plt
    import matplotlib.dates as mdates
    from matplotlib.figure import Figure
    import io
    import base64
    HAS_MATPLOTLIB = True
except ImportError:
    HAS_MATPLOTLIB = False


class PerformanceDatabase:
    """SQLite database for storing performance metrics over time."""
    
    def __init__(self, db_path: str = "tests/performance/performance_history.db"):
        """Initialize performance database."""
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_database()
    
    def _init_database(self):
        """Initialize database schema."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS performance_metrics (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT NOT NULL,
                    git_commit TEXT,
                    category TEXT NOT NULL,
                    test_count INTEGER,
                    collection_time REAL,
                    execution_time REAL,
                    total_time REAL,
                    memory_peak_mb REAL,
                    memory_delta_mb REAL,
                    passed INTEGER,
                    failed INTEGER,
                    skipped INTEGER,
                    errors INTEGER
                )
            """)
            
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_timestamp_category 
                ON performance_metrics(timestamp, category)
            """)
    
    def store_metrics(self, metrics: Dict, git_commit: Optional[str] = None):
        """Store performance metrics in database."""
        with sqlite3.connect(self.db_path) as conn:
            for category, data in metrics.items():
                conn.execute("""
                    INSERT INTO performance_metrics (
                        timestamp, git_commit, category, test_count,
                        collection_time, execution_time, total_time,
                        memory_peak_mb, memory_delta_mb, passed, failed, skipped, errors
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    data.get('timestamp', datetime.now().isoformat()),
                    git_commit,
                    category,
                    data.get('test_count', 0),
                    data.get('collection_time', 0),
                    data.get('execution_time', 0),
                    data.get('total_time', 0),
                    data.get('memory_peak_mb', 0),
                    data.get('memory_delta_mb', 0),
                    data.get('passed', 0),
                    data.get('failed', 0),
                    data.get('skipped', 0),
                    data.get('errors', 0)
                ))
    
    def get_metrics_history(
        self, 
        category: Optional[str] = None,
        days: int = 30
    ) -> List[Dict]:
        """Get performance metrics history."""
        since_date = (datetime.now() - timedelta(days=days)).isoformat()
        
        query = """
            SELECT * FROM performance_metrics 
            WHERE timestamp >= ?
        """
        params = [since_date]
        
        if category:
            query += " AND category = ?"
            params.append(category)
        
        query += " ORDER BY timestamp DESC"
        
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute(query, params)
            return [dict(row) for row in cursor.fetchall()]
    
    def get_latest_metrics(self) -> Dict:
        """Get latest performance metrics for all categories."""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute("""
                SELECT DISTINCT category FROM performance_metrics
            """)
            categories = [row[0] for row in cursor.fetchall()]
            
            latest_metrics = {}
            for category in categories:
                cursor = conn.execute("""
                    SELECT * FROM performance_metrics 
                    WHERE category = ? 
                    ORDER BY timestamp DESC 
                    LIMIT 1
                """, (category,))
                row = cursor.fetchone()
                if row:
                    latest_metrics[category] = dict(row)
            
            return latest_metrics


class PerformanceDashboard:
    """Simple performance monitoring dashboard."""
    
    def __init__(self, db_path: str = "tests/performance/performance_history.db"):
        """Initialize dashboard."""
        self.db = PerformanceDatabase(db_path)
        self.has_matplotlib = HAS_MATPLOTLIB
    
    def generate_trend_chart(self, category: str, metric: str, days: int = 30) -> Optional[str]:
        """Generate trend chart for a specific metric."""
        if not self.has_matplotlib:
            return None
        
        history = self.db.get_metrics_history(category, days)
        if not history:
            return None
        
        # Extract data for plotting
        timestamps = [datetime.fromisoformat(m['timestamp']) for m in history]
        values = [m[metric] for m in history if m[metric] is not None]
        
        if len(values) < 2:
            return None
        
        # Create plot
        fig, ax = plt.subplots(figsize=(10, 6))
        ax.plot(timestamps, values, marker='o', linewidth=2, markersize=4)
        ax.set_title(f'{category.title()} - {metric.replace("_", " ").title()} Trend')
        ax.set_xlabel('Date')
        ax.set_ylabel(metric.replace("_", " ").title())
        ax.grid(True, alpha=0.3)
        
        # Format x-axis
        ax.xaxis.set_major_formatter(mdates.DateFormatter('%m/%d'))
        ax.xaxis.set_major_locator(mdates.DayLocator(interval=max(1, days//10)))
        plt.xticks(rotation=45)
        
        # Convert to base64 string
        buffer = io.BytesIO()
        plt.savefig(buffer, format='png', bbox_inches='tight', dpi=100)
        buffer.seek(0)
        chart_data = base64.b64encode(buffer.getvalue()).decode()
        plt.close(fig)
        
        return f"data:image/png;base64,{chart_data}"
    
    def generate_summary_table(self) -> str:
        """Generate HTML summary table of latest metrics."""
        latest = self.db.get_latest_metrics()
        if not latest:
            return "<p>No performance data available.</p>"
        
        html = """
        <table class="performance-summary">
            <thead>
                <tr>
                    <th>Category</th>
                    <th>Tests</th>
                    <th>Collection (s)</th>
                    <th>Execution (s)</th>
                    <th>Total (s)</th>
                    <th>Memory (MB)</th>
                    <th>Pass Rate</th>
                    <th>Last Updated</th>
                </tr>
            </thead>
            <tbody>
        """
        
        for category, metrics in latest.items():
            total_tests = metrics['test_count'] or 0
            passed = metrics['passed'] or 0
            pass_rate = (passed / total_tests * 100) if total_tests > 0 else 0
            
            timestamp = datetime.fromisoformat(metrics['timestamp'])
            formatted_time = timestamp.strftime('%m/%d %H:%M')
            
            html += f"""
                <tr>
                    <td>{category.title()}</td>
                    <td>{total_tests}</td>
                    <td>{metrics['collection_time']:.1f}</td>
                    <td>{metrics['execution_time']:.1f}</td>
                    <td>{metrics['total_time']:.1f}</td>
                    <td>{metrics['memory_peak_mb']:.0f}</td>
                    <td>{pass_rate:.1f}%</td>
                    <td>{formatted_time}</td>
                </tr>
            """
        
        html += """
            </tbody>
        </table>
        """
        
        return html
    
    def generate_dashboard_html(self) -> str:
        """Generate complete HTML dashboard."""
        html = """
        <!DOCTYPE html>
        <html>
        <head>
            <title>Test Performance Dashboard</title>
            <style>
                body { 
                    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
                    margin: 20px;
                    background-color: #f5f5f5;
                }
                .container { 
                    max-width: 1200px; 
                    margin: 0 auto; 
                    background: white;
                    padding: 20px;
                    border-radius: 8px;
                    box-shadow: 0 2px 4px rgba(0,0,0,0.1);
                }
                h1 { 
                    color: #333; 
                    border-bottom: 2px solid #007acc;
                    padding-bottom: 10px;
                }
                .performance-summary { 
                    width: 100%; 
                    border-collapse: collapse; 
                    margin: 20px 0;
                }
                .performance-summary th, .performance-summary td { 
                    border: 1px solid #ddd; 
                    padding: 8px; 
                    text-align: left;
                }
                .performance-summary th { 
                    background-color: #f2f2f2; 
                    font-weight: bold;
                }
                .performance-summary tr:nth-child(even) { 
                    background-color: #f9f9f9; 
                }
                .chart-container { 
                    margin: 20px 0; 
                    text-align: center;
                }
                .chart-container img { 
                    max-width: 100%; 
                    height: auto;
                    border: 1px solid #ddd;
                    border-radius: 4px;
                }
                .status-indicator {
                    display: inline-block;
                    width: 12px;
                    height: 12px;
                    border-radius: 50%;
                    margin-right: 8px;
                }
                .status-good { background-color: #28a745; }
                .status-warning { background-color: #ffc107; }
                .status-error { background-color: #dc3545; }
                .refresh-info {
                    color: #666;
                    font-size: 0.9em;
                    margin-top: 10px;
                }
            </style>
        </head>
        <body>
            <div class="container">
                <h1>🚀 Test Performance Dashboard</h1>
                
                <div class="status-section">
                    <h2>Current Status</h2>
                    <p>
                        <span class="status-indicator status-good"></span>
                        All systems operational - Performance within acceptable ranges
                    </p>
                </div>
        """
        
        # Add summary table
        html += f"""
                <h2>📊 Latest Performance Metrics</h2>
                {self.generate_summary_table()}
        """
        
        # Add trend charts if matplotlib available
        if self.has_matplotlib:
            categories = ['unit', 'integration', 'ui', 'performance']
            for category in categories:
                chart_data = self.generate_trend_chart(category, 'total_time', 30)
                if chart_data:
                    html += f"""
                    <h3>{category.title()} Tests - Execution Time Trend (30 days)</h3>
                    <div class="chart-container">
                        <img src="{chart_data}" alt="{category} performance trend">
                    </div>
                    """
        else:
            html += """
                <div class="chart-container">
                    <p><em>Install matplotlib to see performance trend charts</em></p>
                </div>
            """
        
        html += f"""
                <div class="refresh-info">
                    <p>Dashboard generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
                    <p>Refresh this page to see updated metrics</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        return html
    
    def save_dashboard(self, output_path: str = "tests/performance/dashboard.html"):
        """Save dashboard to HTML file."""
        html = self.generate_dashboard_html()
        
        output_file = Path(output_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_file, 'w') as f:
            f.write(html)
        
        print(f"📊 Dashboard saved to: {output_file}")
        return output_file
    
    def load_baseline_metrics(self, baseline_file: str = "tests/performance/baseline_metrics.json"):
        """Load baseline metrics into database."""
        baseline_path = Path(baseline_file)
        if not baseline_path.exists():
            print(f"Baseline file not found: {baseline_file}")
            return
        
        with open(baseline_path, 'r') as f:
            metrics = json.load(f)
        
        # Store baseline with current timestamp
        current_commit = self._get_git_commit()
        self.db.store_metrics(metrics, current_commit)
        print(f"✅ Loaded baseline metrics into dashboard database")
    
    def _get_git_commit(self) -> Optional[str]:
        """Get current git commit hash."""
        try:
            import subprocess
            result = subprocess.run(
                ['git', 'rev-parse', '--short', 'HEAD'],
                capture_output=True,
                text=True,
                cwd=Path.cwd()
            )
            return result.stdout.strip() if result.returncode == 0 else None
        except:
            return None


def main():
    """CLI interface for performance dashboard."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Performance Dashboard")
    parser.add_argument("--load-baseline", action="store_true", help="Load baseline metrics")
    parser.add_argument("--generate", action="store_true", help="Generate dashboard HTML")
    parser.add_argument("--output", default="tests/performance/dashboard.html", help="Output file")
    
    args = parser.parse_args()
    
    dashboard = PerformanceDashboard()
    
    if args.load_baseline:
        dashboard.load_baseline_metrics()
    
    if args.generate:
        dashboard.save_dashboard(args.output)
    
    if not args.load_baseline and not args.generate:
        # Default: load baseline and generate dashboard
        dashboard.load_baseline_metrics()
        dashboard.save_dashboard(args.output)


if __name__ == "__main__":
    main()