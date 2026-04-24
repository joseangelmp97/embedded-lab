# Embedded Lab

Interactive learning platform for embedded systems where users solve guided challenges on electronics, microcontrollers, components, wiring, logic, and core embedded concepts.

## Product Vision

Build a practical, structured environment where learners progress from fundamentals to applied embedded problem-solving through clear feedback, measurable progress, and reliable evaluation.

## Main Features

- User authentication and authorization
- User progress tracking across tracks and levels
- Structured learning content: tracks, levels, challenges, and questions
- Multiple question types with type-specific evaluation
- Scoring system with transparent rules
- Leaderboard and rankings
- Deterministic evaluation engine
- AI-assisted evaluation for natural language answers with safeguards
- Early-stage constraint: no full code editor and no arbitrary code execution

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
- Pytest (backend)
- Vitest or Playwright (frontend)

## Expected Repository Structure

```text
apps/
  web/
  api/
docs/
packages/
  shared/
```

## Development Principles

- English only for code, comments, variable names, and docs
- Build incrementally in small, testable slices
- Keep modules separated with clear boundaries
- Break large features into small tasks before implementation
- Update architecture and related documentation when architecture changes
- Never hardcode secrets; use environment or secret management
- Never execute arbitrary user code
- Prefer simple, maintainable solutions over unnecessary complexity

## Current Status

Planning phase.

## Next Steps

1. Define the first vertical slice (authentication + basic user profile).
2. Draft initial data model entities for users, content hierarchy, attempts, and scoring.
3. Define initial API contracts for auth, content read endpoints, and submission flow.
4. Implement deterministic evaluation for one question type end-to-end.
5. Add baseline tests and quality checks (lint, type checks, unit tests).
