"use client";

import { useState } from "react";
import type { LabExercise } from "@/features/labs/interactiveTypes";

interface MultipleChoiceExerciseProps {
  exercise: LabExercise;
  disabled?: boolean;
  onSubmit: (responsePayload: Record<string, unknown>) => Promise<void>;
}

export function MultipleChoiceExercise({ exercise, disabled = false, onSubmit }: MultipleChoiceExerciseProps) {
  const [selectedOptionId, setSelectedOptionId] = useState<string>("");

  const options = (exercise.metadata_json?.options ?? []).filter(
    (option): option is { id: string; label?: unknown } => typeof option?.id === "string" && option.id.trim().length > 0
  );

  const getOptionLabel = (label: unknown, fallbackId: string): string => {
    if (typeof label === "string") {
      const trimmed = label.trim();
      return trimmed.length > 0 ? trimmed : fallbackId;
    }

    return fallbackId;
  };

  return (
    <form
      className="exercise-form"
      onSubmit={(event) => {
        event.preventDefault();
        if (!selectedOptionId || disabled) {
          return;
        }

        void onSubmit({ selected_option_id: selectedOptionId });
      }}
    >
      <fieldset className="exercise-fieldset" disabled={disabled}>
        <legend className="exercise-prompt">{exercise.prompt}</legend>
        <div className="exercise-options-list">
          {options.map((option) => (
            <label key={option.id} className="exercise-option">
              <input
                type="radio"
                name={`exercise-${exercise.id}`}
                value={option.id}
                checked={selectedOptionId === option.id}
                onChange={() => setSelectedOptionId(option.id)}
              />
              <span>{getOptionLabel(option.label, option.id)}</span>
            </label>
          ))}
        </div>
      </fieldset>
      <button type="submit" className="button labs-inline-button" disabled={disabled || !selectedOptionId}>
        Submit answer
      </button>
    </form>
  );
}
