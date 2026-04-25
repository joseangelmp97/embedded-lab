import type { Lab } from "@/features/labs/types";

interface LabCardProps {
  lab: Lab;
}

function formatDifficultyLabel(difficulty: Lab["difficulty"]): string {
  return difficulty.charAt(0).toUpperCase() + difficulty.slice(1);
}

function formatStatusLabel(status: string): string {
  if (!status.trim()) {
    return "Unknown";
  }

  return status
    .split("_")
    .map((word) => word.charAt(0).toUpperCase() + word.slice(1))
    .join(" ");
}

export function LabCard({ lab }: LabCardProps) {
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
      </dl>
    </article>
  );
}
