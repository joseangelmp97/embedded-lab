import json
from typing import Any

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.modules.labs.models.lab import Lab
from app.modules.labs.models.exercise import Exercise


INITIAL_LABS: tuple[dict[str, object], ...] = (
    {"id": "digital-logic-voltage-levels", "slug": "digital-logic-voltage-levels", "title": "Digital logic and voltage levels", "description": "Distinguish logic HIGH and LOW using safe voltage thresholds.", "difficulty": "beginner", "estimated_minutes": 20, "status": "published", "order_index": 1, "learning_objectives_json": json.dumps(["Interpret MCU logic thresholds", "Measure digital voltage levels"]), "tags_json": json.dumps(["gpio", "fundamentals", "electronics"]), "hardware_requirements_json": json.dumps(["microcontroller board", "multimeter", "breadboard"]), "content_version": 2, "is_optional": False},
    {"id": "gpio-led-basics", "slug": "gpio-led-basics", "title": "GPIO and LED basics", "description": "Control an LED with a GPIO output and verify expected behavior.", "difficulty": "beginner", "estimated_minutes": 25, "status": "published", "order_index": 2, "learning_objectives_json": json.dumps(["Configure digital output pins", "Validate LED polarity and wiring"]), "tags_json": json.dumps(["gpio", "output", "led"]), "hardware_requirements_json": json.dumps(["microcontroller board", "LED", "220-ohm resistor", "breadboard"]), "content_version": 2, "is_optional": False},
    {"id": "button-debounce-fundamentals", "slug": "button-debounce-fundamentals", "title": "Button debounce fundamentals", "description": "Implement stable button reads with software debounce timing.", "difficulty": "beginner", "estimated_minutes": 30, "status": "published", "order_index": 3, "learning_objectives_json": json.dumps(["Observe switch bounce", "Apply debounce filtering"]), "tags_json": json.dumps(["input", "debounce", "gpio"]), "hardware_requirements_json": json.dumps(["microcontroller board", "push button", "10k-ohm resistor", "breadboard"]), "content_version": 2, "is_optional": False},
    {"id": "resistor-led-current-limiting", "slug": "resistor-led-current-limiting", "title": "Resistor sizing for LED current limiting", "description": "Choose resistor values to protect GPIO and LED components.", "difficulty": "beginner", "estimated_minutes": 25, "status": "published", "order_index": 4, "learning_objectives_json": json.dumps(["Compute LED resistor values", "Check component power limits"]), "tags_json": json.dumps(["electronics", "safety", "led"]), "hardware_requirements_json": json.dumps(["microcontroller board", "LED", "resistor kit", "multimeter"]), "content_version": 2, "is_optional": False},
    {"id": "timing-with-blocking-delays", "slug": "timing-with-blocking-delays", "title": "Timing with blocking delays", "description": "Create deterministic blink timing and identify blocking side effects.", "difficulty": "beginner", "estimated_minutes": 20, "status": "published", "order_index": 5, "learning_objectives_json": json.dumps(["Use delay loops safely", "Compare expected vs actual periods"]), "tags_json": json.dumps(["timing", "gpio", "firmware"]), "hardware_requirements_json": json.dumps(["microcontroller board", "LED", "logic analyzer optional"]), "content_version": 2, "is_optional": False},
    {"id": "finite-state-machine-basics", "slug": "finite-state-machine-basics", "title": "Finite state machine basics", "description": "Model a small embedded behavior using explicit states and transitions.", "difficulty": "intermediate", "estimated_minutes": 35, "status": "published", "order_index": 6, "learning_objectives_json": json.dumps(["Define firmware states", "Implement transition logic"]), "tags_json": json.dumps(["state-machine", "architecture", "firmware"]), "hardware_requirements_json": json.dumps(["microcontroller board", "LED", "push button"]), "content_version": 2, "is_optional": False},
    {"id": "mcu-memory-map-intro", "slug": "mcu-memory-map-intro", "title": "MCU memory map introduction", "description": "Explore flash, RAM, and peripheral regions in a microcontroller memory map.", "difficulty": "beginner", "estimated_minutes": 30, "status": "published", "order_index": 7, "learning_objectives_json": json.dumps(["Identify memory regions", "Relate addresses to peripherals"]), "tags_json": json.dumps(["mcu", "memory", "architecture"]), "hardware_requirements_json": json.dumps(["microcontroller board", "vendor datasheet"]), "content_version": 2, "is_optional": False},
    {"id": "stack-and-heap-observability", "slug": "stack-and-heap-observability", "title": "Stack and heap observability", "description": "Track stack growth and heap usage during runtime.", "difficulty": "intermediate", "estimated_minutes": 35, "status": "published", "order_index": 8, "learning_objectives_json": json.dumps(["Estimate stack headroom", "Detect risky allocations"]), "tags_json": json.dumps(["memory", "debugging", "runtime"]), "hardware_requirements_json": json.dumps(["microcontroller board", "debugger probe"]), "content_version": 2, "is_optional": False},
    {"id": "interrupt-latency-basics", "slug": "interrupt-latency-basics", "title": "Interrupt latency basics", "description": "Measure and reduce interrupt response latency.", "difficulty": "intermediate", "estimated_minutes": 30, "status": "published", "order_index": 9, "learning_objectives_json": json.dumps(["Measure ISR entry delay", "Identify latency contributors"]), "tags_json": json.dumps(["interrupts", "timing", "mcu"]), "hardware_requirements_json": json.dumps(["microcontroller board", "logic analyzer or oscilloscope"]), "content_version": 2, "is_optional": False},
    {"id": "timer-periodic-tasks", "slug": "timer-periodic-tasks", "title": "Timer-driven periodic tasks", "description": "Use hardware timers to schedule periodic firmware actions.", "difficulty": "intermediate", "estimated_minutes": 35, "status": "published", "order_index": 10, "learning_objectives_json": json.dumps(["Configure timer peripherals", "Execute periodic tasks predictably"]), "tags_json": json.dumps(["timers", "scheduler", "mcu"]), "hardware_requirements_json": json.dumps(["microcontroller board", "LED"]), "content_version": 2, "is_optional": False},
    {"id": "watchdog-configuration-basics", "slug": "watchdog-configuration-basics", "title": "Watchdog configuration basics", "description": "Configure watchdog timers to recover from lockups.", "difficulty": "intermediate", "estimated_minutes": 25, "status": "published", "order_index": 11, "learning_objectives_json": json.dumps(["Enable watchdog safely", "Create watchdog test scenarios"]), "tags_json": json.dumps(["watchdog", "reliability", "reset"]), "hardware_requirements_json": json.dumps(["microcontroller board", "debugger probe"]), "content_version": 2, "is_optional": False},
    {"id": "low-power-sleep-wakeup", "slug": "low-power-sleep-wakeup", "title": "Low-power sleep and wake-up", "description": "Enter sleep modes and wake on events while preserving system state.", "difficulty": "intermediate", "estimated_minutes": 35, "status": "published", "order_index": 12, "learning_objectives_json": json.dumps(["Configure sleep states", "Validate wake-up sources"]), "tags_json": json.dumps(["power", "mcu", "optimization"]), "hardware_requirements_json": json.dumps(["microcontroller board", "current meter"]), "content_version": 2, "is_optional": False},
    {"id": "uart-serial-console-setup", "slug": "uart-serial-console-setup", "title": "UART serial console setup", "description": "Bring up a UART console for runtime diagnostics.", "difficulty": "beginner", "estimated_minutes": 25, "status": "published", "order_index": 13, "learning_objectives_json": json.dumps(["Configure UART baud settings", "Transmit and receive basic frames"]), "tags_json": json.dumps(["uart", "serial", "diagnostics"]), "hardware_requirements_json": json.dumps(["microcontroller board", "USB-UART adapter"]), "content_version": 2, "is_optional": False},
    {"id": "uart-command-parser", "slug": "uart-command-parser", "title": "UART command parser", "description": "Parse line-based serial commands with basic validation.", "difficulty": "intermediate", "estimated_minutes": 35, "status": "published", "order_index": 14, "learning_objectives_json": json.dumps(["Design serial command grammar", "Validate command arguments"]), "tags_json": json.dumps(["uart", "parser", "firmware"]), "hardware_requirements_json": json.dumps(["microcontroller board", "USB-UART adapter"]), "content_version": 2, "is_optional": False},
    {"id": "i2c-device-scan", "slug": "i2c-device-scan", "title": "I2C device scan", "description": "Scan an I2C bus and identify connected peripheral addresses.", "difficulty": "beginner", "estimated_minutes": 25, "status": "published", "order_index": 15, "learning_objectives_json": json.dumps(["Wire I2C bus correctly", "Interpret ACK/NACK behavior"]), "tags_json": json.dumps(["i2c", "bus", "peripherals"]), "hardware_requirements_json": json.dumps(["microcontroller board", "i2c sensor module", "pull-up resistors"]), "content_version": 2, "is_optional": False},
    {"id": "i2c-register-read-write", "slug": "i2c-register-read-write", "title": "I2C register read/write", "description": "Read and write register values on an I2C peripheral.", "difficulty": "intermediate", "estimated_minutes": 35, "status": "published", "order_index": 16, "learning_objectives_json": json.dumps(["Perform register transactions", "Handle repeated start conditions"]), "tags_json": json.dumps(["i2c", "registers", "drivers"]), "hardware_requirements_json": json.dumps(["microcontroller board", "i2c sensor module"]), "content_version": 2, "is_optional": False},
    {"id": "spi-loopback-validation", "slug": "spi-loopback-validation", "title": "SPI loopback validation", "description": "Verify SPI timing and byte framing using loopback tests.", "difficulty": "intermediate", "estimated_minutes": 30, "status": "published", "order_index": 17, "learning_objectives_json": json.dumps(["Configure SPI mode and clock", "Validate full-duplex transfer"]), "tags_json": json.dumps(["spi", "timing", "validation"]), "hardware_requirements_json": json.dumps(["microcontroller board", "jumper wires"]), "content_version": 2, "is_optional": False},
    {"id": "framing-and-checksum-basics", "slug": "framing-and-checksum-basics", "title": "Framing and checksum basics", "description": "Build simple packet framing and checksum verification.", "difficulty": "intermediate", "estimated_minutes": 30, "status": "published", "order_index": 18, "learning_objectives_json": json.dumps(["Define packet boundaries", "Compute simple checksums"]), "tags_json": json.dumps(["protocol", "checksum", "communication"]), "hardware_requirements_json": json.dumps(["microcontroller board", "serial link"]), "content_version": 2, "is_optional": False},
    {"id": "adc-temperature-sensor-read", "slug": "adc-temperature-sensor-read", "title": "ADC temperature sensor read", "description": "Read analog temperature values through an ADC channel.", "difficulty": "beginner", "estimated_minutes": 30, "status": "published", "order_index": 19, "learning_objectives_json": json.dumps(["Configure ADC sampling", "Convert raw counts to engineering units"]), "tags_json": json.dumps(["adc", "sensor", "analog"]), "hardware_requirements_json": json.dumps(["microcontroller board", "analog temperature sensor"]), "content_version": 2, "is_optional": False},
    {"id": "sensor-sampling-and-averaging", "slug": "sensor-sampling-and-averaging", "title": "Sensor sampling and averaging", "description": "Reduce sensor noise with averaging and consistent sampling intervals.", "difficulty": "intermediate", "estimated_minutes": 30, "status": "published", "order_index": 20, "learning_objectives_json": json.dumps(["Design sampling loops", "Apply moving average filtering"]), "tags_json": json.dumps(["sensors", "signal", "filtering"]), "hardware_requirements_json": json.dumps(["microcontroller board", "analog sensor"]), "content_version": 2, "is_optional": False},
    {"id": "threshold-alarm-logic", "slug": "threshold-alarm-logic", "title": "Threshold alarm logic", "description": "Trigger alarms from sensor thresholds with hysteresis to avoid chatter.", "difficulty": "intermediate", "estimated_minutes": 25, "status": "published", "order_index": 21, "learning_objectives_json": json.dumps(["Implement threshold checks", "Use hysteresis for stable alarms"]), "tags_json": json.dumps(["sensors", "alarms", "logic"]), "hardware_requirements_json": json.dumps(["microcontroller board", "sensor", "buzzer or LED"]), "content_version": 2, "is_optional": False},
    {"id": "pwm-motor-speed-control", "slug": "pwm-motor-speed-control", "title": "PWM motor speed control", "description": "Control DC motor speed using PWM duty cycle adjustment.", "difficulty": "intermediate", "estimated_minutes": 40, "status": "published", "order_index": 22, "learning_objectives_json": json.dumps(["Set PWM frequency and duty", "Relate duty cycle to motor response"]), "tags_json": json.dumps(["pwm", "motor", "actuator"]), "hardware_requirements_json": json.dumps(["microcontroller board", "dc motor", "motor driver"]), "content_version": 2, "is_optional": False},
    {"id": "servo-position-control", "slug": "servo-position-control", "title": "Servo position control", "description": "Generate pulse timings to position a hobby servo accurately.", "difficulty": "intermediate", "estimated_minutes": 35, "status": "published", "order_index": 23, "learning_objectives_json": json.dumps(["Map pulse width to angle", "Respect servo power constraints"]), "tags_json": json.dumps(["servo", "pwm", "actuator"]), "hardware_requirements_json": json.dumps(["microcontroller board", "servo motor", "external 5V supply"]), "content_version": 2, "is_optional": False},
    {"id": "h-bridge-direction-control", "slug": "h-bridge-direction-control", "title": "H-bridge direction control", "description": "Drive motor direction safely with an H-bridge interface.", "difficulty": "intermediate", "estimated_minutes": 35, "status": "published", "order_index": 24, "learning_objectives_json": json.dumps(["Control H-bridge inputs", "Prevent shoot-through conditions"]), "tags_json": json.dumps(["h-bridge", "motor", "safety"]), "hardware_requirements_json": json.dumps(["microcontroller board", "h-bridge module", "dc motor"]), "content_version": 2, "is_optional": False},
    {"id": "structured-logging-basics", "slug": "structured-logging-basics", "title": "Structured logging basics", "description": "Emit consistent runtime logs to speed debugging and analysis.", "difficulty": "beginner", "estimated_minutes": 20, "status": "published", "order_index": 25, "learning_objectives_json": json.dumps(["Define log levels", "Use structured log fields"]), "tags_json": json.dumps(["logging", "debugging", "reliability"]), "hardware_requirements_json": json.dumps(["microcontroller board", "serial console"]), "content_version": 2, "is_optional": False},
    {"id": "assertions-and-fail-fast", "slug": "assertions-and-fail-fast", "title": "Assertions and fail-fast behavior", "description": "Use assertions to catch invalid states early.", "difficulty": "intermediate", "estimated_minutes": 25, "status": "published", "order_index": 26, "learning_objectives_json": json.dumps(["Place meaningful assertions", "Handle assertion failures safely"]), "tags_json": json.dumps(["assertions", "safety", "firmware"]), "hardware_requirements_json": json.dumps(["microcontroller board", "debugger probe"]), "content_version": 2, "is_optional": False},
    {"id": "fault-injection-reset-recovery", "slug": "fault-injection-reset-recovery", "title": "Fault injection and reset recovery", "description": "Inject controlled faults and validate recovery after reset.", "difficulty": "advanced", "estimated_minutes": 40, "status": "published", "order_index": 27, "learning_objectives_json": json.dumps(["Design fault scenarios", "Verify reset recovery paths"]), "tags_json": json.dumps(["fault-injection", "reset", "reliability"]), "hardware_requirements_json": json.dumps(["microcontroller board", "debugger probe", "power switch"]), "content_version": 2, "is_optional": False},
    {"id": "boundary-value-test-design", "slug": "boundary-value-test-design", "title": "Boundary value test design", "description": "Design firmware tests around boundary and edge conditions.", "difficulty": "intermediate", "estimated_minutes": 30, "status": "published", "order_index": 28, "learning_objectives_json": json.dumps(["Identify boundary inputs", "Create reproducible test cases"]), "tags_json": json.dumps(["testing", "quality", "validation"]), "hardware_requirements_json": json.dumps(["microcontroller board", "test checklist"]), "content_version": 2, "is_optional": False},
    {"id": "on-target-debugger-breakpoints", "slug": "on-target-debugger-breakpoints", "title": "On-target debugger breakpoints", "description": "Use breakpoints and watch windows to inspect firmware state.", "difficulty": "intermediate", "estimated_minutes": 30, "status": "published", "order_index": 29, "learning_objectives_json": json.dumps(["Set effective breakpoints", "Inspect memory and registers"]), "tags_json": json.dumps(["debugger", "inspection", "tooling"]), "hardware_requirements_json": json.dumps(["microcontroller board", "SWD/JTAG debugger"]), "content_version": 2, "is_optional": False},
    {"id": "postmortem-event-timeline", "slug": "postmortem-event-timeline", "title": "Postmortem event timeline", "description": "Reconstruct failure timelines from logs and observed states.", "difficulty": "advanced", "estimated_minutes": 35, "status": "published", "order_index": 30, "learning_objectives_json": json.dumps(["Correlate events across logs", "Build root-cause hypotheses"]), "tags_json": json.dumps(["postmortem", "debugging", "analysis"]), "hardware_requirements_json": json.dumps(["microcontroller board", "serial logs", "debug notes"]), "content_version": 2, "is_optional": False},
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


SENSITIVE_METADATA_KEYS = {
    "answer",
    "answers",
    "answer_key",
    "accepted_answer",
    "accepted_answers",
    "correct_answer",
    "correct_answers",
    "expected_answer",
    "expected_answers",
    "evaluation_rule",
    "evaluation_rules",
    "rubric",
    "solution",
    "solutions",
}


def _sanitize_json_payload(value: Any) -> Any:
    if isinstance(value, dict):
        sanitized: dict[str, Any] = {}
        for key, item in value.items():
            if key.lower() in SENSITIVE_METADATA_KEYS:
                continue
            sanitized[key] = _sanitize_json_payload(item)
        return sanitized

    if isinstance(value, list):
        return [_sanitize_json_payload(item) for item in value]

    return value


def parse_and_sanitize_json(raw_json: str | None) -> dict[str, Any] | list[Any] | None:
    if raw_json is None:
        return None

    try:
        parsed = json.loads(raw_json)
    except json.JSONDecodeError:
        return None

    if isinstance(parsed, (dict, list)):
        return _sanitize_json_payload(parsed)

    return None


def list_published_lab_exercises(db: Session, lab_id: str) -> list[Exercise]:
    get_lab_by_id(db=db, lab_id=lab_id)
    return list(
        db.scalars(
            select(Exercise)
            .where(
                Exercise.lab_id == lab_id,
                Exercise.status == "published",
            )
            .order_by(Exercise.order_index.asc(), Exercise.id.asc())
        )
    )


def seed_initial_labs(db: Session) -> None:
    existing_labs = {lab.id: lab for lab in db.scalars(select(Lab)).all()}
    has_changes = False

    for lab_payload in INITIAL_LABS:
        lab_id = str(lab_payload["id"])
        lab = existing_labs.get(lab_id)
        if lab is None:
            db.add(Lab(**lab_payload))
            has_changes = True
            continue

        for field_name, field_value in lab_payload.items():
            if getattr(lab, field_name) != field_value:
                setattr(lab, field_name, field_value)
                has_changes = True

    if has_changes:
        db.commit()
