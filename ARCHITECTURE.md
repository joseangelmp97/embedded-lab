# ARCHITECTURE.md

## 1. High-Level System Overview

Embedded Lab is an interactive learning platform for embedded systems.
Learners complete structured challenges about electronics, microcontrollers, components, wiring, code logic, and embedded concepts. The system evaluates answers, assigns scores, updates progress, and maintains rankings.

Main components:

- Web frontend for user interaction and learning flow
- Backend API for business logic and orchestration
- PostgreSQL database for persistent data
- Evaluation engine for answer checking
- Scoring engine for score calculation and policy enforcement
- Progress engine for completion and progression updates
- AI evaluation module for natural-language answer assessment

Early-stage scope constraint:

- No full code editor
- No arbitrary code execution/sandbox

## Code Interaction Policy

In early versions:

- No full code editor
- No code compilation
- No execution of user-submitted code

Instead, code-related challenges must use:
- fill-in-the-blank templates
- multiple choice code snippets
- block-based logic ordering
- guided pseudo-code construction

All code evaluation must be deterministic or pattern-based.

---

## 2. System Architecture Diagram (Text-Based)

```text
[User]
  |
  v
[Frontend (Next.js, TypeScript)]
  |
  | HTTPS (authenticated requests)
  v
[Backend API (FastAPI)]
  |------------------------------|
  | Domain Modules               |
  | auth, users, content         |
  | attempts, evaluation         |
  | scoring, progress            |
  | leaderboard, ai_evaluation   |
  |------------------------------|
   |             |            |
   |             |            +--> [AI Evaluation Module]
   |             |                  (bounded prompts, schema validation, fallback)
   |             |
   |             +--> [Evaluation Engine]
   |                    (question-type evaluators)
   |
   +--> [Scoring Engine] --> [Progress Engine] --> [Leaderboard updates]
   |
   v
[PostgreSQL Database]
```

---

## 3. Module Breakdown (Backend)

### `auth`

Responsibilities:

- Authentication, session/token lifecycle, authorization checks
- Access control enforcement for protected operations

Boundaries:

- Does not own user profile content
- Exposes identity and permission checks to other modules

### `users`

Responsibilities:

- User profile and user metadata management
- User-facing account data not related to auth credentials

Boundaries:

- Depends on auth identity context
- Does not implement evaluation, scoring, or content logic

### `content`

Responsibilities:

- Tracks, levels, challenges, and questions
- Content retrieval and content schema validation

Boundaries:

- Read/write of learning content structures only
- No scoring or progress side effects inside content operations

### `attempts`

Responsibilities:

- Submission lifecycle for user answers
- Attempt creation, state transitions, and attempt history

Boundaries:

- Orchestrates evaluation calls but does not grade directly
- Stores attempt records and links to evaluation outcomes

### `evaluation`

Responsibilities:

- Deterministic grading for supported question types
- Structured evaluation outputs (result, rationale, error state)

Boundaries:

- Focused on correctness assessment only
- No direct progress or leaderboard updates

### `scoring`

Responsibilities:

- Apply scoring policies, weights, penalties, normalization
- Convert evaluation outputs into awarded score changes

Boundaries:

- Uses evaluation results as input
- Does not manage content or identity concerns

### `progress`

Responsibilities:

- Track learner completion status and progression decisions
- Update level/challenge completion in an idempotent way

Boundaries:

- Consumes scoring outcomes and attempt state
- Does not evaluate answers itself

### `leaderboard`

Responsibilities:

- Aggregate and expose ranking data
- Provide reproducible ranking calculations

Boundaries:

- Reads score/progress outcomes
- Does not modify evaluation logic

### `ai_evaluation`

Responsibilities:

- Natural-language answer assessment orchestration
- Prompt constraints, output schema validation, fallback handling

Boundaries:

- Used only when deterministic evaluators are insufficient
- Treats model output as untrusted input until validated

---

## 4. Data Flow

### User Login Flow

1. User submits credentials from frontend.
2. API `auth` validates credentials and authorization context.
3. API returns session/token response.
4. Frontend stores auth state and uses it for subsequent protected requests.

### Loading Content Flow

1. Frontend requests tracks, levels, challenges, and questions.
2. API `content` validates access and query parameters.
3. Content module retrieves structured data from database.
4. API returns normalized content payload for rendering.

### Lab Progression Flow

1. Startup seeding assigns labs to paths and derives linear prerequisites inside each path using `order_index`.
2. When the user calls lab start, the lab-progress service validates the lab prerequisite before creating a new progress row.
3. If the prerequisite lab is not completed by the same user, start is rejected with `403`.
4. Reopen keeps the same progress row and only changes status timestamps (no cascade cleanup of later labs in this phase).
5. Path-level progress summaries aggregate per-path lab totals and statuses (`completed`, `in_progress`, `locked`) based on current prerequisite completion state for the same user.

### Path Module Catalog Read Flow

1. Startup seeding creates `PathModule` rows and assigns seeded labs to modules when available.
2. `GET /api/v1/paths/{path_id}/modules` returns modules belonging to the path, ordered by `order_index`.
3. `GET /api/v1/modules/{module_id}/labs` returns labs in the module, ordered by `order_index`.
4. A lightweight integrity check validates module-aware prerequisites: when a lab has `module_id` and `prerequisite_lab_id`, the prerequisite lab must belong to the same path.

### Challenge Attempt Flow

1. User submits answer for a challenge question.
2. API `attempts` creates an attempt record and validates payload shape.
3. Attempts module routes answer to evaluation pipeline.
4. Evaluation result is attached to the attempt record.

### Evaluation Flow

1. `evaluation` selects evaluator by question type.
2. Deterministic evaluator runs first when available.
3. For natural-language or complex responses, `ai_evaluation` may be invoked.
4. Final validated evaluation result is returned to attempts and scoring.

### Scoring and Progress Update Flow

1. `scoring` computes awarded points from evaluation output.
2. `progress` updates completion and progression state idempotently.
3. `leaderboard` updates or recomputes ranking aggregates.
4. API returns user-facing feedback: score delta, progress status, and rationale.

---

## 5. Evaluation Architecture

Evaluation is question-type driven through a stable evaluator interface.

How different question types are evaluated:

- Each question type maps to a dedicated evaluator strategy.
- Evaluators return structured outputs with pass/fail or graded result, rationale, and error details.
- New question types are added by registering new evaluators, not by expanding a single conditional block.

Deterministic vs AI evaluation:

- Deterministic evaluation is the default and preferred path for reliability, reproducibility, and testability.
- AI-assisted evaluation is used only when deterministic checks are insufficient (for example, nuanced natural-language answers).
- AI outputs are always validated against strict schemas and guarded with fallback behavior.

### Supported Question Types (Initial)

The system must support the following initial question types:

- `single_choice`
- `multiple_choice`
- `fill_blank_code`
- `order_steps`
- `component_selection`
- `connection_graph` (abstract representation, not full simulation)
- `natural_language_ai`

Each type must have:
- a defined input format
- a defined evaluation strategy
- a deterministic or AI-assisted evaluation mode

### Evaluator Output Contract

All evaluators must return a structured response:

- `is_correct` (boolean or graded)
- `score_awarded` (awarded points)
- `max_score`
- `feedback` (user-facing explanation)
- `details` (optional debug or structured info)

Naming rule for question metadata:

- Internal storage and domain model use `metadata_json`.
- API responses use `metadata`.

This contract must remain stable across all evaluators.

---

## 6. Scalability and Extensibility Principles

### Adding New Question Types

- Introduce a new evaluator implementation behind the shared evaluator contract.
- Keep question rendering and input handling separate from scoring and progress logic.
- Add tests for normal, edge, and invalid input paths before rollout.

### Adding New Tracks and Levels

- Extend content entities and relationships in the `content` domain.
- Keep progression logic in `progress` and not embedded in content retrieval.
- Preserve backward-compatible content schema where possible.

### Evolving Scoring Rules

- Centralize scoring policy changes in `scoring`.
- Version or configure scoring policy when changes can affect historical comparability.
- Ensure leaderboard aggregation remains reproducible under new policies.

---

## 7. Implementation Phases

### Phase 1 (V1 Minimal)

- Authentication baseline and basic user profile flow
- Core content hierarchy read flow (tracks, levels, challenges, questions)
- Attempt submission pipeline for one deterministic question type
- Basic scoring and progress updates
- Initial leaderboard aggregation
- Foundational tests and contracts

### Phase 2

- Additional question types with evaluator extensions
- Expanded scoring policies and richer feedback
- Improved progress policies (idempotency and anti-inflation controls)
- Initial AI-assisted evaluation for selected natural-language questions
- Observability, validation hardening, and rate-limiting enhancements

### Phase 3 (Future)

- Broader AI-assisted evaluation coverage with stronger safeguards
- Advanced analytics and learning insights
- Performance optimization and scaling improvements
- More sophisticated leaderboard and progression features
- Continuous architecture refinement with synchronized documentation updates
