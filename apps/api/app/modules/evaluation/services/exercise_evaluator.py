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
    text = re.sub(r"[\.,;:!?()\[\]{}\-_/'\"`]+", " ", text)
    text = re.sub(r"\s+", " ", text)
    return text.replace(" ", "")


def _normalize_fill_blank_correct_answers(metadata: dict[str, Any]) -> list[list[Any]]:
    correct_answers = metadata.get("correct_answers")
    if not isinstance(correct_answers, list) or len(correct_answers) == 0:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail="Exercise metadata is missing correct_answers",
        )

    # Backward compatible shape:
    # correct_answers: ["output", "high"]
    if all(isinstance(value, (str, int, float)) for value in correct_answers):
        return [[value] for value in correct_answers]

    # New shape with variants per blank:
    # correct_answers: [["output", "out"], ["high", "1"]]
    if all(isinstance(value, list) and len(value) > 0 for value in correct_answers):
        normalized_variants: list[list[Any]] = []
        for variants in correct_answers:
            if not all(isinstance(variant, (str, int, float)) for variant in variants):
                raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_CONTENT, detail="Exercise metadata is invalid")
            normalized_variants.append(variants)
        return normalized_variants

    raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_CONTENT, detail="Exercise metadata is invalid")


def _normalize_short_text_value(value: Any) -> str:
    text = str(value).strip().lower()
    text = re.sub(r"[\.,;:!?()\[\]{}\-_/'\"`]+", " ", text)
    text = re.sub(r"\s+", " ", text)
    return text


_SHORT_TEXT_FILLER_WORDS = {
    "a",
    "an",
    "and",
    "as",
    "at",
    "be",
    "because",
    "by",
    "for",
    "from",
    "helps",
    "i",
    "in",
    "is",
    "it",
    "its",
    "of",
    "on",
    "or",
    "our",
    "so",
    "that",
    "the",
    "their",
    "this",
    "to",
    "too",
    "very",
    "we",
    "with",
}


def _normalize_short_text_token(token: str) -> str:
    normalized = token.strip().lower()
    if not normalized:
        return ""

    if normalized.endswith("ies") and len(normalized) > 4:
        normalized = f"{normalized[:-3]}y"
    elif normalized.endswith("es") and len(normalized) > 4 and not normalized.endswith(("ses", "xes", "zes")):
        normalized = normalized[:-2]
    elif normalized.endswith("s") and len(normalized) > 3 and not normalized.endswith("ss"):
        normalized = normalized[:-1]

    if normalized.endswith("ing") and len(normalized) > 5:
        normalized = normalized[:-3]
    elif normalized.endswith("ed") and len(normalized) > 4:
        normalized = normalized[:-2]

    return normalized


def _short_text_tokens(value: Any) -> list[str]:
    normalized_text = _normalize_short_text_value(value)
    tokens: list[str] = []
    for raw_token in normalized_text.split(" "):
        token = _normalize_short_text_token(raw_token)
        if not token or token in _SHORT_TEXT_FILLER_WORDS:
            continue
        tokens.append(token)
    return tokens


def _response_matches_term(response_tokens: list[str], accepted_term_tokens: list[str]) -> bool:
    if len(accepted_term_tokens) == 0:
        return False

    search_index = 0
    for response_token in response_tokens:
        if response_token == accepted_term_tokens[search_index]:
            search_index += 1
            if search_index == len(accepted_term_tokens):
                return True
    return False


def _evaluate_short_text_concepts(metadata: dict[str, Any], response_tokens: list[str], max_score: int) -> EvaluationResult:
    accepted_concepts = metadata.get("accepted_concepts")
    if not isinstance(accepted_concepts, list) or len(accepted_concepts) == 0:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail="Exercise metadata is missing accepted_concepts",
        )

    normalized_concepts: list[dict[str, Any]] = []
    for concept in accepted_concepts:
        if not isinstance(concept, dict):
            raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_CONTENT, detail="Exercise metadata is invalid")
        concept_id = concept.get("id")
        accepted_terms = concept.get("accepted_terms")
        if not isinstance(concept_id, str) or not concept_id.strip():
            raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_CONTENT, detail="Exercise metadata is invalid")
        if not isinstance(accepted_terms, list) or len(accepted_terms) == 0:
            raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_CONTENT, detail="Exercise metadata is invalid")
        if not all(isinstance(term, str) and term.strip() for term in accepted_terms):
            raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_CONTENT, detail="Exercise metadata is invalid")

        normalized_concepts.append({"id": concept_id, "accepted_terms": accepted_terms})

    min_concepts_raw = metadata.get("min_concepts", 1)
    if not isinstance(min_concepts_raw, int) or min_concepts_raw < 1:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_CONTENT, detail="Exercise metadata is invalid")
    min_concepts = min(min_concepts_raw, len(normalized_concepts))

    matched_concept_ids: list[str] = []
    for concept in normalized_concepts:
        concept_terms = concept["accepted_terms"]
        has_match = False
        for term in concept_terms:
            accepted_term_tokens = _short_text_tokens(term)
            if _response_matches_term(response_tokens, accepted_term_tokens):
                has_match = True
                break
        if has_match:
            matched_concept_ids.append(concept["id"])

    matched_count = len(matched_concept_ids)
    is_correct = matched_count >= min_concepts
    feedback = (
        "Good explanation. Your answer captures the key safety concept(s)."
        if is_correct
        else "Not quite yet. Focus on safety purpose, like controlling current and protecting components."
    )
    return EvaluationResult(
        is_correct=is_correct,
        score_awarded=max_score if is_correct else 0,
        feedback=feedback,
        details={
            "exercise_type": "short_text",
            "mode": "deterministic",
            "matched_count": matched_count,
            "min_concepts": min_concepts,
            "matched_concept_ids": matched_concept_ids,
        },
    )


def _evaluate_short_text_legacy(metadata: dict[str, Any], response_tokens: list[str], max_score: int) -> EvaluationResult:
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

    matched_count = 0
    for phrase in accepted_answers:
        phrase_tokens = _short_text_tokens(phrase)
        if _response_matches_term(response_tokens, phrase_tokens):
            matched_count += 1

    is_correct = matched_count >= min_matches
    feedback = (
        "Good explanation. Your answer captures the key safety concept(s)."
        if is_correct
        else "Not quite yet. Focus on safety purpose, like controlling current and protecting components."
    )
    return EvaluationResult(
        is_correct=is_correct,
        score_awarded=max_score if is_correct else 0,
        feedback=feedback,
        details={
            "exercise_type": "short_text",
            "mode": "deterministic",
            "matched_count": matched_count,
            "min_matches": min_matches,
        },
    )


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
    correct_answers = _normalize_fill_blank_correct_answers(metadata)

    submitted_answers = _extract_fill_blank_answers(response_payload_json)
    incorrect_indices: list[int] = []
    correct_count = 0
    total_blanks = len(correct_answers)

    for index, expected_variants in enumerate(correct_answers):
        provided = submitted_answers.get(index)
        normalized_provided = _normalize_fill_blank_value(provided)
        normalized_expected_variants = {_normalize_fill_blank_value(expected) for expected in expected_variants}
        if normalized_provided in normalized_expected_variants:
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
    response_text = response_payload_json.get("answer")
    if not isinstance(response_text, str) or not response_text.strip():
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail="response_payload_json.answer is required",
        )

    response_tokens = _short_text_tokens(response_text)

    if "accepted_concepts" in metadata:
        return _evaluate_short_text_concepts(metadata=metadata, response_tokens=response_tokens, max_score=max_score)
    return _evaluate_short_text_legacy(metadata=metadata, response_tokens=response_tokens, max_score=max_score)


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
