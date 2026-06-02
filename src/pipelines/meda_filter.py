"""
Centralized MEDA Filter Transformer.
This is the single source of truth for feature filtering via MEDA methods.
Used across: exp_05, exp_06, exp_07, exp_08, exp_10, exp_meda_04_v2.
"""

import warnings
from sklearn.base import BaseEstimator, TransformerMixin
from models.r_wrapper import RWrapper
import numpy as np


class MEDAFilter(BaseEstimator, TransformerMixin):
    """
    MEDA (Multivariate Exploratory Data Analysis) Filter.
    
    Wrapper for R-based methods (sPLS-DA, vASCA, ASCA) to filter features
    while maintaining a scikit-learn Pipeline interface.
    
    Parameters
    ----------
    method : str
        MEDA method: 'splsda', 'vasca', 'asca', 'pca', or 'spca'
    n_components : int
        Number of latent components to extract
    sparsity_penalty : float
        Proportion of features to KEEP [0.0, 1.0]
        
    Attributes
    ----------
    selected_indices_ : list
        Indices of features selected by the model. Falls back to all features 
        if the method fails (with warning).
    """
    
    def __init__(self, method='splsda', n_components=2, sparsity_penalty=0.3):
        self.method = method
        self.n_components = n_components
        self.sparsity_penalty = sparsity_penalty
        self.selector_ = RWrapper(
            method=self.method,
            n_components=self.n_components,
            sparsity_penalty=self.sparsity_penalty
        )
        self.selected_indices_ = None
        
    def fit(self, X, y):
        """
        Fit the MEDA method on X, y.
        
        If fitting fails (e.g., SVD singular for vASCA on boolean data),
        falls back to using all features with a warning.
        """
        try:
            self.selector_.fit(X, y)
            self.selected_indices_ = self.selector_.selected_features_
        except Exception as e:
            # Graceful fallback for methods that fail on certain data (e.g., vASCA on boolean)
            warnings.warn(
                f"⚠️  {self.method.upper()} failed to fit (likely SVD singular): "
                f"{type(e).__name__}: {str(e)}. "
                f"Using ALL {X.shape[1]} features downstream as fallback. "
                f"Results may not be biologically filtered. "
                f"Consider using a different MEDA method or preprocessing.",
                UserWarning
            )
            self.selected_indices_ = list(range(X.shape[1]))
        return self
        
    def transform(self, X):
        """Select and return only the filtered features."""
        if self.selected_indices_ is None or len(self.selected_indices_) == 0:
            return X
        return X[:, self.selected_indices_]
    
    def get_feature_names_out(self, input_features=None):
        """Return names of output features (for scikit-learn compatibility)."""
        if self.selected_indices_ is None:
            raise ValueError("The MEDAFilter has not been fitted yet.")
            
        if input_features is None:
            # Generate generic names if none were provided
            return np.array([f"feature_{i}" for i in self.selected_indices_])
            
        # Filter the provided vocabulary using the selected indices
        return np.array([input_features[i] for i in self.selected_indices_])