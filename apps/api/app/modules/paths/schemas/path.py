from pydantic import BaseModel, ConfigDict


class PathResponse(BaseModel):
    id: str
    name: str
    description: str
    order: int

    model_config = ConfigDict(from_attributes=True)
