import type { ExerciseAttemptResult, LabExercise } from "@/features/labs/interactiveTypes";

export type ExerciseRoadmapStatus = "current" | "not_answered" | "answered_correct" | "answered_incorrect" | "locked";

export function getFirstUnansweredIndex(exercises: LabExercise[], answersByExerciseId: Record<string, ExerciseAttemptResult>): number {
  const index = exercises.findIndex((exercise) => !answersByExerciseId[exercise.id]);
  return index === -1 ? Math.max(0, exercises.length - 1) : index;
}

export function getExerciseRoadmapStatus(params: {
  exerciseIndex: number;
  currentIndex: number;
  firstUnansweredIndex: number;
  answersByExerciseId: Record<string, ExerciseAttemptResult>;
  exercise: LabExercise;
}): ExerciseRoadmapStatus {
  const { exerciseIndex, currentIndex, firstUnansweredIndex, answersByExerciseId, exercise } = params;
  const attemptResult = answersByExerciseId[exercise.id];

  if (exerciseIndex === currentIndex) {
    return "current";
  }

  if (attemptResult) {
    return attemptResult.is_correct ? "answered_correct" : "answered_incorrect";
  }

  if (exerciseIndex > firstUnansweredIndex) {
    return "locked";
  }

  return "not_answered";
}

export function canOpenExercise(params: {
  exerciseIndex: number;
  firstUnansweredIndex: number;
  answersByExerciseId: Record<string, ExerciseAttemptResult>;
  exercise: LabExercise;
}): boolean {
  const { exerciseIndex, firstUnansweredIndex, answersByExerciseId, exercise } = params;
  if (answersByExerciseId[exercise.id]) {
    return true;
  }

  return exerciseIndex <= firstUnansweredIndex;
}
