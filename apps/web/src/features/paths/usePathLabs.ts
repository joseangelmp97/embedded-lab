"use client";

import { useCallback, useEffect, useState } from "react";
import { ApiClientError } from "@/lib/apiClient";
import { fetchPathLabs, fetchPaths } from "@/features/paths/pathsService";

import type { PathLabsGroup } from "@/features/paths/types";

interface UsePathLabsResult {
  pathLabs: PathLabsGroup[];
  isLoading: boolean;
  error: string | null;
  reload: () => Promise<void>;
}

function mapPathLabsError(caughtError: unknown): string {
  if (caughtError instanceof ApiClientError && caughtError.status === 401) {
    return "Your session expired or is not valid. Please login again.";
  }

  if (caughtError instanceof Error) {
    return caughtError.message;
  }

  return "Failed to load learning paths.";
}

export function usePathLabs(enabled: boolean): UsePathLabsResult {
  const [pathLabs, setPathLabs] = useState<PathLabsGroup[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const loadPathLabs = useCallback(async () => {
    if (!enabled) {
      setPathLabs([]);
      setError(null);
      return;
    }

    setIsLoading(true);
    setError(null);

    try {
      const paths = await fetchPaths();
      const groups = await Promise.all(
        paths.map(async (path) => ({
          path,
          labs: await fetchPathLabs(path.id)
        }))
      );

      setPathLabs(
        groups
          .slice()
          .sort((left, right) => left.path.order - right.path.order)
          .map((group) => ({
            ...group,
            labs: group.labs.slice().sort((left, right) => left.order_index - right.order_index)
          }))
      );
    } catch (caughtError) {
      setPathLabs([]);
      setError(mapPathLabsError(caughtError));
    } finally {
      setIsLoading(false);
    }
  }, [enabled]);

  useEffect(() => {
    void loadPathLabs();
  }, [loadPathLabs]);

  return {
    pathLabs,
    isLoading,
    error,
    reload: loadPathLabs
  };
}
