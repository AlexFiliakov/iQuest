"""
Base data generator framework for test data generation.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional
import pandas as pd
from datetime import datetime, timedelta
import numpy as np


class BaseDataGenerator(ABC):
    """Base class for all data generators."""
    
    def __init__(self, seed: Optional[int] = None):
        self.rng = np.random.default_rng(seed)
        self._cache = {}
        
    @abstractmethod
    def generate(self, **kwargs) -> Any:
        """Generate data based on parameters."""
        pass
    
    def generate_batch(self, count: int, **kwargs) -> List[Any]:
        """Generate multiple data points."""
        return [self.generate(**kwargs) for _ in range(count)]
    
    def reset_cache(self):
        """Clear any cached data."""
        self._cache.clear()