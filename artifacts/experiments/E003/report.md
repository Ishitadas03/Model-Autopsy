# Empirical Research Report: E003 (RQ5 Model Robustness Comparison)
> **Title:** Cross-Model Empirical Robustness Evaluation Across Diverse Machine Learning Architectures on the Iris Benchmark  
> **Protocol Version:** 1.0.0 | **Execution Timestamp:** 2026-10-25 09:41:48 UTC  
> **Sample Size:** $R = 5$ Independent PRNG Seeds: `[42, 123, 456, 789, 1011]`  
> **Repository Context:** Model Autopsy ML Engine  

---

## 1. Executive Summary & RQ5 Empirical Findings

- **Primary Research Question (RQ5):** *"How does robustness vary across different ML algorithms under identical experimental conditions?"*
- **Summary Matrix Across Models, Corruptions, and Severities:**

| Model Architecture | Corruption Modality | Clean Baseline ($s=0.00$) | Worst Macro-F1 ($s=0.30$, Mean ± SEM) | Absolute Degradation | Relative Degradation | Mean Failure Boundary ($s^*$) | Earliest Individual Boundary |
|---|---|:---:|:---:|:---:|:---:|:---:|:---:|
| **Random Forest** | Additive Gaussian Noise | `0.9265` | `0.8538 ± 0.0282` | `+7.28 pp` | `7.80%` | s* > 0.30 | s* = 0.30 |
| **Random Forest** | MCAR Missingness (Imputed) | `0.9265` | `0.7434 ± 0.0147` | `+18.32 pp` | `19.65%` | s* = 0.25 | s* = 0.20 |
| **Random Forest** | Impulsive Outliers (5σ) | `0.9265` | `0.7610 ± 0.0236` | `+16.55 pp` | `17.88%` | s* = 0.25 | s* = 0.10 |
| **Logistic Regression (Scaled)** | Additive Gaussian Noise | `0.9333` | `0.9130 ± 0.0201` | `+2.03 pp` | `2.17%` | s* > 0.30 | s* > 0.30 |
| **Logistic Regression (Scaled)** | MCAR Missingness (Imputed) | `0.9333` | `0.7522 ± 0.0326` | `+18.11 pp` | `19.40%` | s* = 0.30 | s* = 0.20 |
| **Logistic Regression (Scaled)** | Impulsive Outliers (5σ) | `0.9333` | `0.5192 ± 0.0167` | `+41.41 pp` | `44.37%` | s* = 0.10 | s* = 0.05 |
| **Gradient Boosting** | Additive Gaussian Noise | `0.9666` | `0.8447 ± 0.0305` | `+12.19 pp` | `12.61%` | s* > 0.30 | s* = 0.20 |
| **Gradient Boosting** | MCAR Missingness (Imputed) | `0.9666` | `0.7947 ± 0.0466` | `+17.19 pp` | `17.78%` | s* = 0.30 | s* = 0.20 |
| **Gradient Boosting** | Impulsive Outliers (5σ) | `0.9666` | `0.7159 ± 0.0488` | `+25.07 pp` | `25.93%` | s* = 0.25 | s* = 0.15 |

### Worst-Case Performance Comparison ($s = 0.30$ Maximum Stress)

| Corruption Modality | Random Forest Mean Macro-F1 | Logistic Regression Mean Macro-F1 | Gradient Boosting Mean Macro-F1 |
|---|:---:|:---:|:---:|
| **Additive Gaussian Noise** | `0.8538` | `0.9130` | `0.8447` |
| **MCAR Missingness (Imputed)** | `0.7434` | `0.7522` | `0.7947` |
| **Impulsive Outliers (5σ)** | `0.7610` | `0.5192` | `0.7159` |

- **Mandated Reporting Captions:**
  > *"Observed failure boundary under the specified experimental configuration."*  
  > *"Empirical sensitivity — not a causal explanation."*

---

## 2. Experimental Controls & Data Leakage Prevention

All models were evaluated under strictly identical, frozen experimental invariants:

1. **Frozen Dataset Partitioning:**
   - Canonical Fisher Iris benchmark ($N=150$, $D=4$, 3 classes).
   - Stratified 80/20 train/test split fixed with `split_seed = 42` ($N_{\text{train}}=120$, $N_{\text{test}}=30$).
   - Training and testing partitions exhibit strictly $0$ overlapping indices.
2. **Leakage-Free Preprocessing Pipeline for Logistic Regression:**
   - Logistic Regression requires feature scaling due to uniform $L_2$ penalty weighting.
   - Encapsulated in an explicit `sklearn.pipeline.Pipeline([('scaler', StandardScaler()), ('classifier', LogisticRegression())])`.
   - The `StandardScaler` is fitted **exclusively on the training partition** ($X_{\text{train}}$).
   - During evaluation, test instances (clean and corrupted) are transformed using the frozen training means and dispersions; test data is never used to fit or adapt scaling parameters.
3. **Scale-Invariant Tree Ensembles:**
   - Random Forest and Gradient Boosted Decision Trees partition continuous feature space via orthogonal axis-aligned threshold splits, which are mathematically invariant to monotonic feature scaling. They operate on raw centimeter measurements.

---

## 3. Algorithmic Robustness Breakdown & Inductive Biases

### 3.1 Random Forest (Bagged Orthogonal Trees)
- **Mechanism:** Builds 100 decorrelated, unconstrained decision trees on bootstrap samples with random feature sub-selection.
- **Robustness Profile:** Ensembling over independently grown trees dampens continuous isotropic noise variance. However, high-magnitude outlier spikes ($\pm 5\sigma$) displace test instances across multiple decision boundaries simultaneously, causing acute performance deterioration once critical splits are breached.

### 3.2 Logistic Regression (Regularized Linear Hyperplanes)
- **Mechanism:** Solves convex multinomial loss parameterized by hyperplanes $w_c^T z + b_c$ with $L_2$ weight regularization ($C=1.0$).
- **Robustness Profile:** Linear hyperplanes form smooth, global decision surfaces. While continuous isotropic Gaussian noise is partially averaged across coordinates, extreme impulsive outliers ($5\sigma$) inject immense leverage into the dot product, shifting logits decisively toward incorrect classes.

### 3.3 Gradient Boosted Decision Trees (Additive Sequential Ensembles)
- **Mechanism:** Sequential stagewise boosting of shallow trees (depth 3) minimizing multinomial deviance.
- **Robustness Profile:** Boosted shallow trees construct highly refined, localized decision regions. They achieve superior baseline accuracy on clean data, but their compact sequential dependencies make them sensitive when corrupted coordinates mislead early decision stumps.

---

## 4. Methodological Distinctions: Baseline Capacity vs. Degradation Rate

A central methodological requirement of Model Autopsy is rigorously distinguishing between:
1. **Nominal Baseline Performance on Clean Data ($s=0.00$):** Reflecting model capacity under nominal i.i.d. conditions.
2. **Absolute Degradation ($\Delta_{\text{abs}}$):** Drop in percentage points from clean baseline to stressed state.
3. **Relative Degradation ($\Delta_{\text{rel}}$):** Percentage loss relative to the model's own baseline:
   $$\Delta_{\text{rel}} = \frac{\text{Macro-F1}_{\text{baseline}} - \text{Macro-F1}(s)}{\text{Macro-F1}_{\text{baseline}}} \times 100\%$$

A model with a superior clean baseline may experience a higher absolute percentage-point drop yet maintain higher absolute performance, or vice-versa. Complete decoupling of baseline capacity from degradation dynamics prevents misleading claims of intrinsic robustness.

---

## 5. Methodological Warnings from Phase 3 Audit

1. **Warning 1: Monotone Nested Corruption Filtration:**
   - In the severity loop, operators are invoked with `seed = seed`, meaning `np.random.default_rng(seed)` is re-instantiated at each severity step.
   - For MCAR missingness and outlier contamination, cells corrupted at severity $s_1$ remain corrupted at severity $s_2 > s_1$ ($\text{Cells}(s_1) \subseteq \text{Cells}(s_2)$).
   - This creates an incremental cumulative stress-test filtration rather than 7 mutually independent coordinate draws, isolating the marginal degradation caused by additional corrupted cells.
2. **Warning 2: Finite Resolution & Discretization Plateaus:**
   - With $N_{\text{test}} = 30$ samples, each misclassification alters accuracy by $3.33\,\text{percentage points}$.
   - Flat horizontal segments in Macro-F1 curves between adjacent severities reflect instances where additional perturbed coordinates fell on already-misclassified samples or uninfluential dimensions, not algorithmic immunity.

---

## 6. Deterministic Reproduction Statement

To deterministically reproduce this cross-model evaluation across all 5 seeds:
```bash
python scripts/experiments/run_e003.py
```
