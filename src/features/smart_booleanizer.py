import numpy as np
import pandas as pd
from sklearn.base import BaseEstimator, TransformerMixin
from sklearn.cluster import KMeans
from sklearn.preprocessing import KBinsDiscretizer
import warnings

class SmartBooleanizer(BaseEstimator, TransformerMixin):
    """
    Advanced Booleanizer to transform continuous biomarkers into binary features
    for TMs, supporting Thermometer Encoding and various 
    discretization strategies.
    """

    def __init__(self, strategy='quantile', n_bins=4, encoding='thermometer', random_state=42):
        """
        Initializes the SmartBooleanizer.
        
        Args:
            strategy (str): Discretization method ('quantiles', 'equal_width', 'kmeans').
            n_bins (int): Number of bins/intervals to create.
            encoding (str): Encoding type ('thermometer', 'one_hot').
            random_state (int): Seed for reproducible K-Means clustering.
        """
        self.strategy = strategy
        self.n_bins = n_bins
        self.encoding = encoding
        self.random_state = random_state
        # Dictionary to store the fitted thresholds/centroids for each continuous feature
        self.fitted_thresholds_ = {}
        # Stores the total number of bits generated per feature for the TM
        self.feature_names_in_ = None

    def fit(self, X, y=None):
        """
        Learns the discretization thresholds from the training data X.
        
        Args:
            X (pd.DataFrame or np.ndarray): The continuous training data.
            y (ignored): Required for compatibility with sklearn pipelines.
            
        Returns:
            self: The fitted estimator.
        """
        # 1. Validate input and store feature names
        
        if isinstance(X,pd.DataFrame):
            self.feature_names_in_ = X.columns.tolist()
            X_array = X.values
        else:
            self.feature_names_in_ = [f"Feature_{i}" for i in range(X.shape[1])]
            X_array = np.asarray(X)
        
        n_features = X_array.shape[1]
        
        # 2. Calculate and store thresholds for each continous feature
        for col_idx in range(n_features):
            feature_data = X_array[:,col_idx]
            feature_name = self.feature_names_in_[col_idx]
            
            #Extract internal thresholds based on the mathematical strategy
            thresholds = self._calculate_thresholds(feature_data)
            self.fitted_thresholds_[feature_name] = thresholds
        return self

    def transform(self, X):
        """
        Applies the learned thresholds to discretize X.
        (Note: The boolean expansion will be orchestrated here in Block 3).
        
        Args:
            X (pd.DataFrame or np.ndarray): The continuous test/train data.
            
        Returns:
            np.ndarray: Matrix of discrete bin indices.
        """
        # 1. Validation: Ensure the model has been fitted
        if self.feature_names_in_ is None:
            raise ValueError("The SmartBooleanizer instance is not fitted yet. Call 'fit' with appropriate data before using this estimator.")
        
        if isinstance(X,pd.DataFrame):
            X_array = X.values
        else:
            X_array = np.asarray(X)
        
        n_samples, n_features = X_array.shape
        
        if n_features != len(self.feature_names_in_):
            raise ValueError(f"Input data has {n_features} features, but the model was fitted with {len(self.feature_names_in_)} features.")
        
        #Matrix to hold the discretized bin indices for each feature
        X_discrete = np.zeros((n_samples, n_features), dtype=int)
        # 2. Discretize each feature using the thresholds learned during 'fit'
        
        for col_idx in range(n_features):
            feature_data = X_array[:,col_idx]
            feature_name = self.feature_names_in_[col_idx]
            thresholds = self.fitted_thresholds_[feature_name]
            
            #Assign discrete bin indices based on the thresholds
            X_discrete[:,col_idx] = self._discretize_feature(feature_data, thresholds)
        
        # 3. Apply Therm Encoding to X_discrete
        if self.encoding == 'thermometer':
            return self._apply_thermometer_encoding(X_discrete)
        elif self.encoding == 'one_hot':
            # Placeholder for future one-hot encoding implementation
            pass
        else:
            return X_discrete

    def _calculate_thresholds(self, feature_data, feature_name):
        """
        Internal mathematical method to compute bin edges based on the chosen strategy.
        Args:
            feature_data (np.ndarray): 1D array of a single continuous feature.
            
        Returns:
            np.ndarray: Array of boundary thresholds.
        """
        #Remove NaNs if any exist in the data beafore calculating
        clean_data = feature_data[~np.isnan(feature_data)]
        
        if self.strategy == 'quantile':
            # Use percentiles to determine bin edges
            percentiles = np.linspace(0, 100, self.n_bins + 1)
            thresholds = np.percentile(clean_data, percentiles)
        elif self.strategy == 'equal_width':
            # Use equal width intervals to determine bin edges
            min_val = np.min(clean_data)
            max_val = np.max(clean_data)
            thresholds = np.linspace(min_val, max_val, self.n_bins + 1)
        elif self.strategy == 'kmeans':
            # Uses 1D clustering to find centers of mass in the data distribution
            # Suppress sklearn memory leak warning on Windows for small datasets
            with warnings.catch_warnings():
                warnings.simplefilter("ignore")
                kmeans = KMeans(n_clusters=self.n_bins, random_state=self.random_state, n_init=10)
                kmeans.fit(clean_data.reshape(-1, 1))
            
            # Sort the 1D centroids to preserve biological ordinality
            centers = np.sort(kmeans.cluster_centers_.flatten())
            
            # Calculate the midpoints between consecutive centroids to act as bin edges
            midpoints = (centers[:-1] + centers[1:]) / 2.0
            
            # Add absolute min and max to complete the boundary array
            thresholds = np.concatenate(([np.min(clean_data)], midpoints, [np.max(clean_data)]))
        else:
            raise ValueError("Invalid strategy. Choose from 'quantile', 'equal_width', or 'kmeans'.")

        return np.unique(thresholds)

    def _discretize_feature(self, feature_data, thresholds):
        """
        Internal method to assign continuous values to their corresponding bin index.
        Safely handles out-of-bounds biological values from test sets.
        
        Args:
            feature_data (np.ndarray): 1D array of a single continuous feature.
            thresholds (np.ndarray): Array of threshold values for discretization.
            
        Returns:
            np.ndarray: 1D array of integer bin indices.
        """
        
        #Step A: Outlier Protection(Clipping)
        # If a Test patient has a value lower than the Train minimum, bump it to the minimum.
        # If they have a value higher than the Train maximum, cap it at the maximum.
        min_train_val = thresholds[0]
        max_train_val = thresholds[-1]
        clipped_data = np.clip(feature_data, min_train_val, max_train_val)
        # Step B: Spatial Assignment
        # np.digitize maps values to bins. right=False means intervals are [a, b)
        # We subtract 1 to ensure our bins are 0-indexed (e.g., 0, 1, 2)
        bin_indices = np.digitize(clipped_data, bins=thresholds, right=False) - 1
        
        # Step C: Edge Case Correction
        # np.digitize places values exactly equal to the absolute maximum in an out-of-bounds bin.
        # We clamp it back to ensure it falls into the highest valid bin index.
        max_valid_bin_index = len(thresholds) - 2 
        bin_indices = np.clip(bin_indices, 0, max_valid_bin_index)
        
        return bin_indices

    def _apply_thermometer_encoding(self, X_discrete):
        """
        Internal method to expand discrete indices into cumulative boolean arrays.
        Uses pure mathematical broadcasting for maximum efficiency.
        
        Args:
            X_discrete (np.ndarray): Matrix of integer bin indices (shape: n_samples, n_features)
            
        Returns:
            np.ndarray: Binary matrix ready for the Tsetlin Machine.
        """
        n_samples, n_features = X_discrete.shape
        
        # MATHEMATICAL OPTIMIZATION:
        # If we have 4 bins (Q1, Q2, Q3, Q4), we only need 3 thresholds to separate them.
        # Generating 4 bits where the first bit is always '1' creates a Zero-Variance feature,
        # which wastes Tsetlin Machine memory. We strictly use (n_bins - 1) bits.
        n_bits_per_feature = self.n_bins - 1
        total_bits = n_features * n_bits_per_feature
        
        X_thermo = np.zeros((n_samples, total_bits), dtype=int)
        
        #Bit reference matrix to determine which bits correspond to which features and thresholds
        bit_reference = np.arange(n_bits_per_feature)
        
        for col_idx in range(n_features):
            bin_indices = X_discrete[:, col_idx]
            
            # THE BROADCASTING :
            # If a patient is in Bin 2: (2 > [0, 1, 2]) -> [True, True, False] -> [1, 1, 0]
            # If a patient is in Bin 3: (3 > [0, 1, 2]) -> [True, True, True] -> [1, 1, 1]
            thermo_bits = (bin_indices[:, None] > bit_reference).astype(int)
            
            # Map the bits to the final wide matrix
            start_idx = col_idx * n_bits_per_feature
            end_idx = start_idx + n_bits_per_feature
            X_thermo[:, start_idx:end_idx] = thermo_bits
            
        return X_thermo