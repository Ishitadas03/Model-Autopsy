# Experimental Design & Protocol Specification: E004
## RQ7: Empirical Failure Pattern Analysis Across Multi-Model Robustness Evaluations

**Experiment ID:** `E004`  
**Experiment Title:** Fine-Grained Sample-Level Failure Pattern Analysis Across Model Architectures and Corruption Modalities on the Iris Benchmark  
**Research Question:** **RQ7 — What recurring patterns characterize model failures under controlled data corruption?**  
**Protocol Version:** 1.1.0 (Methodologically Clarified Specification)  
**Parent Documents:**
- [`docs/research/problem_statement.md`](problem_statement.md)
- [`docs/research/experimental_protocol.md`](experimental_protocol.md)
- [`docs/research/e002_experimental_design.md`](e002_experimental_design.md)
- [`docs/research/phase3_scientific_audit.md`](phase3_scientific_audit.md)
- [`docs/research/e003_experimental_design.md`](e003_experimental_design.md)
- [`docs/research/phase5_frontend_integration.md`](phase5_frontend_integration.md)  
**Author:** Person 1 (ML & Research Lead)  
**Target Context:** Model Autopsy ML Engine  
**Status:** Approved for Implementation (Step 5 Authorized)  

---

## 1. Executive Summary & Research Motivation

In Experiments E001 through E003, Model Autopsy established macro-level empirical robustness curves and failure boundaries across:
1. Multi-seed Gaussian noise degradation on Random Forest (E001).
2. Comparative corruption degradation across Gaussian noise, MCAR missingness, and impulsive outliers (E002).
3. Comparative cross-model degradation comparing Random Forest, Logistic Regression, and Gradient Boosting (E003).

While E003 provided definitive evidence regarding aggregate failure boundaries ($s^*_{\text{mean}}$ and $s^*_{\text{indiv}}$) and relative degradation trajectories, macro-averaged metrics (Macro-F1, Accuracy, Mean Confusion Matrices) inherently obscure the microscopic anatomy of model failure:
- **Do different models fail on the same test instances, or do distinct inductive biases yield disjoint failure sets?**
- **Once an instance is misclassified at severity $s$, does it remain misclassified as corruption deepens (absorbing error state), or do predictions oscillate?**
- **Are failures concentrated in specific classes or geometric regions of feature space (e.g., ambiguous decision boundaries)?**
- **How stable are failure patterns across independent research seeds?**

To address **RQ7**, Experiment **E004** establishes a fine-grained, sample-level failure pattern analysis. It bridges the gap between aggregate metrics and instance-level mechanics without compromising the controlled invariants established in E001–E003.

---

## 2. Audit of Existing Artifacts & The Sample-Level Data Gap

### 2.1 Audit of Existing Persisted Outputs
A thorough inspection of `artifacts/experiments/E001/`, `E002/`, and `E003/` was conducted to determine which raw outputs are already persisted:

| Artifact Dimension | E001 / E001_multi_seed | E002 | E003 | Persisted in Storage? |
| :--- | :---: | :---: | :---: | :---: |
| Aggregate metrics (Macro-F1, Accuracy) | Yes | Yes | Yes | **YES** |
| Per-class metrics (F1, Precision, Recall) | Yes | Yes | Yes | **YES** |
| $3 \times 3$ Confusion Matrices per severity | Yes | Yes | Yes | **YES** |
| Model hyperparameters & seed configs | Yes | Yes | Yes | **YES** |
| Dataset hash & partition sizes | Yes | Yes | Yes | **YES** |
| **Raw Per-Sample Predictions ($\hat{y}_{i,s}$)** | **NO** | **NO** | **NO** | **MISSING** |
| **Sample Identifiers / Split Test Indices** | **NO** | **NO** | **NO** | **MISSING** |
| **Instance Misclassification Indicator ($e_i \in \{0, 1\}$)** | **NO** | **NO** | **NO** | **MISSING** |
| **Class Prediction Probabilities ($P(y=k \mid x)$)** | **NO** | **NO** | **NO** | **MISSING** |
| **Feature Corruption Masks / Perturbation Vectors** | **NO** | **NO** | **NO** | **MISSING** |

### 2.2 Mathematical Non-Reconstructibility Proof
It is mathematically impossible to reconstruct sample-level error patterns from aggregate confusion matrices.

Let $N_{\text{test}} = 30$. An aggregate confusion matrix $C \in \mathbb{N}^{3 \times 3}$ at severity $s$ specifies only marginal counts:
$$C_{jk} = \sum_{i=1}^{N_{\text{test}}} \mathbb{I}(y_i = j \land \hat{y}_i = k)$$
Given two models $A$ and $B$ evaluated at severity $s$ with confusion matrices $C^{(A)}$ and $C^{(B)}$:
1. $C^{(A)}$ and $C^{(B)}$ indicate that model $A$ made $m_A = \sum_{j \ne k} C_{jk}^{(A)}$ errors and model $B$ made $m_B = \sum_{j \ne k} C_{jk}^{(B)}$ errors.
2. The intersection size $|\mathcal{E}_A \cap \mathcal{E}_B|$ (instances failed by both models) can take any integer value in:
   $$\max(0, m_A + m_B - N_{\text{test}}) \le |\mathcal{E}_A \cap \mathcal{E}_B| \le \min(m_A, m_B)$$
3. Similarly, given severity $s_1 < s_2$, the confusion matrices $C(s_1)$ and $C(s_2)$ cannot reveal whether an error at $s_1$ persisted at $s_2$.

### 2.3 Proposed Minimal Justified Additive Change
To close this gap without fabricating retrospective data or altering validated E001–E003 scientific outputs:
1. Implement a dedicated Experiment Runner: `E004Runner` (`ml_engine/src/model_autopsy/experiments/e004_runner.py`).
2. Execute the exact deterministic protocol of E003 (identical split seed 42, identical seeds `[42, 123, 456, 789, 1011]`, identical models, corruptions, and severities).
3. Concurrently capture and persist the complete 5D sample prediction tensor:
   $$\mathbf{Y} \in \{0, 1, 2\}^{M \times C \times R \times S \times N_{\text{test}}}$$
   where $M=3$ models, $C=3$ corruptions, $R=5$ research seeds, $S=7$ severities, and $N_{\text{test}}=30$ test instances ($3 \times 3 \times 5 \times 7 \times 30 = 9{,}450$ total atomic prediction records).
4. Persist all outputs in a dedicated, isolated directory: `artifacts/experiments/E004/`.

---

## 3. Shared Experimental Invariants & Protocol Safeguards

E004 strictly adheres to the frozen parameters established in the project protocol:

| Dimension | Invariant Specification | Justification |
| :--- | :--- | :--- |
| **Dataset** | Fisher Iris Benchmark ($N = 150$, 4 continuous features, 3 classes) | Canonical benchmark for E001–E003 continuity. |
| **Partitioning** | Stratified 80/20 train/test split (`split_seed = 42`) | Frozen train ($N_{\text{train}}=120$) and test ($N_{\text{test}}=30$). |
| **Test Set Sample Size** | **$N_{\text{test}} = 30$ ($n_k = 10$ instances per class)** | **Explicit limitation:** All sample-level failure metrics must disclose this sample-size constraint. |
| **Test Indices** | `[38, 127, 57, 93, 42, 56, 22, 20, 147, 84, 107, 141, 104, 51, 7, 49, 14, 69, 63, 138, 10, 140, 58, 134, 132, 77, 75, 18, 116, 28]` | Verified immutable test partition from `iris.py`. |
| **Research Seeds** | $R = 5$ independent seeds: `[42, 123, 456, 789, 1011]` | Captures statistical stability and variance. |
| **Severity Grid ($S$)** | 7 levels: `[0.00, 0.05, 0.10, 0.15, 0.20, 0.25, 0.30]` | Canonical grid. |
| **Model Architectures** | 1. Random Forest (`RandomForestClassifier`, 100 trees, gini)<br>2. Logistic Regression (`Pipeline(StandardScaler)`, lbfgs, C=1.0)<br>3. Gradient Boosting (`GradientBoostingClassifier`, 100 trees, lr=0.1, depth=3) | Identical to E003 specifications. |
| **Corruption Operators** | 1. Additive Gaussian Noise ($\sigma_k = s \cdot \text{std}_{\text{train}}$)<br>2. MCAR Missingness (mean imputation from $X_{\text{train}}$)<br>3. Impulsive Outliers ($+5\sigma_k$ spikes) | Identical to E002/E003 operators. |
| **Preprocessing Isolation** | `StandardScaler` fitted strictly on $X_{\text{train}}$ only | Zero data contamination / leakage. |
| **Primary Metric** | Macro-Averaged F1-Score ($\text{Macro-F1}$) | Primary failure threshold: $\text{Macro-F1} < 0.80$. |
| **Nominal Severity Rule** | Non-equivalence across corruption modalities | No claim that $s=0.10$ noise equals $s=0.10$ missingness. |

---

## 4. Methodological Clarifications & Mathematical Rigor

### 4.1 Nested-Filtration Guarantees by Corruption Modality

Reusing a random seed is not, by itself, mathematical proof of nested filtration. We establish explicit mathematical guarantees for each corruption operator:

1. **Additive Gaussian Noise**:
   - The operator `apply_gaussian_noise(X, train_std, s, seed)` uses `rng = np.random.default_rng(seed)` and draws `noise_matrix = rng.normal(0.0, s * train_std, size)`.
   - In NumPy, `normal(0, scale, size)` generates standard normal variates $\mathbf{Z} \sim \mathcal{N}(0, I)$ and scales them:
     $$\mathbf{E}_{ij}(s) = s \times (\text{train\_std}_j \times Z_{ij})$$
   - Because `seed` is fixed, $\mathbf{Z}$ is identical across all severities $s > 0$.
   - **Nested-Filtration Guarantee:** The perturbation trajectory for each test instance moves along a continuous, deterministic 1D linear ray in feature space:
     $$\mathbf{x}_i(s) = \mathbf{x}_i(0) + s \cdot \mathbf{v}_i, \quad \text{where } \mathbf{v}_{ij} = \text{train\_std}_j \times Z_{ij}$$
   - *Empirically verified*: $\frac{\mathbf{E}(0.10)}{\mathbf{E}(0.05)} \equiv 2.000000$ with zero numerical deviation.

2. **MCAR Missingness (Mean Imputed)**:
   - The operator `apply_feature_missingness_mcar(X, train_mean, s, seed)` draws uniform variates $\mathbf{U}_{ij} \sim \text{Uniform}(0, 1)$ using `np.random.default_rng(seed)`.
   - The missingness mask is defined by indicator $M_{ij}(s) = \mathbb{I}(\mathbf{U}_{ij} < s)$.
   - **Nested-Filtration Guarantee:** For any two severity levels $s_1 < s_2$:
     $$\mathbf{U}_{ij} < s_1 \implies \mathbf{U}_{ij} < s_2 \implies M_{ij}(s_1) \le M_{ij}(s_2)$$
   - Therefore, the set of masked cells satisfies strict subset inclusion:
     $$\mathcal{M}(s_1) \subseteq \mathcal{M}(s_2), \quad \text{where } \mathcal{M}(s) = \{(i, j) : M_{ij}(s) = 1\}$$
   - Every cell imputed at $s_1$ remains imputed with the exact same mean value $\text{train\_mean}_j$ at $s_2$.

3. **Impulsive Outliers ($5\sigma$)**:
   - The operator `apply_feature_outliers(X, train_mean, train_std, s, displacement_factor=5.0, seed)` draws:
     1. Uniform mask variates $\mathbf{U}_{ij} \sim \text{Uniform}(0, 1)$ ($N \times D$ PRNG steps).
     2. Discrete signs $\mathbf{S}_{ij} \in \{-1.0, +1.0\}$ via `rng.choice` ($N \times D$ PRNG steps).
   - **Nested-Filtration Guarantee:** Because step 1 always consumes the exact same number of PRNG draws ($N \times D$), the random signs $\mathbf{S}_{ij}$ are bit-for-bit identical across all severities $s > 0$.
   - Subset inclusion holds: $\mathcal{M}(s_1) \subseteq \mathcal{M}(s_2)$.
   - Every outlier coordinate active at $s_1$ remains an outlier coordinate at $s_2$ with the exact same direction and magnitude:
     $$\mathbf{x}_{ij}(s_2) = \mathbf{x}_{ij}(s_1) = \text{train\_mean}_j + \mathbf{S}_{ij} \cdot (5.0 \times \text{train\_std}_j)$$

### 4.2 Exact Definitions for Error Persistence and Oscillation Metrics

Let $S = (s_0, s_1, \dots, s_{|S|-1}) = (0.00, 0.05, 0.10, 0.15, 0.20, 0.25, 0.30)$ be the ordered severity grid.

1. **First-Error Severity ($s^*(i)$)**:
   $$s^*(i) = \begin{cases} \min \{s \in S : \hat{y}_i(s) \ne y_i\} & \text{if } \exists s \in S \text{ s.t. } \hat{y}_i(s) \ne y_i \\ \text{None (Unobserved, } > 0.30\text{)} & \text{if } \hat{y}_i(s) = y_i \; \forall s \in S \end{cases}$$

2. **Error Persistence Ratio ($\text{EPR}(i)$)**:
   Measures whether errors are absorbing states after their initial occurrence:
   $$\text{EPR}(i) = \begin{cases} \text{NA (Undefined)} & \text{if } s^*(i) = \text{None} \\ \frac{\sum_{s \in S, s \ge s^*(i)} \mathbb{I}(\hat{y}_i(s) \ne y_i)}{|\{s \in S : s \ge s^*(i)\}|} & \text{if } s^*(i) \in S \end{cases}$$
   - **Boundary Case 1 (Never Fails):** If $s^*(i) = \text{None}$, the evaluation set $\{s \ge s^*(i)\}$ is empty. Denominator is 0. $\text{EPR}(i)$ is defined as **`None` / `NA`**. It is excluded from the mean persistence calculation so as not to artificially skew persistence statistics.
   - **Boundary Case 2 (First Fails at $s = 0.30$):** $\{s \in S : s \ge 0.30\} = \{0.30\}$. Cardinality is 1. Numerator is 1. $\text{EPR}(i) = \frac{1}{1} = 1.0$.
   - **Boundary Case 3 (Baseline Error at $s = 0.00$):** $\{s \ge 0.00\} = S$ (size 7). Evaluated across all 7 severity steps.

3. **Prediction Oscillation Count ($\text{POC}(i)$)**:
   Counts prediction label changes across adjacent steps:
   $$\text{POC}(i) = \sum_{j=0}^{|S|-2} \mathbb{I}(\hat{y}_i(s_{j+1}) \ne \hat{y}_i(s_j))$$
   - Well-defined for all samples ($0 \le \text{POC}(i) \le 6$).
   - If a sample is always correct: $\text{POC}(i) = 0$.
   - If a sample fails once at $s=0.20$ and stays in that same incorrect class: $\text{POC}(i) = 1$.
   - If a sample fails at $0.10$, recovers at $0.15$, and fails again at $0.20$: $\text{POC}(i) = 3$.

### 4.3 Training-Derived Covariance & Mahalanobis Distance Analysis

To evaluate feature-space decision margin localization without data leakage:

1. **Training Class Centroids**:
   $$\mu_k = \frac{1}{N_{\text{train}, k}} \sum_{i \in \text{train}, y_i = k} \mathbf{x}_i, \quad k \in \{0, 1, 2\}, \; N_{\text{train}, k} = 40$$

2. **Pooled Training Covariance Matrix**:
   Computed strictly on training fold instances ($N_{\text{train}} = 120, K = 3, D = 4$):
   $$\Sigma_{\text{pooled}} = \frac{1}{N_{\text{train}} - K} \sum_{k=1}^K \sum_{i \in \text{train}, y_i = k} (\mathbf{x}_i - \mu_k)(\mathbf{x}_i - \mu_k)^T$$

3. **Numerical Conditioning & Singular Covariance Handling**:
   To prevent instability or division-by-zero on ill-conditioned sub-matrices, we apply Tikhonov ridge regularization:
   $$\Sigma_{\text{reg}} = \Sigma_{\text{pooled}} + \epsilon \cdot \mathbf{I}_D, \quad \epsilon = 10^{-6}$$
   guaranteeing positive definiteness ($\det(\Sigma_{\text{reg}}) > 0$) while preserving empirical covariance structure.

4. **Distance and Margin Estimands**:
   - Mahalanobis distance from test instance $\mathbf{x}_i$ to class centroid $\mu_k$:
     $$d_M(\mathbf{x}_i, \mu_k) = \sqrt{(\mathbf{x}_i - \mu_k)^T \Sigma_{\text{reg}}^{-1} (\mathbf{x}_i - \mu_k)}$$
   - Clean Opposing-Class Margin:
     $$\Delta_M(\mathbf{x}_i) = \min_{k \ne y_i} d_M(\mathbf{x}_i, \mu_k) - d_M(\mathbf{x}_i, \mu_{y_i})$$
     $\Delta_M(\mathbf{x}_i) > 0$ indicates the sample is closer to its true class centroid; smaller $\Delta_M$ denotes proximity to the decision boundary.

### 4.4 Benjamini–Hochberg False Discovery Rate (FDR) Families

Multiple hypothesis testing correction is organized into three distinct, pre-registered test families:

1. **Family 1: Inter-Model Error Concordance (Jaccard Pairwise Contrasts)**
   - Hypotheses: For each corruption modality, test whether pairwise error-set similarities $J(\text{RF}, \text{LR})$, $J(\text{RF}, \text{GB})$, and $J(\text{LR}, \text{GB})$ exceed chance level ($J > 0$).
   - Family Size: 3 model pairs $\times 7$ severities = **21 hypotheses per corruption family** (total 63 across corruptions).
   - Control: Benjamini-Hochberg FDR at nominal level $q = 0.05$.

2. **Family 2: Class Vulnerability Asymmetry**
   - Hypotheses: Test whether class error rate differences $\text{CER}_{\text{Versicolor}}(s) - \text{CER}_{\text{Virginica}}(s)$ differ from 0 across severities.
   - Family Size: 7 severity tiers per corruption family (**7 hypotheses**).
   - Control: Benjamini-Hochberg FDR at nominal level $q = 0.05$.

3. **Family 3: Boundary Proximity Margin Contrast**
   - Hypothesis: Mann-Whitney U test contrasting clean Mahalanobis margin $\Delta_M$ between Early-Failing instances ($s^*(i) \le 0.15$) and Resilient instances ($s^*(i) > 0.30$).
   - Family Size: 1 primary directional hypothesis test per model architecture (**3 hypotheses**).
   - Control: Bonferroni-Holm family-wise error rate control ($\alpha = 0.05$).

### 4.5 Separation of Seed-Level Variability from Sample-Level Uncertainty

1. **Fixed Evaluation Sample**:
   The test partition consists of exactly $N_{\text{test}} = 30$ instances ($10$ Setosa, $10$ Versicolor, $10$ Virginica).
   The five research seeds (`[42, 123, 456, 789, 1011]`) are **NOT** $5 \times 30 = 150$ independent samples.
2. **Sample-Level Uncertainty**:
   For any failure proportion $p = \frac{k}{30}$ (or $\frac{k}{10}$ per class) at a fixed seed, uncertainty reflects finite test sampling.
   - Estimator: Two-sided 95% Clopper-Pearson exact binomial confidence interval.
3. **Seed-Level Variability**:
   Reflects model initialization, bootstrap sampling, and stochastic corruption draws across the 5 independent seeds.
   - Estimator: Sample standard deviation ($ddof=1$) and Standard Error of the Mean ($\text{SEM} = \frac{\text{std}}{\sqrt{5}}$) with $df = 4, t_{\text{crit}} = 2.7764$.

### 4.6 E003 Reproduction & Tolerance Specifications

E004 executes the identical experimental configuration as E003. To ensure scientific consistency:

| Evaluated Result | Tolerance Standard | Criteria for Acceptance |
| :--- | :---: | :--- |
| **Dataset Ingestion** | Exact ($0$ tolerance) | SHA-256 hash `aa06b8...` and test indices match bit-for-bit. |
| **Clean Baseline Metrics ($s=0.00$)** | Exact ($0$ tolerance) | RF: $0.8997$, LR: $0.9333$, GB: $0.9333$ Macro-F1 at seed 42. |
| **Evidence Conservation Identity** | Exact ($0$ tolerance) | $\sum_{i=1}^{30} \mathbb{I}(\hat{y}_{i,s,m,c,r} \ne y_i) \equiv \sum_{j \ne k} C_{jk}^{(s,m,c,r)}$ for all 315 conditions. |
| **Confusion Matrix Reconstruction** | Exact ($0$ tolerance) | $C_{\text{reconstructed}} \equiv C_{\text{E003}}$ bit-for-bit. |
| **Aggregate Metric Values** | Float $< 10^{-6}$ | Macro-F1 and Accuracy agree with E003 to within floating-point roundoff. |

---

## 5. Required Output Artifacts (`artifacts/experiments/E004/`)

1. **`sample_predictions.json`**: Complete 5D evaluation record ($9{,}450$ atomic prediction events) with sample IDs, true labels, predictions, probabilities, and error flags.
2. **`failure_patterns_summary.json`**: Full quantitative synthesis including class error rates, persistence ratios ($\text{EPR}$), oscillation counts ($\text{POC}$), pairwise Jaccard matrices, and Mahalanobis margins.
3. **`sample_level_metrics.csv`**: Flattened tabular export for analysis.
4. **`manifest.json`**: Cryptographic provenance hashes.
5. **`report.md`**: Formal research synthesis report addressing RQ7.
6. **`failure_patterns_analysis.png`**: Multi-panel visualization:
   - Panel A: Class-wise error rate trajectories ($0.00 \to 0.30$).
   - Panel B: Error persistence ratio distribution and first-error severities.
   - Panel C: Inter-model Jaccard error-set similarity matrices.
   - Panel D: 2D feature-space projection depicting consensus vs unique error samples.
