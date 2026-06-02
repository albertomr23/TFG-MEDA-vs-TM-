# Recommended Fixes for Critical Issues

## Issue #1: Wrong Import in tm_wrapper.py

### Current Code (BROKEN)
```python
# src/models/tm_wrapper.py, line 4
from yaml import warnings  # ❌ WRONG
```

### Fix
```python
# src/models/tm_wrapper.py, line 4
import warnings  # ✅ CORRECT
```

### Why This Matters
The `yaml` module doesn't have a `warnings` attribute. This will cause:
```
AttributeError: module 'yaml' has no attribute 'warnings'
```
when any warning is issued in the TM module.

---

## Issue #2: Consolidate Duplicate Dataset Loading

### Current State (7 copies)
```python
# Duplicated in: main.py, exp_05_hybrid.py, exp_06_pure_comparison.py, 
#               exp_08_inverse_hybrid_latent.py, exp_meda_04_v2.py, 
#               exp_07_extract_rules.py, exp_10_final_translator.py
```

### Proposed Solution

Create `src/data/loaders.py`:
```python
# src/data/loaders.py

import os
import numpy as np
import pandas as pd
from pathlib import Path

class DatasetLoader:
    """Centralized dataset loading with configurable column indices."""
    
    # Dataset schema definitions
    DATASET_SCHEMAS = {
        'simulated': {
            'target_col': 0,
            'feature_cols': slice(1, None),
            'target_encoder': None  # Direct binary encoding
        },
        'simulated_hd': {
            'target_col': 0,
            'feature_cols': slice(1, None),
            'target_encoder': None
        },
        'real': {
            'target_col': 15,
            'feature_cols': slice(16, None),
            'target_encoder': lambda y: np.where(y > 0, 1, 0)
        }
    }
    
    def __init__(self, project_root: str = None):
        """Initialize with optional custom project root."""
        if project_root is None:
            # Auto-detect from this file's location
            self.project_root = Path(__file__).parent.parent.parent
        else:
            self.project_root = Path(project_root)
    
    def load(self, dataset_type: str) -> tuple:
        """
        Load dataset with validation.
        
        Args:
            dataset_type: 'simulated', 'simulated_hd', or 'real'
            
        Returns:
            Tuple of (X, y, feature_names, dataset_type)
            
        Raises:
            ValueError: If dataset type unknown or file not found
        """
        if dataset_type not in self.DATASET_SCHEMAS:
            raise ValueError(f"Unknown dataset type: {dataset_type}")
        
        schema = self.DATASET_SCHEMAS[dataset_type]
        
        # Map dataset type to filename
        filename_map = {
            'simulated': 'dataset_simulado_3000.xlsx',
            'simulated_hd': 'dataset_simulado2.xlsx',
            'real': 'dataset_real.xlsx'
        }
        
        filename = filename_map[dataset_type]
        data_path = self.project_root / "data" / filename
        
        if not data_path.exists():
            raise FileNotFoundError(f"Dataset not found: {data_path}")
        
        # Load data
        try:
            df = pd.read_excel(data_path)
        except Exception as e:
            # Fallback to CSV
            try:
                df = pd.read_csv(data_path.with_suffix('.csv'))
            except Exception:
                raise IOError(f"Cannot load {filename}: {e}")
        
        # Extract features and target
        target_col = schema['target_col']
        feature_slice = schema['feature_cols']
        
        y_raw = df.iloc[:, target_col].values
        X = df.iloc[:, feature_slice].values
        feature_names = df.columns[feature_slice].tolist()
        
        # Apply target encoding if specified
        encoder = schema['target_encoder']
        y = encoder(y_raw) if encoder is not None else y_raw
        
        return X, y, feature_names, dataset_type


def select_and_load_dataset() -> tuple:
    """Interactive dataset selection (backwards compatible)."""
    print("\n" + "="*50)
    print(" 📂 DATASET SELECTION ")
    print("="*50)
    print("1. Simulated Dataset (3000 patients, 40 features)")
    print("2. Real Clinical Dataset (Olga & Eberl - 82 patients)")
    print("3. High-Dim Simulated Dataset (50 patients, 4000 features)")
    
    opcion = input("\nChoose an option (1, 2, or 3): ").strip()
    
    dataset_map = {'1': 'simulated', '2': 'real', '3': 'simulated_hd'}
    dataset_type = dataset_map.get(opcion, 'simulated')
    
    loader = DatasetLoader()
    X, y, feature_names, dataset_type = loader.load(dataset_type)
    
    print(f"✅ Dataset loaded: {X.shape[0]} patients, {X.shape[1]} features")
    return X, y, feature_names, dataset_type
```

### Usage in Experiment Files
```python
# Before (old approach - in every file):
def select_and_load_dataset():
    # ... 40+ lines of duplicated code ...

# After (new approach - one import):
from data.loaders import select_and_load_dataset

X, y, feature_names, dataset_type = select_and_load_dataset()
```

---

## Issue #3: Fix Silent vASCA Failures

### Current Code (BROKEN)
```python
# src/exp_08_inverse_hybrid_latent.py, lines 50-55
def fit(self, X, y):
    try:
        self.selector_.fit(X, y)
        self.selected_indices_ = self.selector_.selected_features_
    except Exception as e:
        # If the matrix goes singular (which will happen with vASCA + Boolean clauses)
        print(f"  [!] {self.method.upper()} crashed: {e}. Passing all features.")
        self.selected_indices_ = list(range(X.shape[1]))  # ❌ Silent fallback
    return self
```

### Problems with Current Approach
1. **Silent Failure**: No indication that feature selection failed
2. **Defeats Purpose**: Passes all features, making feature selection useless
3. **Generic Exception**: Catches programming errors too

### Proposed Fix
```python
# src/pipelines/meda_filter.py

import warnings
import logging
from sklearn.base import BaseEstimator, TransformerMixin
from models.r_wrapper import RWrapper

logger = logging.getLogger(__name__)

class MEDAFilter(BaseEstimator, TransformerMixin):
    """Feature selection filter using R-based MEDA methods."""
    
    def __init__(self, method='splsda', n_components=2, sparsity_penalty=0.3):
        if method not in ['splsda', 'vasca', 'asca', 'spca', 'pca']:
            raise ValueError(f"Unknown method: {method}")
        
        self.method = method
        self.n_components = n_components
        self.sparsity_penalty = sparsity_penalty
        self.selector_ = None
        self.selected_indices_ = None
        self.n_features_in_ = None
        self.fit_failed_ = False
    
    def fit(self, X, y):
        """Fit feature selector with proper error handling."""
        self.n_features_in_ = X.shape[1]
        self.selector_ = RWrapper(
            method=self.method,
            n_components=self.n_components,
            sparsity_penalty=self.sparsity_penalty
        )
        
        try:
            self.selector_.fit(X, y)
            self.selected_indices_ = self.selector_.selected_features_
            self.fit_failed_ = False
            
            n_selected = len(self.selected_indices_)
            logger.info(
                f"{self.method.upper()} selected {n_selected}/{self.n_features_in_} features"
            )
            
        except NotImplementedError as e:
            # Expected for unsupervised methods
            logger.warning(f"{self.method.upper()} is unsupervised: {e}")
            self.selected_indices_ = list(range(self.n_features_in_))
            self.fit_failed_ = True
            
        except ValueError as e:
            # Singular matrix or similar mathematical issue
            logger.error(f"{self.method.upper()} failed (singular matrix?): {e}")
            self.selected_indices_ = list(range(self.n_features_in_))
            self.fit_failed_ = True
            
            # Optional: raise to make failure explicit
            # raise RuntimeError(
            #     f"Feature selection {self.method.upper()} failed. "
            #     f"Consider using simpler method or checking data quality."
            # ) from e
            
        except Exception as e:
            # Unexpected error
            logger.exception(f"Unexpected error in {self.method.upper()}: {e}")
            self.selected_indices_ = list(range(self.n_features_in_))
            self.fit_failed_ = True
        
        return self
    
    def transform(self, X):
        """Transform data using selected features."""
        if self.selected_indices_ is None:
            raise RuntimeError("Fit must be called before transform")
        
        if self.fit_failed_:
            warnings.warn(
                f"{self.method.upper()} feature selection failed. Using all features.",
                UserWarning
            )
        
        if len(self.selected_indices_) == 0:
            return X
        
        return X[:, self.selected_indices_]
    
    def get_feature_names_out(self, input_features=None):
        """Get output feature names (sklearn compatible)."""
        if self.selected_indices_ is None:
            raise RuntimeError("Fit must be called before get_feature_names_out")
        
        if input_features is None:
            input_features = [f"Feature_{i}" for i in range(self.n_features_in_)]
        
        return [input_features[i] for i in self.selected_indices_]
```

---

## Issue #4: Standardize Parameter Naming

### Current State (BROKEN)
```python
# Inconsistent across codebase:
TMWrapper(..., num_bins=4)              # Long form
SmartBooleanizer(..., n_bins=4)         # Short form
TMClauseExtractor(..., num_bins=3)      # Mixed
```

### Proposed Solution

**Convention**: Use `n_bins` everywhere (consistent with scikit-learn)

1. **Update TMWrapper**:
```python
# Before:
def __init__(self, ..., num_bins=4):

# After:
def __init__(self, ..., n_bins=4):
    self.n_bins = n_bins
```

2. **Create compatibility mapper**:
```python
# If supporting legacy code:
def __init__(self, ..., num_bins=None, n_bins=None):
    if num_bins is not None and n_bins is None:
        warnings.warn("num_bins is deprecated, use n_bins", DeprecationWarning)
        self.n_bins = num_bins
    elif n_bins is not None:
        self.n_bins = n_bins
    else:
        self.n_bins = 4  # default
```

---

## Issue #5: Add Type Annotations

### Before (All files)
```python
def fit(self, X, y):
    """Fit the model."""
    ...

def transform(self, X):
    return X[:, self.selected_indices_]

def predict(self, X):
    return self.model_.predict(X)
```

### After (Recommended)
```python
from typing import Union, Tuple, Optional, List
import numpy as np
import pandas as pd

def fit(self, X: Union[np.ndarray, pd.DataFrame], 
        y: np.ndarray) -> 'MEDAFilter':
    """
    Fit feature selector.
    
    Args:
        X: Feature matrix (n_samples, n_features)
        y: Target labels (n_samples,)
    
    Returns:
        self: Fitted estimator
    """
    ...
    return self

def transform(self, X: Union[np.ndarray, pd.DataFrame]) -> np.ndarray:
    """
    Transform data using selected features.
    
    Args:
        X: Feature matrix (n_samples, n_features)
    
    Returns:
        Transformed data (n_samples, n_selected_features)
    """
    return X[:, self.selected_indices_]

def predict(self, X: np.ndarray) -> np.ndarray:
    """
    Make predictions.
    
    Args:
        X: Feature matrix (n_samples, n_features)
    
    Returns:
        Predicted labels (n_samples,)
    """
    return self.model_.predict(X)
```

---

## Issue #6: Input Validation

### Before (No validation)
```python
class RWrapper(BaseEstimator, ClassifierMixin):
    def __init__(self, method='splsda', n_components=2, sparsity_penalty=0.5):
        self.method = method
        self.n_components = n_components
        self.sparsity_penalty = sparsity_penalty
```

### After (With validation)
```python
class RWrapper(BaseEstimator, ClassifierMixin):
    def __init__(self, method='splsda', n_components=2, sparsity_penalty=0.5):
        # Validate method
        valid_methods = ['splsda', 'vasca', 'asca', 'spca', 'pca']
        if method not in valid_methods:
            raise ValueError(
                f"method must be one of {valid_methods}, got '{method}'"
            )
        
        # Validate n_components
        if not isinstance(n_components, int) or n_components < 1:
            raise ValueError(
                f"n_components must be positive integer, got {n_components}"
            )
        
        # Validate sparsity_penalty
        if not 0 <= sparsity_penalty <= 1:
            raise ValueError(
                f"sparsity_penalty must be in [0, 1], got {sparsity_penalty}"
            )
        
        self.method = method
        self.n_components = n_components
        self.sparsity_penalty = sparsity_penalty

    def fit(self, X, y):
        """Fit model with data validation."""
        from sklearn.utils.validation import check_X_y
        
        # Validates X and y dimensions, types, etc.
        X, y = check_X_y(X, y, accept_sparse=False, y_numeric=False)
        
        # Additional custom validation
        if X.ndim != 2:
            raise ValueError(f"X must be 2D, got shape {X.shape}")
        
        if len(y) != X.shape[0]:
            raise ValueError(
                f"X and y have incompatible sizes: {X.shape[0]} != {len(y)}"
            )
        
        # ... rest of fit logic ...
```

---

## Issue #7: Create Configuration System

### Proposed: `src/config.py`
```python
"""Centralized configuration for the project."""

from pathlib import Path
from typing import Dict, Any

class Config:
    """Project-wide configuration."""
    
    # Paths
    PROJECT_ROOT = Path(__file__).parent.parent
    DATA_DIR = PROJECT_ROOT / "data"
    RESULTS_DIR = PROJECT_ROOT / "results"
    
    # Dataset schemas (hardcoded column indices)
    DATASET_SCHEMAS = {
        'simulated': {
            'filename': 'dataset_simulado_3000.xlsx',
            'target_col': 0,
            'feature_cols': slice(1, None),
            'n_samples': 3000,
            'n_features': 40,
        },
        'simulated_hd': {
            'filename': 'dataset_simulado2.xlsx',
            'target_col': 0,
            'feature_cols': slice(1, None),
            'n_samples': 50,
            'n_features': 4000,
        },
        'real': {
            'filename': 'dataset_real.xlsx',
            'target_col': 15,
            'feature_cols': slice(16, None),
            'n_samples': 82,
            'n_features': None,  # Variable
        }
    }
    
    # Pipeline hyperparameters
    PIPELINE_HYPERPARAMS = {
        'n_bins': 3,
        'n_components_meda': 2,
        'sparsity_penalty': 0.3,
        'n_clauses': 100,
        'T': 15,
        's': 3.9,
    }
    
    # Cross-validation
    CV_OUTER_SPLITS = 5
    CV_INNER_SPLITS = 3
    RANDOM_STATE = 42
    
    # Results subdirectories per experiment
    RESULTS_SUBDIRS = {
        'main': 'main',
        'exp_05_hybrid': 'hybrid',
        'exp_06_pure': 'versus',
        'exp_08_inverse': 'inverse_latent',
        'exp_07_rules': 'rules',
        'exp_meda': 'meda_puro',
    }
    
    @classmethod
    def get_results_dir(self, experiment_name: str) -> Path:
        """Get results directory for an experiment."""
        subdir = self.RESULTS_SUBDIRS.get(experiment_name, 'results')
        path = self.RESULTS_DIR / subdir
        path.mkdir(parents=True, exist_ok=True)
        return path
    
    @classmethod
    def get_dataset_schema(cls, dataset_type: str) -> Dict[str, Any]:
        """Get schema for a dataset type."""
        if dataset_type not in cls.DATASET_SCHEMAS:
            raise ValueError(f"Unknown dataset type: {dataset_type}")
        return cls.DATASET_SCHEMAS[dataset_type]


# Usage in experiment files:
# from config import Config
# 
# schema = Config.get_dataset_schema('simulated')
# results_dir = Config.get_results_dir('exp_05_hybrid')
# n_bins = Config.PIPELINE_HYPERPARAMS['n_bins']
```

---

## Summary of Recommended Actions

| Priority | Issue | File(s) | Estimated Time |
|----------|-------|---------|-----------------|
| CRITICAL | Fix yaml import | tm_wrapper.py | 5 min |
| CRITICAL | Extract dataset loader | All exp_*.py | 30 min |
| CRITICAL | Fix silent failures | exp_05,08 | 20 min |
| HIGH | Consolidate MEDAFilter | 6 files | 30 min |
| HIGH | Add type annotations | All files | 2 hours |
| HIGH | Add input validation | All models | 1 hour |
| MEDIUM | Create config system | New file | 1 hour |
| MEDIUM | Standardize param naming | All files | 45 min |
| MEDIUM | Consolidate TMClauseExtractor | 3 files | 20 min |

**Total Estimated Refactoring Time**: 6-8 hours

---

## Testing Recommendations

After implementing fixes, add tests:

```python
# tests/test_data_loader.py
import pytest
from data.loaders import DatasetLoader

def test_dataset_loader_simulated():
    loader = DatasetLoader()
    X, y, names, dtype = loader.load('simulated')
    assert X.shape == (3000, 40)
    assert len(y) == 3000
    assert dtype == 'simulated'

def test_dataset_loader_invalid():
    loader = DatasetLoader()
    with pytest.raises(ValueError):
        loader.load('unknown_type')

def test_meda_filter_with_invalid_params():
    with pytest.raises(ValueError):
        MEDAFilter(method='invalid')

def test_meda_filter_fit_fail_graceful():
    filter = MEDAFilter(method='vasca')
    # Create singular data that causes vASCA to fail
    X = np.ones((10, 5))  # Singular!
    y = np.array([0, 1] * 5)
    
    # Should not raise, but should log warning
    filter.fit(X, y)
    assert filter.fit_failed_ == True
```

