# Experimental Design & Preregistration Protocol: E006
## RQ6: Empirical Robustness and Boundary Characterization Under Systematic Distribution Shift

**Experiment ID:** `E006`  
**Experiment Title:** Empirical Robustness Trajectories and Failure Boundaries Under Parameterized Covariate Shifts (Directional Translation, Dispersion Dilation, and Subpopulation Selection) on the Iris Benchmark  
**Research Question:** **RQ6 — How do machine learning models behave under systematic distributional changes, and how do distribution shifts differ empirically from localized sample corruptions?**  
**Protocol Version:** 1.0.0 (Preregistered Experimental Specification)  
**Parent Documents:**
- [`docs/research/problem_statement.md`](problem_statement.md)
- [`docs/research/experimental_protocol.md`](experimental_protocol.md)
- [`docs/research/e002_experimental_design.md`](e002_experimental_design.md)
- [`docs/research/e003_experimental_design.md`](e003_experimental_design.md)
- [`docs/research/e004_experimental_design.md`](e004_experimental_design.md)
- [`docs/research/e005_experimental_design.md`](e005_experimental_design.md)
- [`docs/research/e005_scientific_audit.md`](e005_scientific_audit.md)
- [`docs/research/project_completion_audit.md`](project_completion_audit.md)  
**Target Subsystem:** `ml_engine` (Model Autopsy Core Framework)  
**Status:** Preregistration Specification (Pre-Implementation Freeze)  

---

## 1. Research Question, Motivation, and Scientific Scope

### 1.1 Formal Definition of RQ6
In Experiments E001 through E005, Model Autopsy evaluated model degradation under **localized sample corruptions** (additive isotropic Gaussian noise, MCAR feature missingness with mean imputation, impulsive outlier spikes, and coordinate-isolated feature corruptions). In those paradigms, evaluation samples were perturbed independently around their nominal positions, leaving the global location of the distribution centroid $\mathbb{E}[X]$ and overall population geometry largely centered on the training manifold.

**Research Question 6 (RQ6)** addresses global, systematic changes in data distribution:
> *"How do machine learning classifiers behave when the test distribution undergoes systematic distribution shift, how does performance degradation under directional covariate shift compare to stochastic corruption, and how do distinct model inductive biases govern vulnerability to out-of-distribution transfer?"*

### 1.2 Essential Scientific Taxonomy: Covariate Shift vs. Concept Drift vs. Localized Corruption
To maintain experimental validity, this protocol formally establishes three mathematical categories of distribution change:

```
┌────────────────────────────────────────────────────────────────────────────────────────┐
│                        TAXONOMY OF INPUT DISTRIBUTION PERTURBATIONS                     │
├──────────────────────────────┬──────────────────────────────┬──────────────────────────┤
│ Localized Sample Corruption  │       Covariate Shift        │       Concept Drift      │
│         (E001–E005)          │         (E006 Core)          │     (Scoped Boundary)    │
├──────────────────────────────┼──────────────────────────────┼──────────────────────────┤
│ • Stochastic, sample-wise    │ • Systematic global change:  │ • Conditional shift:     │
│   perturbation:              │   P_test(X) != P_train(X)    │   P_test(Y|X) !=         │
│   X'_i = X_i + epsilon_i     │ • Ground-truth conditional   │   P_train(Y|X)           │
│ • E[X'] = E[X] (zero-mean)   │   labeling remains invariant:│ • Semantic definition of │
│ • Preserves global centroid  │   P_test(Y|X) == P_train(Y|X)│   classes changes        │
│ • Independent draws per cell │ • Physical translation, scale│ • Biologically unsound on│
│   or coordinate              │   dilation, or selection bias│   static Iris taxonomy   │
└──────────────────────────────┴──────────────────────────────┴──────────────────────────┘
```

1. **Covariate Shift ($P_{\text{test}}(X) \ne P_{\text{train}}(X)$, $P(Y \mid X)$ Invariant):**
   - The marginal density of the input features shifts between training and deployment environments, but the underlying physical/botanical relationship assigning species labels to morphological measurements remains fixed.
   - *Physical Exemplars:* Global climate differences, soil fertility gradients, or sensor calibration offsets that systematically scale morphological structures while preserving biological taxonomy.
   - **Scope Decision:** Covariate shift can be modeled rigorously, continuously, and mathematically on continuous tabular benchmarks like Iris. It forms the primary empirical core of E006.

2. **Concept Drift ($P_{\text{test}}(Y \mid X) \ne P_{\text{train}}(Y \mid X)$):**
   - The conditional mapping from features to classes changes over time or across domains.
   - *Methodological Assessment on the Iris Benchmark:*
     - *Iris* is a closed botanical taxonomy based on Fisher's canonical 1936 specimen measurements of three distinct species (*Iris setosa*, *Iris versicolor*, *Iris virginica*). In nature, biological species definitions do not randomly "drift" their morphological mapping overnight.
     - Creating synthetic concept drift by arbitrarily re-assigning class labels (e.g., swapping Versicolor with Virginica labels, or arbitrarily shifting the decision boundary in label space) is methodologically indistinguishable from label noise or adversarial relabeling. It lacks grounded physical, temporal, or biological meaning.
   - **Preregistered Scoping Decision:** This protocol explicitly documents that **authentic concept drift cannot be scientifically defended on the static Iris dataset**. Rather than manufacturing artificial label permutations and claiming to study concept drift, E006 formally restricts its empirical scope to **Systematic Covariate Shift** and documents concept drift on dynamic/temporal streaming benchmarks as future research.

3. **Localized Corruption vs. Systematic Shift:**
   - Additive Gaussian noise (E001) adds high-frequency zero-mean jitter: $\mathbb{E}[\varepsilon] = 0$. The test distribution broadens symmetrically around each point.
   - Directional covariate shift translates the entire support rigidly along a vector $\mathbf{v}$: $\mathbb{E}[X'] = \mathbb{E}[X] + s \cdot \mathbf{v}$. Every test point moves cohesively, driving the entire population systematically across class boundaries.

---

## 2. Preregistered Hypotheses

All hypotheses are preregistered prior to writing any implementation code or executing tests.

### 2.1 Primary Hypothesis ($H_1$): Architecture-Dependent Resilience Under Directional Covariate Shift
- **Scientific Context:** Linear classifiers (Logistic Regression) construct global separating hyperplanes that extend infinitely across $\mathbb{R}^D$, whereas tree ensembles (Random Forest, Gradient Boosting) partition space into axis-aligned hyperrectangles with bounded, step-wise piece-wise constant extrapolation beyond the training convex hull.
- **Null Hypothesis ($H_{0,1}$):** Under maximum directional covariate shift ($s=0.30$) along the dominant feature axis, the mean Macro-F1 degradation is invariant across Random Forest, Logistic Regression, and Gradient Boosting:
  $$H_{0,1}: \mu_{\Delta}(\text{RF}) = \mu_{\Delta}(\text{LR}) = \mu_{\Delta}(\text{GB})$$
- **Alternative Hypothesis ($H_{1,1}$):** Distinct inductive biases yield statistically significant divergence in degradation rates under directional shift:
  $$H_{1,1}: \exists \, m_a, m_b \in \{\text{RF}, \text{LR}, \text{GB}\}, \; m_a \ne m_b \quad \text{such that} \quad \mu_{\Delta}(m_a) \ne \mu_{\Delta}(m_b)$$
- **Outcome Variable:** Absolute Macro-F1 degradation at $s=0.30$: $\Delta_{\text{abs}}(s=0.30) = \text{Macro-F1}(s=0) - \text{Macro-F1}(s=0.30)$.
- **Decision Rule:** Reject $H_{0,1}$ if the omnibus Friedman test across models paired by seed ($N=5$) yields $p < 0.05$.

### 2.2 Secondary Hypothesis 1 ($H_2$): Asymmetry of Shift Direction (Positive vs. Negative Shift)
- **Scientific Context:** In the Iris feature space, *Iris setosa* occupies a compact, well-separated cluster at low petal values, while *versicolor* and *virginica* share an overlapping, tight decision boundary at higher petal values.
- **Null Hypothesis ($H_{0,2}$):** Positive directional translation ($+s \cdot \boldsymbol{\sigma}$) and negative directional translation ($-s \cdot \boldsymbol{\sigma}$) along the petal axis induce identical performance degradation:
  $$H_{0,2}: \mu_{\Delta}(+s) = \mu_{\Delta}(-s)$$
- **Alternative Hypothesis ($H_{1,2}$):** Due to geometric boundary asymmetry, shift direction exhibits marked directional asymmetry:
  $$H_{1,2}: \mu_{\Delta}(+s) \ne \mu_{\Delta}(-s)$$
- **Outcome Variable:** Difference in terminal degradation: $\delta_{\text{dir}} = \bar{\Delta}_{\text{abs}}(+0.30) - \bar{\Delta}_{\text{abs}}(-0.30)$.
- **Decision Rule:** Reject $H_{0,2}$ if paired Student's $t$-test / Wilcoxon signed-rank test across seeds yields $p < 0.05$.

### 2.3 Secondary Hypothesis 2 ($H_3$): Shift vs. Corruption Acceleration (Cliff Effect)
- **Scientific Context:** Zero-mean stochastic noise (E001/E002) broadens dispersion symmetrically, allowing interior samples to survive. Cohesive directional translation moves all instances simultaneously toward the decision boundary.
- **Null Hypothesis ($H_{0,3}$):** Directional covariate shift and isotropic Gaussian noise exhibit identical failure boundary crossing points $s^*$:
  $$H_{0,3}: s^*_{\text{shift}} = s^*_{\text{noise}}$$
- **Alternative Hypothesis ($H_{1,3}$):** Directional covariate shift causes earlier, steeper failure boundary crossing than isotropic noise:
  $$H_{1,3}: s^*_{\text{shift}} < s^*_{\text{noise}}$$
- **Outcome Variable:** Observed empirical failure boundary $s^* = \min \{ s \in S \mid \text{Macro-F1}(s) < 0.80 \}$.

### 2.4 Secondary Hypothesis 3 ($H_4$): Dispersion Inflation vs. Rigid Translation
- **Scientific Context:** Heteroscedastic scale inflation (expanding distribution tails outward from the centroid) affects peripheral instances first, while rigid translation displaces both interior and peripheral instances uniformly.
- **Null Hypothesis ($H_{0,4}$):** Dispersion dilation and directional translation generate identical Area Under the Degradation Curve ($\text{AUDC}$):
  $$H_{0,4}: \text{AUDC}_{\text{dilation}} = \text{AUDC}_{\text{translation}}$$
- **Alternative Hypothesis ($H_{1,4}$):** Rigid translation generates significantly greater cumulative degradation than dispersion dilation:
  $$H_{1,4}: \text{AUDC}_{\text{translation}} > \text{AUDC}_{\text{dilation}}$$

---

## 3. Mathematical Formulation of Covariate Shift Mechanisms

E006 defines three formal, parameterized covariate shift operators acting on test inputs $X \in \mathbb{R}^{N_{\text{test}} \times D}$ ($D=4$).

### 3.1 Operator 1: Directional Affine Translation (`covariate_directional_shift`)
- **Physical Motivation:** Systematic environmental shift causing directional allometric scaling across features.
- **Mathematical Definition:**
  For test sample $i \in \{1, \dots, N_{\text{test}}\}$ and feature coordinate $j \in \{1, \dots, D\}$:
  $$X'_{ij} = X_{ij} + s \cdot v_j \cdot \sigma_j^{\text{train}}$$
  where:
  - $s \in [0.00, 0.30]$ is the dimensionless severity scalar.
  - $\sigma_j^{\text{train}}$ is the sample standard deviation of feature $j$ estimated strictly on the training partition ($ddof=1$).
  - $\mathbf{v} \in \mathbb{R}^D$ is the unit direction vector in standardized feature space ($\|\mathbf{v}\|_2 = 1$).
- **Shift Regimes Evaluated:**
  1. **Allometric Growth Shift ($\mathbf{v}_{\text{allometric}}$):** Uniform positive translation across all features: $\mathbf{v} = [0.5, 0.5, 0.5, 0.5]^T$.
  2. **Petal Axis Translation ($\mathbf{v}_{\text{petal+}}$):** Positive translation along the highly discriminatory petal dimensions: $\mathbf{v} = [0.0, 0.0, 1/\sqrt{2}, 1/\sqrt{2}]^T$.
  3. **Petal Axis Inversion ($\mathbf{v}_{\text{petal-}}$):** Negative translation along the petal dimensions: $\mathbf{v} = [0.0, 0.0, -1/\sqrt{2}, -1/\sqrt{2}]^T$.
- **Severity-Zero Invariant:** At $s = 0.00$, $X' \equiv X$ bitwise.

### 3.2 Operator 2: Covariate Dispersion Inflation (`covariate_dispersion_shift`)
- **Physical Motivation:** Environmental destabilization or measurement volatility that inflates population variance without shifting the central tendency.
- **Mathematical Definition:**
  Each test sample $i$ is scaled radially outward from the empirical training centroid $\boldsymbol{\mu}^{\text{train}}$:
  $$X'_{ij} = \mu_j^{\text{train}} + (1.0 + s) \cdot (X_{ij} - \mu_j^{\text{train}})$$
  where $\mu_j^{\text{train}}$ is the training feature mean.
- **Statistical Properties:**
  - $\mathbb{E}[X'_j] \approx \mathbb{E}[X_j]$ (central location preserved).
  - $\text{Var}(X'_j) = (1.0 + s)^2 \cdot \text{Var}(X_j)$.
  - Peripheral instances are driven into out-of-distribution regions, while instances near the training centroid experience minimal displacement.
- **Severity-Zero Invariant:** At $s = 0.00$, $(1.0 + 0) \cdot (X_{ij} - \mu_j) + \mu_j = X_{ij}$ bitwise.

### 3.3 Operator 3: Subpopulation Truncation / Selection Bias (`covariate_selection_shift`)
- **Physical Motivation:** Non-random survival, selective filtering, or observation bias where probability of inclusion in the test set depends monotonically on feature magnitude.
- **Mathematical Definition:**
  Rather than perturbing coordinates synthetically, each instance in the pooled test set is assigned an inclusion probability governed by a sigmoid filter on the standardized first principal component $z_{i1}$ (derived strictly from training PCA parameters):
  $$w_i(s) = \frac{1}{1 + \exp\left(-k(s) \cdot z_{i1}\right)}$$
  where $k(s) = 10 \cdot s$.
  - Evaluation metrics are computed via importance-weighted Macro-F1:
    $$\text{Macro-F1}_{\text{weighted}}(s) = \sum_{k=1}^K \frac{2 \cdot \text{Prec}_k(w) \cdot \text{Rec}_k(w)}{\text{Prec}_k(w) + \text{Rec}_k(w)}$$
- **Severity-Zero Invariant:** At $s=0.00$, $k(0) = 0 \implies w_i = 0.5$ (uniform unweighted evaluation).

---

## 4. Dataset and Evaluation Protocol

To ensure strict comparability with Experiments E001–E005, all shared data invariants are preserved:

| Invariant Dimension | Specification | Protocol Guarantee |
|---|---|---|
| **Dataset** | Fisher's Iris Benchmark ($N = 150$, 4 features, 3 classes) | Canonical benchmark preservation |
| **Partitioning** | Stratified 80/20 train/test split (`split_seed = 42`) | Frozen train ($N=120$) and test ($N=30$) |
| **Frozen Test Indices** | `[38, 127, 57, 93, 42, 56, 22, 20, 147, 84, 107, 141, 104, 51, 7, 49, 14, 69, 63, 138, 10, 140, 58, 134, 132, 77, 75, 18, 116, 28]` | Verified immutable test partition from `iris.py` |
| **Research Seed Suite** | $R = 5$ seeds: `[42, 123, 456, 789, 1011]` | Multi-seed statistical stability |
| **Primary Metric** | Macro-Averaged F1-Score ($\text{Macro-F1}$) | Unweighted harmonic mean across classes |
| **Secondary Metrics** | Accuracy, Per-Class Recall, Confusion Matrix, AUDC | Secondary diagnostic indicators |
| **Failure Criterion** | Strict failure if $\text{Macro-F1} < 0.80$ | Predefined reliability threshold |
| **Severity Steps ($S$)** | 7 levels: $[0.00, 0.05, 0.10, 0.15, 0.20, 0.25, 0.30]$ | Canonical severity grid |

---

## 5. Model Configurations and Training Protocol

E006 benchmarks the three model architectures evaluated in E003–E005:

1. **Random Forest (`random_forest`):**
   - Class: `RandomForestAdapter` ([`ml_engine/src/model_autopsy/models/sklearn_rf.py`](../ml_engine/src/model_autopsy/models/sklearn_rf.py))
   - Parameters: `n_estimators=100`, `criterion='gini'`, `max_depth=None`, `bootstrap=True`.
   - Extrapolation Behavior: Predicts constant majority class of the leaf hyperrectangle outside the training convex hull.
2. **Logistic Regression (`logistic_regression`):**
   - Class: `LogisticRegressionAdapter` ([`ml_engine/src/model_autopsy/models/sklearn_logistic.py`](../ml_engine/src/model_autopsy/models/sklearn_logistic.py))
   - Parameters: `Pipeline([('scaler', StandardScaler()), ('classifier', LogisticRegression(C=1.0, solver='lbfgs', max_iter=1000))])`.
   - Extrapolation Behavior: Linear logits grow unbounded proportionally to distance from the separating hyperplane.
3. **Gradient Boosted Trees (`gradient_boosting`):**
   - Class: `GradientBoostingAdapter` ([`ml_engine/src/model_autopsy/models/sklearn_gb.py`](../ml_engine/src/model_autopsy/models/sklearn_gb.py))
   - Parameters: `n_estimators=100`, `learning_rate=0.1`, `max_depth=3`, `subsample=1.0`.
   - Extrapolation Behavior: Sum of shallow tree step-functions saturates at extreme values.

### Training Isolation Guarantee
All models are fitted exclusively on $X_{\text{train}}, y_{\text{train}}$ ($N=120$). The `StandardScaler` in `LogisticRegressionAdapter` is fitted strictly on $X_{\text{train}}$, ensuring zero test-set leakage.

---

## 6. Primary and Secondary Metrics

### 6.1 Clean Baseline Parity
For each model $m$ and seed $r$, clean baseline performance is evaluated at $s=0.00$:
$$\text{Macro-F1}_{\text{clean}}(m, r) = \text{Macro-F1}(X_{\text{test}}, y_{\text{test}} \mid m, r)$$
All shift operators must reproduce clean baseline performance bit-for-bit at $s=0.00$.

### 6.2 Primary Metric: Absolute Macro-F1 Degradation
$$\Delta_{\text{abs}}(s \mid m, \mathcal{P}, r) = \text{Macro-F1}_{\text{clean}}(m, r) - \text{Macro-F1}(X'(s), y_{\text{test}} \mid m, r)$$

### 6.3 Secondary Metrics
1. **Observed Failure Boundary ($s^*$):**
   $$s^* = \min \{ s \in S \mid \text{Macro-F1}(s) < 0.80 \}$$
2. **Area Under the Degradation Curve ($\text{AUDC}$):**
   $$\text{AUDC} = \sum_{k=1}^{|S|-1} \frac{\Delta_{\text{abs}}(s_{k-1}) + \Delta_{\text{abs}}(s_k)}{2} \cdot (s_k - s_{k-1})$$
3. **Per-Class Confusion Dynamics:**
   Tracking the direction of class transitions (e.g., $C_{\text{versicolor} \to \text{virginica}}$ vs. $C_{\text{versicolor} \to \text{setosa}}$) under directional shift.

---

## 7. Statistical Analysis & Multiple-Testing Control

### 7.1 Multi-Seed Aggregation
For each condition $(\text{Model } m, \text{Shift Operator } \mathcal{P}, \text{Severity } s)$ across $R=5$ seeds:
- Mean $\bar{M} = \frac{1}{R} \sum_{r=1}^R M_r$.
- Sample standard deviation with Bessel's correction: $S = \sqrt{\frac{1}{R-1} \sum_{r=1}^R (M_r - \bar{M})^2}$ ($ddof=1$).
- Standard error of the mean: $\text{SEM} = S / \sqrt{5}$.
- Two-sided 95% Confidence Interval using Student's $t$ with $\nu = 4$ degrees of freedom ($t_{0.025, 4} \approx 2.7764$).

### 7.2 Hypothesis Testing Procedure
1. **Omnibus Architecture Comparison ($H_1$):**
   - Friedman's test across the 3 models at $s=0.30$ paired by random seed ($N=5, k=3, df=2$).
   - Post-hoc pairwise model comparisons with Benjamini–Hochberg FDR control at $\alpha = 0.05$.
2. **Directional Asymmetry Test ($H_2$):**
   - Paired Student's $t$-test / Wilcoxon signed-rank test comparing terminal drop under positive vs. negative translation: $\bar{\Delta}(+0.30)$ vs. $\bar{\Delta}(-0.30)$.
3. **Shift vs. Corruption Comparison ($H_3$):**
   - Paired comparison of $s^*$ and $\text{AUDC}$ between directional shift and E001/E002 isotropic Gaussian noise.

---

## 8. Data Leakage Prevention and Protocol Safeguards

E006 enforces all five mandatory Model Autopsy isolation barriers:

| Isolation Barrier | Protocol Safeguard | Verification Check |
|---|---|---|
| **Split Isolation** | Stratified split frozen at `split_seed=42`; indices frozen in `iris.py`. | Automated test confirms $I_{\text{train}} \cap I_{\text{test}} = \emptyset$. |
| **Shift Parameter Isolation** | Translation magnitudes $s \cdot \sigma_j^{\text{train}}$ and centroids $\mu_j^{\text{train}}$ fitted strictly on $X_{\text{train}}$. | Test confirms shift parameters are identical if test set is altered. |
| **Preprocessing Isolation** | `StandardScaler` in `LogisticRegressionAdapter` fitted strictly on $X_{\text{train}}$. | Scaler mean and variance match $X_{\text{train}}$ bit-for-bit. |
| **Input Immutability** | $X_{\text{test}}$ marked non-writeable (`flags.writeable = False`). | Mutating input in-place raises `ValueError`. |
| **Deterministic Reproducibility** | All stochastic PRNG calls use explicit, isolated seeds. | Re-running produces bitwise-identical output hashes. |

---

## 9. Expected Artifact Schema and Output Structure

All artifacts will be saved to `artifacts/experiments/E006/`:

```
artifacts/experiments/E006/
├── metrics.json                     # Complete hierarchical execution record
├── shift_summary.csv                # Flattened tabular results across all conditions
├── shift_comparisons.json           # Formal hypothesis tests (H1-H4) and AUDC statistics
├── reproducibility_manifest.json    # Commit hash, environment, library versions, seed list
├── report.md                        # Formal research report with mandated caveats
└── figures/
    ├── covariate_shift_curves.png   # Degradation curves under directional shift
    ├── directional_asymmetry_bars.png # Bar chart comparing positive vs negative shift
    └── shift_vs_corruption_comparison.png # Comparison of shift vs isotropic noise degradation
```

---

## 10. Acceptance Criteria for E006 Completion

Experiment E006 will be declared complete and verified only when:

1. **Protocol Execution:** Evaluates 3 models $\times$ 3 shift operators $\times$ 7 severities $\times$ 5 seeds = **315 evaluation cells** (plus directional sub-regimes).
2. **Baseline Parity:** Macro-F1 matches clean baseline bit-for-bit at $s=0.00$ ($\Delta_{\text{abs}} = 0.0000$).
3. **Data Leakage Immunity:** Shift translation parameters and scalers have zero dependency on $X_{\text{test}}$.
4. **Statistical Rigor:** All reported intervals use Student's $t$ with $ddof=1$ ($\nu=4$), and all pairwise tests apply BH-FDR correction.
5. **Deterministic Reproducibility:** Back-to-back runs produce bitwise identical JSON/CSV outputs.
6. **Artifact Completeness:** All 5 required files and 3 publication figures exist, parse cleanly, and are non-empty.
7. **Mandatory Caveats:** The generated report contains the mandated non-causal caption and finite-sample disclaimers verbatim.
8. **Independent Scientific Audit:** Dedicated audit document (`docs/research/e006_scientific_audit.md`) is completed, confirming all findings with a formal verdict of **PASS**.

---

## 11. Scientific Limitations and Threats to Validity

1. **Sample Size Constraints ($N_{\text{test}} = 30$):**
   The test partition contains 30 instances (10 per class). Individual sample misclassifications induce discrete $3.33$ pp accuracy shifts.
2. **Label Invariance Assumption Under Extreme Translation:**
   Covariate shift assumes $P(Y \mid X)$ remains fixed. If an *Iris setosa* sample is shifted $+0.30 \cdot \boldsymbol{\sigma}$ along the petal axis, its physical dimensions approach those of a *versicolor*. The classifier's prediction of *versicolor* is technically a misclassification under fixed historical labels, but biologically represents a true change in morphology. E006 explicitly documents this semantic tension.
3. **Closed Benchmark Scope:**
   Findings on 4 continuous botanical features under synthetic translation do not generalize directly to natural covariate shifts in high-dimensional perceptual domains (e.g., changes in lighting in computer vision, or domain shift in language models).

---

## 12. Demarcation: Resolution of the Concept Drift Question

- **Preregistered Finding on Concept Drift:**
  - Concept drift ($P(Y \mid X)$ shifting over time) cannot be simulated on the static Fisher Iris benchmark without arbitrary, synthetic label permutation (e.g., relabeling *versicolor* as *virginica*).
  - Such synthetic label switching constitutes **label noise**, not authentic concept drift.
  - **Conclusion:** E006 focuses exclusively on mathematically defensible **Covariate Shift**. Authentic concept drift is formally deferred to future multi-dataset streaming extensions where ground-truth temporal or domain drift exists naturally.
