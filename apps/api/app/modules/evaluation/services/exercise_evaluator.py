import json
import re
from dataclasses import dataclass
from typing import Any

from fastapi import HTTPException, status


SUPPORTED_EXERCISE_TYPES = {"multiple_choice", "fill_blank", "short_text"}


@dataclass(frozen=True)
class EvaluationResult:
    is_correct: bool
    score_awarded: int
    feedback: str
    details: dict[str, Any]


def _parse_metadata(metadata_json: str | None) -> dict[str, Any]:
    if metadata_json is None:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_CONTENT, detail="Exercise metadata is invalid")
    try:
        parsed = json.loads(metadata_json)
    except json.JSONDecodeError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_CONTENT, detail="Exercise metadata is invalid") from exc
    if not isinstance(parsed, dict):
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_CONTENT, detail="Exercise metadata is invalid")
    return parsed


def _normalize_fill_blank_value(value: Any) -> str:
    text = str(value).strip().lower()
    text = re.sub(r"\s+", " ", text)
    return text.replace(" ", "")


def _normalize_short_text_value(value: Any) -> str:
    return str(value).strip().lower()


def _extract_mcq_selected_option_id(response_payload_json: dict[str, Any]) -> str:
    selected_option_id = response_payload_json.get("selected_option_id")
    if not isinstance(selected_option_id, str) or not selected_option_id.strip():
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail="response_payload_json.selected_option_id is required",
        )
    return selected_option_id


def _evaluate_multiple_choice(metadata: dict[str, Any], response_payload_json: dict[str, Any], max_score: int) -> EvaluationResult:
    correct_option_id = None
    for key in ("correct_option_id", "correct_answer", "answer"):
        value = metadata.get(key)
        if isinstance(value, str) and value.strip():
            correct_option_id = value
            break
    if correct_option_id is None:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_CONTENT, detail="Exercise metadata is missing correct option")

    selected_option_id = _extract_mcq_selected_option_id(response_payload_json)
    is_correct = selected_option_id == correct_option_id
    return EvaluationResult(
        is_correct=is_correct,
        score_awarded=max_score if is_correct else 0,
        feedback="Correct answer." if is_correct else "Incorrect answer. Try again.",
        details={"exercise_type": "multiple_choice", "mode": "deterministic"},
    )


def _extract_fill_blank_answers(response_payload_json: dict[str, Any]) -> dict[int, Any]:
    answers = response_payload_json.get("answers")
    if isinstance(answers, list):
        return {index: value for index, value in enumerate(answers)}
    if isinstance(answers, dict):
        mapped: dict[int, Any] = {}
        for key, value in answers.items():
            if isinstance(key, int):
                mapped[key] = value
                continue
            if isinstance(key, str) and key.isdigit():
                mapped[int(key)] = value
                continue
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
                detail="response_payload_json.answers map keys must be blank indices",
            )
        return mapped
    raise HTTPException(
        status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
        detail="response_payload_json.answers must be an array or an object",
    )


def _evaluate_fill_blank(metadata: dict[str, Any], response_payload_json: dict[str, Any], max_score: int) -> EvaluationResult:
    correct_answers = metadata.get("correct_answers")
    if not isinstance(correct_answers, list) or len(correct_answers) == 0:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail="Exercise metadata is missing correct_answers",
        )
    if not all(isinstance(value, (str, int, float)) for value in correct_answers):
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_CONTENT, detail="Exercise metadata is invalid")

    submitted_answers = _extract_fill_blank_answers(response_payload_json)
    incorrect_indices: list[int] = []
    correct_count = 0
    total_blanks = len(correct_answers)

    for index, expected in enumerate(correct_answers):
        provided = submitted_answers.get(index)
        if _normalize_fill_blank_value(provided) == _normalize_fill_blank_value(expected):
            correct_count += 1
        else:
            incorrect_indices.append(index)

    # Integer storage strategy: deterministic floor via int() conversion.
    score_awarded = int((correct_count / total_blanks) * max_score)
    is_correct = correct_count == total_blanks
    if is_correct:
        feedback = "All blanks are correct."
    else:
        feedback = f"Some blanks are incorrect: {incorrect_indices}."

    return EvaluationResult(
        is_correct=is_correct,
        score_awarded=score_awarded,
        feedback=feedback,
        details={
            "exercise_type": "fill_blank",
            "mode": "deterministic",
            "correct_blanks": correct_count,
            "total_blanks": total_blanks,
            "incorrect_indices": incorrect_indices,
        },
    )


def _evaluate_short_text(metadata: dict[str, Any], response_payload_json: dict[str, Any], max_score: int) -> EvaluationResult:
    accepted_answers = metadata.get("accepted_answers")
    if not isinstance(accepted_answers, list) or len(accepted_answers) == 0:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail="Exercise metadata is missing accepted_answers",
        )
    if not all(isinstance(value, str) and value.strip() for value in accepted_answers):
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_CONTENT, detail="Exercise metadata is invalid")

    min_matches_raw = metadata.get("min_matches", 1)
    if not isinstance(min_matches_raw, int) or min_matches_raw < 1:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_CONTENT, detail="Exercise metadata is invalid")
    min_matches = min(min_matches_raw, len(accepted_answers))

    response_text = response_payload_json.get("answer")
    if not isinstance(response_text, str) or not response_text.strip():
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail="response_payload_json.answer is required",
        )

    normalized_response = _normalize_short_text_value(response_text)
    normalized_accepted = [_normalize_short_text_value(value) for value in accepted_answers]
    matched_count = sum(1 for phrase in normalized_accepted if phrase in normalized_response)

    is_correct = matched_count >= min_matches
    return EvaluationResult(
        is_correct=is_correct,
        score_awarded=max_score if is_correct else 0,
        feedback="Answer accepted." if is_correct else "Answer is not sufficient yet. Try again.",
        details={
            "exercise_type": "short_text",
            "mode": "deterministic",
            "matched_count": matched_count,
            "min_matches": min_matches,
        },
    )


def evaluate_exercise_submission(
    exercise_type: str,
    metadata_json: str | None,
    response_payload_json: dict[str, Any],
    max_score: int,
) -> EvaluationResult:
    if exercise_type not in SUPPORTED_EXERCISE_TYPES:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail=f"Exercise type '{exercise_type}' is not supported",
        )

    metadata = _parse_metadata(metadata_json)
    if exercise_type == "multiple_choice":
        return _evaluate_multiple_choice(metadata, response_payload_json, max_score)
    if exercise_type == "fill_blank":
        return _evaluate_fill_blank(metadata, response_payload_json, max_score)
    return _evaluate_short_text(metadata, response_payload_json, max_score)
