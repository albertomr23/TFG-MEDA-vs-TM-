# src/exp_bool_02.py

import numpy as np
import os
import warnings
import matplotlib.pyplot as plt
from sklearn.datasets import make_classification
from sklearn.pipeline import Pipeline

# Import custom modules
from models.tm_wrapper import TMWrapper
from features.smart_booleanizer import SmartBooleanizer
from evaluation.benchmark_engine import BenchmarkEngine

warnings.filterwarnings('ignore')

def main():
    print("=========================================================")
    print(" 📊 EXPERIMENT 02: BOOLEANIZER RESOLUTION IMPACT (ADVANCED) ")
    print("=========================================================\n")
    
    bins_to_test = [2, 3, 4, 5]
    
    mcc_distributions = []
    stability_history = []
    literal_space_history = []
    
    # Generamos un dataset de clasificación estándar (40 features continuas)
    n_features = 40
    X, y = make_classification(n_samples=150, n_features=n_features, n_informative=10, random_state=42)
    
    # Motor de evaluación con 3 pliegues externos
    engine = BenchmarkEngine(outer_cv=3, inner_cv=2, random_state=42)
    
    for n_bins in bins_to_test:
        print(f"\n>>> RUNNING SCENARIO: Resolution = {n_bins} Bins")
        
        tm_pipeline = Pipeline([
            ('booleanizer', SmartBooleanizer(n_bins=n_bins)),
            ('model', TMWrapper(number_of_clauses=100, T=15, s=3.9, n_bins=n_bins))
        ])
        
        tm_grid = {'model__number_of_clauses': [50, 100], 'model__T': [15, 25]}
        model_name = f"TM_{n_bins}_bins"
        
        # Ejecutamos el benchmark con validación cruzada anidada
        engine.run_benchmark(X, y, model_name, tm_pipeline, tm_grid)
        
        # 1. Extraemos la distribución completa de MCC de los pliegues (para el Boxplot)
        folds_mcc = [m['mcc'] for m in engine.results_[model_name]['fold_details']]
        mcc_distributions.append(folds_mcc)
        
        # 2. Calculamos la estabilidad de Jaccard
        stability = engine.calculate_stability_index(model_name, total_features=X.shape[1])
        stability_history.append(stability)
        
        # 3. Cálculo matemático del espacio de literales activo: 2 * features * (bins - 1)
        total_literals = 2 * n_features * (n_bins - 1)
        literal_space_history.append(total_literals)
        
        print(f"    -> Mean MCC: {np.mean(folds_mcc):.3f} | Stability: {stability:.3f} | Total Literals: {total_literals}")

    # ==========================================
    # PLOTTING THE RESULTS (1x2 SUBPLOT AVANZADO)
    # ==========================================
    print("\n[FINISH] Generating advanced multi-panel visual proof...")
    
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(15, 6))
    fig.suptitle('State-Space Analysis and Generalization Capacity', fontsize=16, fontweight='bold', y=1.05)
    
    # PANEL 1: Distribución de la Capacidad Predictiva (Boxplot de MCC)
    box = ax1.boxplot(mcc_distributions, patch_artist=True, labels=[f"{b} Bins" for b in bins_to_test])
    
    # Estilizar el boxplot de forma elegante
    for patch in box['boxes']:
        patch.set_alpha(0.6)
    for median in box['medians']:
        median.set_linewidth(2)
        
    ax1.set_title('Predictive Performance Stability across Folds', fontsize=13)
    ax1.set_xlabel('Discretization Resolution', fontsize=11)
    ax1.set_ylabel('Matthews Correlation Coefficient (MCC)', fontsize=11)
    ax1.set_ylim([-0.1, 1.1])
    ax1.grid(True, linestyle=':', alpha=0.5)
    
    # PANEL 2: Dilema de Complejidad Combinatoria (Doble Eje Y)
    color_jaccard = '#e74c3c'
    ax2.plot([str(b) for b in bins_to_test], stability_history, color=color_jaccard, marker='o', linewidth=3, label='Stability (Jaccard)')    
    ax2.set_title('Literal Space Explosion vs. Rule Stability', fontsize=13)
    ax2.set_xlabel('Number of Intervals (Bins)', fontsize=11)
    ax2.set_ylabel('Selection Stability (Jaccard Index)', color=color_jaccard, fontsize=11)
    ax2.tick_params(axis='y', labelcolor=color_jaccard)
    ax2.set_ylim([-0.05, 1.05])
    
    # Segundo eje Y para el tamaño del espacio binarizado
    ax3 = ax2.twinx()
    color_literals = '#2c3e50'
    ax3.plot([str(b) for b in bins_to_test], literal_space_history, color=color_literals, marker='s', linewidth=2, linestyle='--')
    ax3.set_ylabel('Literal Space Size (2 * N * (Bins-1))', color=color_literals, fontsize=11)
    ax3.tick_params(axis='y', labelcolor=color_literals)
    
    ax2.grid(True, linestyle=':', alpha=0.5)
    
    plt.tight_layout()
    
    # Guardar de forma segura en la carpeta raíz del proyecto
    current_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.abspath(os.path.join(current_dir, ".."))
    results_dir = os.path.join(project_root, "results")
    os.makedirs(results_dir, exist_ok=True)
    
    output_filename = os.path.join(results_dir, "grafica_exp02_bins_avanzado.png")
    plt.savefig(output_filename, dpi=300, bbox_inches='tight')
    print(f"✅ Advanced discretization analysis graph saved at: {output_filename}")

if __name__ == "__main__":
    main()