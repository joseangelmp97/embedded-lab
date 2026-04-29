import type { Lab, LabProgressStatus } from "@/features/labs/types";

export const LOCKED_LAB_MESSAGE = "Complete previous lab to unlock";

export function getEffectiveLabProgressStatus(status: LabProgressStatus, locked: boolean): LabProgressStatus {
  if (locked) {
    return "not_started";
  }

  return status;
}

export function isLabLocked(lab: Lab, getLabStatus: (labId: string) => LabProgressStatus): boolean {
  const prerequisiteLabId = lab.prerequisite_lab_id?.trim();

  if (!prerequisiteLabId) {
    return false;
  }

  return getLabStatus(prerequisiteLabId) !== "completed";
}
