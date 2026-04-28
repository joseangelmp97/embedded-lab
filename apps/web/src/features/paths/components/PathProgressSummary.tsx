import type { PathProgressSummary as PathProgressSummaryType } from "@/features/paths/types";

interface PathProgressSummaryProps {
  summary: PathProgressSummaryType;
  compact?: boolean;
}

export function PathProgressSummary({ summary, compact = false }: PathProgressSummaryProps) {
  return (
    <section className={`path-progress-summary ${compact ? "is-compact" : ""}`.trim()} aria-label={`${summary.path_name} progress`}>
      <div className="path-progress-summary-header">
        <p className="path-progress-summary-title">{summary.path_name}</p>
        <p className="path-progress-summary-percent">{summary.completion_percentage}%</p>
      </div>

      {!compact ? <p className="path-progress-summary-description">{summary.path_description}</p> : null}

      <div
        className="progress-bar-track"
        role="progressbar"
        aria-valuemin={0}
        aria-valuemax={100}
        aria-valuenow={summary.completion_percentage}
      >
        <div className="progress-bar-fill" style={{ width: `${summary.completion_percentage}%` }} />
      </div>

      <p className="path-progress-summary-meta">
        <strong>{summary.completed_labs}</strong> / {summary.total_labs} completed · {summary.in_progress_labs} in progress · {summary.locked_labs} locked
      </p>
    </section>
  );
}
