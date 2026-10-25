# Empirical Research Report: E001
> **Title:** Empirical Characterization of Random Forest Classifier Robustness Under Additive Gaussian Feature Noise on the Iris Benchmark  
> **Protocol Version:** 1.0.0 | **Execution Timestamp:** 2026-10-25 08:22:56 UTC  
> **Repository Context:** Model Autopsy ML Engine  

---

## 1. Executive Summary

- **Primary Research Question:** *"How does Gaussian input noise affect the Macro-F1 performance of a Random Forest classifier on the Iris dataset?"*
- **Baseline Performance ($s = 0.00$):** Macro-F1 = `0.8997`, Accuracy = `0.9000`
- **Worst-Case Performance ($s = 0.30$):** Macro-F1 = `0.8653` (Absolute degradation = `3.44 pp`)
- **Observed Failure Boundary ($s^*$):** **Not observed within tested severity range (`s* > 0.30`)**
- **Mandated Boundary Caption:**
  > *"Observed failure boundary under the specified experimental configuration."*

---

## 2. Experimental Configuration

| Component | Value / Specification |
|---|---|
| **Dataset** | Fisher Iris Benchmark (150 instances, 4 features, 3 classes) |
| **Train/Test Partitioning** | Stratified 80/20 split (`split_seed = 42`, Frozen) |
| **Sample Counts** | $N_{\\text{train}} = 120$ (40/class), $N_{\\text{test}} = 30$ (10/class) |
| **Feature Standard Deviations ($\sigma_j$)** | Estimated strictly on $X_{\\text{train}}$ ($ddof=1$) |
| **Model Family** | `RandomForestClassifier` (100 estimators, unconstrained depth, Gini criterion) |
| **Model PRNG Seed** | `model_seed = 42` |
| **Noise Formulation** | $\\varepsilon_{ij} \\sim \\mathcal{N}(0, (s \\cdot \\sigma_j)^2)$, where $s \\in [0.00, 0.30]$ |
| **Reliability Criterion** | Strict failure if $\\text{Macro-F1} < 0.80$ |

---

## 3. Systematic Robustness Degradation Results

| Severity ($s$) | Macro-F1 | Accuracy | Abs Degradation (pp) | Rel Degradation (%) | Status | Rel Drop > 15% Flag |
|---|---|---|---|---|---|---|
| `0.00` | `0.8997` | `0.9000` | `+0.00 pp` | `+0.00%` | PASS | No |
| `0.05` | `0.9333` | `0.9333` | `-3.36 pp` | `-3.73%` | PASS | No |
| `0.10` | `0.9333` | `0.9333` | `-3.36 pp` | `-3.73%` | PASS | No |
| `0.15` | `0.8997` | `0.9000` | `+0.00 pp` | `+0.00%` | PASS | No |
| `0.20` | `0.8997` | `0.9000` | `+0.00 pp` | `+0.00%` | PASS | No |
| `0.25` | `0.8997` | `0.9000` | `+0.00 pp` | `+0.00%` | PASS | No |
| `0.30` | `0.8653` | `0.8667` | `+3.44 pp` | `+3.82%` | PASS | No |

*Note: Absolute degradation is reported in percentage points (pp). Relative degradation represents percentage drop relative to baseline Macro-F1.*

---

## 4. Empirical Feature Vulnerability Analysis

Features perturbed independently at $s = 0.20$ to quantify relative empirical sensitivity:

| Rank | Feature Name | Macro-F1 Drop (pp) | Isolated Macro-F1 |
|---|---|---|---|
| 1 | `sepal length (cm)` | `0.00 pp` | `0.8997` |
| 2 | `sepal width (cm)` | `0.00 pp` | `0.8997` |
| 3 | `petal length (cm)` | `0.00 pp` | `0.9333` |
| 4 | `petal width (cm)` | `0.00 pp` | `0.9333` |

> **Mandated Sensitivity Caveat:** *"Empirical sensitivity — not a causal explanation."*

---

## 5. Failure Boundary Characterization

- **Threshold Setting:** $\\text{Macro-F1} < 0.80$
- **Observed Failure Boundary ($s^*$):** **Not observed within tested severity range (`s* > 0.30`)**
- **Diagnostic Finding:** Failure boundary not observed within tested severity range (s* > 0.30). Model maintained macro_f1 >= 0.80 across all tested levels.
- **Mandated Reporting Caption:**
  > *"Observed failure boundary under the specified experimental configuration."*

---

## 6. Scientific Limitations & Threats to Validity

1. **Test Set Granularity:** With $N_{\\text{test}} = 30$ samples (10 per class), a single misclassified sample alters accuracy and recall by $3.33\\,\\text{percentage points}$.
2. **Benchmark Scale:** The Iris dataset is small, low-dimensional ($D=4$), and possesses well-separated clusters; results do not directly extrapolate to high-dimensional or complex data modalities.
3. **Perturbation Model:** Additive Gaussian noise is a synthetic perturbation that does not represent structured corruptions or adversarial attacks.
4. **Non-Causal Sensitivity:** Feature rankings describe observational sensitivity under this perturbation, not causal mechanisms.

---

## 7. Reproducibility Statement

The development experiment was executed with single-seed isolation (`seed = 42`).  
To deterministically reproduce this exact run:
```bash
python scripts/experiments/run_e001.py --seed 42
```
Full multi-seed statistical evaluation suite ($R=5$ seeds: `[42, 123, 456, 789, 1011]`) is specified for future research extensions.
