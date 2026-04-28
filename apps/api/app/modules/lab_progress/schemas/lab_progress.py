from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict


LabProgressStatus = Literal["not_started", "in_progress", "completed"]


class LabProgressResponse(BaseModel):
    id: str
    user_id: str
    lab_id: str
    status: LabProgressStatus
    started_at: datetime | None
    completed_at: datetime | None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class PathProgressSummaryResponse(BaseModel):
    path_id: str
    path_name: str
    path_description: str
    total_labs: int
    completed_labs: int
    in_progress_labs: int
    locked_labs: int
    completion_percentage: int
