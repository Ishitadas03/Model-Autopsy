# Experimental Protocol: E001 — Robustness of Random Forest under Gaussian Noise

**Experiment ID:** `E001`  
**Experiment Title:** Empirical Characterization of Random Forest Classifier Robustness Under Additive Gaussian Feature Noise on the Iris Benchmark  
**Protocol Version:** 1.0.0  
**Parent Document:** [`docs/research/problem_statement.md`](file:///c:/Users/ishit/Model-Autopsy/docs/research/problem_statement.md)  
**Target Context:** B.Tech CSE-AIML Research Project & Empirical ML Robustness Foundation  
**Status:** Approved Specification  

---

## 1. Experiment ID and Title

- **Experiment Identifier:** `E001`
- **Formal Title:** Empirical Evaluation of Classification Performance Degradation and Failure Boundary Detection in a Random Forest Classifier Subjected to Controlled Additive Gaussian Input Noise on the Iris Dataset.
- **Protocol Category:** Tabular Baseline Stress-Testing Experiment (Phase 1 MVP).

---

## 2. Research Question

### Primary Research Question
> **"How does Gaussian input noise affect the Macro-F1 performance of a Random Forest classifier on the Iris dataset?"**

### Secondary Exploratory Questions
1. At what discrete noise severity level $s^*$ (if any within the tested range $s \in [0.00, 0.30]$) does the model's Macro-F1 score drop below the predefined reliability threshold of $0.80$?
2. Does performance degrade gracefully (approximately linear decay) or experience an abrupt transition (catastrophic cliff)?
3. Which specific class decision boundaries (e.g., *Iris setosa* vs. *Iris versicolor* vs. *Iris virginica*) exhibit the earliest confusion under increasing noise?
4. How consistent is the observed degradation trajectory across distinct pseudo-random number generator (PRNG) seed initializations?

---

## 3. Hypothesis and Rationale

### Scientific Hypotheses

- **Working Hypothesis ($H_1$):** Increasing the severity of additive Gaussian noise applied to test features will cause a monotonic decrease in the model's Macro-F1 score. Furthermore, classification error will disproportionately manifest as confusion between *Iris versicolor* and *Iris virginica* due to their overlapping feature space, whereas the linearly separable *Iris setosa* will remain relatively resilient at low-to-moderate noise severities ($s \le 0.15$).
- **Null Hypothesis ($H_0$):** Additive Gaussian noise within the severity range $s \in [0.00, 0.30]$ produces no statistically significant degradation in the Macro-F1 score of the Random Forest classifier relative to baseline performance ($s = 0.00$).

### Scientific Rationale
Tree-based ensemble architectures (such as Random Forests) construct orthogonal axis-aligned decision boundaries. Additive Gaussian perturbations displace test points across these boundaries. In regions where class margins are narrow (notably between *versicolor* and *virginica*), small feature shifts $\varepsilon_{ij}$ are hypothesized to cross partition thresholds, whereas classes with substantial geometric separation (*setosa*) require larger displacements to induce misclassification.

> **Methodological Note:** This hypothesis represents a testable scientific expectation. The protocol assumes neither the validation nor the refutation of $H_1$ prior to empirical execution and data collection.

---

## 4. Dataset Description

The experiment utilizes the canonical **Iris Flower Dataset** (Fisher, 1936; UCI Machine Learning Repository):

| Property | Value / Specification |
|---|---|
| **Dataset Name** | Iris Flower Dataset |
| **Total Instances ($N$)** | 150 |
| **Total Features ($D$)** | 4 continuous numerical features |
| **Feature 1 (`f0`)** | `sepal length (cm)` |
| **Feature 2 (`f1`)** | `sepal width (cm)` |
| **Feature 3 (`f2`)** | `petal length (cm)` |
| **Feature 4 (`f3`)** | `petal width (cm)` |
| **Target Variable ($Y$)** | Multi-class categorical (3 classes, balanced) |
| **Class 0 (`c0`)** | *Iris setosa* ($n = 50$, 33.33%) |
| **Class 1 (`c1`)** | *Iris versicolor* ($n = 50$, 33.33%) |
| **Class 2 (`c2`)** | *Iris virginica* ($n = 50$, 33.33%) |
| **Missing Values** | 0 (complete dataset) |

---

## 5. Dataset Validation and Preprocessing

Prior to execution, the data ingestion pipeline must execute the following deterministic validation checks:

```
┌────────────────────────────────────────────────────────────────────────┐
│                      DATA VALIDATION PIPELINE                          │
├────────────────────────────────────────────────────────────────────────┤
│ 1. Schema Check: Verify exactly 4 input features and 1 target column. │
│ 2. Nullity Check: Verify 0 null, NaN, or infinite values.              │
│ 3. Class Balance Check: Verify exactly 50 samples per class.           │
│ 4. Type Check: Cast features to float64, target to integer {0, 1, 2}.  │
└────────────────────────────────────────────────────────────────────────┘
```

### Preprocessing Strategy
- **Scaling / Transformation:** Random Forest decision splits are invariant to monotonic feature scaling. To preserve direct interpretability and avoid unnecessary transformations, raw feature scales in centimeters are retained.
- **Feature Dispersion Estimation:** Feature sample standard deviations ($\sigma_j$) required for noise scaling are computed **exclusively from the training partition** (see Section 8).

---

## 6. Train/Test Split Strategy

To guarantee reproducible and unbiased evaluation:

- **Partitioning Method:** Stratified Random Splitting (`sklearn.model_selection.train_test_split` with `stratify=y`).
- **Split Proportion:** 80% Training ($N_{\text{train}} = 120$), 20% Testing ($N_{\text{test}} = 30$).
- **Stratification Guarantee:** Exactly 40 samples per class in $X_{\text{train}}$ and 10 samples per class in $X_{\text{test}}$.
- **Split Seed:** `split_seed = 42` (strictly fixed across all severity levels, runs, and seed variations).

```
Total Dataset (N = 150)
├── Training Partition: 80% (N_train = 120; 40 setosa, 40 versicolor, 40 virginica) [FROZEN]
└── Test Partition:     20% (N_test = 30;  10 setosa, 10 versicolor, 10 virginica) [EVALUATION ONLY]
```

> **Crucial Rule:** The train/test split is generated once and frozen. It is never re-partitioned across different noise severities or research seeds.

---

## 7. Model Configuration

The classifier under evaluation is an ensemble Random Forest model:

| Hyperparameter | Configuration Value | Rationale |
|---|---|---|
| **Model Family** | `RandomForestClassifier` (`sklearn.ensemble`) | Canonical non-linear ensemble baseline |
| **`n_estimators`** | `100` | Standard ensemble capacity for tabular benchmarks |
| **`max_depth`** | `None` | Trees expand until all leaves are pure |
| **`criterion`** | `'gini'` | Standard Gini impurity criterion |
| **`min_samples_split`** | `2` | Standard unconstrained split threshold |
| **`min_samples_leaf`** | `1` | Standard leaf size |
| **`bootstrap`** | `True` | Standard bootstrap aggregation |
| **`random_state`** | `model_seed` (parameterized: `42` for dev; suite for research) | Controls tree bootstrapping and feature subsampling |

---

## 8. Gaussian Noise Mathematical Definition

Let $X_{ij}$ represent the uncorrupted value of feature $j \in \{1, 2, 3, 4\}$ for test sample $i \in \{1, \dots, N_{\text{test}}\}$.

The perturbed test feature value $X'_{ij}$ is defined as:

$$X'_{ij} = X_{ij} + \varepsilon_{ij}$$

where the additive perturbation $\varepsilon_{ij}$ is drawn from an independent, zero-mean Gaussian distribution scaled to the empirical standard deviation of feature $j$:

$$\varepsilon_{ij} \sim \mathcal{N}\left(0, \, (s \cdot \sigma_j)^2\right)$$

### Parameter Definitions:
1. **$s \in [0.0, 1.0]$ (Noise Severity Factor):** A dimensionless fractional scalar determining the perturbation magnitude relative to feature dispersion.
2. **$\sigma_j$ (Training Feature Standard Deviation):** The sample standard deviation of feature $j$ calculated **strictly on the training partition**:

$$\sigma_j = \sqrt{\frac{1}{N_{\text{train}} - 1} \sum_{k=1}^{N_{\text{train}}} \left(X_{kj}^{\text{train}} - \bar{X}_j^{\text{train}}\right)^2}$$

where $\bar{X}_j^{\text{train}} = \frac{1}{N_{\text{train}}} \sum_{k=1}^{N_{\text{train}}} X_{kj}^{\text{train}}$.

```
Feature Training Dispersion (Estimated from X_train, N_train=120):
  σ_1 (Sepal Length) ──┐
  σ_2 (Sepal Width)  ──┼──> Scaled Noise Matrix: ε_ij ~ N(0, (s * σ_j)^2)
  σ_3 (Petal Length) ──┤                               │
  σ_4 (Petal Width)  ──┘                               ▼
                                  Perturbed Test Set: X'_test = X_test + ε
```

---

## 9. Noise Severity Levels

The experiment evaluates a structured grid of 7 discrete noise severity levels:

$$S = \{0.00, 0.05, 0.10, 0.15, 0.20, 0.25, 0.30\}$$

| Severity Level ($s$) | Percentage Representation | Experimental Role |
|---|---|---|
| **`0.00`** | 0.0% ($\varepsilon_{ij} = 0$) | **Control Baseline** (pristine evaluation) |
| **`0.05`** | 5.0% of $\sigma_j$ | Low-level perturbation (sensor tolerance) |
| **`0.10`** | 10.0% of $\sigma_j$ | Moderate perturbation |
| **`0.15`** | 15.0% of $\sigma_j$ | Moderate-high perturbation |
| **`0.20`** | 20.0% of $\sigma_j$ | High perturbation |
| **`0.25`** | 25.0% of $\sigma_j$ | Severe perturbation |
| **`0.30`** | 30.0% of $\sigma_j$ | Extreme perturbation (stress boundary) |

---

## 10. Random Seed and Reproducibility Strategy

To decouple data partitioning variance from stochastic model training and perturbation generation, the protocol defines three distinct seed controls:

```
┌────────────────────────────────────────────────────────────────────────┐
│                        SEED ISOLATION ARCHITECTURE                     │
├────────────────────────────────────────────────────────────────────────┤
│ 1. split_seed = 42          [FROZEN: Defines immutable train/test split]│
│ 2. model_seed = seed_val    [CONTROLS: Forest bootstrapping & splits]  │
│ 3. noise_seed = seed_val    [CONTROLS: Gaussian PRNG draw for ε_ij]    │
└────────────────────────────────────────────────────────────────────────┘
```

### Seed Execution Suites

1. **Initial Development Seed:**
   - Single-run validation: `seed = 42` (`split_seed = 42`, `model_seed = 42`, `noise_seed = 42`).
2. **Planned Research Multi-Seed Suite:**
   - Multi-run statistical suite: $R = 5$ seeds:
   
   $$\text{Seeds} = [42, 123, 456, 789, 1011]$$

   - For each seed $r \in \text{Seeds}$, `model_seed = r` and `noise_seed = r`, while `split_seed` remains permanently fixed at `42`.

---

## 11. Evaluation Metrics

All evaluations report exact floating-point values rounded to four decimal places (e.g., `0.9667`):

### 11.1 Primary Metric: Macro-Averaged F1-Score ($\text{Macro-F1}$)
For classes $k \in \{0, 1, 2\}$:

$$\text{Macro-F1} = \frac{1}{3} \sum_{k=0}^2 \text{F1}_k = \frac{1}{3} \sum_{k=0}^2 \frac{2 \cdot \text{Precision}_k \cdot \text{Recall}_k}{\text{Precision}_k + \text{Recall}_k}$$

### 11.2 Secondary Metrics
- **Classification Accuracy:** $\text{Accuracy} = \frac{1}{N_{\text{test}}} \sum_{i=1}^{N_{\text{test}}} \mathbb{I}(\hat{y}_i = y_i)$
- **Per-Class Metrics:** $\text{Precision}_k$, $\text{Recall}_k$, and $\text{F1}_k$ for each species.
- **Confusion Matrix ($C$):** $3 \times 3$ integer matrix where $C_{k, l}$ records the count of test samples from true class $k$ predicted as class $l$.

### 11.3 Performance Degradation Metrics
- **Absolute Degradation ($\Delta_{\text{abs}}$):**
  
  $$\Delta_{\text{abs}}(s) = \text{Macro-F1}(0) - \text{Macro-F1}(s)$$
  
  Reported in **percentage points (`pp`)**, where $1.0\,\text{point} = 0.01$.

- **Relative Degradation ($\Delta_{\text{rel}}$):**
  
  $$\Delta_{\text{rel}}(s) = \frac{\text{Macro-F1}(0) - \text{Macro-F1}(s)}{\text{Macro-F1}(0)} \times 100\%$$

---

## 12. Predefined Failure Criterion

To prevent post-hoc rationalization, the failure criterion is strictly established *a priori*:

### Definition of Failure
A model is deemed to have **failed** at noise severity $s$ if its Macro-F1 score falls below the fixed reliability threshold:

$$\text{Failure Condition:} \quad \text{Macro-F1}(s) < 0.80$$

### Observed Failure Boundary ($s^*$)
The observed failure boundary $s^*$ is defined as the minimum tested severity level at which the failure condition is met:

$$s^* = \min \left\{ s \in S \mid \text{Macro-F1}(s) < 0.80 \right\}$$

- If $\text{Macro-F1}(s) \ge 0.80$ for all $s \in S$, the result is recorded as:
  $$s^* > 0.30 \quad (\text{Not observed within tested severity range})$$

### Mandatory Reporting Caption
Any presentation or discussion of $s^*$ must be accompanied verbatim by:
> *"Observed failure boundary under the specified experimental configuration."*

---

## 13. Experiment Execution Procedure

The execution of experiment E001 follows a strict 7-phase procedural pipeline:

```
[Phase 1: Environment & Config Lock]
         │
[Phase 2: Ingestion & Stratified Split (split_seed=42)]
         │
[Phase 3: Compute Training Dispersion (σ_j from X_train)]
         │
[Phase 4: Train Random Forest (model_seed)]
         │
[Phase 5: Evaluate Control Baseline (s=0.00)]
         │
[Phase 6: Systematic Stress Sweep (s in {0.05, ..., 0.30})]
         │
[Phase 7: Artifact Synthesis & Manifest Generation]
```

### Detailed Steps:
1. **Phase 1 — Configuration & Environment Lock:**
   - Load experiment parameters from configuration. Record Python version, OS metadata, and package versions (`numpy`, `scipy`, `scikit-learn`).
2. **Phase 2 — Ingestion & Stratified Partitioning:**
   - Ingest the 150 Iris instances.
   - Execute stratified split with `split_seed = 42` into $X_{\text{train}}$ ($n=120$) and $X_{\text{test}}$ ($n=30$).
3. **Phase 3 — Training Dispersion Estimation:**
   - Compute standard deviation vector $\boldsymbol{\sigma} = [\sigma_1, \sigma_2, \sigma_3, \sigma_4]$ using solely $X_{\text{train}}$.
4. **Phase 4 — Model Training:**
   - Instantiate `RandomForestClassifier(n_estimators=100, max_depth=None, random_state=model_seed)`.
   - Fit model exclusively on $(X_{\text{train}}, Y_{\text{train}})$.
5. **Phase 5 — Baseline Evaluation ($s = 0.00$):**
   - Predict labels on unperturbed $X_{\text{test}}$.
   - Compute and log baseline metrics: $\text{Macro-F1}(0)$, $\text{Accuracy}(0)$, per-class F1, and $C(0)$.
6. **Phase 6 — Systematic Severity Sweep ($s \in \{0.05, 0.10, 0.15, 0.20, 0.25, 0.30\}$):**
   - For each severity level $s$:
     a. Initialize NumPy PRNG with `noise_seed`.
     b. Draw $\varepsilon_{ij} \sim \mathcal{N}(0, (s \cdot \sigma_j)^2)$ for all $i \in \{1, \dots, 30\}$, $j \in \{1, \dots, 4\}$.
     c. Construct $X'_{\text{test}} = X_{\text{test}} + \boldsymbol{\varepsilon}$.
     d. Generate predictions $\hat{y} = \text{model.predict}(X'_{\text{test}})$.
     e. Compute $\text{Macro-F1}(s)$, $\text{Accuracy}(s)$, $\Delta_{\text{abs}}(s)$, $\Delta_{\text{rel}}(s)$, and $C(s)$.
     f. Check failure condition $\text{Macro-F1}(s) < 0.80$.
7. **Phase 7 — Artifact Serialization:**
   - Emit structured evaluation tables, confusion matrices, robustness curves, and the complete JSON manifest.

---

## 14. Data Leakage Prevention

To maintain impeccable scientific integrity, four inviolable isolation barriers are enforced:

| Isolation Barrier | Mechanism | Audit Check |
|---|---|---|
| **Barrier 1: Split Isolation** | Data partitioning occurs prior to any statistical calculation. | $X_{\text{test}}$ is never passed to any fitting or parameter estimation routine. |
| **Barrier 2: Training-Only Dispersion** | Feature standard deviations $\sigma_j$ are calculated strictly on $X_{\text{train}}$. | Verify $\sigma_j$ code references $X_{\text{train}}$, never $X$ or $X_{\text{test}}$. |
| **Barrier 3: Evaluation-Only Perturbation** | Noise is applied exclusively to $X_{\text{test}}$ at evaluation time. | Model training is executed on pure, unperturbed $X_{\text{train}}$. |
| **Barrier 4: Label Immutability** | Perturbations modify continuous features only ($X \to X'$). | Ground truth targets $Y_{\text{test}}$ remain unaltered. |

---

## 15. Expected Output Artifacts

Upon completion of E001, the system must generate and persist the following artifacts:

```
artifacts/experiments/E001/
├── manifest.json                  # Experiment metadata, seeds, git SHA, environment
├── baseline_metrics.json          # Metrics at s=0.00
├── severity_metrics.csv           # Tabular results for all s in S
├── robustness_curve.json          # Formatted coordinates for UI / visualization
├── confusion_matrices/
│   ├── cm_s00.json
│   ├── cm_s05.json
│   ├── ...
│   └── cm_s30.json
└── failure_analysis.json          # Observed boundary s* and class degradation breakdown
```

### Manifest Schema (`manifest.json`)
The manifest must contain:
- `experiment_id`: `"E001"`
- `protocol_version`: `"1.0.0"`
- `timestamp_utc`: ISO 8601 string
- `git_commit_hash`: String (or `"uncommitted"` in dirty dev state)
- `seeds`: `{"split_seed": 42, "model_seed": 42, "noise_seed": 42}`
- `model_config`: `{"name": "RandomForestClassifier", "n_estimators": 100, "max_depth": null}`
- `dataset_metadata`: `{"name": "iris", "n_train": 120, "n_test": 30, "feature_sigmas": [ ... ]}`
- `failure_threshold`: `0.80`

---

## 16. Statistical Analysis Plan

For multi-seed execution across $R = 5$ seeds ($\text{Seeds} = [42, 123, 456, 789, 1011]$):

### 16.1 Point Estimators and Dispersion
For each severity level $s \in S$:

1. **Sample Mean ($\bar{M}(s)$):**
   
   $$\bar{M}(s) = \frac{1}{R} \sum_{r=1}^R M_r(s)$$

2. **Sample Standard Deviation ($S_M(s)$):**
   
   $$S_M(s) = \sqrt{\frac{1}{R - 1} \sum_{r=1}^R \left(M_r(s) - \bar{M}(s)\right)^2}$$

3. **Standard Error of the Mean ($\text{SEM}(s)$):**
   
   $$\text{SEM}(s) = \frac{S_M(s)}{\sqrt{R}}$$

### 16.2 Confidence Intervals
A 95% Confidence Interval for the mean Macro-F1 at severity $s$ will be constructed using Student's $t$-distribution with $R - 1 = 4$ degrees of freedom ($t_{0.025, 4} = 2.776$):

$$\text{CI}_{95\%}(s) = \left[ \bar{M}(s) - 2.776 \cdot \text{SEM}(s), \; \bar{M}(s) + 2.776 \cdot \text{SEM}(s) \right]$$

### 16.3 Monotonicity and Trend Analysis
- Verify whether $\bar{M}(s_k) \ge \bar{M}(s_{k+1})$ across consecutive severity steps.
- If non-monotonic deviations occur, analyze sample-level transitions to determine if small perturbations coincidentally shifted ambiguous instances across decision boundaries.

---

## 17. Success Criteria

The experimental execution of E001 will be considered successful if and only if all the following verifiable criteria are satisfied:

- [ ] **Execution Integrity:** Pipeline executes from start to finish without runtime exceptions.
- [ ] **Grid Completeness:** All 7 severity levels ($s \in \{0.00, 0.05, 0.10, 0.15, 0.20, 0.25, 0.30\}$) are fully evaluated.
- [ ] **Data Isolation Verification:** Unit tests confirm zero test leakage during $\sigma_j$ calculation and zero contamination of $X_{\text{train}}$ during noise injection.
- [ ] **Metric Verification:** Computed values for $\text{Macro-F1}$, $\text{Accuracy}$, $\Delta_{\text{abs}}$, and $\Delta_{\text{rel}}$ match independent hand-calculated assertions on test vectors.
- [ ] **Deterministic Reproducibility:** Re-running the pipeline with `seed = 42` generates bitwise identical metrics across repeated executions.
- [ ] **Artifact Generation:** All 6 required artifact types (manifest, baseline metrics, CSV table, robustness curve data, confusion matrices, failure analysis) are persisted to disk in valid JSON/CSV formats.

---

## 18. Limitations and Threats to Validity

To preserve scientific rigor, the following experimental limitations and threats to validity are formally acknowledged:

1. **Test Set Granularity (Internal Validity):** With $N_{\text{test}} = 30$ samples (10 per class), a single misclassified sample alters accuracy and recall by $3.33\,\text{percentage points}$. Consequently, minor metric variations between adjacent severities may reflect discrete sample discretization rather than continuous behavioral shifts.
2. **Benchmark Generalizability (External Validity):** The Iris dataset is small, low-dimensional ($D=4$), and contains well-defined cluster geometry. Conclusions drawn from E001 cannot be extrapolated to high-dimensional image, text, or noisy tabular datasets without separate empirical validation.
3. **Perturbation Specificity (Construct Validity):** Isotropic additive Gaussian noise is a synthetic perturbation model. It does not reflect correlated feature corruptions, structural dropouts, adversarial perturbations, or non-linear sensor drift.
4. **Threshold Subjectivity (Conclusion Validity):** The failure threshold ($\text{Macro-F1} < 0.80$) is an operational convention chosen *a priori*. A different threshold (e.g., $0.85$ or $0.75$) would shift the observed boundary $s^*$.
5. **No Causal Claim:** Identified feature sensitivities or class confusion patterns represent observational correlations under the tested noise protocol, not causal mechanisms.

---

## 19. Experiment Reproduction Instructions

Once the underlying ML execution engine is implemented, experiment E001 can be deterministically reproduced using the following protocol:

### Prerequisites
- Python $\ge 3.10$
- Dependencies: `numpy`, `scipy`, `scikit-learn`, `pydantic`

### Reproduction Command (CLI)
```bash
# Execute single-seed validation run (Development Seed 42)
python -m ml_engine.experiments.run --config configs/experiments/e001_iris_rf_gaussian.yaml --seed 42

# Execute full 5-seed research suite
python -m ml_engine.experiments.run --config configs/experiments/e001_iris_rf_gaussian.yaml --multi-seed
```

### Verification Verification
```bash
# Execute automated unit and integration tests for E001
pytest tests/ml_engine/test_e001_protocol.py -v
```
