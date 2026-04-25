"use client";

import { useCallback, useEffect, useState } from "react";
import { fetchLabs } from "@/features/labs/labsService";

import type { Lab } from "@/features/labs/types";

interface UseLabsResult {
  labs: Lab[];
  isLoading: boolean;
  error: string | null;
  reload: () => Promise<void>;
}

export function useLabs(enabled: boolean): UseLabsResult {
  const [labs, setLabs] = useState<Lab[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const loadLabs = useCallback(async () => {
    if (!enabled) {
      setLabs([]);
      setError(null);
      return;
    }

    setIsLoading(true);
    setError(null);

    try {
      const fetchedLabs = await fetchLabs();
      setLabs(fetchedLabs);
    } catch (caughtError) {
      if (caughtError instanceof Error) {
        setError(caughtError.message);
      } else {
        setError("Failed to load labs.");
      }
    } finally {
      setIsLoading(false);
    }
  }, [enabled]);

  useEffect(() => {
    void loadLabs();
  }, [loadLabs]);

  return {
    labs,
    isLoading,
    error,
    reload: loadLabs
  };
}
