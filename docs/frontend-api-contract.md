# Frontend ↔ Backend API Contract

> **Service**: `Model Autopsy REST API`  
> **Backend Base Path**: `/api`  
> **Client Consumer**: [`frontend/lib/api.ts`](file:///c:/MODEL_AUTOSPY/Model-Autopsy/frontend/lib/api.ts)  
> **Schemas Reference**: [`frontend/lib/schemas.ts`](file:///c:/MODEL_AUTOSPY/Model-Autopsy/frontend/lib/schemas.ts)

This document specifies the exact REST API contract required by the Model Autopsy frontend when `NEXT_PUBLIC_USE_MOCKS=false`.

---

## 1. System Health

### `GET /api/health`
Checks backend service availability and mode.

#### Response `200 OK`
```json
{
  "status": "ok",
  "mode": "live",
  "version": "0.1.0"
}
```

---

## 2. Experiments

### `GET /api/experiments`
Lists all submitted and completed autopsy experiments.

#### Response `200 OK`
```json
[
  {
    "id": "EXP-0241",
    "modelName": "RandomForest-v2 (Credit)",
    "datasetName": "German Credit Benchmark",
    "datasetId": "german-credit",
    "taskType": "classification",
    "perturbationFamily": "gaussian_noise",
    "noiseType": "Gaussian Noise",
    "evaluationMetric": "f1",
    "failureThreshold": 0.80,
    "seed": 42,
    "status": "completed",
    "progressPercent": 100,
    "createdAt": "2026-10-05T12:00:00.000Z",
    "results": {
      "baselineScore": 0.958,
      "worstCaseScore": 0.712,
      "observedBoundary": 0.231,
      "failedSamplesCount": 143,
      "curveData": [
        { "noiseLevel": 0.0, "score": 0.958 },
        { "noiseLevel": 0.05, "score": 0.932 },
        { "noiseLevel": 0.10, "score": 0.885 },
        { "noiseLevel": 0.15, "score": 0.841 },
        { "noiseLevel": 0.20, "score": 0.824 },
        { "noiseLevel": 0.25, "score": 0.768 },
        { "noiseLevel": 0.30, "score": 0.712 }
      ],
      "featureVulnerabilities": [
        { "feature": "Credit Score", "drop": 0.284, "rank": 1, "caveat": "Empirical sensitivity — not a causal explanation." },
        { "feature": "Income", "drop": 0.192, "rank": 2, "caveat": "Empirical sensitivity — not a causal explanation." },
        { "feature": "Age", "drop": 0.115, "rank": 3, "caveat": "Empirical sensitivity — not a causal explanation." },
        { "feature": "Loan Amount", "drop": 0.083, "rank": 4, "caveat": "Empirical sensitivity — not a causal explanation." }
      ]
    }
  }
]
```

---

### `GET /api/experiments/{id}`
Fetches status, telemetry, and results for a single experiment.

#### Response `200 OK`
Returns the `Experiment` object as detailed above.

#### Response `404 Not Found`
```json
{
  "detail": "Experiment EXP-9999 not found"
}
```

---

### `POST /api/experiments`
Submits a new stress-testing autopsy job.

#### Request Body
```json
{
  "modelName": "RandomForest-v2 (Credit)",
  "datasetName": "German Credit Benchmark",
  "datasetId": "german-credit",
  "taskType": "classification",
  "perturbationFamily": "gaussian_noise",
  "noiseType": "Gaussian Noise",
  "evaluationMetric": "f1",
  "failureThreshold": 0.80,
  "seed": 42
}
```

#### Response `201 Created`
Returns the initialized `Experiment` with:
- `id`: Unique identifier (e.g. `"EXP-0242"`)
- `status`: `"queued"`
- `progressPercent`: `0`
- `createdAt`: ISO 8601 timestamp

---

### `POST /api/experiments/{id}/cancel`
Requests cancellation of an actively running or queued experiment.

#### Response `200 OK`
```json
{
  "success": true
}
```

---

## 3. Failure Samples & Decision Geometry

### `GET /api/experiments/{id}/failures`
Retrieves paginated failed sample instances with feature values under clean vs. stressed states.

#### Query Parameters
- `page` (integer, default: 1): 1-indexed page number
- `limit` (integer, default: 20): Page size
- `filterClass` (string, optional): Filter by ground truth or predicted class

#### Response `200 OK`
```json
{
  "total": 143,
  "samples": [
    {
      "id": "samp-101",
      "sampleIndex": 42,
      "trueLabel": "Legitimate",
      "predictedLabel": "Fraud",
      "confidence": 0.874,
      "noiseLevel": 0.20,
      "features": {
        "Income": { "clean": 65000, "stressed": 58200 },
        "Credit Score": { "clean": 720, "stressed": 580 },
        "Age": { "clean": 34, "stressed": 34 },
        "Loan Amount": { "clean": 12000, "stressed": 12000 }
      }
    }
  ]
}
```

---

## 4. Catalogs & Registries

### `GET /api/datasets`
Lists available benchmark datasets registered in the system.

#### Response `200 OK`
```json
[
  {
    "id": "german-credit",
    "name": "German Credit Benchmark",
    "description": "Statlog German Credit dataset evaluating creditworthiness risks across demographic and financial indicators.",
    "taskType": "classification",
    "sampleCount": 1000,
    "featureCount": 4,
    "license": "CC-BY-4.0",
    "tags": ["tabular", "finance", "credit-risk"]
  }
]
```

---

### `GET /api/models`
Lists supported pre-configured model adapters. **Note: No arbitrary weight uploading is allowed; all models are defined by catalog adapter configs.**

#### Response `200 OK`
```json
[
  {
    "id": "rf-german-credit",
    "name": "RandomForest-v2 (Credit)",
    "description": "Standard ensemble classifier trained on German Credit tabular features.",
    "taskType": "classification",
    "supportedDatasets": ["german-credit"],
    "framework": "scikit-learn",
    "baselineF1": 0.958
  }
]
```

---

## 5. Mandatory Honesty & Scientific Invariants

Any backend implementation **must conform** to the following contract rules:
1. **Empirical Boundary**: The boundary metric must always be accompanied by the metadata field:  
   `"Observed failure boundary under the specified experimental configuration."`
2. **Feature Sensitivities**: Each feature sensitivity score must contain the caveat field:  
   `"Empirical sensitivity — not a causal explanation."`
3. **No Overall Grade**: The backend API must **not** output an aggregate "robustness score", "letter grade", or subjective rating.
4. **Metric Polarity**: For `f1`, `accuracy`, and `roc_auc`, higher is better. For `mae`, `mse`, and `loss`, lower is better.
