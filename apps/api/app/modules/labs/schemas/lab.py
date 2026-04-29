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
    path_id: str | None = None
    module_id: str | None = None
    prerequisite_lab_id: str | None
    slug: str | None = None
    learning_objectives_json: str | None = None
    tags_json: str | None = None
    hardware_requirements_json: str | None = None
    content_version: int
    is_optional: bool
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
