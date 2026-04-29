from collections import defaultdict

from fastapi import HTTPException, status
from sqlalchemy import inspect, select
from sqlalchemy.orm import Session

from app.modules.labs.models.lab import Lab
from app.modules.paths.models.path import Path


INITIAL_PATHS: tuple[dict[str, object], ...] = (
    {
        "id": "247f7a42-17d9-4f08-8fc3-7284fdbbe93c",
        "name": "Embedded Fundamentals",
        "description": "Core embedded concepts: digital I/O, timing basics, and practical hardware interactions.",
        "order": 1,
    },
    {
        "id": "fcb79cb6-18f6-4347-a7cb-f8f57c4d4f17",
        "name": "Sensors & IO",
        "description": "Learn reliable input handling and output control with common embedded peripherals.",
        "order": 2,
    },
    {
        "id": "f9f6a909-9772-4498-a401-c30ec57cee82",
        "name": "Communication",
        "description": "Build communication fundamentals across wired and serial embedded interfaces.",
        "order": 3,
    },
    {
        "id": "0f4e1c77-fbe2-4b3f-b4d6-3496083f7ecd",
        "name": "IoT Basics",
        "description": "Connect embedded systems to networked services with secure and practical IoT patterns.",
        "order": 4,
    },
)

LAB_PATH_ASSIGNMENTS: dict[str, str] = {
    "digital-logic-voltage-levels": "Embedded Fundamentals",
    "gpio-led-basics": "Embedded Fundamentals",
    "button-debounce-fundamentals": "Embedded Fundamentals",
    "resistor-led-current-limiting": "Embedded Fundamentals",
    "timing-with-blocking-delays": "Embedded Fundamentals",
    "finite-state-machine-basics": "Embedded Fundamentals",
    "mcu-memory-map-intro": "Embedded Fundamentals",
    "stack-and-heap-observability": "Embedded Fundamentals",
    "interrupt-latency-basics": "Embedded Fundamentals",
    "timer-periodic-tasks": "Embedded Fundamentals",
    "watchdog-configuration-basics": "Embedded Fundamentals",
    "low-power-sleep-wakeup": "Embedded Fundamentals",
    "uart-serial-console-setup": "Embedded Fundamentals",
    "uart-command-parser": "Embedded Fundamentals",
    "i2c-device-scan": "Embedded Fundamentals",
    "i2c-register-read-write": "Embedded Fundamentals",
    "spi-loopback-validation": "Embedded Fundamentals",
    "framing-and-checksum-basics": "Embedded Fundamentals",
    "adc-temperature-sensor-read": "Embedded Fundamentals",
    "sensor-sampling-and-averaging": "Embedded Fundamentals",
    "threshold-alarm-logic": "Embedded Fundamentals",
    "pwm-motor-speed-control": "Embedded Fundamentals",
    "servo-position-control": "Embedded Fundamentals",
    "h-bridge-direction-control": "Embedded Fundamentals",
    "structured-logging-basics": "Embedded Fundamentals",
    "assertions-and-fail-fast": "Embedded Fundamentals",
    "fault-injection-reset-recovery": "Embedded Fundamentals",
    "boundary-value-test-design": "Embedded Fundamentals",
    "on-target-debugger-breakpoints": "Embedded Fundamentals",
    "postmortem-event-timeline": "Embedded Fundamentals",
}


def list_paths(db: Session) -> list[Path]:
    return list(db.scalars(select(Path).order_by(Path.order.asc(), Path.name.asc())))


def get_path_by_id(db: Session, path_id: str) -> Path:
    path = db.scalar(select(Path).where(Path.id == path_id))
    if path is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Path not found",
        )

    return path


def list_labs_by_path_id(db: Session, path_id: str) -> list[Lab]:
    get_path_by_id(db=db, path_id=path_id)
    return list(
        db.scalars(
            select(Lab)
            .where(Lab.path_id == path_id)
            .order_by(Lab.order_index.asc(), Lab.title.asc()),
        ),
    )


def seed_initial_paths(db: Session) -> None:
    existing_paths = {path.id: path for path in db.scalars(select(Path)).all()}
    has_changes = False

    for path_payload in INITIAL_PATHS:
        path_id = str(path_payload["id"])
        path = existing_paths.get(path_id)
        if path is None:
            db.add(Path(**path_payload))
            has_changes = True
            continue

        for field_name, field_value in path_payload.items():
            if getattr(path, field_name) != field_value:
                setattr(path, field_name, field_value)
                has_changes = True

    if has_changes:
        db.commit()


def assign_labs_to_paths(db: Session) -> None:
    bind = db.get_bind()
    inspector = inspect(bind)
    if "paths" not in inspector.get_table_names() or "labs" not in inspector.get_table_names():
        return

    lab_column_names = {column["name"] for column in inspector.get_columns("labs")}
    if "path_id" not in lab_column_names:
        return

    path_name_to_id = {name: path_id for path_id, name in db.execute(select(Path.id, Path.name))}

    has_changes = False
    for lab_id, path_name in LAB_PATH_ASSIGNMENTS.items():
        path_id = path_name_to_id.get(path_name)
        if path_id is None:
            continue

        lab = db.scalar(select(Lab).where(Lab.id == lab_id))
        if lab is None or lab.path_id == path_id:
            continue

        lab.path_id = path_id
        has_changes = True

    if has_changes:
        db.commit()

    assign_lab_prerequisites_by_path(db=db)


def assign_lab_prerequisites_by_path(db: Session) -> None:
    bind = db.get_bind()
    inspector = inspect(bind)
    if "labs" not in inspector.get_table_names():
        return

    lab_column_names = {column["name"] for column in inspector.get_columns("labs")}
    if "path_id" not in lab_column_names or "prerequisite_lab_id" not in lab_column_names:
        return

    labs = list(
        db.scalars(
            select(Lab)
            .where(Lab.path_id.is_not(None))
            .order_by(Lab.path_id.asc(), Lab.order_index.asc(), Lab.title.asc()),
        ),
    )

    labs_by_path_id: dict[str, list[Lab]] = defaultdict(list)
    for lab in labs:
        if lab.path_id is None:
            continue
        labs_by_path_id[lab.path_id].append(lab)

    has_changes = False
    for path_labs in labs_by_path_id.values():
        previous_lab_id: str | None = None
        for lab in path_labs:
            if lab.prerequisite_lab_id != previous_lab_id:
                lab.prerequisite_lab_id = previous_lab_id
                has_changes = True
            previous_lab_id = lab.id

    if has_changes:
        db.commit()
