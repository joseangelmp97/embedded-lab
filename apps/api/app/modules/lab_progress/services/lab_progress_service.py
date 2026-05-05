from datetime import datetime, timezone

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.modules.lab_progress.models.lab_progress import LabProgress
from app.modules.labs.models.exercise import Exercise
from app.modules.labs.services.lab_service import get_lab_by_id
from app.modules.labs.models.lab import Lab
from app.modules.paths.models.path import Path
from app.modules.users.models.user import User


COMPLETION_SOURCE_MANUAL = "manual"
COMPLETION_SOURCE_EVALUATION = "evaluation"


def _is_effectively_unlocked(
    *,
    lab: Lab,
    labs_by_id: dict[str, Lab],
    completed_lab_ids: set[str],
    unlock_cache: dict[str, bool],
) -> bool:
    cached = unlock_cache.get(lab.id)
    if cached is not None:
        return cached

    prerequisite_lab_id = lab.prerequisite_lab_id
    if prerequisite_lab_id is None:
        unlock_cache[lab.id] = True
        return True

    prerequisite_lab = labs_by_id.get(prerequisite_lab_id)
    if prerequisite_lab is None:
        unlock_cache[lab.id] = False
        return False

    is_unlocked = (
        prerequisite_lab_id in completed_lab_ids
        and _is_effectively_unlocked(
            lab=prerequisite_lab,
            labs_by_id=labs_by_id,
            completed_lab_ids=completed_lab_ids,
            unlock_cache=unlock_cache,
        )
    )
    unlock_cache[lab.id] = is_unlocked
    return is_unlocked


def list_user_lab_progress(db: Session, user_id: str) -> list[LabProgress]:
    return list(
        db.scalars(
            select(LabProgress)
            .where(LabProgress.user_id == user_id)
            .order_by(LabProgress.updated_at.desc(), LabProgress.created_at.desc()),
        ),
    )


def list_user_path_progress_summaries(db: Session, user_id: str) -> list[dict[str, object]]:
    paths = list(db.scalars(select(Path).order_by(Path.order.asc(), Path.name.asc())))
    if not paths:
        return []

    path_ids = [path.id for path in paths]
    labs = list(
        db.scalars(
            select(Lab)
            .where(Lab.path_id.in_(path_ids))
            .order_by(Lab.path_id.asc(), Lab.order_index.asc(), Lab.title.asc()),
        ),
    )

    labs_by_path_id: dict[str, list[Lab]] = {path_id: [] for path_id in path_ids}
    lab_ids: list[str] = []
    for lab in labs:
        if lab.path_id is None:
            continue
        labs_by_path_id[lab.path_id].append(lab)
        lab_ids.append(lab.id)

    progress_rows: list[LabProgress] = []
    progress_by_lab_id: dict[str, str] = {}
    if lab_ids:
        progress_rows = list(
            db.scalars(
                select(LabProgress).where(
                    LabProgress.user_id == user_id,
                    LabProgress.lab_id.in_(lab_ids),
                ),
            ),
        )
        progress_by_lab_id = {progress.lab_id: progress.status for progress in progress_rows}

    progression_completed_lab_ids = {
        progress.lab_id
        for progress in progress_rows
        if progress.status == "completed" and progress.completion_source == COMPLETION_SOURCE_EVALUATION
    }

    summaries: list[dict[str, object]] = []
    for path in paths:
        path_labs = labs_by_path_id.get(path.id, [])
        labs_by_id = {lab.id: lab for lab in path_labs}
        unlock_cache: dict[str, bool] = {}
        unlocked_lab_ids = {
            lab.id
            for lab in path_labs
            if _is_effectively_unlocked(
                lab=lab,
                labs_by_id=labs_by_id,
                completed_lab_ids=progression_completed_lab_ids,
                unlock_cache=unlock_cache,
            )
        }
        total_labs = len(path_labs)
        completed_labs = sum(1 for lab in path_labs if progress_by_lab_id.get(lab.id) == "completed")
        in_progress_labs = sum(
            1
            for lab in path_labs
            if lab.id in unlocked_lab_ids and progress_by_lab_id.get(lab.id) == "in_progress"
        )
        locked_labs = sum(
            1
            for lab in path_labs
            if lab.id not in unlocked_lab_ids
        )
        completion_percentage = int((completed_labs * 100) / total_labs) if total_labs else 0

        summaries.append(
            {
                "path_id": path.id,
                "path_name": path.name,
                "path_description": path.description,
                "total_labs": total_labs,
                "completed_labs": completed_labs,
                "in_progress_labs": in_progress_labs,
                "locked_labs": locked_labs,
                "completion_percentage": completion_percentage,
            },
        )

    return summaries


def start_lab_progress(db: Session, user: User, lab_id: str) -> LabProgress:
    lab = get_lab_by_id(db=db, lab_id=lab_id)

    if lab.prerequisite_lab_id is not None:
        prerequisite_progress = db.scalar(
            select(LabProgress).where(
                LabProgress.user_id == user.id,
                LabProgress.lab_id == lab.prerequisite_lab_id,
                LabProgress.status == "completed",
                LabProgress.completion_source == COMPLETION_SOURCE_EVALUATION,
            ),
        )
        if prerequisite_progress is None:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=(
                    f"Lab is locked. Complete prerequisite lab '{lab.prerequisite_lab_id}' before starting this one."
                ),
            )

    progress = db.scalar(
        select(LabProgress).where(
            LabProgress.user_id == user.id,
            LabProgress.lab_id == lab_id,
        ),
    )

    if progress is not None:
        return progress

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
    return _complete_lab_progress(db=db, user=user, lab_id=lab_id, completion_source=COMPLETION_SOURCE_MANUAL)


def complete_lab_progress_from_evaluation(db: Session, user: User, lab_id: str) -> LabProgress:
    return _complete_lab_progress(db=db, user=user, lab_id=lab_id, completion_source=COMPLETION_SOURCE_EVALUATION)


def _complete_lab_progress(db: Session, user: User, lab_id: str, completion_source: str) -> LabProgress:
    get_lab_by_id(db=db, lab_id=lab_id)

    if completion_source == COMPLETION_SOURCE_MANUAL:
        has_interactive_exercises = db.scalar(
            select(Exercise.id).where(
                Exercise.lab_id == lab_id,
                Exercise.status == "published",
            ).limit(1),
        )
        if has_interactive_exercises is not None:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=(
                    "Manual completion is not allowed for interactive labs. "
                    "Complete required exercises through evaluation to unlock progression."
                ),
            )

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
            completion_source=completion_source,
            started_at=now,
            completed_at=now,
        )
        db.add(progress)
    elif progress.status != "completed":
        progress.status = "completed"
        progress.completion_source = completion_source
        progress.started_at = progress.started_at or now
        progress.completed_at = now
    elif progress.completion_source != completion_source and completion_source == COMPLETION_SOURCE_EVALUATION:
        progress.completion_source = completion_source

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
            completion_source=None,
            started_at=now,
            completed_at=None,
        )
        db.add(progress)
    elif progress.status == "completed":
        progress.status = "in_progress"
        progress.completion_source = None
        progress.started_at = progress.started_at or now
        progress.completed_at = None

    db.commit()
    db.refresh(progress)
    return progress
