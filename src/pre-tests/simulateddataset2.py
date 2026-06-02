# src/simulateddataset2.py

import numpy as np
import pandas as pd
import os

def generar_dataset_simulado_alta_dim(n_pacientes=50, n_biomarcadores=4000, random_seed=42):
    # Fijamos la semilla para que sea 100% reproducible
    np.random.seed(random_seed)

    # 1. Nombrar las columnas
    columnas = [f'Biomarker_{i}' for i in range(n_biomarcadores)]
    columnas[0] = 'IL-6'  # Biomarcador Clave 1
    columnas[1] = 'IL-10' # Biomarcador Clave 2
    columnas[2] = 'TNF-a' # Biomarcador Cebo (Colineal para engañar al sPLS-DA)

    # 2. Generar distribuciones base simulando mediciones ruidosas
    # Matriz enorme de N x P
    X = np.random.normal(loc=50, scale=15, size=(n_pacientes, n_biomarcadores))

    # 3. Forzar Colinealidad: TNF-a copia casi exactamente a IL-6
    X[:, 2] = X[:, 0] + np.random.normal(0, 2, n_pacientes)

    # 4. Establecer umbrales biológicos (Mediana)
    umbral_il6 = np.median(X[:, 0])
    umbral_il10 = np.median(X[:, 1])

    # 5. Inyectar la regla epistática estricta 
    Y = np.zeros(n_pacientes, dtype=int)
    for i in range(n_pacientes):
        # LA REGLA OCULTA: SI (IL-6 es Alto) AND (IL-10 es Bajo) -> Infectado
        if X[i, 0] > umbral_il6 and X[i, 1] < umbral_il10:
            Y[i] = 1

    # 6. Empaquetar en DataFrame
    df = pd.DataFrame(X, columns=columnas)

    # 7. Introducir un poco de ruido en el diagnóstico 
    # Al tener tan pocos pacientes, el 5% es apenas 2 o 3 pacientes.
    n_ruido = max(1, int(n_pacientes * 0.05))
    indices_ruido = np.random.choice(n_pacientes, size=n_ruido, replace=False)
    Y[indices_ruido] = 1 - Y[indices_ruido]

    # Añadir el Target al DataFrame y reordenar para que sea la primera columna
    df['PathoCode'] = Y
    cols = ['PathoCode'] + columnas
    df = df[cols]

    return df

if __name__ == "__main__":
    print("=========================================================")
    print(" 🧬 GENERADOR DE DATASET: CURSE OF DIMENSIONALITY (N<<P) ")
    print("=========================================================\n")
    
    
    N = 50 
    P = 4000
    
    print(f">>> Generando {N} pacientes con {P} biomarcadores...")
    df_hd = generar_dataset_simulado_alta_dim(n_pacientes=N, n_biomarcadores=P)
    
    # Guardar en la carpeta data
    current_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.abspath(os.path.join(current_dir, ".."))
    data_dir = os.path.join(project_root, "data")
    os.makedirs(data_dir, exist_ok=True)
    
    ruta_guardado = os.path.join(data_dir, "dataset_simulado2.xlsx")
    df_hd.to_excel(ruta_guardado, index=False)
    
    print(f"\n✅ Dataset guardado con éxito en: {ruta_guardado}")
    print(f"📊 Dimensiones finales: {df_hd.shape[0]} filas x {df_hd.shape[1]} columnas.")
    print("Distribución de clases (Aprox. 25% Infectados esperados por la regla AND):")
    print(df_hd['PathoCode'].value_counts())
    print("\n¡Listo para destruir modelos lineales!")