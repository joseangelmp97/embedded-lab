from datetime import datetime, timezone

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.modules.lab_progress.models.lab_progress import LabProgress
from app.modules.labs.services.lab_service import get_lab_by_id
from app.modules.users.models.user import User


def list_user_lab_progress(db: Session, user_id: str) -> list[LabProgress]:
    return list(
        db.scalars(
            select(LabProgress)
            .where(LabProgress.user_id == user_id)
            .order_by(LabProgress.updated_at.desc(), LabProgress.created_at.desc()),
        ),
    )


def start_lab_progress(db: Session, user: User, lab_id: str) -> LabProgress:
    lab = get_lab_by_id(db=db, lab_id=lab_id)

    progress = db.scalar(
        select(LabProgress).where(
            LabProgress.user_id == user.id,
            LabProgress.lab_id == lab_id,
        ),
    )

    if progress is not None:
        return progress

    if lab.prerequisite_lab_id is not None:
        prerequisite_progress = db.scalar(
            select(LabProgress).where(
                LabProgress.user_id == user.id,
                LabProgress.lab_id == lab.prerequisite_lab_id,
                LabProgress.status == "completed",
            ),
        )
        if prerequisite_progress is None:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=(
                    f"Lab is locked. Complete prerequisite lab '{lab.prerequisite_lab_id}' before starting this one."
                ),
            )

    now = datetime.now(tz=timezone.utc)
    progress = LabProgress(
        user_id=user.id,
        lab_id=lab_id,
        status="in_progress",
        started_at=now,
        completed_at=None,
    )
    db.add(progress)
    db.commit()
    db.refresh(progress)
    return progress


def complete_lab_progress(db: Session, user: User, lab_id: str) -> LabProgress:
    get_lab_by_id(db=db, lab_id=lab_id)

    now = datetime.now(tz=timezone.utc)
    progress = db.scalar(
        select(LabProgress).where(
            LabProgress.user_id == user.id,
            LabProgress.lab_id == lab_id,
        ),
    )

    if progress is None:
        progress = LabProgress(
            user_id=user.id,
            lab_id=lab_id,
            status="completed",
            started_at=now,
            completed_at=now,
        )
        db.add(progress)
    elif progress.status != "completed":
        progress.status = "completed"
        progress.started_at = progress.started_at or now
        progress.completed_at = now

    db.commit()
    db.refresh(progress)
    return progress


def reopen_lab_progress(db: Session, user: User, lab_id: str) -> LabProgress:
    get_lab_by_id(db=db, lab_id=lab_id)

    now = datetime.now(tz=timezone.utc)
    progress = db.scalar(
        select(LabProgress).where(
            LabProgress.user_id == user.id,
            LabProgress.lab_id == lab_id,
        ),
    )

    if progress is None:
        progress = LabProgress(
            user_id=user.id,
            lab_id=lab_id,
            status="in_progress",
            started_at=now,
            completed_at=None,
        )
        db.add(progress)
    elif progress.status == "completed":
        progress.status = "in_progress"
        progress.started_at = progress.started_at or now
        progress.completed_at = None

    db.commit()
    db.refresh(progress)
    return progress
