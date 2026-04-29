"use client";

import { useCallback, useEffect, useState } from "react";
import { ApiClientError } from "@/lib/apiClient";
import { fetchModuleLabs, fetchPathModules, fetchPaths } from "@/features/paths/pathsService";

import type { PathModulesLabsGroup } from "@/features/paths/types";

interface UsePathLabsResult {
  pathLabs: PathModulesLabsGroup[];
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
  const [pathLabs, setPathLabs] = useState<PathModulesLabsGroup[]>([]);
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
        paths.map(async (path) => {
          const pathModules = await fetchPathModules(path.id);
          const modules = await Promise.all(
            pathModules.map(async (module) => ({
              module,
              labs: await fetchModuleLabs(module.id)
            }))
          );

          return {
            path,
            modules
          };
        })
      );

      setPathLabs(
        groups
          .slice()
          .sort((left, right) => left.path.order - right.path.order)
          .map((group) => ({
            ...group,
            modules: group.modules
              .slice()
              .sort((left, right) => left.module.order_index - right.module.order_index)
              .map((moduleGroup) => ({
                ...moduleGroup,
                labs: moduleGroup.labs.slice().sort((left, right) => left.order_index - right.order_index)
              }))
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
