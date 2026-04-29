from datetime import datetime
from uuid import uuid4

from sqlalchemy import DateTime, ForeignKey, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.shared.db.base import Base


class LabAttemptSession(Base):
    __tablename__ = "lab_attempt_sessions"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"), nullable=False, index=True)
    lab_id: Mapped[str] = mapped_column(String(100), ForeignKey("labs.id"), nullable=False, index=True)
    attempt_number: Mapped[int] = mapped_column(Integer, nullable=False)
    lab_attempt_status: Mapped[str] = mapped_column(String(32), nullable=False)
    total_score_awarded: Mapped[int] = mapped_column(Integer, nullable=False, default=0, server_default="0")
    max_score: Mapped[int] = mapped_column(Integer, nullable=False)
    required_exercises_correct: Mapped[int] = mapped_column(Integer, nullable=False, default=0, server_default="0")
    required_exercises_total: Mapped[int] = mapped_column(Integer, nullable=False, default=0, server_default="0")
    hints_used_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0, server_default="0")
    content_version: Mapped[int] = mapped_column(Integer, nullable=False, default=1, server_default="1")
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )
