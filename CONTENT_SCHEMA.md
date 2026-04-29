# CONTENT_SCHEMA.md

## Overview

This document is the canonical schema source for question content and response payload validation.

Naming rule:

- Internal storage/domain model use `metadata_json`.
- API responses use `metadata`.
- Both represent the same logical structure.

General requirements:

- Every question has `question_type`, `prompt`, `max_score`, `evaluation_mode`, and metadata.
- Every submitted answer uses `response_payload` and must match the schema for its `question_type`.
- Unsupported fields must be rejected unless explicitly allowed.

---

## 1) `single_choice`

Evaluation mode:

- `deterministic`

Metadata structure (`metadata_json` / `metadata`):

```json
{
  "options": [
    { "id": "a", "label": "OUTPUT" },
    { "id": "b", "label": "INPUT" }
  ],
  "correct_option_id": "b",
  "shuffle_options": false
}
```

Response payload structure:

```json
{
  "selected_option_id": "b"
}
```

Validation rules:

- `options` must contain at least 2 entries.
- Each option `id` must be unique.
- `correct_option_id` must exist in `options`.
- `selected_option_id` must be one of the option ids.

Example:

```json
{
  "question_type": "single_choice",
  "evaluation_mode": "deterministic",
  "metadata": {
    "options": [
      { "id": "a", "label": "Rising edge" },
      { "id": "b", "label": "Falling edge" }
    ],
    "correct_option_id": "a",
    "shuffle_options": false
  },
  "response_payload": {
    "selected_option_id": "a"
  }
}
```

---

## 2) `multiple_choice`

Evaluation mode:

- `deterministic`

Metadata structure (`metadata_json` / `metadata`):

```json
{
  "options": [
    { "id": "a", "label": "GPIO" },
    { "id": "b", "label": "UART" },
    { "id": "c", "label": "HTTP" }
  ],
  "correct_option_ids": ["a", "b"],
  "scoring": {
    "mode": "partial",
    "penalty_per_wrong": 0.25,
    "min_score_ratio": 0.0
  }
}
```

Response payload structure:

```json
{
  "selected_option_ids": ["a", "b"]
}
```

Validation rules:

- `correct_option_ids` must be non-empty.
- `correct_option_ids` values must exist in `options`.
- `selected_option_ids` must be unique.
- `selected_option_ids` values must exist in `options`.
- `penalty_per_wrong` must be in range `0.0..1.0`.

Example:

```json
{
  "question_type": "multiple_choice",
  "evaluation_mode": "deterministic",
  "metadata": {
    "options": [
      { "id": "a", "label": "ADC" },
      { "id": "b", "label": "PWM" },
      { "id": "c", "label": "SQL" }
    ],
    "correct_option_ids": ["a", "b"],
    "scoring": {
      "mode": "partial",
      "penalty_per_wrong": 0.25,
      "min_score_ratio": 0.0
    }
  },
  "response_payload": {
    "selected_option_ids": ["a", "b"]
  }
}
```

---

## 3) `fill_blank_code`

Evaluation mode:

- `deterministic`

Metadata structure (`metadata_json` / `metadata`):

```json
{
  "template": "pinMode({{pin}}, {{mode}});",
  "blanks": [
    { "id": "pin", "expected_values": ["LED_PIN"] },
    { "id": "mode", "expected_values": ["OUTPUT"] }
  ],
  "case_sensitive": true,
  "trim_whitespace": true
}
```

Response payload structure:

```json
{
  "answers": {
    "pin": "LED_PIN",
    "mode": "OUTPUT"
  }
}
```

Validation rules:

- `template` must reference all blank ids.
- `blanks` ids must be unique.
- Each blank must define at least one `expected_values` entry.
- `answers` must include every required blank id.
- No extra blank ids allowed in `answers`.

Example:

```json
{
  "question_type": "fill_blank_code",
  "evaluation_mode": "deterministic",
  "metadata": {
    "template": "digitalWrite({{pin}}, {{value}});",
    "blanks": [
      { "id": "pin", "expected_values": ["LED_PIN"] },
      { "id": "value", "expected_values": ["HIGH"] }
    ],
    "case_sensitive": true,
    "trim_whitespace": true
  },
  "response_payload": {
    "answers": {
      "pin": "LED_PIN",
      "value": "HIGH"
    }
  }
}
```

---

## 4) `order_steps`

Evaluation mode:

- `deterministic`

Metadata structure (`metadata_json` / `metadata`):

```json
{
  "steps": [
    { "id": "s1", "text": "Configure GPIO mode" },
    { "id": "s2", "text": "Read pin value" },
    { "id": "s3", "text": "Apply debounce" }
  ],
  "correct_order": ["s1", "s2", "s3"],
  "scoring": {
    "mode": "position_based"
  }
}
```

Response payload structure:

```json
{
  "ordered_ids": ["s1", "s2", "s3"]
}
```

Validation rules:

- `steps` ids must be unique.
- `correct_order` must contain all and only step ids.
- `ordered_ids` must contain all and only step ids.
- Duplicate ids in `ordered_ids` are invalid.

Example:

```json
{
  "question_type": "order_steps",
  "evaluation_mode": "deterministic",
  "metadata": {
    "steps": [
      { "id": "s1", "text": "Initialize UART" },
      { "id": "s2", "text": "Set baud rate" },
      { "id": "s3", "text": "Transmit byte" }
    ],
    "correct_order": ["s1", "s2", "s3"],
    "scoring": {
      "mode": "position_based"
    }
  },
  "response_payload": {
    "ordered_ids": ["s1", "s2", "s3"]
  }
}
```

---

## 5) `component_selection`

Evaluation mode:

- `deterministic`

Metadata structure (`metadata_json` / `metadata`):

```json
{
  "available_components": ["resistor_220", "led_red", "button", "capacitor_10uF"],
  "required_component_ids": ["resistor_220", "led_red"],
  "min_required": 2,
  "max_allowed": 3
}
```

Response payload structure:

```json
{
  "selected_component_ids": ["resistor_220", "led_red"]
}
```

Validation rules:

- `required_component_ids` must be a subset of `available_components`.
- `selected_component_ids` entries must exist in `available_components`.
- `selected_component_ids` must be unique.
- Count of selected components must satisfy `min_required` and `max_allowed`.

Example:

```json
{
  "question_type": "component_selection",
  "evaluation_mode": "deterministic",
  "metadata": {
    "available_components": ["resistor_220", "led_red", "button"],
    "required_component_ids": ["resistor_220", "led_red"],
    "min_required": 2,
    "max_allowed": 3
  },
  "response_payload": {
    "selected_component_ids": ["resistor_220", "led_red"]
  }
}
```

---

## 6) `connection_graph`

Edges are undirected unless explicitly configured otherwise.
For comparison, evaluators must normalize edge order.
Example: ["a", "b"] and ["b", "a"] are equivalent.

Evaluation mode:

- `deterministic`

Metadata structure (`metadata_json` / `metadata`):

```json
{
  "nodes": ["mcu_pin_13", "resistor_220", "led_anode", "led_cathode", "gnd"],
  "required_edges": [
    ["mcu_pin_13", "resistor_220"],
    ["resistor_220", "led_anode"],
    ["led_cathode", "gnd"]
  ],
  "forbidden_edges": [
    ["mcu_pin_13", "gnd"]
  ],
  "allow_extra_edges": false
}
```

Response payload structure:

```json
{
  "edges": [
    ["mcu_pin_13", "resistor_220"],
    ["resistor_220", "led_anode"],
    ["led_anode", "gnd"]
  ]
}
```

Validation rules:

- Every edge node id must exist in `nodes`.
- Duplicate edges are not allowed.
- All `required_edges` must be present.
- Any `forbidden_edges` present in response causes invalid result.
- If `allow_extra_edges` is `false`, response must not include non-required edges.

Example:

```json
{
  "question_type": "connection_graph",
  "evaluation_mode": "deterministic",
  "metadata": {
    "nodes": ["vcc", "resistor_1k", "led_anode", "gnd"],
    "required_edges": [
      ["vcc", "resistor_1k"],
      ["resistor_1k", "led_anode"],
      ["led_anode", "gnd"]
    ],
    "forbidden_edges": [
      ["vcc", "gnd"]
    ],
    "allow_extra_edges": false
  },
  "response_payload": {
    "edges": [
      ["vcc", "resistor_1k"],
      ["resistor_1k", "led_anode"],
      ["led_anode", "gnd"]
    ]
  }
}
```

---

## 7) `natural_language_ai`

Evaluation mode:

- `ai_assisted` (with deterministic guardrails and fallback)

Metadata structure (`metadata_json` / `metadata`):

```json
{
  "rubric": [
    { "id": "r1", "criterion": "Explains pull-up resistor purpose", "weight": 0.4 },
    { "id": "r2", "criterion": "Mentions current limiting for LED", "weight": 0.6 }
  ],
  "required_concepts": ["pull-up resistor", "current limiting"],
  "max_response_chars": 1000,
  "minimum_confidence": 0.7,
  "fallback_policy": "deterministic_keyword_check"
}
```

Response payload structure:

```json
{
  "answer_text": "A pull-up resistor keeps the pin high when the button is open..."
}
```

Validation rules:

- `rubric` weights must sum to `1.0` (+/- small tolerance).
- `answer_text` must be non-empty and within `max_response_chars`.
- Unsafe or malformed model output must be rejected before scoring.
- If model output fails schema/confidence checks, apply `fallback_policy`.

Example:

```json
{
  "question_type": "natural_language_ai",
  "evaluation_mode": "ai_assisted",
  "metadata": {
    "rubric": [
      { "id": "r1", "criterion": "Explains debounce need", "weight": 0.5 },
      { "id": "r2", "criterion": "Explains floating input risk", "weight": 0.5 }
    ],
    "required_concepts": ["debounce", "floating input"],
    "max_response_chars": 800,
    "minimum_confidence": 0.7,
    "fallback_policy": "deterministic_keyword_check"
  },
  "response_payload": {
    "answer_text": "Without debounce, one press can register as multiple transitions..."
  }
}
```


---

## 8) Phase 1 Lab Exercise Schemas (`exercise_type`)

Compatibility note:
- Existing `question_type` schemas remain valid for challenge-based flows.
- Interactive lab flows in Phase 1 use `exercise_type` schemas below.
- Both models coexist during incremental delivery.

Phase 1 constraints:
- supported `exercise_type`: `multiple_choice`, `fill_blank`, `short_text`
- deterministic evaluation only
- no AI grading
- no code execution/sandbox

Evaluation result field naming for Phase 1 lab attempts:
- canonical response fields are `is_correct`, `score_awarded`, and `feedback`
- `hint` and `explanation` are not result field names in this phase

### 8.1) `multiple_choice` (exercise_type)

Metadata structure (`metadata_json` / `metadata`):
```json
{
  "options": [
    { "id": "a", "label": "GPIO" },
    { "id": "b", "label": "UART" },
    { "id": "c", "label": "HTTP" }
  ],
  "correct_option_ids": ["a", "b"]
}
```

Response payload structure:
```json
{
  "selected_option_ids": ["a", "b"]
}
```

Validation rules:
- `options` must contain at least 2 entries.
- option IDs must be unique.
- `correct_option_ids` must be non-empty and present in `options`.
- `selected_option_ids` must be unique and present in `options`.

### 8.2) `fill_blank` (exercise_type)

Metadata structure (`metadata_json` / `metadata`):
```json
{
  "blanks": [
    { "id": "blank_1", "accepted_answers": ["INPUT_PULLUP", "input_pullup"] },
    { "id": "blank_2", "accepted_answers": ["HIGH"] }
  ],
  "case_sensitive": false,
  "trim_whitespace": true
}
```

Response payload structure:
```json
{
  "answers": {
    "blank_1": "INPUT_PULLUP",
    "blank_2": "HIGH"
  }
}
```

Validation rules:
- blank IDs must be unique.
- each blank must define at least one accepted answer.
- `answers` must include all and only declared blank IDs.

### 8.3) `short_text` (exercise_type)

Metadata structure (`metadata_json` / `metadata`):
```json
{
  "match_type": "keyword_set",
  "required_keywords": ["pull-up", "floating"],
  "forbidden_keywords": [],
  "min_chars": 10,
  "max_chars": 300,
  "case_sensitive": false,
  "trim_whitespace": true
}
```

Response payload structure:
```json
{
  "answer_text": "A pull-up resistor prevents a floating input."
}
```

Validation rules:
- `answer_text` length must be within configured range.
- `required_keywords` must be non-empty when `match_type` is `keyword_set`.
- evaluation is deterministic normalization/keyword matching only.
- no semantic AI interpretation is allowed in Phase 1.

