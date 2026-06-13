

import numpy as np
import warnings
from sklearn.datasets import make_classification
import rpy2.robjects as robjects


from models.r_wrapper import RWrapper

warnings.filterwarnings('ignore')

def main():
    print("=========================================================")
    print(" 🛠️ VASCA & ASCA DEBUGGER ")
    print("=========================================================\n")
    
    # 1. Creamos el mismo dataset de prueba
    X, y = make_classification(n_samples=150, n_features=50, n_informative=10, random_state=42)
    
    print("[1] Instanciando el RWrapper para vASCA...")
    # Usamos sparsity_penalty=0.5 (esto se traduce al siglev en R)
    wrapper = RWrapper(method='vasca', n_components=2, sparsity_penalty=0.5)
    
    print("[2] Ajustando el modelo (Mandando datos a R)...")
    wrapper.fit(X, y)
    
    # 3. Vemos qué ha devuelto matemáticamente
    print("\n[RESULTADOS DE EXTRACCIÓN]")
    print(f" -> Variables seleccionadas: {wrapper.selected_features_}")
    print(f" -> Número total retenido:   {len(wrapper.selected_features_)} de 50")
    
    # 4. Forzamos a R a que nos diga cuáles eran esos 12 warnings
    print("\n[R WARNINGS INTERNOS]")
    try:
        robjects.r('if(length(warnings()) > 0) print(warnings()) else print("No hay warnings pendientes en R.")')
    except Exception as e:
        print("Error leyendo warnings de R:", e)

if __name__ == "__main__":
    main()