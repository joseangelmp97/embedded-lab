import type { Lab } from "@/features/labs/types";

export interface LearningPath {
  id: string;
  name: string;
  description: string;
  order: number;
}

export interface PathLabsGroup {
  path: LearningPath;
  labs: Lab[];
}

export interface PathProgressSummary {
  path_id: string;
  path_name: string;
  path_description: string;
  total_labs: number;
  completed_labs: number;
  in_progress_labs: number;
  locked_labs: number;
  completion_percentage: number;
}
