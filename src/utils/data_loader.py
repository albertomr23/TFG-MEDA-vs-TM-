"""
Centralized Data Loading Module.
This is the single source of truth for dataset selection and loading.
Used across: exp_05, exp_06, exp_07, exp_08, exp_09, exp_10, exp_meda_04_v2.
"""

import os
import numpy as np
import pandas as pd
from typing import Tuple, List


def select_and_load_dataset() -> Tuple[np.ndarray, np.ndarray, List[str], str, str]:
    """
    Interactive prompt to select and load a dataset with correct preprocessing.
    
    Returns
    -------
    X : np.ndarray
        Feature matrix of shape (n_samples, n_features)
    y : np.ndarray
        Target vector of shape (n_samples,)
    feature_names : List[str]
        List of feature names
    dataset_type : str
        One of: 'simulated', 'real', 'simulated_hd'
    project_root : str
        Absolute path to project root directory
        
    Notes
    -----
    - Simulated datasets: target in column 0, features start at column 1
    - Real dataset: target in column 15, features start at column 16 (Peritonitis indicator)
    - High-dim simulated: same structure as simulated (curse of dimensionality)
    """
    print("\n" + "="*50)
    print(" DATASET SELECTION ")
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
        dataset_type = "simulated_hd"  
    else:
        print("[!] Invalid option. Defaulting to Option 1.")
        filename = "dataset_simulado_3000.xlsx"
        dataset_type = "simulated"

    # Locate the data directory
    current_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.abspath(os.path.join(current_dir, "..", ".."))  # Go up to project root
    data_path = os.path.join(project_root, "data", filename)
    
    print(f"Loading data from: {filename}...")
    try:
        df = pd.read_excel(data_path)
    except Exception as e:
        print(f"  Excel failed ({e}), trying CSV...")
        df = pd.read_csv(data_path.replace('.xlsx', '.csv'))
    
    # Apply dataset-specific slicing logic
    if dataset_type in ["simulated", "simulated_hd"]:
        # Simulated: Column 0 is binary target (0=healthy, 1=infected)
        y = df.iloc[:, 0].values
        X = df.iloc[:, 1:].values
        feature_names = df.columns[1:].tolist()
    elif dataset_type == "real":
        # Real: Column 15 is Peritonitis binary indicator, features start at column 16
        y_raw = df.iloc[:, 15].values
        X = df.iloc[:, 16:].values
        y = np.where(y_raw > 0, 1, 0)  # Binary: >0 = infected
        feature_names = df.columns[16:].tolist()
    else:
        raise ValueError(f"Unknown dataset_type: {dataset_type}")

    print(f"✅ Dataset loaded successfully: {X.shape[0]} patients and {X.shape[1]} biomarkers.\n")
    
    return X, y, feature_names, dataset_type, project_root
