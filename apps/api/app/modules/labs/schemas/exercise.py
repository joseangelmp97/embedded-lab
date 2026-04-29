from typing import Any, Literal

from pydantic import BaseModel


ExerciseType = Literal["multiple_choice", "fill_blank", "short_text"]


class ExerciseListItemResponse(BaseModel):
    id: str
    exercise_type: ExerciseType
    prompt: str
    order_index: int
    max_score: int
    metadata_json: dict[str, Any] | list[Any] | None
    hint_policy_json: dict[str, Any] | list[Any] | None
    explanation: str | None
