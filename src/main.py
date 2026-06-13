"""
===============================================================================
GLOBAAL MENU AND DATA LOADER FOR EXPERIMENTS

Autor: Alberto Munuera Ramos
Date: June 2026
University: UGR

===============================================================================
"""

import os
import sys
import warnings

# Import the centralized data loader from your utils module
from utils.data_loader import select_and_load_dataset

# Mute warnings to keep the CLI output clean and readable during demonstrations
warnings.filterwarnings('ignore')

def display_menu():
    """
    Displays the main experiment menu and captures the user's choice.
    Returns:
        str: The selected experiment option.
    """
    print("\n" + "="*70)
    print(" 🔬 EXPERIMENT DISPATCHER: ALGEBRA VS. LOGIC ")
    print("="*70)
    print("Select the mathematical experiment you want to run:")
    print("  1. Exp 01: Noise Stress Test (Advanced Metrics)")
    print("  2. Exp 02: Booleanizer Resolution Impact")
    print("  3. Exp 03: Pure MEDA Evaluation (LR vs SVM)")
    print("  4. Exp 04: The Ultimate Clash (Pure Logic vs Algebra)")
    print("  5. Exp 05: Forward Hybridization (Algebra + Logic)")
    print("  6. Exp 06: Comparative Rule Extraction (XAI)")
    print("  7. Exp 07: Inverse Hybrid Latent Collapse (TM -> sPLSDA/vASCA)")
    print("  8. Exp 08: Inverse Hybrid Architecture (TM -> Linear SVM)")
    print("  9. Exp 09: Final Clinical Translation (White-Box XAI)")
    print("  0. Exit")
    print("="*70)
    
    return input("\nEnter the number of the experiment: ").strip()


def main():
    """
    Main entry point. Acts as a dynamic router to the different experiment modules,
    ensuring the core data context is loaded once and passed consistently.
    """
    print("=========================================================")
    print(" 🧬 TFG: EXPERIMENTAL ORCHESTRATOR ")
    print("=========================================================\n")
    
    # Step 1: Establish the topological space (Data Context) using the centralized loader
    try:
        # This will trigger your interactive prompt from utils.data_loader
        X, y, feature_names, dataset_type, project_root = select_and_load_dataset()
        
        # Setup the universal results directory for the main orchestrator
        results_dir = os.path.join(project_root, "results")
        os.makedirs(results_dir, exist_ok=True)
        
    except Exception as e:
        print(f"[!] Critical Error loading dataset via data_loader: {e}")
        sys.exit(1)
        
    # Step 2: Interactive Dispatcher Loop
    while True:
        choice = display_menu()
        
        if choice == '0':
            print("\n[INFO] Exiting Orchestrator. Goodbye!")
            break
            
        elif choice == '1':
            print("\n[INFO] Routing to Noise Stress Test...")
            import exp_01_noise
            exp_01_noise.main()
            
        elif choice == '2':
            print("\n[INFO] Routing to Booleanizer Resolution Analysis...")
            import exp_02_bool
            exp_02_bool.main()
            
        elif choice == '3':
            print("\n[INFO] Routing to Pure MEDA Tournament...")
            from exp_03_meda import run_experiment
            # Overriding specific results dir for modularity
            target_dir = os.path.join(results_dir, "meda_puro")
            os.makedirs(target_dir, exist_ok=True)
            run_experiment(X, y, feature_names, dataset_type, target_dir)
            
        elif choice == '4':
            print("\n[INFO] Routing to The Ultimate Clash...")
            import exp_04_versus
            exp_04_versus.main()
            
        elif choice == '5':
            print("\n[INFO] Routing to Forward Hybridization Evaluation...")
            from exp_05_hybrid import run_experiment
            target_dir = os.path.join(results_dir, "hybrid")
            os.makedirs(target_dir, exist_ok=True)
            run_experiment(X, y, dataset_type, target_dir)
            
        elif choice == '6':
            print("\n[INFO] Routing to Rule Extraction (XAI)...")
            from exp_06_extract_rules import run_experiment
            target_dir = os.path.join(results_dir, "rules")
            os.makedirs(target_dir, exist_ok=True)
            run_experiment(X, y, feature_names, dataset_type, target_dir)
            
        elif choice == '7':
            print("\n[INFO] Routing to Latent Collapse Analysis...")
            from exp_07_inverse_hybrid_latent import run_experiment
            target_dir = os.path.join(results_dir, "inverse_latent")
            os.makedirs(target_dir, exist_ok=True)
            run_experiment(X, y, dataset_type, target_dir)
            
        elif choice == '8':
            print("\n[INFO] Routing to Logic-to-Geometry (Inverse Hybrid SVM)...")
            from exp_08_inv_hybrid_svm import run_experiment
            target_dir = os.path.join(results_dir, "inverse_hybrid")
            os.makedirs(target_dir, exist_ok=True)
            run_experiment(X, y, dataset_type, target_dir)
            
        elif choice == '9':
            print("\n[INFO] Routing to Final Clinical Translation...")
            import exp_09_final_translator
            exp_09_final_translator.main()
            
        else:
            print("\n[!] Invalid choice. Please select a valid number from the menu.")

if __name__ == "__main__":
    main()