from datetime import datetime
from uuid import uuid4

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.shared.db.base import Base


class ExerciseAttempt(Base):
    __tablename__ = "exercise_attempts"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    lab_attempt_session_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("lab_attempt_sessions.id"),
        nullable=False,
        index=True,
    )
    exercise_id: Mapped[str] = mapped_column(String(36), ForeignKey("exercises.id"), nullable=False, index=True)
    response_payload_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_correct: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    score_awarded: Mapped[int] = mapped_column(Integer, nullable=False, default=0, server_default="0")
    max_score: Mapped[int] = mapped_column(Integer, nullable=False)
    feedback: Mapped[str | None] = mapped_column(Text, nullable=True)
    evaluation_details_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    hint_shown: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False, server_default="0")
    hint_index_shown: Mapped[int | None] = mapped_column(Integer, nullable=True)
    attempt_sequence: Mapped[int] = mapped_column(Integer, nullable=False)
    evaluated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
