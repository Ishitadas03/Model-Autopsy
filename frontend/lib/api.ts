import { Experiment, FailedSample, Dataset, ModelAdapter } from './schemas';
import { MOCK_EXPERIMENTS, MOCK_FAILED_SAMPLES, HERO_EXPERIMENT } from './mocks/experiments';
import { MOCK_DATASETS } from './mocks/datasets';
import { MOCK_MODELS } from './mocks/models';

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
    if (USE_MOCKS) {
      await new Promise((r) => setTimeout(r, 100));
      const exp = runtimeExperiments.find((e) => e.id === id);
      return exp ? { ...exp } : null;
    }
    const res = await fetch(`/api/experiments/${id}`);
    if (!res.ok) return null;
    return res.json();
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
