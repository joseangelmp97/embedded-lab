export type LabDifficulty = "beginner" | "intermediate" | "advanced";
export type LabProgressStatus = "not_started" | "in_progress" | "completed";

export interface Lab {
  id: string;
  title: string;
  description: string;
  prerequisite_lab_id?: string | null;
  difficulty: LabDifficulty;
  estimated_minutes: number;
  status: string;
  order_index: number;
  created_at: string;
  updated_at: string;
}

export interface LabProgress {
  id: string;
  user_id: string;
  lab_id: string;
  status: LabProgressStatus;
  started_at: string | null;
  completed_at: string | null;
  created_at: string;
  updated_at: string;
}
