# Independent Scientific Audit: Experiment E004 (RQ7 Failure Pattern Analysis)

**Document ID:** `AUDIT-E004-RQ7-20261025`  
**Auditor Role:** Independent ML Research Auditor and Statistical Verification Specialist  
**Target:** Model Autopsy Phase 6 (Experiment E004)  
**Parent Specification:** [`docs/research/e004_experimental_design.md`](e004_experimental_design.md)  
**Implementation Report:** [`docs/research/e004_implementation_report.md`](e004_implementation_report.md)  
**Audit Date:** 2026-10-25  
**Audit Status:** Complete  

---

## Executive Summary & Formal Verdict

An independent, evidence-based scientific audit of **Experiment E004** was conducted to verify whether the implementation, raw prediction records, statistical derivations, and scientific conclusions are mathematically sound, faithful to the pre-registered protocol, and reproducible from stored artifacts.

Every reported number was independently recomputed from raw data without relying on summary files. All 315 evaluation cells were audited against E003 baseline results, and all 9,450 atomic sample prediction events were verified for consistency, calibration, and evidence conservation.

### Formal Audit Verdict: **PASS WITH WARNINGS**

```
========================================================================================
E004 SCIENTIFIC AUDIT VERDICT SCORECARD
========================================================================================
[PASS]  Raw Evidence Integrity:       9,450 records, unique keys, valid schema, no fabrication
[PASS]  Evidence Conservation:        315 / 315 cells satisfy sum(e_i) == sum(C_jk) (100.0%)
[PASS]  E003 Parity:                  315 / 315 confusion matrices match bit-for-bit (100.0%)
[PASS]  H1 Class Vulnerability:       Confirmed: Setosa 0.0% clean, Sample 25 consensus error
[PASS]  H2 Error Persistence:         Confirmed: Mean EPR = 0.9390, 89.0% perfect persistence
[PASS]  H3 Inter-Model Concordance:   Confirmed: Jaccard RF/LR=0.3648, RF/GB=0.4486, LR/GB=0.3297
[PASS]  H4 Mahalanobis Margins:       Confirmed: Early 1.0306 vs Resilient 6.1342 (p = 0.000030)
[PASS]  H5 Cross-Seed Stability:      Confirmed: Mutually exclusive & exhaustive partition (N=30)
[PASS]  Automated Test Suite:         70 / 70 tests passing (zero regressions across E001-E004)
----------------------------------------------------------------------------------------
[WARN]  Warning 1 (H1 Reporting):     Clopper-Pearson CI uses n_k=10 instead of pooled N=450
[WARN]  Warning 2 (H2 Nomenclature):  "Absorbing state" is an empirical metaphor (11% escape)
[WARN]  Warning 3 (H3 Scope):         "23 consensus failures" is a multi-seed union intersection
[WARN]  Warning 4 (H4 Geometry):      Mahalanobis margin is centroid-based, not decision boundary
========================================================================================
OVERALL AUDIT VERDICT: PASS WITH WARNINGS
Phase 6 is scientifically validated and cleared for formal completion subject to documented warnings.
========================================================================================
```

---

## 1. Audit of Raw Evidence, Schema, & E003 Reproduction

### 1.1 Tensor Factorization & Uniqueness Audit
The primary raw evidence was audited from [`sample_predictions.json`](file:///c:/Users/ishit/Model-Autopsy/artifacts/experiments/E004/sample_predictions.json) and [`sample_level_metrics.csv`](file:///c:/Users/ishit/Model-Autopsy/artifacts/experiments/E004/sample_level_metrics.csv):

- **Atomic Record Count:** Exactly 9,450 records in both JSON and CSV files.
- **Factorization:** $3\text{ models} \times 3\text{ corruptions} \times 5\text{ seeds} \times 7\text{ severities} \times 30\text{ test samples} = 9{,}450$.
- **Unique Event Keys:** Evaluated tuples $(\text{model\_id}, \text{corruption\_id}, \text{seed}, \text{severity}, \text{sample\_id})$. The set cardinality is exactly 9,450. Zero duplicate event keys exist.
- **Ground Truth Invariance:** For every `sample_id` $i \in [0, 29]$, `true_label` and `iris_dataset_index` are 100% identical across all 315 evaluation occurrences and match the canonical Iris stratified test partition from `iris.py` (`split_seed = 42`).
- **Error Flag Calibration:** `is_error == (predicted_label != true_label)` holds across 100% of the 9,450 records.
- **Probability Vectors:** For all records containing probabilities, arrays have length 3, sum to $1.0 \pm 10^{-4}$, and satisfy $\arg\max(\mathbf{p}) \equiv \text{predicted\_label}$.

### 1.2 Evidence Conservation Identity
For each of the 315 evaluation cells, the confusion matrix $C_{\text{rec}} \in \mathbb{N}^{3 \times 3}$ was recomputed by summing atomic sample indicators:
$$C_{\text{rec}}[j, k] = \sum_{i=0}^{29} \mathbb{I}(y_i = j \land \hat{y}_i = k)$$
The internal evidence conservation identity was verified:
$$\sum_{j \ne k} C_{\text{rec}}[j, k] \equiv \sum_{i=0}^{29} \mathbb{I}(\hat{y}_i \ne y_i)$$
**Audit Verification:** 315 / 315 cells (100.0%) satisfied exact evidence conservation with zero numerical discrepancy.

### 1.3 Bit-for-Bit Reproduction of Experiment E003
Every reconstructed confusion matrix $C_{\text{rec}}$ was checked against the corresponding matrix stored in `artifacts/experiments/E003/`:
- **Evaluation Cells Checked:** 315 cells.
- **Exact Bit-for-Bit Matches:** 315 / 315 (100.0%).
- **Categorical / Numerical Mismatches:** 0.

**Finding:** E004 faithfully reproduces the canonical E003 experimental protocol down to the exact individual sample prediction. No historical artifacts were overwritten.

---

## 2. Audit of Hypothesis H1: Class Vulnerability Asymmetry

### 2.1 Recomputed Class Error Rates
Class error rates were independently recomputed from raw prediction records:

| Class | Sample Count ($n_k$) | Clean Error Rate ($s=0.00$) | Max Severity Rate ($s=0.30$) | Worst Modality Rate ($s=0.30$, Outliers) |
| :--- | :---: | :---: | :---: | :---: |
| **Setosa** | 10 | **0 / 450 (0.00%)** | 78 / 450 (17.33%) | 78 / 150 (52.00%) |
| **Versicolor** | 10 | **45 / 450 (10.00%)** | 123 / 450 (27.33%) | 72 / 150 (48.00%) |
| **Virginica** | 10 | **33 / 450 (7.33%)** | 108 / 450 (24.00%) | 75 / 150 (50.00%) |

### 2.2 Consensus Baseline-Error Instance
- **Sample Index 25** (Iris dataset row `77`, True class: `1 = versicolor`):
  - In clean space ($s = 0.00$), Sample 25 is misclassified in **45 out of 45 evaluations (100.0%)**.
  - In all 45 evaluations, it is predicted as **Class 2 (`virginica`)**.
  - This confirms the existence of a universal baseline consensus error on the overlapping Versicolor/Virginica boundary across Random Forest, Logistic Regression, and Gradient Boosting.
- **Sample Index 23** (Iris dataset row `134`, True class: `2 = virginica`):
  - Misclassified by `logistic_regression` in 15 / 15 clean evaluations (100.0%).
  - Misclassified by `random_forest` in 12 / 15 clean evaluations (80.0%).
  - Misclassified by `gradient_boosting` in **0 / 15 clean evaluations (0.0%)**.
  - This demonstrates algorithm-specific clean boundary separation: Gradient Boosting correctly isolates Sample 23, whereas Logistic Regression fails consistently.

### 2.3 Warning 1: Clopper-Pearson Denominator Aggregation Level
> [!WARNING]
> **Warning 1: Clopper-Pearson Confidence Interval Denominator Ambiguity**  
> In [`report.md`](file:///c:/Users/ishit/Model-Autopsy/artifacts/experiments/E004/report.md#L41-L46), the reported 95% Clopper-Pearson confidence intervals for class error rates are:
> - Setosa: $[0.0000, 0.3085]$ (corresponding to $k=0, n=10$).
> - Versicolor: $[0.0667, 0.6525]$ (corresponding to $k=3, n=10$).
> - Virginica: $[0.0252, 0.5561]$ (corresponding to $k=2, n=10$).
>
> These intervals are computed assuming a single-evaluation test partition sample size ($n_k = 10$). If calculated over the pooled evaluation set across 5 seeds and 3 models ($n = 450$), the exact Clopper-Pearson intervals would be significantly tighter:
> - Setosa Clean: $[0.0000, 0.0082]$ ($k=0, n=450$).
> - Versicolor Clean: $[0.0739, 0.1317]$ ($k=45, n=450$).
> - Virginica Clean: $[0.0511, 0.1022]$ ($k=33, n=450$).
>
> **Scientific Remediation:** The report correctly captures single-run uncertainty ($n_k=10$), but it must explicitly specify that $n=10$ was the denominator used so readers do not confuse single-run sampling error with multi-seed estimation variance.

---

## 3. Audit of Hypothesis H2: Error Persistence & Oscillation

### 3.1 Recomputed Persistence Estimands
Across all $3 \times 3 \times 5 \times 30 = 1{,}350$ sample trajectories:
- **Never-Failing Trajectories ($s^* = \text{None}$):** 1,006 / 1,350 (**74.52%**). Properly assigned $s^* = \text{None}, \text{EPR} = \text{None}, \text{POC} = 0$.
- **Max-Severity First Failures ($s^* = 0.30$):** 55 / 1,350 (**4.07%**). Properly assigned $\text{EPR} = 1.0$.
- **Valid Failing Trajectories:** 344 trajectories.
- **Mean Error Persistence Ratio (EPR):** **0.9390** (Recomputed from raw predictions: $\frac{1}{344} \sum \text{EPR}_i = 0.939023$).
- **Perfect Persistence ($\text{EPR} = 1.0$):** 306 / 344 (**88.95%**).

### 3.2 Prediction Oscillation Count (POC) Distribution
The distribution of prediction label changes across the 7 severity steps ($s_0 \to s_1 \to \dots \to s_6$) was audited:
- $\text{POC} = 0$ (Constant prediction throughout): 1,062 trajectories (78.67%).
- $\text{POC} = 1$ (Single permanent transition): 264 trajectories (19.56%).
- $\text{POC} = 2$ (Two transitions): 20 trajectories (1.48%).
- $\text{POC} = 3$ (Three transitions): 4 trajectories (0.30%).
- Trajectories with $\text{POC} > 1$ (Fluctuating): 24 / 1,350 (**1.78%**).

### 3.3 Warning 2: Theoretical Precision of "Absorbing States"
> [!WARNING]
> **Warning 2: "Absorbing State" is an Empirical Metaphor, Not a Markov Guarantee**  
> In [`report.md`](file:///c:/Users/ishit/Model-Autopsy/artifacts/experiments/E004/report.md#L27) and [`e004_implementation_report.md`](file:///c:/Users/ishit/Model-Autopsy/docs/research/e004_implementation_report.md#L173), failures are characterized as "absorbing error states."
>
> In Markov chain theory, an absorbing state is a state that, once entered, cannot be left ($P(X_{t+1} = i \mid X_t = i) \equiv 1.0$). Here, the raw empirical data demonstrates that **11.05% of failing sample trajectories (38 / 344) exhibit non-absorbing behavior**:
> - Some samples fail at $s=0.10$, recover correct classification at $s=0.15$, and fail again at $s=0.20$.
> - This occurs because multi-dimensional continuous noise $\mathbf{x} + s \cdot \mathbf{v}$ or cell imputation can transiently push a point back across non-linear boundaries.
>
> **Scientific Remediation:** The term "absorbing state" must be qualified as an *empirical approximation* or *high-persistence attractor* (mean $\text{EPR} = 0.939$), not a strict mathematical guarantee.

---

## 4. Audit of Hypothesis H3: Inter-Model Concordance

### 4.1 Recomputed Pairwise Jaccard Similarities
At maximum severity ($s = 0.30$), pairwise Jaccard error-set similarities were recomputed across all corruptions and seeds:
- **Random Forest vs Logistic Regression:** Mean $J = \mathbf{0.3648}$ (range: 0.1250 to 0.5882).
- **Random Forest vs Gradient Boosting:** Mean $J = \mathbf{0.4486}$ (range: 0.1875 to 0.7059).
- **Logistic Regression vs Gradient Boosting:** Mean $J = \mathbf{0.3297}$ (range: 0.1111 to 0.5882).

Tree-based ensembles (RF and GB) exhibit significantly higher pairwise error concordance ($J = 0.4486$) than linear models paired with ensembles ($J = 0.3297$ to $0.3648$), confirming that inductive bias shapes corruption vulnerability.

### 4.2 Warning 3: Definition of the "23 Consensus Failures"
> [!WARNING]
> **Warning 3: Ambiguity in the "23 Consensus Failures" Estimand**  
> In [`report.md`](file:///c:/Users/ishit/Model-Autopsy/artifacts/experiments/E004/report.md#L29) and [`failure_patterns_summary.json`](file:///c:/Users/ishit/Model-Autopsy/artifacts/experiments/E004/failure_patterns_summary.json), the text reports:
> > *"All three model families share a core consensus error set of 23 boundary samples under worst-case corruption."*
>
> Independent verification reveals that **in any single evaluation run** (a single seed and corruption at $s=0.30$), the simultaneous 3-model error set intersection $\mathcal{E}_{\text{RF}} \cap \mathcal{E}_{\text{LR}} \cap \mathcal{E}_{\text{GB}}$ has:
> - **Mean:** 2.87 samples
> - **Min:** 0 samples
> - **Max:** 6 samples
>
> The number **23** is obtained by taking the **intersection of the multi-seed error unions across all corruptions and seeds at $s=0.30$**:
> $$\mathcal{E}_{\text{RF}}^{\text{pooled}} = \bigcup_{c, r} \mathcal{E}_{\text{RF}}(s=0.30) \quad (26\text{ samples})$$
> $$\mathcal{E}_{\text{LR}}^{\text{pooled}} = \bigcup_{c, r} \mathcal{E}_{\text{LR}}(s=0.30) \quad (29\text{ samples})$$
> $$\mathcal{E}_{\text{GB}}^{\text{pooled}} = \bigcup_{c, r} \mathcal{E}_{\text{GB}}(s=0.30) \quad (25\text{ samples})$$
> $$\mathcal{E}_{\text{consensus}}^{\text{pooled}} = \mathcal{E}_{\text{RF}}^{\text{pooled}} \cap \mathcal{E}_{\text{LR}}^{\text{pooled}} \cap \mathcal{E}_{\text{GB}}^{\text{pooled}} = \{0, 1, 2, 3, 5, 8, 9, 11, 12, 13, 14, 16, 17, 18, 19, 20, 22, 23, 24, 25, 26, 27, 29\} \quad (23\text{ samples})$$
>
> **Scientific Remediation:** The report must clearly state that the 23 instances represent the *multi-condition pooled union intersection*, rather than implying that all 3 models failed 23 samples concurrently in a single evaluation run.

---

## 5. Audit of Hypothesis H4: Mahalanobis Margins & Boundary Inference

### 5.1 Training Covariance & Margin Recomputation
The Mahalanobis distance calculation was audited for data leakage and mathematical accuracy:
- **Leakage Audit:** Class centroids $\mu_k$ ($k \in \{0, 1, 2\}$) and pooled covariance $\Sigma_{\text{pooled}}$ were recomputed strictly on $X_{\text{train}}$ ($N_{\text{train}} = 120, K = 3$):
  $$\Sigma_{\text{pooled}} = \frac{1}{117} \sum_{k=0}^2 \sum_{i \in \text{train}_k} (\mathbf{x}_i - \mu_k)(\mathbf{x}_i - \mu_k)^T$$
- **Numerical Conditioning:** $\Sigma_{\text{reg}} = \Sigma_{\text{pooled}} + 10^{-6}\mathbf{I}$ has condition number $\kappa \approx 31.4$, guaranteeing stable inversion.
- **Opposing Centroid Margin:** $\Delta_M(\mathbf{x}_i) = \min_{k \ne y_i} d_M(\mathbf{x}_i, \mu_k) - d_M(\mathbf{x}_i, \mu_{y_i})$.

### 5.2 Recomputed Statistical Contrasts across All Three Models
Contrasting early-failing instances ($s^* \le 0.15$) against resilient instances ($s^* > 0.30$) under canonical Gaussian noise:

| Model Architecture | Early Group Size ($n_1$) | Early Mean Margin $\Delta_M$ | Resilient Group Size ($n_2$) | Resilient Mean Margin $\Delta_M$ | Mann-Whitney $U$ | Exact $p$-value | Rank-Biserial Effect Size ($r$) |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **Random Forest** | 6 | **1.0306** | 18 | **6.1342** | **2.0** | **0.000030** | **0.9630** |
| **Gradient Boosting** | 7 | **1.1432** | 16 | **6.2886** | **1.0** | **0.000008** | **0.9821** |
| **Logistic Regression** | 3 | **0.8616** | 21 | **5.7684** | **1.0** | **0.000988** | **0.9683** |

### 5.3 Multiple Testing Correction Audit
Testing Family 3 (Margin Disparity across the 3 models):
- $p_{(1)} = 0.000008 \le \frac{1}{3} \times 0.05 = 0.0167$ (Significant)
- $p_{(2)} = 0.000030 \le \frac{2}{3} \times 0.05 = 0.0333$ (Significant)
- $p_{(3)} = 0.000988 \le \frac{3}{3} \times 0.05 = 0.0500$ (Significant)

All three models survive both Benjamini-Hochberg FDR control ($q = 0.05$) and Bonferroni-Holm family-wise error rate control ($\alpha = 0.05$).

### 5.4 Warning 4: Distance to Centroids vs True Decision Boundary
> [!WARNING]
> **Warning 4: Centroid-Based Margin is a Feature-Space Proxy, Not the Actual Decision Boundary**  
> In [`report.md`](file:///c:/Users/ishit/Model-Autopsy/artifacts/experiments/E004/report.md#L31), the margin $\Delta_M$ is described as measuring "decision boundary proximity."
>
> The metric $\Delta_M(\mathbf{x}_i)$ computes the difference in Mahalanobis distance to class **centroids**. While for a linear discriminant analysis (LDA) classifier the decision boundary is identical to the midpoint between centroids under pooled covariance, **Random Forest and Gradient Boosting construct non-linear, hyper-rectangular step boundaries**.
>
> **Scientific Remediation:** The report must clearly state that $\Delta_M$ measures *feature-space geometric separation relative to training centroids*, which serves as an empirical proxy for boundary proximity, rather than the exact orthogonal step boundary of tree ensembles.

---

## 6. Audit of Hypothesis H5: Cross-Seed Failure Stability

### 6.1 Mutually Exclusive & Exhaustive Partitioning
For each of the 9 evaluation conditions (3 models $\times$ 3 corruptions at $s = 0.15$), the cross-seed failure frequency $\Phi(i) = \frac{1}{5} \sum_{r=1}^5 \mathbb{I}(\hat{y}_{i,r} \ne y_i)$ was evaluated:
- **Core Hard Failures:** $\Phi(i) \ge 0.80$ ($\ge 4$ seeds).
- **Seed-Vulnerable Failures:** $0.20 \le \Phi(i) \le 0.60$ (1 to 3 seeds).
- **Resilient Instances:** $\Phi(i) = 0.00$ (0 seeds).

**Audit Verification:** In all 9 conditions, the sum of sample counts across the three categories equals exactly 30 ($N_{\text{test}} = 30$). Partitioning is 100% mutually exclusive and exhaustive.

### 6.2 Key Modality Sensitivity Discrepancy
- Under Gaussian noise:
  - Random Forest: 1 Core Hard, 5 Seed-Vulnerable, 24 Resilient.
  - Logistic Regression: 1 Core Hard, 2 Seed-Vulnerable, 27 Resilient.
- Under Impulsive Outliers ($5\sigma$):
  - Logistic Regression: 1 Core Hard, **25 Seed-Vulnerable**, 4 Resilient.
  - This demonstrates that Logistic Regression is highly unstable across seeds under impulsive contamination (83.3% of the test partition fluctuates depending on the outlier mask seed).

---

## 7. Artifact Provenance, Plot Verification, & Git Audit

### 7.1 Provenance & SHA-256 Checksums
All files in `artifacts/experiments/E004/` were checked for SHA-256 integrity:

| Artifact | Size | SHA-256 Digest | Audit Status |
| :--- | :---: | :--- | :---: |
| `sample_predictions.json` | 3,879,281 bytes | `1aa7a2146235e570cce1cbb94d508e604f76aa4efef58c73d9dff43067cafdd1` | VERIFIED |
| `failure_patterns_summary.json` | 105,637 bytes | `a8723d737ad186326168ef97980313cb1e8eaecfca4f09d3da14cf67b4002416` | VERIFIED |
| `sample_level_metrics.csv` | 758,817 bytes | `f7957019fa7cedf9226cf72ebc7476839352e00885e50956b9c9704062e80600` | VERIFIED |
| `manifest.json` | 4,458 bytes | `d6e5a849650b6d9203a5c2b3e89547d6ba2f58eebc47a544976a161846cbb73a` | VERIFIED |
| `report.md` | 6,818 bytes | `648aa51122e06a5a2bb60fa392bead88b85b9be70f97973c5cf8c439db5e9b3f` | VERIFIED |
| `failure_patterns_analysis.png` | 701,948 bytes | `be8f56d254abe90f421115ef61a052fa97ea4f9c212269a941549ee1c955a595` | VERIFIED |

### 7.2 Plot Inspection (`failure_patterns_analysis.png`)
The generated 4-panel figure was audited:
- **Panel A:** Class error rates match reported numbers (Setosa stays flat at 0.0% until outliers, Versicolor/Virginica degrade rapidly).
- **Panel B:** EPR histogram matches valid EPR distribution with peak at $\text{EPR} = 1.0$ and vertical dashed line at mean EPR $0.94$.
- **Panel C:** Pairwise Jaccard curves agree with computed values across the 7 severity steps.
- **Panel D:** 2D PCA projection depicts Iris classes with consensus failures clearly marked on the boundary between classes 1 and 2.
- **Captions:** Contains verbatim required non-causal disclosures and sample size disclosures ($N_{\text{test}} = 30, n_k = 10$).

### 7.3 Git Tree Cleanliness
`git status` confirms:
- Zero staged changes (`git add` was not executed).
- Zero commits created (`HEAD` is unmodified at `6cc9887`).
- Zero pushes executed.
- Frontend directory `frontend/` is completely untouched.
- Pre-existing artifacts in `artifacts/experiments/E001/`, `E002/`, `E003/` remain bit-for-bit identical.

---

## 8. Final Audit Conclusions & Next Steps

### 8.1 Completion Status of Phase 6
Phase 6 (RQ7 Failure Pattern Analysis) has met all scientific, mathematical, and implementation criteria:
1. Per-sample evaluation data was captured without fabricating missing retrospective data.
2. Evidence conservation holds across all 315 evaluation cells.
3. E003 baseline results were reproduced with 100% exact parity.
4. All five hypotheses H1–H5 are supported by reproducible empirical calculations.
5. All automated unit and protocol tests pass (70 / 70 tests).

Phase 6 is formally declared **COMPLETE WITH DOCUMENTED WARNINGS**.

### 8.2 Recommended Next Step for RQ4 (Failure Boundary Analysis)
With microscopic sample-level failure data now fully validated, Model Autopsy has the requisite foundations to address **RQ4**:
> *"RQ4: How can we mathematically formalize and empirically locate the precise critical boundary where a machine learning model undergoes catastrophic failure?"*

**Recommended Execution Steps for RQ4:**
1. Formulate a continuous interpolation or root-finding estimator (e.g., bisection or logistic spline fitting) over severity $s$ to locate the exact crossing point $s^*$ where $\text{Macro-F1}(s) = 0.80$, rather than relying on grid discretization ($s \in \{0.00, 0.05, \dots, 0.30\}$).
2. Connect the sample-level first-error severity $s^*(i)$ from E004 to the global aggregate failure boundary $s^*_{\text{macro}}$ from E001–E003.
3. Formulate the official **E005 Experimental Design** in `docs/research/e005_experimental_design.md` prior to implementation.
