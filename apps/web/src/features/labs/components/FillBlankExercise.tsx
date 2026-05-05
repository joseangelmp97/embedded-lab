"use client";

import { useEffect, useMemo, useState } from "react";
import type { LabExercise } from "@/features/labs/interactiveTypes";

interface FillBlankExerciseProps {
  exercise: LabExercise;
  disabled?: boolean;
  onSubmit: (responsePayload: Record<string, unknown>) => Promise<void>;
}

export function FillBlankExercise({ exercise, disabled = false, onSubmit }: FillBlankExerciseProps) {
  const fields = useMemo(() => exercise.metadata_json?.fields ?? [], [exercise.metadata_json?.fields]);

  const promptText = useMemo(() => {
    if (typeof exercise.prompt !== "string") {
      return "";
    }

    return exercise.prompt;
  }, [exercise.prompt]);

  const promptParts = useMemo(() => promptText.split("____"), [promptText]);
  const blankCount = useMemo(() => Math.max(0, promptParts.length - 1), [promptParts]);

  const placeholdersByIndex = useMemo(
    () => Array.from({ length: blankCount }, (_, index) => fields[index]?.placeholder ?? "Type answer"),
    [blankCount, fields]
  );

  const [answers, setAnswers] = useState<string[]>(() => Array.from({ length: blankCount }, () => ""));

  useEffect(() => {
    setAnswers(Array.from({ length: blankCount }, () => ""));
  }, [exercise.id, blankCount]);

  const canSubmit = blankCount > 0 && answers.length === blankCount && answers.every((answer) => answer.trim().length > 0);

  const helperText = `${blankCount} blank${blankCount === 1 ? "" : "s"} to fill`;

  return (
    <form
      className="exercise-form"
      onSubmit={(event) => {
        event.preventDefault();
        if (disabled || !canSubmit) {
          return;
        }

        void onSubmit({ answers });
      }}
    >
      <p className="exercise-prompt">
        {promptParts.map((part, index) => (
          <span key={`part-${index}`}>
            {part}
            {index < blankCount ? (
              <input
                aria-label={`Blank ${index + 1}`}
                className="input"
                value={answers[index] ?? ""}
                onChange={(event) =>
                  setAnswers((current) =>
                    current.map((value, valueIndex) => (valueIndex === index ? event.target.value : value))
                  )
                }
                placeholder={placeholdersByIndex[index]}
                disabled={disabled}
                style={{ display: "inline-block", width: "clamp(120px, 28vw, 220px)", margin: "0 0.35rem" }}
              />
            ) : null}
          </span>
        ))}
      </p>
      <p className="feedback">{helperText}</p>
      <button type="submit" className="button labs-inline-button" disabled={disabled || !canSubmit}>
        Submit answer
      </button>
    </form>
  );
}
