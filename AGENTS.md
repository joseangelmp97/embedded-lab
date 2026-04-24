# AGENTS.md

## Purpose

This document defines how coding agents must work in this repository.

Project: interactive learning platform for embedded systems where users solve challenges about electronics, microcontrollers, components, wiring, logic, and embedded concepts.

Agents must prioritize correctness, security, maintainability, and incremental delivery.

---

## Non-Negotiable Rules

1. **English only** in all code, comments, variable names, commit messages, and documentation.
2. **Build incrementally**: deliver small, testable steps.
3. **Keep modules separated**: avoid tight coupling and cross-module leakage.
4. **Break large features into small tasks** before implementation.
5. **Do not change architecture without updating documentation**.
6. **Do not hardcode secrets** (API keys, tokens, credentials, private URLs).
7. **Do not execute arbitrary user code**.
8. **Prefer simple, maintainable solutions** over clever or complex designs.

If a task conflicts with any rule above, stop and propose a compliant approach.

---

## Product Scope (Current)

The platform includes:

- User authentication
- User progress tracking
- Tracks, levels, challenges, questions
- Multiple question types
- Scoring system
- Leaderboard
- Evaluation engine
- AI-assisted evaluation for natural language answers

### Explicit Early-Stage Constraint

- No full code editor.
- No arbitrary code execution/sandbox in first versions.

---

## Engineering Principles

- Use clear domain boundaries.
- Design for predictable behavior and easy debugging.
- Favor explicit contracts over implicit behavior.
- Keep functions focused and modules cohesive.
- Minimize hidden side effects.
- Make failures observable and actionable.
- Add only the minimum complexity required for current scope.

---

## Recommended Module Boundaries

Organize code by domain capability, not by random technical layer.

- `auth` - identity, sessions, authorization checks
- `users` - profile and user metadata
- `content` - tracks, levels, challenges, questions
- `attempts` - submissions, attempts, answer lifecycle
- `evaluation` - deterministic grading and rule-based scoring
- `ai_evaluation` - natural-language assessment orchestration and safeguards
- `progress` - completion state and progression logic
- `leaderboard` - rankings and score aggregation
- `scoring` - score policies, weights, penalties, normalization
- `shared` - cross-domain utilities, errors, config, logging

Rules for boundaries:

- Cross-domain access should happen through clear interfaces/services.
- Avoid direct database access across domains where possible.
- No circular dependencies between modules.
- Shared module must not become a dumping ground.

---

## Security and Safety Requirements

- Never trust client input; validate and sanitize on the server.
- Enforce authorization on every protected operation.
- Store secrets in environment variables or secret managers only.
- Log security-relevant events (auth failures, suspicious evaluation input).
- Rate-limit sensitive endpoints where applicable.
- For AI-assisted evaluation:
  - Treat model output as untrusted until validated.
  - Use bounded prompts and strict output schemas.
  - Add fallback behavior when AI response is invalid or unavailable.
- Reject any requirement that implies arbitrary code execution.

---

## Data and Contract Discipline

When changing behavior that affects data or APIs:

1. Update `DATA_MODEL.md` for schema/entity changes.
2. Update `API_CONTRACT.md` for endpoint/request/response changes.
3. Update `CONTENT_SCHEMA.md` for challenge/question format changes.
4. Update `ARCHITECTURE.md` for boundary or flow changes.
5. Update `ROADMAP.md` if scope or sequence changes materially.

No architecture-affecting code change is complete without matching docs.

---

## Incremental Delivery Workflow

For every non-trivial feature, follow this order:

1. Define a small vertical slice.
2. Identify touched modules and contracts.
3. Implement minimum working behavior.
4. Add/adjust tests.
5. Update docs.
6. Run quality checks.
7. Ship in small reviewable change.

Avoid multi-domain rewrites in a single change set.

---

## Task Sizing Rules

A task is too large if it includes multiple domains, multiple new abstractions, and new contracts all at once.

Before coding large requests, split into subtasks such as:

- Domain model setup
- API contract + endpoint skeleton
- Core business logic
- Validation and error handling
- Tests
- Documentation updates

Prefer PRs that can be reviewed in under ~400 lines of meaningful diff (when possible).

---

## Feature Implementation Guidance

### Authentication

- Start with secure baseline (session/token strategy, password handling, auth middleware).
- Enforce role/ownership checks consistently.
- Keep auth concerns isolated from content/evaluation logic.

### Content (Tracks, Levels, Challenges, Questions)

- Model hierarchy explicitly.
- Version content schema when introducing breaking format changes.
- Validate question payloads strictly by type.

### Multiple Question Types

- Use a stable question interface with type-specific evaluators.
- Add new types via extension points, not condition sprawl.
- Keep rendering/input and scoring logic decoupled.

### Evaluation Engine

- Deterministic evaluators first.
- Make scoring rules explicit and testable.
- Return structured feedback (score, rationale, error state).

### AI-Assisted Evaluation

- Use AI only where deterministic checks are insufficient.
- Keep prompts constrained and auditable.
- Require post-processing/validation of model output.
- Include fallback path and confidence handling.

### Progress Tracking and Leaderboard

- Progress updates must be idempotent where possible.
- Leaderboard calculations must be reproducible and transparent.
- Prevent score inflation from repeated identical submissions if policy forbids it.

---

## Testing and Quality Gates

Minimum expectations for meaningful changes:

- Unit tests for core domain logic.
- Integration tests for key API flows.
- Validation/error-path tests for input handling.
- Tests for scoring/evaluation correctness.
- Regression tests for fixed bugs.

Also required:

- Lint/format/type checks pass.
- No dead code or unused abstractions introduced.
- Logging and error messages are actionable and safe.

---

## Simplicity Checklist (Apply Before Merging)

- Is there a simpler design with equal correctness?
- Are names clear and domain-meaningful?
- Are there avoidable abstractions?
- Is each module doing one coherent job?
- Can a new engineer understand this quickly?

If any answer is "no", refactor before finalizing.

---

## Prohibited Practices

- Hardcoded secrets.
- Hidden magic constants without explanation or centralization.
- Cross-module imports that bypass boundaries.
- Silent failure handling.
- Broad `catch` blocks that suppress root causes.
- Architecture changes without documentation updates.
- Introducing code-execution features in early versions.

---

## Definition of Done

A change is done only if all apply:

1. Scope is small and focused.
2. Code follows module boundaries and project rules.
3. Tests pass and cover critical logic.
4. Contracts/docs are updated where required.
5. Security constraints are preserved.
6. No arbitrary user code execution introduced.
7. Implementation is understandable and maintainable.

---

## Agent Collaboration Notes

When multiple agents collaborate:

- One owner agent defines task breakdown.
- Each agent works on a bounded module/task.
- Integration agent verifies contracts and documentation consistency.
- Resolve conflicts in favor of simplicity and documented architecture.

---

## Decision Policy for Ambiguity

When requirements are ambiguous:

1. Choose the safest option.
2. Choose the simplest maintainable option.
3. Preserve existing architecture and contracts.
4. Document assumptions in task notes or PR description.
5. Ask for clarification only when ambiguity materially changes behavior or security.

---

## Recommended Tech Stack

Frontend:
- Next.js
- TypeScript
- TailwindCSS

Backend:
- FastAPI
- Python
- PostgreSQL
- SQLAlchemy
- Alembic

Testing:
- Pytest for backend
- Vitest or Playwright for frontend when needed

---

## Expected Repository Structure

apps/
  web/
  api/
docs/
packages/
  shared/