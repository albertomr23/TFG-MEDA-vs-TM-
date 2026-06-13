"""
===============================================================================
EXPERIMENT 07: INVERSE HYBRID ARCHITECTURE (TM -> sPLSDA / vASCA)

Autor: Alberto Munuera Ramos
Date: June 2026
University: UGR

===============================================================================
"""

import os
import time
import numpy as np
import pandas as pd
import warnings
import matplotlib.pyplot as plt
import seaborn as sns

from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.svm import SVC
from sklearn.decomposition import PCA
from sklearn.model_selection import StratifiedKFold, cross_validate
from sklearn.metrics import make_scorer, matthews_corrcoef, f1_score
from sklearn.base import BaseEstimator, TransformerMixin
from utils.data_loader import select_and_load_dataset
from pipelines.meda_filter import MEDAFilter

# Importing our custom TFG modules
from models.r_wrapper import RWrapper
from models.tm_wrapper import TMWrapper
from features.smart_booleanizer import SmartBooleanizer

warnings.filterwarnings('ignore')

# --- CUSTOM TRANSFORMERS FOR THE INVERSE CASCADE ---


class TMClauseExtractor(BaseEstimator, TransformerMixin):
    """
    The core of the Inverse Hybrid Architecture.
    Acts as an upstream Non-Linear Epistatic Feature Extractor.
    Transforms raw continuous biomarkers into a sparse matrix of active boolean clauses.
    """
    def __init__(self, number_of_clauses=100, T=15, s=3.9, n_bins=3):
        self.number_of_clauses = number_of_clauses
        self.T = T
        self.s = s
        self.n_bins = n_bins
        # Internal TM components setup
        self.booleanizer = SmartBooleanizer(n_bins=self.n_bins)
        self.tm = TMWrapper(number_of_clauses=self.number_of_clauses, T=self.T, s=self.s, n_bins=self.n_bins)
    
    def fit(self, X, y):
        X_bool = self.booleanizer.fit_transform(X)
        self.tm.fit(X_bool, y)
        return self

    def transform(self, X):
        X_bool = self.booleanizer.transform(X)
        # Extract the logical state (activations) of the clauses for each patient
        # We cast to float64 so the downstream algebraic models (like SVM or sPLSDA) don't complain
        return self.tm.get_clause_activations(X_bool).astype(np.float64)



def run_experiment(X, y, dataset_type, results_dir):
    print("\n" + "="*70)
    print("  EXPERIMENT 07: LATENT COLLAPSE (Testing TM -> sPLSDA / vASCA) ")
    print("="*70)
    
    # These are the exact pipelines mentioned in the LaTeX report
    pipelines = {
        'Pure_SVM': Pipeline([
            ('scaler', StandardScaler()),
            ('svm', SVC(kernel='rbf', random_state=42))
        ]),
        
        'Pure_TM': Pipeline([
            ('booleanizer', SmartBooleanizer(n_bins=3)),
            ('tm', TMWrapper(number_of_clauses=100, T=15, s=3.9, n_bins=3))
        ]),
        
        'Inverse_TM_sPLSDA': Pipeline([
            ('tm_extractor', TMClauseExtractor(number_of_clauses=100, T=15, s=3.9, n_bins=3)),
            ('splsda', MEDAFilter(method='splsda', n_components=2, sparsity_penalty=0.3)),
            ('svm', SVC(kernel='linear', random_state=42)) 
        ]),

        'Inverse_TM_vASCA': Pipeline([
            ('tm_extractor', TMClauseExtractor(number_of_clauses=100, T=15, s=3.9, n_bins=3)),
            ('vasca', MEDAFilter(method='vasca', n_components=2, sparsity_penalty=0.3)),
            ('svm', SVC(kernel='linear', random_state=42)) 
        ])
    }
    
    scoring = {
        'MCC': make_scorer(matthews_corrcoef),
        'F1-Score': make_scorer(f1_score)
    }
    
    cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)
    results_db = {}
    raw_mcc_folds = {}
    
    colors_dict = {
        'Pure_SVM': '#34495e', 
        'Pure_TM': '#2ecc71', 
        'Inverse_TM_sPLSDA': '#9b59b6',
        'Inverse_TM_vASCA': '#e74c3c'
    }

    for name, pipeline in pipelines.items():
        print(f"\n>>> EVALUATING ARCHITECTURE: {name}")
        try:
            cv_results = cross_validate(pipeline, X, y, cv=cv, scoring=scoring)
            
            results_db[name] = {
                'MCC': np.mean(cv_results['test_MCC']),
                'F1': np.mean(cv_results['test_F1-Score'])
            }
            raw_mcc_folds[name] = cv_results['test_MCC']
            print(f"    -> Mean MCC: {results_db[name]['MCC']:.3f} | Mean F1: {results_db[name]['F1']:.3f}")
        except Exception as e:
            print(f"    [!] Fatal collapse during CV for {name}: {e}")
            results_db[name] = {'MCC': 0.0, 'F1': 0.0}
            raw_mcc_folds[name] = [0.0] * cv.n_splits

    print("\n[FINISH] Generating Architectural Visualizations...")
    sns.set_theme(style="whitegrid")

    # ==========================================
    # CHART 1: GROUPED METRICS BAR CHART
    # ==========================================
    metrics_bar = ['MCC', 'F1-Score']
    x_bar = np.arange(len(metrics_bar))
    width = 0.20
    fig1, ax1 = plt.subplots(figsize=(10, 6))
    
    for i, (name, metrics) in enumerate(results_db.items()):
        scores = [metrics['MCC'], metrics['F1']]
        offset = (i - len(pipelines)/2 + 0.5) * width
        ax1.bar(x_bar + offset, scores, width, label=name.replace('_', ' '), color=colors_dict[name], edgecolor='black')
        
    ax1.set_title('Inverse Architecture: The Latent Collapse', fontsize=15, fontweight='bold')
    ax1.set_xticks(x_bar)
    ax1.set_xticklabels(metrics_bar, fontweight='bold', fontsize=12)
    ax1.set_ylim([-0.3, 1.1]) # Extended downwards just in case high-dim fails
    ax1.legend(loc='upper right', bbox_to_anchor=(1.35, 1))
    fig1.savefig(os.path.join(results_dir, f"[{dataset_type}]_01_Latent_Metrics.png"), dpi=300, bbox_inches='tight')
    plt.close(fig1)

    # ==========================================
    # CHART 2: STABILITY VIOLIN PLOT 
    # ==========================================
    fig_viol, ax_viol = plt.subplots(figsize=(10, 6))
    data_for_violin = [raw_mcc_folds[name] for name in pipelines.keys()]
    
    sns.violinplot(data=data_for_violin, palette=list(colors_dict.values()), ax=ax_viol, inner="quartile", alpha=0.7)
    sns.swarmplot(data=data_for_violin, color="black", alpha=0.6, ax=ax_viol)
    
    ax_viol.set_xticklabels([n.replace('_', '\n') for n in pipelines.keys()], fontweight='bold')
    ax_viol.set_ylabel('MCC per Fold', fontweight='bold')
    ax_viol.set_title('Stability Distribution (Latent Space Collapse)', fontweight='bold', fontsize=14)
    fig_viol.savefig(os.path.join(results_dir, f"[{dataset_type}]_02_Latent_Stability.png"), dpi=300, bbox_inches='tight')
    plt.close(fig_viol)

    # ==========================================
    # CHART 3: THE MATHEMATICAL PROOF (PCA Projection)
    # ==========================================
    print("  -> Generating Topological Proof (PCA)...")
    
    # 1. Raw space PCA
    pca_raw = PCA(n_components=2, random_state=42)
    X_pca_raw = pca_raw.fit_transform(StandardScaler().fit_transform(X))
    
    # 2. Clause space PCA (Logical Islands)
    extractor = TMClauseExtractor(number_of_clauses=100, T=15, s=3.9, n_bins=3)
    X_clauses = extractor.fit(X, y).transform(X)
    pca_clauses = PCA(n_components=2, random_state=42)
    X_pca_clauses = pca_clauses.fit_transform(X_clauses)

    fig3, axes = plt.subplots(1, 2, figsize=(14, 6))
    fig3.suptitle('Topological Transformation: Continuous Geometry vs. Logical Islands', fontsize=16, fontweight='bold', y=1.05)
    
    scatter_colors = ['#3498db', '#e74c3c']
    labels = ['Healthy (0)', 'Infected (1)']
    
    # Subplot A: Raw Data
    axA = axes[0]
    for class_val in [0, 1]:
        mask = (y == class_val)
        axA.scatter(X_pca_raw[mask, 0], X_pca_raw[mask, 1], c=scatter_colors[class_val], label=labels[class_val], alpha=0.7, edgecolors='k', s=60)
    axA.set_title('PCA on Raw Biomarkers\n(Overlapping Algebraic Space)', fontweight='bold')
    axA.set_xlabel('Principal Component 1')
    axA.set_ylabel('Principal Component 2')
    axA.legend()

    # Subplot B: Clause Space (The "Islands")
    axB = axes[1]
    for class_val in [0, 1]:
        mask = (y == class_val)
        axB.scatter(X_pca_clauses[mask, 0], X_pca_clauses[mask, 1], c=scatter_colors[class_val], label=labels[class_val], alpha=0.7, edgecolors='k', s=60)
    axB.set_title('PCA on TM Clause Embeddings\n(Discrete Logical Islands)', fontweight='bold')
    axB.set_xlabel('Principal Component 1')
    axB.legend()

    plt.tight_layout()
    fig3.savefig(os.path.join(results_dir, f"[{dataset_type}]_03_TopologicalProof.png"), dpi=300, bbox_inches='tight')
    plt.close(fig3)

    print("[OK] Experiment completed successfully. All artifacts saved.")

if __name__ == "__main__":
    try:
        X, y, feature_names, dataset_type, project_root = select_and_load_dataset()
        results_dir = os.path.join(project_root, "results", "inverse_latent")
        os.makedirs(results_dir, exist_ok=True)
        run_experiment(X, y, dataset_type, results_dir)
    except Exception as e:
        print(f"[!] Fatal Error: {e}")