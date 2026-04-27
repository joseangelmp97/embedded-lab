from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.modules.labs.models.lab import Lab


INITIAL_LABS: tuple[dict[str, object], ...] = (
    {
        "id": "gpio-led-basics",
        "title": "GPIO and LED basics",
        "description": "Learn GPIO output fundamentals by controlling an LED with a microcontroller pin.",
        "difficulty": "beginner",
        "estimated_minutes": 25,
        "status": "published",
        "order_index": 1,
    },
    {
        "id": "button-debounce-fundamentals",
        "title": "Button debounce fundamentals",
        "description": "Understand switch bounce behavior and implement reliable button input handling.",
        "difficulty": "beginner",
        "estimated_minutes": 35,
        "status": "published",
        "order_index": 2,
    },
    {
        "id": "pwm-motor-speed-control",
        "title": "PWM motor speed control",
        "description": "Use PWM duty cycle control to adjust DC motor speed with stable output behavior.",
        "difficulty": "intermediate",
        "estimated_minutes": 45,
        "status": "published",
        "order_index": 3,
    },
)


def list_labs(db: Session) -> list[Lab]:
    return list(db.scalars(select(Lab).order_by(Lab.order_index.asc(), Lab.title.asc())))


def get_lab_by_id(db: Session, lab_id: str) -> Lab:
    lab = db.scalar(select(Lab).where(Lab.id == lab_id))
    if lab is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Lab not found",
        )

    return lab


def seed_initial_labs(db: Session) -> None:
    existing_ids = set(db.scalars(select(Lab.id)))
    labs_to_create = [Lab(**lab_payload) for lab_payload in INITIAL_LABS if lab_payload["id"] not in existing_ids]

    if not labs_to_create:
        return

    db.add_all(labs_to_create)
    db.commit()
