# Model Autopsy

### Find Out Why AI Fails

Model Autopsy is a research-oriented machine learning testing laboratory
designed to evaluate how models behave under challenging conditions.
Instead of reporting accuracy alone, it investigates **when a model
becomes unreliable, which inputs trigger failures, and what evidence may
explain those failures**.

> **Project status:** Research prototype concept / development
> blueprint. Features described below are proposed capabilities unless
> explicitly marked as implemented in your repository. This README does
> not claim that the system is already built or validated.

------------------------------------------------------------------------

## Table of Contents

-   [Overview](#overview)
-   [Problem Statement](#problem-statement)
-   [Goals](#goals)
-   [Key Features](#key-features)
-   [How It Works](#how-it-works)
-   [Failure Boundary](#failure-boundary)
-   [Proposed Architecture](#proposed-architecture)
-   [Technology Stack](#technology-stack)
-   [Supported Experiments](#supported-experiments)
-   [Metrics](#metrics)
-   [Research Methodology](#research-methodology)
-   [Project Structure](#project-structure)
-   [Getting Started](#getting-started)
-   [Security Considerations](#security-considerations)
-   [Limitations](#limitations)
-   [Roadmap](#roadmap)
-   [Contributing](#contributing)
-   [License](#license)

------------------------------------------------------------------------

## Overview

Conventional model evaluation usually measures performance on a fixed
test set. That is useful, but it does not fully reveal how a model
behaves when real-world data changes, features are missing, inputs are
corrupted, or examples are deliberately constructed to mislead it.

Model Autopsy aims to make these weaknesses observable through
controlled, repeatable experiments.

The platform is envisioned as a dashboard where users can provide a
supported model and dataset, select stress tests, run experiments,
inspect failures, explore performance boundaries, and export an
evidence-based report.

### Core question

**Under what conditions does a machine learning model stop meeting a
defined reliability requirement---and what evidence helps explain the
failure?**

## Problem Statement

A model can perform well on a conventional benchmark and still fail
under realistic conditions. A single aggregate score can hide:

-   Severe performance drops for particular classes.
-   Sensitivity to a small set of input features.
-   Fragility when data is incomplete or corrupted.
-   Poor generalization under distribution shift.
-   Incorrect predictions made with high confidence.
-   Differences between models that have similar baseline scores.

Model Autopsy is designed to reveal these failure modes through
structured experimentation.

## Goals

1.  Establish a reproducible baseline for a model and dataset.
2.  Apply controlled input and distribution changes.
3.  Measure performance degradation across stress levels.
4.  Estimate where predefined reliability thresholds are crossed.
5.  Preserve examples and evidence associated with failures.
6.  Investigate possible explanations without confusing correlation with
    causation.
7.  Compare models and experiments under consistent conditions.
8.  Produce reports that another person can reproduce.

## Key Features

### Model and dataset management

-   Upload supported model artifacts and datasets.
-   Validate dataset schema, data types, labels, and missing values.
-   Record model, dataset, and preprocessing metadata.
-   Run baseline evaluation before stress testing.

### Stress-testing laboratory

-   **Distribution shift:** Evaluate on data whose distribution differs
    from the baseline.
-   **Noise injection:** Add controlled noise or corruption.
-   **Missing features:** Remove selected columns or feature groups.
-   **Outlier injection:** Test sensitivity to extreme values.
-   **Class imbalance:** Change class proportions and evaluate per-class
    effects.
-   **Feature perturbation:** Change selected input features within
    defined constraints.
-   **Adversarial testing:** Use supported attack methods to generate
    challenging inputs.
-   **Combined stress tests:** Apply multiple stressors together.
-   **Configurable severity:** Control the range, increments, and
    parameters of an experiment.

### Failure boundary analysis

-   Plot performance against stress intensity.
-   Define a metric and minimum acceptable threshold.
-   Find threshold crossings using an appropriate search method.
-   Report the estimated boundary and search resolution.
-   Compare boundaries across models, datasets, and stress types.

### Failure investigation

-   Inspect individual incorrect predictions.
-   Compare original and modified inputs.
-   View true labels, predicted labels, and model scores where
    available.
-   Analyze class-specific errors and confusion matrices.
-   Use feature attribution or ablation experiments to investigate
    possible dependencies.
-   Flag high-confidence incorrect predictions.
-   Separate measured observations from hypotheses about root causes.

### Experiment management

-   Run experiments asynchronously.
-   Track status, parameters, random seeds, and results.
-   Store experiment history and failure examples.
-   Compare runs and model versions.
-   Reproduce experiments from saved configurations.
-   Export metrics and reports.

### Dashboard and reporting

-   Model health overview.
-   Performance-under-stress charts.
-   Robustness comparisons across test types.
-   Experiment progress and logs.
-   Failure case inspector.
-   Feature analysis and confusion matrix.
-   Autopsy report with findings, evidence, limitations, and
    recommendations.
-   CSV and PDF exports.

> Feature availability depends on implementation. Some
> capabilities---especially adversarial attacks, multimodal inputs,
> drift monitoring, and automated root-cause analysis---require
> additional engineering and validation.

## How It Works

1.  **Upload a model:** Provide a supported model artifact and its
    required preprocessing pipeline.
2.  **Upload a dataset:** Provide evaluation data with labels when the
    selected metrics require them.
3.  **Validate inputs:** Check schema compatibility, data types, missing
    values, and model requirements.
4.  **Run baseline evaluation:** Calculate metrics on unmodified data.
5.  **Configure stress tests:** Select test types, features, intensity
    ranges, and experiment settings.
6.  **Execute experiments:** Generate altered inputs and evaluate the
    model under each condition.
7.  **Analyze failures:** Compare results with the baseline and inspect
    examples.
8.  **Estimate failure boundaries:** Find where a selected metric
    crosses its configured threshold.
9.  **Generate a report:** Save the configuration, results,
    visualizations, and evidence-based observations.

## Failure Boundary

A **failure boundary** is the condition at which a model crosses a
predefined reliability threshold.

For example, suppose a classifier must maintain at least 80% accuracy.
If accuracy falls below 80% as input noise increases, the system
estimates the noise level at which that threshold is crossed.

A boundary should specify:

-   The model and dataset version.
-   The stress type and its parameters.
-   The metric being evaluated.
-   The chosen threshold.
-   The estimated crossing point and search resolution.
-   The evaluation sample size and uncertainty, where available.

A boundary is not necessarily a single value. With multiple interacting
stressors, it may be a region in a multidimensional space.

**Important:** Binary search is appropriate only when the tested
condition and threshold behavior support it (for example, a sufficiently
monotonic response). If performance is irregular or non-monotonic, use
grid-based or adaptive sampling and report that limitation.

## Proposed Architecture

``` text
                  ┌──────────────────────────┐
                  │      Next.js UI          │
                  │ Dashboard / Experiments  │
                  └────────────┬─────────────┘
                               │ REST / WebSocket
                  ┌────────────▼─────────────┐
                  │       FastAPI API        │
                  │ Auth / Validation / Jobs │
                  └──────┬───────────┬──────┘
                         │           │
             ┌───────────▼───┐   ┌───▼────────────┐
             │ PostgreSQL    │   │ Redis + Celery │
             │ Metadata      │   │ Background Jobs│
             └───────────────┘   └───┬────────────┘
                                     │
                           ┌─────────▼──────────┐
                           │ Python ML Workers  │
                           │ Stress / Metrics / │
                           │ Boundary Analysis  │
                           └───────┬────────────┘
                                   │
                           ┌───────▼────────────┐
                           │ Object Storage     │
                           │ Models / Datasets  │
                           │ Artifacts / Reports│
                           └────────────────────┘
```

### Main components

-   **Frontend:** Experiment configuration, dashboards, visualizations,
    and report browsing.
-   **API service:** Input validation, access control, experiment
    creation, and result retrieval.
-   **Experiment engine:** Model adapters, perturbation methods, metric
    calculation, and boundary search.
-   **Background workers:** Execute potentially long-running experiments
    outside request-response cycles.
-   **Relational database:** Store users, metadata, experiment
    configurations, metrics, and status.
-   **Object storage:** Store model files, datasets, generated
    artifacts, and reports.

## Technology Stack

  -----------------------------------------------------------------------
  Layer                               Proposed technologies
  ----------------------------------- -----------------------------------
  Frontend                            Next.js, React, TypeScript

  UI and styling                      Tailwind CSS, shadcn/ui, Lucide

  Charts                              Recharts, Plotly

  API                                 Python, FastAPI, Pydantic

  Data processing                     NumPy, Pandas, SciPy

  ML support                          Scikit-learn, PyTorch

  Robustness testing                  Adversarial Robustness Toolbox
                                      (ART), Alibi Detect

  Explainability                      SHAP, LIME

  Database                            PostgreSQL, SQLAlchemy, Alembic

  Background jobs                     Celery, Redis

  Artifact storage                    MinIO or S3-compatible storage

  Experiment tracking                 MLflow; DVC where dataset/model
                                      versioning is needed

  Testing                             Pytest, HTTPX, Vitest, Playwright

  Deployment                          Docker, GitHub Actions, cloud
                                      hosting
  -----------------------------------------------------------------------

Choose libraries based on the model types and experiments actually
supported. The full stack is a proposed target, not a requirement for
the first version.

## Supported Experiments

The initial prototype should focus on tabular classification and a
small, well-defined set of experiments.

  -----------------------------------------------------------------------
  Experiment              Example method          Key consideration
  ----------------------- ----------------------- -----------------------
  Feature missingness     Remove or mask selected Match realistic
                          columns                 missing-data behavior

  Numeric noise           Add controlled          Respect valid feature
                          perturbations           ranges

  Outlier stress          Inject extreme values   Define plausible and
                                                  implausible ranges

  Distribution shift      Reweight, resample, or  Keep labels and split
                          use a shifted test set  methodology clear

  Class imbalance         Alter class proportions Report per-class
                                                  metrics

  Feature ablation        Remove one feature or   Treat impact as
                          feature group           evidence of dependence,
                                                  not automatic proof of
                                                  causation

  Adversarial test        Apply a supported       State threat model and
                          attack                  constraints
  -----------------------------------------------------------------------

## Metrics

Use metrics appropriate to the task and dataset.

### Classification metrics

-   Accuracy
-   Precision, recall, and F1
-   Confusion matrix
-   ROC-AUC and PR-AUC where applicable
-   Per-class performance

### Robustness and reliability metrics

-   Performance degradation relative to baseline
-   Stress intensity at threshold crossing
-   Area under a performance-versus-stress curve, with a defined
    normalization
-   Failure rate under each test condition
-   Confidence calibration metrics, when meaningful
-   Boundary stability across repeated runs or resampled datasets

Do not rely on accuracy alone for imbalanced tasks. For example, a fraud
classifier can achieve high accuracy while missing many fraudulent
transactions.

## Research Methodology

A research evaluation should:

1.  Define research questions and hypotheses before running experiments.
2.  Select datasets and models with documented provenance.
3.  Establish consistent train, validation, and test splits.
4.  Record preprocessing and model versions.
5.  Define stress transformations and valid parameter ranges.
6.  Use fixed random seeds where possible and repeat stochastic
    experiments.
7.  Compare results against baseline evaluation and relevant existing
    methods.
8.  Report sample sizes, uncertainty, limitations, and negative results.
9.  Avoid tuning on the final test set.
10. Make experiment configurations and code available where licensing
    and privacy permit.

### Example research question

> Do failure-boundary profiles reveal meaningful robustness differences
> between models with similar baseline performance?

A possible study would compare several models across noise,
missing-feature, and distribution-shift experiments, then evaluate
whether boundary estimates are stable and whether they provide
information beyond baseline metrics.

The novelty of any proposed method must be established through a
literature review and empirical comparison. Combining existing libraries
into a dashboard is useful engineering, but is not by itself evidence of
a novel research contribution.

## Project Structure

A possible repository layout:

``` text
model-autopsy/
├── frontend/
│   ├── app/
│   ├── components/
│   ├── features/
│   └── lib/
├── backend/
│   ├── app/
│   │   ├── api/
│   │   ├── core/
│   │   ├── models/
│   │   ├── schemas/
│   │   ├── services/
│   │   └── main.py
│   └── tests/
├── engine/
│   ├── adapters/
│   ├── validation/
│   ├── perturbations/
│   ├── evaluators/
│   ├── metrics/
│   ├── boundaries/
│   ├── explainability/
│   └── reports/
├── workers/
├── docs/
├── docker-compose.yml
├── .env.example
└── README.md
```

This is a suggested structure; adjust it to match the actual repository.

## Getting Started

The commands below are a **starting template**, not guaranteed to work
until the corresponding application files and dependencies have been
created.

### Prerequisites

-   Python 3.11 or a compatible version supported by your chosen
    dependencies.
-   Node.js LTS and npm.
-   Docker and Docker Compose, if using containerized PostgreSQL, Redis,
    or workers.
-   Git.

### 1. Clone the repository

``` bash
git clone <YOUR_REPOSITORY_URL>
cd model-autopsy
```

### 2. Configure environment variables

Create local environment files from the examples provided by the
project:

``` bash
cp .env.example .env
```

Set database, Redis, object-storage, and authentication settings as
applicable. Do not commit secrets.

### 3. Start infrastructure

If a Docker Compose configuration is provided:

``` bash
docker compose up -d
```

### 4. Install dependencies

Install the frontend and backend dependencies using the package
manifests included in the repository. Exact commands depend on the final
project structure.

### 5. Run the application

Start the FastAPI API, background worker, and Next.js frontend using the
scripts defined in their respective project configurations.

> Setup instructions should be updated after the repository, dependency
> files, migrations, and Docker configuration are finalized.

## Security Considerations

Model artifacts and datasets must be treated as untrusted input.

-   Do not load untrusted pickle or joblib files in the main API
    process. These formats can execute arbitrary code during
    deserialization.
-   Run untrusted model execution in isolated containers or sandboxes.
-   Apply CPU, memory, disk, and time limits.
-   Restrict worker network access and filesystem permissions.
-   Validate file types, file sizes, dataset schemas, and archive
    contents.
-   Keep credentials and API keys out of source control.
-   Enforce authentication, authorization, and per-user resource limits.
-   Avoid logging sensitive dataset rows or personal information.
-   Use datasets only when you have appropriate rights and permissions.

## Limitations

-   A stress test covers only the transformations and conditions that
    were tested.
-   Synthetic corruption may not represent real-world distribution
    changes.
-   A measured failure boundary depends on the dataset, metric,
    threshold, and test protocol.
-   Feature importance and explanation methods do not automatically
    establish causality.
-   Confidence scores are not necessarily calibrated probabilities.
-   Some adversarial attacks require gradients, model access, or
    specific assumptions.
-   Results from one dataset or model family may not generalize to
    others.
-   Automated explanations should be treated as hypotheses unless
    independently validated.

## Roadmap

### Phase 1 --- Core prototype

-   [ ] Model and dataset validation
-   [ ] Baseline evaluation
-   [ ] Noise, missing-feature, and distribution-shift tests
-   [ ] Performance-versus-stress plots
-   [ ] Configurable threshold and boundary estimation
-   [ ] Exportable experiment results

### Phase 2 --- Failure analysis

-   [ ] Failure case inspector
-   [ ] Feature ablation and attribution
-   [ ] Confidence and calibration analysis
-   [ ] Experiment history and reproducibility
-   [ ] PDF report generation

### Phase 3 --- Advanced laboratory

-   [ ] Adversarial testing
-   [ ] Adaptive boundary search
-   [ ] Model and version comparisons
-   [ ] Image and text testing
-   [ ] Drift monitoring
-   [ ] Isolated execution for untrusted models
-   [ ] Research benchmark and validation study

## Contributing

Contributions are welcome. For a useful contribution:

1.  Open an issue describing the bug, experiment, or proposed feature.
2.  Include a reproducible example where possible.
3.  Add tests for new transformations, metrics, or boundary methods.
4.  Document assumptions, parameter ranges, and limitations.
5.  Ensure results are deterministic where feasible.

## License

Choose and add a license before publishing the repository. If this
project uses third-party datasets, models, or code, verify and comply
with their individual licenses and usage terms.

------------------------------------------------------------------------

**Model Autopsy --- Don't just measure accuracy. Discover the conditions
under which AI fails.**
