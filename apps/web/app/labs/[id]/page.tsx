"use client";

import Link from "next/link";
import { useAuth } from "@/features/auth/useAuth";
import {
  formatDifficultyLabel,
  formatLabProgressStatusLabel,
  formatStatusLabel,
  formatTimestamp
} from "@/features/labs/labFormatters";
import { getEffectiveLabProgressStatus, isLabLocked, LOCKED_LAB_MESSAGE } from "@/features/labs/labProgressRules";
import { useLabDetail } from "@/features/labs/useLabDetail";
import { useLabProgress } from "@/features/labs/useLabProgress";

interface LabDetailPageProps {
  params: {
    id: string;
  };
}

export default function LabDetailPage({ params }: LabDetailPageProps) {
  const { user, isInitializing, handleLogout } = useAuth();
  const { lab, isLoading, error } = useLabDetail(params.id, Boolean(user));
  const {
    isLoading: isProgressLoading,
    loadingError: progressLoadingError,
    actionError: progressActionError,
    pendingActions,
    getLabStatus,
    startLabProgress,
    completeLabProgress,
    reopenLabProgress
  } = useLabProgress(Boolean(user));

  const displayName = user?.display_name?.trim() || "Learner";
  const labProgressStatus = lab ? getLabStatus(lab.id) : "not_started";
  const locked = lab ? isLabLocked(lab, getLabStatus) : false;
  const effectiveLabProgressStatus = getEffectiveLabProgressStatus(labProgressStatus, locked);

  if (isInitializing) {
    return (
      <main className="public-auth-page">
        <section className="card auth-card" aria-live="polite">
          <p className="feedback">Loading your session...</p>
        </section>
      </main>
    );
  }

  if (!user) {
    return (
      <main className="public-auth-page">
        <section className="card auth-card" aria-label="Protected route">
          <h1 className="auth-heading">Login required</h1>
          <p className="subtitle">You need an active session to access lab details.</p>
          <Link href="/" className="button labs-inline-button">
            Go to login
          </Link>
        </section>
      </main>
    );
  }

  return (
    <div className="private-shell">
      <header className="shell-header">
        <div className="shell-brand">
          <p className="shell-eyebrow">Embedded Lab</p>
          <h1 className="shell-title">Lab Details</h1>
        </div>

        <div className="shell-user">
          <p className="shell-user-name">{displayName}</p>
          <p className="shell-user-email">{user.email}</p>
          <button type="button" className="button secondary shell-logout" onClick={handleLogout}>
            Logout
          </button>
        </div>
      </header>

      <main className="shell-main labs-main">
        <section className="welcome-card" aria-label="Lab detail actions">
          <h2>Lab overview</h2>
          <p className="subtitle">Review this lab before starting your practical embedded systems exercise.</p>
          <div className="labs-page-actions">
            <Link href="/labs" className="button secondary labs-inline-button">
              Back to labs
            </Link>
          </div>
        </section>

        {isLoading ? <p className="feedback">Loading lab details...</p> : null}
        {error ? <p className="feedback error">{error}</p> : null}
        {isProgressLoading ? <p className="feedback">Loading your lab progress...</p> : null}
        {progressLoadingError ? <p className="feedback error">{progressLoadingError}</p> : null}
        {progressActionError ? <p className="feedback error">{progressActionError}</p> : null}

        {!isLoading && !error && lab ? (
          <article className={`lab-detail-card ${locked ? "is-locked" : ""}`} aria-label={`Lab ${lab.title}`}>
            <div className="lab-card-header">
              <h2>{lab.title}</h2>
              <span className={`status-badge ${lab.status === "published" ? "is-published" : ""}`}>
                {formatStatusLabel(lab.status)}
              </span>
            </div>

            <p className="lab-card-description">{lab.description}</p>
            {locked ? <p className="lab-lock-message">{LOCKED_LAB_MESSAGE}</p> : null}

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
                <dt>Order index</dt>
                <dd>{lab.order_index}</dd>
              </div>
              <div>
                <dt>Created</dt>
                <dd>{formatTimestamp(lab.created_at)}</dd>
              </div>
              <div>
                <dt>Updated</dt>
                <dd>{formatTimestamp(lab.updated_at)}</dd>
              </div>
              <div>
                <dt>Lab id</dt>
                <dd className="lab-id-value">{lab.id}</dd>
              </div>
              <div>
                <dt>Your progress</dt>
                <dd>
                  <span className={`progress-badge progress-${effectiveLabProgressStatus}`}>
                    {formatLabProgressStatusLabel(effectiveLabProgressStatus)}
                  </span>
                </dd>
              </div>
            </dl>

            <div className="lab-card-actions">
              <button
                type="button"
                className="button secondary labs-inline-button"
                onClick={() => void startLabProgress(lab.id)}
                disabled={locked || effectiveLabProgressStatus !== "not_started" || Boolean(pendingActions[lab.id])}
              >
                {pendingActions[lab.id]
                  ? "Saving..."
                  : locked
                    ? "Locked"
                    : effectiveLabProgressStatus === "not_started"
                      ? "Start lab"
                      : effectiveLabProgressStatus === "completed"
                        ? "Completed"
                      : "Started"}
              </button>
              {locked ? null : effectiveLabProgressStatus === "completed" ? (
                <button
                  type="button"
                  className="button secondary labs-inline-button"
                  onClick={() => void reopenLabProgress(lab.id)}
                  disabled={Boolean(pendingActions[lab.id])}
                >
                  {pendingActions[lab.id] ? "Saving..." : "Practice again"}
                </button>
              ) : (
                <button
                  type="button"
                  className="button secondary labs-inline-button"
                  onClick={() => {
                    if (window.confirm("Mark this lab as completed?")) {
                      void completeLabProgress(lab.id);
                    }
                  }}
                  disabled={Boolean(pendingActions[lab.id])}
                >
                  {pendingActions[lab.id] ? "Saving..." : "Mark as completed"}
                </button>
              )}
            </div>
          </article>
        ) : null}
      </main>
    </div>
  );
}
