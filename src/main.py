# src/main.py

import os
import sys
import warnings
import numpy as np
import pandas as pd


# Filter warnings for a clean CLI experience
warnings.filterwarnings('ignore')

def display_menu():
    """
    Displays the main experiment menu and captures the user's choice.
    Returns:
        str: The selected experiment option.
    """
    print("\n" + "="*60)
    print(" 🔬 EXPERIMENT DISPATCHER: ALGEBRA VS. LOGIC ")
    print("="*60)
    print("Select the mathematical experiment you want to run:")
    print("  1. Baseline: Pure Models (sPLS-DA vs. Tsetlin Machine)")
    print("  2. Experiment 04: MEDA Tournament (PCA, sPCA, sPLS-DA, vASCA)")
    print("  3. Experiment 05/06: Hybridization (Algebra + Logic)")
    print("  4. Experiment 07: Clinical Rule Extraction (XAI)")
    print("  0. Exit")
    print("="*60)
    
    return input("\nEnter the number of the experiment: ").strip()

def select_and_load_dataset():
    print("\n" + "="*50)
    print(" 📂 DATASET SELECTION ")
    print("="*50)
    print("1. Simulated Dataset (3000 patients, 40 features)")
    print("2. Real Clinical Dataset (Olga & Eberl - 82 patients)")
    print("3. High-Dim Simulated Dataset (Curse of Dimensionality: 50 patients, 4000 features)")
    
    opcion = input("\nChoose an option (1, 2, or 3): ").strip()
    
    if opcion == '1':
        filename = "dataset_simulado_3000.xlsx"
        dataset_type = "simulated"
    elif opcion == '2':
        filename = "dataset_real.xlsx"
        dataset_type = "real"
    elif opcion == '3':
        filename = "dataset_simulado2.xlsx"
        # Added this suffix so the new plots don't overwrite my previous 3000-patient ones
        dataset_type = "simulated_hd"  
    else:
        print("[!] Invalid option. Defaulting to Option 1.")
        filename = "dataset_simulado_3000.xlsx"
        dataset_type = "simulated"

    current_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.abspath(os.path.join(current_dir, ".."))
    data_path = os.path.join(project_root, "data", filename)
    
    # Make sure we are pointing to the right results folder for this specific script
    results_dir = os.path.join(project_root, "results", "main")
    os.makedirs(results_dir, exist_ok=True)

    print(f"Loading data from: {filename}...")
    try:
        df = pd.read_excel(data_path)
    except Exception as e:
        # Quick fallback just in case I saved it as CSV instead of Excel during generation
        df = pd.read_csv(data_path.replace('.xlsx', '.csv'))
    
    # Target and feature slicing logic depends on the raw Excel structure
    if dataset_type in ["simulated", "simulated_hd"]:
        # For my custom generated datasets, the target (PathoCode) is always at column 0
        y = df.iloc[:, 0].values
        X = df.iloc[:, 1:].values
        feature_names = df.columns[1:].tolist()
    elif dataset_type == "real":
        # For the Olga & Eberl clinical cohort, Peritonitis target is at 15 and biomarkers start at 16
        y_raw = df.iloc[:, 15].values
        X = df.iloc[:, 16:].values
        y = np.where(y_raw > 0, 1, 0)
        feature_names = df.columns[16:].tolist()

    print(f"✅ Dataset loaded successfully: {X.shape[0]} patients and {X.shape[1]} biomarkers.\n")
    
    # Returning feature_names too, since I'll probably need them later for the Clinical Translator
    return X, y, feature_names, dataset_type, results_dir


def main():
    """
    Main entry point. Acts as a router to the different experiment modules,
    ensuring data context is loaded once and passed consistently.
    """
    print("=========================================================")
    print(" 🧬 TFG: EXPERIMENTAL ORCHESTRATOR ")
    print("=========================================================\n")
    
    # Step 1: Load the topological space (Data context)
    try:
        X, y, feature_names, dataset_type, results_dir = select_and_load_dataset()
    except Exception as e:
        print(f"[!] Critical Error loading dataset: {e}")
        sys.exit(1)
        
    # Step 2: Interactive Dispatcher Loop
    while True:
        choice = display_menu()
        
        if choice == '0':
            print("\n[INFO] Exiting Orchestrator. Goodbye!")
            break
            
        elif choice == '1':
            print("\n[INFO] Routing to Baseline Evaluation...")
            # Example of how we will import and route
            # from experiments.exp_baseline import run_experiment
            # run_experiment(X, y, feature_names, dataset_type, results_dir)
            print("[!] Module not yet linked. Coming soon!")
            
        elif choice == '2':
            print("\n[INFO] Routing to MEDA Tournament...")
            from exp_meda_04_v2 import run_experiment
            run_experiment(X, y, feature_names, dataset_type, results_dir)
            
        elif choice == '3':
            print("\n[INFO] Routing to Hybridization Evaluation...")
            # Assuming you rename exp_05_hybrid.py's main function to run_experiment
            from exp_05_hybrid import run_experiment
            run_experiment(X, y, feature_names, dataset_type, results_dir)
            
        elif choice == '4':
            print("\n[INFO] Routing to Clinical Rule Extraction...")
            from exp_07_extract_rules import run_experiment
            run_experiment(X, y, feature_names, dataset_type, results_dir)
            
        else:
            print("\n[!] Invalid choice. Please select a valid number.")

if __name__ == "__main__":
    main()