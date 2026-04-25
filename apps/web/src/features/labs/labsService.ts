import { apiRequest } from "@/lib/apiClient";
import type { Lab } from "@/features/labs/types";

const LABS_BASE_PATH = "/api/v1/labs";

export async function fetchLabs(): Promise<Lab[]> {
  return apiRequest<Lab[]>(LABS_BASE_PATH, {
    auth: true
  });
}

export async function fetchLabById(labId: string): Promise<Lab> {
  return apiRequest<Lab>(`${LABS_BASE_PATH}/${labId}`, {
    auth: true
  });
}
