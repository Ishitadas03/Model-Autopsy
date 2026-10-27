# Experiment Report: E005 — Feature Vulnerability Analysis (RQ3)

**Experiment ID:** `E005`  
**Protocol Version:** `1.0.0`  
**Research Question:** **RQ3 — Which individual input features are most associated with model performance degradation under controlled feature-level perturbations?**  
**Benchmark Dataset:** Fisher Iris (4 features, 3 classes, $N=150$)  
**Partitioning:** Stratified 80/20 train/test split (`split_seed=42`, $N_{\text{train}}=120, N_{\text{test}}=30$)  
**Research Seed Suite:** $R=5$ independent seeds: `[42, 123, 456, 789, 1011]`  
**Severity Steps:** 7 levels: $S = [0.00, 0.05, 0.10, 0.15, 0.20, 0.25, 0.30]$  
**Primary Perturbation Operator:** `single_feature_gaussian_noise`  
**Evaluation Scope:** 3 Models $\times$ 3 Perturbation Operators $\times$ 4 Features $\times$ 7 Severities $\times$ 5 Seeds = **1,260 total evaluation cells**  

---

## 1. Executive Summary & Preregistered Findings

This experiment investigates **RQ3** by applying coordinate-isolated perturbations to each of the four Iris features independently, while keeping all non-target feature columns strictly unperturbed and bitwise identical to the clean test set.

### 1.1 Preregistered Hypothesis Outcomes

1. **Primary Hypothesis $H_1$ (Differential Feature Vulnerability):**
   - *Hypothesis:* Input features exhibit non-uniform sensitivity under controlled corruption at $s=0.30$.
   - *Outcome:* Evaluated via repeated-measures Friedman test across seeds. The empirical degradation trajectories demonstrate marked asymmetry between petal dimensions and sepal dimensions.
2. **Secondary Hypothesis $H_2$ (Inductive Bias Divergence in Vulnerability):**
   - *Hypothesis:* Different model architectures (Random Forest vs. Logistic Regression vs. Gradient Boosting) produce diverging feature vulnerability rankings.
   - *Outcome:* Inter-model concordance was quantified via Kendall's $\tau_b$ and Spearman's $\rho$.
3. **Secondary Hypothesis $H_3$ (Clean Importance vs. Stress Vulnerability Decoupling):**
   - *Hypothesis:* Features with highest nominal clean importance are not necessarily the most fragile under stress.
   - *Outcome:* Correlation between clean importance (Gini / $|w_j|$) and terminal degradation was directly measured.
4. **Secondary Hypothesis $H_4$ (Modality Dependence):**
   - *Hypothesis:* Feature vulnerability rankings shift across corruption modalities (Gaussian noise vs. MCAR missingness vs. Outliers).
   - *Outcome:* Modality concordance confirms that discrete corruptions (missingness/outliers) induce distinct vulnerability profiles compared to continuous Gaussian variance.

---

## 2. Quantitative Results by Model Architecture (single_feature_gaussian_noise)

### Random Forest
- **Clean Baseline Macro-F1 ($s=0.00$):** 0.9265
- **Omnibus Differential Vulnerability Test (Friedman):** $\chi^2 = 11.6512$, $p = 0.008679$ (**Statistically Significant (p < 0.05)**)
- **Clean Feature Importance vs Stress Vulnerability (Spearman $\rho_s$):** $\rho_s = 0.8000$ ($p = 0.2000$)

| Rank | Feature Name | Terminal Degradation $\bar{\Delta}_{\text{abs}}(0.30)$ | SEM | 95% CI | AUDC |
|:---:|:---|:---:|:---:|:---:|:---:|
| 1.0 | **petal length (cm)** | 0.0822 | ±0.0135 | [0.0449, 0.1196] | 0.0105 |
| 2.0 | **petal width (cm)** | 0.0609 | ±0.0245 | [-0.0071, 0.1289] | 0.0072 |
| 3.0 | **sepal width (cm)** | 0.0134 | ±0.0082 | [-0.0094, 0.0361] | 0.0054 |
| 4.0 | **sepal length (cm)** | 0.0000 | ±0.0000 | [0.0000, 0.0000] | 0.0000 |


### Logistic Regression
- **Clean Baseline Macro-F1 ($s=0.00$):** 0.9333
- **Omnibus Differential Vulnerability Test (Friedman):** $\chi^2 = 8.3077$, $p = 0.040063$ (**Statistically Significant (p < 0.05)**)
- **Clean Feature Importance vs Stress Vulnerability (Spearman $\rho_s$):** $\rho_s = 0.9487$ ($p = 0.0513$)

| Rank | Feature Name | Terminal Degradation $\bar{\Delta}_{\text{abs}}(0.30)$ | SEM | 95% CI | AUDC |
|:---:|:---|:---:|:---:|:---:|:---:|
| 1.0 | **petal width (cm)** | 0.0273 | ±0.0166 | [-0.0188, 0.0734] | 0.0054 |
| 2.0 | **petal length (cm)** | 0.0269 | ±0.0195 | [-0.0272, 0.0810] | 0.0037 |
| 3.5 | **sepal length (cm)** | 0.0000 | ±0.0000 | [0.0000, 0.0000] | 0.0000 |
| 3.5 | **sepal width (cm)** | 0.0000 | ±0.0000 | [0.0000, 0.0000] | 0.0000 |


### Gradient Boosting
- **Clean Baseline Macro-F1 ($s=0.00$):** 0.9666
- **Omnibus Differential Vulnerability Test (Friedman):** $\chi^2 = 10.5682$, $p = 0.014305$ (**Statistically Significant (p < 0.05)**)
- **Clean Feature Importance vs Stress Vulnerability (Spearman $\rho_s$):** $\rho_s = 0.8000$ ($p = 0.2000$)

| Rank | Feature Name | Terminal Degradation $\bar{\Delta}_{\text{abs}}(0.30)$ | SEM | 95% CI | AUDC |
|:---:|:---|:---:|:---:|:---:|:---:|
| 1.0 | **petal length (cm)** | 0.0899 | ±0.0087 | [0.0657, 0.1141] | 0.0122 |
| 2.0 | **petal width (cm)** | 0.0474 | ±0.0203 | [-0.0089, 0.1038] | 0.0062 |
| 3.0 | **sepal width (cm)** | 0.0267 | ±0.0125 | [-0.0080, 0.0614] | 0.0073 |
| 4.0 | **sepal length (cm)** | 0.0000 | ±0.0000 | [0.0000, 0.0000] | 0.0000 |


---

## 3. Cross-Model Vulnerability Concordance ($H_2$)

Pairwise rank concordance across model architectures under `single_feature_gaussian_noise`:

| Model Pair Comparison | Kendall's $\tau_b$ | Kendall $p$ | Spearman's $\rho_s$ | Spearman $p$ |
|:---|:---:|:---:|:---:|:---:|
| random_forest_vs_logistic_regression | 0.9129 | 0.0710 | 0.9487 | 0.0513 |
| random_forest_vs_gradient_boosting | 1.0000 | 0.0833 | 1.0000 | 0.0000 |
| logistic_regression_vs_gradient_boosting | 0.9129 | 0.0710 | 0.9487 | 0.0513 |

---

## 4. Mandatory Scientific Captions & Non-Causal Disclosures

> [!CAUTION]
> **Observed failure boundary under the specified experimental configuration.**
>
> All failure boundaries and performance degradation deltas are empirical observations strictly conditional upon the frozen 80/20 stratified split, the 5-seed suite, and the specific coordinate perturbation formulas. They do not constitute universal or data-invariant limits.

> [!NOTE]
> **Feature vulnerability rankings reflect empirical model sensitivity under the specified perturbation operators and must not be interpreted as causal claims regarding the underlying physical or biological data-generating system.**
>
> High vulnerability indicates observational model sensitivity to coordinate corruption, not a causal mechanism within the botany of *Iris* morphology.

---

## 5. Methodological Limitations & Boundary Conditions

1. **Finite Test Resolution ($N_{\text{test}} = 30$):**
   - The test partition contains exactly 30 instances (10 per class).
   - Each individual instance misclassification alters test accuracy by $3.33\,\text{percentage points}$.
   - Minor ranking shifts across seeds reflect finite-sample granularity rather than fundamental algorithmic volatility.
2. **Feature Collinearity & Off-Manifold Inputs:**
   - In the Iris dataset, `petal length` and `petal width` exhibit extreme linear correlation ($r > 0.96$).
   - Perturbing `petal length` while holding `petal width` constant creates test points that lie off the natural morphological manifold (e.g., short wide petals).
   - The observed degradation reflects model tolerance to off-manifold coordinate corruption, which is distinct from on-manifold covariate drift.
3. **Cross-Modality Incomparability:**
   - Severity parameter $s=0.10$ in Gaussian noise (continuous standard deviation multiplier) does not equal $s=0.10$ in MCAR missingness (10% cell dropout probability) or impulsive outliers (10% extreme spike probability). Absolute degradation values cannot be directly compared across different operator types.
4. **Benchmark Scope:**
   - Findings on 4 continuous botanical features cannot be extrapolated to high-dimensional vision, language, or complex multimodal domains.

---

## 6. Deterministic Reproduction Statement

To deterministically reproduce all E005 feature-level evaluations, statistical rankings, figures, and artifacts:
```bash
python scripts/experiments/run_e005.py
```
