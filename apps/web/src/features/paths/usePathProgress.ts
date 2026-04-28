"use client";

import { useCallback, useEffect, useState } from "react";
import { ApiClientError } from "@/lib/apiClient";
import { fetchMyPathProgress } from "@/features/paths/pathsService";

import type { PathProgressSummary } from "@/features/paths/types";

interface UsePathProgressResult {
  pathProgress: PathProgressSummary[];
  isLoading: boolean;
  error: string | null;
  reload: () => Promise<void>;
}

function mapPathProgressError(caughtError: unknown): string {
  if (caughtError instanceof ApiClientError && caughtError.status === 401) {
    return "Your session expired or is not valid. Please login again.";
  }

  if (caughtError instanceof Error) {
    return caughtError.message;
  }

  return "Failed to load path progress.";
}

export function usePathProgress(enabled: boolean): UsePathProgressResult {
  const [pathProgress, setPathProgress] = useState<PathProgressSummary[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const loadPathProgress = useCallback(async () => {
    if (!enabled) {
      setPathProgress([]);
      setError(null);
      return;
    }

    setIsLoading(true);
    setError(null);

    try {
      const summaries = await fetchMyPathProgress();
      setPathProgress(summaries);
    } catch (caughtError) {
      setPathProgress([]);
      setError(mapPathProgressError(caughtError));
    } finally {
      setIsLoading(false);
    }
  }, [enabled]);

  useEffect(() => {
    void loadPathProgress();
  }, [loadPathProgress]);

  return {
    pathProgress,
    isLoading,
    error,
    reload: loadPathProgress
  };
}
