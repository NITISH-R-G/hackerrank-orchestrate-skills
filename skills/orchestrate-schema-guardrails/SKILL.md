---
name: orchestrate-schema-guardrails
description: Build validation guardrails around every LLM-generated field before it reaches output.csv in a HackerRank Orchestrate submission — schema validation, rejecting unsupported label values, and retry-on-malformed-output. Use this whenever writing the code path that turns a model response into a CSV row, when an agent's output occasionally doesn't match the expected schema, or before finalizing output validation for any Orchestrate challenge (support-agent, multi-modal-review, or future ones).
---

# Orchestrate: Schema Guardrails

**Direct evidence**: HackerRank's own "Getting better at Orchestrate" post names this explicitly as recommended practice — *"Build guardrails around LLM outputs—validate schemas, reject unsupported labels, retry malformed responses."* This is not inferred; it's stated advice from the organizers.

## Why this is scored, not just good practice

Every Orchestrate challenge defines a fixed output schema (`status` ∈ {replied, escalated}, `request_type` ∈ {product_issue, feature_request, bug, invalid} for the support challenge; `claim_status` ∈ {supported, contradicted, not_enough_information} for the multi-modal challenge). An LLM will occasionally emit a value outside that set — a synonym, a slightly different casing, an extra field. Left unguarded, that becomes a malformed row in `output.csv`, which is graded mechanically against a golden dataset. A malformed row doesn't get "partial credit for being close" — it's either wrong or it breaks the grading script's parse.

## The guardrail pattern

1. **Define the schema once, in code, not in a prompt comment.** An enum/constant list the validator imports — not a string embedded in the prompt that the validator has no way to check against.
2. **Validate every model response against it before writing a row.** Check required fields are present, enum fields are in the allowed set, and free-text fields aren't empty when required.
3. **On failure, retry with the failure fed back to the model** — "you returned `status: closed`, which isn't a valid value; valid values are `replied` or `escalated`" — rather than silently coercing or discarding.
4. **Cap retries and have a defined fallback** (see `orchestrate-failure-handling` for what that fallback should be — never a silent guess).

## What this looks like in review

An interviewer or code reviewer who opens your validation module should immediately see: the schema, the check, the retry, the fallback. If that logic is scattered across the codebase or absent entirely — if a bad model response can reach `output.csv` unfiltered — that's a concrete, checkable gap, not a matter of opinion.

## Anti-pattern this prevents

Trusting `response_format={"type": "json_object"}` or a Pydantic model alone to guarantee schema compliance. Structured-output modes reduce malformed responses; they don't eliminate the case where the model chooses a *syntactically valid but semantically wrong* enum value (e.g., a plausible-sounding but non-existent `request_type`). The guardrail has to check values, not just shape.
