export type LabDifficulty = "beginner" | "intermediate" | "advanced";

export interface Lab {
  id: string;
  title: string;
  description: string;
  difficulty: LabDifficulty;
  estimated_minutes: number;
  status: string;
  order_index: number;
  created_at: string;
  updated_at: string;
}
