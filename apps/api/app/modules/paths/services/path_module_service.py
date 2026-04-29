from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.modules.labs.models.lab import Lab
from app.modules.paths.models.path import Path
from app.modules.paths.models.path_module import PathModule


INITIAL_PATH_MODULES: tuple[dict[str, object], ...] = (
    {
        "id": "4f5204af-0a30-4c87-87ad-42f2f06f4c11",
        "path_id": "247f7a42-17d9-4f08-8fc3-7284fdbbe93c",
        "slug": "embedded-foundations",
        "title": "Embedded Foundations",
        "description": "Build practical embedded fundamentals with digital logic, timing, and safe hardware bring-up.",
        "order_index": 1,
        "is_published": True,
    },
    {
        "id": "ffd6056e-b9d7-474f-bbf5-08f0c91ed67f",
        "path_id": "247f7a42-17d9-4f08-8fc3-7284fdbbe93c",
        "slug": "mcu-core",
        "title": "MCU Core",
        "description": "Understand microcontroller internals, memory, interrupts, timers, and low-power operation.",
        "order_index": 2,
        "is_published": True,
    },
    {
        "id": "8daf952f-c0d8-4e74-9f4a-2a6d13d47cdb",
        "path_id": "247f7a42-17d9-4f08-8fc3-7284fdbbe93c",
        "slug": "interfaces-and-communication",
        "title": "Interfaces and Communication",
        "description": "Practice UART, SPI, and I2C integration patterns for robust peripheral communication.",
        "order_index": 3,
        "is_published": True,
    },
    {
        "id": "76fe96a3-a500-4a41-857a-462c08b3d3ca",
        "path_id": "247f7a42-17d9-4f08-8fc3-7284fdbbe93c",
        "slug": "sensors-and-actuators",
        "title": "Sensors and Actuators",
        "description": "Connect, calibrate, and control real-world sensors and actuators with repeatable behavior.",
        "order_index": 4,
        "is_published": True,
    },
    {
        "id": "109a5f48-e4e3-4a6c-b44b-219cf616ef69",
        "path_id": "247f7a42-17d9-4f08-8fc3-7284fdbbe93c",
        "slug": "reliability-and-debugging",
        "title": "Reliability and Debugging",
        "description": "Increase firmware quality with fault analysis, traceability, and defensive debugging workflows.",
        "order_index": 5,
        "is_published": True,
    },
)

LAB_MODULE_ASSIGNMENTS: dict[str, str] = {
    "digital-logic-voltage-levels": "4f5204af-0a30-4c87-87ad-42f2f06f4c11",
    "gpio-led-basics": "4f5204af-0a30-4c87-87ad-42f2f06f4c11",
    "button-debounce-fundamentals": "4f5204af-0a30-4c87-87ad-42f2f06f4c11",
    "resistor-led-current-limiting": "4f5204af-0a30-4c87-87ad-42f2f06f4c11",
    "timing-with-blocking-delays": "4f5204af-0a30-4c87-87ad-42f2f06f4c11",
    "finite-state-machine-basics": "4f5204af-0a30-4c87-87ad-42f2f06f4c11",
    "mcu-memory-map-intro": "ffd6056e-b9d7-474f-bbf5-08f0c91ed67f",
    "stack-and-heap-observability": "ffd6056e-b9d7-474f-bbf5-08f0c91ed67f",
    "interrupt-latency-basics": "ffd6056e-b9d7-474f-bbf5-08f0c91ed67f",
    "timer-periodic-tasks": "ffd6056e-b9d7-474f-bbf5-08f0c91ed67f",
    "watchdog-configuration-basics": "ffd6056e-b9d7-474f-bbf5-08f0c91ed67f",
    "low-power-sleep-wakeup": "ffd6056e-b9d7-474f-bbf5-08f0c91ed67f",
    "uart-serial-console-setup": "8daf952f-c0d8-4e74-9f4a-2a6d13d47cdb",
    "uart-command-parser": "8daf952f-c0d8-4e74-9f4a-2a6d13d47cdb",
    "i2c-device-scan": "8daf952f-c0d8-4e74-9f4a-2a6d13d47cdb",
    "i2c-register-read-write": "8daf952f-c0d8-4e74-9f4a-2a6d13d47cdb",
    "spi-loopback-validation": "8daf952f-c0d8-4e74-9f4a-2a6d13d47cdb",
    "framing-and-checksum-basics": "8daf952f-c0d8-4e74-9f4a-2a6d13d47cdb",
    "adc-temperature-sensor-read": "76fe96a3-a500-4a41-857a-462c08b3d3ca",
    "sensor-sampling-and-averaging": "76fe96a3-a500-4a41-857a-462c08b3d3ca",
    "threshold-alarm-logic": "76fe96a3-a500-4a41-857a-462c08b3d3ca",
    "pwm-motor-speed-control": "76fe96a3-a500-4a41-857a-462c08b3d3ca",
    "servo-position-control": "76fe96a3-a500-4a41-857a-462c08b3d3ca",
    "h-bridge-direction-control": "76fe96a3-a500-4a41-857a-462c08b3d3ca",
    "structured-logging-basics": "109a5f48-e4e3-4a6c-b44b-219cf616ef69",
    "assertions-and-fail-fast": "109a5f48-e4e3-4a6c-b44b-219cf616ef69",
    "fault-injection-reset-recovery": "109a5f48-e4e3-4a6c-b44b-219cf616ef69",
    "boundary-value-test-design": "109a5f48-e4e3-4a6c-b44b-219cf616ef69",
    "on-target-debugger-breakpoints": "109a5f48-e4e3-4a6c-b44b-219cf616ef69",
    "postmortem-event-timeline": "109a5f48-e4e3-4a6c-b44b-219cf616ef69",
}


def seed_initial_path_modules(db: Session) -> None:
    existing_modules = {module.id: module for module in db.scalars(select(PathModule)).all()}
    has_changes = False

    for module_payload in INITIAL_PATH_MODULES:
        module_id = str(module_payload["id"])
        module = existing_modules.get(module_id)
        if module is None:
            db.add(PathModule(**module_payload))
            has_changes = True
            continue

        for field_name, field_value in module_payload.items():
            if getattr(module, field_name) != field_value:
                setattr(module, field_name, field_value)
                has_changes = True

    if has_changes:
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

    assign_lab_prerequisites_by_module(db=db)

    validate_module_prerequisite_integrity(db=db)


def assign_lab_prerequisites_by_module(db: Session) -> None:
    modules = list(db.scalars(select(PathModule).order_by(PathModule.order_index.asc(), PathModule.title.asc())))
    if not modules:
        return

    has_changes = False
    for module in modules:
        module_labs = list(
            db.scalars(
                select(Lab)
                .where(Lab.module_id == module.id)
                .order_by(Lab.order_index.asc(), Lab.title.asc()),
            ),
        )
        previous_lab_id: str | None = None
        for lab in module_labs:
            if lab.prerequisite_lab_id != previous_lab_id:
                lab.prerequisite_lab_id = previous_lab_id
                has_changes = True
            previous_lab_id = lab.id

    if has_changes:
        db.commit()


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
