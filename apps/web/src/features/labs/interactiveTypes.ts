export type LabExerciseType = "multiple_choice" | "fill_blank" | "short_text";

export interface MultipleChoiceOption {
  id: string;
  label?: unknown;
}

export interface FillBlankField {
  id: string;
  label?: string;
  placeholder?: string;
}

export interface LabExercise {
  id: string;
  exercise_type: LabExerciseType;
  prompt: string;
  order_index: number;
  max_score: number;
  metadata_json?: {
    options?: MultipleChoiceOption[];
    fields?: FillBlankField[];
    placeholder?: string;
  };
}

export interface LabAttemptSession {
  id: string;
  lab_id: string;
  lab_attempt_status: string;
  attempt_number: number;
  total_score_awarded: number;
  max_score: number;
  required_exercises_correct: number;
  required_exercises_total: number;
}

export interface ExerciseAttemptResult {
  exercise_id: string;
  exercise_type: LabExerciseType;
  is_correct: boolean;
  score_awarded: number;
  max_score: number;
  feedback: string;
}

export interface ExerciseSubmissionPayload {
  exercise_id: string;
  response_payload_json: Record<string, unknown>;
}

export interface SubmitExerciseResponse {
  exercise_attempt_id: string;
  is_correct: boolean;
  score_awarded: number;
  max_score: number;
  feedback: string;
  session: {
    id: string;
    lab_id: string;
    attempt_number: number;
    lab_attempt_status: string;
    total_score_awarded: number;
    max_score: number;
    required_exercises_correct: number;
    required_exercises_total: number;
    hints_used_count: number;
    content_version: number;
    started_at: string;
    completed_at: string | null;
    updated_at: string;
  };
}
