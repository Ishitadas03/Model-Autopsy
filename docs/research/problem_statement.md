# Research Problem Statement: Model Autopsy

**Project Title:** Model Autopsy — Find Out Why AI Models Fail  
**Document Version:** 1.0.0  
**Target Context:** B.Tech CSE-AIML Research Project & Empirical ML Robustness Foundation  
**Status:** Approved Specification  

---

## 1. Project Overview

**Model Autopsy** is a research framework and evaluation platform designed to systematically examine the empirical behavior, robustness limits, and failure modes of machine learning (ML) models under controlled input corruptions and data stress conditions.

In classical machine learning workflows, model evaluation is predominantly conducted by computing point-estimate performance metrics (such as accuracy, F1-score, or mean squared error) over an independent and identically distributed (i.i.d.) test set drawn from the same distribution as the training data. While necessary for benchmarking nominal capacity, this aggregate paradigm provides minimal visibility into how a trained model behaves when inputs undergo measurement noise, sensory degradation, missing values, feature-level corruptions, or distribution shifts.

The primary research purpose of Model Autopsy is to transition model assessment from static, single-point validation to a structured "stress-testing" methodology—analogous to physical materials testing or medical autopsy—where the breakdown points, degradation curves, and behavioral vulnerabilities of predictive models are rigorously identified, isolated, and documented under reproducible experimental protocols.

The intended users of Model Autopsy include:
- **Machine Learning Researchers and Students:** Investigating empirical model robustness, out-of-distribution behavior, and stress-testing methodologies.
- **ML Quality and Validation Engineers:** Auditing predictive pipelines against operational hazards prior to deployment.
- **Safety and Reliability Auditors:** Requiring reproducible artifacts, failure boundary estimations, and transparent audit trails for model behavior under non-ideal input regimes.

---

## 2. Background and Motivation

Standard statistical learning theory relies heavily on the assumption that training and test samples are drawn from the identical underlying probability distribution:

$$P_{\text{train}}(X, Y) = P_{\text{test}}(X, Y)$$

In real-world deployment settings, this assumption is regularly violated. Models encounter physical sensor noise, environmental distortions, transmission loss, numerical quantization, feature corruption, and semantic shifts in input feature distributions. When an ML model encounters corrupted inputs:
1. **Aggregate metrics obscure critical sub-population and sample-level failures:** A model maintaining an aggregate accuracy of 85% under moderate corruption may experience a 100% failure rate on a safety-critical sub-class or specific feature slice.
2. **Nominal test accuracy correlates poorly with out-of-distribution robustness:** Prior empirical research has repeatedly demonstrated that models with near-identical clean test performance can exhibit drastically divergent degradation rates when exposed to systematic input perturbations.
3. **The failure boundary is rarely characterized:** Practitioners often do not know at what corruption magnitude ($s^*$) a model crosses from an acceptable operating regime into an unacceptably degraded state.

To address these vulnerabilities, robust evaluation demands:
- **Controlled Perturbations:** Applying mathematically well-defined, parameterized corruptions to isolate specific vulnerability vectors.
- **Robustness Evaluation across Continuous Severities:** Measuring performance trajectory across systematically stepped corruption intensities rather than evaluating a single arbitrary noise level.
- **Failure Analysis:** Dissecting the specific misclassification patterns, confusion transitions, and feature sensitivities that arise as corruption scales.
- **Reproducible Experimentation:** Enforcing strict seed management, immutable dataset partitioning, frozen preprocessing pipelines, and deterministic experiment manifests to ensure scientific verifiability.

---

## 3. Research Problem

### The Scientific Gap
Standard machine learning validation treats model performance as a scalar value under nominal test conditions. However, there is a fundamental gap between measuring **aggregate predictive performance on clean data** and **systematically characterizing performance degradation dynamics and failure behaviors under controlled stress conditions**.

Specifically, the literature and current tooling present the following open empirical challenges:
1. **Degradation Trajectory Uncertainty:** It is often unknown whether performance degrades linearly, exponentially, or exhibits a sharp catastrophic collapse (cliff effect) as input corruption increases.
2. **Class and Feature Asymmetry:** Models rarely fail uniformly across all classes or feature dimensions; identifying which subsets are intrinsically fragile requires fine-grained stress decomposition.
3. **Absence of Standardized Empirical Failure Boundaries:** Operational definitions of what constitutes a "failure point" vary, and methods to empirically locate the corruption severity at which a model breaches a predefined reliability threshold under controlled conditions are not systematically embedded into evaluation pipelines.

### Distinguishing Engineering Objectives from Scientific Questions
To maintain scientific rigor, Model Autopsy explicitly separates its engineering infrastructure from its scientific research questions:

- **Engineering Objective:** To design and build an extensible, reproducible, modular software platform that executes parameterized perturbation pipelines, calculates standardized multi-metric degradation, visualizes robustness curves, logs full reproducibility manifests, and surfaces sample-level failure diagnostics.
- **Scientific Questions:** To determine how different model architectures, inductive biases, feature distributions, and hyperparameter configurations influence the rate of performance decay, the emergence of specific failure modes, and the location of empirical failure boundaries under controlled input perturbations.

---

## 4. Primary Research Question

The central research question guiding the Model Autopsy project is:

> **"How does increasing input corruption affect the reliability of machine learning models, and how can their failure behaviour be systematically measured and characterized under controlled experimental conditions?"**

---

## 5. Research Objectives

The project pursues the following progressive research objectives:

1. **Establish Clean-Data Baseline Performance:** Measure and verify reference performance metrics (Macro-F1, Accuracy, per-class metrics, confusion matrix) on uncorrupted validation/test splits.
2. **Measure Performance Degradation Across Increasing Corruption Severities:** Quantify both absolute and relative degradation across an ordered, parameterized sequence of stress levels.
3. **Compare Different Corruption Types:** Evaluate model sensitivity across diverse perturbation families (e.g., additive Gaussian noise, uniform noise, feature dropout/missingness, salt-and-pepper noise, out-of-range outlier injection).
4. **Investigate Feature-Wise and Class-Wise Failure Patterns:** Dissect confusion matrix shifts, class-specific recall deterioration, and empirical feature vulnerability rankings under stress.
5. **Compare Models Under Consistent Experimental Conditions:** Benchmark multiple distinct model families (e.g., Random Forests, Gradient Boosted Trees, Support Vector Machines, Multi-Layer Perceptrons) against identical train/test splits, preprocessing chains, and corruption sequences.
6. **Estimate Observed Failure Boundaries Using Predefined Reliability Criteria:** Determine the lowest corruption severity at which a model's performance drops below an a priori fixed reliability threshold.
7. **Evaluate Uncertainty and Consistency Across Repeated Experiments:** Assess variance and empirical stability by running multi-seed experiment batches across fixed seed suites.
8. **Support Reproducible Experiments and Research Reporting:** Package datasets, preprocessing artifacts, random seeds, software environments, and evaluation metrics into self-contained, machine-readable reproducibility manifests and structured research reports.

> *Note on Scope:* These objectives represent the overarching research agenda for the Model Autopsy initiative. The initial baseline experiment (E001) implements a focused subset of these objectives to establish a validated empirical benchmark.

---

## 6. Initial Research Experiment: E001

The inaugural experiment, designated **E001**, serves as the foundational benchmark to validate the stress-testing framework on a well-understood canonical dataset before extending to higher-dimensional or domain-specific benchmarks.

### 6.1 Experiment Specification

| Parameter | Specification |
|---|---|
| **Experiment ID** | `E001` |
| **Research Question** | *How does Gaussian input noise affect the Macro-F1 performance of a Random Forest classifier on the Iris dataset?* |
| **Dataset** | Iris Flower Dataset (Fisher, 1936 / UCI ML Repository) |
| **Task Type** | Multi-class tabular classification (3 classes, 4 continuous features) |
| **Model** | Random Forest Classifier (`sklearn.ensemble.RandomForestClassifier`) |
| **Primary Metric** | Macro-Averaged F1-Score ($\text{Macro-F1}$) |
| **Secondary Metrics** | Classification Accuracy, Per-Class Precision/Recall/F1, Confusion Matrix |
| **Initial Development Seed** | `42` |
| **Planned Research Multi-Seed Suite** | `[42, 123, 456, 789, 1011]` |
| **Perturbation Type** | Additive Gaussian Feature Noise |
| **Noise Severity Levels ($s$)** | `[0.00, 0.05, 0.10, 0.15, 0.20, 0.25, 0.30]` (0%, 5%, 10%, 15%, 20%, 25%, 30%) |
| **Evaluation Outputs** | Baseline metrics ($s=0$), stressed metrics ($s > 0$), absolute degradation ($\Delta_{\text{abs}}$), relative degradation ($\Delta_{\text{rel}}$), robustness curves, reproducibility manifest, and preliminary failure analysis |

---

### 6.2 Mathematical Definition of Perturbation

For a dataset containing $N$ samples and $D$ continuous features, let $X_{ij}$ denote the original, unperturbed value of feature $j \in \{1, \dots, D\}$ for test sample $i \in \{1, \dots, N\}$.

The perturbed test value $X'_{ij}$ is defined as:

$$X'_{ij} = X_{ij} + \varepsilon_{ij}$$

where the perturbation term $\varepsilon_{ij}$ is sampled from a zero-mean Gaussian distribution scaled proportionally to the feature's empirical dispersion:

$$\varepsilon_{ij} \sim \mathcal{N}\left(0, \, (s \cdot \sigma_j)^2\right)$$

- $s \in [0.0, 1.0]$ represents the **noise severity factor** (expressed as a fraction, e.g., $s=0.10$ for 10% noise).
- $\sigma_j$ is the **sample standard deviation of feature $j$ estimated exclusively from the training partition**:
  
  $$\sigma_j = \sqrt{\frac{1}{N_{\text{train}} - 1} \sum_{k=1}^{N_{\text{train}}} \left(X^{\text{train}}_{kj} - \bar{X}^{\text{train}}_j\right)^2}$$

#### Methodological Guarantees:
1. **Strict Data Leakage Prevention:** $\sigma_j$ is computed strictly on $X_{\text{train}}$. Under no circumstances is test data used to compute feature standard deviations or fit preprocessing scalers.
2. **Frozen Split and Preprocessing Protocol:** The train/test split (e.g., stratified 80/20 split) is generated once using the documented seed and held strictly identical across all severity evaluations $s \in \{0.00, \dots, 0.30\}$.
3. **Target Isolation:** Perturbations are applied **exclusively to test inputs** ($X_{\text{test}}$) during evaluation. Training inputs ($X_{\text{train}}$) and ground truth labels ($Y_{\text{test}}$) remain uncorrupted.
4. **No Synthetic Result Fabrication:** All metric numbers, degradation statistics, and curves must be generated via actual execution of the Python test pipeline; no hypothetical or mocked values may be substituted in scientific reporting.

---

## 7. Evaluation Criteria and Metrics

To measure performance and characterize degradation rigorously, the following metrics and analytical constructs are formally defined:

### 7.1 Macro-Averaged F1-Score ($\text{Macro-F1}$) — Primary Metric
For a $K$-class classification problem, Macro-F1 computes the unweighted arithmetic mean of F1-scores across all classes:

$$\text{Macro-F1} = \frac{1}{K} \sum_{k=1}^K \text{F1}_k = \frac{1}{K} \sum_{k=1}^K \frac{2 \cdot \text{Precision}_k \cdot \text{Recall}_k}{\text{Precision}_k + \text{Recall}_k}$$

*Rationale:* In multi-class evaluation, Macro-F1 treats all classes with equal importance, preventing majority-class dominance from masking catastrophic failures on smaller or more vulnerable classes.

### 7.2 Classification Accuracy — Secondary Metric
The fraction of total test samples correctly predicted:

$$\text{Accuracy} = \frac{1}{N_{\text{test}}} \sum_{i=1}^{N_{\text{test}}} \mathbb{I}\left(\hat{y}_i = y_i\right)$$

### 7.3 Absolute Performance Degradation ($\Delta_{\text{abs}}$)
The arithmetic difference between baseline performance ($s=0$) and performance at corruption severity $s$:

$$\Delta_{\text{abs}}(s) = M(0) - M(s)$$

where $M(s)$ is the metric value (e.g., Macro-F1) at severity $s$. For bounded metrics in $[0, 1]$, $\Delta_{\text{abs}}$ is reported in **percentage points (pp)**.

### 7.4 Relative Performance Degradation ($\Delta_{\text{rel}}$)
The percentage loss in performance relative to the baseline score:

$$\Delta_{\text{rel}}(s) = \begin{cases} 
\dfrac{M(0) - M(s)}{M(0)} \times 100\%, & \text{if } M(0) > 0 \\ 
0\%, & \text{if } M(0) = 0 
\end{cases}$$

### 7.5 Robustness Curve
The empirical function plotting metric performance $M(s)$ against severity $s \in [s_{\min}, s_{\max}]$. The trajectory of this curve indicates whether degradation is:
- **Resilient/Plateauing:** Minimal degradation over initial severity increases.
- **Gracefully Degrading:** Gradual, approximately linear decay.
- **Catastrophic/Cliff:** Abrupt, nonlinear drop-off past a critical threshold.

### 7.6 A Priori Failure Threshold and Observed Failure Boundary
- **A Priori Reliability Criterion:** A minimum acceptable performance threshold ($M_{\text{threshold}}$, e.g., $\text{Macro-F1} \ge 0.80$ or $\Delta_{\text{abs}} \le 15\,\text{pp}$) must be **justified and frozen prior to running the experiment**. Selecting a threshold retrospectively after viewing results introduces confirmation bias and invalidates boundary objectivity.
- **Observed Failure Boundary ($s^*$):** The minimum tested severity level $s$ at which the observed metric falls below the predefined reliability threshold:
  
  $$s^* = \min \left\{ s \in \{s_0, s_1, \dots, s_m\} \mid M(s) < M_{\text{threshold}} \right\}$$

- **Mandatory Reporting Caption:** Any reported boundary must be accompanied by the explicit disclaimer:
  > *"Observed failure boundary under the specified experimental configuration."*

---

## 8. Expected Outcomes

Upon execution of experiment E001, the system will produce concrete, auditable research artifacts:

1. **Baseline Evaluation Artifact:** Complete metric profile of the trained Random Forest model on pristine test data ($s=0$).
2. **Severity-Wise Evaluation Table:** A structured tabular record documenting $s$, Macro-F1, Accuracy, Per-Class F1, $\Delta_{\text{abs}}$, and $\Delta_{\text{rel}}$ for all configured severity steps ($s \in \{0.00, 0.05, 0.10, 0.15, 0.20, 0.25, 0.30\}$).
3. **Empirical Robustness Curves:** Visual and tabular representations of $\text{Macro-F1}(s)$ and $\text{Accuracy}(s)$.
4. **Reproducibility Manifest:** A JSON/YAML manifest capturing the exact Git commit SHA, Python runtime environment, library versions (`scikit-learn`, `numpy`), random seeds, model hyperparameters, dataset hash, and preprocessing parameters.
5. **Preliminary Failure Analysis:** Class confusion flow analysis showing which Iris species (e.g., *Iris versicolor* vs. *Iris virginica*) experience boundary confusion under noise.
6. **Observed Failure Boundary Estimate:** A documented value for $s^*$, produced **only if** the predefined reliability criterion is crossed within the tested severity window $[0.00, 0.30]$. If performance remains above the threshold throughout the range, the artifact must record $s^* > 0.30$ (unobserved within tested bounds).

---

## 9. Scope

To ensure deliverability and experimental integrity, the project enforces a clear separation between initial MVP deliverables and future research phases:

```
┌─────────────────────────────────────────────────────────────────────────┐
│                          PROJECT SCOPE MATRIX                           │
├────────────────────────────────────┬────────────────────────────────────┤
│       CURRENT MVP (Phase 1)        │      FUTURE EXTENSIONS (Phase 2+)   │
├────────────────────────────────────┼────────────────────────────────────┤
│ • Canonical Dataset: Iris          │ • Complex Tabular, Text, & Vision  │
│ • Model: Random Forest Classifier  │ • Multi-Model Benchmark (GBM, SVM, │
│ • Single Perturbation: Gaussian     │   MLP, Deep Neural Networks)       │
│   Additive Feature Noise           │ • Broad Perturbation Taxonomy:     │
│ • Severity Range: 0% to 30%        │   Missingness, Outliers, Drift,    │
│ • Metrics: Macro-F1, Accuracy,     │   Salt & Pepper, Label Noise       │
│   Confusion Matrix                 │ • Statistical Uncertainty Analysis │
│ • Single-Seed Baseline & Validated │   (Confidence intervals, bootstrap)│
│   Multi-Seed Execution Spec        │ • Advanced Automated Autopsy:      │
│ • Standard Reproducibility Manifest│   SHAP/LIME stress sensitivity,    │
│                                    │   subgroup slicing, causal audits  │
└────────────────────────────────────┴────────────────────────────────────┘
```

---

## 10. Research Limitations

Honest characterization of methodological boundaries is essential to prevent overstated claims. The following limitations apply to the Model Autopsy research framework:

1. **Benchmark Scale Limitations:** The Iris dataset is a low-dimensional (4 features), small-sample (150 instances) benchmark. Empirical findings on Iris serve as proof-of-methodology and cannot be generalized to high-dimensional or non-tabular domains without empirical validation.
2. **No Universal Robustness Claims:** Observing high resilience or rapid failure in a Random Forest on a single dataset does not establish universal robustness properties for tree-based models generally.
3. **Protocol and Parameter Dependency:** All quantitative findings are strictly conditional on the specific train/test split ratio, random seed, preprocessing scaling, perturbation definition ($\sigma_j$ scaling), and tested severity range.
4. **Noise Realism Boundaries:** Isotropic additive Gaussian noise is a mathematical abstraction; it does not capture all physical corruptions, structured adversarial perturbations, semantic covariate shifts, or non-linear sensor defects.
5. **Empirical Sensitivity is Not Causality:** Feature vulnerability rankings reflect observational sensitivity under specific perturbations and must not be interpreted as causal explanations of model decision logic.
6. **Conditional Nature of Failure Boundaries:** The observed failure boundary $s^*$ is an empirical artifact of the chosen reliability threshold ($M_{\text{threshold}}$) and experimental setup, not an intrinsic physical constant of the model.

---

## 11. Success Criteria

The completion of the research foundation and initial experiment E001 will be evaluated against the following objective, verifiable criteria:

- [ ] **Baseline Execution:** The Random Forest classifier trains and evaluates on uncorrupted test data ($s=0$), outputting baseline Macro-F1 and Accuracy without errors.
- [ ] **Full Severity Sweep:** The test suite evaluates all seven configured noise severity levels ($s \in \{0.00, 0.05, 0.10, 0.15, 0.20, 0.25, 0.30\}$) deterministically.
- [ ] **Mathematical Correctness:** Metric computations ($\text{Macro-F1}$, $\text{Accuracy}$, $\Delta_{\text{abs}}$, $\Delta_{\text{rel}}$) and noise transformations ($X'_{ij} = X_{ij} + \varepsilon_{ij}$ using training standard deviations $\sigma_j$) are validated by unit tests.
- [ ] **Curve Generation:** A complete robustness curve table and visualization dataset are emitted directly from verified experimental runs.
- [ ] **Manifest Completeness:** An experiment manifest is generated containing model hyperparameters, dataset checksums, random seed (`42`), and environmental dependencies.
- [ ] **Deterministic Reproducibility:** Re-executing the experiment pipeline with seed `42` on the same environment produces bitwise identical evaluation metrics and degradation values.
- [ ] **Code Quality & Testing:** All ml-engine modules are accompanied by unit test coverage verifying split isolation, zero test leakage, and deterministic perturbation generation.

---

## 12. References and Further Reading

The theoretical framing, robustness protocols, and reproducibility standards of Model Autopsy are grounded in the following foundational literature:

1. **Hendrycks, D., & Dietterich, T. (2019).** Benchmarking Neural Network Robustness to Common Corruptions and Perturbations. *Proceedings of the International Conference on Learning Representations (ICLR 2019).* [arXiv:1903.12261](https://arxiv.org/abs/1903.12261)
2. **Koh, P. W., Sagawa, S., Marklund, H., Xie, S. M., Zhang, M., Balsubramani, A., ... & Liang, P. (2021).** WILDS: A Benchmark of in-the-Wild Distribution Shifts. *International Conference on Machine Learning (ICML 2021)*, PMLR 139:5637-5664.
3. **Sculley, D., Holt, G., Golovin, D., Davydov, E., Phillips, T., Ebner, D., Chaudhary, V., Young, M., Crespo, J. F., & Dennison, D. (2015).** Hidden Technical Debt in Machine Learning Systems. *Advances in Neural Information Processing Systems (NeurIPS 2015)*, 28:2503-2511.
4. **Pineau, J., Vincent-Lamarre, P., Sinha, K., Larivière, V., Beygelzimer, A., d'Alché-Buc, F., Fox, E., & Larochelle, H. (2021).** Improving Reproducibility in Machine Learning Research (A Report from the NeurIPS 2019 Reproducibility Program). *Journal of Machine Learning Research (JMLR)*, 22(164):1-20.
5. **Ribeiro, M. T., Wu, T., Guestrin, C., & Singh, S. (2020).** Beyond Accuracy: Behavioral Testing of NLP Models with CheckList. *Proceedings of the 58th Annual Meeting of the Association for Computational Linguistics (ACL 2020)*, pp. 4902-4912.
6. **Breiman, L. (2001).** Random Forests. *Machine Learning*, 45(1), 5-32.
7. **Fisher, R. A. (1936).** The use of multiple measurements in taxonomic problems. *Annals of Eugenics*, 7(2), 179-188.
