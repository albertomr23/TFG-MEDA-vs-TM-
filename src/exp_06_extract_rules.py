"""
===============================================================================
EXPERIMENT 06: COMPARATIVE RULE EXTRACTION (PURE TM vs HYBRID sPLSDA)

Autor: Alberto Munuera Ramos
Date: June 2026
University: UGR

===============================================================================
"""

import numpy as np
import pandas as pd
import os
import warnings

from sklearn.pipeline import Pipeline
from sklearn.base import BaseEstimator, TransformerMixin

from models.r_wrapper import RWrapper
from models.tm_wrapper import TMWrapper
from features.smart_booleanizer import SmartBooleanizer
from interpretability.clinical_translator import ClinicalTranslator
from utils.data_loader import select_and_load_dataset
from pipelines.meda_filter import MEDAFilter

import rpy2.robjects as robjects
robjects.r('options(warn=-1)')

warnings.filterwarnings('ignore')

def generate_boolean_feature_names(original_names, n_bins):
    """
    Generate feature names for boolean-encoded data using thermometer encoding.
    Thermometer encoding uses (n_bins - 1) boolean features per original feature.
    """
    bool_names = []
    n_bits_per_feature = n_bins - 1  # Thermometer encoding uses n_bins-1 bits
    for orig_name in original_names:
        for bit_idx in range(n_bits_per_feature):
            bool_names.append(f"{orig_name}_Bit{bit_idx+1}")
    return bool_names


def run_experiment(X, y, feature_names, dataset_type, results_dir):
    print("\n" + "="*70)
    print("  EXPERIMENT 06: COMPARATIVE RULE EXTRACTION (PURE TM vs HYBRID sPLSDA) ")
    print("="*70)
    
    # ---------------------------------------------------------
    # 1. PURE TSETLIN MACHINE (The Absolute Champion)
    # ---------------------------------------------------------
    print("\n>>> PHASE 1: Training PURE TSETLIN MACHINE (100% Features)...")
    pure_pipeline = Pipeline([
        ('booleanizer', SmartBooleanizer(n_bins=3)), 
        ('tm', TMWrapper(number_of_clauses=100, T=15, s=3.9, n_bins=3))
    ])
    
    pure_pipeline.fit(X, y)
    bool_model_pure = pure_pipeline.named_steps['booleanizer']
    X_bool_pure = bool_model_pure.transform(X)
    tm_pure_step = pure_pipeline.named_steps['tm']
    native_pure_tm = getattr(tm_pure_step, 'tm_', getattr(tm_pure_step, 'model_', tm_pure_step))
    
    # Generate proper boolean feature names for pure TM
    n_bins = bool_model_pure.n_bins
    max_bits = n_bins - 1
    bool_feature_names_pure = generate_boolean_feature_names(feature_names, n_bins)
    
    translator_pure = ClinicalTranslator(tm_model=native_pure_tm, biomarker_names=bool_feature_names_pure, max_bits=max_bits)
    report_pure = translator_pure.generate_clinical_profiles(X_data=X_bool_pure, Y_data=y, max_rules_per_class=4)
    
    # ---------------------------------------------------------
    # 2. HYBRID sPLS-DA + TM (The Efficiency Champion)
    # ---------------------------------------------------------
    print("\n>>> PHASE 2: Training HYBRID sPLS-DA + TM (Cost-Efficient)...")
    hybrid_pipeline = Pipeline([
        ('filter', MEDAFilter(method='splsda', n_components=2, sparsity_penalty=0.5)),
        ('booleanizer', SmartBooleanizer(n_bins=3)),
        ('tm', TMWrapper(number_of_clauses=100, T=15, s=3.9, n_bins=3))
    ])
    
    hybrid_pipeline.fit(X, y)
    filter_step = hybrid_pipeline.named_steps['filter']
    surviving_indices = filter_step.selected_indices_
    surviving_biomarkers = [feature_names[i] for i in surviving_indices]
    
    print(f"  -> sPLS-DA algebraic filter retained {len(surviving_biomarkers)} core biomarkers.")
    
    X_filtered = filter_step.transform(X)
    bool_model_hybrid = hybrid_pipeline.named_steps['booleanizer']
    X_bool_hybrid = bool_model_hybrid.transform(X_filtered)
    tm_hybrid_step = hybrid_pipeline.named_steps['tm']
    native_hybrid_tm = getattr(tm_hybrid_step, 'tm_', getattr(tm_hybrid_step, 'model_', tm_hybrid_step))
    
    # Generate proper boolean feature names for hybrid TM
    n_bins_hybrid = bool_model_hybrid.n_bins
    max_bits_hybrid = n_bins_hybrid - 1
    bool_feature_names_hybrid = generate_boolean_feature_names(surviving_biomarkers, n_bins_hybrid)
    
    translator_hybrid = ClinicalTranslator(tm_model=native_hybrid_tm, biomarker_names=bool_feature_names_hybrid, max_bits=max_bits_hybrid)
    report_hybrid = translator_hybrid.generate_clinical_profiles(X_data=X_bool_hybrid, Y_data=y, max_rules_per_class=4)

    # ---------------------------------------------------------
    # 3. SAVE COMPARATIVE ARTIFACT
    # ---------------------------------------------------------
    print("\n[FINISH] Generating Comparative Knowledge Base...")
    report_filename = os.path.join(results_dir, f"[{dataset_type}]_comparative_clinical_rules.txt")
    
    with open(report_filename, "w", encoding="utf-8") as f:
        f.write("=================================================================\n")
        f.write(f" TFG CLINICAL REPORT: EPISTATIC RULE COMPARISON\n")
        f.write(f" Dataset: {dataset_type.upper()} | Total Patients: {X.shape[0]}\n")
        f.write(" Legend: T1 (Low), T2 (Medium), T3 (High)\n")
        f.write("=================================================================\n\n")
        
        f.write("-----------------------------------------------------------------\n")
        f.write(" PART 1: PURE TSETLIN MACHINE (100% Topologic Vocabulary)\n")
        f.write("-----------------------------------------------------------------\n")
        f.write(f"Available Biomarkers ({len(feature_names)}): {', '.join(feature_names)}\n\n")
        f.write(report_pure)
        f.write("\n\n")
        
        f.write("-----------------------------------------------------------------\n")
        f.write(" PART 2: HYBRID sPLS-DA + TM (Algebraically Filtered Vocabulary)\n")
        f.write("-----------------------------------------------------------------\n")
        f.write(f"Surviving Biomarkers ({len(surviving_biomarkers)}): {', '.join(surviving_biomarkers)}\n\n")
        f.write(report_hybrid)

    print(f"[OK] Comparative Clinical Knowledge Base saved locally at: {report_filename}")

if __name__ == "__main__":
    try:
        X, y, feature_names, dataset_type, project_root = select_and_load_dataset()
        results_dir = os.path.join(project_root, "results", "rules")
        os.makedirs(results_dir, exist_ok=True)
        run_experiment(X, y, feature_names, dataset_type, results_dir)
    except Exception as e:
        print(f"[!] Fatal Error during standalone execution: {e}")