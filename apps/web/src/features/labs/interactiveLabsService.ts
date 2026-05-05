import { apiRequest } from "@/lib/apiClient";
import type {
  ExerciseSubmissionPayload,
  LabAttemptSession,
  LabExercise,
  SubmitExerciseResponse
} from "@/features/labs/interactiveTypes";

interface ApiEnvelope<T> {
  success?: boolean;
  data?: T;
}

function unwrap<T>(payload: ApiEnvelope<T> | T): T {
  if (payload && typeof payload === "object" && "data" in (payload as Record<string, unknown>)) {
    const data = (payload as ApiEnvelope<T>).data;
    if (typeof data !== "undefined") {
      return data;
    }
  }

  return payload as T;
}

export async function fetchLabExercises(labId: string): Promise<LabExercise[]> {
  const response = await apiRequest<ApiEnvelope<LabExercise[]> | LabExercise[]>(`/api/v1/labs/${labId}/exercises`, {
    auth: true
  });

  return unwrap(response);
}

export async function createOrResumeLabAttempt(labId: string): Promise<LabAttemptSession> {
  const response = await apiRequest<ApiEnvelope<LabAttemptSession> | LabAttemptSession>(`/api/v1/labs/${labId}/attempts`, {
    method: "POST",
    auth: true
  });

  return unwrap(response);
}

export async function submitExerciseAnswer(
  labId: string,
  attemptId: string,
  submission: ExerciseSubmissionPayload
): Promise<SubmitExerciseResponse> {
  const response = await apiRequest<ApiEnvelope<SubmitExerciseResponse> | SubmitExerciseResponse>(
    `/api/v1/labs/${labId}/attempts/${attemptId}/submit`,
    {
      method: "POST",
      auth: true,
      body: submission
    }
  );

  return unwrap(response);
}
