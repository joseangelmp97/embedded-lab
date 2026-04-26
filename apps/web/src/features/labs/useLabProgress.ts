"use client";

import { useCallback, useEffect, useState } from "react";
import { ApiClientError } from "@/lib/apiClient";
import { completeLab, fetchMyLabProgress, startLab } from "@/features/labs/labsService";

import type { LabProgress, LabProgressStatus } from "@/features/labs/types";

type LabProgressMap = Record<string, LabProgress>;
type LabProgressAction = "start" | "complete";

interface UseLabProgressResult {
  progressByLabId: LabProgressMap;
  isLoading: boolean;
  loadingError: string | null;
  actionError: string | null;
  pendingActions: Record<string, LabProgressAction | undefined>;
  getLabStatus: (labId: string) => LabProgressStatus;
  reload: () => Promise<void>;
  startLabProgress: (labId: string) => Promise<void>;
  completeLabProgress: (labId: string) => Promise<void>;
}

function toProgressMap(progressItems: LabProgress[]): LabProgressMap {
  return progressItems.reduce<LabProgressMap>((accumulator, item) => {
    accumulator[item.lab_id] = item;
    return accumulator;
  }, {});
}

function mapProgressActionError(error: unknown): string {
  if (error instanceof ApiClientError) {
    if (error.status === 401) {
      return "Your session expired or is not valid. Please login again.";
    }

    if (error.status === 404) {
      return "Lab not found.";
    }

    return error.message;
  }

  if (error instanceof Error) {
    return error.message;
  }

  return "Failed to update lab progress.";
}

export function useLabProgress(enabled: boolean): UseLabProgressResult {
  const [progressByLabId, setProgressByLabId] = useState<LabProgressMap>({});
  const [isLoading, setIsLoading] = useState(false);
  const [loadingError, setLoadingError] = useState<string | null>(null);
  const [actionError, setActionError] = useState<string | null>(null);
  const [pendingActions, setPendingActions] = useState<Record<string, LabProgressAction | undefined>>({});

  const loadProgress = useCallback(async () => {
    if (!enabled) {
      setProgressByLabId({});
      setLoadingError(null);
      setActionError(null);
      setPendingActions({});
      return;
    }

    setIsLoading(true);
    setLoadingError(null);

    try {
      const progressRows = await fetchMyLabProgress();
      setProgressByLabId(toProgressMap(progressRows));
    } catch (caughtError) {
      setProgressByLabId({});
      setLoadingError(mapProgressActionError(caughtError));
    } finally {
      setIsLoading(false);
    }
  }, [enabled]);

  useEffect(() => {
    void loadProgress();
  }, [loadProgress]);

  const executeAction = useCallback(
    async (labId: string, action: LabProgressAction) => {
      if (!enabled || !labId.trim() || pendingActions[labId]) {
        return;
      }

      setActionError(null);
      setPendingActions((previous) => ({
        ...previous,
        [labId]: action
      }));

      try {
        const updatedProgress = action === "start" ? await startLab(labId) : await completeLab(labId);

        setProgressByLabId((previous) => ({
          ...previous,
          [labId]: updatedProgress
        }));
      } catch (caughtError) {
        setActionError(mapProgressActionError(caughtError));
      } finally {
        setPendingActions((previous) => ({
          ...previous,
          [labId]: undefined
        }));
      }
    },
    [enabled, pendingActions]
  );

  const getLabStatus = useCallback(
    (labId: string): LabProgressStatus => {
      if (!labId.trim()) {
        return "not_started";
      }

      return progressByLabId[labId]?.status ?? "not_started";
    },
    [progressByLabId]
  );

  const startLabProgress = useCallback(
    async (labId: string) => {
      await executeAction(labId, "start");
    },
    [executeAction]
  );

  const completeLabProgress = useCallback(
    async (labId: string) => {
      await executeAction(labId, "complete");
    },
    [executeAction]
  );

  return {
    progressByLabId,
    isLoading,
    loadingError,
    actionError,
    pendingActions,
    getLabStatus,
    reload: loadProgress,
    startLabProgress,
    completeLabProgress
  };
}
