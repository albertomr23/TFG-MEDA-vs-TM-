import os
import numpy as np
import pandas as pd
import warnings
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.svm import SVC
from sklearn.base import BaseEstimator, TransformerMixin

# Importing custom TFG modules
from models.r_wrapper import RWrapper
from models.tm_wrapper import TMWrapper
from features.smart_booleanizer import SmartBooleanizer

warnings.filterwarnings('ignore')

# Load dataset
current_dir = os.path.dirname(os.path.abspath(__file__))
data_path = os.path.join(current_dir, "data", "dataset_simulado_3000.xlsx")

df = pd.read_excel(data_path)
y = df.iloc[:, 0].values
X = df.iloc[:, 1:].values
feature_names = df.columns[1:].tolist()

print(f"X shape: {X.shape}")
print(f"y shape: {y.shape}")
print(f"Feature names count: {len(feature_names)}")

# Test sPLSDA_TM pipeline
print("\n=== Testing sPLSDA_TM Pipeline ===")

splsda = RWrapper(method='splsda', n_components=2, sparsity_penalty=0.3)
splsda.fit(X, y)

X_lat = splsda.transform(X)
print(f"X_lat shape (after sPLSDA): {X_lat.shape}")

booleanizer = SmartBooleanizer(n_bins=3)
booleanizer.fit(X_lat, y)

X_bool = booleanizer.transform(X_lat)
print(f"X_bool shape (after booleanizer): {X_bool.shape}")
print(f"Booleanizer n_bins: {booleanizer.n_bins}")

tm = TMWrapper(number_of_clauses=100, T=15, s=3.9, num_bins=3)
tm.fit(X_bool, y)

print(f"TM number_of_features: {tm.model_.number_of_features}")
print(f"TM half_features: {tm.model_.number_of_features // 2}")
print(f"TM number_of_clauses: {tm.model_.number_of_clauses}")
print(f"TM number_of_classes: {tm.model_.number_of_classes}")

# Generate names
n_bins = booleanizer.n_bins
n_bits_per_feature = n_bins - 1

latent_features = [f"Latent_Score_{i+1}" for i in range(2)]
print(f"\nOriginal latent features: {latent_features}")

bool_names = []
for orig_name in latent_features:
    for bit_idx in range(n_bits_per_feature):
        bool_names.append(f"{orig_name}_Bit{bit_idx+1}")

print(f"Generated boolean feature names ({len(bool_names)} total):")
for i, name in enumerate(bool_names):
    print(f"  {i}: {name}")

print(f"\nExpected by decoder:")
print(f"  max_bits = {n_bits_per_feature}")
print(f"  For TM with {tm.model_.number_of_features} features:")
print(f"    half_features = {tm.model_.number_of_features // 2}")
print(f"    actual_k will range from 0 to {tm.model_.number_of_features // 2 - 1}")
print(f"    bm_index will range from 0 to {(tm.model_.number_of_features // 2 - 1) // n_bits_per_feature}")
print(f"    Max bm_index needed: {(tm.model_.number_of_features // 2 - 1) // n_bits_per_feature}")
print(f"    But we only have {len(bool_names)} names (indices 0-{len(bool_names)-1})")
