from datetime import datetime

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
