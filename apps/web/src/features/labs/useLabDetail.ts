"use client";

import { useCallback, useEffect, useState } from "react";
import { fetchLabById } from "@/features/labs/labsService";
import { ApiClientError } from "@/lib/apiClient";

import type { Lab } from "@/features/labs/types";

interface UseLabDetailResult {
  lab: Lab | null;
  isLoading: boolean;
  error: string | null;
  reload: () => Promise<void>;
}

function mapLabDetailError(caughtError: unknown): string {
  if (caughtError instanceof ApiClientError) {
    if (caughtError.status === 401) {
      return "Your session expired or is not valid. Please login again.";
    }

    if (caughtError.status === 404) {
      return "The requested lab was not found.";
    }

    return caughtError.message;
  }

  if (caughtError instanceof Error) {
    return caughtError.message;
  }

  return "Failed to load lab details.";
}

export function useLabDetail(labId: string, enabled: boolean): UseLabDetailResult {
  const [lab, setLab] = useState<Lab | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const loadLab = useCallback(async () => {
    if (!enabled || !labId.trim()) {
      setLab(null);
      setError(null);
      return;
    }

    setIsLoading(true);
    setError(null);

    try {
      const fetchedLab = await fetchLabById(labId);
      setLab(fetchedLab);
    } catch (caughtError) {
      setLab(null);
      setError(mapLabDetailError(caughtError));
    } finally {
      setIsLoading(false);
    }
  }, [enabled, labId]);

  useEffect(() => {
    void loadLab();
  }, [loadLab]);

  return {
    lab,
    isLoading,
    error,
    reload: loadLab
  };
}
