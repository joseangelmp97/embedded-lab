from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.modules.labs.models.lab import Lab
from app.modules.paths.models.path import Path
from app.modules.paths.models.path_module import PathModule


INITIAL_PATH_MODULES: tuple[dict[str, object], ...] = (
    {
        "id": "ce4fce5f-b9a4-4e9f-8c4f-07fbe8838399",
        "path_id": "247f7a42-17d9-4f08-8fc3-7284fdbbe93c",
        "slug": "gpio-fundamentals",
        "title": "GPIO Fundamentals",
        "description": "Understand microcontroller digital output concepts with practical hardware control.",
        "order_index": 1,
        "is_published": True,
    },
    {
        "id": "b2ad4087-f7e2-42fc-9d4d-306fd83b5ab2",
        "path_id": "fcb79cb6-18f6-4347-a7cb-f8f57c4d4f17",
        "slug": "input-reliability",
        "title": "Reliable Input Handling",
        "description": "Handle noisy digital input signals and stable embedded interaction patterns.",
        "order_index": 1,
        "is_published": True,
    },
    {
        "id": "fd771a62-a917-4e95-bcb0-a71f73898e37",
        "path_id": "fcb79cb6-18f6-4347-a7cb-f8f57c4d4f17",
        "slug": "output-control",
        "title": "Output Control",
        "description": "Apply output control techniques for motors and actuators.",
        "order_index": 2,
        "is_published": True,
    },
)

LAB_MODULE_ASSIGNMENTS: dict[str, str] = {
    "gpio-led-basics": "ce4fce5f-b9a4-4e9f-8c4f-07fbe8838399",
    "button-debounce-fundamentals": "b2ad4087-f7e2-42fc-9d4d-306fd83b5ab2",
    "pwm-motor-speed-control": "fd771a62-a917-4e95-bcb0-a71f73898e37",
}


def seed_initial_path_modules(db: Session) -> None:
    existing_ids = set(db.scalars(select(PathModule.id)))
    modules_to_create = [
        PathModule(**module_payload)
        for module_payload in INITIAL_PATH_MODULES
        if module_payload["id"] not in existing_ids
    ]

    if not modules_to_create:
        return

    db.add_all(modules_to_create)
    db.commit()


def list_modules_by_path_id(db: Session, path_id: str) -> list[PathModule]:
    path = db.scalar(select(Path.id).where(Path.id == path_id))
    if path is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Path not found")

    return list(
        db.scalars(
            select(PathModule)
            .where(PathModule.path_id == path_id)
            .order_by(PathModule.order_index.asc(), PathModule.title.asc()),
        ),
    )


def list_labs_by_module_id(db: Session, module_id: str) -> list[Lab]:
    module = db.scalar(select(PathModule).where(PathModule.id == module_id))
    if module is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Module not found")

    return list(
        db.scalars(
            select(Lab)
            .where(Lab.module_id == module_id)
            .order_by(Lab.order_index.asc(), Lab.title.asc()),
        ),
    )


def assign_labs_to_modules(db: Session) -> None:
    has_changes = False
    for lab_id, module_id in LAB_MODULE_ASSIGNMENTS.items():
        lab = db.scalar(select(Lab).where(Lab.id == lab_id))
        if lab is None or lab.module_id == module_id:
            continue

        lab.module_id = module_id
        if not lab.slug:
            lab.slug = lab.id
        has_changes = True

    if has_changes:
        db.commit()

    validate_module_prerequisite_integrity(db=db)


def validate_module_prerequisite_integrity(db: Session) -> None:
    labs = list(db.scalars(select(Lab).where(Lab.module_id.is_not(None), Lab.prerequisite_lab_id.is_not(None))))
    if not labs:
        return

    lab_by_id = {lab.id: lab for lab in db.scalars(select(Lab)).all()}
    for lab in labs:
        prerequisite_lab = lab_by_id.get(lab.prerequisite_lab_id or "")
        if prerequisite_lab is None:
            continue

        if lab.path_id is not None and prerequisite_lab.path_id != lab.path_id:
            raise ValueError(
                f"Invalid prerequisite mapping for lab '{lab.id}': prerequisite must be in same path when module_id is assigned."
            )
