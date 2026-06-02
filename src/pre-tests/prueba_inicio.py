# -*- coding: utf-8 -*-

import pandas as pd
import numpy as np
import bisect
import matplotlib.pyplot as plt
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, classification_report, ConfusionMatrixDisplay
from imblearn.over_sampling import RandomOverSampler
from pyTsetlinMachine.tm import MultiClassTsetlinMachine
import copy
import sys
import os

ruta_src = os.path.dirname(os.path.abspath(__file__))

if ruta_src not in sys.path:
    sys.path.append(ruta_src)

from interpretability.clinical_translator import ClinicalTranslator


# 1. Función casera para evitar importar TensorFlow
def to_categorical(y, num_classes):
    return np.eye(num_classes, dtype=int)[y]

# 2. Booleanizador
class Booleanizer:
    def __init__(self, mdn=False, encoding='one_hot', max_bits_per_feature=1, equal_bins=True):
        self.mdn = mdn
        self.encoding = encoding
        self.max_bits_per_feature = max_bits_per_feature
        self.equal_bins = equal_bins

    def fit(self, X):
        self.number_of_features = 0
        self.bins_list = []
        self.bits_per_feature = []
        for i in range(X.shape[1]):
            bins_no = self.max_bits_per_feature
            self.number_of_features += bins_no
            self.bits_per_feature.append(bins_no)
            if self.mdn:
                _, bins = pd.qcut(X[:, i], q=bins_no, retbins=True, duplicates='drop')
            else:
                bins = np.linspace(X[:, i].min(), X[:, i].max(), bins_no + 1)
            self.bins_list.append(bins)

    def transform(self, X):
        X_indx = np.zeros((X.shape[0], X.shape[1]), np.int64)
        for i in range(X.shape[1]):
            for j in range(X.shape[0]):
                X_indx[j, i] = bisect.bisect_right(self.bins_list[i][1:-1], X[j, i])

        if self.encoding == 'one_hot':
            X_out = np.array(to_categorical(X_indx[:, 0], num_classes=self.bits_per_feature[0]).astype(int))
            for i in range(1, X.shape[1]):
                X_out = np.concatenate((X_out, np.array(to_categorical(X_indx[:, i], num_classes=self.bits_per_feature[i])).astype(int)), axis=1)
        return X_out

# ==========================================
# 3. CARGA DE DATOS (Adaptado al simulado)
# ==========================================
print("Cargando y procesando dataset...")

# Asegúrate de que el nombre coincide con el de tu archivo
ruta_archivo = 'data/dataset_simulado_3000.xlsx' 
df = pd.read_excel(ruta_archivo)

# Limpieza automática: elimina espacios invisibles
df.columns = df.columns.str.strip()

# Separación Universal de X e Y
Y = df['PathoCode'].values
X_df_solubles = df.drop(columns=['PathoCode'])
X = X_df_solubles.values

bms_no = X.shape[1]
bm_names = list(X_df_solubles.columns)

print(f"Dataset listo: {X.shape[0]} pacientes y {bms_no} biomarcadores solubles.")

# ==========================================
# 4. BINARIZACIÓN Y SPLIT
# ==========================================
print("Booleanizando biomarcadores (4 intervalos)...")
max_bits = 4
bn = Booleanizer(mdn=False, encoding='one_hot', max_bits_per_feature=max_bits)
bn.fit(X)
X_bn = bn.transform(X)

X_train, X_test, Y_train, Y_test = train_test_split(X_bn, Y, test_size=0.2, stratify=Y, random_state=42)

ros = RandomOverSampler(random_state=42)
X_train_bal, Y_train_bal = ros.fit_resample(X_train, Y_train)

print(f"Set de Entrenamiento Balanceado: {X_train_bal.shape[0]} muestras.")
print(f"Set de Test: {X_test.shape[0]} muestras.")

# ==========================================
# 5. ENTRENAMIENTO DE LA TSETLIN MACHINE
# ==========================================
C, T, s = 20, 3, 5
tm = MultiClassTsetlinMachine(C, T, s)

tm_train_results = []
tm_test_results = []
epochs = 50 # He bajado de 300 a 50 para que no tarde demasiado en la prueba

best_test_acc = 0
best_tm = None 

print(f"Entrenando Tsetlin Machine ({epochs} epochs)...")
for epoch in range(epochs):
    tm.fit(X_train_bal, Y_train_bal, epochs=1, incremental=True)

    acc_train = accuracy_score(Y_train_bal, tm.predict(X_train_bal))
    acc_test = accuracy_score(Y_test, tm.predict(X_test))

    tm_train_results.append(acc_train)
    tm_test_results.append(acc_test)

    # Guardar el autómata cuando alcanza su mejor rendimiento
    if acc_test >= best_test_acc:
        best_test_acc = acc_test
        best_tm = copy.deepcopy(tm) 

print(f"¡Entrenamiento completado! El pico máximo en Test fue: {best_test_acc:.2%}")

# ==========================================
# 6. EVALUACIÓN Y GRÁFICAS
# ==========================================
y_test_pred = best_tm.predict(X_test)

print("\n================ REPORT DE CLASIFICACIÓN ================")
print(f"Accuracy final Test (Mejor Epoch): {best_test_acc:.2%}")
print("=========================================================\n")
print(classification_report(Y_test, y_test_pred, target_names=['Sano (0)', 'Infectado (1)']))

# 1. Gráfica de Aprendizaje
plt.figure(figsize=(10, 4))
plt.plot(tm_train_results, label='Train Accuracy', color='blue')
plt.plot(tm_test_results, label='Test Accuracy', color='red')
plt.axhline(y=best_test_acc, color='green', linestyle='--', label='Pico Máximo')
plt.title('Evolución del Accuracy de la Tsetlin Machine por Epoch')
plt.ylabel('Accuracy')
plt.xlabel('Epoch')
plt.legend(loc='lower right')
plt.grid(True, linestyle='--', alpha=0.6)
plt.savefig('results/ev_acc_prueba_inicio.png', bbox_inches='tight', dpi=300)
print("-> Gráfica de evolución guardada como 'ev_acc_prueba_inicio.png'")

# 2. Matriz de Confusión
print("\nMatriz de Confusión en Test (Mejor Modelo):")
ConfusionMatrixDisplay.from_predictions(Y_test, y_test_pred, display_labels=['Sano', 'Infectado'], cmap='Blues')
plt.savefig('results/mat_conf_prueba_inicio.png', bbox_inches='tight', dpi=300)
print("-> Matriz de confusión guardada como 'data/mat_conf_prueba_inicio.png'")

# ==========================================
# 3. INTERPRETABILITY (CLINICAL TRANSLATOR)
# ==========================================
print("\nGenerating clinical report using the external module...")

# Se actualizaron los nombres de los argumentos (tm_model, biomarker_names)
translator = ClinicalTranslator(tm_model=best_tm, biomarker_names=bm_names, max_bits=4)

# Llamada pasando los datos para que calcule los porcentajes
report = translator.get_clinical_profiles(X_data=X_train_bal, Y_data=Y_train_bal, max_rules_per_class=4)

print(report)
print("Legend: Q1 (Very Low), Q2 (Medium-Low), Q3 (Medium-High), Q4 (Very High)")