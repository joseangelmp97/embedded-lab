import Link from "next/link";
import { formatDifficultyLabel, formatLabProgressStatusLabel, formatStatusLabel } from "@/features/labs/labFormatters";
import type { Lab, LabProgressStatus } from "@/features/labs/types";

interface LabCardProps {
  lab: Lab;
  progressStatus: LabProgressStatus;
  isSubmitting: boolean;
  onStart: () => void;
  onComplete: () => void;
}

export function LabCard({ lab, progressStatus, isSubmitting, onStart, onComplete }: LabCardProps) {
  const canStart = progressStatus === "not_started";
  const canComplete = progressStatus !== "completed";

  return (
    <article className="lab-card" aria-label={`Lab ${lab.title}`}>
      <div className="lab-card-header">
        <h2>{lab.title}</h2>
        <span className={`status-badge ${lab.status === "published" ? "is-published" : ""}`}>
          {formatStatusLabel(lab.status)}
        </span>
      </div>

      <p className="lab-card-description">{lab.description}</p>

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
          {isSubmitting ? "Saving..." : canStart ? "Start lab" : "Started"}
        </button>
        <button
          type="button"
          className="button secondary labs-inline-button"
          onClick={onComplete}
          disabled={!canComplete || isSubmitting}
        >
          {isSubmitting ? "Saving..." : canComplete ? "Mark as completed" : "Completed"}
        </button>
        <Link href={`/labs/${lab.id}`} className="button secondary labs-inline-button">
          View details
        </Link>
      </div>
    </article>
  );
}
