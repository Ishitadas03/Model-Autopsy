# Experimental Design & Protocol Specification: E002

**Experiment ID:** `E002`  
**Experiment Title:** Comparative Empirical Robustness Evaluation Across Diverse Input Corruption Mechanisms (Gaussian Noise, MCAR Missingness, and Outlier Contamination) on the Iris Benchmark  
**Protocol Version:** 1.0.0  
**Parent Documents:** [`docs/research/problem_statement.md`](problem_statement.md), [`docs/research/experimental_protocol.md`](experimental_protocol.md)  
**Author:** Person 1 (ML & Research Lead)  
**Target Context:** Model Autopsy ML Engine  
**Status:** Proposal for Approval  

---

## 1. Step 1 Audit Findings & Discrepancy Resolution

### 1.1 Resolution of Diagnostic Threshold Discrepancy
- **Audit Target:** Predefined diagnostic threshold for relative performance degradation ($\Delta_{\text{rel}}$).
- **Findings Across Codebase & Configurations:**
  - `configs/experiments/e001.yaml` explicitly sets:
    ```yaml
    evaluation:
      primary_metric: "macro_f1"
      failure_threshold: 0.80
      strict_comparison: true
      relative_drop_diagnostic_threshold_pct: 15.0
    ```
  - `ml_engine/src/model_autopsy/metrics/evaluator.py` implements:
    ```python
    rel_drop_exceeds_15_pct = bool(relative_degradation_pct > 15.0)
    ```
  - `artifacts/experiments/E001/report.md` reports: `Rel Drop > 15% Flag`.
  - In the preceding Phase 2 summary conversation text, an incidental narrative typo referenced `10.0%` instead of `15.0%`.
- **Resolution:**
  - The actual, validated, and config-governed diagnostic threshold is strictly **$15.0\%$**.
  - Seed 123 under $s=0.30$ recorded a relative degradation of $20.15\%$, which correctly triggered the diagnostic flag under the true $15.0\%$ threshold ($20.15\% > 15.0\%$).
  - This design specification formally reaffirms the canonical threshold of **$15.0\%$** for all secondary diagnostic alerts.

### 1.2 Verification of Phase 2 Internal Consistency
- Sample standard deviations across all seeds correctly utilize Bessel's correction with degrees of freedom $ddof = 1$.
- Standard error of the mean correctly uses $\text{SEM} = S_M / \sqrt{5}$.
- Two-sided 95% Confidence Intervals correctly apply the Student's $t$ distribution with $\nu = R - 1 = 4$ degrees of freedom ($t_{0.025, 4} \approx 2.7764$).
- All calculations in `artifacts/experiments/E001_multi_seed/aggregate_results.csv` and `aggregate_results.json` match independent analytical recalculations.
- No existing E001 single-seed or multi-seed artifacts have been overwritten or modified.

---

## 2. Research Objective: RQ2

**Primary Research Question (RQ2):**  
> *"How do different types of input corruption (continuous additive Gaussian noise, discrete MCAR missingness with mean imputation, and impulsive outlier contamination) affect model reliability differently under controlled experimental conditions?"*

### Secondary Research Questions
1. Does the Random Forest classifier exhibit greater vulnerability to widespread low-magnitude perturbations (Gaussian noise) or sparse high-magnitude perturbations (outliers and missingness)?
2. At what discrete severity level $s^*$ (if any within $s \in [0.00, 0.30]$) does each corruption family trigger the primary failure threshold ($\text{Macro-F1} < 0.80$)?
3. How do the trajectories of degradation compare across corruption mechanisms (graceful linear decline vs. abrupt cliff effect)?

---

## 3. Shared Experimental Invariants (Preserved from E001)

To isolate corruption mechanism as the sole independent variable, all baseline parameters are frozen identically to E001:

| Dimension | Specification | E001 Parity |
|---|---|---|
| **Dataset** | Fisher Iris Benchmark ($N = 150$, 4 features, 3 classes) | Identical |
| **Data Partitioning** | Stratified 80/20 train/test split (`split_seed = 42`) | Identical ($N_{\text{train}}=120, N_{\text{test}}=30$) |
| **Model Family** | `RandomForestClassifier` (`n_estimators=100`, `max_depth=None`, `criterion='gini'`) | Identical |
| **Research Seed Suite** | $R = 5$ seeds: `[42, 123, 456, 789, 1011]` | Identical |
| **Primary Metric** | Macro-Averaged F1-Score ($\text{Macro-F1}$) | Identical |
| **Secondary Metrics** | Classification Accuracy, Per-Class F1/Precision/Recall, Confusion Matrix | Identical |
| **Failure Criterion** | Strict failure if $\text{Macro-F1} < 0.80$ | Identical |
| **Diagnostic Flag** | Secondary flag if $\Delta_{\text{rel}} > 15.0\%$ | Identical |
| **Severity Steps** | 7 discrete levels: $S = [0.00, 0.05, 0.10, 0.15, 0.20, 0.25, 0.30]$ | Identical grid |

---

## 4. Mathematical Formulation of Candidate Corruption Operators

### 4.1 Operator A: Additive Gaussian Noise (`gaussian_noise`)
- **Semantic Characterization:** Continuous isotropic measurement jitter or sensor noise.
- **Severity Parameter $s \in [0.00, 0.30]$:** Dimensionless scaling factor proportional to training standard deviation.
- **Formulation:**
  $$X'_{ij} = X_{ij} + \varepsilon_{ij}, \quad \varepsilon_{ij} \sim \mathcal{N}\left(0, (s \cdot \sigma_j^{\text{train}})^2\right)$$
  where $\sigma_j^{\text{train}}$ is estimated strictly on $X_{\text{train}}$ with $ddof=1$.
- **Severity-Zero Invariant:** $\varepsilon_{ij} = 0 \implies X' = X$.

### 4.2 Operator B: Missing Completely at Random (`feature_missingness_mcar`)
- **Semantic Characterization:** Sensor dropout, packet drop, or unrecorded measurement values.
- **Missingness Mechanism:** Missing Completely at Random (MCAR). Each evaluation cell $(i, j)$ has independent probability $p_{\text{miss}} = s$ of being unobserved:
  $$M_{ij} \sim \text{Bernoulli}(s), \quad s \in [0.00, 0.30]$$
- **Model Compatibility & Imputation Pipeline:**
  Standard `RandomForestClassifier` cannot process `np.nan` values. To prevent model failure while strictly avoiding test leakage, an explicit **training-fitted univariate mean imputer** is established:
  $$\mu_j^{\text{train}} = \frac{1}{N_{\text{train}}} \sum_{k=1}^{N_{\text{train}}} X_{kj}^{\text{train}}$$
  When cell $(i, j)$ is masked ($M_{ij} = 1$), it is replaced by $\mu_j^{\text{train}}$:
  $$\hat{X}_{ij} = \begin{cases} X_{ij} & \text{if } M_{ij} = 0 \\ \mu_j^{\text{train}} & \text{if } M_{ij} = 1 \end{cases}$$
- **Severity-Zero Invariant:** At $s = 0.00$, $P(M_{ij}=1) = 0 \implies M_{ij} = 0 \implies \hat{X} = X$.
- **Data Leakage Guarantee:** Imputation values $\boldsymbol{\mu}^{\text{train}}$ are calculated exclusively from $X_{\text{train}}$. $X_{\text{test}}$ is never used for parameter estimation.

### 4.3 Operator C: Feature Outlier Contamination (`feature_outliers`)
- **Semantic Characterization:** Impulsive physical disruptions, electrical spikes, or catastrophic measurement malfunctions.
- **Contamination Mechanism:** Each evaluation cell $(i, j)$ has independent probability $p_{\text{outlier}} = s$ of experiencing an extreme out-of-distribution spike:
  $$O_{ij} \sim \text{Bernoulli}(s), \quad s \in [0.00, 0.30]$$
- **Outlier Value Generation:**
  Contaminated entries are replaced with an extreme $5$-sigma displacement from the training mean:
  $$X'_{ij} = \begin{cases} X_{ij} & \text{if } O_{ij} = 0 \\ \mu_j^{\text{train}} + \delta_{ij} \cdot (5.0 \cdot \sigma_j^{\text{train}}) & \text{if } O_{ij} = 1 \end{cases}$$
  where $\delta_{ij} \in \{-1, +1\}$ with equal probability ($P(\delta_{ij}=+1) = 0.5$) driven by the isolated PRNG stream.
- **Severity-Zero Invariant:** At $s = 0.00$, $P(O_{ij}=1) = 0 \implies O_{ij} = 0 \implies X' = X$.
- **Data Leakage Guarantee:** Parameters $\boldsymbol{\mu}^{\text{train}}$ and $\boldsymbol{\sigma}^{\text{train}}$ are computed strictly on $X_{\text{train}}$.

---

## 5. Fair Comparison & Calibration Principles

### 5.1 Non-Equivalence Disclosure
Equal numerical severity ($s = 0.10$) across corruption operators does **not** signify equal physical or statistical corruption strength:
- In Gaussian noise, $s = 0.10$ perturbs **all $100\%$ of features** with a mild $\sigma/10$ standard deviation displacement.
- In MCAR missingness, $s = 0.10$ completely obliterates the identity of an expected **$10\%$ of feature entries**, substituting the training population mean.
- In Outlier contamination, $s = 0.10$ replaces an expected **$10\%$ of feature entries** with violent $5\sigma$ impulsive spikes.

### 5.2 Comparative Analysis Protocol
1. **Within-Type Trajectories:** Each corruption type is analyzed along its own progressive severity axis $s \in [0.00, 0.30]$ to assess monotonicity, stability, and failure boundary $s^*$.
2. **Between-Type Cross-Comparison:** Robustness comparison evaluates which corruption modality inflicts more severe performance degradation at commensurate nominal rates, illuminating the model's structural weaknesses (e.g., resilience to continuous noise vs. fragility to missing informative splits).
3. **Causal Caveat:** No causal claims regarding feature vulnerability will be inferred; all findings remain strictly observational empirical sensitivities.

---

## 6. Target Artifact Hierarchy (`artifacts/experiments/E002/`)

```
artifacts/experiments/E002/
├── config.yaml                    # Full experiment definition
├── manifest.json                  # Reproducibility manifest (environment, hashes, seeds)
├── aggregate_comparison.csv       # Unified table comparing Gaussian vs MCAR vs Outliers
├── aggregate_comparison.json      # Structured multi-seed statistical summaries
├── robustness_comparison.png      # Multi-curve comparison plot with 95% Student's t CI bands
├── report.md                      # Comprehensive empirical research report
├── corruptions/
│   ├── gaussian/                  # Per-seed results & summary for Gaussian noise
│   ├── missingness_mcar/          # Per-seed results & summary for MCAR missingness
│   └── outliers/                  # Per-seed results & summary for Outlier contamination
```

---

## 7. Protocol Compliance Checklist

- [x] Pre-experimental audit completed; diagnostic threshold affirmed as 15.0%.
- [x] Phase 2 internal consistency validated.
- [x] E001 single-seed and multi-seed artifacts safely isolated.
- [x] Imputation and outlier operators guarantee 0 data leakage (training parameters only).
- [x] Severity zero identity guarantee verified for all 3 operators.
- [x] Mathematical definitions explicitly stated.
- [x] Approval sought prior to code execution.
