import { apiRequest } from "@/lib/apiClient";

import type { Lab } from "@/features/labs/types";
import type { LearningModule, LearningPath, PathProgressSummary } from "@/features/paths/types";

const PATHS_BASE_PATH = "/api/v1/paths";
const MY_PATH_PROGRESS_PATH = "/api/v1/me/path-progress";

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

export async function fetchPathModules(pathId: string): Promise<LearningModule[]> {
  return apiRequest<LearningModule[]>(`${PATHS_BASE_PATH}/${pathId}/modules`, {
    auth: true
  });
}

export async function fetchModuleLabs(moduleId: string): Promise<Lab[]> {
  return apiRequest<Lab[]>(`/api/v1/modules/${moduleId}/labs`, {
    auth: true
  });
}

export async function fetchMyPathProgress(): Promise<PathProgressSummary[]> {
  return apiRequest<PathProgressSummary[]>(MY_PATH_PROGRESS_PATH, {
    auth: true
  });
}
