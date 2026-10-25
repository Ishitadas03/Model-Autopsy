import { Experiment, FailedSample, Dataset, ModelAdapter, E003ComparisonData } from './schemas';
import { MOCK_EXPERIMENTS, MOCK_FAILED_SAMPLES, HERO_EXPERIMENT, E003_EXPERIMENT } from './mocks/experiments';
import { MOCK_DATASETS } from './mocks/datasets';
import { MOCK_MODELS } from './mocks/models';
import { E003_FIXTURE_DATA } from './mocks/e003Data';

const USE_MOCKS =
  typeof window !== 'undefined'
    ? process.env.NEXT_PUBLIC_USE_MOCKS !== 'false'
    : true;

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
    return res.json();
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
    return res.json();
  },

  async getModels(): Promise<ModelAdapter[]> {
    if (USE_MOCKS) {
      return [...MOCK_MODELS];
    }
    const res = await fetch('/api/models');
    return res.json();
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
};

