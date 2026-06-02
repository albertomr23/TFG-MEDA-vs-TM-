# test_booleanizer.py

import numpy as np
import pandas as pd
import sys
import os

ruta_raiz = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ruta_raiz not in sys.path:
    sys.path.append(ruta_raiz)

from src.features.smart_booleanizer import SmartBooleanizer

def run_test():
    print("=== INITIALIZING SMART BOOLEANIZER TEST ===\n")
    
    # 1. Create a mock training dataset (5 patients, 2 biomarkers)
    # IL-6 range roughly 10 to 50. TNF-a range roughly 20 to 100.
    train_data = pd.DataFrame({
        'IL-6': [10.0, 20.0, 30.0, 40.0, 50.0],
        'TNF-a': [20.0, 40.0, 60.0, 80.0, 100.0]
    })
    
    print("1. TRAINING DATA (X_train):")
    print(train_data)
    print("-" * 50)
    
    # 2. Initialize and Fit the Booleanizer (4 bins = Quartiles)
    # This should generate 3 bits per feature (n_bins - 1)
    booleanizer = SmartBooleanizer(strategy='quantile', n_bins=4, encoding='thermometer')
    booleanizer.fit(train_data)
    
    print("2. LEARNED THRESHOLDS (Cuts):")
    for feature, thresholds in booleanizer.fitted_thresholds_.items():
        print(f"   {feature}: {thresholds}")
    print("-" * 50)
    
    # 3. Create a mock test dataset to challenge the algorithm
    # Patient 0: Normal values
    # Patient 1: OUT OF BOUNDS LOW (IL-6 = 2.0 -> Should clip to Q1)
    # Patient 2: OUT OF BOUNDS HIGH (TNF-a = 200.0 -> Should clip to Q4)
    test_data = pd.DataFrame({
        'IL-6': [25.0, 2.0, 45.0],
        'TNF-a': [50.0, 30.0, 200.0]
    })
    
    print("3. TEST DATA (X_test - Includes Outliers):")
    print(test_data)
    print("-" * 50)
    
    # 4. Transform the test data
    X_encoded = booleanizer.transform(test_data)
    
    print("4. THERMOMETER ENCODED OUTPUT (For Tsetlin Machine):")
    print("Columns: [IL-6_b1, IL-6_b2, IL-6_b3, TNF-a_b1, TNF-a_b2, TNF-a_b3]")
    print(X_encoded)
    print("\n=== TEST COMPLETE ===")

if __name__ == '__main__':
    run_test()