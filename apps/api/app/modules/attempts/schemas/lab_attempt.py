from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict


class LabAttemptSessionResponse(BaseModel):
    id: str
    lab_id: str
    attempt_number: int
    lab_attempt_status: str
    total_score_awarded: int
    max_score: int
    required_exercises_correct: int
    required_exercises_total: int
    hints_used_count: int
    content_version: int
    started_at: datetime
    completed_at: datetime | None
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ExerciseSubmitRequest(BaseModel):
    exercise_id: str
    response_payload_json: dict[str, Any]


class AttemptSessionSummaryResponse(BaseModel):
    id: str
    lab_id: str
    attempt_number: int
    lab_attempt_status: str
    total_score_awarded: int
    max_score: int
    required_exercises_correct: int
    required_exercises_total: int
    hints_used_count: int
    content_version: int
    started_at: datetime
    completed_at: datetime | None
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ExerciseSubmitResponse(BaseModel):
    exercise_attempt_id: str
    is_correct: bool
    score_awarded: int
    max_score: int
    feedback: str
    session: AttemptSessionSummaryResponse
