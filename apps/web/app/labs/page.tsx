"use client";

import Link from "next/link";
import { useAuth } from "@/features/auth/useAuth";
import { LabCard } from "@/features/labs/components/LabCard";
import { useLabProgress } from "@/features/labs/useLabProgress";
import { useLabs } from "@/features/labs/useLabs";

export default function LabsPage() {
  const { user, isInitializing, handleLogout } = useAuth();
  const { labs, isLoading, error, reload } = useLabs(Boolean(user));
  const {
    isLoading: isProgressLoading,
    loadingError: progressLoadingError,
    actionError: progressActionError,
    pendingActions,
    getLabStatus,
    reload: reloadProgress,
    startLabProgress,
    completeLabProgress
  } = useLabProgress(Boolean(user));

  const displayName = user?.display_name?.trim() || "Learner";

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
          <p className="subtitle">You need an active session to access labs.</p>
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
          <h1 className="shell-title">Labs</h1>
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
        <section className="welcome-card" aria-label="Labs summary">
          <h2>Available labs</h2>
          <p className="subtitle">Explore hands-on exercises and keep progressing through practical scenarios.</p>
          <div className="labs-page-actions">
            <Link href="/" className="button secondary labs-inline-button">
              Back to dashboard
            </Link>
            <button type="button" className="button secondary labs-inline-button" onClick={() => void reload()}>
              Refresh labs
            </button>
            <button type="button" className="button secondary labs-inline-button" onClick={() => void reloadProgress()}>
              Refresh progress
            </button>
          </div>
        </section>

        {isLoading ? <p className="feedback">Loading labs...</p> : null}
        {error ? <p className="feedback error">{error}</p> : null}
        {isProgressLoading ? <p className="feedback">Loading your lab progress...</p> : null}
        {progressLoadingError ? <p className="feedback error">{progressLoadingError}</p> : null}
        {progressActionError ? <p className="feedback error">{progressActionError}</p> : null}

        {!isLoading && !error && labs.length === 0 ? (
          <section className="welcome-card" aria-live="polite">
            <h2>No labs available</h2>
            <p className="subtitle">New labs will appear here as soon as they are published.</p>
          </section>
        ) : null}

        {!isLoading && !error && labs.length > 0 ? (
          <section className="labs-grid" aria-label="Labs list">
            {labs.map((lab) => (
              <LabCard
                key={lab.id}
                lab={lab}
                progressStatus={getLabStatus(lab.id)}
                isSubmitting={Boolean(pendingActions[lab.id])}
                onStart={() => void startLabProgress(lab.id)}
                onComplete={() => void completeLabProgress(lab.id)}
              />
            ))}
          </section>
        ) : null}
      </main>
    </div>
  );
}
