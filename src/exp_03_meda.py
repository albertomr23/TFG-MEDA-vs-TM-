"""
===============================================================================
EXPERIMENT 03: PURE MEDA EVALUATION (LR vs SVM)

Autor: Alberto Munuera Ramos
Date: June 2026
University: UGR

===============================================================================
"""

import numpy as np
import pandas as pd
import os
import warnings
import matplotlib.pyplot as plt
import seaborn as sns

from sklearn.datasets import make_classification
from sklearn.pipeline import Pipeline
from sklearn.base import BaseEstimator, TransformerMixin
from sklearn.linear_model import LogisticRegression
from sklearn.svm import SVC
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import StratifiedKFold, cross_validate, cross_val_predict
from sklearn.metrics import make_scorer, matthews_corrcoef, f1_score, accuracy_score, precision_score, recall_score
from sklearn.metrics import roc_curve, auc, precision_recall_curve, average_precision_score
from utils.data_loader import select_and_load_dataset
from pipelines.meda_filter import MEDAFilter


import rpy2.robjects as robjects
robjects.r('options(warn=-1)') # Mute R warnings

# Importing my own modules
from models.r_wrapper import RWrapper

warnings.filterwarnings('ignore')



def run_experiment(X, y, feature_names, dataset_type, results_dir):
    print("\n=========================================================")
    print("  EXPERIMENT 03: PURE MEDA EVALUATION (LR vs SVM) ")
    print("=========================================================\n")
    
    meda_methods = ['pca', 'spca', 'splsda', 'asca', 'vasca'] 
    
    classifiers = {
        'Logistic_Regression': LogisticRegression(random_state=42, max_iter=500),
        'SVM': SVC(kernel='rbf', random_state=42, probability=True,max_iter=1500, cache_size=500) # Probability required for ROC/PR
    }
    
    scoring = {
        'Accuracy': make_scorer(accuracy_score),
        'Sensitivity': make_scorer(recall_score),
        'Precision': make_scorer(precision_score),
        'F1-Score': make_scorer(f1_score),
        'MCC': make_scorer(matthews_corrcoef)
    }
    
    cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)
    colors = sns.color_palette("husl", len(meda_methods))
    
    # --- GLOBAL FEATURE EXTRACTION (HEATMAP) ---
    print("\n[INFO] Generating Universal Feature Intersection Matrix...")
    selection_matrix = np.zeros((len(feature_names), len(meda_methods)))
    
    for col_idx, method in enumerate(meda_methods):
        filter_model = MEDAFilter(method=method, n_components=2, sparsity_penalty=0.3)
        filter_model.fit(X, y)
        for idx in filter_model.selected_indices_:
            selection_matrix[idx, col_idx] = 1

    fig_heat, ax_heat = plt.subplots(figsize=(10, 8))
    active_mask = np.sum(selection_matrix, axis=1) > 0
    filtered_matrix = selection_matrix[active_mask]
    filtered_names = np.array(feature_names)[active_mask]
    
    if len(filtered_names) > 25:
        top_indices = np.argsort(np.sum(filtered_matrix, axis=1))[::-1][:25]
        filtered_matrix = filtered_matrix[top_indices]
        filtered_names = filtered_names[top_indices]

    sns.heatmap(filtered_matrix, cmap="Blues", cbar=False, ax=ax_heat, linewidths=.5, linecolor='gray',
                xticklabels=[m.upper() for m in meda_methods], yticklabels=filtered_names)
    ax_heat.set_title('Biomarker Intersection Agreement (Top 25)', fontsize=14, fontweight='bold')
    plt.tight_layout()
    heat_file = os.path.join(results_dir, f"[{dataset_type}]_Heatmap_Biomarkers.png")
    fig_heat.savefig(heat_file, dpi=300)
    plt.close(fig_heat)
    print(f"[OK] Global Heatmap saved: {heat_file}")

    # --- CLASSIFIER TOURNAMENT ---
    for clf_name, clf in classifiers.items():
        print(f"\n{'='*50}")
        print(f" EVALUATING WITH: {clf_name.upper()} ")
        print(f"{'='*50}")
        
        # Trackers
        metrics_by_method = {m.upper(): [] for m in meda_methods}
        roc_data = {}
        pr_data = {}
        
        # Prepare individual plots
        fig_roc, ax_roc = plt.subplots(figsize=(8, 6))
        fig_pr, ax_pr = plt.subplots(figsize=(8, 6))
        
        for idx, method in enumerate(meda_methods):
            print(f"\n>>> Running {method.upper()} ...")
            
            pipeline = Pipeline([
                ('filter', MEDAFilter(method=method, n_components=2, sparsity_penalty=0.3)),
                ('scaler', StandardScaler()),
                ('classifier', clf)
            ])
            
            # 1. Metrics Calculation
            cv_results = cross_validate(pipeline, X, y, cv=cv, scoring=scoring)
            method_scores = [np.mean(cv_results[f'test_{metric}']) for metric in scoring.keys()]
            metrics_by_method[method.upper()] = method_scores
            
            print(f"    MCC: {method_scores[-1]:.3f} | F1: {method_scores[-2]:.3f}")
            
            # 2. Probability Prediction for ROC and PR
            y_pred_proba = cross_val_predict(pipeline, X, y, cv=cv, method='predict_proba')[:, 1]
            
            # ROC
            fpr, tpr, _ = roc_curve(y, y_pred_proba)
            roc_auc = auc(fpr, tpr)
            ax_roc.plot(fpr, tpr, color=colors[idx], lw=2, label=f'{method.upper()} (AUC = {roc_auc:.3f})')
            
            # Precision-Recall
            precision, recall, _ = precision_recall_curve(y, y_pred_proba)
            pr_auc = average_precision_score(y, y_pred_proba)
            ax_pr.plot(recall, precision, color=colors[idx], lw=2, label=f'{method.upper()} (AP = {pr_auc:.3f})')
            
            # 3. Decision Boundary Plot (Trained strictly on 2D space for visualization)
            print(f"    Plotting Topological Boundary for {method.upper()}...")
            meda_filter = MEDAFilter(method=method, n_components=2, sparsity_penalty=0.3)
            X_filtered = meda_filter.fit_transform(X, y)
            
            if X_filtered.shape[1] >= 2:
                X_2d = StandardScaler().fit_transform(X_filtered[:, :2])
                clf_2d = type(clf)(**clf.get_params())
                clf_2d.fit(X_2d, y)
                
                fig_bound, ax_bound = plt.subplots(figsize=(7, 6))
                
                # Meshgrid creation
                x_min, x_max = X_2d[:, 0].min() - 1, X_2d[:, 0].max() + 1
                y_min, y_max = X_2d[:, 1].min() - 1, X_2d[:, 1].max() + 1
                xx, yy = np.meshgrid(np.arange(x_min, x_max, 0.05), np.arange(y_min, y_max, 0.05))
                
                Z = clf_2d.predict_proba(np.c_[xx.ravel(), yy.ravel()])[:, 1]
                Z = Z.reshape(xx.shape)
                
                contour = ax_bound.contourf(xx, yy, Z, alpha=0.6, cmap='RdBu_r')
                plt.colorbar(contour, ax=ax_bound, label='Probability of Infection')
                
                # Scatter points
                scatter_colors = ['#3498db' if label == 0 else '#e74c3c' for label in y]
                ax_bound.scatter(X_2d[:, 0], X_2d[:, 1], c=scatter_colors, edgecolors='k', alpha=0.8)
                ax_bound.set_title(f'Decision Boundary: {method.upper()} + {clf_name}', fontweight='bold')
                
                bound_file = os.path.join(results_dir, f"[{dataset_type}]_Boundary_{clf_name}_{method.upper()}.png")
                fig_bound.savefig(bound_file, dpi=300, bbox_inches='tight')
                plt.close(fig_bound)

        # --- ROC PLOT SAVING ---
        ax_roc.plot([0, 1], [0, 1], color='navy', lw=2, linestyle='--')
        ax_roc.set_xlim([0.0, 1.0])
        ax_roc.set_ylim([0.0, 1.05])
        ax_roc.set_xlabel('False Positive Rate', fontweight='bold')
        ax_roc.set_ylabel('True Positive Rate', fontweight='bold')
        ax_roc.set_title(f'ROC Curve Comparison - {clf_name}', fontweight='bold')
        ax_roc.legend(loc="lower right")
        roc_file = os.path.join(results_dir, f"[{dataset_type}]_ROC_{clf_name}.png")
        fig_roc.savefig(roc_file, dpi=300, bbox_inches='tight')
        plt.close(fig_roc)
        print(f"[OK] ROC Curve saved: {roc_file}")

        # --- PR PLOT SAVING ---
        ax_pr.set_xlim([0.0, 1.0])
        ax_pr.set_ylim([0.0, 1.05])
        ax_pr.set_xlabel('Recall (Sensitivity)', fontweight='bold')
        ax_pr.set_ylabel('Precision', fontweight='bold')
        ax_pr.set_title(f'Precision-Recall Curve - {clf_name}', fontweight='bold')
        ax_pr.legend(loc="lower left")
        pr_file = os.path.join(results_dir, f"[{dataset_type}]_PR_Curve_{clf_name}.png")
        fig_pr.savefig(pr_file, dpi=300, bbox_inches='tight')
        plt.close(fig_pr)
        print(f"[OK] Precision-Recall Curve saved: {pr_file}")

        # --- GROUPED METRICS BAR CHART ---
        fig_metrics, ax_metrics = plt.subplots(figsize=(12, 6))
        x = np.arange(len(scoring.keys()))  # Group by Metrics
        width = 0.15 
        
        for i, (method_name, scores) in enumerate(metrics_by_method.items()):
            offset = (i - len(meda_methods)/2 + 0.5) * width 
            ax_metrics.bar(x + offset, scores, width, label=method_name, color=colors[i], edgecolor='black', alpha=0.85)
            
        ax_metrics.set_title(f'Comparative Metrics Array by Category ({clf_name})', fontsize=14, fontweight='bold')
        ax_metrics.set_xticks(x)
        ax_metrics.set_xticklabels(list(scoring.keys()), fontweight='bold', fontsize=11)
        ax_metrics.set_ylabel('Score (0 to 1)', fontsize=12)
        ax_metrics.set_ylim(0, 1.25)
        ax_metrics.legend(loc='upper right', ncol=len(meda_methods))
        ax_metrics.grid(True, axis='y', linestyle=':', alpha=0.7)
        
        metrics_file = os.path.join(results_dir, f"[{dataset_type}]_Metrics_Grouped_{clf_name}.png")
        fig_metrics.savefig(metrics_file, dpi=300, bbox_inches='tight')
        plt.close(fig_metrics)
        print(f"[OK] Grouped Metrics Chart saved: {metrics_file}")

if __name__ == "__main__":
    try:
        #Use our centralized loader that also returns project_root for consistent results saving
        X, y, feature_names, dataset_type, project_root = select_and_load_dataset()
        
        # Create the specific results folder for this experiment
        results_dir = os.path.join(project_root, "results", "meda_puro")
        os.makedirs(results_dir, exist_ok=True)
        
        run_experiment(X, y, feature_names, dataset_type, results_dir)
    except Exception as e:
        print(f"[!] Fatal Error during standalone execution: {e}")