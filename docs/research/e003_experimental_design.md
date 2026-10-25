# Experimental Design & Protocol Specification: E003

**Experiment ID:** `E003`  
**Experiment Title:** Cross-Model Empirical Robustness Evaluation Across Machine Learning Architectures on the Iris Benchmark  
**Protocol Version:** 1.0.0  
**Parent Documents:** [`docs/research/problem_statement.md`](problem_statement.md), [`docs/research/experimental_protocol.md`](experimental_protocol.md), [`docs/research/e002_experimental_design.md`](e002_experimental_design.md), [`docs/research/phase3_scientific_audit.md`](phase3_scientific_audit.md)  
**Author:** Person 1 (ML & Research Lead)  
**Target Context:** Model Autopsy ML Engine  
**Status:** Approved Specification  

---

## 1. Executive Summary & Research Motivation

In Experiments E001 and E002, the Model Autopsy project established:
1. The empirical degradation trajectory and failure boundary of a canonical Random Forest classifier under additive Gaussian feature noise ($s^* > 0.30$ for mean performance).
2. The differential impact of distinct corruption modalities on a single model architecture (E002), demonstrating that discrete cell loss (MCAR) and impulsive outliers ($5\sigma$) trigger earlier failure boundaries ($s^* = 0.25$) than continuous Gaussian jitter.

However, a fundamental scientific question in empirical ML safety remains unanswered:
> **RQ5: How does robustness vary across different ML algorithms under identical experimental conditions?**

Different machine learning architectures embody fundamentally different inductive biases, loss formulations, and geometric decision boundaries:
- **Random Forests (Bagged Orthogonal Trees):** Ensembles of decorrelated axis-aligned partition trees with majority voting.
- **Logistic Regression (Linear Classification):** Parametric hyperplanes governed by linear combinations of features through a multinomial softmax/logistic link, regularized by an $L_2$ norm.
- **Gradient Boosted Decision Trees (Sequentially Boosted Trees):** Forward stagewise additive expansion of shallow decision trees minimizing multi-class log-loss.

Experiment **E003** provides a controlled, leak-free, multi-seed comparative audit of these three model families across all three corruption modalities (Gaussian noise, MCAR missingness, and impulsive outliers) over the established 7-point severity grid.

---

## 2. Shared Experimental Invariants

To guarantee that observed performance variations arise exclusively from algorithmic differences and inductive biases, all external experimental factors are strictly frozen:

| Experimental Dimension | Canonical Specification | Controlled Source |
|---|---|---|
| **Benchmark Dataset** | Fisher Iris Dataset ($N = 150$, 4 features, 3 classes) | `sklearn.datasets.load_iris` |
| **Dataset Validation** | Complete, non-null, schema $(150, 4)$, 50 samples/class | `iris.py:load_and_validate_iris` |
| **Partitioning Strategy** | Stratified 80/20 train/test split | `train_test_split(stratify=y)` |
| **Split Seed** | `split_seed = 42` (strictly frozen across all models) | $N_{\text{train}} = 120, N_{\text{test}} = 30$ |
| **Class Distribution** | Training: 40/class; Testing: 10/class | Zero partition index overlap |
| **Research Seed Suite** | $R = 5$ seeds: `[42, 123, 456, 789, 1011]` | Protocol §10 |
| **Severity Grid ($S$)** | 7 levels: `[0.00, 0.05, 0.10, 0.15, 0.20, 0.25, 0.30]` | Protocol §9 |
| **Corruption Operators** | Gaussian Noise, MCAR Missingness, Impulsive Outliers ($5\sigma$) | E002 validated operators |
| **Primary Evaluation Metric** | Macro-Averaged F1-Score ($\text{Macro-F1}$) | Protocol §11.1 |
| **Secondary Evaluation Metrics**| Accuracy, per-class F1/Precision/Recall, Confusion Matrix | Protocol §11.2 |
| **Primary Failure Threshold** | Strict inequality: $\text{Macro-F1} < 0.80$ | Protocol §12 |
| **Diagnostic Alert** | Relative degradation $\Delta_{\text{rel}} > 15.0\%$ | Configs & Protocol §12 |
| **Mandatory Caption** | *"Observed failure boundary under the specified experimental configuration."* | Protocol §12 |

---

## 3. Evaluated Model Architectures & Preprocessing Pipelines

### 3.1 Model 1: Random Forest Classifier (`random_forest`)
- **Estimator:** `sklearn.ensemble.RandomForestClassifier`
- **Hyperparameter Specification:**
  - `n_estimators`: 100
  - `max_depth`: None (unconstrained tree growth)
  - `criterion`: `'gini'`
  - `min_samples_split`: 2
  - `min_samples_leaf`: 1
  - `bootstrap`: True
  - `random_state`: Parameterized seed ($r \in \{42, 123, 456, 789, 1011\}$)
- **Preprocessing Strategy:**
  - Raw continuous features in centimeters.
  - Decision tree threshold splits are strictly invariant to monotonic feature scaling; therefore, no feature standardization is applied.
- **Inductive Bias & Hypothesis:**
  - Non-linear, step-function orthogonal partitions. Averaging over 100 trees dampens localized noise variance. However, high-magnitude outlier spikes can alter partition activations if they cross outermost training thresholds.

### 3.2 Model 2: Regularized Logistic Regression (`logistic_regression`)
- **Estimator:** `sklearn.linear_model.LogisticRegression`
- **Hyperparameter Specification:**
  - `penalty`: `'l2'`
  - `C`: 1.0 (inverse regularization strength)
  - `solver`: `'lbfgs'`
  - `max_iter`: 1000 (ensuring absolute mathematical convergence)
  - `multi_class`: `'multinomial'` (or `'auto'` resolving to multinomial)
  - `random_state`: Parameterized seed ($r$)
- **Preprocessing Strategy & Leakage Prevention Pipeline:**
  - **Requirement:** Unlike tree-based algorithms, linear models are sensitive to feature scales because the $L_2$ regularization penalty ($\lambda \sum w_j^2$) penalizes weights uniformly across dimensions regardless of variance.
  - **Pipeline Architecture:** Encapsulated in an explicit `sklearn.pipeline.Pipeline`:
    ```python
    Pipeline([
        ('scaler', StandardScaler(with_mean=True, with_std=True)),
        ('classifier', LogisticRegression(C=1.0, max_iter=1000, random_state=seed))
    ])
    ```
  - **Leakage Prevention Invariant:**
    The `StandardScaler` must be fitted **strictly on the training partition** ($X_{\text{train}}$) during `pipeline.fit(X_train, y_train)`.
    During stress evaluation, `pipeline.predict(X_corrupted)` applies the frozen training parameters ($\mu_j^{\text{train}}, \sigma_j^{\text{train}}$) to scale corrupted inputs:
    $$Z_{ij} = \frac{X'_{ij} - \mu_j^{\text{train}}}{\sigma_j^{\text{train}}}$$
    $X_{\text{test}}$ is never used for parameter fitting or updating.
- **Inductive Bias & Hypothesis:**
  - Globally linear decision hyperplanes. Log-odds are linear in feature values:
    $$P(Y = c \mid X) \propto \exp(w_c^T Z + b_c)$$
  - Because predictions depend on the linear dot product $\sum w_{cj} Z_{ij}$, a massive outlier ($+5\sigma$) in a single feature coordinate dramatically scales the logit, potentially causing severe misclassification. Conversely, moderate symmetric Gaussian noise may cancel out on average across features.

### 3.3 Model 3: Gradient Boosted Decision Trees (`gradient_boosting`)
- **Estimator:** `sklearn.ensemble.GradientBoostingClassifier`
- **Hyperparameter Specification:**
  - `n_estimators`: 100
  - `learning_rate`: 0.1
  - `max_depth`: 3 (shallow decision trees)
  - `subsample`: 1.0 (deterministic gradient boosting)
  - `criterion`: `'friedman_mse'`
  - `random_state`: Parameterized seed ($r$)
- **Preprocessing Strategy:**
  - Raw continuous features in centimeters (tree splits are scale-invariant; no scaling required).
- **Inductive Bias & Hypothesis:**
  - Sequential residual minimization. Unlike Random Forests (which build deep, independent trees in parallel), Gradient Boosting fits each tree sequentially to the pseudo-residuals of the prior ensemble.
  - With constrained tree depth (`max_depth = 3`), individual trees have limited complexity, which may provide strong generalization on clean data but could exhibit vulnerability if early sequential trees commit to corrupted splits.

---

## 4. Candidate Corruption Modalities & Operator Reuse

E003 reuses the exact, audited mathematical corruption operators from E002:

1. **Additive Gaussian Noise (`gaussian_noise`):**
   $$X'_{ij} = X_{ij} + \varepsilon_{ij}, \quad \varepsilon_{ij} \sim \mathcal{N}\left(0, (s \cdot \sigma_j^{\text{train}})^2\right)$$
   Continuous perturbation scaled relative to training-only feature standard deviations $\sigma_j^{\text{train}}$ ($ddof=1$).
2. **MCAR Missingness with Training-Mean Imputation (`feature_missingness_mcar`):**
   $$M_{ij} \sim \text{Bernoulli}(s), \quad \hat{X}_{ij} = \begin{cases} X_{ij} & \text{if } M_{ij} = 0 \\ \mu_j^{\text{train}} & \text{if } M_{ij} = 1 \end{cases}$$
   Evaluates resilience to structural information loss where missing cells are imputed with training-only feature means $\mu_j^{\text{train}}$.
3. **Impulsive Outlier Contamination (`feature_outliers`):**
   $$O_{ij} \sim \text{Bernoulli}(s), \quad X'_{ij} = \begin{cases} X_{ij} & \text{if } O_{ij} = 0 \\ \mu_j^{\text{train}} + \delta_{ij} \cdot 5.0 \cdot \sigma_j^{\text{train}} & \text{if } O_{ij} = 1 \end{cases}$$
   where $\delta_{ij} \in \{-1.0, +1.0\}$ with equal probability ($p=0.5$).

---

## 5. Methodological Rigor & Audit Warning Compliance

The Phase 3 scientific audit ([`docs/research/phase3_scientific_audit.md`](phase3_scientific_audit.md)) documented two explicit warnings that govern E003:

### 5.1 Warning 1: Preserving Monotone Nested Filtrations
- **Audit Observation:** Calling `feature_missingness_mcar` and `feature_outliers` with `seed = seed` inside the severity loop instantiates `np.random.default_rng(seed)` afresh at each severity step. This ensures that cells corrupted at severity $s_1$ remain corrupted at severity $s_2 > s_1$ ($\text{Cells}(s_1) \subseteq \text{Cells}(s_2)$).
- **E003 Protocol Decision:** This nested filtration behavior is **deliberately preserved**. It enables a true incremental stress-test where higher severities compound perturbations on existing corrupted cells rather than testing mutually independent random subsets. All models will encounter the exact same corrupted matrices across all seeds and severity steps.

### 5.2 Warning 2: Discretization Plateaus on $N_{\text{test}} = 30$
- **Audit Observation:** With $N_{\text{test}} = 30$ samples, each misclassification changes accuracy by exactly $1/30 \approx 3.33\,\text{pp}$. Between certain severities, additional corrupted coordinates may not trigger any net decision boundary transitions, creating horizontal plateaus.
- **E003 Protocol Decision:** Such plateaus must not be interpreted as algorithmic immunity. Both accuracy and Macro-F1 will be reported alongside confusion matrices to provide complete transparency regarding discrete sample transitions.

### 5.3 Decoupling Clean Baseline Performance from Robustness Degradation
A critical methodological trap in cross-model comparisons is conflating high nominal test accuracy with intrinsic corruption robustness:
- A model with clean baseline Macro-F1 of $0.97$ that drops to $0.78$ at $s=0.25$ experiences an absolute drop of $19.0\,\text{pp}$ ($\Delta_{\text{rel}} = 19.6\%$).
- A model with clean baseline Macro-F1 of $0.90$ that drops to $0.78$ at $s=0.25$ experiences an absolute drop of $12.0\,\text{pp}$ ($\Delta_{\text{rel}} = 13.3\%$).
- Therefore, E003 will compute and report:
  1. Absolute performance: $\text{Macro-F1}(s)$
  2. Absolute degradation: $\Delta_{\text{abs}}(s) = (\text{Macro-F1}_{\text{baseline}} - \text{Macro-F1}(s)) \times 100$
  3. Relative degradation: $\Delta_{\text{rel}}(s) = \frac{\text{Macro-F1}_{\text{baseline}} - \text{Macro-F1}(s)}{\text{Macro-F1}_{\text{baseline}}} \times 100\%$

---

## 6. Statistical Design & Aggregation

For each model $m \in \{\text{RF}, \text{LR}, \text{GB}\}$, corruption $c \in \{\text{Gaussian}, \text{MCAR}, \text{Outlier}\}$, and severity $s \in S$:
1. **Sample Mean:**
   $$\bar{M} = \frac{1}{R} \sum_{r=1}^R M_{r, s}$$
2. **Sample Standard Deviation ($ddof=1$):**
   $$S_M = \sqrt{\frac{1}{R - 1} \sum_{r=1}^R (M_{r, s} - \bar{M})^2}$$
3. **Standard Error of the Mean (SEM):**
   $$\text{SEM} = \frac{S_M}{\sqrt{R}}$$
4. **Two-Sided 95% Student's $t$ Confidence Interval:**
   $$\text{CI}_{95\%} = \bar{M} \pm t_{0.025, \nu} \cdot \text{SEM}$$
   With $R=5$, degrees of freedom $\nu = 4$, and two-sided critical value $t_{0.025, 4} \approx 2.776445$.
5. **Failure Boundaries:**
   - **Mean Performance Boundary ($s^*_{\text{mean}}$):** The lowest severity where $\bar{M} < 0.80$.
   - **Earliest Individual Boundary ($s^*_{\text{indiv}}$):** The lowest severity where any individual seed $r$ has $M_{r, s} < 0.80$.

---

## 7. Artifact Schema & Directory Layout

Artifacts will be serialized to `artifacts/experiments/E003/`:

```
artifacts/experiments/E003/
├── aggregate_comparison.csv          # 63 rows (3 models × 3 corruptions × 7 severities)
├── aggregate_comparison.json         # Complete structured statistical schema
├── manifest.json                     # Git commit, Python/sklearn versions, dataset SHA-256
├── report.md                         # Formal research report with empirical analysis
├── robustness_comparison.png         # Publication-grade 3-panel comparison visualization
└── models/
    ├── random_forest/
    │   ├── aggregate_results.csv
    │   └── corruptions/{gaussian_noise, feature_missingness_mcar, feature_outliers}/
    ├── logistic_regression/
    │   ├── aggregate_results.csv
    │   └── corruptions/{gaussian_noise, feature_missingness_mcar, feature_outliers}/
    └── gradient_boosting/
        ├── aggregate_results.csv
        └── corruptions/{gaussian_noise, feature_missingness_mcar, feature_outliers}/
```

---

## 8. Automated Test Specifications

The E003 test suite (`ml_engine/tests/test_e003_protocol.py`) will strictly verify:
1. **Model Instantiation & Hyperparameter Fidelity:** Validating RF, LR, and GB configs.
2. **Pre-processing Leakage Protection:** Verifying that `StandardScaler` in LR is fitted only on $X_{\text{train}}$ and never accesses $X_{\text{test}}$.
3. **Identical Splitting:** Verifying that all three models receive identical train/test index partitions.
4. **Determinism & Reproducibility:** Verifying that fixed seeds yield deterministic predictions and metrics.
5. **Operator Compatibility:** Verifying that all three models can evaluate corrupted matrices without NaN or runtime exceptions.
6. **Decoupled Failure Logic:** Verifying that $\text{Macro-F1} < 0.80$ and $\Delta_{\text{rel}} > 15.0\%$ operate independently.
7. **End-to-End Runner Execution:** Executing a fast protocol test verifying complete artifact generation and schema validity.
