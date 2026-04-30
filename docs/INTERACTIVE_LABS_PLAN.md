# Interactive Labs Implementation Plan

---

## 1. Recommended Architecture

Keep strict module boundaries and add interactive behavior incrementally:

- **content**: owns exercise definitions attached to labs (prompt/type/order/hints/explanation)
- **attempts**: owns user attempt sessions + per-exercise submissions
- **evaluation**: deterministic grading for multiple_choice, fill_blank, short_text
- **scoring**: computes awarded points and hint penalties
- **progress**: updates lab progress state from evaluated attempts
- **existing labs/progress APIs**: remain compatible

### Core Flow

1. FE loads lab + exercises
2. User starts/continues an attempt session
3. User submits an exercise answer
4. Backend validates + evaluates + scores
5. Attempt persisted
6. Progress updated (in_progress/completed)
7. FE shows result + next step

---

## 2. Recommended Data Model

Add these entities (no breaking changes):

### Exercise

- `id`, `lab_id`, `type`, `prompt`, `order_index`
- `max_score`, `is_required`, `status`, `content_version`
- `metadata_json` (type-specific config)
- `hint_policy_json` (max_hints, penalty, hints[])
- `explanation`

### LabAttemptSession

- `id`, `user_id`, `lab_id`, `attempt_number`
- `status` (started|completed|abandoned)
- aggregate fields: total_score_awarded, max_score, required_exercises_correct/total, hints_used_count
- timestamps + content_version

### ExerciseAttempt

- `id`, `lab_attempt_session_id`, `exercise_id`
- `response_payload_json`
- result fields: `is_correct`, `score_awarded`, `max_score`, `feedback_text`, `evaluation_details_json`
- hint fields: `hint_shown`, `hint_index_shown`
- `attempt_sequence`, `evaluated_at`

---

## 3. Recommended Endpoints (Additive)

Keep existing endpoints intact. Add:

- `GET /api/v1/labs/{lab_id}/exercises`
- `POST /api/v1/labs/{lab_id}/attempt-sessions` (create/reuse active session)
- `GET /api/v1/lab-attempt-sessions/{session_id}`
- `POST /api/v1/lab-attempt-sessions/{session_id}/exercise-attempts`
- (optional) `POST /api/v1/lab-attempt-sessions/{session_id}/finalize`

### Submit Response Shape

Should include:

- `is_correct`
- `score_awarded`
- `feedback`
- `hint` (optional)
- `explanation` (optional)
- `session` summary (progress + aggregate score)

---

## 4. Evaluation Planning by Exercise Type

### Multiple Choice

- **Answer format**: selected option_id
- **Grading**: exact option match
- **Score**: full or zero
- **Feedback**: concise correct/incorrect reason
- **Hint**: next hint if incorrect and hints available

### Fill Blank

- **Answer format**: one value or per-blank map
- **Grading**: normalized compare (trim/case/punctuation rules)
- **Score**: full or partial by blank
- **Feedback**: indicate which blank is wrong (no leakage)
- **Hint**: guided clue for incorrect blanks

### Short Text (v1 Deterministic, No AI Yet)

- **Answer format**: short free text
- **Grading**: accepted phrase/concept matching with normalization
- **Score**: full/partial based on concept coverage
- **Feedback**: concept-based guidance
- **Hint**: conceptual nudge if incorrect

---

## 5. Progress Integration Rules

- Lab becomes **in_progress** when:
  - user starts lab explicitly, or
  - first attempt session starts

- Lab becomes **completed** automatically when completion criteria met

- **Recommended v1 completion rule**: all required exercises correct (clear and easy to explain)

- Keep manual complete/reopen endpoints for compatibility/admin use

### Reopen Behavior

- creates a new session (attempt_number +1)
- old attempts remain immutable history
- best-score policy for ranking/progress aggregation (avoid inflation)

---

## 6. Initial Interactive Subset (Small, High-Quality)

Don't convert all labs yet. Start with 3 labs from one path:

**Path**: Embedded Fundamentals

1. **Module**: Embedded Foundations - **Lab**: digital-logic-voltage-levels
2. **Module**: Embedded Foundations - **Lab**: gpio-led-basics
3. **Module**: MCU Core - **Lab**: timer-periodic-tasks

This is enough for a meaningful first learner journey.

---

## 7. Example Exercises (Seed-Ready Conceptually)

### digital-logic-voltage-levels

**Objective**: understand logic HIGH/LOW thresholds

- **MCQ** prompt: "For a 3.3V MCU, which voltage is safely interpreted as HIGH?"
  - Expected: 3.1V
  - Distractors: 0.2V, 1.1V, 1.6V
  - Correct feedback: "Well above typical VIH threshold."
  - Incorrect feedback: "HIGH must exceed input-high threshold."

- **Fill blank**: "Logic LOW is typically near ___ volts."
  - Expected: 0 (accept 0V, 0.0)

### gpio-led-basics

**Objective**: basic GPIO output control

- **MCQ**: required pin mode to drive LED ON/OFF → OUTPUT

- **Fill blank**:
  - `pinMode(LED_PIN, ____);`
  - `digitalWrite(LED_PIN, ____);`
  - Expected: OUTPUT, HIGH

- **Short text**: "Why is a resistor needed in series with LED?"
  - Expected concept: limits current/protects LED/GPIO

### timer-periodic-tasks

**Objective**: periodic behavior with timers

- **MCQ**: reason for timer vs delay loop → precision + non-blocking

- **Short text**: blocking 200ms loop impact on button handling
  - Expected: missed presses/latency

- **Fill blank**: "A 1 kHz tick is ___ ms."
  - Expected: 1

---

## 8. Frontend UX Plan

Lab detail page should include:

- lab overview/objective
- exercise list/stepper
- input by type:
  - **MCQ**: radio options
  - **fill_blank**: inline blanks or text fields
  - **short_text**: textarea with character guidance
- submit CTA
- result panel (correct/incorrect, score, feedback, hint/explanation)
- completion badge/state + next action

**Fallback for non-interactive labs**: "interactive exercises coming soon"

---

## 9. Testing Plan

### Backend

- unit tests for each evaluator type
- normalization and edge cases
- scoring + hint penalties
- progress transitions (not_started -> in_progress -> completed)
- persistence of sessions/attempts

### Integration

- full flow: start -> answer -> evaluate -> progress update
- reopen and new session behavior
- backwards compatibility with existing lab/progress endpoints

### Frontend

- component tests per exercise input type
- feedback/result rendering
- e2e/manual flow for one complete interactive lab + reopen

---

## 10. Incremental Delivery Phases

1. Docs/contracts first (DATA_MODEL, API_CONTRACT, CONTENT_SCHEMA, ARCHITECTURE updates)
2. Backend skeleton (Exercise, sessions, attempts; fetch exercises)
3. Submit/evaluate endpoint (start with MCQ)
4. Add fill_blank + short_text evaluators
5. Progress auto-completion integration
6. Seed 3 interactive labs only
7. Frontend interactive UI
8. Hardening (rate limits, idempotency, logs, regression checks)
9. Expand content gradually

---

---

# Detailed Phase Breakdown

## Phase 1 — Docs/Contracts for Exercises and Attempts

### Goal

Lock contracts first so backend/frontend can build independently and safely

### Exact Scope

- Define v1 exercise types and payloads: multiple_choice, fill_blank, short_text
- Define attempt lifecycle and submit response contract
- Document explicit constraints: no AI grading, no code execution
- Document backward compatibility with existing lab flow

### Existing Modules Affected

- content, attempts, evaluation, scoring, lab_progress, labs

### New Files/Modules Needed

- No runtime code
- Docs updates only (ARCHITECTURE, DATA_MODEL, API_CONTRACT, CONTENT_SCHEMA)

### Backend Endpoints

Contract only (no implementation yet):

- `GET /labs/{lab_id}/exercises`
- `POST /labs/{lab_id}/attempts`
- `GET /labs/{lab_id}/attempts/{attempt_id}`
- `POST /labs/{lab_id}/attempts/{attempt_id}/submit`

### Frontend Changes

- None

### Tests Required

- None (docs phase)

### Acceptance Criteria

- API/data schemas unambiguous and implementation-ready
- Backward compatibility statement explicitly documented
- v1 constraints clearly documented

**Suggested commit message**: `docs: define v1 exercise and attempt contracts`

---

## Phase 2 — Backend Data Model Skeleton

### Goal

Create minimal persistence layer for exercises and attempts

### Exact Scope

- Add tables/models for:
  - lab_exercises
  - lab_attempts
  - optional per-submission row (lab_attempt_answers / exercise_attempts)
- Add enums for exercise type and attempt status
- Add migrations
- No behavior change in progress completion yet

### Existing Modules Affected

- content, attempts, labs

### New Files/Modules Needed

- ORM model files (or extensions in existing model files)
- Migration(s)
- Optional shared enum/constants file

### Backend Endpoints

- None yet

### Frontend Changes

- None

### Tests Required

- Migration/schema tests
- Model/repository smoke tests

### Acceptance Criteria

- Tables and relations are stable and reversible
- Existing start/complete/reopen behavior unchanged

**Suggested commit message**: `feat(content,attempts): add exercise and attempt data model skeleton`

---

## Phase 3 — Fetch Exercises Endpoint

### Goal

Expose exercises for a lab to clients

### Exact Scope

- Implement exercise read endpoint
- Return ordered, published exercises only
- Hide answer keys from response

### Existing Modules Affected

- content, labs, auth (and users if access checks rely on user state)

### New Files/Modules Needed

- Route/controller
- Response DTO/schema
- Content query/service

### Backend Endpoints

- `GET /labs/{lab_id}/exercises`

### Frontend Changes

- Optional API client method only

### Tests Required

- Success + auth + 404/403 integration tests
- Ensure answer keys are not leaked

### Acceptance Criteria

- Endpoint returns valid v1 exercise payloads
- Non-interactive labs handled predictably (empty list or defined response mode)

**Suggested commit message**: `feat(content): add GET lab exercises endpoint`

---

## Phase 4 — Attempt Session Creation/Retrieval

### Goal

Enable users to open/resume lab attempt sessions

### Exact Scope

- Create attempt session for user+lab
- Retrieve attempt session by id (owner-only)
- Enforce active-attempt policy

### Existing Modules Affected

- attempts, auth, labs, lab_progress (compat checks only)

### New Files/Modules Needed

- Attempt session service/repository
- Route/controller
- DTOs

### Backend Endpoints

- `POST /labs/{lab_id}/attempts`
- `GET /labs/{lab_id}/attempts/{attempt_id}`

### Frontend Changes

- API client methods to start/get attempts

### Tests Required

- Owner authorization tests
- duplicate-active-attempt policy tests
- lifecycle state tests

### Acceptance Criteria

- Users can reliably start and retrieve their own sessions
- Legacy lab lifecycle still unchanged

**Suggested commit message**: `feat(attempts): add attempt session create and retrieve APIs`

---

## Phase 5 — Submit/Evaluate Multiple Choice

### Goal

Ship first fully interactive exercise type end-to-end

### Exact Scope

- Implement submit endpoint for multiple_choice
- Deterministic evaluator + score mapping
- Persist submission + result + feedback

### Existing Modules Affected

- attempts, evaluation, scoring, content

### New Files/Modules Needed

- multiple_choice evaluator
- submission service handler
- scoring constants/policy

### Backend Endpoints

- `POST /labs/{lab_id}/attempts/{attempt_id}/submit` (MCQ only initially)

### Frontend Changes

- API client supports submit payload for MCQ

### Tests Required

- evaluator unit tests
- scoring tests
- submit integration tests
- invalid payload/closed attempt negative tests

### Acceptance Criteria

- MCQ evaluated server-side only
- deterministic result (is_correct, score, feedback)
- no client-trusted correctness

**Suggested commit message**: `feat(evaluation): implement multiple-choice submission and scoring`

---

## Phase 6 — Add Fill Blank and Short Text Evaluators

### Goal

Complete v1 exercise type coverage

### Exact Scope

- Extend submit endpoint for fill_blank and short_text
- Add normalization rules (trim/case/spacing)
- Keep short_text deterministic (accepted answers/concepts only)

### Existing Modules Affected

- evaluation, attempts, scoring, content

### New Files/Modules Needed

- fill_blank evaluator
- short_text evaluator
- evaluator registry/factory extension

### Backend Endpoints

- Reuse submit endpoint with new supported types

### Frontend Changes

- API client typed payloads for new types

### Tests Required

- normalization edge cases
- evaluator dispatch tests
- mixed-type integration tests

### Acceptance Criteria

- All 3 exercise types pass end-to-end
- unsupported type returns clean validation error
- MCQ behavior unchanged

**Suggested commit message**: `feat(evaluation): add fill-blank and short-text deterministic evaluators`

---

## Phase 7 — Progress Auto-Completion Integration

### Goal

Connect evaluated attempts to lab completion safely

### Exact Scope

- Auto-complete interactive labs when completion criteria met
- Preserve existing manual start/complete/reopen behavior
- Idempotent updates; prevent score/progress inflation

### Existing Modules Affected

- lab_progress, attempts, evaluation, scoring, labs

### New Files/Modules Needed

- Progress integration service/hook from submit flow

### Backend Endpoints

- No new endpoint; behavior wired into submit flow and existing progress model

### Frontend Changes

- None required (existing progress views should reflect backend state)

### Tests Required

- interactive auto-complete integration tests
- reopen behavior tests
- duplicate submission idempotency tests
- legacy non-interactive regression tests

### Acceptance Criteria

- interactive labs auto-complete correctly
- legacy labs retain old behavior
- repeated submits don't inflate outcomes

**Suggested commit message**: `feat(lab_progress): auto-complete interactive labs from evaluated attempts`

---

## Phase 8 — Seed 3 Interactive Labs

### Goal

Provide real solvable content for end-to-end validation

### Exact Scope

- Seed exactly 3 labs (small subset) with mixed exercise types
- Ensure schema-valid prompts, expected answers, feedback/hints

### Existing Modules Affected

- content, labs, paths (if path linkage needed)

### New Files/Modules Needed

- seed data files / seed script updates

### Backend Endpoints

- None new

### Frontend Changes

- None required yet

### Tests Required

- seed validation tests
- fetch exercises smoke tests
- optional API flow smoke against seeded labs

### Acceptance Criteria

- 3 interactive labs available after normal seed run
- labs are solvable via APIs without manual DB intervention

**Suggested commit message**: `chore(content): seed three v1 interactive labs`

---

## Phase 9 — Frontend Interactive Lab UI

### Goal

Deliver minimal, usable learner experience for interactive labs

### Exact Scope

- Lab detail page: overview + exercise area + submit + feedback + completion state
- Components for MCQ, fill_blank, short_text
- Start/resume attempt, submit answers, show result and progress
- Keep non-interactive labs unchanged

### Existing Modules Affected

- Frontend app pages/components (lab detail/progress views)
- Backend consumed via existing APIs only

### New Files/Modules Needed

- MultipleChoiceExercise, FillBlankExercise, ShortTextExercise
- API client hooks/services for exercises/attempts/submit
- simple per-page session state

### Backend Endpoints

- Consumes phases 3–7 endpoints

### Frontend Changes

- Yes (main UI phase)

### Tests Required

- component tests for 3 input types
- page integration tests for attempt lifecycle
- e2e happy path for one seeded interactive lab
- regression for non-interactive lab UI

### Acceptance Criteria

- user can complete seeded labs in browser end-to-end
- reload/resume works via attempt retrieval
- legacy labs render exactly as before

**Suggested commit message**: `feat(web): add v1 interactive lab exercise UI flow`

---

## Phase 10 — Full Regression and Release Gate

### Goal

Ensure release safety and quality

### Exact Scope

- Run full backend/frontend tests and quality checks
- Validate old and new flows side-by-side
- Final docs/contract alignment pass

### Existing Modules Affected

- All touched modules: auth, users, labs, paths, lab_progress, attempts, evaluation, scoring, content

### New Files/Modules Needed

- Optional release checklist doc / release note entry

### Backend Endpoints

- Verify all new endpoints + legacy endpoints via regression matrix

### Frontend Changes

- Only defect fixes found during gate (small follow-up commits)

### Tests Required

- full CI suite
- manual smoke checklist:
  - legacy start/complete/reopen
  - interactive fetch/start/submit/auto-complete
  - auth and validation/security checks

### Acceptance Criteria

- CI green
- no critical regressions
- release notes include limitations (deterministic grading only, no code exec/AI)

**Suggested commit message**: `chore(release): regression gate for interactive labs v1`

---

## Strict Sequencing Dependencies

```
1 → 2 → 3 → 4 → 5 → 6 → 7 → 8 → 9 → 10
```

### Hard Gates

- Phase 5 requires 3 + 4
- Phase 6 requires 5
- Phase 7 requires 6
- Phase 9 requires 8 and stable APIs from 3–7
- Phase 10 requires everything complete
