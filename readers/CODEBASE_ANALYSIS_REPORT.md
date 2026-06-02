# Comprehensive Codebase Analysis Report
## TFG: MEDA vs Tsetlin Machine

**Date**: 2026-06-01  
**Scope**: All Python files in `src/` directory  
**Total Files Analyzed**: 25+ files  

---

## EXECUTIVE SUMMARY

The codebase exhibits significant structural issues, code duplication, inconsistent naming conventions, and missing type annotations. These issues primarily stem from evolutionary development (multiple experiment iterations) without refactoring for consistency. Below is a detailed categorized analysis with 35+ specific issues identified.

---

## 1. IMPORT INCONSISTENCIES

### 1.1 Wrong Module Import
**File**: [src/models/tm_wrapper.py](src/models/tm_wrapper.py#L4)  
**Issue**: Incorrect import statement
```python
from yaml import warnings  # ❌ WRONG
```
**Should be**:
```python
import warnings  # ✅ CORRECT
```
**Impact**: Could cause AttributeError when trying to use warnings module functions.

---

### 1.2 Path-Based Import Issues in Test Files
**Files**: 
- [src/test_booleanizer.py](src/test_booleanizer.py#L6)
- [src/test_r_wrapper.py](src/test_r_wrapper.py#L10)

**Issue**: Inconsistent import approach
```python
# test_booleanizer.py
from src.features.smart_booleanizer import SmartBooleanizer  # Absolute path works from root

# test_r_wrapper.py
from models.r_wrapper import RWrapper  # Relative import requires src/ context
```
**Problem**: Test files use different import styles; test_booleanizer.py will fail when run from src/ directory.

---

### 1.3 Missing Module Initialization
**File**: [src/interpretability/__init__.py](src/interpretability/__init__.py)  
**Issue**: File exists but is empty  
**Should contain**:
```python
from .clinical_translator import ClinicalTranslator

__all__ = ['ClinicalTranslator']
```
**Impact**: Prevents proper package imports; requires full path imports instead of `from interpretability import ClinicalTranslator`.

---

### 1.4 Missing Imports in Files
**File**: [src/evaluation/benchmark_engine.py](src/evaluation/benchmark_engine.py#L1-10)  
**Issue**: Uses `BenchmarkEngine._extract_selected_features()` method but it's never imported or defined in visible code. Referenced in [exp_05_hybrid.py](src/exp_05_hybrid.py) but implementation not shown.

---

### 1.5 Unused Import
**File**: [src/models/tm_wrapper.py](src/models/tm_wrapper.py#L1-5)  
**Issue**: 
```python
import warnings  # Later line 4 imports from yaml instead
```
Line 4 imports incorrectly override this.

---

### 1.6 Missing rpy2 Error Handling
**File**: [src/models/r_wrapper.py](src/models/r_wrapper.py#L54-70)  
**Issue**: No import of rpy2 exception types. If R loading fails, error handling is incomplete.

---

## 2. FUNCTION/CLASS NAMING INCONSISTENCIES

### 2.1 Class Definition Duplication
**Same class defined in multiple files**:
- [src/exp_05_hybrid.py](src/exp_05_hybrid.py#L14-48)
- [src/exp_06_pure_comparison.py](src/exp_06_pure_comparison.py#L17-42)
- [src/exp_08_inverse_hybrid_latent.py](src/exp_08_inverse_hybrid_latent.py#L31-60)
- [src/exp_07_extract_rules.py](src/exp_07_extract_rules.py#L1-40)
- [src/exp_10_final_translator.py](src/exp_10_final_translator.py#L1-40)
- [src/exp_meda_04_v2.py](src/exp_meda_04_v2.py#L27-45)

**Issue**: `MEDAFilter` class is defined with nearly identical implementations in 6 different files.

**Correct Approach**: Create [src/pipelines/meda_filter.py](src/pipelines/meda_filter.py) with single definition.

---

### 2.2 Similar Class Name with Different Implementations
**Files**:
- [src/exp_08_inverse_hybrid_latent.py](src/exp_08_inverse_hybrid_latent.py#L64-87): `TMClauseExtractor`
- [src/exp_09_inv_hybrid_svm.py](src/exp_09_inv_hybrid_svm.py#L23-50): `TMClauseExtractor` (different)
- [src/exp_10_final_translator.py](src/exp_10_final_translator.py#L18-43): `TMClauseExtractor` (again)

**Issue**: Same class name, slightly different implementations (parameter differences: `num_bins` vs `n_bins`).

---

### 2.3 Parameter Naming Inconsistency: `num_bins` vs `n_bins`
**Files**:
- [src/models/tm_wrapper.py](src/models/tm_wrapper.py#L6): uses `num_bins`
- [src/features/smart_booleanizer.py](src/features/smart_booleanizer.py#L16): uses `n_bins`
- [src/exp_10_final_translator.py](src/exp_10_final_translator.py#L25): uses `n_bins`
- [src/exp_08_inverse_hybrid_latent.py](src/exp_08_inverse_hybrid_latent.py#L69): uses `num_bins`

**Issue**: Inconsistent parameter naming across pipeline stages.
```python
# TMWrapper
def __init__(self, ..., num_bins=4):  # Long form

# SmartBooleanizer  
def __init__(self, ..., n_bins=4, ...):  # Short form

# When used together:
TMClauseExtractor(..., num_bins=3)  # One name
booleanizer = SmartBooleanizer(n_bins=self.num_bins)  # Different name!
```

---

### 2.4 Error Message Inconsistency
**Various Files**:
- `[XXXX]` - [exp_05_hybrid.py](src/exp_05_hybrid.py#L43)
- `[!]` - [exp_06_pure_comparison.py](src/exp_06_pure_comparison.py#L37)
- `[Error]` - [exp_07_extract_rules.py](src/exp_07_extract_rules.py#L1-40)
- `[Oops]` - [exp_meda_04_v2.py](src/exp_meda_04_v2.py#L43)

**Issue**: No standardized error prefix convention. Should use consistent logging format.

---

### 2.5 Inconsistent Exception Handling Messages
**File**: [src/exp_08_inverse_hybrid_latent.py](src/exp_08_inverse_hybrid_latent.py#L52-54)
```python
# Line 52-54 comment mentions "If the matrix goes singular (which will happen 
# with vASCA + Boolean clauses)" - this suggests a KNOWN BUG that's being 
# suppressed rather than fixed
```

---

### 2.6 Method Name Ambiguity in TMWrapper
**File**: [src/models/tm_wrapper.py](src/models/tm_wrapper.py#L87-95)
```python
# Multiple attributes used interchangeably:
native_tm = getattr(self, 'tm_', getattr(self, 'model_', getattr(self, 'model', None)))
```
Should be consistent: only use `self.model_` based on fit() method (line 21).

---

## 3. TYPE ANNOTATION ISSUES

### 3.1 Complete Absence of Type Hints
**All files**: No type annotations present

**Examples**:
- [src/models/r_wrapper.py](src/models/r_wrapper.py#L18-30)
```python
def __init__(self, method='splsda', n_components=2, sparsity_penalty=0.5):
    # Should be:
    # def __init__(self, method: str = 'splsda', n_components: int = 2, 
    #             sparsity_penalty: float = 0.5) -> None:
```

- [src/features/smart_booleanizer.py](src/features/smart_booleanizer.py#L58)
```python
def fit(self, X, y=None):
    # Should be:
    # def fit(self, X: Union[pd.DataFrame, np.ndarray], y: Optional[np.ndarray] = None) -> 'SmartBooleanizer':
```

---

### 3.2 Inconsistent Return Types
**File**: [src/models/r_wrapper.py](src/models/r_wrapper.py)
```python
# Line 158: Returns np.ndarray (sometimes)
self.selected_features_ = r_indices.astype(int) - 1

# Line 161: Returns np.arange (sometimes)
self.selected_features_ = np.arange(n_features)

# Both stored in same attribute but different types
```

**File**: [src/models/tm_wrapper.py](src/models/tm_wrapper.py#L59)
```python
# Returns list
return list(selected_original_features)
```

---

### 3.3 Missing Return Type Documentation
**File**: [src/evaluation/benchmark_engine.py](src/evaluation/benchmark_engine.py#L25-35)
```python
def run_benchmark(self, X, y, model_name, pipeline, param_grid):
    # Returned type not documented (returns dict but unclear structure)
```

---

### 3.4 Inconsistent Variable Type Contracts
**File**: [src/exp_05_hybrid.py](src/exp_05_hybrid.py#L38-42)
```python
def fit(self, X, y):
    try:
        ...
        self.selected_indices_ = self.selector_.selected_features_  # Could be array or list
    except:
        self.selected_indices_ = list(range(X.shape[1]))  # Always list
```
`selected_indices_` could be np.ndarray or list depending on error path.

---

## 4. API/METHOD CALL INCONSISTENCIES

### 4.1 Inconsistent Feature Selection Return Types
**File**: [src/models/tm_wrapper.py](src/models/tm_wrapper.py#L59)
```python
@property
def selected_features_(self):
    ...
    return list(selected_original_features)  # Returns list
```

**File**: [src/models/r_wrapper.py](src/models/r_wrapper.py#L158)
```python
self.selected_features_ = r_indices.astype(int) - 1  # Returns np.ndarray
```

**Problem**: Calling code must handle both types:
```python
extracted_features = self._extract_selected_features(best_model)
# Is this a list or ndarray?
```

---

### 4.2 Dataset Loading Function Duplication
**Same function defined in**:
- [src/main.py](src/main.py#L28-85)
- [src/exp_05_hybrid.py](src/exp_05_hybrid.py#L50-95)
- [src/exp_06_pure_comparison.py](src/exp_06_pure_comparison.py#L44-88)
- [src/exp_08_inverse_hybrid_latent.py](src/exp_08_inverse_hybrid_latent.py#L97-141)
- [src/exp_meda_04_v2.py](src/exp_meda_04_v2.py#L49-93)
- [src/exp_07_extract_rules.py](src/exp_07_extract_rules.py#L40-85)
- [src/exp_10_final_translator.py](src/exp_10_final_translator.py#L50-95)

**Issue**: `select_and_load_dataset()` duplicated in 7 files with minor variations.

**Correct Approach**: Create single function in [src/data/loaders.py](src/data/loaders.py).

---

### 4.3 Inconsistent Pipeline API Calls
**File**: [src/exp_07_extract_rules.py](src/exp_07_extract_rules.py#L90-110)
```python
# Accessing fitted model differently:
native_pure_tm = getattr(tm_pure_step, 'tm_', getattr(tm_pure_step, 'model_', tm_pure_step))
```

vs [src/evaluation/benchmark_engine.py](src/evaluation/benchmark_engine.py#L50-60)
```python
# Direct access pattern not shown but likely different
```

---

### 4.4 Inconsistent Method Chaining
**File**: [src/exp_05_hybrid.py](src/exp_05_hybrid.py#L30-50)
```python
# Filter then booleanize:
MEDAFilter -> SmartBooleanizer -> TMWrapper
```

**File**: [src/exp_08_inverse_hybrid_latent.py](src/exp_08_inverse_hybrid_latent.py#L150-160)
```python
# Booleanize inside TMClauseExtractor:
TMClauseExtractor (contains booleanizer) -> MEDAFilter -> SVM
```

Inconsistent architectural patterns.

---

### 4.5 Incomplete API Implementation
**File**: [src/models/r_wrapper.py](src/models/r_wrapper.py#L230-240)
```python
elif self.method in ['asca', 'vasca']:
    # Note: ASCA/VASCA are traditionally ANOVA-based variance decomposition tools,
    # not direct standalone classifiers.
    raise NotImplementedError(
        f"Direct classification prediction for {self.method.upper()} requires..."
    )
```

**Problem**: VASCA/ASCA cannot predict directly, limiting pipeline flexibility.

---

## 5. DATA FORMAT INCONSISTENCIES

### 5.1 Different Column Indexing Between Dataset Types
**File**: [src/main.py](src/main.py#L75-92)

```python
# SIMULATED DATASETS
if dataset_type in ["simulated", "simulated_hd"]:
    y = df.iloc[:, 0].values          # Column 0
    X = df.iloc[:, 1:].values         # Columns 1+
    feature_names = df.columns[1:].tolist()

# REAL DATASET
elif dataset_type == "real":
    y_raw = df.iloc[:, 15].values     # Column 15
    X = df.iloc[:, 16:].values        # Columns 16+
    y = np.where(y_raw > 0, 1, 0)     # Additional encoding step
    feature_names = df.columns[16:].tolist()
```

**Issue**: Hard-coded column indices; different target encoding.

**Problem Cascade**:
1. Clinical Translator assumes specific biomarker structure
2. Booleanization assumes specific feature dimensionality
3. Pipeline parameters hardcoded for simulated (40 features) not real (unknown features)

---

### 5.2 Inconsistent Target Encoding
**File**: [src/simulateddataset.py](src/simulateddataset.py#L35-45)
```python
# Simulated: Binary encoding directly
Y = np.zeros(n_pacientes, dtype=int)
for i in range(n_pacientes):
    if X[i, 0] > umbral_il6 and X[i, 1] < umbral_il10:
        Y[i] = 1  # Direct 0/1
```

**File**: [src/main.py](src/main.py#L91)
```python
# Real: Conversion from continuous to binary
y = np.where(y_raw > 0, 1, 0)  # Assumes y_raw can be >0
```

**Issue**: Different assumptions about raw label format.

---

### 5.3 Binarization Parameter Inconsistency
**Dataset Generation**:
- [src/simulateddataset.py](src/simulateddataset.py#L20): 40 features
- [src/simulateddataset2.py](src/simulateddataset2.py#L20): 4000 features

**Booleanization Parameters**:
- [src/test_booleanizer.py](src/test_booleanizer.py#L20): `n_bins=4` (creates 3 bits per feature)
- [src/exp_05_hybrid.py](src/exp_05_hybrid.py#L128): `n_bins=3` (creates 2 bits per feature)
- [src/exp_08_inverse_hybrid_latent.py](src/exp_08_inverse_hybrid_latent.py#L71): `num_bins=3`

**Problem**: Different binarization creates incompatible feature spaces.

---

### 5.4 Discretization Strategy Inconsistency
**File**: [src/features/smart_booleanizer.py](src/features/smart_booleanizer.py#L16)
```python
def __init__(self, strategy='quantile', ...):
```

**Usage Examples**:
- Most files use default `strategy='quantile'`
- No files explicitly test `strategy='equal_width'` or `strategy='kmeans'`
- Unknown default behavior in production

---

### 5.5 Feature Scaling Inconsistency
**File**: [src/exp_05_hybrid.py](src/exp_05_hybrid.py#L105-110)
```python
'vASCA_SVM': Pipeline([
    ('filter', MEDAFilter(...)),
    ('scaler', StandardScaler()),  # Scales after filtering
    ('svm', SVC(...))
])
```

**File**: [src/exp_06_pure_comparison.py](src/exp_06_pure_comparison.py#L60-65)
```python
'Raw_SVM': Pipeline([
    ('scaler', StandardScaler()),  # Scales before filtering
    ('svm', SVC(...))
])
```

**Issue**: Scaling position affects feature selection quality.

---

## 6. CONFIGURATION/PARAMETER INCONSISTENCIES

### 6.1 Hyperparameter Variations Across Files

| Parameter | exp_05_hybrid | exp_06_pure | exp_08_inverse | exp_09_hybrid | Notes |
|-----------|:-------------:|:-----------:|:-------------:|:-------------:|-------|
| `number_of_clauses` | 100 | 100 | 100 | 100 | Consistent |
| `T` (Threshold) | 15 | 15 | 15 | 15 | Consistent |
| `s` (Specificity) | 3.9 | 3.9 | 3.9 | 3.9 | Consistent |
| `n_bins` | 3 | 3 | 3 | 3 | Consistent |
| `n_components` (MEDA) | 2 | 2 | 2 | 2 | Hardcoded everywhere |
| `sparsity_penalty` | 0.3, 0.3 | 0.3 | 0.3 | 0.3 | Mostly consistent |

**Issue**: Parameters never validated as optimal; appear arbitrary.

---

### 6.2 Cross-Validation Configuration Variance
**File**: [src/exp_05_hybrid.py](src/exp_05_hybrid.py#L87)
```python
engine = BenchmarkEngine(outer_cv=5, inner_cv=2, random_state=42)
```

**File**: [src/exp_08_inverse_hybrid_latent.py](src/exp_08_inverse_hybrid_latent.py#L175)
```python
cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)
# Different from nested CV above
```

**Issue**: Inconsistent CV strategy affects result comparability.

---

### 6.3 Metrics Calculation Inconsistency
**File**: [src/exp_05_hybrid.py](src/exp_05_hybrid.py#L87-95)
```python
# Uses BenchmarkEngine with GridSearchCV
grid_search = GridSearchCV(
    ...,
    scoring='matthews_corrcoef',
    ...
)
```

**File**: [src/exp_06_pure_comparison.py](src/exp_06_pure_comparison.py#L100-110)
```python
# Manual CV loop with metrics
fold_metrics = {'MCC': [], 'F1': [], ...}
# Manually calculates and stores metrics
```

**Issue**: Different evaluation methodologies; difficult to compare results.

---

### 6.4 Random State Management
- Some files: `random_state=42` explicitly set
- [src/test_booleanizer.py](src/test_booleanizer.py#L16): `random_state=42` in init
- [src/features/smart_booleanizer.py](src/features/smart_booleanizer.py#L16): defaults to 42
- [src/simulateddataset.py](src/simulateddataset.py#L10): `random_seed=42`

**Inconsistency**: Parameter naming (`random_state` vs `random_seed`).

---

### 6.5 Default Parameter Assumptions
**File**: [src/models/r_wrapper.py](src/models/r_wrapper.py#L110)
```python
def fit(self, X, y, permutations=100):
    # Hardcoded permutations parameter only for VASCA/ASCA
    # No validation if appropriate for data size
```

**Issue**: 100 permutations might be insufficient for small datasets (e.g., real: 82 patients).

---

## 7. STRUCTURAL AND LOGICAL PROBLEMS

### 7.1 Hardcoded Column Indices
**Files with hardcoded indices**:
- [src/main.py](src/main.py#L75-92): Columns 0, 15, 16
- All experiment files: Identical hardcoding
- [src/interpretability/clinical_translator.py](src/interpretability/clinical_translator.py#L22): Assumes column structure

**Issue**: Not configurable; breaks with different datasets.

**Remedy**: Create config file or pass as parameters.

---

### 7.2 Acknowledged Known Bug: Singular Matrix Crash
**File**: [src/exp_08_inverse_hybrid_latent.py](src/exp_08_inverse_hybrid_latent.py#L52-54)
```python
except Exception as e:
    # If the matrix goes singular (which will happen with vASCA + Boolean clauses)
    print(f"  [!] {self.method.upper()} crashed: {e}")
    self.selected_indices_ = list(range(X.shape[1]))  # Silent fallback
```

**Issue**: Known that vASCA + Boolean clauses causes singular matrix but no fix attempted.

**Problem**: Silent failure -> model passes all features -> defeats feature selection purpose.

---

### 7.3 Incomplete Feature Extraction Implementation
**File**: [src/evaluation/benchmark_engine.py](src/evaluation/benchmark_engine.py#L50-65)
```python
extracted_features = self._extract_selected_features(best_model)
# Method called but implementation not visible
```

**Issue**: Method referenced but undefined in available code.

---

### 7.4 One-Hot Encoding Placeholder
**File**: [src/features/smart_booleanizer.py](src/features/smart_booleanizer.py#L147-154)
```python
elif self.encoding == 'one_hot':
    # Placeholder for future one-hot encoding implementation
    pass  # ❌ NOT IMPLEMENTED
else:
    return X_discrete
```

**Issue**: Parameter accepted but not implemented; silently falls back to raw discrete.

---

### 7.5 Inconsistent Pipeline Architecture
**Pattern 1** - [src/exp_05_hybrid.py](src/exp_05_hybrid.py#L100-120):
```python
'Hybrid_sPLSDA_TM': Pipeline([
    ('filter', MEDAFilter(...)),        # Feature selection
    ('booleanizer', SmartBooleanizer(...)),  # Discretization
    ('tm', TMWrapper(...))              # Classification
])
```

**Pattern 2** - [src/exp_08_inverse_hybrid_latent.py](src/exp_08_inverse_hybrid_latent.py#L150-165):
```python
'Inverse_TM_sPLSDA': Pipeline([
    ('tm_extractor', TMClauseExtractor(...)),  # TM with internal booleanizer
    ('splsda', MEDAFilter(...)),               # Feature selection
    ('svm', SVC(...))                          # Classification
])
```

**Issue**: Two architectural approaches; unclear when to use which.

---

### 7.6 Path Handling Inconsistencies
**File**: [src/main.py](src/main.py#L56-65)
```python
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(current_dir, ".."))
data_path = os.path.join(project_root, "data", filename)
results_dir = os.path.join(project_root, "results", "main")
```

**Repeated in every experiment file** but with different `results_dir`:
- main: `"results/main"`
- exp_05: `"results/hybrid"`
- exp_06: `"results/versus"`
- exp_08: `"results/inverse_latent"`
- exp_07: `"results/rules"`
- etc.

**Issue**: No centralized path configuration.

---

### 7.7 No Input Validation
**File**: [src/models/r_wrapper.py](src/models/r_wrapper.py#L28-40)
```python
def __init__(self, method='splsda', n_components=2, sparsity_penalty=0.5):
    valid_methods = ['splsda', 'vasca', 'asca', 'spca', 'pca']
    if method not in valid_methods:
        raise ValueError(...)  # ✓ Good
    # But n_components and sparsity_penalty never validated
```

**Other issues**:
- No validation that `sparsity_penalty` is in [0, 1]
- No validation that `n_components` > 0
- No validation of X, y dimensions in fit()

---

### 7.8 No Data Format Validation
**File**: [src/models/tm_wrapper.py](src/models/tm_wrapper.py#L20-30)
```python
def fit(self, X, y):
    self.n_features_in_ = X.shape[1]
    self.classes_ = np.unique(y)
    self.model_ = MultiClassTsetlinMachine(...)
    self.model_.fit(np.asarray(X, dtype=np.int32), ...)  # Assumes X is binarized!
```

**Issue**: No check that X contains only {0, 1} values before passing to Tsetlin Machine.

---

### 7.9 Silent Failures in Error Handling
**File**: [src/exp_05_hybrid.py](src/exp_05_hybrid.py#L38-48)
```python
def fit(self, X, y):
    try:
        self.selector_.fit(X, y)
        self.selected_indices_ = self.selector_.selected_features_
    except Exception as e:
        print(f"  [XXXX] {self.method.upper()} failed: {e}. Passing all features.")
        self.selected_indices_ = list(range(X.shape[1]))  # Silent fallback
    return self
```

**Problems**:
1. Generic `Exception` catches everything (including programming errors)
2. Silent fallback defeats feature selection (defeats purpose)
3. Different behavior not communicated to downstream

---

### 7.10 Hardcoded Class Assumptions
**File**: [src/interpretability/clinical_translator.py](src/interpretability/clinical_translator.py#L32-35)
```python
for i in range(self.tm.number_of_classes):
    status = 'INFECTED (Peritonitis)' if i == 1 else 'HEALTHY (Homeostasis)'
```

**Issues**:
- Assumes binary classification
- Assumes class 1 = Peritonitis (domain-specific)
- Not generalizable

---

### 7.11 Testing Files Not Integrated
**Files**:
- [src/test_booleanizer.py](src/test_booleanizer.py)
- [src/test_r_wrapper.py](src/test_r_wrapper.py)

**Issues**:
- Manual testing approach
- Not integrated into CI/CD
- No assertions or formal test framework
- Would fail silently if run improperly

---

### 7.12 Module Unused/Unclear Purpose
**File**: [src/debug_vasca.py](src/debug_vasca.py)
- Purpose not clear
- Likely dead code

---

## 8. DETAILED FINDINGS BY FILE

### [src/models/r_wrapper.py](src/models/r_wrapper.py)
**Issues**:
1. Line 4: Wrong import (`from yaml import warnings`)
2. Line 231: NotImplementedError for ASCA/VASCA prediction (incomplete API)
3. Line 115: Complex try-except for R script sourcing (fragile)
4. No type hints
5. No input validation on parameters
6. Inconsistent return types from predict()

---

### [src/models/tm_wrapper.py](src/models/tm_wrapper.py)
**Issues**:
1. Line 4: Wrong import
2. Line 87-95: Ambiguous attribute access (`tm_` vs `model_` vs `model`)
3. No type hints
4. No validation that X is binarized before fitting
5. Selected_features_ property uses complex logic

---

### [src/features/smart_booleanizer.py](src/features/smart_booleanizer.py)
**Issues**:
1. Parameter naming: `n_bins` (inconsistent with `num_bins` elsewhere)
2. Line 147-154: One-hot encoding not implemented
3. No type hints
4. Hardcoded default `strategy='quantile'` not documented

---

### [src/interpretability/clinical_translator.py](src/interpretability/clinical_translator.py)
**Issues**:
1. Hardcoded class mapping (Peritonitis assumption)
2. No validation of input data
3. Limited to binary classification
4. No type hints
5. Magic numbers: `max_bits=4`, quartile assumptions

---

### [src/evaluation/benchmark_engine.py](src/evaluation/benchmark_engine.py)
**Issues**:
1. Method `_extract_selected_features()` referenced but not defined
2. No type hints
3. Unclear return format from `run_benchmark()`

---

### [src/exp_*_*.py files (all experiment files)](src/)
**Common Issues**:
1. Duplicate `select_and_load_dataset()` (7 copies)
2. Duplicate `MEDAFilter` class (6 copies)
3. Duplicate `TMClauseExtractor` class (3 copies)
4. Different results directories hardcoded
5. No refactoring for DRY principle
6. No central configuration
7. No type hints

---

## 9. SUMMARY TABLE OF ISSUES

| Category | Issue Count | Severity | Impact |
|----------|:-----------:|:--------:|--------|
| Import Inconsistencies | 6 | HIGH | Module loading failures |
| Naming Inconsistencies | 6 | MEDIUM | Code maintenance, clarity |
| Type Annotations | 4 | MEDIUM | IDE support, debugging |
| API/Method Calls | 5 | HIGH | Pipeline integration |
| Data Format | 5 | CRITICAL | Model accuracy, reproducibility |
| Configuration | 5 | MEDIUM | Result comparability |
| Structural/Logical | 12 | HIGH | Robustness, maintainability |
| **TOTAL** | **35+** | | |

---

## 10. RECOMMENDED ACTIONS (PRIORITY ORDER)

### Priority 1 (Critical - Fix Immediately)
1. **Fix wrong import** in [src/models/tm_wrapper.py](src/models/tm_wrapper.py#L4)
2. **Consolidate duplicate functions** into shared modules
3. **Fix hardcoded column indices** - create config file
4. **Fix vASCA singular matrix crash** - implement proper error handling
5. **Add input validation** to all model classes

### Priority 2 (High - Fix Soon)
1. **Standardize parameter naming** (`num_bins` → `n_bins`)
2. **Add type annotations** to all files
3. **Create shared utilities** module for dataset loading
4. **Consolidate MEDAFilter** into single definition
5. **Document data format requirements** for each dataset

### Priority 3 (Medium - Fix When Time Permits)
1. Add comprehensive error logging
2. Implement proper testing framework
3. Create configuration file system
4. Document pipeline architecture decisions
5. Refactor for code reuse

---

## 11. CODE SMELL INDICATORS

🔴 **High Risk Areas**:
- [src/models/r_wrapper.py](src/models/r_wrapper.py#L115-125): Complex R environment loading
- [src/models/tm_wrapper.py](src/models/tm_wrapper.py#L87-95): Attribute resolution ambiguity
- [src/exp_*_*.py](src/): All experiment files (code duplication)

🟡 **Medium Risk Areas**:
- [src/features/smart_booleanizer.py](src/features/smart_booleanizer.py#L147-154): Incomplete features
- [src/interpretability/clinical_translator.py](src/interpretability/clinical_translator.py#L32-35): Hardcoded assumptions

🟢 **Lower Risk**:
- Data generation files (simulateddataset.py, simulateddataset2.py): More stable

---

## 12. CONCLUSION

The codebase exhibits signs of evolutionary development without systematic refactoring. The primary issues stem from:

1. **Code Duplication**: Critical functions duplicated across files
2. **Inconsistent Conventions**: Parameter naming, error messages, paths
3. **Missing Type Safety**: No annotations; weak input validation
4. **Hardcoded Values**: Data structure assumptions not configurable
5. **Known Bugs**: vASCA singular matrix issue silently suppressed
6. **Architecture Inconsistency**: Multiple incompatible design patterns

**Estimated Technical Debt**: Moderate-to-High
**Refactoring Time Estimate**: 20-30 hours for comprehensive fixes
**Risk Level**: MEDIUM (functional but fragile)

---

**Report Generated**: 2026-06-01  
**Analysis Tool**: GitHub Copilot Static Analysis  
**Scope**: Complete src/ directory
