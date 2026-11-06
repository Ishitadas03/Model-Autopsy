import { Experiment, FailedSample, Dataset, ModelAdapter, E003ComparisonData } from './schemas';
import { MOCK_EXPERIMENTS, MOCK_FAILED_SAMPLES, HERO_EXPERIMENT, E003_EXPERIMENT } from './mocks/experiments';
import { MOCK_DATASETS } from './mocks/datasets';
import { MOCK_MODELS } from './mocks/models';
import { E003_FIXTURE_DATA } from './mocks/e003Data';

const USE_MOCKS =
  typeof window !== 'undefined'
    ? process.env.NEXT_PUBLIC_USE_MOCKS === 'true'
    : false;

let runtimeExperiments: Experiment[] = [...MOCK_EXPERIMENTS];

export interface HealthResponse {
  status: 'ok' | 'degraded' | 'error';
  mode: 'mock' | 'live';
  version: string;
}

export interface E003FetchResult {
  data: E003ComparisonData | null;
  isLive: boolean;
  error: string | null;
}

export const api = {
  async getHealth(): Promise<HealthResponse> {
    if (USE_MOCKS) {
      return { status: 'ok', mode: 'mock', version: '0.1.0' };
    }
    const res = await fetch('/api/health');
    return res.json();
  },

  async getExperiments(): Promise<Experiment[]> {
    if (USE_MOCKS) {
      await new Promise((r) => setTimeout(r, 150));
      return [...runtimeExperiments];
    }
    const res = await fetch('/api/experiments');
    if (!res.ok) {
      const err = await res.json().catch(() => ({ detail: `HTTP ${res.status}` }));
      throw new Error(err.detail || `Failed to fetch experiments (HTTP ${res.status})`);
    }
    const data = await res.json();
    return Array.isArray(data) ? data : [];
  },

  async getExperiment(id: string): Promise<Experiment | null> {
    if (id.toUpperCase() === 'E003') {
      return { ...E003_EXPERIMENT };
    }
    if (USE_MOCKS) {
      await new Promise((r) => setTimeout(r, 100));
      const exp = runtimeExperiments.find((e) => e.id.toLowerCase() === id.toLowerCase());
      return exp ? { ...exp } : null;
    }
    const res = await fetch(`/api/experiments/${id}`);
    if (!res.ok) return null;
    return res.json();
  },

  async getE003Data(forceMock = false): Promise<E003FetchResult> {
    if (forceMock) {
      return { data: E003_FIXTURE_DATA, isLive: false, error: null };
    }
    try {
      const res = await fetch('/api/experiments/e003');
      if (!res.ok) {
        const errJson = await res.json().catch(() => ({}));
        // If in explicit mock environment without backend, provide fixture:
        if (USE_MOCKS && res.status === 404) {
          return { data: E003_FIXTURE_DATA, isLive: false, error: null };
        }
        return {
          data: null,
          isLive: false,
          error: errJson.error || `Failed to load E003 canonical artifact (HTTP ${res.status})`,
        };
      }
      const json = await res.json();
      return { data: json, isLive: true, error: null };
    } catch (e: any) {
      if (USE_MOCKS) {
        return { data: E003_FIXTURE_DATA, isLive: false, error: null };
      }
      return {
        data: null,
        isLive: false,
        error: e?.message || 'Network error fetching E003 experiment data.',
      };
    }
  },

  async getE003RawArtifact(format: 'json' | 'csv' | 'markdown' = 'json'): Promise<string> {
    const res = await fetch(`/api/experiments/e003?format=${format}`);
    if (!res.ok) {
      throw new Error(`Failed to fetch artifact format ${format} (HTTP ${res.status})`);
    }
    return res.text();
  },

  async createExperiment(newExp: Omit<Experiment, 'id' | 'createdAt' | 'status' | 'progressPercent'>): Promise<Experiment> {
    if (USE_MOCKS) {
      await new Promise((r) => setTimeout(r, 200));
      const id = `EXP-0${Math.floor(250 + Math.random() * 700)}`;
      const exp: Experiment = {
        ...newExp,
        id,
        status: 'queued',
        createdAt: new Date().toISOString(),
        progressPercent: 0,
      };
      runtimeExperiments = [exp, ...runtimeExperiments];
      return exp;
    }
    const res = await fetch('/api/experiments', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(newExp),
    });
    return res.json();
  },

  async cancelExperiment(id: string): Promise<{ success: boolean }> {
    if (USE_MOCKS) {
      await new Promise((r) => setTimeout(r, 150));
      runtimeExperiments = runtimeExperiments.map((e) =>
        e.id === id ? { ...e, status: 'cancelled' as const } : e
      );
      return { success: true };
    }
    const res = await fetch(`/api/experiments/${id}/cancel`, { method: 'POST' });
    return res.json();
  },

  async getDatasets(): Promise<Dataset[]> {
    if (USE_MOCKS) {
      return [...MOCK_DATASETS];
    }
    const res = await fetch('/api/datasets');
    if (!res.ok) {
      return [...MOCK_DATASETS];
    }
    const data = await res.json();
    return Array.isArray(data) && data.length > 0 ? data : [...MOCK_DATASETS];
  },

  async uploadDataset(
    file: File,
    options?: {
      datasetId?: string;
      name?: string;
      description?: string;
      taskType?: string;
      targetName?: string;
    }
  ): Promise<Dataset> {
    if (USE_MOCKS) {
      await new Promise((r) => setTimeout(r, 400));
      const mockId = options?.datasetId || `custom-${Date.now()}`;
      return {
        id: mockId,
        name: options?.name || file.name.replace(/\.csv$/i, ''),
        description: options?.description || 'User-uploaded CSV dataset',
        taskType: (options?.taskType as any) || 'classification',
        sampleCount: 150,
        featureCount: 4,
        classCount: 2,
        isCustom: true,
        features: [
          { name: 'feature_1', type: 'numeric', missingCount: 0 },
          { name: 'feature_2', type: 'numeric', missingCount: 0 },
        ],
      };
    }

    const formData = new FormData();
    formData.append('file', file);
    if (options?.datasetId) formData.append('dataset_id', options.datasetId);
    if (options?.name) formData.append('name', options.name);
    if (options?.description) formData.append('description', options.description);
    if (options?.taskType) formData.append('task_type', options.taskType);
    if (options?.targetName) formData.append('target_name', options.targetName);

    const res = await fetch('/api/datasets/upload', {
      method: 'POST',
      body: formData,
    });

    if (!res.ok) {
      const errJson = await res.json().catch(() => ({}));
      throw new Error(errJson.detail || `Dataset upload failed (HTTP ${res.status})`);
    }

    return res.json();
  },

  getDatasetDownloadUrl(datasetId: string): string {
    return `/api/datasets/${datasetId}/download`;
  },

  getArtifactDownloadUrl(experimentId: string, artifactType: string): string {
    return `/api/experiments/${experimentId}/artifacts/${artifactType}`;
  },

  async getModels(): Promise<ModelAdapter[]> {
    if (USE_MOCKS) {
      return [...MOCK_MODELS];
    }
    const res = await fetch('/api/models');
    if (!res.ok) {
      return [...MOCK_MODELS];
    }
    const data = await res.json();
    return Array.isArray(data) && data.length > 0 ? data : [...MOCK_MODELS];
  },

  async getFailedSamples(
    _experimentId: string,
    page = 1,
    pageSize = 20,
    filterClass?: string
  ): Promise<{ samples: FailedSample[]; total: number }> {
    if (USE_MOCKS) {
      await new Promise((r) => setTimeout(r, 150));
      let filtered = [...MOCK_FAILED_SAMPLES];
      if (filterClass && filterClass !== 'All') {
        filtered = filtered.filter(
          (s) => s.trueLabel === filterClass || s.predictedLabel === filterClass
        );
      }
      const start = (page - 1) * pageSize;
      const end = start + pageSize;
      return {
        samples: filtered.slice(start, end),
        total: filtered.length,
      };
    }
    const res = await fetch(`/api/experiments/${_experimentId}/failures?page=${page}&limit=${pageSize}`);
    return res.json();
  },

  async evaluateBaseline(config: {
    datasetId: string;
    modelId?: string;
    taskType?: string;
    testSize?: number;
    seed?: number;
    targetName?: string;
    modelParams?: Record<string, any>;
  }): Promise<{
    datasetId: string;
    modelId: string;
    taskType: string;
    sampleCount: number;
    trainCount: number;
    testCount: number;
    targetName: string;
    featureNames: string[];
    metrics: Record<string, any>;
  }> {
    if (USE_MOCKS) {
      await new Promise((r) => setTimeout(r, 400));
      return {
        datasetId: config.datasetId,
        modelId: config.modelId || 'random-forest-classifier',
        taskType: config.taskType || 'classification',
        sampleCount: 150,
        trainCount: 120,
        testCount: 30,
        targetName: config.targetName || 'target',
        featureNames: ['feature_1', 'feature_2', 'feature_3', 'feature_4'],
        metrics:
          config.taskType === 'regression'
            ? { mae: 0.182, mse: 0.054, rmse: 0.232, r2: 0.884 }
            : { accuracy: 0.9667, precision: 0.9667, recall: 0.9667, f1: 0.9667 },
      };
    }

    const res = await fetch('/api/experiments/baseline', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        datasetId: config.datasetId,
        modelId: config.modelId || 'random-forest-classifier',
        taskType: config.taskType || 'classification',
        testSize: config.testSize ?? 0.2,
        seed: config.seed ?? 42,
        targetName: config.targetName,
        modelParams: config.modelParams || {},
      }),
    });

    if (!res.ok) {
      const err = await res.json().catch(() => ({ detail: `HTTP ${res.status}` }));
      throw new Error(err.detail || `Baseline evaluation failed (HTTP ${res.status})`);
    }

    return res.json();
  },
};

