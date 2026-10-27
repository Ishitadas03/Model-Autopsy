# Experimental Design & Preregistration Protocol: E005
## RQ3: Empirical Feature Vulnerability Analysis Under Coordinate-Isolated Perturbations

**Experiment ID:** `E005`  
**Experiment Title:** Empirical Feature-Level Vulnerability and Sensitivity Ranking Under Coordinate-Isolated Stress Operators on the Iris Benchmark  
**Research Question:** **RQ3 — Which individual input features are most associated with model performance degradation under controlled feature-level perturbations?**  
**Protocol Version:** 1.0.0 (Preregistered Experimental Specification)  
**Parent Documents:**
- [`docs/research/problem_statement.md`](problem_statement.md)
- [`docs/research/experimental_protocol.md`](experimental_protocol.md)
- [`docs/research/e002_experimental_design.md`](e002_experimental_design.md)
- [`docs/research/phase3_scientific_audit.md`](phase3_scientific_audit.md)
- [`docs/research/e003_experimental_design.md`](e003_experimental_design.md)
- [`docs/research/e004_experimental_design.md`](e004_experimental_design.md)
- [`docs/research/e004_scientific_audit.md`](e004_scientific_audit.md)
- [`docs/research/project_completion_audit.md`](project_completion_audit.md)  
**Target Subsystem:** `ml_engine` (Model Autopsy Core Framework)  
**Status:** Preregistration Specification (Pre-Implementation Freeze)  

---

## 1. Research Question and Scope

### 1.1 Formal Definition of RQ3
In Experiments E001 through E004, Model Autopsy evaluated model degradation when perturbations were applied isotropically or uniformly across the entire input feature space $\mathbb{R}^D$ (where $D=4$). While these experiments characterized aggregate model resilience (RQ1), corruption modality divergence (RQ2), cross-architecture inductive bias differences (RQ5), and sample-level decision boundary failures (RQ7), they treated the feature vector as an undifferentiated unit.

**Research Question 3 (RQ3)** isolates the input coordinate space:
> *"Which individual input features are most associated with model performance degradation when subjected to controlled, coordinate-isolated perturbations, and how stable are empirical feature vulnerability rankings across model architectures, random seeds, and perturbation modalities?"*

### 1.2 Essential Scientific Distinctions
To maintain experimental validity and prevent unjustified interpretative leaps, this protocol enforces three formal conceptual boundaries:

1. **Feature Vulnerability vs. Clean Feature Importance:**
   - *Clean Feature Importance* (e.g., Gini impurity decrease in tree ensembles, split frequency, or nominal coefficient magnitudes $|w_j|$ in linear models) measures how much a trained model relies on feature $j$ to partition uncorrupted, in-distribution data ($s=0.00$).
   - *Feature Vulnerability* ($\text{Vuln}_j$) measures the empirical rate and magnitude of model performance decay when feature $j$ is corrupted while all other $D-1$ features remain pristine.
   - *Non-Equivalence Principle:* A feature with high clean importance may be exceptionally robust to localized perturbation if redundant features compensate for it, or it may be brittle. Conversely, a feature with low nominal importance may cause catastrophic misclassification if corrupted into an out-of-bounds regime. Clean importance and perturbation vulnerability are distinct quantities and must not be conflated.

2. **Feature Vulnerability vs. Permutation Feature Importance:**
   - Standard Permutation Feature Importance (Breiman, 2001; Fisher et al., 2019) shuffles the observed test values of feature $j$ across samples. While permutation breaks the feature-target dependency $P(Y \mid X_j)$, it preserves the empirical marginal distribution of $X_j$ and applies a fixed, unparameterized shuffle.
   - *Feature Vulnerability Stress Testing* applies parameterized, stepped perturbations ($s \in [0.00, 0.30]$) along calibrated dimensions of variation (continuous variance scaling, missingness imputation, and impulsive outliers), mapping a continuous *degradation trajectory* rather than a single permutation delta.

3. **Empirical Sensitivity vs. Causal Attribution:**
   - Feature vulnerability rankings reflect the *observational sensitivity* of a specific frozen classifier $f_\theta$ under a specific mathematical corruption operator $\mathcal{P}$.
   - They do **not** identify causal drivers within the underlying botanical data-generating process of *Iris* morphology.
   - **Mandatory Reporting Caption:** All generated tables, figures, and reports must include the verbatim statement:
     > *"Feature vulnerability rankings reflect empirical model sensitivity under the specified perturbation operators and must not be interpreted as causal claims regarding the underlying physical or biological data-generating system."*

---

## 2. Preregistered Hypotheses

All hypotheses are formally preregistered prior to configuring, coding, or executing Experiment E005.

### 2.1 Primary Hypothesis ($H_1$): Differential Feature Vulnerability
- **Scientific Context:** If all features contribute equally to model robustness, perturbing any single feature should induce identical performance degradation at maximum severity ($s=0.30$).
- **Null Hypothesis ($H_{0,1}$):** Under maximum severity ($s=0.30$) for any given model architecture $m$ and perturbation operator $\mathcal{P}$, the mean Macro-F1 degradation is invariant across all four features:
  $$H_{0,1}: \mu_{\Delta}(f_1) = \mu_{\Delta}(f_2) = \mu_{\Delta}(f_3) = \mu_{\Delta}(f_4)$$
- **Alternative Hypothesis ($H_{1,1}$):** At least one feature exhibits a statistically significant difference in mean Macro-F1 degradation compared to the other features:
  $$H_{1,1}: \exists \, j, k \in \{1, 2, 3, 4\}, \; j \ne k \quad \text{such that} \quad \mu_{\Delta}(f_j) \ne \mu_{\Delta}(f_k)$$
- **Outcome Variable:** Absolute Macro-F1 degradation at $s=0.30$: $\Delta_{\text{abs}}(s=0.30, f_j) = \text{Macro-F1}(s=0) - \text{Macro-F1}(s=0.30, f_j)$.
- **Decision Rule:** Reject $H_{0,1}$ if the omnibus repeated-measures Friedman test across the 4 features yields $p < 0.05$.

### 2.2 Secondary Hypothesis 1 ($H_2$): Inductive Bias Divergence in Vulnerability
- **Scientific Context:** Different model families possess distinct inductive biases (hyperplane separation vs. orthogonal recursive partitioning vs. additive gradient boosting).
- **Null Hypothesis ($H_{0,2}$):** The empirical feature vulnerability ranking is identical between linear models (Logistic Regression) and tree-based ensembles (Random Forest, Gradient Boosting):
  $$H_{0,2}: \tau_{\text{Kendall}}(\mathbf{R}_{\text{LR}}, \mathbf{R}_{\text{RF}}) = 1.0$$
- **Alternative Hypothesis ($H_{1,2}$):** Distinct inductive biases yield diverging feature vulnerability rankings:
  $$H_{1,2}: \tau_{\text{Kendall}}(\mathbf{R}_{\text{LR}}, \mathbf{R}_{\text{RF}}) < 1.0$$
- **Outcome Variable:** Kendall's rank correlation coefficient $\tau_b$ computed between model-specific 4-feature vulnerability rankings.

### 2.3 Secondary Hypothesis 2 ($H_3$): Decoupling of Clean Importance and Robustness Vulnerability
- **Scientific Context:** Practitioners often assume that features with the highest clean feature importance are the most dangerous failure vectors when corrupted.
- **Null Hypothesis ($H_{0,3}$):** Clean baseline feature importance ranks correlate perfectly with perturbation vulnerability ranks:
  $$H_{0,3}: \rho_{\text{Spearman}}(\mathbf{I}_{\text{clean}}, \mathbf{V}_{\text{stress}}) = 1.0$$
- **Alternative Hypothesis ($H_{1,3}$):** Clean baseline feature importance ranks do not correlate perfectly with perturbation vulnerability ranks:
  $$H_{1,3}: \rho_{\text{Spearman}}(\mathbf{I}_{\text{clean}}, \mathbf{V}_{\text{stress}}) < 1.0$$
- **Outcome Variable:** Spearman's rank correlation $\rho_s$ between clean Gini importance (RF) / absolute scaled coefficients $|w_j|$ (LR) and empirical vulnerability rank.

### 2.4 Secondary Hypothesis 3 ($H_4$): Modality-Dependent Vulnerability Ranking
- **Scientific Context:** A feature may be highly vulnerable to continuous variance perturbation (noise) but robust to complete absence (mean imputation), or vice versa.
- **Null Hypothesis ($H_{0,4}$):** For a given model $m$, the feature vulnerability ranking under Gaussian noise ($\mathbf{R}_{\text{noise}}$) is identical to the ranking under MCAR missingness with mean imputation ($\mathbf{R}_{\text{missing}}$):
  $$H_{0,4}: \mathbf{R}_{\text{noise}} = \mathbf{R}_{\text{missing}}$$
- **Alternative Hypothesis ($H_{1,4}$):** The feature vulnerability ranking shifts depending on whether the perturbation is continuous or missingness-based:
  $$H_{1,4}: \mathbf{R}_{\text{noise}} \ne \mathbf{R}_{\text{missing}}$$

---

## 3. Dataset and Evaluation Protocol

To guarantee continuity and bit-for-bit parity with Experiments E001–E004, the data partition and split mechanics are preserved as strict invariants.

### 3.1 Dataset Specification
- **Benchmark:** Fisher's Iris Benchmark dataset ($N=150$, 4 continuous input features, 3 balanced classes of 50 samples each).
- **Features ($D=4$):**
  1. Index 0: `sepal length (cm)` ($f_0$)
  2. Index 1: `sepal width (cm)` ($f_1$)
  3. Index 2: `petal length (cm)` ($f_2$)
  4. Index 3: `petal width (cm)` ($f_3$)
- **Targets ($K=3$):** `0: setosa`, `1: versicolor`, `2: virginica`.

### 3.2 Partitioning & Frozen Indices
- **Stratified Split:** 80% training ($N_{\text{train}} = 120$), 20% testing ($N_{\text{test}} = 30$, exactly 10 instances per class).
- **Split Random Seed:** `split_seed = 42` (generated strictly via [`ml_engine/src/model_autopsy/datasets/iris.py`](../ml_engine/src/model_autopsy/datasets/iris.py)).
- **Frozen Test Indices ($N_{\text{test}}=30$):**
  ```python
  [38, 127, 57, 93, 42, 56, 22, 20, 147, 84, 107, 141, 104, 51, 7, 49, 14, 69, 63, 138, 10, 140, 58, 134, 132, 77, 75, 18, 116, 28]
  ```
- **Frozen Training Parameters (Fitted on $X_{\text{train}}$ Only):**
  - Training standard deviations $\boldsymbol{\sigma}^{\text{train}} = [\sigma_0, \sigma_1, \sigma_2, \sigma_3]$ with $ddof=1$.
  - Training feature means $\boldsymbol{\mu}^{\text{train}} = [\mu_0, \mu_1, \mu_2, \mu_3]$.
  - Training `StandardScaler` parameters (used exclusively by Logistic Regression).

### 3.3 Research Seed Suite
- As established in E001 multi-seed through E004, all evaluations run across the canonical 5-seed research suite:
  $$R = [42, 123, 456, 789, 1011]$$
- Seeds govern:
  1. Stochastic model fitting (Random Forest tree bootstraps, Gradient Boosting subsampling).
  2. Pseudo-random number generation (PRNG) for feature perturbations.

---

## 4. Model Architectures & Adapters

E005 deploys the three model families evaluated in E003 and E004. Hyperparameters are held strictly identical to prior experiments:

| Model ID | Adapter Class | Architecture & Key Hyperparameters | Deterministic Seed Binding |
|---|---|---|---|
| `random_forest` | [`RandomForestAdapter`](../ml_engine/src/model_autopsy/models/sklearn_rf.py) | `n_estimators=100`, `criterion='gini'`, `max_depth=None`, `bootstrap=True` | `random_state=seed` |
| `logistic_regression` | [`LogisticRegressionAdapter`](../ml_engine/src/model_autopsy/models/sklearn_logistic.py) | `Pipeline([('scaler', StandardScaler()), ('classifier', LogisticRegression(C=1.0, solver='lbfgs', max_iter=1000))])` | `random_state=seed` |
| `gradient_boosting` | [`GradientBoostingAdapter`](../ml_engine/src/model_autopsy/models/sklearn_gb.py) | `n_estimators=100`, `learning_rate=0.1`, `max_depth=3`, `subsample=1.0` | `random_state=seed` |

### Preprocessing and Scaling Isolation Guarantee
- Linear models require feature standardization to prevent scale dominance. The `StandardScaler` in `LogisticRegressionAdapter` is fitted strictly on $X_{\text{train}}$. During corrupted evaluation, perturbed test inputs are passed to `pipeline.predict()`, ensuring that scaling transforms use frozen training parameters without adaptive test leakage.

---

## 5. Coordinate-Isolated Perturbation Operators

In contrast to E001–E004 where perturbations affected all features simultaneously, E005 defines **coordinate-isolated perturbation operators**.

Let $X \in \mathbb{R}^{N_{\text{test}} \times D}$ denote the unperturbed test feature matrix. For a selected target feature coordinate $j^* \in \{0, 1, 2, 3\}$ and severity factor $s \in [0.00, 0.30]$:
$$X'_{ik} = X_{ik} \quad \forall \, k \ne j^*, \quad \forall \, i \in \{1, \dots, N_{\text{test}}\}$$
Only the target column $j^*$ receives perturbation.

### 5.1 Operator 1: Coordinate-Isolated Additive Gaussian Noise (`single_feature_gaussian_noise`)
- **Semantic Intent:** Measures model sensitivity to continuous measurement jitter isolated to a single sensor/feature.
- **Mathematical Formulation:**
  $$X'_{i j^*} = X_{i j^*} + \varepsilon_i, \quad \varepsilon_i \sim \mathcal{N}\left(0, (s \cdot \sigma_{j^*}^{\text{train}})^2\right)$$
  where $\sigma_{j^*}^{\text{train}}$ is the sample standard deviation of feature $j^*$ computed strictly from the training split ($ddof=1$).
- **Severity Parameter $s$:** Dimensionless scale factor $s \in \{0.00, 0.05, 0.10, 0.15, 0.20, 0.25, 0.30\}$.
- **Identity Invariant ($s=0.00$):** At $s=0.00$, $\varepsilon_i = 0$, guaranteeing $X'_{i j^*} = X_{i j^*}$ bitwise.

### 5.2 Operator 2: Coordinate-Isolated MCAR Missingness (`single_feature_missingness`)
- **Semantic Intent:** Measures model degradation when a specific sensor drops out or becomes unrecorded, evaluated under training-mean imputation.
- **Mathematical Formulation:**
  For each test sample $i \in \{1, \dots, N_{\text{test}}\}$, an independent masking indicator is drawn:
  $$M_i \sim \text{Bernoulli}(s), \quad s \in [0.00, 0.30]$$
  If $M_i = 1$, the feature value is replaced with the training mean $\mu_{j^*}^{\text{train}}$:
  $$X'_{i j^*} = \begin{cases} X_{i j^*} & \text{if } M_i = 0 \\ \mu_{j^*}^{\text{train}} & \text{if } M_i = 1 \end{cases}$$
- **Severity Parameter $s$:** Probability of missingness $p_{\text{miss}} = s$.
- **Identity Invariant ($s=0.00$):** $P(M_i = 1) = 0 \implies X' = X$.

### 5.3 Operator 3: Coordinate-Isolated Outlier Contamination (`single_feature_outliers`)
- **Semantic Intent:** Measures model resilience against localized catastrophic spikes or hardware malfunctions on a single feature channel.
- **Mathematical Formulation:**
  $$O_i \sim \text{Bernoulli}(s), \quad s \in [0.00, 0.30]$$
  If $O_i = 1$, an impulsive displacement of magnitude $5 \cdot \sigma_{j^*}^{\text{train}}$ is injected:
  $$X'_{i j^*} = \begin{cases} X_{i j^*} & \text{if } O_i = 0 \\ \mu_{j^*}^{\text{train}} + \zeta_i \cdot 5\sigma_{j^*}^{\text{train}} & \text{if } O_i = 1 \end{cases}$$
  where $\zeta_i \in \{-1, +1\}$ is an equiprobable Rademacher sign variable.
- **Severity Parameter $s$:** Contamination rate $p_{\text{outlier}} = s$.
- **Identity Invariant ($s=0.00$):** $P(O_i = 1) = 0 \implies X' = X$.

### 5.4 Technical Guarantees for All Operators
1. **Array Immutability:** Input feature matrices must remain read-only (`X.flags.writeable == False`). Perturbations return fresh, read-only NumPy arrays.
2. **Monotone Nested Filtration:** As established in the E004 audit ([`e004_scientific_audit.md` §3.2](e004_scientific_audit.md#L140-L157)), for Bernoulli-based operators (missingness and outliers), PRNG streams are constructed such that coordinates corrupted at severity $s_1$ remain corrupted at severity $s_2 > s_1$. This isolates the marginal impact of increasing corruption.
3. **Cross-Modality Incomparability:** Severity $s=0.10$ in Gaussian noise (continuous standard deviation multiplier) does **not** represent the same physical perturbation intensity as $s=0.10$ in missingness (10% sample dropout) or outliers (10% impulsive spikes). Direct numerical comparisons of absolute degradation between different operator types are scientifically invalid and strictly prohibited.

---

## 6. Baselines, Evaluation Metrics, and Vulnerability Ranking

### 6.1 Clean Baseline Parity
For every model $m \in \{\text{RF}, \text{LR}, \text{GB}\}$ and seed $r \in R$, clean baseline performance is evaluated at $s=0.00$:
$$\text{Macro-F1}_{\text{clean}}(m, r) = \text{Macro-F1}(X_{\text{test}}, y_{\text{test}} \mid m, r)$$
All four feature perturbation runs for a given $(m, r)$ must exhibit **exact bitwise parity** at $s=0.00$.

### 6.2 Primary Outcome Metric: Absolute Macro-F1 Degradation
For target feature $j^*$, severity $s$, model $m$, and seed $r$:
$$\Delta_{\text{abs}}(s, j^* \mid m, r) = \text{Macro-F1}_{\text{clean}}(m, r) - \text{Macro-F1}(s, j^* \mid m, r)$$
Reported in percentage points (pp).

### 6.3 Secondary Outcome Metrics
1. **Relative Macro-F1 Degradation ($\Delta_{\text{rel}}$):**
   $$\Delta_{\text{rel}}(s, j^* \mid m, r) = \frac{\Delta_{\text{abs}}(s, j^* \mid m, r)}{\text{Macro-F1}_{\text{clean}}(m, r)} \times 100\%$$
2. **Classification Accuracy Degradation ($\Delta_{\text{acc}}$).**
3. **Per-Class Recall Deterioration ($\Delta_{\text{rec}, k}$):** Tracks whether a specific feature's corruption disproportionately destroys recall for *versicolor* or *virginica*.

### 6.4 Formal Feature Vulnerability Ranking Mechanics
To prevent ranking ambiguity or post-hoc metric selection, feature vulnerability is quantified via two complementary, preregistered metrics:

1. **Terminal Severity Vulnerability ($\text{Vuln}_{\text{term}}$):**
   The mean absolute Macro-F1 degradation at the maximum tested severity ($s=0.30$):
   $$\bar{\Delta}_{j^*} = \frac{1}{|R|} \sum_{r \in R} \Delta_{\text{abs}}(s=0.30, j^* \mid m, r)$$
   Features are ranked in descending order: $\text{Rank}(j^*) \in \{1, 2, 3, 4\}$, where $\text{Rank} = 1$ denotes the **most vulnerable feature** (highest degradation).

2. **Area Under the Degradation Curve ($\text{AUDC}$):**
   Quantifies cumulative vulnerability across the entire severity trajectory $S = [0.00, \dots, 0.30]$ using trapezoidal integration:
   $$\text{AUDC}(j^* \mid m, r) = \sum_{k=1}^{|S|-1} \frac{\Delta_{\text{abs}}(s_{k-1}, j^*) + \Delta_{\text{abs}}(s_k, j^*)}{2} \cdot (s_k - s_{k-1})$$
   $\text{AUDC}$ captures early-onset degradation that plateaus versus late-onset cliff degradation.

### 6.5 Tie-Handling & Stability Criteria
- If two features exhibit identical degradation within numerical precision ($|\bar{\Delta}_{j} - \bar{\Delta}_{k}| < 10^{-6}$), they are assigned the mid-rank (e.g., $1.5$).
- Rank stability across seeds is evaluated via the empirical standard deviation of ranks $s_{\text{rank}}(j) = \sqrt{\frac{1}{|R|-1} \sum_r (\text{Rank}_r(j) - \bar{\text{Rank}}(j))^2}$.

---

## 7. Statistical Analysis & Multiple Testing Correction

### 7.1 Multi-Seed Aggregation Framework
For each experimental cell defined by $(\text{Model } m, \text{Operator } \mathcal{P}, \text{Feature } j^*, \text{Severity } s)$:
1. **Sample Mean:** $\bar{M} = \frac{1}{R} \sum_{r=1}^R M_r$.
2. **Sample Standard Deviation ($ddof=1$):** $S = \sqrt{\frac{1}{R-1} \sum_{r=1}^R (M_r - \bar{M})^2}$.
3. **Standard Error of the Mean (SEM):** $\text{SEM} = S / \sqrt{R} = S / \sqrt{5}$.
4. **Student's $t$ 95% Confidence Interval:**
   $$\text{CI}_{95\%} = \left[ \bar{M} - t_{0.025, 4} \cdot \text{SEM}, \; \bar{M} + t_{0.025, 4} \cdot \text{SEM} \right]$$
   where $t_{0.025, 4} \approx 2.7764$.

### 7.2 Hypothesis Testing Procedure
1. **Omnibus Test for $H_1$:**
   - Execute Friedman's test across the four features at $s=0.30$ paired by random seed ($N=5$).
   - If $p \ge 0.05$, fail to reject $H_{0,1}$; conclude that feature vulnerabilities are statistically indistinguishable under the tested sample size.
2. **Post-Hoc Pairwise Comparisons:**
   - If omnibus $p < 0.05$, perform paired Wilcoxon signed-rank tests (or paired Student's $t$-tests if normality is verified via Shapiro-Wilk) across all $\binom{4}{2} = 6$ feature pairs.
3. **Multiple Testing Correction:**
   - Control the False Discovery Rate (FDR) using the Benjamini-Hochberg (BH) procedure at target rate $\alpha = 0.05$:
     $$p_{(i)} \le \frac{i}{m_{\text{tests}}} \cdot \alpha, \quad m_{\text{tests}} = 6$$
   - Both unadjusted $p$-values and BH-adjusted $q$-values must be reported.

### 7.3 Rank Concordance Testing ($H_2, H_3$)
- **Inter-Model Concordance ($H_2$):** Compute Kendall's $\tau_b$ and associated exact permutation $p$-values between the 4-feature ranking vectors of (RF vs. LR), (RF vs. GB), and (LR vs. GB).
- **Clean vs. Vulnerability Concordance ($H_3$):** Compute Spearman's $\rho$ between nominal feature importance (RF Gini importance; LR standardized $|w_j|$) and terminal degradation $\bar{\Delta}$.

---

## 8. Data Leakage Prevention & Reproducibility Guarantees

E005 enforces the five mandatory Model Autopsy isolation barriers:

| Isolation Barrier | Protocol Mechanism | Audit Verification Test |
|---|---|---|
| **Split Isolation** | Stratified split executed once with `split_seed=42`; indices frozen in [`iris.py`](../ml_engine/src/model_autopsy/datasets/iris.py). | Test verifies train/test index sets are strictly disjoint ($I_{\text{train}} \cap I_{\text{test}} = \emptyset$). |
| **Dispersion Isolation** | $\sigma_j^{\text{train}}$ and $\mu_j^{\text{train}}$ computed strictly on $X_{\text{train}}$ ($N=120$). | Test verifies recalculation using $X_{\text{train}}$ matches operator scaling parameters bit-for-bit. |
| **Preprocessing Isolation** | `StandardScaler` in `LogisticRegressionAdapter` fitted strictly on $X_{\text{train}}$. | Test verifies scaler `mean_` and `var_` match training split statistics bit-for-bit. |
| **Input Immutability** | $X_{\text{test}}$ marked non-writeable (`flags.writeable = False`). | Attempting in-place modification of evaluation inputs raises `ValueError`. |
| **Deterministic Reproducibility** | Full PRNG seed isolation via `np.random.default_rng(seed)`. | Independent back-to-back executions produce bitwise-identical output hashes. |

---

## 9. Proposed Artifact Schema and Reporting

All outputs will be generated into an isolated directory: `artifacts/experiments/E005/`.

### 9.1 File Layout
```
artifacts/experiments/E005/
├── metrics.json                     # Complete nested hierarchical results tensor
├── feature_vulnerability_summary.csv# Tabular metrics for all model/feature/severity combinations
├── feature_rankings.json            # Final computed rankings, AUDC, and statistical test results
├── reproducibility_manifest.json    # Complete runtime environment, commit SHA, and seed records
├── report.md                        # Human-readable synthesis with mandated scientific caveats
└── figures/
    ├── feature_degradation_curves.png  # 3-panel plot (RF, LR, GB) showing degradation curves for 4 features
    ├── feature_vulnerability_bars.png   # Bar chart of terminal degradation with 95% CI error bars
    └── clean_vs_vulnerability_scatter.png # Scatter plot comparing clean importance vs. stress vulnerability
```

### 9.2 Proposed `feature_vulnerability_summary.csv` Schema
```csv
model_id,corruption_type,feature_index,feature_name,severity,macro_f1_mean,macro_f1_std,macro_f1_sem,macro_f1_ci95_low,macro_f1_ci95_high,delta_abs_mean,delta_rel_mean,is_failed
random_forest,single_feature_gaussian_noise,0,sepal length (cm),0.00,0.9265,0.0152,0.0068,0.9076,0.9454,0.0000,0.0000,false
...
```

### 9.3 Proposed `feature_rankings.json` Schema
```json
{
  "experiment_id": "E005",
  "generated_at": "ISO-8601-TIMESTAMP",
  "models": {
    "random_forest": {
      "single_feature_gaussian_noise": {
        "terminal_rankings": [
          {"rank": 1, "feature_name": "petal length (cm)", "delta_abs_mean": 0.1245, "sem": 0.0112},
          {"rank": 2, "feature_name": "petal width (cm)", "delta_abs_mean": 0.0832, "sem": 0.0095},
          {"rank": 3, "feature_name": "sepal length (cm)", "delta_abs_mean": 0.0210, "sem": 0.0041},
          {"rank": 4, "feature_name": "sepal width (cm)", "delta_abs_mean": 0.0085, "sem": 0.0030}
        ],
        "audc_rankings": [...],
        "friedman_test": {"statistic": 13.8, "p_value": 0.0032},
        "clean_importance_correlation": {"spearman_rho": 0.80, "p_value": 0.20}
      }
    }
  }
}
```

---

## 10. Acceptance Criteria for E005 Completion

Experiment E005 will be considered **scientifically complete and verified** only when all nine criteria are met:

1. **Protocol Compliance:** Evaluation executes across all 3 models (RF, LR, GB), 4 features, 7 severities, and 5 seeds ($3 \times 4 \times 7 \times 5 = 420$ evaluation cells per operator).
2. **Baseline Parity:** At $s=0.00$, Macro-F1 across all 4 feature evaluations matches the clean model baseline bit-for-bit for every seed.
3. **Data Leakage Immunity:** Automated test verifies that perturbation scaling parameters ($\boldsymbol{\sigma}^{\text{train}}, \boldsymbol{\mu}^{\text{train}}$) and model scalers have zero dependency on $X_{\text{test}}$.
4. **Array Immutability:** Unit tests verify that test arrays and training statistics are non-writeable.
5. **Statistical Rigor:** All reported bounds utilize Student's $t$ with $ddof=1$ ($\nu=4$), and all pairwise hypothesis tests apply Benjamini-Hochberg FDR correction.
6. **Deterministic Reproducibility:** Re-running the execution script produces bitwise identical JSON metrics and CSV tables.
7. **Artifact Completeness:** All files specified in §9 exist, parse cleanly against schema validators, and are non-empty.
8. **Mandated Caveats:** The generated `report.md` contains the mandatory non-causal caption and finite-sample disclaimers verbatim.
9. **Independent Scientific Audit:** An independent audit document (`docs/research/e005_scientific_audit.md`) is completed, recalculating all metrics from raw outputs and scoring a formal verdict of **PASS**.

---

## 11. Scientific Limitations and Boundary Conditions

To prevent scientific overclaiming, the findings of Experiment E005 are explicitly bounded by the following methodological constraints:

1. **Sample Size Constraints ($N_{\text{test}} = 30$):**
   The test split contains only 30 instances (10 per class). Consequently, a single sample misclassification alters accuracy by $3.33$ percentage points. Rank stability must be evaluated with explicit reference to this discrete resolution.
2. **High Feature Collinearity in Iris:**
   In the Iris dataset, `petal length` and `petal width` exhibit extreme linear correlation ($r > 0.96$). Perturbing only one of these features while holding the other constant creates synthetic points that lie off the natural data manifold (e.g., a flower with a 5.0 cm petal length but a 0.2 cm petal width). Observed degradation reflects the model's tolerance to off-manifold coordinate corruption, which may differ from on-manifold degradation.
3. **Domain Specificity:**
   Empirical vulnerability rankings on 4 morphological measurements of Iris flowers cannot be generalized to complex tabular domains (financial risk, clinical records) or high-dimensional perceptual data (images, text).
4. **Model Architecture Scope:**
   Findings are limited to scikit-learn implementations of Random Forest, L2-penalized Logistic Regression, and shallow Gradient Boosted Trees. They do not generalize to deep neural networks, kernel machines, or nearest-neighbor classifiers.

---

## 12. Demarcation from RQ6 (Distribution Shift)

- **RQ6 Definition:** *"How do models behave under systematic distributional changes?"*
- **Scope Demarcation:**
  - **RQ3 (E005)** focuses exclusively on **coordinate-isolated feature vulnerability** where the data-generating distribution is held fixed and localized perturbation operators are applied to single test coordinates.
  - **RQ6** addresses **systematic distribution shift**, including:
    1. Covariate shift: Systematic translation or rotation of the joint feature distribution $P_{\text{test}}(X) \ne P_{\text{train}}(X)$ (e.g., domain shifts, environmental temperature shifts).
    2. Concept drift: Changes in the posterior label distribution $P(Y \mid X)$.
    3. Subpopulation shift: Changing class proportions or subgroup representation.
- **Protocol Separation:** E005 makes **no claims** regarding distribution shift (RQ6). RQ6 is reserved for future experimental phases (e.g., E006) and will be governed by an independent preregistered design document.
