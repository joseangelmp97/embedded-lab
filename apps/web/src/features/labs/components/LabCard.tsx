import Link from "next/link";
import { formatDifficultyLabel, formatStatusLabel } from "@/features/labs/labFormatters";
import type { Lab } from "@/features/labs/types";

interface LabCardProps {
  lab: Lab;
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

      <div className="lab-card-actions">
        <Link href={`/labs/${lab.id}`} className="button secondary labs-inline-button">
          View details
        </Link>
      </div>
    </article>
  );
}
