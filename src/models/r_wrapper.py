
import numpy as np
import warnings
import sys 
import os
from sklearn.base import BaseEstimator, ClassifierMixin
from sklearn.utils.validation import check_X_y, check_array, check_is_fitted

# rpy2 imports for R-Python bridge
import rpy2.robjects as robjects
from rpy2.robjects import FloatVector, numpy2ri
from rpy2.robjects.packages import importr
import os

class RWrapper(BaseEstimator, ClassifierMixin):
    """
    Adapter class to execute R-based models (like sPLS-DA or vASCA) 
    while exposing a standard scikit-learn API in Python.
    """

    def __init__(self, method='splsda', n_components=2, sparsity_penalty=0.5):
        """
        Initializes the R Wrapper.
        
        Args:
            method (str): 'splsda', 'vasca', 'asca', 'spca', or 'pca'.
            n_components (int): Number of latent variables to extract.
            sparsity_penalty (float): Proportion of features to KEEP per component (0.0 to 1.0).
        """
        
        valid_methods = ['splsda', 'vasca', 'asca', 'spca', 'pca']
        if method not in valid_methods:
            raise ValueError(f"Method must be one of {valid_methods}")
        
        self.method = method
        self.n_components = n_components
        self.sparsity_penalty = sparsity_penalty
        
        # Internal state variables
        self.classes_ = None
        self.selected_features_ = None
        self._r_model = None  
        self._r_mixomics = None
        self._r_failed = False

        # Activate automatic numpy to R matrix conversion
        numpy2ri.activate()
        self._load_r_environment()

    def _load_r_environment(self):
        """Loads specific R libraries needed for the chosen method."""
        try:
            self._r_base = importr('base')
            self._r_stats = importr('stats')
            
            # mixOmics covers sPLS-DA, PCA, and sPCA natively
            if self.method in ['splsda', 'spca', 'pca']:
                self._r_mixomics = importr('mixOmics')
            
            # ASCA and VASCA usually require MEDA Toolbox or custom Camacho scripts
            elif self.method in ['asca', 'vasca']:
                # 1. We define the path to the local r_scripts folder where Daniel's R scripts are stored
                base_dir = os.path.dirname(os.path.abspath(__file__))
                r_scripts_dir = os.path.join(base_dir, 'r_scripts')
                
                # 2. We source Daniel's R scripts into the R environment
                for file_name in os.listdir(r_scripts_dir):
                    if file_name.endswith('.R') or file_name.endswith('.r'):
                        script_path = os.path.join(r_scripts_dir, file_name)
                        robjects.r.source(script_path)
                        
                # We save the R functions into Python variables for later use
                self._r_parglm = robjects.r['parglmVS']
                self._r_vasca = robjects.r['vasca']
            
        except Exception as e:
            warnings.warn(f"Failed to load R environment for {self.method}. Error: {str(e)}")

    def fit(self, X, y, permutations=100):
        
        """
        Translates X and y to R, fits the chosen model, and retrieves the structural loadings.
        """
        X, y = check_X_y(X, y, multi_output=True)
        self.classes_ = np.unique(y)
        n_features = X.shape[1]

        # ---------------------------------------------------------
        # ALGORITHM 1: sPLS-DA
        # ---------------------------------------------------------
        if self.method == 'splsda':
            main_label = y[:, 0] if y.ndim > 1 else y
            y_r = robjects.FactorVector(robjects.IntVector(main_label.flatten()))
            keep_x_count = max(1, int(n_features * self.sparsity_penalty))
            keepX = robjects.IntVector([keep_x_count] * self.n_components)
            
            # 1. Fit the sPLS-DA model
            self._r_model = self._r_mixomics.splsda(X=X, Y=y_r, ncomp=self.n_components, keepX=keepX)
            
            # Store training latent scores for later use in transform
            try:
                self.train_variates_X_ = np.array(self._r_model.rx2('variates').rx2('X'))
            except Exception:
                self.train_variates_X_ = None
            
            # ================================================================
            # 2. INTERNAL Q-SCORE (Cross-Validated Predictive Variance)
            # ================================================================

            try:
                robjects.globalenv['r_model_python'] = self._r_model
                r_code_q2 = """
                # suppressMessages y suppressWarnings silencian a mixOmics
                suppressMessages(suppressWarnings({
                    perf_res <- perf(r_model_python, validation = 'Mfold', folds = 3, progressBar = FALSE)
                    error_rate <- min(perf_res$error.rate$BER[, 'max.dist'])
                }))
                1 - error_rate
                """
                self.q_score_ = float(np.array(robjects.r(r_code_q2))[0])
            except Exception:
                self.q_score_ = None # Si R falla, seguimos          
            # 3. Extract structurally relevant variables (Original logic)
            loadings_matrix = np.array(self._r_model.rx2('loadings').rx2('X'))
            active_features_mask = np.any(loadings_matrix != 0, axis=1)
            self.selected_features_ = np.where(active_features_mask)[0]
        # ---------------------------------------------------------
        # ALGORITHM 2: sPCA(Sparse PCA) 
        # ---------------------------------------------------------
        elif self.method == 'spca':
            keep_x_count = max(1, int(n_features * self.sparsity_penalty))
            keepX = robjects.IntVector([keep_x_count] * self.n_components)
            
            # sPCA is unsupervised, it doesn't take Y during fit
            self._r_model = self._r_mixomics.spca(X=X, ncomp=self.n_components, keepX=keepX)
            loadings_matrix = np.array(self._r_model.rx2('loadings').rx2('X'))
            active_features_mask = np.any(loadings_matrix != 0, axis=1)
            self.selected_features_ = np.where(active_features_mask)[0]

        # ---------------------------------------------------------
        # ALGORITHMS 3 & 4: ASCA & VASCA
        # ---------------------------------------------------------
        elif self.method in ['asca', 'vasca']:
            
            # 1. Ensure C-contiguous memory and float64 type for safety
            X_matrix = np.ascontiguousarray(X, dtype=np.float64)
            
            # 2. Reshape y to a 2D matrix if it is 1D (ASCA requires a design matrix)
            if y.ndim == 1:
                y_matrix = np.ascontiguousarray(y.reshape(-1, 1), dtype=np.float64)
            else:
                y_matrix = np.ascontiguousarray(y, dtype=np.float64)
            
            # 3. Fast Bridge: numpy2ri is active, so we pass Numpy arrays directly.
            # We use the dynamic 'permutations' parameter (defaults to 100).
            glm_output = self._r_parglm(X_matrix, y_matrix, model="full", permutations=permutations)
            parglmoVS = glm_output.rx2(2)
            
            # 4. Variable Selection and Component Analysis
            if self.method == 'asca':
                self._r_model = self._r_vasca(parglmoVS, siglev=1.0)
            else:
                # Top-K hard selection based on sparsity_penalty
                keep_count = max(1, int(n_features * self.sparsity_penalty))
                self._r_model = self._r_vasca(parglmoVS, siglev=-float(keep_count))
            
            # 5. Robust Feature Extraction
            try:
                robjects.globalenv['r_vasca_model'] = self._r_model
                r_code_extract = """
                if ("factors" %in% names(r_vasca_model) && length(r_vasca_model$factors) >= 1) {
                    factor_1 <- r_vasca_model$factors[[1]]
                    if ("ind" %in% names(factor_1)) {
                        as.integer(factor_1$ind)
                    } else {
                        integer(0)
                    }
                } else {
                    integer(0)
                }
                """
                r_indices = np.array(robjects.r(r_code_extract))
                
                # Convert from R's 1-based indexing to Python's 0-based indexing
                if r_indices.size > 0:
                    self.selected_features_ = r_indices.astype(int) - 1
                else:
                    self.selected_features_ = np.arange(n_features)
            except Exception as e:
                self._r_failed = True
                warnings.warn(f"[RWrapper] {self.method.upper()} crashed in R (Possible Singular Matrix): {e}. Fallback to full feature set.")
                self.selected_features_ = list(range(n_features))
                     
        # ---------------------------------------------------------
        # ALGORITHM 5: Standard PCA
        # ---------------------------------------------------------
        elif self.method == 'pca':
            self._r_model = self._r_mixomics.pca(X=X, ncomp=self.n_components)
            # Standard PCA doesn't do variable selection (all weights are non-zero)
            self.selected_features_ = np.arange(n_features)

        return self

    def predict(self, X):
        """
        Translates test data X to R, predicts classes using the fitted model.
        """
        check_is_fitted(self, ['_r_model', 'classes_'])
        X = check_array(X)
        r_predict = robjects.r['predict']

        if self.method == 'splsda':
            # 1. Pasamos temporalmente las variables al entorno global de R
            robjects.globalenv['X_test_python'] = X
            robjects.globalenv['r_model_python'] = self._r_model
            # Pasamos también el número de componentes para que R sepa qué columna cortar
            robjects.globalenv['n_comp_python'] = self.n_components 
            
            # 2. Ejecutamos el código nativo en R
            r_code = """
            # Convertimos la matriz de test y le ponemos los nombres de las columnas
            X_test_r <- as.matrix(X_test_python)
            colnames(X_test_r) <- colnames(r_model_python$X)
            
            # Hacemos la predicción
            pred_obj <- predict(r_model_python, newdata=X_test_r, dist="max.dist")
            
            # Cortamos la columna EXACTA dentro de R
            col_idx <- as.integer(n_comp_python)
            class_preds <- pred_obj$class$max.dist[, col_idx]
            
            # R devuelve un 'Factor', lo forzamos a ser números enteros (0 y 1)
            as.numeric(as.character(class_preds))
            """
            
            # 3. Traemos a Python un vector 1D puro (ya no hay matrices raras)
            final_predictions = np.array(robjects.r(r_code))
            
            return final_predictions.astype(int)
            
        elif self.method in ['spca', 'pca']:
            # PCA is for feature extraction (Pathway A), not direct classification.
            # Usually, you extract the scores and pass them to a classifier.
            raise ValueError(f"{self.method.upper()} is unsupervised and cannot directly predict classes. Use it as a transformer.")
            
        elif self.method in ['asca', 'vasca']:
            # Note: ASCA/VASCA are traditionally ANOVA-based variance decomposition tools,
            # not direct standalone classifiers. To predict a new patient's class, data is usually 
            # projected onto the components and classified via Mahalanobis distance or similar heuristics.
            
            # Example implementation (pending lab confirmation):
            # r_predict_function = robjects.r['predict_vasca_class']
            # pred_obj = r_predict_function(self._r_model, newdata=X)
            # return np.array(pred_obj).astype(int)
            
            raise NotImplementedError(
                f"Direct classification prediction for {self.method.upper()} requires a specific "
                "classification heuristic (e.g., distance to centroids in score space). "
                "Please replace this error with the specific R prediction function provided by your laboratory."
            )

    def transform(self, X):
        """
        I need this method so Scikit-Learn can use this class as a feature filter 
        in my hybrid pipeline, instead of just a final predictor.
        
        For dimensionality reduction methods (sPLS-DA, PCA), this returns the latent scores.
        For feature selection methods (vASCA, ASCA), this returns the selected features.
        """
        check_is_fitted(self)
        X_arr = check_array(X)
        
        if getattr(self, '_r_failed', False):
            warnings.warn("[RWrapper] Predicting with a crashed R model. Returning dummy predictions to avoid breaking CV fold.")
            return np.full(X_arr.shape[0], self.classes_[0])
        
        # For sPLS-DA, PCA, sPCA: Return latent scores (dimensionality reduction)
        if self.method == 'splsda':
            # Use R's predict function with the original features
            try:
                robjects.globalenv['r_model_transform'] = self._r_model
                robjects.globalenv['X_transform'] = X_arr
                
                # Use the loadings and means from the fitted model to project new data
                r_code = """
                # Project the new data using the model's loadings
                X_centered <- sweep(X_transform, 2, colMeans(r_model_transform$X))
                loadings_X <- r_model_transform$loadings$X
                # Compute scores by multiplying centered data with loadings
                scores <- X_centered %*% loadings_X
                as.matrix(scores)
                """
                latent_scores = np.array(robjects.r(r_code))
                # Ensure we get the right dimensions
                if latent_scores.ndim == 1:
                    latent_scores = latent_scores.reshape(-1, self.n_components)
                return latent_scores[:, :self.n_components]
            except Exception as e:
                warnings.warn(f"Failed to extract latent scores for sPLS-DA: {e}. Falling back to selected features.")
                if hasattr(self, 'selected_features_') and self.selected_features_ is not None and len(self.selected_features_) > 0:
                    return X_arr[:, self.selected_features_]
                else:
                    return X_arr
        
        # For PCA, sPCA: Use R's predict
        elif self.method in ['pca', 'spca']:
            try:
                robjects.globalenv['r_model_transform'] = self._r_model
                robjects.globalenv['X_transform'] = X_arr
                
                r_code = f"""
                scores <- predict(r_model_transform, newdata = X_transform)
                if (is.null(dim(scores))) {{
                    matrix(scores, nrow = nrow(X_transform), ncol = {self.n_components})
                }} else {{
                    scores[, 1:{self.n_components}]
                }}
                """
                latent_scores = np.array(robjects.r(r_code))
                return latent_scores
            except Exception as e:
                warnings.warn(f"Failed to extract latent scores for {self.method}: {e}. Falling back to selected features.")
                if hasattr(self, 'selected_features_') and self.selected_features_ is not None and len(self.selected_features_) > 0:
                    return X_arr[:, self.selected_features_]
                else:
                    return X_arr
        
        # For ASCA, vASCA: Return selected features
        elif self.method in ['asca', 'vasca']:
            if hasattr(self, 'selected_features_') and self.selected_features_ is not None and len(self.selected_features_) > 0:
                return X_arr[:, self.selected_features_]
            else:
                warnings.warn(f"Watch out: {self.method.upper()} didn't select specific features. Passing all of them.")
                return X_arr
        
        # Fallback
        else:
            if hasattr(self, 'selected_features_') and self.selected_features_ is not None and len(self.selected_features_) > 0:
                return X_arr[:, self.selected_features_]
            else:
                return X_arr        