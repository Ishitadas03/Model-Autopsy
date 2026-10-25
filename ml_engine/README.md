# Model Autopsy — ML Engine

The `ml_engine` package is the core computational and scientific engine of the Model Autopsy platform. It executes deterministic stress-testing pipelines, calculates multi-metric performance degradation trajectories, characterizes failure boundaries, and synthesizes machine-readable reproducibility manifests.

---

## 🏗 Architecture & Modules

The package follows a modular scientific layout under `ml_engine/src/model_autopsy/`:

```
ml_engine/
├── src/
│   └── model_autopsy/
│       ├── datasets/          # Deterministic dataset ingestion & stratified splitting (e.g. iris.py)
│       ├── models/            # Explicit, serializable model adapters (e.g. sklearn_rf.py)
│       ├── stress_tests/      # Parameterized corruption operators (e.g. noise/gaussian.py)
│       ├── metrics/           # Evaluation metrics, degradation deltas, and failure criteria
│       ├── analysis/          # Failure boundary detection & empirical feature vulnerability
│       ├── visualization/     # Publication-grade robustness curve plotting
│       ├── reporting/         # Artifact synthesis, JSON manifests, and research markdown reports
│       └── experiments/       # High-level pipeline orchestrators (e.g. e001_runner.py)
└── tests/                     # Comprehensive pytest test suite (24 unit & integration tests)
```

---

## 🧪 Experiment E001: Gaussian Noise on Random Forest (Iris)

### 1. Research Question
> *"How does increasing the severity of Gaussian input noise affect the Macro-F1 performance of a Random Forest classifier on the Iris dataset?"*

### 2. Mathematical Noise Formulation
Perturbation is applied strictly to evaluation instances ($X_{\text{test}}$) scaled by training dispersion:

$$X'_{ij} = X_{ij} + \varepsilon_{ij}$$

$$\varepsilon_{ij} \sim \mathcal{N}\left(0, (s \cdot \sigma_j)^2\right)$$

where:
- $s \in \{0.00, 0.05, 0.10, 0.15, 0.20, 0.25, 0.30\}$ (dimensionless severity factor).
- $\sigma_j$ is the sample standard deviation ($ddof=1$) computed **strictly on the training partition** ($X_{\text{train}}$).
- At $s = 0.00$, the function returns an exact, bitwise identical copy of $X_{\text{test}}$.
- The original evaluation array is never mutated in-place.

### 3. Metric and Failure Definitions
- **Primary Metric:** Macro-Averaged F1-Score ($\text{Macro-F1}$).
- **Secondary Metric:** Classification Accuracy.
- **Absolute Degradation (percentage points):**
  $$\Delta_{\text{abs}}(s) = (\text{Macro-F1}(0) - \text{Macro-F1}(s)) \times 100$$
- **Relative Degradation (percentage):**
  $$\Delta_{\text{rel}}(s) = \frac{\text{Macro-F1}(0) - \text{Macro-F1}(s)}{\text{Macro-F1}(0)} \times 100\%$$
- **Primary Failure Criterion:**
  $$\text{Macro-F1}(s) < 0.80 \quad (\text{Strict less-than comparison})$$
- **Observed Failure Boundary ($s^*$):**
  $$s^* = \min \{ s \in S \mid \text{Macro-F1}(s) < 0.80 \}$$
  If no severity drops below $0.80$, the boundary is recorded as unobserved ($s^* > 0.30$).
- **Mandated Reporting Caption:**
  > *"Observed failure boundary under the specified experimental configuration."*
- **Empirical Feature Sensitivity Caveat:**
  > *"Empirical sensitivity — not a causal explanation."*

---

## 🚀 Setup & Execution

### Prerequisites
- Python $\ge 3.10$
- Dependencies: `numpy`, `scipy`, `scikit-learn`, `pandas`, `matplotlib`, `pydantic`, `pyyaml`, `pytest`

### Running Experiment E001
From the repository root:

```bash
# Execute single-seed validation run (Development Seed 42)
python scripts/experiments/run_e001.py

# Explicit seed and config
python scripts/experiments/run_e001.py --seed 42 --config configs/experiments/e001.yaml

# Execute full 5-seed research evaluation suite [42, 123, 456, 789, 1011]
python scripts/experiments/run_e001.py --multi-seed
```

### Running Automated Tests
```bash
# Run complete test suite (24 unit & integration tests)
python -m pytest ml_engine/tests -v
```

---

## 📦 Generated Artifacts

All outputs are saved to `artifacts/experiments/E001/`:

| Artifact | Format | Description |
|---|---|---|
| `results.csv` | CSV | Tabular metrics ($\text{Macro-F1}$, Accuracy, $\Delta_{\text{abs}}$, $\Delta_{\text{rel}}$, Failure Flag) per severity |
| `results.json` | JSON | Machine-readable results and configuration |
| `manifest.json` | JSON | Reproducibility metadata (Git SHA, Python/library versions, seeds, dataset hash) |
| `robustness_curve.png` | PNG | High-resolution publication chart with threshold line and failure regime |
| `report.md` | Markdown | Formal scientific report with findings, tables, and limitations |
| `baseline_metrics.json` | JSON | Exact baseline scores at $s=0.00$ |
| `robustness_curve.json` | JSON | Coordinate points for frontend visualization integration |
| `confusion_matrices/` | Directory | Per-severity $3 \times 3$ confusion matrices (`cm_s00.json` to `cm_s30.json`) |
| `failure_analysis.json` | JSON | Boundary finding and empirical feature vulnerability rankings |

---

## 🔒 Scientific Limitations & Threats to Validity

1. **Test Set Granularity:** With $N_{\text{test}} = 30$ samples (10 per class), a single misclassified sample alters accuracy and recall by $3.33\,\text{percentage points}$.
2. **Benchmark Scale:** The Iris dataset is small, low-dimensional ($D=4$), and possesses well-separated clusters; results do not directly extrapolate to high-dimensional or complex data modalities.
3. **Perturbation Specificity:** Additive Gaussian noise is a synthetic perturbation model and does not reflect structured, semantic, or adversarial corruptions.
4. **Non-Causal Sensitivity:** Feature rankings describe observational sensitivity under this perturbation, not causal mechanisms.

---

## 🔌 Backend Integration Contract (For Person 2)

Person 2 can invoke the ML Engine directly without any coupling to web frameworks:

```python
from model_autopsy.experiments.e001_runner import run_e001_experiment

# Trigger experiment asynchronously or in background worker
result = run_e001_experiment(
    config_path="configs/experiments/e001.yaml",
    seed=42,
    output_dir="artifacts/experiments/E001",
)
# Returns structured dictionary matching frontend-api-contract.md schema
```
