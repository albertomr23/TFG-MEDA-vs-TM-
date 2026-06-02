# src/exp_10_final_translation.py

import os
import numpy as np
import pandas as pd
import warnings
from sklearn.svm import SVC
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.base import BaseEstimator, TransformerMixin

# Importing custom TFG modules
from models.r_wrapper import RWrapper
from models.tm_wrapper import TMWrapper
from features.smart_booleanizer import SmartBooleanizer
from interpretability.clinical_translator import ClinicalTranslator
from utils.data_loader import select_and_load_dataset  # ✅ CENTRALIZED
from pipelines.meda_filter import MEDAFilter  # ✅ CENTRALIZED

warnings.filterwarnings('ignore')

class TMClauseExtractor(BaseEstimator, TransformerMixin):
    """
    Clause Extractor for the Inverse Hybrid Architecture.
    Uses the Tsetlin Machine upstream to evaluate the full biomarker vocabulary 
    and outputs the boolean activation state of its clauses.
    """
    def __init__(self, number_of_clauses=100, T=15, s=3.9, n_bins=3):
        self.number_of_clauses = number_of_clauses
        self.T = T
        self.s = s
        self.n_bins = n_bins
        # Initialize internal components
        self.booleanizer = SmartBooleanizer(n_bins=self.n_bins)
        self.tm = TMWrapper(number_of_clauses=self.number_of_clauses, T=self.T, s=self.s, n_bins=self.n_bins)

    def fit(self, X, y):
        # Discretize continuous data and train the Tsetlin Machine
        X_bool = self.booleanizer.fit_transform(X)
        self.tm.fit(X_bool, y)
        return self

    def transform(self, X):
        # Transform data into discrete bins and extract clause activation vectors
        X_bool = self.booleanizer.transform(X)
        return self.tm.get_clause_activations(X_bool)

def generate_boolean_feature_names(original_names, n_bins):
    """
    Generate feature names for boolean-encoded data using thermometer encoding.
    Thermometer encoding uses (n_bins - 1) boolean features per original feature.
    
    For example, with n_bins=3:
    - Q1: [0, 0]
    - Q2: [1, 0]
    - Q3: [1, 1]
    
    So each original feature becomes (n_bins-1) boolean features.
    """
    bool_names = []
    n_bits_per_feature = n_bins - 1  # Thermometer encoding uses n_bins-1 bits
    for orig_name in original_names:
        for bit_idx in range(n_bits_per_feature):
            bool_names.append(f"{orig_name}_Bit{bit_idx+1}")
    return bool_names




def main():
    # 1. Load data using the centralized interactive function
    X, y, feature_names, dataset_type, project_root = select_and_load_dataset()

    # Create the specific output directory for this final experiment
    results_dir = os.path.join(project_root, "results", "final_translation")
    os.makedirs(results_dir, exist_ok=True)

    print("\n" + "="*70)
    print(f" 🏥 EXP 10: FINAL CLINICAL TRANSLATION ({dataset_type.upper()}) ")
    print("="*70)

    # 2. Define the 3 mathematical architectures requested in the memory
    pipelines = {
        'Pure_TM': Pipeline([
            ('booleanizer', SmartBooleanizer(n_bins=3)),
            ('tm', TMWrapper(number_of_clauses=100, T=15, s=3.9, n_bins=3))
        ]),
        'sPLSDA_TM': Pipeline([
            ('splsda', MEDAFilter(method='splsda', n_components=2, sparsity_penalty=0.3)),
            ('booleanizer', SmartBooleanizer(n_bins=3)),
            ('tm', TMWrapper(number_of_clauses=100, T=15, s=3.9, n_bins=3))
        ]),
        'Inverse_TM_SVM': Pipeline([
            
            ('tm_extractor', TMClauseExtractor(number_of_clauses=100, T=15, s=3.9, n_bins=3)),
            ('svm', SVC(kernel='linear', random_state=42)) 
        ])
    }

    report_path = os.path.join(results_dir, f"Final_Report_{dataset_type}.txt")
    
    with open(report_path, "w", encoding="utf-8") as f:
        f.write("="*80 + "\n")
        f.write(f" CLINICAL KNOWLEDGE BASE - DATASET: {dataset_type.upper()}\n")
        f.write("="*80 + "\n\n")

        for model_name, pipeline in pipelines.items():
            print(f"    -> Extracting rules from architecture: {model_name}...")
            pipeline.fit(X, y)

            # 3. Dynamic rule extraction based on the mathematical nature of the model
            if model_name == 'Inverse_TM_SVM':
                extractor = pipeline.named_steps['tm_extractor']
                svm = pipeline.named_steps['svm']
                n_bins = extractor.n_bins
                
                # Generate proper boolean feature names (thermometer encoding uses n_bins-1 bits per feature)
                bool_feature_names = generate_boolean_feature_names(feature_names, n_bins)
                
                # Use max_bits = n_bins - 1 (thermometer encoding) for proper indexing
                max_bits = n_bins - 1
                translator = ClinicalTranslator(tm_model=extractor.tm.model_, biomarker_names=bool_feature_names, max_bits=max_bits)
                svm_weights = svm.coef_[0]
                
                top_infected_idx = np.argsort(svm_weights)[-5:][::-1]
                top_healthy_idx = np.argsort(svm_weights)[:5]
                
                report_text = "--- TOP 5 GEOMETRIC RULES FOR INFECTION (Class 1) ---\n"
                for rank, idx in enumerate(top_infected_idx):
                    # Map the linear SVM weight index back to the specific class/clause in TM
                    class_idx = idx // extractor.tm.number_of_clauses
                    clause_idx = idx % extractor.tm.number_of_clauses
                    
                    # FIXED: Direct call to your internal decoding method
                    rule_text = translator._decode_clause(class_idx, clause_idx)
                    report_text += f"Rank #{rank+1} [SVM Weight: +{svm_weights[idx]:.3f}]:\n  {rule_text}\n\n"
                    
                report_text += "--- TOP 5 GEOMETRIC RULES FOR HOMEOSTASIS (Class 0) ---\n"
                for rank, idx in enumerate(top_healthy_idx):
                    class_idx = idx // extractor.tm.number_of_clauses
                    clause_idx = idx % extractor.tm.number_of_clauses
                    
                    rule_text = translator._decode_clause(class_idx, clause_idx)
                    report_text += f"Rank #{rank+1} [SVM Weight: {svm_weights[idx]:.3f}]:\n  {rule_text}\n\n"

            elif model_name == 'sPLSDA_TM':
                # 1. Recuperamos los índices que han sobrevivido al filtro algebraico
                filter_step = pipeline.named_steps['splsda']
                surviving_indices = filter_step.selected_indices_
                # 2. Rescatamos sus nombres reales de la lista original
                surviving_biomarkers = [feature_names[i] for i in surviving_indices]
                
                tm_model = pipeline.named_steps['tm']
                bool_model = pipeline.named_steps['booleanizer']
                n_bins = bool_model.n_bins
                
                # Transformamos usando las variables filtradas
                X_filtered = filter_step.transform(X)
                X_bool = bool_model.transform(X_filtered)
                
                # 3. Generamos los nombres booleanos usando las variables supervivientes
                bool_feature_names = generate_boolean_feature_names(surviving_biomarkers, n_bins)
                
                max_bits = n_bins - 1
                translator = ClinicalTranslator(tm_model=tm_model.model_, biomarker_names=bool_feature_names, max_bits=max_bits)
                report_text = translator.generate_clinical_profiles(X_data=X_bool, Y_data=y, max_rules_per_class=5)

            else: 
                tm_model = pipeline.named_steps['tm']
                bool_model = pipeline.named_steps['booleanizer']
                X_bool = bool_model.transform(X)
                n_bins = bool_model.n_bins
                
                # Generate proper boolean feature names (thermometer encoding uses n_bins-1 bits per feature)
                bool_feature_names = generate_boolean_feature_names(feature_names, n_bins)
                
                # Use max_bits = n_bins - 1 (thermometer encoding) for proper indexing
                max_bits = n_bins - 1
                translator = ClinicalTranslator(tm_model=tm_model.model_, biomarker_names=bool_feature_names, max_bits=max_bits)
                report_text = translator.generate_clinical_profiles(X_data=X_bool, Y_data=y, max_rules_per_class=5)

            # Write architecture rules to the dataset's final report
            f.write(f"--- ARCHITECTURE: {model_name} ---\n")
            f.write(report_text + "\n")
            f.write("-" * 80 + "\n\n")

    print(f"[+] Translation complete! Report saved to: {report_path}")
    
if __name__ == "__main__":
    main()