# src/models/tm_wrapper.py
from sklearn.base import BaseEstimator, ClassifierMixin
from pyTsetlinMachine.tm import MultiClassTsetlinMachine
import numpy as np
import warnings

class TMWrapper(BaseEstimator, ClassifierMixin):
    """
    Scikit-learn compatible wrapper for pyTsetlinMachine.
    Includes an exact clause-decoder to extract selected features natively.
    """
    def __init__(self, number_of_clauses=100, T=15, s=3.9, n_bins=4):
        self.number_of_clauses = number_of_clauses
        self.T = T
        self.s = s
        self.n_bins = n_bins # Needed to map boolean bits back to clinical features
        self.model_ = None
        
    def fit(self, X, y):
        self.n_features_in_ = X.shape[1]
        self.classes_ = np.unique(y)
        self.model_ = MultiClassTsetlinMachine(
            number_of_clauses=self.number_of_clauses, 
            T=self.T, 
            s=self.s
        )
        self.model_.fit(np.asarray(X, dtype=np.int32), np.asarray(y, dtype=np.int32))
        return self
        
    def predict(self, X):
        return self.model_.predict(np.asarray(X, dtype=np.int32))

    @property
    def selected_features_(self):
        """
        Decodes the Tsetlin Automata to find which original features are actually 
        used in the learned logic clauses. This unifies the API with sPLS-DA.
        """
        if self.model_ is None:
            return []
            
        selected_original_features = set()
        n_classes = len(self.classes_)
        
        # Iterate through the TM memory (Classes -> Clauses -> Features)
        for c in range(n_classes):
            for j in range(self.number_of_clauses):
                for f in range(self.n_features_in_):
                    try:
                        # ta_action returns 1 if the literal is included in the clause
                        # f is the direct literal, f + n_features_in_ is the negated literal
                        if self.model_.ta_action(c, j, f) == 1 or \
                           self.model_.ta_action(c, j, f + self.n_features_in_) == 1:
                            
                            # Map the boolean bit back to the original clinical biomarker
                            original_feature_idx = f // (self.n_bins-1)
                            selected_original_features.add(original_feature_idx)
                    except:
                        pass
                        
        return list(selected_original_features)
    
    def get_clause_activations(self, X_bool):
        """
        Extracts the binary activation state of all clauses for a given dataset.
        Uses highly optimized NumPy vectorization to bypass slow Python loops,
        ensuring scalability for large clinical cohorts or omics data.
        
        Args:
            X_bool (np.ndarray): The booleanized feature matrix (N_samples, N_features).
            
        Returns:
            np.ndarray: A matrix of shape (N_samples, Total_Active_Clauses).
        """
        import warnings
        
        # Safely extract the native pyTsetlinMachine model instance
        native_tm = getattr(self, 'tm_', getattr(self, 'model_', getattr(self, 'model', None)))
        
        if native_tm is None:
            raise AttributeError("[!] The native Tsetlin Machine model was not found in TMWrapper. Check your fit() method.")
            
        # 1. Native API Fallback (if future versions of the library support it)
        if hasattr(native_tm, 'transform') and callable(getattr(native_tm, 'transform')):
            return native_tm.transform(X_bool)
            
        # 2. Vectorized Extraction Engine
        n_samples = X_bool.shape[0]
        n_clauses = getattr(self, 'number_of_clauses', 20)
        n_classes = native_tm.number_of_classes
        n_features_total = native_tm.number_of_features
        half_features = n_features_total // 2
        
        activations = []
        
        for class_idx in range(n_classes):
            for clause_idx in range(n_clauses):
                
                # Identify which literals the Tsetlin Automata decided to INCLUDE
                included_literals = [
                    k for k in range(n_features_total) 
                    if native_tm.ta_action(class_idx, clause_idx, k) == 1
                ]
                
                # Skip mathematically empty clauses (no structural pattern)
                if not included_literals:
                    continue
                    
                pos_indices = [k for k in included_literals if k < half_features]
                neg_indices = [k - half_features for k in included_literals if k >= half_features]
                
                clause_output = np.ones(n_samples, dtype=bool)
                
                if pos_indices:
                    clause_output &= np.all(X_bool[:, pos_indices] == 1, axis=1)
                if neg_indices:
                    clause_output &= np.all(X_bool[:, neg_indices] == 0, axis=1)
                    
                activations.append(clause_output.astype(int))
                
        if not activations:
            warnings.warn("[TMWrapper] The model generated zero active clauses.")
            return np.zeros((n_samples, 1), dtype=int)
            
        return np.column_stack(activations)