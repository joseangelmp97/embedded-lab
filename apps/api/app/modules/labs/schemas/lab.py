from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict


LabDifficulty = Literal["beginner", "intermediate", "advanced"]
LabStatus = Literal["draft", "published", "archived"]


class LabResponse(BaseModel):
    id: str
    title: str
    description: str
    difficulty: LabDifficulty
    estimated_minutes: int
    status: LabStatus
    order_index: int
    prerequisite_lab_id: str | None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
