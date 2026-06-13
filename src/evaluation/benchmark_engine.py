"""
===============================================================================
BENCHMARK ENGINE

Autor: Alberto Munuera Ramos
Date: June 2026
University: UGR

===============================================================================
"""

import numpy as np
import time
import warnings
from sklearn.model_selection import StratifiedKFold, GridSearchCV
from sklearn.metrics import matthews_corrcoef, f1_score, accuracy_score
from pyTsetlinMachine.tm import MultiClassTsetlinMachine

class BenchmarkEngine:
    """
    Rigorous evaluation engine to compare models (TM vs sPLS-DA ).
    Implements Nested Cross-Validation (NCV) to prevent data leakage during 
    hyperparameter fine-tuning, as proposed in the TFG methodology.
    """
    
    def __init__(self, outer_cv=5, inner_cv=3, random_state=42):
        self.outer_splits = outer_cv
        self.inner_splits = inner_cv
        self.random_state = random_state
        self.results_ = {}
        
        # StratifiedKFold ensures the same proportion of Healthy/Sick patients in every split
        self.outer_cv = StratifiedKFold(n_splits=outer_cv, shuffle=True, random_state=random_state)
        self.inner_cv = StratifiedKFold(n_splits=inner_cv, shuffle=True, random_state=random_state)

    def run_benchmark(self, X, y, model_name, pipeline, param_grid):
        """
        Executes the Nested CV loop for a specific model.
        """
        print(f"\n[{time.strftime('%H:%M:%S')}] Starting Nested CV for: {model_name}")
        
        X_arr = np.asarray(X)
        y_arr = np.asarray(y)
        total_features = X_arr.shape[1]
        
        fold_metrics = []
        selected_features_per_fold = []
        
        # ==========================================
        # OUTER LOOP (Final Model Evaluation)
        # ==========================================
        for fold_idx, (train_idx, test_idx) in enumerate(self.outer_cv.split(X_arr, y_arr)):
            print(f"  -> Processing Outer Fold {fold_idx + 1}/{self.outer_splits}...")
            
            # Strict isolation of the Test patients (Unseen data)
            X_train, X_test = X_arr[train_idx], X_arr[test_idx]
            y_train, y_test = y_arr[train_idx], y_arr[test_idx]
            
            # ==========================================
            # INNER LOOP (Hyperparameter Tuning)
            # ==========================================
            # GridSearchCV searches for the best configuration using ONLY X_train
            grid_search = GridSearchCV(
                estimator=pipeline,
                param_grid=param_grid,
                cv=self.inner_cv,
                scoring='matthews_corrcoef', # Optimizing for MCC 
                n_jobs=None
            )
            
            # Fit the grid search (ignoring library warnings)
            with warnings.catch_warnings():
                warnings.simplefilter("ignore")
                grid_search.fit(X_train, y_train)
                
            best_model = grid_search.best_estimator_
            
            # Extract selected biomarkers to calculate Sparsity and Kuncheva later
            extracted_features = self._extract_selected_features(best_model)
            selected_features_per_fold.append(extracted_features)
            
            # ==========================================
            # FINAL EVALUATION (On the isolated Test patients)
            # ==========================================
            y_pred = best_model.predict(X_test)
            
            # Calculate metrics promised in the presentation
            n_selected = len(extracted_features)
            sparsity = 1.0 - (n_selected / total_features) if total_features > 0 else 0
            
            metrics = {
                'fold': fold_idx + 1,
                'best_params': grid_search.best_params_,
                'mcc': matthews_corrcoef(y_test, y_pred),
                'f1_score': f1_score(y_test, y_pred, average='weighted'),
                'accuracy': accuracy_score(y_test, y_pred),
                'n_features_selected': n_selected,
                'sparsity': sparsity
            }
            fold_metrics.append(metrics)
            
        # Store the historical results for this model
        self.results_[model_name] = {
            'fold_details': fold_metrics,
            'features_selected_per_fold': selected_features_per_fold
        }
        
        self._print_summary(model_name, fold_metrics)
        return self.results_[model_name]

    def _extract_selected_features(self, best_model):
        """
        Extracts the indices of the selected features from the fitted model.
        Intelligently searches through pipeline steps to find the exact MEDA filter,
        preventing metric distortion from downstream classifiers or booleanizers.
        """
        # 1. Inspect Pipeline steps for a designated feature selector
        if hasattr(best_model, 'steps'):
            for name, step in best_model.steps:
                # Match our custom MEDAFilter
                if hasattr(step, 'selected_indices_'):
                    return set(step.selected_indices_)
                # Match direct RWrapper usage
                elif hasattr(step, 'selected_features_'):
                    return set(step.selected_features_)
                    
        # 2. If not a pipeline, check the model directly
        else:
            if hasattr(best_model, 'selected_features_'):
                return set(best_model.selected_features_)
                
        # 3. Fallback: Pure Logic Models (like Pure_TM or normal SVM)
        # If no explicit feature selection filter is found, the model relies on the 
        # full input topological space.
        if hasattr(best_model, 'n_features_in_'):
            return set(range(best_model.n_features_in_))
            
        return set()
    
    def calculate_stability_index(self, model_name, total_features):
        """
        Calculates the Feature Selection Stability across all CV folds.
        Uses the Pairwise Jaccard Index to elegantly handle subsets of varying sizes,
        acting as a robust alternative to the classic Kuncheva Index.
        
        Args:
            model_name (str): Identifier of the evaluated model.
            total_features (int): Total 'n' variables in the original dataset.
            
        Returns:
            float: Stability score [0.0 (random) to 1.0 (perfectly stable)].
        """
        if model_name not in self.results_:
            raise ValueError(f"No results found for '{model_name}'. Run benchmark first.")
            
        features_per_fold = self.results_[model_name]['features_selected_per_fold']
        num_folds = len(features_per_fold)
        
        # If we didn't do CV (only 1 fold), stability -> 1.0
        if num_folds < 2:
            return 1.0 
            
        pairwise_similarities = []
        
        # Compare every fold's subset against every other fold's subset 
        for i in range(num_folds):
            for j in range(i + 1, num_folds):
                set_a = features_per_fold[i]
                set_b = features_per_fold[j]
                
                # Edge Case: The algorithm aggressively dropped ALL features in both folds
                if len(set_a) == 0 and len(set_b) == 0:
                    pairwise_similarities.append(1.0)
                    continue
                # Edge Case: Dropped everything in only one fold
                elif len(set_a) == 0 or len(set_b) == 0:
                    pairwise_similarities.append(0.0)
                    continue
                    
                # Intersection over Union (Jaccard)
                intersection = len(set_a.intersection(set_b))
                union = len(set_a.union(set_b))
                
                similarity = intersection / union
                pairwise_similarities.append(similarity)
                
        mean_stability = np.mean(pairwise_similarities)
        
        print(f"  -> Biomarker Stability Index (Jaccard): {mean_stability:.4f} (1.0 is perfectly stable)")
        self.results_[model_name]['stability_index'] = mean_stability
        
        return mean_stability

    def _print_summary(self, model_name, fold_metrics):
        """Prints a clean summary of the metrics."""
        mcc_scores = [m['mcc'] for m in fold_metrics]
        f1_scores = [m['f1_score'] for m in fold_metrics]
        sparsities = [m['sparsity'] for m in fold_metrics]
        
        print(f"\n[RESULTS] {model_name} Completed.")
        print(f"  -> Mean MCC:      {np.mean(mcc_scores):.4f} (+/- {np.std(mcc_scores):.4f})")
        print(f"  -> Mean F1-Score: {np.mean(f1_scores):.4f} (+/- {np.std(f1_scores):.4f})")
        print(f"  -> Mean Sparsity: {np.mean(sparsities)*100:.2f}% feature reduction.")