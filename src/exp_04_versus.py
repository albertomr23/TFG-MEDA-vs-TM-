# src/exp_06_pure_comparison.py

import numpy as np
import pandas as pd
import os
import warnings
import time
import math
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.pipeline import Pipeline
from sklearn.svm import SVC
from sklearn.preprocessing import StandardScaler
from sklearn.base import BaseEstimator, TransformerMixin
from sklearn.model_selection import StratifiedKFold
from sklearn.metrics import matthews_corrcoef, f1_score, precision_score, recall_score, accuracy_score
from utils.data_loader import select_and_load_dataset
from pipelines.meda_filter import MEDAFilter

# Importing custom modules
from models.r_wrapper import RWrapper
from models.tm_wrapper import TMWrapper
from features.smart_booleanizer import SmartBooleanizer

warnings.filterwarnings('ignore')


def main():
    print("=========================================================")
    print(" ⚔️  THE ULTIMATE CLASH: PURE LOGIC VS ALGEBRA ")
    print("=========================================================\n")
    
    X, y, feature_names, dataset_type, project_root = select_and_load_dataset()
    results_dir = os.path.join(project_root, "results", "versus")
    os.makedirs(results_dir, exist_ok=True)
    
    pipelines = {
        'Pure_TM': Pipeline([
            ('booleanizer', SmartBooleanizer(n_bins=3)),
            ('tm', TMWrapper(number_of_clauses=100, T=15, s=3.9, n_bins=3))
        ]),
        'Raw_SVM': Pipeline([
            ('scaler', StandardScaler()),
            ('svm', SVC(kernel='rbf', random_state=42))
        ]),
        'sPLSDA_SVM': Pipeline([
            ('splsda', MEDAFilter(method='splsda', n_components=2, sparsity_penalty=0.3)),
            ('scaler', StandardScaler()),
            ('svm', SVC(kernel='rbf', random_state=42))
        ]),
        'vASCA_SVM': Pipeline([
            ('vasca', MEDAFilter(method='vasca', n_components=2, sparsity_penalty=0.3)),
            ('scaler', StandardScaler()),
            ('svm', SVC(kernel='rbf', random_state=42))
        ])
    }
    
    cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)
    results_db = {}
    predictions_db = {}
    
    colors_dict = {'Pure_TM': '#2ecc71', 'Raw_SVM': '#95a5a6', 'sPLSDA_SVM': '#f39c12', 'vASCA_SVM': '#e74c3c'}

    for name, pipeline in pipelines.items():
        print(f"\n>>> FIGHTER ENTERING ARENA: {name}")
        start_time = time.time()
        
        # Trackers manually setup for custom printing
        y_pred_full = np.zeros_like(y)
        fold_metrics = {'MCC': [], 'F1': [], 'Precision': [], 'Recall': [], 'Accuracy': []}
        
        for fold_idx, (train_idx, test_idx) in enumerate(cv.split(X, y)):
            print(f"      -> Processing Fold {fold_idx + 1}/{cv.n_splits}...")
            
            X_train, y_train = X[train_idx], y[train_idx]
            X_test, y_test = X[test_idx], y[test_idx]
            
            # Fit and Predict
            pipeline.fit(X_train, y_train)
            y_pred = pipeline.predict(X_test)
            y_pred_full[test_idx] = y_pred
            
            # Compute metrics
            fold_metrics['MCC'].append(matthews_corrcoef(y_test, y_pred))
            fold_metrics['F1'].append(f1_score(y_test, y_pred))
            fold_metrics['Precision'].append(precision_score(y_test, y_pred, zero_division=0))
            fold_metrics['Recall'].append(recall_score(y_test, y_pred))
            fold_metrics['Accuracy'].append(accuracy_score(y_test, y_pred))
            
        elapsed_time = time.time() - start_time
        predictions_db[name] = y_pred_full
        
        # Aggregate Results
        results_db[name] = {
            'MCC': np.mean(fold_metrics['MCC']),
            'F1': np.mean(fold_metrics['F1']),
            'Precision': np.mean(fold_metrics['Precision']),
            'Recall': np.mean(fold_metrics['Recall']),
            'Accuracy': np.mean(fold_metrics['Accuracy']),
            'Time_Seconds': elapsed_time
        }
        
        print(f"    [RESULTS] {name} Completed in {elapsed_time:.2f}s:")
        print(f"      -> MCC:       {results_db[name]['MCC']:.3f}")
        print(f"      -> F1-Score:  {results_db[name]['F1']:.3f}")
        print(f"      -> Precision: {results_db[name]['Precision']:.3f}")
        print(f"      -> Recall:    {results_db[name]['Recall']:.3f}")
        print(f"      -> Accuracy:  {results_db[name]['Accuracy']:.3f}")

    print("\n[FINISH] Generating Advanced Clash Analytics (Saved in /results/versus/)...")

    # ==========================================
    # CHART 1: GROUPED BAR CHART
    # ==========================================
    metrics_bar = ['MCC', 'F1', 'Precision', 'Recall']
    x_bar = np.arange(len(metrics_bar))
    width = 0.25
    fig1, ax1 = plt.subplots(figsize=(10, 6))
    
    for i, (name, metrics) in enumerate(results_db.items()):
        scores = [metrics['MCC'], metrics['F1'], metrics['Precision'], metrics['Recall']]
        offset = (i - len(pipelines)/2 + 0.5) * width
        ax1.bar(x_bar + offset, scores, width, label=name, color=colors_dict[name], edgecolor='black')
        
    ax1.set_title('Clash of Titans: Baseline Predictive Performance', fontsize=14, fontweight='bold')
    ax1.set_xticks(x_bar)
    ax1.set_xticklabels(metrics_bar, fontweight='bold')
    ax1.set_ylim([0, 1.1])
    ax1.legend(loc='upper right')
    ax1.grid(True, axis='y', linestyle='--', alpha=0.5)
    fig1.savefig(os.path.join(results_dir, f"[{dataset_type}]_01_BarChart.png"), dpi=300, bbox_inches='tight')
    plt.close(fig1)

    # ==========================================
    # CHART 2: RADAR CHART (SPIDER PLOT)
    # ==========================================
    categories = ['MCC', 'F1', 'Precision', 'Recall', 'Accuracy']
    N = len(categories)
    angles = [n / float(N) * 2 * math.pi for n in range(N)]
    angles += angles[:1] # Close the polygon
    
    fig2, ax2 = plt.subplots(figsize=(8, 8), subplot_kw=dict(polar=True))
    ax2.set_theta_offset(math.pi / 2)
    ax2.set_theta_direction(-1)
    ax2.set_xticks(angles[:-1])
    ax2.set_xticklabels(categories, fontweight='bold', size=11)
    ax2.set_ylim(0, 1)
    
    for name, metrics in results_db.items():
        values = [metrics[cat] for cat in categories]
        values += values[:1] # Close the polygon
        ax2.plot(angles, values, color=colors_dict[name], linewidth=2, linestyle='solid', label=name)
        ax2.fill(angles, values, color=colors_dict[name], alpha=0.1)
        
    ax2.set_title('Multimetric Footprint: Logic vs Algebra', size=15, fontweight='bold', y=1.1)
    ax2.legend(loc='upper right', bbox_to_anchor=(1.2, 1.1))
    fig2.savefig(os.path.join(results_dir, f"[{dataset_type}]_02_RadarChart.png"), dpi=300, bbox_inches='tight')
    plt.close(fig2)

    # ==========================================
    # CHART 3: CLINICAL AGREEMENT MATRIX (McNemar)
    # ==========================================
    correct_tm = (predictions_db['Pure_TM'] == y)
    correct_vasca = (predictions_db['vASCA_SVM'] == y)
    
    both_correct = np.sum(correct_tm & correct_vasca)
    tm_only = np.sum(correct_tm & ~correct_vasca)
    svm_only = np.sum(~correct_tm & correct_vasca)
    both_wrong = np.sum(~correct_tm & ~correct_vasca)
    
    agreement_matrix = np.array([[both_correct, svm_only], [tm_only, both_wrong]])
    
    fig3, ax3 = plt.subplots(figsize=(7, 6))
    sns.heatmap(agreement_matrix, annot=True, fmt='d', cmap='Purples', cbar=False, ax=ax3,
                annot_kws={"size": 16, "weight": "bold"}, linewidths=1, linecolor='black')
    
    ax3.set_xticklabels(['vASCA+SVM\nCorrect', 'vASCA+SVM\nIncorrect'], fontweight='bold', fontsize=11)
    ax3.set_yticklabels(['TM\nCorrect', 'TM\nIncorrect'], fontweight='bold', fontsize=11, va='center')
    ax3.set_title('Prediction Orthogonality\n(Evaluated Patients)', fontsize=14, fontweight='bold', pad=20)
    fig3.savefig(os.path.join(results_dir, f"[{dataset_type}]_03_AgreementMatrix.png"), dpi=300, bbox_inches='tight')
    plt.close(fig3)

    # ==========================================
    # CHART 4: COMPUTATIONAL EFFICIENCY
    # ==========================================
    fig4, ax4 = plt.subplots(figsize=(8, 6))
    for name, metrics in results_db.items():
        ax4.scatter(metrics['Time_Seconds'], metrics['MCC'], s=300, c=[colors_dict[name]], 
                    label=name, alpha=0.8, edgecolors='black', linewidth=2)
        
    ax4.set_title('Trade-off: Computational Cost vs MCC', fontsize=14, fontweight='bold')
    ax4.set_xlabel('Training and Validation Time (Seconds)', fontsize=12, fontweight='bold')
    ax4.set_ylabel('Matthews Correlation Coefficient (MCC)', fontsize=12, fontweight='bold')
    ax4.grid(True, linestyle='--', alpha=0.6)
    ax4.legend(loc='lower right', title="Models", fontsize=11)
    fig4.savefig(os.path.join(results_dir, f"[{dataset_type}]_04_EfficiencyScatter.png"), dpi=300, bbox_inches='tight')
    plt.close(fig4)

    print("✅ All advanced visualizations correctly separated and saved in /results/versus/!")

if __name__ == "__main__":
    main()