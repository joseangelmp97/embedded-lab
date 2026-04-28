import Link from "next/link";
import { formatDifficultyLabel, formatLabProgressStatusLabel, formatStatusLabel } from "@/features/labs/labFormatters";
import { LOCKED_LAB_MESSAGE } from "@/features/labs/labProgressRules";
import type { Lab, LabProgressStatus } from "@/features/labs/types";

interface LabCardProps {
  lab: Lab;
  progressStatus: LabProgressStatus;
  isLocked: boolean;
  isSubmitting: boolean;
  onStart: () => void;
  onComplete: () => void;
  onReopen: () => void;
}

export function LabCard({ lab, progressStatus, isLocked, isSubmitting, onStart, onComplete, onReopen }: LabCardProps) {
  const canStart = !isLocked && progressStatus === "not_started";
  const isCompleted = progressStatus === "completed";

  return (
    <article className={`lab-card ${isLocked ? "is-locked" : ""}`} aria-label={`Lab ${lab.title}`}>
      <div className="lab-card-header">
        <h2>{lab.title}</h2>
        <span className={`status-badge ${lab.status === "published" ? "is-published" : ""}`}>
          {formatStatusLabel(lab.status)}
        </span>
      </div>

      <p className="lab-card-description">{lab.description}</p>
      {isLocked ? <p className="lab-lock-message">{LOCKED_LAB_MESSAGE}</p> : null}

      <dl className="lab-meta-list">
        <div>
          <dt>Difficulty</dt>
          <dd>{formatDifficultyLabel(lab.difficulty)}</dd>
        </div>
        <div>
          <dt>Estimated time</dt>
          <dd>{lab.estimated_minutes} min</dd>
        </div>
        <div>
          <dt>Your progress</dt>
          <dd>
            <span className={`progress-badge progress-${progressStatus}`}>
              {formatLabProgressStatusLabel(progressStatus)}
            </span>
          </dd>
        </div>
      </dl>

      <div className="lab-card-actions">
        <button type="button" className="button secondary labs-inline-button" onClick={onStart} disabled={!canStart || isSubmitting}>
          {isSubmitting ? "Saving..." : isLocked ? "Locked" : canStart ? "Start lab" : isCompleted ? "Completed" : "Started"}
        </button>
        {isCompleted ? (
          <button type="button" className="button secondary labs-inline-button" onClick={onReopen} disabled={isSubmitting}>
            {isSubmitting ? "Saving..." : "Reopen lab"}
          </button>
        ) : (
          <button type="button" className="button secondary labs-inline-button" onClick={onComplete} disabled={isLocked || isSubmitting}>
            {isSubmitting ? "Saving..." : "Mark as completed"}
          </button>
        )}
        <Link href={`/labs/${lab.id}`} className="button secondary labs-inline-button">
          View details
        </Link>
      </div>
    </article>
  );
}
