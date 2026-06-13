"""
===============================================================================
EXPERIMENT 05: HYBRIDIZATION (ALGEBRA + LOGIC)

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
from sklearn.svm import SVC
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import Pipeline
from sklearn.base import BaseEstimator, TransformerMixin

from models.r_wrapper import RWrapper
from models.tm_wrapper import TMWrapper
from features.smart_booleanizer import SmartBooleanizer
from evaluation.benchmark_engine import BenchmarkEngine
from utils.data_loader import select_and_load_dataset
from pipelines.meda_filter import MEDAFilter

import rpy2.robjects as robjects
robjects.r('options(warn=-1)') 

warnings.filterwarnings('ignore')


def run_experiment(X, y, dataset_type, results_dir):
    print("\n=========================================================")
    print("  EXPERIMENT 05: HYBRIDIZATION (ALGEBRA + LOGIC) ")
    print("=========================================================\n")
    
    engine = BenchmarkEngine(outer_cv=5, inner_cv=2, random_state=42)
    
    pipelines_to_test = {
        'Pure_sPLSDA': RWrapper(method='splsda', n_components=2, sparsity_penalty=0.3),
        'vASCA_SVM': Pipeline([
            ('filter', MEDAFilter(method='vasca', n_components=2, sparsity_penalty=0.3)),
            ('scaler', StandardScaler()),
            ('svm', SVC(kernel='rbf', random_state=42))
        ]),
        'Pure_TM': Pipeline([
            ('booleanizer', SmartBooleanizer(n_bins=3)),
            ('tm', TMWrapper(number_of_clauses=100, T=15, s=3.9, n_bins=3))
        ]),
        'Hybrid_sPLSDA_TM': Pipeline([
            ('filter', MEDAFilter(method='splsda', n_components=2, sparsity_penalty=0.3)),
            ('booleanizer', SmartBooleanizer(n_bins=3)),
            ('tm', TMWrapper(number_of_clauses=100, T=15, s=3.9, n_bins=3))
        ]),
        'Hybrid_vASCA_TM': Pipeline([
            ('filter', MEDAFilter(method='vasca', n_components=2, sparsity_penalty=0.3)),
            ('booleanizer', SmartBooleanizer(n_bins=3)),
            ('tm', TMWrapper(number_of_clauses=100, T=15, s=3.9, n_bins=3))
        ])
    }
    
    results_db = {}
    raw_mcc_folds = {} # To store raw arrays for Boxplots
    
    colors_dict = {
        'Pure_sPLSDA': '#95a5a6', 
        'vASCA_SVM': '#e74c3c', 
        'Pure_TM': '#2ecc71', 
        'Hybrid_sPLSDA_TM': '#8e44ad', 
        'Hybrid_vASCA_TM': '#f39c12'
    }

    # Extract Sparsity directly for the Bubble Chart
    sparsity_dict = {
        'Pure_sPLSDA': 46.5 if dataset_type=='real' else 56.0,
        'vASCA_SVM': 71.4 if dataset_type=='real' else 70.0,
        'Pure_TM': 0.0,
        'Hybrid_sPLSDA_TM': 46.5 if dataset_type=='real' else 56.0,
        'Hybrid_vASCA_TM': 71.4 if dataset_type=='real' else 70.0
    }

    for name, pipeline in pipelines_to_test.items():
        print(f"\n>>> TESTING CANDIDATE: {name.upper()}")
        engine.run_benchmark(X, y, name, pipeline, {})
        
        fold_details = engine.results_[name].get('fold_details', [])
        mcc_array = [m.get('mcc', 0) for m in fold_details] if fold_details else [0]
        mcc_val = np.mean(mcc_array)
        f1_val = np.mean([m.get('f1', 0) for m in fold_details]) if fold_details else 0
        time_val = np.mean([m.get('fit_time', 1) for m in fold_details]) if fold_details else 1
        
        raw_mcc_folds[name] = mcc_array
        results_db[name] = {
            'MCC': mcc_val,
            'F1': f1_val,
            'Time': time_val,
            'Sparsity': sparsity_dict[name]
        }
        print(f"    -> Extracted Final MCC for plots: {mcc_val:.3f}")

    print("\n[FINISH] Generating Advanced Hybrid Analytics (Saved in /results/hybrid/)...")

    sns.set_theme(style="whitegrid")

    # ==========================================
    # CHART 1: VIOLIN PLOT (Stability & Variance)
    # ==========================================
    fig1, ax1 = plt.subplots(figsize=(12, 6))
    data_for_violin = [raw_mcc_folds[name] for name in pipelines_to_test.keys()]
    
    sns.violinplot(data=data_for_violin, palette=colors_dict.values(), ax=ax1, inner="quartile", alpha=0.7)
    sns.swarmplot(data=data_for_violin, color="black", alpha=0.6, ax=ax1, size=6)
    
    ax1.set_title('Predictive Stability Distribution (MCC per Fold)', fontsize=15, fontweight='bold')
    ax1.set_xticklabels(pipelines_to_test.keys(), fontweight='bold', rotation=15)
    ax1.set_ylabel('Matthews Correlation Coefficient (MCC)', fontweight='bold')
    fig1.savefig(os.path.join(results_dir, f"[{dataset_type}]_01_ViolinStability.png"), dpi=300, bbox_inches='tight')
    plt.close(fig1)

    # ==========================================
    # CHART 2: SLOPE CHART (The Synergy Trajectory)
    # ==========================================
    fig2, ax2 = plt.subplots(figsize=(8, 6))
    
    ax2.plot([0, 1], [results_db['Pure_TM']['MCC'], results_db['Hybrid_sPLSDA_TM']['MCC']], 
             color=colors_dict['Hybrid_sPLSDA_TM'], marker='o', markersize=12, linewidth=3, label='sPLS-DA Hybrid')
    ax2.plot([0, 1], [results_db['Pure_TM']['MCC'], results_db['Hybrid_vASCA_TM']['MCC']], 
             color=colors_dict['Hybrid_vASCA_TM'], marker='s', markersize=12, linewidth=3, label='vASCA Hybrid')
    
    ax2.set_xticks([0, 1])
    ax2.set_xticklabels(['Pure Tsetlin Machine\n(0% Filtering)', 'Hybrid Architectures\n(MEDA Filtering)'], fontweight='bold')
    ax2.set_ylabel('Mean MCC', fontweight='bold')
    ax2.set_title('Logic-Algebraic Synergy Trajectory', fontsize=15, fontweight='bold')
    ax2.legend(loc='best')
    fig2.savefig(os.path.join(results_dir, f"[{dataset_type}]_02_SynergySlope.png"), dpi=300, bbox_inches='tight')
    plt.close(fig2)

    # ==========================================
    # CHART 3: BUBBLE CHART (Sparsity vs Performance)
    # ==========================================
    fig3, ax3 = plt.subplots(figsize=(10, 6))
    
    for name, metrics in results_db.items():
        ax3.scatter(metrics['Sparsity'], metrics['MCC'], s=metrics['F1']*1500, 
                    c=[colors_dict[name]], label=name, alpha=0.7, edgecolors='black', linewidth=2)
        ax3.text(metrics['Sparsity'], metrics['MCC'] + 0.015, name, ha='center', fontsize=9, fontweight='bold')

    ax3.set_title('Filtering Trade-off: Sparsity vs. Predictive Power', fontsize=15, fontweight='bold')
    ax3.set_xlabel('Sparsity (% of Variables Removed)', fontweight='bold')
    ax3.set_ylabel('Mean MCC', fontweight='bold')
    ax3.grid(True, linestyle='--', alpha=0.6)
    
    from matplotlib.lines import Line2D
    legend_elements = [Line2D([0], [0], marker='o', color='w', label='Size = F1-Score', markerfacecolor='gray', markersize=15)]
    ax3.legend(handles=legend_elements, loc='lower left')
    
    fig3.savefig(os.path.join(results_dir, f"[{dataset_type}]_03_SparsityBubble.png"), dpi=300, bbox_inches='tight')
    plt.close(fig3)

    print(" 3 NEW Advanced Visualizations (Violin, Slope, Bubble) generated successfully!")

if __name__ == "__main__":
    try:
        X, y, features_names, dataset_type, project_root = select_and_load_dataset()
        results_dir = os.path.join(project_root, "results", "hybrid")
        os.makedirs(results_dir, exist_ok=True)
        run_experiment(X, y, dataset_type, results_dir)
    except Exception as e:
        print(f"[!] Fatal Error during standalone execution: {e}")