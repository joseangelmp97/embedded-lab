import { apiRequest } from "@/lib/apiClient";
import type { Lab, LabProgress } from "@/features/labs/types";

const LABS_BASE_PATH = "/api/v1/labs";
const MY_LAB_PROGRESS_PATH = "/api/v1/me/lab-progress";

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

export async function fetchMyLabProgress(): Promise<LabProgress[]> {
  return apiRequest<LabProgress[]>(MY_LAB_PROGRESS_PATH, {
    auth: true
  });
}

export async function startLab(labId: string): Promise<LabProgress> {
  return apiRequest<LabProgress>(`${LABS_BASE_PATH}/${labId}/start`, {
    method: "POST",
    auth: true
  });
}

export async function completeLab(labId: string): Promise<LabProgress> {
  return apiRequest<LabProgress>(`${LABS_BASE_PATH}/${labId}/complete`, {
    method: "POST",
    auth: true
  });
}

export async function reopenLab(labId: string): Promise<LabProgress> {
  return apiRequest<LabProgress>(`${LABS_BASE_PATH}/${labId}/reopen`, {
    method: "POST",
    auth: true
  });
}
