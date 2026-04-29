# DATA_MODEL.md

## Overview

This document defines the conceptual data model for Embedded Lab, an interactive learning platform for embedded systems.

Scope includes:

- authentication and user identity
- content hierarchy (tracks, levels, challenges, questions)
- attempts and evaluations
- scoring, progress, and leaderboard
- optional achievements

This is a conceptual model only (no SQL schema yet).

Naming rule for question metadata:

- Internal storage and domain model use `metadata_json`.
- API responses use `metadata`.

---

## 1) Core Entities

## User

Purpose:
- Represents an authenticated account that can access the platform.

Main fields:
- `id`
- `email`
- `password_hash` (or external auth reference)
- `auth_provider` (local, oauth, etc.)
- `role` (learner, admin)
- `status` (active, suspended)
- `last_login_at`
- `created_at`
- `updated_at`

Relationships:
- One `User` has one `UserProfile`
- One `User` has many `Attempt`
- One `User` has one `UserScore` aggregate
- One `User` has many `Leaderboard` entries (historical snapshots, optional)
- One `User` has many `UserAchievement` records (optional)
- One `User` has many `Achievement` records through `UserAchievement` (optional)

---

## UserProfile

Purpose:
- Stores user-facing profile and learning metadata separate from authentication.

Main fields:
- `id`
- `user_id`
- `display_name`
- `avatar_url` (optional)
- `country` (optional)
- `preferred_language` (optional)
- `learning_goal` (optional)
- `created_at`
- `updated_at`

Relationships:
- Many-to-one with `User` (conceptually 1:1 via unique `user_id`)

---

## UserProgress

Purpose:
- Stores explicit progress state per user across tracks, levels, and challenges.

Main fields:
- `id`
- `user_id`
- `track_id` (nullable)
- `level_id` (nullable)
- `challenge_id` (nullable)
- `status` (`locked`, `unlocked`, `in_progress`, `completed`)
- `completion_percentage`
- `last_attempt_id` (optional)
- `updated_at`

Relationships:
- Many-to-one with `User`
- Optional references to `Track`, `Level`, `Challenge`

---

## Track

Purpose:
- Top-level learning path (for example, basics, microcontrollers, sensors).

Main fields:
- `id`
- `slug`
- `title`
- `description`
- `order_index`
- `is_published`
- `version`
- `created_at`
- `updated_at`

Relationships:
- One `Track` has many `Level`

---

## Level

Purpose:
- Ordered segment within a track.

Main fields:
- `id`
- `track_id`
- `slug`
- `title`
- `description`
- `order_index`
- `difficulty`
- `is_published`
- `created_at`
- `updated_at`

Relationships:
- Many-to-one with `Track`
- One `Level` has many `Challenge`

---

## Challenge

Purpose:
- Learning unit containing one or more questions around a specific embedded topic.

Main fields:
- `id`
- `level_id`
- `slug`
- `title`
- `description`
- `learning_objectives` (conceptual list)
- `order_index`
- `difficulty`
- `max_score`
- `is_published`
- `created_at`
- `updated_at`

Relationships:
- Many-to-one with `Level`
- One `Challenge` has many `Question`
- One `Challenge` has many `Attempt` (through user submissions)

---

## Question

Purpose:
- Atomic item to evaluate user understanding.

Main fields:
- `id`
- `challenge_id`
- `question_type`
- `prompt`
- `order_index`
- `max_score`
- `evaluation_mode` (`deterministic`, `ai_assisted`, `hybrid`)
- `metadata_json` (type-specific structure)
- `is_required`
- `created_at`
- `updated_at`

Relationships:
- Many-to-one with `Challenge`
- One `Question` has many `QuestionResponse`

---

## Lab

Purpose:
- Represents a practical hands-on embedded exercise shown in the Labs UI.

Main fields:
- `id` (stable string slug)
- `path_id` (nullable reference to `Path`)
- `module_id` (nullable reference to `PathModule`; nullable for backward compatibility and incremental rollout)
- `prerequisite_lab_id` (nullable self-reference to `Lab`; used for guided progression inside a path)
- `slug` (nullable URL-safe identifier)
- `title`
- `description`
- `learning_objectives_json` (nullable serialized list)
- `tags_json` (nullable serialized list)
- `hardware_requirements_json` (nullable serialized list)
- `content_version` (default `1`)
- `is_optional` (default `false`)
- `difficulty` (`beginner`, `intermediate`, `advanced`)
- `estimated_minutes`
- `status` (`draft`, `published`, `archived`)
- `order_index`
- `created_at`
- `updated_at`

Relationships:
- Many-to-one with `Path`
- Optional many-to-one with `PathModule`
- Optional many-to-one self-reference with `Lab` through `prerequisite_lab_id`
- One `Lab` has many `LabProgress` records

---

## PathModule

Purpose:
- Represents a module inside a learning path used to group labs into smaller ordered units.

Main fields:
- `id`
- `path_id` (reference to `Path`)
- `slug`
- `title`
- `description`
- `order_index`
- `is_published`
- `created_at`
- `updated_at`

Relationships:
- Many-to-one with `Path`
- One `PathModule` has many `Lab`

---

## Path

Purpose:
- Represents a top-level learning path used to group labs into guided sequences.

Main fields:
- `id`
- `name`
- `description`
- `order`
- `created_at`
- `updated_at`

Relationships:
- One `Path` has many `PathModule`
- One `Path` has many `Lab`

---

## LabProgress

Purpose:
- Stores user-specific progress state for each lab.

Main fields:
- `id`
- `user_id`
- `lab_id`
- `status` (`not_started`, `in_progress`, `completed`)
- `started_at` (nullable)
- `completed_at` (nullable)
- `created_at`
- `updated_at`

Constraints:
- Unique progress per `(user_id, lab_id)`.

Relationships:
- Many-to-one with `User`
- Many-to-one with `Lab`

---

## Attempt

Purpose:
- Represents one user submission session for a challenge.

Main fields:
- `id`
- `user_id`
- `challenge_id`
- `attempt_number`
- `status` (`started`, `submitted`, `evaluated`, `failed`, `evaluating`)
- `submitted_at`
- `evaluated_at`
- `total_score_awarded`
- `max_score`
- `evaluation_summary_json`
- `created_at`
- `updated_at`
- `started_at`
- `time_spent_seconds`
- `content_version`

Relationships:
- Many-to-one with `User`
- Many-to-one with `Challenge`
- One `Attempt` has many `QuestionResponse`
- One `Attempt` may produce one score event in `UserScore` history (conceptual)

---

## QuestionResponse

Purpose:
- Stores per-question user answer and evaluation result within an attempt.

Main fields:
- `id`
- `attempt_id`
- `question_id`
- `response_payload_json`
- `is_correct` (boolean)
- `is_partial` (boolean)
- `score_awarded`
- `max_score`
- `evaluation_mode_used` (`deterministic`, `ai_assisted`)
- `feedback`
- `evaluation_details_json`
- `evaluated_at`
- `created_at`
- `updated_at`
- `time_spent_seconds`

Relationships:
- Many-to-one with `Attempt`
- Many-to-one with `Question`

---

## UserScore (Score)

Purpose:
- Maintains user scoring totals and normalized ranking metrics.

Main fields:
- `id`
- `user_id`
- `total_points`
- `normalized_points`
- `best_attempt_points` (optional)
- `last_score_update_at`
- `version` (for optimistic updates)
- `created_at`
- `updated_at`

Optional supporting concept:
- `ScoreEvent` (append-only history for auditability and anti-inflation checks)
  - `id`, `user_id`, `attempt_id`, `points_delta`, `reason`, `created_at`

Relationships:
- Many-to-one with `User` (often 1:1 aggregate by unique `user_id`)
- Derived from `Attempt` and `QuestionResponse` results

---

## Leaderboard

Purpose:
- Stores ranking output for fast retrieval and historical snapshots.

Main fields:
- `id`
- `scope_type` (`global`, `track`, `level`, `time_window`)
- `scope_ref_id` (nullable for global)
- `user_id`
- `rank_position`
- `score_value`
- `snapshot_at`
- `created_at`

Relationships:
- Many-to-one with `User`
- Optionally scoped to `Track` or `Level` through `scope_ref_id`

---

## Achievement (Optional but Recommended)

Purpose:
- Rewards milestones and supports engagement.

Main fields:
- `id`
- `key`
- `title`
- `description`
- `criteria_json`
- `points_bonus` (optional)
- `is_active`
- `created_at`
- `updated_at`

User ownership bridge (conceptual):
- `UserAchievement`
  - `id`, `user_id`, `achievement_id`, `awarded_at`, `source_ref`, `created_at`

Relationships:
- Many-to-many between `User` and `Achievement` via `UserAchievement`

---

## 2) Relationship Summary

Primary one-to-many relationships:

- `Track` -> `Level` (1:N)
- `Path` -> `Lab` (1:N)
- `Level` -> `Challenge` (1:N)
- `Challenge` -> `Question` (1:N)
- `User` -> `Attempt` (1:N)
- `Challenge` -> `Attempt` (1:N)
- `Attempt` -> `QuestionResponse` (1:N)
- `Question` -> `QuestionResponse` (1:N)
- `User` -> `Leaderboard` entries (1:N snapshots)
- `User` -> `UserAchievement` (1:N, optional)

Primary many-to-one relationships:

- `Level` -> `Track` (N:1)
- `Lab` -> `Path` (N:1)
- `Challenge` -> `Level` (N:1)
- `Question` -> `Challenge` (N:1)
- `Attempt` -> `User` (N:1)
- `Attempt` -> `Challenge` (N:1)
- `QuestionResponse` -> `Attempt` (N:1)
- `QuestionResponse` -> `Question` (N:1)

One-to-one style relationships (enforced by uniqueness):

- `User` <-> `UserProfile`
- `User` <-> `UserScore` aggregate

Many-to-many (optional):

- `User` <-> `Achievement` via `UserAchievement`

---

## 3) Question Structure

Questions are polymorphic by `question_type` with shared core fields plus type-specific metadata in `metadata_json`.

Shared fields:
- `question_type`
- `prompt`
- `max_score`
- `evaluation_mode`

`metadata_json` stores per-type configuration, such as:

- `single_choice`: options, correct_option_id
- `multiple_choice`: options, correct_option_ids, partial_scoring_rules
- `fill_blank_code`: template, expected_tokens/patterns, tolerance rules
- `order_steps`: step_pool, expected_order, scoring strategy
- `component_selection`: valid_components, required_set, constraints
- `connection_graph`: allowed_nodes, required_connections, forbidden_connections
- `natural_language_ai`: rubric, required concepts, safety constraints, fallback rules

Design principle:
- Add new question types via new evaluator strategies and metadata schema, without changing core question entity shape.

---

## 4) Attempt and Evaluation Model

Attempt storage:
- One `Attempt` per user submission session for a challenge.
- `attempt_number` increments per (`user_id`, `challenge_id`).
- Stores lifecycle timestamps and overall score summary.

Response storage:
- `QuestionResponse` stores each per-question answer payload and result.
- `response_payload_json` keeps raw structured input by question type.
- One response per (`attempt_id`, `question_id`) for normal flows.

Evaluation result storage:
- Per-question evaluation fields live in `QuestionResponse`:
  - correctness/partial correctness
  - awarded score
  - feedback
  - details JSON (for traceability)
- Aggregated attempt result lives in `Attempt`:
  - `total_score_awarded`
  - evaluation summary JSON

Deterministic and AI-assisted support:
- `evaluation_mode_used` records which path was used.
- AI outputs are persisted only after schema validation and safety checks.
- Invalid AI outputs trigger deterministic fallback or safe failure state.

---

## 5) Constraints

Uniqueness constraints (conceptual):
- `User.email` unique
- `Track.slug` unique
- (`Level.track_id`, `Level.slug`) unique
- (`Challenge.level_id`, `Challenge.slug`) unique
- (`Question.challenge_id`, `Question.order_index`) unique
- (`Attempt.user_id`, `Attempt.challenge_id`, `Attempt.attempt_number`) unique
- (`QuestionResponse.attempt_id`, `QuestionResponse.question_id`) unique
- `UserProfile.user_id` unique
- `UserScore.user_id` unique
- For leaderboard snapshots: (`scope_type`, `scope_ref_id`, `snapshot_at`, `user_id`) unique

Idempotency for progress updates:
- Progress updates are keyed by stable events (for example `attempt_id` + transition state).
- Reprocessing the same evaluation event must not duplicate completion or points.
- Progress engine should ignore duplicate terminal updates for the same attempt.

Avoiding score inflation:
- Define scoring policy per challenge (for example best-attempt-only or capped retries).
- Prevent repeated identical submissions from granting unlimited points.
- Use append-only score events (recommended) plus deduplication keys.
- Recompute leaderboard from trusted aggregates/events when needed.

---

## 6) Notes on Future Scalability

- Keep domain boundaries strict (`content`, `attempts`, `evaluation`, `scoring`, `progress`, `leaderboard`).
- Use append-only event history for scoring/progress auditability and recovery.
- Version content and question metadata schemas to support backward compatibility.
- Version scoring policies to preserve historical leaderboard fairness.
- Separate read-optimized leaderboard views from write paths for performance.
- Introduce partitioning/sharding strategies for high-volume `Attempt` and `QuestionResponse` data.
- Cache frequently requested content trees (tracks/levels/challenges) with invalidation on publish updates.
- Keep AI evaluation asynchronous-capable for future queue-based scaling and retries.
- Maintain deterministic fallback paths to preserve availability when AI services degrade.

---

## 7) Canonical Enums

Use these values consistently across data model, architecture, and API contract.

### difficulty

- `beginner`
- `intermediate`
- `advanced`

### attempt_status

- `started`
- `submitted`
- `evaluating`
- `evaluated`
- `failed`

### lab_attempt_status

- `started`
- `submitted`
- `evaluated`
- `failed`

### progress_status

- `locked`
- `unlocked`
- `in_progress`
- `completed`

### evaluation_mode

- `deterministic`
- `ai_assisted`
- `hybrid`

### question_type

- `single_choice`
- `multiple_choice`
- `fill_blank_code`
- `order_steps`
- `component_selection`
- `connection_graph`
- `natural_language_ai`

### exercise_type

- `multiple_choice`
- `fill_blank`
- `short_text`

### leaderboard_scope

- `global`
- `track`
- `level`
- `time_window`

### user_role

- `learner`
- `admin`

### user_status

- `active`
- `suspended`

### lab_status

- `draft`
- `published`
- `archived`

### lab_progress_status

- `not_started`
- `in_progress`
- `completed`


---

## 8) Phase 2 Addendum: Interactive Lab Entities (Data Model Skeleton)

### Exercise

Purpose:
- Represents one evaluable exercise inside a lab.

Main fields:
- `id`
- `lab_id`
- `exercise_type` (`multiple_choice`, `fill_blank`, `short_text`)
- `prompt`
- `order_index`
- `max_score`
- `is_required`
- `status` (`draft`, `published`, `archived`)
- `content_version`
- `metadata_json`
- `hint_policy_json`
- `explanation`
- `created_at`
- `updated_at`

Relationships:
- Many-to-one with `Lab`
- One `Exercise` has many `ExerciseAttempt`

### LabAttemptSession

Purpose:
- Represents one user session attempting exercises in a single lab.

Main fields:
- `id`
- `user_id`
- `lab_id`
- `attempt_number`
- `lab_attempt_status` (`started`, `submitted`, `evaluated`, `failed`)
- `total_score_awarded`
- `max_score`
- `required_exercises_correct`
- `required_exercises_total`
- `hints_used_count`
- `content_version`
- `started_at`
- `completed_at` (nullable)
- `updated_at`

Relationships:
- Many-to-one with `User`
- Many-to-one with `Lab`
- One `LabAttemptSession` has many `ExerciseAttempt`

### ExerciseAttempt

Purpose:
- Stores per-exercise response payload and deterministic evaluation result.

Main fields:
- `id`
- `lab_attempt_session_id`
- `exercise_id`
- `response_payload_json`
- `is_correct`
- `score_awarded`
- `max_score`
- `feedback`
- `evaluation_details_json` (optional)
- `hint_shown`
- `hint_index_shown` (nullable)
- `attempt_sequence`
- `evaluated_at`

Constraints:
- Foreign keys to `LabAttemptSession` and `Exercise`.

### Compatibility Constraints

- `LabAttemptSession` and `ExerciseAttempt` are additive and do not replace `LabProgress`.
- Existing endpoints remain authoritative for lifecycle transitions:
  - `POST /api/v1/labs/{lab_id}/start`
  - `POST /api/v1/labs/{lab_id}/complete`
  - `POST /api/v1/labs/{lab_id}/reopen`
- Phase 2 scope is schema-only (no evaluation or lifecycle endpoints in this slice).

