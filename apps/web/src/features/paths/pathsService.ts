import { apiRequest } from "@/lib/apiClient";

import type { Lab } from "@/features/labs/types";
import type { LearningPath } from "@/features/paths/types";

const PATHS_BASE_PATH = "/api/v1/paths";

export async function fetchPaths(): Promise<LearningPath[]> {
  return apiRequest<LearningPath[]>(PATHS_BASE_PATH, {
    auth: true
  });
}

export async function fetchPathLabs(pathId: string): Promise<Lab[]> {
  return apiRequest<Lab[]>(`${PATHS_BASE_PATH}/${pathId}/labs`, {
    auth: true
  });
}
