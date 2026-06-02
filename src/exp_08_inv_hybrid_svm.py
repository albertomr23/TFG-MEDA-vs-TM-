# src/exp_09_inv_hybrid_latent.py

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

# Importing our custom TFG modules
from models.r_wrapper import RWrapper
from models.tm_wrapper import TMWrapper
from features.smart_booleanizer import SmartBooleanizer

import rpy2.robjects as robjects
robjects.r('options(warn=-1)')

warnings.filterwarnings('ignore')

class TMClauseExtractor(BaseEstimator, TransformerMixin):
    """
    The core of the Inverse Hybrid Architecture.
    Uses the Tsetlin Machine as a Non-Linear Epistatic Feature Extractor.
    Translates the continuous biomarker space into a discrete boolean clause space.
    """
    def __init__(self, number_of_clauses=100, T=15, s=3.9, n_bins=3):
        self.number_of_clauses = number_of_clauses
        self.T = T
        self.s = s
        self.n_bins = n_bins
        self.booleanizer = SmartBooleanizer(n_bins=self.n_bins)
        self.tm = TMWrapper(number_of_clauses=self.number_of_clauses, T=self.T, s=self.s, n_bins=self.n_bins)

    def fit(self, X, y):
        X_bool = self.booleanizer.fit_transform(X)
        self.tm.fit(X_bool, y)
        return self

    def transform(self, X):
        X_bool = self.booleanizer.transform(X)
        return self.tm.get_clause_activations(X_bool).astype(np.float64)


def run_experiment(X, y, dataset_type, results_dir):
    print("\n" + "="*80)
    print(" 🧠 EXP 09: INVERSE HYBRID EXPLORATION (Logic -> Geometry vs Latent) ")
    print("="*80)
    
    pipelines = {
        # 1. Pure Geometric Margin (Geometry)
        'Pure_SVM': Pipeline([
            ('scaler', StandardScaler()),
            ('svm', SVC(kernel='rbf', random_state=42))
        ]),
        
        # 2. Pure Propositional Logic (Logic)
        'Pure_TM': Pipeline([
            ('booleanizer', SmartBooleanizer(n_bins=3)),
            ('tm', TMWrapper(number_of_clauses=100, T=15, s=3.9, n_bins=3))
        ]),
      
        # 3. Inverse Hybridization (Logic -> Geometry)
        'Inverse_TM_SVM': Pipeline([
            ('tm_extractor', TMClauseExtractor(number_of_clauses=100, T=15, s=3.9, n_bins=3)),
            ('svm', SVC(kernel='rbf', random_state=42))
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
        'Inverse_TM_SVM': '#e74c3c',
        'Inverse_TM_sPLSDA': '#9b59b6',
        'Inverse_TM_vASCA': '#f39c12'
    }

    for name, pipeline in pipelines.items():
        print(f"\n>>> EVALUATING ARCHITECTURE: {name}")
        
        try:
            # error_score='raise' is avoided to prevent the whole script from crashing if R fails
            cv_results = cross_validate(pipeline, X, y, cv=cv, scoring=scoring, error_score=0.0)
            
            mcc_array = cv_results['test_MCC']
            raw_mcc_folds[name] = mcc_array
            
            results_db[name] = {
                'MCC': np.mean(mcc_array),
                'F1': np.mean(cv_results['test_F1-Score'])
            }
            print(f"    -> Mean MCC: {results_db[name]['MCC']:.3f} | Mean F1: {results_db[name]['F1']:.3f}")
        except Exception as e:
            print(f"    [!] FATAL ERROR during execution: R model likely collapsed due to zero-variance boolean matrix.")
            print(f"        Details: {e}")
            raw_mcc_folds[name] = [0, 0, 0, 0, 0]
            results_db[name] = {'MCC': 0.0, 'F1': 0.0}

    print("\n[FINISH] Generating Comprehensive Analytical Visualizations...")
    sns.set_theme(style="whitegrid")

    # ==========================================
    # CHART 1: GROUPED METRICS
    # ==========================================
    metrics_bar = ['MCC', 'F1-Score']
    x_bar = np.arange(len(metrics_bar))
    width = 0.15
    fig1, ax1 = plt.subplots(figsize=(12, 6))
    
    for i, (name, metrics) in enumerate(results_db.items()):
        scores = [metrics['MCC'], metrics['F1']]
        offset = (i - len(pipelines)/2 + 0.5) * width
        ax1.bar(x_bar + offset, scores, width, label=name.replace('_', ' '), color=colors_dict[name], edgecolor='black')
        
    ax1.set_title('Inverse Architecture Showdown: Geometry vs Latent Spaces', fontsize=15, fontweight='bold')
    ax1.set_xticks(x_bar)
    ax1.set_xticklabels(metrics_bar, fontweight='bold', fontsize=12)
    ax1.set_ylim([0, 1.1])
    ax1.legend(loc='upper right', bbox_to_anchor=(1.35, 1))
    fig1.savefig(os.path.join(results_dir, f"[{dataset_type}]_01_Latent_Metrics.png"), dpi=300, bbox_inches='tight')
    plt.close(fig1)

    # ==========================================
    # CHART 2: VIOLIN PLOT (STABILITY ANALYSIS)
    # ==========================================
    fig2, ax2 = plt.subplots(figsize=(12, 6))
    data_for_violin = [raw_mcc_folds[name] for name in pipelines.keys()]
    
    sns.violinplot(data=data_for_violin, palette=colors_dict.values(), ax=ax2, inner="quartile", alpha=0.7)
    sns.swarmplot(data=data_for_violin, color="black", alpha=0.6, ax=ax2, size=6)
    
    ax2.set_title('Distribution of Predictive Stability (The "Latent Collapse" Check)', fontsize=15, fontweight='bold')
    ax2.set_xticklabels([n.replace('_', '\n') for n in pipelines.keys()], fontweight='bold', fontsize=10)
    ax2.set_ylabel('Matthews Correlation Coefficient (MCC)', fontweight='bold')
    fig2.savefig(os.path.join(results_dir, f"[{dataset_type}]_02_Latent_Stability.png"), dpi=300, bbox_inches='tight')
    plt.close(fig2)

    # ==========================================
    # CHART 3: TOPOLOGICAL PROOF (PCA)
    # ==========================================
    print("  -> Generating Topological Proof (PCA)...")
    pca_raw = PCA(n_components=2, random_state=42)
    X_pca_raw = pca_raw.fit_transform(StandardScaler().fit_transform(X))
    
    extractor = TMClauseExtractor(number_of_clauses=100, T=15, s=3.9, n_bins=3)
    X_clauses = extractor.fit(X, y).transform(X)
    pca_clauses = PCA(n_components=2, random_state=42)
    X_pca_clauses = pca_clauses.fit_transform(X_clauses)

    fig3, axes = plt.subplots(1, 2, figsize=(14, 6))
    fig3.suptitle('Why SVM Succeeds: The Linear Separability of Logic', fontsize=16, fontweight='bold', y=1.05)
    
    scatter_colors = ['#3498db', '#e74c3c']
    labels = ['Healthy (0)', 'Infected (1)']
    
    # Subplot A
    ax1 = axes[0]
    for class_val in [0, 1]:
        mask = (y == class_val)
        ax1.scatter(X_pca_raw[mask, 0], X_pca_raw[mask, 1], c=scatter_colors[class_val], label=labels[class_val], alpha=0.7, edgecolors='k', s=60)
    ax1.set_title(f'PCA on Raw Biomarkers\n(Entangled Algebraic Space)', fontweight='bold')
    ax1.set_xlabel('Principal Component 1')
    ax1.set_ylabel('Principal Component 2')
    ax1.legend()
    
    # Subplot B
    ax2 = axes[1]
    for class_val in [0, 1]:
        mask = (y == class_val)
        ax2.scatter(X_pca_clauses[mask, 0], X_pca_clauses[mask, 1], c=scatter_colors[class_val], label=labels[class_val], alpha=0.7, edgecolors='k', s=60)
    ax2.set_title(f'PCA on TM Clause Embeddings\n(Linearly Separable Logical Space)', fontweight='bold')
    ax2.set_xlabel('Principal Component 1')
    ax2.legend()

    plt.tight_layout()
    fig3.savefig(os.path.join(results_dir, f"[{dataset_type}]_03_TopologicalProof.png"), dpi=300, bbox_inches='tight')
    plt.close(fig3)

    print(f"[OK] Alternative Inverse Hybrids successfully evaluated! Check the /results/inverse_hybrid/ folder.")

if __name__ == "__main__":
    try:
        X, y, feature_names, dataset_type, project_root = select_and_load_dataset()
        results_dir = os.path.join(project_root, "results", "inverse_hybrid")
        os.makedirs(results_dir, exist_ok=True)
        run_experiment(X, y, dataset_type, results_dir)
    except Exception as e:
        print(f"[!] Fatal Error: {e}")