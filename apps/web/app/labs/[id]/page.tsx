"use client";

import Link from "next/link";
import { useEffect, useMemo, useState } from "react";
import { useAuth } from "@/features/auth/useAuth";
import {
  formatDifficultyLabel,
  formatLabProgressStatusLabel,
  formatStatusLabel,
  formatTimestamp
} from "@/features/labs/labFormatters";
import { FillBlankExercise } from "@/features/labs/components/FillBlankExercise";
import { MultipleChoiceExercise } from "@/features/labs/components/MultipleChoiceExercise";
import { ShortTextExercise } from "@/features/labs/components/ShortTextExercise";
import {
  createOrResumeLabAttempt,
  fetchLabExercises,
  submitExerciseAnswer
} from "@/features/labs/interactiveLabsService";
import {
  canOpenExercise,
  getExerciseRoadmapStatus,
  getFirstUnansweredIndex,
  type ExerciseRoadmapStatus
} from "@/features/labs/interactiveRoadmap";
import { getEffectiveLabProgressStatus, isLabLocked, LOCKED_LAB_MESSAGE } from "@/features/labs/labProgressRules";
import type { ExerciseAttemptResult, LabExercise } from "@/features/labs/interactiveTypes";
import { useLabDetail } from "@/features/labs/useLabDetail";
import { useLabProgress } from "@/features/labs/useLabProgress";
import { ApiClientError } from "@/lib/apiClient";

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
    reopenLabProgress
  } = useLabProgress(Boolean(user));

  const displayName = user?.display_name?.trim() || "Learner";
  const [exercises, setExercises] = useState<LabExercise[]>([]);
  const [isExercisesLoading, setIsExercisesLoading] = useState(false);
  const [exercisesError, setExercisesError] = useState<string | null>(null);
  const [attemptId, setAttemptId] = useState<string | null>(null);
  const [submitError, setSubmitError] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [activeExerciseIndex, setActiveExerciseIndex] = useState(0);
  const [answersByExerciseId, setAnswersByExerciseId] = useState<Record<string, ExerciseAttemptResult>>({});
  const [latestResult, setLatestResult] = useState<ExerciseAttemptResult | null>(null);
  const [attemptSummary, setAttemptSummary] = useState<{ total: number; max: number; status: string } | null>(null);
  const [supportsExerciseCompletion, setSupportsExerciseCompletion] = useState<boolean | null>(null);

  const labProgressStatus = lab ? getLabStatus(lab.id) : "not_started";
  const locked = lab ? isLabLocked(lab, getLabStatus) : false;
  const effectiveLabProgressStatus = getEffectiveLabProgressStatus(labProgressStatus, locked);
  const firstUnansweredIndex = useMemo(
    () => getFirstUnansweredIndex(exercises, answersByExerciseId),
    [answersByExerciseId, exercises]
  );
  const activeExercise = exercises[activeExerciseIndex] ?? null;

  useEffect(() => {
    if (!lab || locked) {
      setSupportsExerciseCompletion(null);
      return;
    }

    let isCancelled = false;

    const checkExerciseAvailability = async () => {
      try {
        const fetchedExercises = await fetchLabExercises(lab.id);

        if (!isCancelled) {
          setSupportsExerciseCompletion(fetchedExercises.length > 0);
        }
      } catch {
        if (!isCancelled) {
          setSupportsExerciseCompletion(null);
        }
      }
    };

    void checkExerciseAvailability();

    return () => {
      isCancelled = true;
    };
  }, [lab, locked]);

  const loadInteractiveData = async () => {
    if (!lab || locked) {
      return;
    }

    setIsExercisesLoading(true);
    setExercisesError(null);
    setSubmitError(null);

    try {
      const [fetchedExercises, attempt] = await Promise.all([fetchLabExercises(lab.id), createOrResumeLabAttempt(lab.id)]);
      const sortedExercises = [...fetchedExercises].sort((a, b) => a.order_index - b.order_index);

      setExercises(sortedExercises);
      setAttemptId(attempt.id);
      setAttemptSummary({
        total: attempt.total_score_awarded,
        max: attempt.max_score,
        status: attempt.lab_attempt_status
      });
      setActiveExerciseIndex(0);
    } catch (caughtError) {
      setExercisesError(caughtError instanceof Error ? caughtError.message : "Failed to load interactive exercises.");
    } finally {
      setIsExercisesLoading(false);
    }
  };

  const submitActiveExercise = async (responsePayload: Record<string, unknown>) => {
    if (!lab || !attemptId || !activeExercise) {
      return;
    }

    setSubmitError(null);
    setIsSubmitting(true);

    try {
      const response = await submitExerciseAnswer(lab.id, attemptId, {
        exercise_id: activeExercise.id,
        response_payload_json: responsePayload
      });
      const updatedResult: ExerciseAttemptResult = {
        exercise_id: activeExercise.id,
        exercise_type: activeExercise.exercise_type,
        is_correct: response.is_correct,
        score_awarded: response.score_awarded,
        max_score: response.max_score,
        feedback: response.feedback
      };

      setAnswersByExerciseId((current) => ({
        ...current,
        [activeExercise.id]: updatedResult
      }));
      setLatestResult(updatedResult);

      setAttemptSummary({
        total: response.session.total_score_awarded,
        max: response.session.max_score,
        status: response.session.lab_attempt_status
      });
    } catch (caughtError) {
      if (caughtError instanceof ApiClientError && caughtError.status === 422) {
        setSubmitError(
          "Your answer format is invalid for this exercise. Please review your input and try again."
        );
      } else {
        setSubmitError(caughtError instanceof Error ? caughtError.message : "Failed to submit answer.");
      }
    } finally {
      setIsSubmitting(false);
    }
  };

  const goToNextAvailable = () => {
    const nextIndex = Math.min(firstUnansweredIndex, exercises.length - 1);
    setActiveExerciseIndex((current) => {
      if (current >= nextIndex) {
        return current;
      }

      return current + 1;
    });
  };

  const roadmapStatusClass: Record<ExerciseRoadmapStatus, string> = {
    current: "is-current",
    not_answered: "is-not-answered",
    answered_correct: "is-correct",
    answered_incorrect: "is-incorrect",
    locked: "is-locked"
  };

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
              ) : null}
            </div>

            {!locked && supportsExerciseCompletion ? (
              <p className="feedback">Complete the exercises to finish this lab.</p>
            ) : null}

            {locked ? null : (
              <section className="interactive-lab-card" aria-label="Interactive exercises">
                <div className="interactive-header-row">
                  <h3>Interactive exercises</h3>
                  <button
                    type="button"
                    className="button secondary labs-inline-button"
                    onClick={() => void loadInteractiveData()}
                    disabled={isExercisesLoading}
                  >
                    {isExercisesLoading ? "Loading..." : "Start / resume exercises"}
                  </button>
                </div>

                {isExercisesLoading ? <p className="feedback">Loading exercises...</p> : null}
                {exercisesError ? <p className="feedback error">{exercisesError}</p> : null}
                {submitError ? <p className="feedback error">{submitError}</p> : null}

                {!isExercisesLoading && !exercisesError && exercises.length === 0 ? (
                  <p className="feedback">Interactive exercises coming soon.</p>
                ) : null}

                {exercises.length > 0 && activeExercise ? (
                  <div className="interactive-layout">
                    <section className="interactive-active-panel">
                      <p className="interactive-active-title">
                        Exercise {activeExerciseIndex + 1} of {exercises.length}
                      </p>

                      {activeExercise.exercise_type === "multiple_choice" ? (
                        <MultipleChoiceExercise
                          key={activeExercise.id}
                          exercise={activeExercise}
                          disabled={isSubmitting}
                          onSubmit={submitActiveExercise}
                        />
                      ) : null}

                      {activeExercise.exercise_type === "fill_blank" ? (
                        <FillBlankExercise
                          key={activeExercise.id}
                          exercise={activeExercise}
                          disabled={isSubmitting}
                          onSubmit={submitActiveExercise}
                        />
                      ) : null}

                      {activeExercise.exercise_type === "short_text" ? (
                        <ShortTextExercise
                          key={activeExercise.id}
                          exercise={activeExercise}
                          disabled={isSubmitting}
                          onSubmit={submitActiveExercise}
                        />
                      ) : null}

                      {latestResult?.exercise_id === activeExercise.id ? (
                        <div className={`exercise-result ${latestResult.is_correct ? "is-correct" : "is-incorrect"}`}>
                          <p>
                            <strong>{latestResult.is_correct ? "Correct" : "Incorrect"}</strong> · Score {latestResult.score_awarded}/
                            {latestResult.max_score}
                          </p>
                          <p>{latestResult.feedback}</p>
                          <div className="lab-card-actions">
                            <button
                              type="button"
                              className="button labs-inline-button"
                              onClick={goToNextAvailable}
                              disabled={activeExerciseIndex >= exercises.length - 1}
                            >
                              Next
                            </button>
                          </div>
                        </div>
                      ) : null}

                      {activeExerciseIndex === exercises.length - 1 && latestResult?.exercise_id === activeExercise.id ? (
                        <p className="feedback success">
                          {attemptSummary?.status === "completed"
                            ? "Lab completed automatically by backend. Great job!"
                            : "You reached the last exercise. Complete remaining exercise checks to finish automatically."}
                        </p>
                      ) : null}
                    </section>

                    <aside className="interactive-roadmap-panel" aria-label="Exercise roadmap">
                      <h4>Roadmap</h4>
                      <ul className="exercise-roadmap-list">
                        {exercises.map((exercise, index) => {
                          const status = getExerciseRoadmapStatus({
                            exercise,
                            exerciseIndex: index,
                            currentIndex: activeExerciseIndex,
                            firstUnansweredIndex,
                            answersByExerciseId
                          });
                          const isAccessible = canOpenExercise({
                            exercise,
                            exerciseIndex: index,
                            firstUnansweredIndex,
                            answersByExerciseId
                          });

                          return (
                            <li key={exercise.id}>
                              <button
                                type="button"
                                className={`exercise-roadmap-item ${roadmapStatusClass[status]}`}
                                onClick={() => {
                                  if (!isAccessible) {
                                    return;
                                  }

                                  setActiveExerciseIndex(index);
                                }}
                                disabled={!isAccessible}
                              >
                                <span>
                                  #{index + 1} · {exercise.exercise_type}
                                </span>
                                <span>{exercise.prompt.slice(0, 52)}{exercise.prompt.length > 52 ? "..." : ""}</span>
                                <small>
                                  {status === "current" ? "Current" : null}
                                  {status === "not_answered" ? "Not answered" : null}
                                  {status === "answered_correct" ? "Answered correct" : null}
                                  {status === "answered_incorrect" ? "Answered incorrect" : null}
                                  {status === "locked"
                                    ? index === firstUnansweredIndex + 1
                                      ? "Complete previous exercise to unlock"
                                      : "Coming next"
                                    : null}
                                </small>
                              </button>
                            </li>
                          );
                        })}
                      </ul>
                    </aside>
                  </div>
                ) : null}
              </section>
            )}
          </article>
        ) : null}
      </main>
    </div>
  );
}
