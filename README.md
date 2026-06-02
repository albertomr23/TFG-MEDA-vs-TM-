# AI for Tsetlin Machines: A Comparative Study of MEDA Methods

**Bachelor Thesis in Artificial Intelligence**  
*Double Degree in Computer Engineering and Mathematics*  
University of Granada (Universidad de Granada - UGR)

**Author:** Alberto Munuera Ramos  
**Academic Year:** 2025-2026

---

## 📋 Abstract

This thesis presents a comprehensive comparative analysis of Multivariate Exploratory Data Analysis (MEDA) methods against **Tsetlin Machines (TM)** for classification tasks in biomedical data. The study evaluates multiple architectures combining MEDA techniques (sPLS-DA, sPCA, ASCA, vASCA) with classical machine learning and novel inverse hybrid approaches using TM clause embeddings as features for downstream algebraic models.

### Key Contributions:
- Systematic performance comparison of MEDA methods vs. pure TM implementations
- Novel **Inverse Hybrid Architecture**: TM clause activation ↔ sPLSDA/vASCA pipeline
- Analysis on both simulated (3000 samples, 40 features) and real clinical datasets (82 samples, multi-biomarker)
- Statistical robustness assessment across high-dimensional scenarios (4000 features)
- Integration of clinical interpretability through epistatic rule extraction

---

## 🎯 Project Overview

This repository implements a multi-faceted machine learning pipeline comparing traditional MEDA-based dimensionality reduction with emerging Tsetlin Machine-based feature learning. The project investigates whether discrete, interpretable boolean logic (TM) can compete with or exceed continuous algebraic methods (MEDA) in medical classification tasks.

### Primary Research Questions:
1. **Performance**: Can TM achieve competitive accuracy compared to MEDA methods?
2. **Interpretability**: Do TM clause activations provide more interpretable biomarker relationships?
3. **Scalability**: How do these methods perform under the curse of dimensionality?
4. **Hybrid Potential**: Can combining TM feature extraction with algebraic models improve both accuracy and interpretability?

---

## 📂 Directory Structure

```
TFG-MEDA-vs-TM/
├── README.md                           # This file
├── requirements.txt                    # Python dependencies
├── CODEBASE_ANALYSIS_REPORT.md        # Detailed code quality analysis
├── ISSUES_QUICK_REFERENCE.md          # Quick reference for identified issues
├── RECOMMENDED_FIXES.md               # Proposed solutions and refactoring steps
│
├── data/                              # Dataset files
│   ├── dataset_simulado_3000.xlsx     # Simulated: 3000 patients, 40 biomarkers
│   ├── dataset_simulado2.xlsx         # High-dim: 50 patients, 4000 features
│   └── dataset_real.xlsx              # Clinical: 82 patients, real biomarkers
│
├── src/                               # Main source code
│   ├── main.py                        # Entry point (interactive menu)
│   │
│   ├── exp_*.py                       # Experiment scripts
│   │   ├── exp_noise_01.py           # Robustness under Gaussian noise
│   │   ├── exp_bool_02.py            # Pure TM with boolean features
│   │   ├── exp_interpretability_03.py # Feature importance analysis
│   │   ├── exp_meda_04_v2.py         # Baseline MEDA methods (sPLS, sPCA, ASCA, vASCA)
│   │   ├── exp_05_hybrid.py          # Hybrid TM ↔ MEDA combinations
│   │   ├── exp_06_pure_comparison.py # Categorical comparison: SVM vs TM
│   │   ├── exp_07_extract_rules.py   # TM clause rule extraction
│   │   ├── exp_08_inverse_hybrid_latent.py   # Novel: TM→sPLSDA/vASCA→SVM
│   │   ├── exp_09_inv_hybrid_svm.py  # Variant: TM→SVM pipeline
│   │   └── exp_10_final_translator.py # Clinical translation & interpretability
│   │
│   ├── models/                        # Core ML wrappers
│   │   ├── tm_wrapper.py             # Tsetlin Machine scikit-learn compatible wrapper
│   │   ├── r_wrapper.py              # R interface for MEDA (rpy2 bridge)
│   │   └── r_scripts/                # R implementations
│   │       ├── vasca.R              # vASCA (variable selection via Tsetlin)
│   │       ├── asca.R               # ASCA (Analysis of Structures)
│   │       ├── parglmVS.R           # Parallel GLM for variable selection
│   │       ├── pcaEig.R             # PCA via eigendecomposition
│   │       └── preprocess2D.R       # Data preprocessing utilities
│   │
│   ├── features/                      # Feature engineering
│   │   └── smart_booleanizer.py      # Adaptive boolean encoding (binning strategy)
│   │
│   ├── interpretability/              # Interpretability modules
│   │   ├── __init__.py
│   │   └── clinical_translator.py     # Convert TM logic → clinical rules
│   │
│   ├── evaluation/                    # Evaluation utilities
│   │   └── benchmark_engine.py        # Cross-validation & metrics computation
│   │
│   ├── test_*.py                      # Unit tests
│   ├── debug_*.py                     # Debugging scripts
│   └── simulated*.py                  # Dataset generation utilities
│
├── notebooks/                         # Jupyter notebooks (exploratory analysis)
│
└── results/                           # Output artifacts
    ├── meda_puro/                    # Pure MEDA results
    ├── hybrid/                       # Hybrid architecture results
    ├── inverse_hybrid/               # Inverse hybrid outputs
    ├── inverse_latent/               # Latent space collapse analysis
    ├── meda_tournament/              # Method comparison tournament
    ├── rules/                        # Extracted epistatic rules
    │   ├── [real]_comparative_clinical_rules.txt
    │   ├── [simulated]_comparative_clinical_rules.txt
    │   └── [simulated_hd]_comparative_clinical_rules.txt
    ├── versus/                       # Head-to-head comparisons
    └── final_translation/            # Final clinical interpretability report
```

---

## 🔧 Installation & Setup

### Prerequisites
- Python 3.8+
- R 4.0+ (for MEDA methods via rpy2)
- pip or conda

### Step 1: Clone Repository
```bash
git clone https://github.com/albertomr23/TFG-MEDA-vs-TM.git
cd TFG-MEDA-vs-TM
```

### Step 2: Install Python Dependencies
```bash
pip install -r requirements.txt
```

### Step 3: Install R Dependencies (Optional)
If you plan to use MEDA methods (sPLSDA, vASCA, ASCA):

```r
# In R console:
install.packages(c("pls", "mvtnorm", "ASCA", "rPy2"))
install.packages("devtools")
devtools::install_github("user/R-package-name")  # If needed
```

### Step 4: Verify Installation
```bash
python src/main.py
```

---

## 🚀 Quick Start

### Interactive Menu (Recommended)
```bash
python src/main.py
```

This launches an interactive menu where you can:
1. Select dataset (simulated 3K, real clinical, high-dim 4K)
2. Choose experiment (noise robustness, pure comparison, hybrid, etc.)
3. Automatically generate visualizations and metrics

### Run Specific Experiment
```bash
# Pure TM comparison
python src/exp_06_pure_comparison.py

# Novel inverse hybrid architecture
python src/exp_08_inverse_hybrid_latent.py

# Clinical rule extraction & interpretation
python src/exp_10_final_translator.py

# MEDA baseline methods
python src/exp_meda_04_v2.py
```

---

## 📊 Core Experiments

### Experiment 1: Noise Robustness (`exp_noise_01.py`)
- Tests model stability under Gaussian noise (σ = 0.1 to 1.0)
- Metric: MCC degradation curve
- Purpose: Assess real-world robustness

### Experiment 2: Pure TM Analysis (`exp_bool_02.py`)
- Evaluates Tsetlin Machine on raw boolean features
- Baseline for hybrid comparisons
- Outputs: Clause importance rankings

### Experiment 3: Feature Interpretability (`exp_interpretability_03.py`)
- Extracts feature importance from TM clauses
- Compares with MEDA variable selection
- Outputs: Feature ranking heatmaps

### Experiment 4: MEDA Baseline (`exp_meda_04_v2.py`)
- Implements sPLS-DA, sPCA, ASCA, vASCA methods
- Cross-validation with MCC & F1-Score metrics
- Outputs: Comparative performance visualizations

### Experiment 5: Hybrid Architectures (`exp_05_hybrid.py`)
- Tests combinations: TM + MEDA + SVM
- Evaluates synergistic potential
- Outputs: Architecture comparison charts

### Experiment 6: Pure Comparison (`exp_06_pure_comparison.py`)
- Head-to-head: SVM vs. TM vs. Hybrid
- Different kernel/clause configurations
- Outputs: Tournament-style rankings

### Experiment 7: Rule Extraction (`exp_07_extract_rules.py`)
- Converts TM clauses into human-readable logic
- Format: "IF (biomarker_i AND biomarker_j) THEN pathology"
- Purpose: Clinical interpretability

### Experiment 8: Inverse Hybrid (Novel) (`exp_08_inverse_hybrid_latent.py`)
- **Key Innovation**: TM as upstream feature extractor
- Pipeline: Raw Biomarkers → **TM Clauses** → sPLSDA/vASCA → SVM
- Tests latent space collapse hypothesis
- Outputs: Topological proof via PCA projections

### Experiment 9: Inverse SVM Variant (`exp_09_inv_hybrid_svm.py`)
- Simplified inverse: TM → SVM directly
- Faster execution, comparable performance

### Experiment 10: Clinical Translation (`exp_10_final_translator.py`)
- Integrates all findings for clinical use
- Outputs: Epistatic rule sets + confidence scores
- Format: Ready for clinical validation studies

---

## 📈 Key Metrics

| Metric | Formula | Purpose |
|--------|---------|---------|
| **MCC** (Matthews Correlation Coefficient) | $\frac{TP \cdot TN - FP \cdot FN}{\sqrt{(TP+FP)(TP+FN)(TN+FP)(TN+FN)}}$ | Balanced accuracy for imbalanced datasets |
| **F1-Score** | $\frac{2 \cdot TP}{2 \cdot TP + FP + FN}$ | Harmonic mean of precision & recall |
| **Specificity** | $\frac{TN}{TN + FP}$ | True negative rate (clinical relevance) |
| **AUC-ROC** | Area under ROC curve | Overall discrimination ability |

---

## 🧬 Technical Details

### Tsetlin Machine Architecture
- **Clauses**: Boolean feature combinations (AND gates)
- **Voting**: Weighted clause activations → classification
- **Learning**: Feedback-driven clause refinement via sTiG (Self-Timed Gates)
- **Interpretability**: Each clause = explicit AND of binary features

### MEDA Methods
- **sPLS-DA**: Sparse Partial Least Squares Discriminant Analysis
- **sPCA**: Sparse Principal Component Analysis
- **ASCA**: ANOVA-Simultaneous Component Analysis
- **vASCA**: Variable-selection ASCA

### Smart Booleanizer
Adaptive binning strategy:
- Equal-width vs. equal-frequency bins
- Feature-specific optimization
- Handles continuous → boolean conversion

### R Integration (rpy2)
- R methods (MEDA, statistical tests) called from Python
- Automatic data marshaling
- Error handling with fallbacks

---

## ⚠️ Known Issues & Code Quality Notes

The codebase has evolved through multiple experimental iterations. Several structural improvements are documented in:

- **[CODEBASE_ANALYSIS_REPORT.md](CODEBASE_ANALYSIS_REPORT.md)** — Comprehensive analysis with 35+ identified issues
- **[ISSUES_QUICK_REFERENCE.md](ISSUES_QUICK_REFERENCE.md)** — Priority checklist
- **[RECOMMENDED_FIXES.md](RECOMMENDED_FIXES.md)** — Concrete refactoring solutions

### Critical Issues (Priority Fixes):
1. ❌ Wrong import in `tm_wrapper.py` (line 4): `from yaml import warnings` → should be `import warnings`
2. ⚠️ Code duplication: `MEDAFilter` class defined 6x across exp files
3. ⚠️ Function duplication: `select_and_load_dataset()` repeated 7x
4. 🔧 Hardcoded column indices (0, 15, 16) make datasets brittle
5. 🔧 Silent vASCA failures (singular matrix) not properly caught

### Recommended Next Steps:
- **Short-term**: Fix imports and error handling (2-3 hours)
- **Medium-term**: Refactor common code into shared modules (3-4 hours)
- **Long-term**: Add type annotations & comprehensive unit tests (2-3 hours)

See [RECOMMENDED_FIXES.md](RECOMMENDED_FIXES.md) for detailed solutions.

---

## 📝 Dataset Specifications

### Simulated Dataset (3000 samples)
- **Size**: 3000 patients × 40 biomarkers
- **Target**: Binary classification (Healthy=0, Infected=1)
- **Structure**: Intentional epistatic relationships embedded
- **File**: `data/dataset_simulado_3000.xlsx`

### Real Clinical Dataset (82 samples)
- **Source**: Olga & Eberl peritonitis cohort
- **Size**: 82 patients × 15 clinical features + biomarker panel
- **Target**: Peritonitis presence (binary)
- **Biomarkers**: Columns 16+ (protein abundance measurements)
- **File**: `data/dataset_real.xlsx`

### High-Dimensional Dataset (50 samples)
- **Challenge**: Curse of dimensionality
- **Size**: 50 patients × 4000 features
- **Purpose**: Stress-test method robustness
- **Generation**: Synthetic via `simulateddataset2.py`
- **File**: `data/dataset_simulado2.xlsx`

---

## 🎓 Academic References

Key citations informing this thesis:
- **Tsetlin Machines**: Granmo, O. C. (2018). "The Tsetlin Machine"
- **MEDA**: Ferré, J. (2018). "A short introduction to multivariate exploratory data analysis"
- **sPLS-DA**: Lê Cao, K.-A. et al. (2011). "Sparse PLS discriminant analysis"
- **vASCA**: Smilde, A. K., et al. (2005). "ASCA with fixed effects"

---

## 📧 Contact & Collaboration

**Author:** Alberto Munuera Ramos  
**Institution:** University of Granada (UGR)  
**Program:** Double Degree in Computer Engineering & Mathematics  
**Email:** (contact information)  

For questions, suggestions, or collaboration opportunities related to this research, please reach out.

---

## 📄 License

This thesis project is provided as-is for educational and research purposes. 

**Note**: Some datasets (real clinical data) may have restricted usage due to privacy regulations. Ensure proper ethical approval before using real patient data.

---

## 🔬 Future Work

1. **Scalability**: Implement parallel cross-validation for high-dimensional datasets
2. **Deep Learning**: Compare with neural network-based feature extraction
3. **Clinical Validation**: Run prospective study with extracted TM rules
4. **Interpretability**: Develop interactive visualization tool for rule exploration
5. **Ensemble Methods**: Combine multiple TM+MEDA pipelines for robustness
6. **Real-Time Inference**: Deploy optimized TM model for clinical DSS

---

## 📚 Supplementary Materials

- **Thesis Document**: (PDF link when completed)
- **Presentation Slides**: (Slides on GitHub)
- **Supplementary Data**: (Results directory with visualizations)
- **Code Documentation**: See inline comments and docstrings

---

**Last Updated:** June 1, 2026  
**Repository Status:** Active Development  
**Thesis Status:** In Progress
