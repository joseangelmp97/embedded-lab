from datetime import datetime

from pydantic import BaseModel, ConfigDict


class PathModuleResponse(BaseModel):
    id: str
    path_id: str
    slug: str
    title: str
    description: str
    order_index: int
    is_published: bool
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
