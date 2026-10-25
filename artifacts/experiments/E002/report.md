# Empirical Research Report: E002 (RQ2 Corruption Comparison)
> **Title:** Controlled Cross-Corruption Robustness Evaluation of Random Forest under Continuous, Missing, and Impulsive Input Corruptions  
> **Protocol Version:** 1.0.0 | **Execution Timestamp:** 2026-10-25 08:56:43 UTC  
> **Sample Size:** $R = 5$ Independent PRNG Seeds: `[42, 123, 456, 789, 1011]`  
> **Repository Context:** Model Autopsy ML Engine  

---

## 1. Executive Summary

- **Primary Research Question (RQ2):** *"How do different types of input corruption affect model reliability differently under controlled experimental conditions?"*
- **Cross-Corruption Comparison Summary ($s = 0.30$ Worst-Case Stress):**

| Corruption Modality | Baseline Macro-F1 ($s=0.00$) | Worst Macro-F1 ($s=0.30$, Mean ± SEM) | Absolute Degradation | Mean Failure Boundary ($s^*$) | Earliest Individual Boundary |
|---|---|---|---|---|---|
| **Additive Gaussian Noise** | `0.9265` | `0.8538 ± 0.0282` | `+7.28 pp` | s* > 0.30 (Unobserved) | s* = 0.30 |
| **MCAR Missingness (Mean Imputed)** | `0.9265` | `0.7434 ± 0.0147` | `+18.32 pp` | s* = 0.25 | s* = 0.20 |
| **Impulsive Outliers (5σ)** | `0.9265` | `0.7610 ± 0.0236` | `+16.55 pp` | s* = 0.25 | s* = 0.10 |

- **Mandated Reporting Caption:**
  > *"Observed failure boundary under the specified experimental configuration."*

---

## 2. Experimental Invariants & Data Isolation

| Dimension | Experimental Specification | Protocol Guarantee |
|---|---|---|
| **Benchmark Dataset** | Fisher Iris ($N = 150$, 4 features, 3 classes) | Unaltered canonical benchmark |
| **Partitioning Strategy** | Stratified 80/20 train/test split (`split_seed = 42`) | **Frozen split** ($N_{\text{train}}=120$, $N_{\text{test}}=30$) |
| **Model Configuration** | `RandomForestClassifier(n_estimators=100, max_depth=None, criterion='gini')` | Identical tree capacity |
| **Statistical Suite** | 5 seeds: `[42, 123, 456, 789, 1011]` | Bessel's correction $ddof=1$, Student's $t$ CI with $\text{df}=4$ |
| **Reliability Criterion** | Strict failure if $\text{Macro-F1} < 0.80$ | Predefined threshold |
| **Diagnostic Flag** | Secondary flag if $\Delta_{\text{rel}} > 15.0\%$ | Predefined threshold |

---

## 3. Systematic Multi-Corruption Degradation Table

Comparison of Mean Macro-F1 with 95% Student's $t$ Confidence Intervals across all evaluated severity levels:

| Nominal Severity ($s$) | Additive Gaussian Noise | MCAR Missingness (Mean Imputed) | Impulsive Outliers (5σ) |
|---|---|---|---|
| `0.00` | `0.9265 [0.8917, 0.9613]` (0/5 failed) | `0.9265 [0.8917, 0.9613]` (0/5 failed) | `0.9265 [0.8917, 0.9613]` (0/5 failed) |
| `0.05` | `0.9332 [0.9039, 0.9626]` (0/5 failed) | `0.9131 [0.8759, 0.9502]` (0/5 failed) | `0.8919 [0.8564, 0.9275]` (0/5 failed) |
| `0.10` | `0.9332 [0.8916, 0.9747]` (0/5 failed) | `0.8876 [0.8420, 0.9332]` (0/5 failed) | `0.8582 [0.8038, 0.9126]` (1/5 failed) |
| `0.15` | `0.9132 [0.8660, 0.9604]` (0/5 failed) | `0.8489 [0.8141, 0.8838]` (0/5 failed) | `0.8582 [0.8038, 0.9126]` (1/5 failed) |
| `0.20` | `0.8991 [0.8465, 0.9517]` (0/5 failed) | `0.8034 [0.7384, 0.8685]` (2/5 failed) | `0.8268 [0.7710, 0.8826]` (2/5 failed) |
| `0.25` | `0.8912 [0.8537, 0.9288]` (0/5 failed) | `0.7779 [0.7419, 0.8140]` (3/5 failed) | `0.7811 [0.7385, 0.8237]` (4/5 failed) |
| `0.30` | `0.8538 [0.7755, 0.9320]` (1/5 failed) | `0.7434 [0.7026, 0.7841]` (5/5 failed) | `0.7610 [0.6956, 0.8265]` (4/5 failed) |

*Notes: Values formatted as `Mean [95% CI Lower, Upper]` with failure counts across $R=5$ seeds. Confidence intervals use Student's $t$-distribution with $\text{df} = 4$ ($t_{0.025, 4} = 2.7764$).*

---

## 4. Failure Boundary & Vulnerability Analysis

1. **Mean Performance Failure Boundary ($s^*_{\text{mean}}$):**
   - Gaussian Noise: Not observed within tested range ($s^* > 0.30$).
   - MCAR Missingness: Evaluated along missingness fraction $p_{\text{miss}} \in [0.00, 0.30]$.
   - Outlier Contamination: Evaluated along contamination fraction $p_{\text{outlier}} \in [0.00, 0.30]$.
2. **Individual-Run Boundary Dispersion ($s^*_{\text{indiv}}$):**
   - Tracks whether any individual stochastic PRNG draw breached the $\text{Macro-F1} < 0.80$ threshold.
3. **Mandated Caption:**
   > *"Observed failure boundary under the specified experimental configuration."*

---

## 5. Non-Equivalence & Calibration Discussion

- **Calibration Caveat:** Equal nominal severity values ($s = 0.10$) do **not** represent equal corruption strength across differing physical perturbation mechanisms:
  - In Gaussian noise, $s=0.10$ adds a subtle $0.1\sigma$ shift across all features.
  - In MCAR missingness, $s=0.10$ replaces $10\%$ of all feature cells with the training mean.
  - In Outliers, $s=0.10$ injects catastrophic $5\sigma$ spikes into $10\%$ of all feature cells.
- **Observational Constraint:** Cross-corruption performance rankings reflect empirical sensitivity under these calibrated mathematical definitions, not causal vulnerability.

---

## 6. Scientific Limitations & Threats to Validity

1. **Test Set Granularity:** With $N_{\text{test}} = 30$ samples (10 per class), a single misclassified sample alters accuracy and recall by $3.33\,\text{percentage points}$.
2. **Benchmark Scale:** The Iris dataset is small, low-dimensional ($D=4$), and possesses well-separated clusters; results do not directly extrapolate to high-dimensional or complex data modalities.
3. **Imputation Model Dependency:** For missingness, substituting training means is one of several operational imputation policies. A more sophisticated model (e.g. k-NN or iterative imputation) could exhibit different degradation profiles.
4. **No Causal Claim:** Identified sensitivities represent observational shifts under the defined operators, not causal mechanisms.

---

## 7. Deterministic Reproduction Statement

To deterministically reproduce this cross-corruption evaluation across all 5 seeds:
```bash
python scripts/experiments/run_e002.py
```
