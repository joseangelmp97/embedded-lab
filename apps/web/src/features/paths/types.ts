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
