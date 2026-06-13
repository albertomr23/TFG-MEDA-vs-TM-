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
│
├── data/                              # Dataset files
│   ├── dataset_simulado_3000.xlsx     # Simulated: 3000 patients, 40 biomarkers
│   ├── dataset_simulado2.xlsx         # High-dim: 50 patients, 4000 features
│   └── dataset_real.xlsx              # Clinical: 82 patients, real biomarkers
|
├── src/                               # Main source code
│   ├── main.py                        # Global Orchestrator & CLI entry point
│   │
│   ├── exp_01_noise.py                # Exp 1: Robustness under Gaussian noise
│   ├── exp_02_bool.py                 # Exp 2: Booleanizer resolution impact
│   ├── exp_03_meda.py                 # Exp 3: Pure MEDA baseline (LR vs SVM)
│   ├── exp_04_versus.py               # Exp 4: The Ultimate Clash (TM vs MEDA)
│   ├── exp_05_hybrid.py               # Exp 5: Forward Hybridization (MEDA -> TM)
│   ├── exp_06_extract_rules.py        # Exp 6: Comparative XAI Rule Extraction
│   ├── exp_07_inverse_hybrid_latent.py # Exp 7: Latent Collapse (TM -> sPLSDA/vASCA)
│   ├── exp_08_inv_hybrid_svm.py       # Exp 8: Logic-to-Geometry (TM -> Linear SVM)
│   └── exp_09_final_translator.py     # Exp 9: Clinical translation & White-Box XAI
│   |
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
│   ├── pipelines/                     # Pipelines modules
│   │   └── meda_filter.py             # MEDA filter used in exps
|
│   ├── utils/                         # Common scripts used in experiments
│   │   └── data_loader.py             # Cross-validation & metrics computation
|
│   ├── pre-tests/                     # Test created for debugging
│   │   └── ...
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
python/python3 src/main.py
```

---

## 🚀 Quick Start

### Interactive Menu (Recommended)
```bash
python/python3 src/main.py
```

This launches an interactive menu where you can:
1. Select dataset (simulated 3K, real clinical, high-dim 4K)
2. Choose experiment (noise robustness, pure comparison, hybrid, etc.)
3. Automatically generate visualizations and metrics

### Run Specific Experiment
If you prefer to bypass the interactive menu, you can execute modules directly:

```bash
# Pure MEDA baseline evaluation
python/python3 src/exp_03_meda.py

# Head-to-Head: Pure Logic vs Pure Algebra
python/python3 src/exp_04_versus.py

# Novel Logic-to-Geometry Architecture
python/python3 src/exp_08_inv_hybrid_svm.py

# Clinical rule extraction & interpretation
python/python3 src/exp_09_final_translator.py
```

---

## 📊 Core Experiments

### Experiment 1: Noise Stress Test (`exp_01_noise.py`)
- Tests model stability under Gaussian noise (increasing noisy features)
- Metric: MCC degradation curve and Jaccard Stability
- Purpose: Assess structural robustness against biological noise.

### Experiment 2: Booleanizer Resolution Impact (`exp_02_bool.py`)
- Evaluates the state-space explosion when increasing discretization bins.
- Purpose: Find the optimal balance between mathematical resolution and combinatorial overfitting.

### Experiment 3: Pure MEDA Evaluation (`exp_03_meda.py`)
- Establishes the classical geometric baseline (sPLS-DA, PCA, ASCA, vASCA).
- Classifiers: Logistic Regression vs. Non-linear SVM.
- Outputs: Multi-panel ROC curves and topological decision boundaries.

### Experiment 4: The Ultimate Clash (`exp_04_versus.py`)
- Head-to-head paradigm comparison: Pure Logic (TM) vs. Pure Algebra (vASCA+SVM).
- Outputs: Radar charts, execution efficiency, and McNemar Agreement matrices proving algorithmic orthogonality.

### Experiment 5: Forward Hybridization (`exp_05_hybrid.py`)
- Tests conventional cascade: Algebraic Filter → Logical Classifier.
- Discovers the **"Algebraic Bottleneck"**, proving continuous filters destroy epistatic vocabulary.

### Experiment 6: Comparative Rule Extraction (`exp_06_extract_rules.py`)
- White-Box XAI audit using the custom `ClinicalTranslator`.
- Physically demonstrates how upstream MEDA filters force downstream TM to hallucinate "Spaghetti Rules".

### Experiment 7: Latent Collapse (`exp_07_inverse_hybrid_latent.py`)
- Tests the Inverse pipeline: TM clauses → sPLS-DA/vASCA.
- Proves the "Zero-Variance Crash": continuous models cannot parse discrete Hamming spaces.
- Discovers the formation of **"Logical Islands"**.

### Experiment 8: Logic-to-Geometry Pipeline (`exp_08_inv_hybrid_svm.py`)
- The definitive architecture: TM (Epistatic Extractor) → Linear SVM (Margin Maximization).
- Solves the clinical entangled topology without suffering the curse of dimensionality.

### Experiment 9: Final Clinical Translation (`exp_09_final_translator.py`)
- Maps geometric SVM weights back to raw boolean logical clauses.
- Outputs: Actionable, human-readable immunological rules detailing the non-linear cytokine collapse in Peritonitis.
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
**Email:** e.amunuerar@go.ugr.es 

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

- **Thesis Document**: Included in the repository
- **Presentation Slides**: Included in the repository(To be added)
- **Supplementary Data**: Results directory
- **Code Documentation**: See inline comments and docstrings

---

**Last Updated:** June 13, 2026  
**Repository Status:** Active Development  
**Thesis Status:** Nearly finished
