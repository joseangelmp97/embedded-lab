"use client";

import { useState } from "react";
import type { LabExercise } from "@/features/labs/interactiveTypes";

interface ShortTextExerciseProps {
  exercise: LabExercise;
  disabled?: boolean;
  onSubmit: (responsePayload: Record<string, unknown>) => Promise<void>;
}

export function ShortTextExercise({ exercise, disabled = false, onSubmit }: ShortTextExerciseProps) {
  const [textValue, setTextValue] = useState("");

  return (
    <form
      className="exercise-form"
      onSubmit={(event) => {
        event.preventDefault();
        if (disabled || !textValue.trim()) {
          return;
        }

        void onSubmit({ answer: textValue });
      }}
    >
      <label className="row">
        <span className="exercise-prompt">{exercise.prompt}</span>
        <textarea
          className="input exercise-textarea"
          rows={5}
          value={textValue}
          onChange={(event) => setTextValue(event.target.value)}
          placeholder="Write a concise technical explanation"
          disabled={disabled}
        />
      </label>
      <button type="submit" className="button labs-inline-button" disabled={disabled || !textValue.trim()}>
        Submit answer
      </button>
    </form>
  );
}
