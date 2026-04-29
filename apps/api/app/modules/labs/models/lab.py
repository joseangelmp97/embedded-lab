from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.shared.db.base import Base


class Lab(Base):
    __tablename__ = "labs"

    id: Mapped[str] = mapped_column(String(100), primary_key=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str] = mapped_column(String(1000), nullable=False)
    difficulty: Mapped[str] = mapped_column(String(32), nullable=False)
    estimated_minutes: Mapped[int] = mapped_column(Integer, nullable=False)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="published")
    order_index: Mapped[int] = mapped_column(Integer, nullable=False)
    path_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("paths.id"), nullable=True, index=True)
    module_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("path_modules.id"), nullable=True, index=True)
    prerequisite_lab_id: Mapped[str | None] = mapped_column(
        String(100),
        ForeignKey("labs.id"),
        nullable=True,
        index=True,
    )
    slug: Mapped[str | None] = mapped_column(String(255), nullable=True)
    learning_objectives_json: Mapped[str | None] = mapped_column(String, nullable=True)
    tags_json: Mapped[str | None] = mapped_column(String, nullable=True)
    hardware_requirements_json: Mapped[str | None] = mapped_column(String, nullable=True)
    content_version: Mapped[int] = mapped_column(Integer, nullable=False, default=1, server_default="1")
    is_optional: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False, server_default="0")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )
