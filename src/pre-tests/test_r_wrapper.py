# src/test_r_wrapper.py

import numpy as np
import sys
import os
from sklearn.datasets import make_classification
from sklearn.model_selection import train_test_split

# Subimos al directorio raíz para que Python encuentre el módulo 'src'
ruta_raiz = os.path.dirname(os.path.abspath(__file__))
if ruta_raiz not in sys.path:
    sys.path.append(ruta_raiz)

from models.r_wrapper import RWrapper

def run_comprehensive_test():
    print("=== INITIALIZING COMPREHENSIVE R-PYTHON BRIDGE TEST ===\n")
    
    # 1. Generar datos sintéticos
    X, y = make_classification(
        n_samples=100, n_features=20, n_informative=10, n_classes=2, random_state=42
    )
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
    
    # ¡AQUÍ ESTÁ LA MAGIA! Metemos todos los modelos en la arena
    modelos_a_probar = ['splsda', 'spca', 'pca', 'vasca', 'asca']
    
    for metodo in modelos_a_probar:
        print(f"\n" + "="*50)
        print(f" TESTING MODEL: {metodo.upper()}")
        print("="*50)
        
        # Inicializamos el wrapper. Usamos sparsity=0.3 (30%) para que se note el corte
        wrapper = RWrapper(method=metodo, n_components=2, sparsity_penalty=0.3)
        
        # --- TEST FIT ---
        print(f"[1] Testing FIT for {metodo}...")
        try:
            wrapper.fit(X_train, y_train)
            print("    ✅ FIT SUCCESSFUL!")
            print(f"    Variables selected: {wrapper.selected_features_}")
            print(f"    Total variables kept: {len(wrapper.selected_features_)} out of 20")
        except Exception as e:
            print(f"    ❌ FIT FAILED: {e}")
            if metodo in ['vasca', 'asca']:
                print("    (💡 Nota: Revisa que parglmVS.R y vasca.R estén en src/models/r_scripts/)")
            continue # Si falla el fit, pasamos al siguiente modelo
            
        # --- TEST PREDICT ---
        print(f"\n[2] Testing PREDICT for {metodo}...")
        try:
            predictions = wrapper.predict(X_test)
            print("    ✅ PREDICT SUCCESSFUL!")
            accuracy = np.mean(predictions == y_test)
            print(f"    -> Accuracy: {accuracy * 100:.2f}%")
        except Exception as e:
            # Evaluamos si el error era esperado o no
            if metodo == 'splsda':
                # sPLS-DA DEBERÍA predecir, si entra aquí es un fallo real
                print(f"    ❌ PREDICT FAILED (Unexpected error): {e}")
            else:
                # Los demás NO deben predecir, así que el error es correcto
                print(f"    ⚠️ PREDICT BLOCKED (Expected behavior): {e}")

    print("\n=== COMPREHENSIVE TEST COMPLETE ===")

if __name__ == '__main__':
    run_comprehensive_test()