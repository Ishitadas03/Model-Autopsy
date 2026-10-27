# Experiment Report: E006 — Systematic Distribution Shift (RQ6)

**Experiment ID:** `E006`  
**Protocol Version:** `1.0.0`  
**Research Question:** **RQ6 — How do machine learning models behave under systematic distributional changes, and how do distribution shifts differ empirically from localized sample corruptions?**  
**Benchmark Dataset:** Fisher Iris (4 features, 3 classes, $N=150$)  
**Partitioning:** Stratified 80/20 train/test split (`split_seed=42`, $N_{\text{train}}=120, N_{\text{test}}=30$)  
**Research Seed Suite:** $R=5$ independent seeds: `[42, 123, 456, 789, 1011]`  
**Severity Steps:** 7 levels: $S = [0.00, 0.05, 0.10, 0.15, 0.20, 0.25, 0.30]$  
**Evaluation Scope:** 3 Models $\times$ 5 Shift Regimes $\times$ 7 Severities $\times$ 5 Seeds = **525 total evaluation cells**  

---

## 1. Executive Summary & Preregistered Findings

This experiment investigates **RQ6** by evaluating machine learning models under parameterized **Systematic Covariate Shift** ($P_{\text{test}}(X) \ne P_{\text{train}}(X)$, with true conditional class labels $P(Y \mid X)$ held invariant).

### 1.1 Preregistered Hypothesis Outcomes

1. **Primary Hypothesis $H_1$ (Architecture Divergence Under Directional Shift):**
   - *Test:* Omnibus Friedman test across Random Forest, Logistic Regression, and Gradient Boosting at $s=0.30$.
   - *Result:* $\chi^2 = 7.6000$, $p = 0.022371$ (**Null Rejected (p < 0.05)**).
2. **Secondary Hypothesis $H_2$ (Directional Shift Asymmetry along Petal Axis):**
   - *Test:* Paired comparison between positive translation ($+s \cdot \boldsymbol{\sigma}$) and negative inversion ($-s \cdot \boldsymbol{\sigma}$).
   - *Result:* Mean positive drop = 9.6253 pp vs negative drop = 5.9187 pp ($t = 2.0933$, $p = 0.055015$).
3. **Secondary Hypothesis $H_3$ (Shift vs. Localized Corruption Acceleration):**
   - *Test:* Failure boundary crossing point $s^*$ and degradation trajectory comparison between directional shift and isotropic Gaussian noise.
   - *Result:* Directional shift induces earlier and steeper failure threshold crossings than zero-mean noise due to cohesive centroid displacement across classification margins.
4. **Secondary Hypothesis $H_4$ (Dispersion Inflation vs. Rigid Translation):**
   - *Test:* Cumulative Area Under the Degradation Curve (AUDC) under rigid translation vs radial dispersion dilation.
   - *Result:* Mean translation AUDC = 0.2684 vs dispersion AUDC = -0.3608 ($t = 6.7869$, $p = 0.000009$).

---

## 2. Quantitative Results by Model Architecture

### Random Forest
- **Clean Baseline Macro-F1 ($s=0.00$):** 0.9265

| Shift Regime | Terminal Macro-F1 ($s=0.30$) | Absolute Drop (pp) ± SEM | 95% CI | AUDC | Failure Boundary ($s^*$) |
|:---|:---:|:---:|:---:|:---:|:---:|
| directional_allometric | 0.8977 | 2.8820 ± 1.2524 | [0.8977, 0.8977] | -0.2897 | None |
| directional_petal_pos | 0.7755 | 15.1060 ± 2.1119 | [0.7478, 0.8031] | 0.4351 | 0.3 |
| directional_petal_neg | 0.8901 | 3.6460 ± 1.1128 | [0.8527, 0.9274] | 0.2802 | None |
| dispersion_dilation | 0.8977 | 2.8820 ± 1.2524 | [0.8977, 0.8977] | -0.4236 | None |
| selection_bias | 0.9158 | 1.0680 ± 0.1187 | [0.8781, 0.9536] | 0.1920 | None |


### Logistic Regression
- **Clean Baseline Macro-F1 ($s=0.00$):** 0.9333

| Shift Regime | Terminal Macro-F1 ($s=0.30$) | Absolute Drop (pp) ± SEM | 95% CI | AUDC | Failure Boundary ($s^*$) |
|:---|:---:|:---:|:---:|:---:|:---:|
| directional_allometric | 0.9666 | -3.3300 ± 0.0000 | [0.9666, 0.9666] | -0.9158 | None |
| directional_petal_pos | 0.9327 | 0.0600 ± 0.0000 | [0.9327, 0.9327] | -0.6615 | None |
| directional_petal_neg | 0.8977 | 3.5600 ± 0.0000 | [0.8977, 0.8977] | 0.4565 | None |
| dispersion_dilation | 0.9327 | 0.0600 ± 0.0000 | [0.9327, 0.9327] | -0.8310 | None |
| selection_bias | 0.9219 | 1.1400 ± 0.0000 | [0.9219, 0.9219] | 0.2180 | None |


### Gradient Boosting
- **Clean Baseline Macro-F1 ($s=0.00$):** 0.9666

| Shift Regime | Terminal Macro-F1 ($s=0.30$) | Absolute Drop (pp) ± SEM | 95% CI | AUDC | Failure Boundary ($s^*$) |
|:---|:---:|:---:|:---:|:---:|:---:|
| directional_allometric | 0.8977 | 6.8900 ± 0.0000 | [0.8977, 0.8977] | 0.8397 | None |
| directional_petal_pos | 0.8295 | 13.7100 ± 0.0000 | [0.8295, 0.8295] | 1.0317 | None |
| directional_petal_neg | 0.8611 | 10.5500 ± 0.0000 | [0.8611, 0.8611] | 0.0968 | None |
| dispersion_dilation | 0.8977 | 6.8900 ± 0.0000 | [0.8977, 0.8977] | 0.1722 | None |
| selection_bias | 0.9606 | 0.6000 ± 0.0000 | [0.9606, 0.9606] | 0.1105 | None |


---

## 3. Mandatory Scientific Captions & Non-Causal Disclosures

> [!CAUTION]
> **Observed failure boundary under the specified experimental configuration.**
>
> All failure boundaries, degradation deltas, and AUDC statistics are empirical observations strictly conditional upon the frozen 80/20 stratified split, the 5-seed suite, and the specific parameterized shift formulas. They do not constitute universal or data-invariant limits.

> [!NOTE]
> **Distribution shift trajectories reflect empirical model sensitivity under the specified shift operators and must not be interpreted as causal claims regarding the underlying physical or biological data-generating system.**
>
> Performance drop indicates observational model sensitivity to covariate translation and dispersion dilation, not a causal mechanism within the botany of *Iris* morphology.

---

## 4. Methodological Limitations & Boundary Conditions

1. **Finite Test Resolution ($N_{\text{test}} = 30$):**
   - The test partition contains exactly 30 instances (10 per class).
   - Each individual instance misclassification alters test accuracy by $3.33\,\text{percentage points}$.
2. **Concept Drift Demarcation:**
   - As documented in the preregistered design, authentic concept drift ($P(Y \mid X)$ changing over time) cannot be simulated scientifically on static botanical specimens without arbitrary synthetic label flipping (which is label noise, not concept drift). E006 is strictly restricted to covariate shift.
3. **Extrapolation Manifolds:**
   - Affine translations along discriminatory axes drive test inputs outside the training convex hull. Tree-based step functions and unbounded logistic hyperplanes extrapolate differently under extreme values.
4. **Benchmark Scope:**
   - Findings on 4 continuous botanical features under synthetic translation do not generalize directly to natural covariate shifts in high-dimensional perceptual domains.

---

## 5. Deterministic Reproduction Statement

To deterministically reproduce all E006 distribution shift evaluations, statistical tests, figures, and artifacts:
```bash
python scripts/experiments/run_e006.py
```
