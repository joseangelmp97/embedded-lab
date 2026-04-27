# API_CONTRACT.md

## Overview

This document defines the API contract for Embedded Lab.
It describes endpoint behavior, request/response shapes, and error conventions for the planning and initial implementation phases.

Base path (versioned):

- `/api/v1`

Content type:

- Requests: `application/json`
- Responses: `application/json`

---

## 1) General API Design Principles

### REST Style

- Use resource-oriented, predictable paths.
- Use HTTP methods consistently:
  - `GET` read
  - `POST` create/action
  - `PATCH` partial update (reserved for future use)
- Keep payloads explicit and schema-driven.

### Authentication Approach

- Authenticated endpoints require a bearer token:
  - `Authorization: Bearer <token>`
- Token is issued on login and invalidated on logout.
- Protected endpoints return `401` when token is missing/invalid.

### Response Format

- Success responses use:
  - `success: true`
  - `data: {...}` or `data: [...]`
  - optional `meta` for pagination or context
- Error responses use a standard `error` object (defined in section 9).

### Error Handling

- Use appropriate HTTP status codes (`400`, `401`, `403`, `404`, `409`, `422`, `429`, `500`).
- Return machine-readable `error.code` and human-readable `error.message`.
- Include `request_id` for traceability.

### Naming Rules

- Internal storage and domain models use `metadata_json`.
- API responses use `metadata`.
- Evaluated per-question score field uses `score_awarded`.

---

## 2) Canonical Enums

These enums are canonical and must match `DATA_MODEL.md`.

- `difficulty`: `beginner`, `intermediate`, `advanced`
- `attempt_status`: `started`, `submitted`, `evaluating`, `evaluated`, `failed`
- `progress_status`: `locked`, `unlocked`, `in_progress`, `completed`
- `evaluation_mode`: `deterministic`, `ai_assisted`, `hybrid`
- `question_type`: `single_choice`, `multiple_choice`, `fill_blank_code`, `order_steps`, `component_selection`, `connection_graph`, `natural_language_ai`
- `leaderboard_scope`: `global`, `track`, `level`, `time_window`
- `user_role`: `learner`, `admin`
- `user_status`: `active`, `suspended`

---

## 3) Auth Endpoints

### `POST /api/v1/auth/register`

Creates a new learner account.

Request:

```json
{
  "email": "student@example.com",
  "password": "StrongPassword123!",
  "display_name": "Embedded Learner"
}
```

Response `201`:

```json
{
  "success": true,
  "data": {
    "user": {
      "id": "usr_123",
      "email": "student@example.com",
      "role": "learner",
      "created_at": "2026-04-24T10:00:00Z"
    }
  }
}
```

### `POST /api/v1/auth/login`

Authenticates user and returns access token.

Request:

```json
{
  "email": "student@example.com",
  "password": "StrongPassword123!"
}
```

Response `200`:

```json
{
  "success": true,
  "data": {
    "access_token": "jwt_or_opaque_token",
    "token_type": "Bearer",
    "expires_in": 3600,
    "user": {
      "id": "usr_123",
      "email": "student@example.com",
      "display_name": "Embedded Learner",
      "role": "learner"
    }
  }
}
```

### `POST /api/v1/auth/logout`

Invalidates current token/session.

Request: no body required.

Response `200`:

```json
{
  "success": true,
  "data": {
    "logged_out": true
  }
}
```

### `GET /api/v1/auth/me`

Returns current authenticated user.

Response `200`:

```json
{
  "success": true,
  "data": {
    "id": "usr_123",
    "email": "student@example.com",
    "display_name": "Embedded Learner",
    "role": "learner",
    "status": "active"
  }
}
```

---

## 4) Content Endpoints

### `GET /api/v1/tracks`

Returns published tracks.

Query params (optional):

- `include_progress` (`true|false`, default `false`)

Response `200`:

```json
{
  "success": true,
  "data": [
    {
      "id": "trk_basics",
      "slug": "embedded-basics",
      "title": "Embedded Basics",
      "description": "Foundational concepts",
      "order_index": 1,
      "version": 1
    }
  ]
}
```

### `GET /api/v1/tracks/{track_id}/levels`

Returns levels for a specific track.

Response `200`:

```json
{
  "success": true,
  "data": [
    {
      "id": "lvl_1",
      "track_id": "trk_basics",
      "slug": "digital-logic-intro",
      "title": "Digital Logic Intro",
      "order_index": 1,
      "difficulty": "beginner"
    }
  ]
}
```

### `GET /api/v1/levels/{level_id}/challenges`

Returns challenges for a specific level.

Response `200`:

```json
{
  "success": true,
  "data": [
    {
      "id": "chl_101",
      "level_id": "lvl_1",
      "slug": "gpio-input-output",
      "title": "GPIO Input and Output",
      "order_index": 1,
      "difficulty": "beginner",
      "max_score": 100
    }
  ]
}
```

### `GET /api/v1/challenges/{challenge_id}`

Returns challenge details including questions.

Response `200`:

```json
{
  "success": true,
  "data": {
    "id": "chl_101",
    "title": "GPIO Input and Output",
    "description": "Understand GPIO direction and states",
    "max_score": 100,
    "questions": [
      {
        "id": "q_1",
        "question_type": "single_choice",
        "prompt": "Which pin mode reads a button state?",
        "order_index": 1,
        "max_score": 20,
        "metadata": {
          "options": [
            { "id": "a", "label": "OUTPUT" },
            { "id": "b", "label": "INPUT" }
          ]
        }
      }
    ]
  }
}
```

---

## 5) Attempt Endpoints

All response_payload objects must be validated against the question_type schema defined in CONTENT_SCHEMA.md.
Invalid payloads must be rejected with VALIDATION_ERROR.

Submission and evaluation are decoupled:

- Submitting responses does not guarantee immediate evaluation
- Finalization triggers evaluation, which may be synchronous or asynchronous
- Clients must poll GET /attempts/{attempt_id} to retrieve final results

Idempotency requirements:

- `POST /api/v1/attempts/{attempt_id}/responses` must support `Idempotency-Key` header.
- `POST /api/v1/attempts/{attempt_id}/finalize` must support `Idempotency-Key` header.
- Repeated requests with the same method, path, user, and `Idempotency-Key` must return the original result and must not duplicate score or progress updates.
- If same key is reused with a different payload, return `409 CONFLICT`.

### `POST /api/v1/challenges/{challenge_id}/attempts`

Starts a new attempt for the authenticated user.

Request (optional client metadata):

```json
{
  "client_context": {
    "source": "web",
    "content_version": 1
  }
}
```

Response `201`:

```json
{
  "success": true,
  "data": {
    "attempt_id": "att_9001",
    "challenge_id": "chl_101",
    "status": "started",
    "attempt_number": 1,
    "started_at": "2026-04-24T10:20:00Z",
    "content_version": 1
  }
}
```

### `POST /api/v1/attempts/{attempt_id}/responses`

Submits answer(s) to an attempt. Supports per-question and batch submission.

Required header:

- `Idempotency-Key: <unique_key>`

Request (single response):

```json
{
  "responses": [
    {
      "question_id": "q_1",
      "response_payload": {
        "selected_option_id": "b"
      },
      "time_spent_seconds": 18
    }
  ]
}
```

Response `200`:

```json
{
  "success": true,
  "data": {
    "attempt_id": "att_9001",
    "accepted": 1,
    "rejected": 0,
    "status": "submitted"
  }
}
```

### `POST /api/v1/attempts/{attempt_id}/finalize`

Finalizes attempt, triggers evaluation/scoring/progress pipeline.

Required header:

- `Idempotency-Key: <unique_key>`

Request:

```json
{
  "finalize": true
}
```

Response `202` (evaluation queued or in progress):

```json
{
  "success": true,
  "data": {
    "attempt_id": "att_9001",
    "status": "evaluating"
  }
}
```

Response `200` (evaluation completed quickly):

```json
{
  "success": true,
  "data": {
    "attempt_id": "att_9001",
    "status": "evaluated",
    "total_score_awarded": 80,
    "max_score": 100
  }
}
```

### `GET /api/v1/attempts/{attempt_id}`

Returns full attempt result and per-question feedback.

Response `200`:

```json
{
  "success": true,
  "data": {
    "attempt_id": "att_9001",
    "challenge_id": "chl_101",
    "status": "evaluated",
    "total_score_awarded": 80,
    "max_score": 100,
    "question_results": [
      {
        "question_id": "q_1",
        "is_correct": true,
        "score_awarded": 20,
        "max_score": 20,
        "evaluation_mode_used": "deterministic",
        "feedback": "Correct. INPUT mode reads button state."
      }
    ],
    "scoring": {
      "points_delta": 80,
      "policy": "best_attempt_only"
    },
    "progress": {
      "challenge_status": "completed",
      "level_completion_percentage": 40
    }
  }
}
```

---

## 6) Progress Endpoints

### `GET /api/v1/progress/me`

Returns authenticated user overall progress summary.

Response `200`:

```json
{
  "success": true,
  "data": {
    "user_id": "usr_123",
    "total_completed_challenges": 12,
    "total_score": 950,
    "tracks": [
      {
        "track_id": "trk_basics",
        "completion_percentage": 55
      }
    ]
  }
}
```

### `GET /api/v1/progress/me/tracks/{track_id}`

Returns user progress scoped to one track (and nested level summaries).

Response `200`:

```json
{
  "success": true,
  "data": {
    "track_id": "trk_basics",
    "completion_percentage": 55,
    "levels": [
      {
        "level_id": "lvl_1",
        "completion_percentage": 80,
        "completed_challenges": 4,
        "total_challenges": 5
      }
    ]
  }
}
```

### `GET /api/v1/progress/me/levels/{level_id}`

Returns user progress scoped to one level.

Response `200`:

```json
{
  "success": true,
  "data": {
    "level_id": "lvl_1",
    "completion_percentage": 80,
    "challenges": [
      {
        "challenge_id": "chl_101",
        "status": "completed",
        "best_score": 80
      }
    ]
  }
}
```

---

## 7) Leaderboard Endpoints

### `GET /api/v1/leaderboard/global`

Returns global leaderboard.

Query params (optional):

- `limit` (default `50`, max `200`)
- `offset` (default `0`)

Response `200`:

```json
{
  "success": true,
  "data": [
    {
      "rank": 1,
      "user_id": "usr_777",
      "display_name": "Ada",
      "score_value": 3200
    },
    {
      "rank": 2,
      "user_id": "usr_123",
      "display_name": "Embedded Learner",
      "score_value": 3000
    }
  ],
  "meta": {
    "limit": 50,
    "offset": 0,
    "scope": "global"
  }
}
```

### `GET /api/v1/tracks/{track_id}/leaderboard`

Returns leaderboard scoped to a track.

Response `200`:

```json
{
  "success": true,
  "data": [
    {
      "rank": 1,
      "user_id": "usr_123",
      "display_name": "Embedded Learner",
      "score_value": 1200
    }
  ],
  "meta": {
    "scope": "track",
    "track_id": "trk_basics"
  }
}
```

---

## 8) Request/Response Examples (Key Endpoints)

### Example: Login

Request `POST /api/v1/auth/login`

```json
{
  "email": "student@example.com",
  "password": "StrongPassword123!"
}
```

Response `200`

```json
{
  "success": true,
  "data": {
    "access_token": "jwt_or_opaque_token",
    "token_type": "Bearer",
    "expires_in": 3600,
    "user": {
      "id": "usr_123",
      "email": "student@example.com",
      "display_name": "Embedded Learner",
      "role": "learner"
    }
  }
}
```

### Example: Start Attempt

Request `POST /api/v1/challenges/chl_101/attempts`

```json
{
  "client_context": {
    "source": "web",
    "content_version": 1
  }
}
```

Response `201`

```json
{
  "success": true,
  "data": {
    "attempt_id": "att_9001",
    "status": "started",
    "attempt_number": 1
  }
}
```

### Example: Submit and Finalize

Request `POST /api/v1/attempts/att_9001/responses`

Headers:

```text
Idempotency-Key: 9f7a5f6a-5d2f-41ac-b9d2-4132dcf93624
```

```json
{
  "responses": [
    {
      "question_id": "q_1",
      "response_payload": {
        "selected_option_id": "b"
      }
    },
    {
      "question_id": "q_2",
      "response_payload": {
        "ordered_ids": ["step_2", "step_1", "step_3"]
      }
    }
  ]
}
```

Response `200`

```json
{
  "success": true,
  "data": {
    "attempt_id": "att_9001",
    "accepted": 2,
    "status": "submitted"
  }
}
```

Request `POST /api/v1/attempts/att_9001/finalize`

Headers:

```text
Idempotency-Key: 7bd9f0de-89bb-4f99-a8b7-fbfcb7ab9f75
```

```json
{
  "finalize": true
}
```

Response `202`

```json
{
  "success": true,
  "data": {
    "attempt_id": "att_9001",
    "status": "evaluating"
  }
}
```

---

## 9) Error Format

All non-2xx responses follow this structure:

```json
{
  "success": false,
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Invalid request payload.",
    "details": [
      {
        "field": "responses[0].question_id",
        "issue": "Question does not belong to challenge"
      }
    ]
  },
  "request_id": "req_abc123"
}
```

Standard error codes:

- `VALIDATION_ERROR` (`400` or `422`)
- `UNAUTHORIZED` (`401`)
- `FORBIDDEN` (`403`)
- `NOT_FOUND` (`404`)
- `CONFLICT` (`409`)
- `RATE_LIMITED` (`429`)
- `INTERNAL_ERROR` (`500`)

Notes:

- `details` is optional and should be included for validation and conflict scenarios.
- `request_id` is required in all error responses.
- Error messages must avoid leaking sensitive internals.

---

## 10) Paths, Labs and Lab Progress Endpoints (Implemented)

These endpoints are protected and require `Authorization: Bearer <token>`.

### `GET /api/v1/paths`

Returns all learning paths ordered by `order`.

Response `200`:

```json
[
  {
    "id": "247f7a42-17d9-4f08-8fc3-7284fdbbe93c",
    "name": "Embedded Fundamentals",
    "description": "Core embedded concepts: digital I/O, timing basics, and practical hardware interactions.",
    "order": 1
  }
]
```

### `GET /api/v1/paths/{path_id}/labs`

Returns labs associated with a specific path ordered by `order_index`.

- `404` when the path does not exist (`detail: "Path not found"`).

### `GET /api/v1/labs`

Returns all available labs ordered by `order_index`.

Response `200`:

```json
[
  {
    "id": "gpio-led-basics",
    "title": "GPIO and LED basics",
    "description": "Learn GPIO output fundamentals by controlling an LED with a microcontroller pin.",
    "difficulty": "beginner",
    "estimated_minutes": 25,
    "status": "published",
    "order_index": 1,
    "created_at": "2026-04-27T10:00:00Z",
    "updated_at": "2026-04-27T10:00:00Z"
  }
]
```

### `GET /api/v1/labs/{lab_id}`

Returns one lab by id.

- `404` when the lab does not exist (`detail: "Lab not found"`).

### `GET /api/v1/me/lab-progress`

Returns lab progress rows for the authenticated user.

Response `200`:

```json
[
  {
    "id": "8ed6d0eb-c53d-4b1f-9b8f-b0e8f916c33a",
    "user_id": "96b2b1f8-499f-4cef-a76a-44295f38d6be",
    "lab_id": "gpio-led-basics",
    "status": "in_progress",
    "started_at": "2026-04-27T10:05:00Z",
    "completed_at": null,
    "created_at": "2026-04-27T10:05:00Z",
    "updated_at": "2026-04-27T10:05:00Z"
  }
]
```

### `POST /api/v1/labs/{lab_id}/start`

Starts lab progress for the authenticated user.

- Idempotent: if progress already exists for `(user_id, lab_id)`, returns existing row.
- `404` when the lab does not exist.

### `POST /api/v1/labs/{lab_id}/complete`

Marks lab progress as completed.

- Creates progress if missing.
- Sets `status=completed`, `completed_at=now`, and ensures `started_at` is populated.
- `404` when the lab does not exist.

### `POST /api/v1/labs/{lab_id}/reopen`

Reopens lab progress.

- If status is `completed`, sets `status=in_progress` and clears `completed_at`.
- If missing, creates progress in `in_progress` state.
- `404` when the lab does not exist.
