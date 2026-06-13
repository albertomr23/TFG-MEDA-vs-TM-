"""
===============================================================================
EXPERIMENT 01: NOISE STRESS TEST (ADVANCED METRICS)

Autor: Alberto Munuera Ramos
Date: June 2026
University: UGR

===============================================================================
"""

import numpy as np
import os
import warnings
import matplotlib.pyplot as plt
from sklearn.datasets import make_classification
from sklearn.pipeline import Pipeline

# Import custom modules
from models.r_wrapper import RWrapper
from models.tm_wrapper import TMWrapper
from features.smart_booleanizer import SmartBooleanizer
from evaluation.benchmark_engine import BenchmarkEngine


warnings.filterwarnings('ignore')

def main():
    print("=========================================================")
    print("  EXPERIMENT 01: NOISE STRESS TEST (ADVANCED METRICS) ")
    print("=========================================================\n")
    
    total_features_list = [20, 40, 80]
    
    # Trackers for MCC
    mcc_plsda_history = [] #UPDATE
    mcc_splsda_history = []
    mcc_tm_history = []
    
    # Trackers for Algorithmic Stability (Jaccard)
    stab_plsda_history = []
    stab_splsda_history = []
    stab_tm_history = []
    
    # Fast Engine for graphing (Outer 3, Inner 2)
    engine = BenchmarkEngine(outer_cv=3, inner_cv=2, random_state=42)
    
    for n_features in total_features_list:
        print(f"\n>>> RUNNING SCENARIO: {n_features} Total Features (10 Informative, {n_features-10} Noise)")
        
        # 1. Generate Data
        X, y = make_classification(
            n_samples=150, 
            n_features=n_features, 
            n_informative=10, 
            n_redundant=n_features - 15 if n_features > 15 else 0,
            n_classes=2, 
            random_state=42
        )
        
        # 2. Evaluate PLS-DA (Standard - NO Feature Selection)
        # We use sparsity_penalty=1.0 so it keeps 100% of features.
        plsda_pipeline = Pipeline([('model', RWrapper(method='splsda'))])
        plsda_grid = {'model__n_components': [2], 'model__sparsity_penalty': [1.0]}
        
        engine.run_benchmark(X, y, "PLS-DA (Dense)", plsda_pipeline, plsda_grid)
        
        mcc_plsda = np.mean([m['mcc'] for m in engine.results_["PLS-DA (Dense)"]['fold_details']])
        stab_plsda = engine.calculate_stability_index("PLS-DA (Dense)", total_features=n_features)
        
        mcc_plsda_history.append(mcc_plsda)
        stab_plsda_history.append(stab_plsda)
        
        # 3. Evaluate sPLS-DA (Algebra)
        splsda_pipeline = Pipeline([('model', RWrapper(method='splsda'))])
        splsda_grid = {'model__n_components': [2], 'model__sparsity_penalty': [0.1, 0.125, 0.25, 0.5]}
        
        engine.run_benchmark(X, y, "sPLS-DA", splsda_pipeline, splsda_grid)
        
        # Extract MCC and Stability
        mcc_splsda = np.mean([m['mcc'] for m in engine.results_["sPLS-DA"]['fold_details']])
        stab_splsda = engine.calculate_stability_index("sPLS-DA", total_features=n_features)
        
        mcc_splsda_history.append(mcc_splsda)
        stab_splsda_history.append(stab_splsda)
        
        # 3. Evaluate Tsetlin Machine (Logic)
        tm_pipeline = Pipeline([
            ('booleanizer', SmartBooleanizer(n_bins=4)),
            ('model', TMWrapper(number_of_clauses=100, T=15, s=3.9, n_bins=4))
        ])
        tm_grid = {'model__number_of_clauses': [50, 100], 'model__T': [15, 25]}
        
        engine.run_benchmark(X, y, "Tsetlin Machine", tm_pipeline, tm_grid)
        
        # Extract MCC and Stability
        mcc_tm = np.mean([m['mcc'] for m in engine.results_["Tsetlin Machine"]['fold_details']])
        stab_tm = engine.calculate_stability_index("Tsetlin Machine", total_features=n_features)
        
        mcc_tm_history.append(mcc_tm)
        stab_tm_history.append(stab_tm)

    # ==========================================
    # PLOTTING THE RESULTS (1x2 SUBPLOT)
    # ==========================================
    print("\n[FINISH] Generating advanced multi-metric graph...")
    
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(15, 6))
    fig.suptitle('Algorithmic Degradation under Biological Noise Stress', fontsize=16, fontweight='bold', y=1.05)
    
    # Panel 1: Predictive Power (MCC)
    ax1.plot(total_features_list, mcc_plsda_history, marker='^', linewidth=2, label='PLS-DA (Dense)', color='#27ae60')
    ax1.plot(total_features_list, mcc_splsda_history, marker='o', linewidth=2, label='sPLS-DA (Algebra)', color='#e74c3c')
    ax1.plot(total_features_list, mcc_tm_history, marker='s', linewidth=2, label='Tsetlin Machine (Logic)', color='#2980b9')
    ax1.set_title('Impact on Predictive Performance (MCC)', fontsize=13)
    ax1.set_xlabel('Feature Dimensionality (Increasing Noise)', fontsize=11)
    ax1.set_ylabel('MCC', fontsize=11)
    ax1.axvline(x=10, color='gray', linestyle='--', label='Informative Features (10)', alpha=0.5)
    ax1.legend(fontsize=10)
    ax1.grid(True, linestyle=':', alpha=0.7)
    
    # Panel 2: Algorithmic Stability (Jaccard Index)
    ax2.plot(total_features_list, stab_plsda_history, marker='^', linewidth=2, label='PLS-DA Stability', color='#27ae60', linestyle='-.')
    ax2.plot(total_features_list, stab_splsda_history, marker='o', linewidth=2, label='sPLS-DA Stability', color='#e74c3c', linestyle='-.')
    ax2.plot(total_features_list, stab_tm_history, marker='s', linewidth=2, label='TM Stability', color='#2980b9', linestyle='-.')
    ax2.set_title('Impact on Selection Stability (Jaccard Index)', fontsize=13)
    ax2.set_xlabel('Feature Dimensionality (Increasing Noise)', fontsize=11)
    ax2.set_ylabel('Jaccard Similarity [0, 1]', fontsize=11)
    ax2.set_ylim([-0.05, 1.05])
    ax2.axvline(x=10, color='gray', linestyle='--', alpha=0.5)
    ax2.legend(fontsize=10)
    ax2.grid(True, linestyle=':', alpha=0.7)
    
    plt.tight_layout()
    
    # Save the plot securely in the project's root 'results' folder
    current_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.abspath(os.path.join(current_dir, ".."))
    results_dir = os.path.join(project_root, "results")
    os.makedirs(results_dir, exist_ok=True)
    
    output_filename = os.path.join(results_dir, "grafica_exp01_ruido_avanzado.png")
    plt.savefig(output_filename, dpi=300, bbox_inches='tight')
    print(f"✅ Advanced multi-metric graph saved securely at: {output_filename}")

if __name__ == "__main__":
    main()