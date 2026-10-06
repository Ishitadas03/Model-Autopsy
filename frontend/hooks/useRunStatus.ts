'use client';

import { useState, useEffect, useRef } from 'react';
import { Experiment } from '@/lib/schemas';
import { api } from '@/lib/api';

export interface UseRunStatusResult {
  experiment: Experiment | null;
  loading: boolean;
  error: string | null;
  progressPercent: number;
  currentStage: string;
  elapsedSeconds: number;
  completedStages: string[];
  cancelRun: () => Promise<boolean>;
  retryRun: () => void;
}

export const STAGES = [
  'Baseline Evaluation',
  'Gaussian Noise (5%)',
  'Gaussian Noise (10%)',
  'Gaussian Noise (20%)',
  'Gaussian Noise (30%)',
  'Analyzing Failures',
];

export function useRunStatus(experimentId: string): UseRunStatusResult {
  const [experiment, setExperiment] = useState<Experiment | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const [progressPercent, setProgressPercent] = useState(0);
  const [currentStage, setCurrentStage] = useState(STAGES[0]);
  const [completedStages, setCompletedStages] = useState<string[]>([]);
  const [elapsedSeconds, setElapsedSeconds] = useState(0);

  const intervalRef = useRef<NodeJS.Timeout | null>(null);
  const timerRef = useRef<NodeJS.Timeout | null>(null);

  const fetchStatus = async () => {
    try {
      const data = await api.getExperiment(experimentId);
      if (!data) {
        setError(`Experiment ${experimentId} not found`);
        return;
      }
      setExperiment(data);

      if (data.status === 'completed') {
        setProgressPercent(100);
        setCurrentStage('Complete');
        setCompletedStages(STAGES);
      } else if (data.status === 'failed' || data.status === 'cancelled') {
        // Stop progression
      }
    } catch (err: any) {
      setError(err?.message || 'Failed to poll experiment status');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchStatus();

    // Elapsed timer
    timerRef.current = setInterval(() => {
      setElapsedSeconds((prev) => prev + 1);
    }, 1000);

    // Progress simulation loop if running/queued
    intervalRef.current = setInterval(() => {
      setProgressPercent((prev) => {
        if (prev >= 100) {
          if (intervalRef.current) clearInterval(intervalRef.current);
          return 100;
        }

        const next = Math.min(100, prev + Math.floor(Math.random() * 5) + 3);
        const stageIndex = Math.min(
          STAGES.length - 1,
          Math.floor((next / 100) * STAGES.length)
        );

        setCurrentStage(STAGES[stageIndex]);
        setCompletedStages(STAGES.slice(0, stageIndex));

        return next;
      });
    }, 800);

    return () => {
      if (intervalRef.current) clearInterval(intervalRef.current);
      if (timerRef.current) clearInterval(timerRef.current);
    };
  }, [experimentId]);

  const cancelRun = async (): Promise<boolean> => {
    if (intervalRef.current) clearInterval(intervalRef.current);
    if (timerRef.current) clearInterval(timerRef.current);

    const res = await api.cancelExperiment(experimentId);
    if (res.success) {
      setExperiment((prev) => (prev ? { ...prev, status: 'cancelled' } : null));
    }
    return res.success;
  };

  const retryRun = () => {
    setProgressPercent(0);
    setElapsedSeconds(0);
    setCompletedStages([]);
    setCurrentStage(STAGES[0]);
    fetchStatus();
  };

  return {
    experiment,
    loading,
    error,
    progressPercent,
    currentStage,
    elapsedSeconds,
    completedStages,
    cancelRun,
    retryRun,
  };
}
