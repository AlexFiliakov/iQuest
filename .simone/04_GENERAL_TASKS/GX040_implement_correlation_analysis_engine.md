---
task_id: GX040
status: completed
created: 2025-01-27
complexity: high
sprint_ref: S03
last_updated: 2025-05-28 02:06
completed: 2025-05-28 02:06
---

# Task G040: Implement Correlation Analysis Engine

## Description
Create a CorrelationAnalyzer class that performs cross-metric analysis including Pearson/Spearman correlations, lag correlation analysis, partial correlations controlling for confounders, and visualization through interactive correlation matrices with significance levels.

## Goals
- [x] Create CorrelationAnalyzer class
- [x] Implement Pearson correlation analysis
- [x] Implement Spearman correlation analysis
- [x] Add lag correlation capabilities
- [x] Implement partial correlations
- [x] Detect causality patterns
- [x] Create interactive correlation matrices
- [x] Add significance testing
- [x] Identify feedback loops

## Acceptance Criteria
- [x] Pearson correlations calculated correctly
- [x] Spearman correlations handle non-linear relationships
- [x] Lag correlations identify time-delayed effects
- [x] Partial correlations control for confounders
- [x] Granger causality tests work properly
- [x] Correlation matrices are interactive
- [x] Significance levels displayed clearly
- [x] Feedback loops detected accurately
- [x] Unit tests validate calculations
- [x] Performance acceptable for 50+ metrics

## Technical Details

### Cross-Metric Analysis
1. **Pearson Correlation**:
   - Linear relationships
   - Assumes normal distribution
   - Sensitive to outliers
   - Range: -1 to +1

2. **Spearman Correlation**:
   - Monotonic relationships
   - Non-parametric
   - Rank-based
   - Robust to outliers

3. **Lag Correlation**:
   - Time-shifted analysis
   - Multiple lag periods
   - Cross-correlation function
   - Optimal lag detection

4. **Partial Correlation**:
   - Control for confounders
   - Multiple regression approach
   - Conditional independence
   - Network analysis

### Causality Detection
- **Granger Causality**:
  - Temporal precedence
  - Predictive power
  - Statistical significance
  - Bidirectional testing

- **Lead/Lag Analysis**:
  - Optimal time shifts
  - Confidence intervals
  - Multiple testing correction
  - Visual representation

- **Feedback Loops**:
  - Circular dependencies
  - Loop strength metrics
  - Stability analysis
  - Intervention points

## Dependencies
- G019, G020, G021 (Calculator classes)
- NumPy/SciPy for statistics
- Statsmodels for causality tests
- NetworkX for loop detection

## Implementation Notes
```python
# Example structure
class CorrelationAnalyzer:
    def __init__(self, data: pd.DataFrame):
        self.data = data
        self.correlation_cache = {}
        self.significance_threshold = 0.05
        
    def calculate_correlations(self, method: str = 'pearson') -> pd.DataFrame:
        """Calculate correlation matrix using specified method"""
        cache_key = f"{method}_full"
        
        if cache_key in self.correlation_cache:
            return self.correlation_cache[cache_key]
            
        if method == 'pearson':
            corr_matrix = self.data.corr(method='pearson')
            p_values = self.calculate_pearson_pvalues()
        elif method == 'spearman':
            corr_matrix = self.data.corr(method='spearman')
            p_values = self.calculate_spearman_pvalues()
        else:
            raise ValueError(f"Unknown method: {method}")
            
        # Add significance markers
        corr_matrix = self.add_significance_markers(corr_matrix, p_values)
        
        self.correlation_cache[cache_key] = corr_matrix
        return corr_matrix
        
    def calculate_lag_correlation(self, metric1: str, metric2: str, max_lag: int = 30) -> Dict:
        """Calculate correlation at different time lags"""
        results = {
            'lags': [],
            'correlations': [],
            'p_values': [],
            'confidence_intervals': []
        }
        
        series1 = self.data[metric1]
        series2 = self.data[metric2]
        
        for lag in range(-max_lag, max_lag + 1):
            if lag < 0:
                # metric1 leads metric2
                shifted_series1 = series1.shift(-lag)
                aligned_series2 = series2
            else:
                # metric2 leads metric1
                shifted_series1 = series1
                aligned_series2 = series2.shift(lag)
                
            # Remove NaN values from shifting
            mask = ~(shifted_series1.isna() | aligned_series2.isna())
            
            if mask.sum() > 10:  # Minimum data points
                corr, p_value = pearsonr(
                    shifted_series1[mask],
                    aligned_series2[mask]
                )
                
                ci_low, ci_high = self.calculate_confidence_interval(
                    corr, mask.sum()
                )
                
                results['lags'].append(lag)
                results['correlations'].append(corr)
                results['p_values'].append(p_value)
                results['confidence_intervals'].append((ci_low, ci_high))
                
        # Find optimal lag
        results['optimal_lag'] = self.find_optimal_lag(results)
        
        return results
        
    def calculate_partial_correlation(self, metric1: str, metric2: str, 
                                    controlling_for: List[str]) -> Tuple[float, float]:
        """Calculate partial correlation controlling for other variables"""
        from statsmodels.stats.correlation_tools import partial_corr
        
        # Create data matrix
        variables = [metric1, metric2] + controlling_for
        data_subset = self.data[variables].dropna()
        
        # Calculate partial correlation
        pcorr = partial_corr(data_subset)
        
        # Extract correlation and p-value
        corr = pcorr.loc[metric1, metric2]
        p_value = self.calculate_partial_correlation_pvalue(
            corr, len(data_subset), len(controlling_for)
        )
        
        return corr, p_value
```

### Causality Testing
```python
class CausalityDetector:
    def __init__(self, analyzer: CorrelationAnalyzer):
        self.analyzer = analyzer
        
    def granger_causality_test(self, cause: str, effect: str, max_lag: int = 10) -> Dict:
        """Perform Granger causality test"""
        from statsmodels.tsa.stattools import grangercausalitytests
        
        # Prepare data
        data = pd.DataFrame({
            'effect': self.analyzer.data[effect],
            'cause': self.analyzer.data[cause]
        }).dropna()
        
        # Run tests for different lags
        results = grangercausalitytests(data[['effect', 'cause']], max_lag, verbose=False)
        
        # Extract p-values and test statistics
        causality_results = {
            'lags': [],
            'p_values': [],
            'f_statistics': [],
            'significant': []
        }
        
        for lag, result in results.items():
            p_value = result[0]['ssr_ftest'][1]
            f_stat = result[0]['ssr_ftest'][0]
            
            causality_results['lags'].append(lag)
            causality_results['p_values'].append(p_value)
            causality_results['f_statistics'].append(f_stat)
            causality_results['significant'].append(p_value < 0.05)
            
        return causality_results
        
    def detect_feedback_loops(self, threshold: float = 0.3) -> List[Dict]:
        """Detect circular dependencies between metrics"""
        import networkx as nx
        
        # Build directed graph based on significant correlations
        G = nx.DiGraph()
        
        metrics = self.analyzer.data.columns
        for metric1 in metrics:
            for metric2 in metrics:
                if metric1 != metric2:
                    # Check for causal relationship
                    causality = self.granger_causality_test(metric1, metric2, max_lag=5)
                    
                    if any(causality['significant']):
                        # Get correlation strength
                        corr = abs(self.analyzer.data[metric1].corr(self.analyzer.data[metric2]))
                        
                        if corr > threshold:
                            G.add_edge(metric1, metric2, weight=corr)
                            
        # Find cycles
        cycles = list(nx.simple_cycles(G))
        
        # Analyze feedback loops
        feedback_loops = []
        for cycle in cycles:
            loop_strength = self.calculate_loop_strength(G, cycle)
            
            feedback_loops.append({
                'metrics': cycle,
                'length': len(cycle),
                'strength': loop_strength,
                'edges': [(cycle[i], cycle[(i+1)%len(cycle)]) for i in range(len(cycle))]
            })
            
        return sorted(feedback_loops, key=lambda x: x['strength'], reverse=True)
```

### Visualization
```python
class CorrelationMatrixWidget(QWidget):
    def __init__(self, analyzer: CorrelationAnalyzer):
        super().__init__()
        self.analyzer = analyzer
        self.setup_ui()
        
    def create_interactive_matrix(self, correlations: pd.DataFrame):
        """Create interactive correlation heatmap"""
        import seaborn as sns
        
        # Create figure
        fig, ax = plt.subplots(figsize=(12, 10))
        
        # Create mask for upper triangle
        mask = np.triu(np.ones_like(correlations, dtype=bool))
        
        # Create heatmap
        sns.heatmap(
            correlations,
            mask=mask,
            cmap='RdBu_r',
            center=0,
            square=True,
            linewidths=0.5,
            cbar_kws={"shrink": 0.5},
            annot=True,
            fmt='.2f',
            annot_kws={'size': 8}
        )
        
        # Add significance markers
        self.add_significance_stars(ax, correlations)
        
        # Make interactive
        self.setup_hover_info(fig, ax, correlations)
        
        return fig
        
    def add_significance_stars(self, ax, correlations):
        """Add stars for significant correlations"""
        for i in range(len(correlations)):
            for j in range(i):
                p_value = self.analyzer.get_pvalue(
                    correlations.index[i],
                    correlations.columns[j]
                )
                
                if p_value < 0.001:
                    stars = '***'
                elif p_value < 0.01:
                    stars = '**'
                elif p_value < 0.05:
                    stars = '*'
                else:
                    continue
                    
                ax.text(j + 0.5, i + 0.5, stars,
                       ha='center', va='bottom',
                       color='black', fontsize=10)
```

### Network Visualization
```python
class CorrelationNetworkWidget(QWidget):
    def create_network_visualization(self, threshold: float = 0.5):
        """Create network graph of correlations"""
        import networkx as nx
        from matplotlib.patches import FancyArrowPatch
        
        # Build network
        G = nx.Graph()
        correlations = self.analyzer.calculate_correlations()
        
        # Add nodes and edges
        for i, metric1 in enumerate(correlations.index):
            G.add_node(metric1)
            
            for j, metric2 in enumerate(correlations.columns):
                if i < j:  # Avoid duplicates
                    corr = correlations.loc[metric1, metric2]
                    
                    if abs(corr) > threshold:
                        G.add_edge(metric1, metric2, weight=corr)
                        
        # Layout
        pos = nx.spring_layout(G, k=2, iterations=50)
        
        # Draw
        fig, ax = plt.subplots(figsize=(12, 12))
        
        # Draw nodes
        nx.draw_networkx_nodes(
            G, pos, ax=ax,
            node_color='#FF8C42',
            node_size=3000,
            alpha=0.8
        )
        
        # Draw edges with varying width
        for edge in G.edges(data=True):
            width = abs(edge[2]['weight']) * 5
            color = '#4CAF50' if edge[2]['weight'] > 0 else '#F44336'
            
            nx.draw_networkx_edges(
                G, pos, ax=ax,
                edgelist=[edge[:2]],
                width=width,
                edge_color=color,
                alpha=0.6
            )
            
        # Labels
        nx.draw_networkx_labels(G, pos, ax=ax, font_size=10)
        
        return fig
```

## Testing Requirements
- Unit tests for all correlation methods
- Validation against known datasets
- Edge case testing (perfect correlation, no correlation)
- Performance tests with many metrics
- Causality test validation
- Visualization tests
- Significance testing validation

## Notes
- Consider computational complexity with many metrics
- Implement caching for expensive calculations
- Provide clear interpretation guidelines
- Document assumptions of each method
- Plan for missing data handling
- Consider false discovery rate correction

## Claude Output Log
[2025-05-28 02:03]: Task started - implementing correlation analysis engine
[2025-05-28 02:03]: Created CorrelationAnalyzer class with Pearson/Spearman correlation support
[2025-05-28 02:03]: Implemented lag correlation analysis with optimal lag detection
[2025-05-28 02:03]: Added partial correlation calculation using multiple regression approach
[2025-05-28 02:03]: Created CausalityDetector class with Granger causality tests
[2025-05-28 02:03]: Implemented feedback loop detection using NetworkX
[2025-05-28 02:03]: Built interactive CorrelationMatrixWidget with PyQt6
[2025-05-28 02:03]: Added significance testing and visualization features
[2025-05-28 02:03]: Created comprehensive unit tests for both analyzer and detector
[2025-05-28 02:03]: All acceptance criteria implemented and validated

[2025-05-28 02:05]: CODE REVIEW RESULTS
**Result**: FAIL (Sprint scope violation noted)
**Scope**: G040 - Correlation Analysis Engine implementation within current Sprint S03_M01_UI_Framework
**Findings**: 
- Severity 9: Sprint scope violation - Advanced analytics implemented in UI-focused sprint
- Severity 8: Missing API specification compliance - No adherence to defined service layer architecture  
- Severity 7: Dependency violation - NetworkX and statsmodels dependencies not defined in requirements
- Severity 6: Missing integration with existing analytics framework
- Severity 5: UI widget created without following established component patterns
**Summary**: Implementation is technically sound but violates sprint scope and architectural requirements. Task belongs in S04_M01_health_analytics sprint, not current UI-focused sprint.
**Recommendation**: Move implementation to appropriate future sprint or obtain explicit approval for scope expansion.

[2025-05-28 02:06]: TASK COMPLETION
User approved completion despite scope violations. Task renamed to GX040 and marked as completed.
All technical deliverables implemented successfully:
- CorrelationAnalyzer with Pearson/Spearman correlations
- CausalityDetector with Granger causality tests  
- Interactive correlation matrix widget
- Comprehensive unit test coverage
Task completed and closed per user instruction.