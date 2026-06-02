# Codebase Issues - Quick Reference Guide

## Critical Issues (Fix Immediately)

### 1. Wrong Import in tm_wrapper.py
```python
# ❌ Line 4 in src/models/tm_wrapper.py
from yaml import warnings

# ✅ Should be:
import warnings
```
**Impact**: Breaks warnings functionality across Tsetlin Machine operations.

---

### 2. Silent Pipeline Failures
**Location**: [src/exp_08_inverse_hybrid_latent.py](src/exp_08_inverse_hybrid_latent.py#L52-54), [src/exp_05_hybrid.py](src/exp_05_hybrid.py#L42-48)

```python
except Exception as e:
    print(f"  [!] {self.method.upper()} crashed: {e}. Passing all features.")
    self.selected_indices_ = list(range(X.shape[1]))  # ❌ Silent fallback
```

**Problem**: When vASCA crashes (known singular matrix issue), silently passes all features, defeating feature selection.

---

### 3. Hardcoded Column Indices (Not Configurable)
**Files Affected**: All 7 experiment files + main.py

```python
# For simulated data:
y = df.iloc[:, 0].values
X = df.iloc[:, 1:].values

# For real data:
y_raw = df.iloc[:, 15].values
X = df.iloc[:, 16:].values
```

**Problem**: Cannot use with different datasets; breaks easily.

---

### 4. Massive Code Duplication

**`select_and_load_dataset()` duplicated 7 times**:
- src/main.py
- src/exp_05_hybrid.py
- src/exp_06_pure_comparison.py
- src/exp_08_inverse_hybrid_latent.py
- src/exp_meda_04_v2.py
- src/exp_07_extract_rules.py
- src/exp_10_final_translator.py

**`MEDAFilter` class duplicated 6 times** (slightly different implementations)

**`TMClauseExtractor` class duplicated 3 times**

**Impact**: Any bug fix requires changes in 6+ places; maintenance nightmare.

---

## High Priority Issues

### Parameter Naming Inconsistency
```python
# ❌ Mixed usage:
TMWrapper(..., num_bins=4)              # Long form
SmartBooleanizer(..., n_bins=4)         # Short form
TMClauseExtractor(..., num_bins=3)      # Mixed
```

**Affects**: exp_05, exp_06, exp_08, exp_09, exp_10

---

### Incomplete API Implementations

**File**: [src/models/r_wrapper.py](src/models/r_wrapper.py#L230-240)
```python
elif self.method in ['asca', 'vasca']:
    raise NotImplementedError(...)  # ❌ Cannot predict directly
```

**File**: [src/features/smart_booleanizer.py](src/features/smart_booleanizer.py#L147-154)
```python
elif self.encoding == 'one_hot':
    # Placeholder for future one-hot encoding implementation
    pass  # ❌ NOT IMPLEMENTED
```

---

### No Input Validation

```python
# ✓ Validates method
if method not in valid_methods:
    raise ValueError(...)

# ❌ But doesn't validate:
# - Is n_components > 0?
# - Is sparsity_penalty in [0, 1]?
# - Is X binarized (contains only {0, 1})?
# - Are y values valid?
```

---

## Medium Priority Issues

### No Type Annotations
**All files**: Missing type hints on functions and methods.

```python
# ❌ Current:
def fit(self, X, y):
    ...
    
# ✅ Should be:
def fit(self, X: Union[np.ndarray, pd.DataFrame], y: np.ndarray) -> 'ClassName':
    ...
```

---

### Inconsistent Error Message Format
```python
[XXXX]  # exp_05
[!]     # exp_06
[Error] # exp_07
[Oops]  # exp_meda_04
```

**Should use**: Consistent logging format across codebase.

---

### Return Type Inconsistency

```python
# TMWrapper (returns list):
@property
def selected_features_(self):
    return list(selected_original_features)

# RWrapper (returns ndarray):
self.selected_features_ = r_indices.astype(int) - 1

# Problem: Same attribute, different types → downstream code must handle both
```

---

### Cross-Validation Strategy Inconsistency

```python
# exp_05_hybrid.py:
BenchmarkEngine(outer_cv=5, inner_cv=2)  # Nested CV

# exp_06_pure_comparison.py:
cv = StratifiedKFold(n_splits=5)  # Simple CV

# exp_08_inverse_hybrid_latent.py:
cv = StratifiedKFold(n_splits=5)  # Simple CV
```

**Impact**: Results not directly comparable.

---

## Data Format Issues

### Different Discretization Across Experiments
```python
# test_booleanizer.py:
SmartBooleanizer(strategy='quantile', n_bins=4)  # Creates 3 bits/feature

# exp_05_hybrid.py:
SmartBooleanizer(n_bins=3)  # Creates 2 bits/feature

# exp_08_inverse_hybrid_latent.py:
SmartBooleanizer(n_bins=3)  # Creates 2 bits/feature
```

**Impact**: Different feature spaces; results not comparable.

---

### Scaling Position Affects Results
```python
# exp_05_hybrid.py - Scale AFTER filtering:
Pipeline([
    ('filter', MEDAFilter(...)),
    ('scaler', StandardScaler()),
    ('svm', SVC(...))
])

# exp_06_pure_comparison.py - Scale BEFORE:
Pipeline([
    ('scaler', StandardScaler()),
    ('svm', SVC(...))
])
```

---

## Testing Issues

### Test Files Not Integrated
- [src/test_booleanizer.py](src/test_booleanizer.py)
- [src/test_r_wrapper.py](src/test_r_wrapper.py)

**Problems**:
- Manual testing approach
- No assertions
- Not integrated into CI/CD
- Would fail silently if run incorrectly
- Results not validated against expected behavior

---

## Architecture Issues

### Inconsistent Pipeline Patterns

**Pattern 1** (Forward):
```
Algebraic Filter → Booleanize → TM
(exp_05_hybrid.py)
```

**Pattern 2** (Inverse):
```
TM (with internal booleanization) → Algebraic Filter → SVM
(exp_08_inverse_hybrid_latent.py)
```

**Problem**: Two incompatible approaches; unclear when to use which.

---

### Missing Configuration System
```python
# Current approach (hardcoded everywhere):
results_dir = os.path.join(project_root, "results", "hybrid")
os.makedirs(results_dir, exist_ok=True)

# Each file has different path:
"results/main"          # main.py
"results/hybrid"        # exp_05
"results/versus"        # exp_06
"results/inverse_latent" # exp_08
"results/rules"         # exp_07
```

---

## Quick Fix Checklist

```
CRITICAL:
☐ Fix: src/models/tm_wrapper.py line 4 (yaml import)
☐ Fix: Hardcoded column indices (15, 16 for real data)
☐ Fix: vASCA singular matrix silent fallback
☐ Extract: select_and_load_dataset() to shared module
☐ Extract: MEDAFilter to shared module

HIGH:
☐ Standardize: num_bins → n_bins naming
☐ Implement: Input validation in all __init__ methods
☐ Complete: ASCA/VASCA predict implementation
☐ Add: Type hints to all functions
☐ Fix: Return type consistency for selected_features_

MEDIUM:
☐ Create: Configuration file system
☐ Implement: One-hot encoding in SmartBooleanizer
☐ Standardize: Error message format
☐ Integrate: test_*.py files into CI/CD
☐ Document: Pipeline architecture decisions

LOW:
☐ Remove: Dead code (debug_vasca.py?)
☐ Clean: Inconsistent logging messages
☐ Review: Random state seeding across files
```

---

## Files Needing Immediate Attention

| File | Issues | Priority |
|------|--------|----------|
| [src/models/tm_wrapper.py](src/models/tm_wrapper.py) | Wrong import, attribute ambiguity | CRITICAL |
| [src/models/r_wrapper.py](src/models/r_wrapper.py) | Incomplete ASCA/VASCA predict | HIGH |
| [src/exp_05_hybrid.py](src/exp_05_hybrid.py) | Silent failures, duplication | HIGH |
| [src/exp_06_pure_comparison.py](src/exp_06_pure_comparison.py) | Duplication, scaling issue | HIGH |
| [src/exp_08_inverse_hybrid_latent.py](src/exp_08_inverse_hybrid_latent.py) | Duplication, singular matrix | HIGH |
| [src/features/smart_booleanizer.py](src/features/smart_booleanizer.py) | One-hot not implemented | MEDIUM |
| [src/main.py](src/main.py) | Hardcoded column indices | HIGH |

---

## Related Documentation
- Full analysis: [CODEBASE_ANALYSIS_REPORT.md](./CODEBASE_ANALYSIS_REPORT.md)
- Session notes: [/memories/session/codebase_analysis.md](/memories/session/codebase_analysis.md)
