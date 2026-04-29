import type { Lab } from "@/features/labs/types";

export interface LearningPath {
  id: string;
  name: string;
  description: string;
  order: number;
}

export interface LearningModule {
  id: string;
  path_id: string;
  slug: string;
  title: string;
  description: string;
  order_index: number;
  is_published: boolean;
  created_at: string;
  updated_at: string;
}

export interface ModuleLabsGroup {
  module: LearningModule;
  labs: Lab[];
}

export interface PathModulesLabsGroup {
  path: LearningPath;
  modules: ModuleLabsGroup[];
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
