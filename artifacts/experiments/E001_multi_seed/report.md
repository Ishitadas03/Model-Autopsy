# Empirical Research Report: E001 (Multi-Seed Evaluation)
> **Title:** Multi-Seed Statistical Characterization of Random Forest Robustness Under Additive Gaussian Noise on the Iris Benchmark  
> **Protocol Version:** 1.0.0 | **Execution Timestamp:** 2026-10-25 08:23:00 UTC  
> **Sample Size:** $R = 5$ Independent PRNG Seeds: `[42, 123, 456, 789, 1011]`  
> **Repository Context:** Model Autopsy ML Engine  

---

## 1. Executive Summary

- **Primary Research Question:** *"How does Gaussian input noise affect the Macro-F1 performance of a Random Forest classifier on the Iris dataset across repeated independent stochastic initializations?"*
- **Baseline Performance ($s = 0.00$):**
  - Mean Macro-F1: `0.9265 ± 0.0125` ($\text{SEM}$), 95% CI: `[0.8917, 0.9613]`
  - Mean Accuracy: `0.9267 ± 0.0125` ($\text{SEM}$)
- **Worst-Case Performance ($s = 0.30$):**
  - Mean Macro-F1: `0.8538 ± 0.0282` ($\text{SEM}$), 95% CI: `[0.7755, 0.9320]`
  - Mean Absolute Degradation: `7.28 pp`
- **Observed Mean Failure Boundary:** **Not observed within tested severity range (`s* > 0.30`)**
- **Earliest Individual Run Failure Boundary:** `s* = 0.30`
- **Mandated Reporting Caption:**
  > *"Observed failure boundary under the specified experimental configuration."*

---

## 2. Experimental & Statistical Protocol

| Component | Value / Specification |
|---|---|
| **Dataset** | Fisher Iris Benchmark ($N = 150$, 4 continuous features, 3 classes) |
| **Train/Test Partitioning** | Stratified 80/20 split (`split_seed = 42`, Frozen across all seeds) |
| **Partition Sample Counts** | $N_{\text{train}} = 120$ (40/class), $N_{\text{test}} = 30$ (10/class) |
| **Feature Dispersion ($\sigma_j$)** | Estimated strictly on $X_{\text{train}}$ partition using sample standard deviation ($ddof = 1$) |
| **Model Family** | `RandomForestClassifier` (100 trees, unconstrained depth, Gini criterion) |
| **Evaluated PRNG Seeds ($R=5$)** | `[42, 123, 456, 789, 1011]` |
| **Noise Formulation** | $\varepsilon_{ij} \sim \mathcal{N}(0, (s \cdot \sigma_j)^2)$, where $s \in [0.00, 0.30]$ |
| **Statistical Estimators** | Sample mean $\bar{M}(s)$, sample standard deviation $S_M(s)$ ($ddof=1$), $\text{SEM} = S_M / \sqrt{R}$ |
| **Confidence Interval** | Two-sided 95% Student's $t$-distribution with $R - 1 = 4$ degrees of freedom ($t_{0.025, 4} = 2.7764$) |
| **Reliability Criterion** | Strict failure if $\text{Macro-F1} < 0.80$ |

---

## 3. Multi-Seed Statistical Robustness Table

| Severity ($s$) | Mean Macro-F1 | Sample Std ($S_M$) | SEM | 95% Student's t CI | Mean Accuracy | Abs Drop (pp) | Run Failures | Status |
|---|---|---|---|---|---|---|---|---|
| `0.00` | `0.9265` | `±0.0280` | `±0.0125` | `[0.8917, 0.9613]` | `0.9267` | `+0.00 pp` | 0/5 (0.0%) | PASS |
| `0.05` | `0.9332` | `±0.0237` | `±0.0106` | `[0.9039, 0.9626]` | `0.9333` | `-0.67 pp` | 0/5 (0.0%) | PASS |
| `0.10` | `0.9332` | `±0.0335` | `±0.0150` | `[0.8916, 0.9747]` | `0.9333` | `-0.67 pp` | 0/5 (0.0%) | PASS |
| `0.15` | `0.9132` | `±0.0380` | `±0.0170` | `[0.8660, 0.9604]` | `0.9133` | `+1.33 pp` | 0/5 (0.0%) | PASS |
| `0.20` | `0.8991` | `±0.0424` | `±0.0190` | `[0.8465, 0.9517]` | `0.9000` | `+2.74 pp` | 0/5 (0.0%) | PASS |
| `0.25` | `0.8912` | `±0.0302` | `±0.0135` | `[0.8537, 0.9288]` | `0.8933` | `+3.53 pp` | 0/5 (0.0%) | PASS |
| `0.30` | `0.8538` | `±0.0630` | `±0.0282` | `[0.7755, 0.9320]` | `0.8600` | `+7.28 pp` | 1/5 (20.0%) | PASS |

*Notes: Sample standard deviation $S_M$ is computed strictly with $ddof=1$. Confidence intervals use Student's $t$-distribution with $\text{df} = 4$ ($t_{0.025, 4} = 2.7764$). Abs Drop indicates mean absolute degradation in percentage points.*

---

## 4. Per-Seed Performance & Boundary Breakdown

| Seed ($r$) | Baseline Macro-F1 ($s=0$) | Worst Macro-F1 Observed | Observed Failure Boundary ($s^*$) |
|---|---|---|---|
| `42` | `0.8997` | `0.8653` (at `s=0.30`) | `s* > 0.30` (Unobserved) |
| `123` | `0.9333` | `0.7452` (at `s=0.30`) | `s* = 0.30` |
| `456` | `0.9666` | `0.8977` (at `s=0.30`) | `s* > 0.30` (Unobserved) |
| `789` | `0.8997` | `0.8624` (at `s=0.25`) | `s* > 0.30` (Unobserved) |
| `1011` | `0.9333` | `0.8982` (at `s=0.30`) | `s* > 0.30` (Unobserved) |

---

## 5. Failure Boundary Characterization

- **Mean Performance Failure Boundary:** **Not observed within tested severity range (`s* > 0.30`)**
- **Individual-Run Boundary Dispersion:** `s* = 0.30`
- **Methodological Distinction:**
  The aggregate failure boundary evaluates whether the *sample mean* $\bar{M}(s)$ crosses the reliability threshold ($0.80$), whereas per-seed boundaries track whether any *individual stochastic realization* crossed the boundary.
- **Mandated Reporting Caption:**
  > *"Observed failure boundary under the specified experimental configuration."*

---

## 6. Monotonicity & Trend Analysis

- **Strict Monotonic Decay Across All Severities:** `No`
- **Diagnostic Finding:**
  Monotonic decay holds if each step exhibits non-increasing mean performance. Minor non-monotonic increases at low severity can occur when isotropic noise incidentally shifts ambiguous borderline points toward true class clusters.

---

## 7. Scientific Limitations & Threats to Validity

1. **Small Sample Benchmark:** The Iris dataset contains only 150 instances and 4 features. High robustness observed on Iris cannot be generalized to complex vision, speech, or high-dimensional tabular data.
2. **Discretization Uncertainty:** In a 30-sample test partition, a single classification shift produces a $3.33\,\text{pp}$ metric change.
3. **Synthetic Corruption:** Isotropic additive Gaussian noise is a continuous perturbation model that does not capture structured sensor outages, distribution drift, or adversarial perturbations.
4. **Non-Causal Interpretability:** Feature rankings and metric shifts represent observational sensitivity under the tested perturbation protocol, not causal mechanisms.

---

## 8. Reproducibility Statement

To deterministically reproduce this 5-seed research evaluation:
```bash
python scripts/experiments/run_e001.py --multi-seed
```
