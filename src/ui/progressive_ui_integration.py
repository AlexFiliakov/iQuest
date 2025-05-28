"""UI integration for progressive loading from optimized analytics engine."""

from typing import Dict, Any, Optional, Callable
import logging
from PyQt6.QtCore import QObject, pyqtSignal, QThread
from PyQt6.QtWidgets import QWidget

from ..analytics import (
    ProgressiveLoaderCallbacks, 
    ProgressiveLoader,
    ProgressiveAnalyticsManager,
    OptimizedCalculatorFactory
)

logger = logging.getLogger(__name__)


class ProgressiveLoadingBridge(QObject):
    """
    Bridge between analytics callbacks and PyQt6 signals.
    
    Converts callback-based progressive loading events to Qt signals.
    """
    
    # Qt signals for UI updates
    loading_started = pyqtSignal()
    skeleton_ready = pyqtSignal(dict)
    first_data_ready = pyqtSignal(dict)  # Convert ProgressiveResult to dict
    progress_update = pyqtSignal(dict)
    loading_complete = pyqtSignal(dict)
    loading_error = pyqtSignal(str)
    
    def __init__(self):
        """Initialize the bridge."""
        super().__init__()
        self._callbacks = ProgressiveLoaderCallbacks()
        
        # Connect callbacks to signal emission
        self._callbacks.on_loading_started = self._emit_loading_started
        self._callbacks.on_skeleton_ready = self._emit_skeleton_ready
        self._callbacks.on_first_data_ready = self._emit_first_data_ready
        self._callbacks.on_progress_update = self._emit_progress_update
        self._callbacks.on_loading_complete = self._emit_loading_complete
        self._callbacks.on_loading_error = self._emit_loading_error
        
    def get_callbacks(self) -> ProgressiveLoaderCallbacks:
        """Get callbacks instance for progressive loader."""
        return self._callbacks
    
    def _emit_loading_started(self):
        """Emit loading started signal."""
        self.loading_started.emit()
    
    def _emit_skeleton_ready(self, skeleton_config: dict):
        """Emit skeleton ready signal."""
        self.skeleton_ready.emit(skeleton_config)
    
    def _emit_first_data_ready(self, result):
        """Emit first data ready signal."""
        # Convert ProgressiveResult to dict for Qt signal
        result_dict = {
            'stage': result.stage.name,
            'data': result.data,
            'progress': result.progress,
            'message': result.message,
            'metadata': result.metadata or {}
        }
        self.first_data_ready.emit(result_dict)
    
    def _emit_progress_update(self, result):
        """Emit progress update signal."""
        result_dict = {
            'stage': result.stage.name,
            'data': result.data,
            'progress': result.progress,
            'message': result.message,
            'metadata': result.metadata or {}
        }
        self.progress_update.emit(result_dict)
    
    def _emit_loading_complete(self, result):
        """Emit loading complete signal."""
        result_dict = {
            'stage': result.stage.name,
            'data': result.data,
            'progress': result.progress,
            'message': result.message,
            'metadata': result.metadata or {}
        }
        self.loading_complete.emit(result_dict)
    
    def _emit_loading_error(self, error_msg: str):
        """Emit loading error signal."""
        self.loading_error.emit(error_msg)


class ProgressiveCalculatorWidget(QWidget):
    """
    Base widget class with progressive loading support.
    
    Provides easy integration with optimized calculators.
    """
    
    def __init__(self, calculator_factory: OptimizedCalculatorFactory, parent=None):
        """
        Initialize widget with calculator factory.
        
        Args:
            calculator_factory: Factory for optimized calculators
            parent: Parent widget
        """
        super().__init__(parent)
        self.calculator_factory = calculator_factory
        self._loading_bridge = ProgressiveLoadingBridge()
        self._current_session_id: Optional[str] = None
        
        # Connect signals to default handlers
        self._loading_bridge.loading_started.connect(self.on_loading_started)
        self._loading_bridge.skeleton_ready.connect(self.on_skeleton_ready)
        self._loading_bridge.first_data_ready.connect(self.on_first_data_ready)
        self._loading_bridge.progress_update.connect(self.on_progress_update)
        self._loading_bridge.loading_complete.connect(self.on_loading_complete)
        self._loading_bridge.loading_error.connect(self.on_loading_error)
    
    def start_progressive_calculation(self, calculator_type: str, **kwargs) -> str:
        """
        Start a progressive calculation.
        
        Args:
            calculator_type: Type of calculator ('daily', 'weekly', 'monthly')
            **kwargs: Arguments for the calculation
            
        Returns:
            Session ID for tracking
        """
        # Get appropriate calculator
        if calculator_type == 'daily':
            calculator = self.calculator_factory.get_daily_calculator()
        elif calculator_type == 'weekly':
            calculator = self.calculator_factory.get_weekly_calculator()
        elif calculator_type == 'monthly':
            calculator = self.calculator_factory.get_monthly_calculator()
        else:
            raise ValueError(f"Unknown calculator type: {calculator_type}")
        
        # Set callbacks
        calculator.set_progress_callbacks(self._loading_bridge.get_callbacks())
        
        # Start progressive calculation
        self._current_session_id = calculator.calculate_progressive(**kwargs)
        
        return self._current_session_id
    
    def cancel_current_calculation(self):
        """Cancel the current calculation if running."""
        if self._current_session_id:
            # TODO: Implement cancellation in progressive loader
            logger.info(f"Cancelling calculation: {self._current_session_id}")
            self._current_session_id = None
    
    # Override these methods in subclasses for custom behavior
    
    def on_loading_started(self):
        """Called when loading starts."""
        logger.debug("Progressive loading started")
    
    def on_skeleton_ready(self, skeleton_config: dict):
        """Called when skeleton UI should be shown."""
        logger.debug(f"Skeleton ready: {skeleton_config}")
    
    def on_first_data_ready(self, result: dict):
        """Called when first data is available."""
        logger.debug(f"First data ready: {result['progress']*100:.0f}%")
    
    def on_progress_update(self, result: dict):
        """Called on progress updates."""
        logger.debug(f"Progress update: {result['progress']*100:.0f}%")
    
    def on_loading_complete(self, result: dict):
        """Called when loading is complete."""
        logger.debug("Loading complete")
        self._current_session_id = None
    
    def on_loading_error(self, error_msg: str):
        """Called on loading error."""
        logger.error(f"Loading error: {error_msg}")
        self._current_session_id = None


class CalculatorWorkerThread(QThread):
    """
    Worker thread for running calculations in background.
    
    Useful for non-progressive calculations.
    """
    
    # Signals
    calculation_complete = pyqtSignal(dict)
    calculation_error = pyqtSignal(str)
    
    def __init__(self, calculator: Any, method_name: str, kwargs: dict):
        """
        Initialize worker thread.
        
        Args:
            calculator: Calculator instance
            method_name: Method to call
            kwargs: Arguments for the method
        """
        super().__init__()
        self.calculator = calculator
        self.method_name = method_name
        self.kwargs = kwargs
        
    def run(self):
        """Run the calculation."""
        try:
            # Get the method
            method = getattr(self.calculator, self.method_name)
            
            # Run calculation
            result = method(**self.kwargs)
            
            # Emit result
            self.calculation_complete.emit(result)
            
        except Exception as e:
            logger.error(f"Calculation error: {e}")
            self.calculation_error.emit(str(e))


def create_optimized_calculator_widgets(database_path: str) -> Dict[str, Any]:
    """
    Create UI widgets with optimized calculator support.
    
    Args:
        database_path: Path to SQLite database
        
    Returns:
        Dictionary of widget classes and factory
    """
    # Create factory
    factory = OptimizedCalculatorFactory(database_path)
    
    # Create specialized widget classes
    class OptimizedDailyWidget(ProgressiveCalculatorWidget):
        """Daily metrics widget with optimization."""
        
        def __init__(self, parent=None):
            super().__init__(factory, parent)
            self.calculator = factory.get_daily_calculator()
    
    class OptimizedWeeklyWidget(ProgressiveCalculatorWidget):
        """Weekly metrics widget with optimization."""
        
        def __init__(self, parent=None):
            super().__init__(factory, parent)
            self.calculator = factory.get_weekly_calculator()
    
    class OptimizedMonthlyWidget(ProgressiveCalculatorWidget):
        """Monthly metrics widget with optimization."""
        
        def __init__(self, parent=None):
            super().__init__(factory, parent)
            self.calculator = factory.get_monthly_calculator()
    
    return {
        'factory': factory,
        'DailyWidget': OptimizedDailyWidget,
        'WeeklyWidget': OptimizedWeeklyWidget,
        'MonthlyWidget': OptimizedMonthlyWidget,
        'ProgressiveBridge': ProgressiveLoadingBridge,
        'WorkerThread': CalculatorWorkerThread
    }