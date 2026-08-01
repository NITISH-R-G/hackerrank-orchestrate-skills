---
name: orchestrate-multimodal-evidence-grounding
description: Ground claim-verification decisions in specific, cited visual evidence for HackerRank Orchestrate's multi-modal-review challenge (or any future multi-modal Orchestrate challenge) — mapping each claim verdict back to specific image IDs, classifying severity/risk explicitly, and distinguishing "contradicted" from "not enough information" rather than collapsing them. Use when building the image-to-claim reasoning pipeline, or when writing the claim_status_justification field.
---

# Orchestrate: Multi-Modal Evidence Grounding

**Direct evidence**: the multi-modal-review challenge's required output schema includes `supporting_image_ids` (which specific images support the verdict), `claim_status_justification` (evidence-grounded explanation), and a three-way `claim_status` split between `supported`, `contradicted`, and `not_enough_information` — a structurally different decision space from a binary yes/no.

## Why the three-way split is the core design challenge

Collapsing `contradicted` and `not_enough_information` into one "reject" bucket is the most likely single design mistake in this challenge, because they mean genuinely different things and likely warrant different downstream handling:

- **`contradicted`**: the image evidence actively conflicts with the claim (e.g., claim describes water damage, image shows no visible water damage on the claimed component) — a confident, evidence-backed negative.
- **`not_enough_information`**: the image doesn't clearly show enough to judge either way (wrong angle, too dark, wrong object entirely, image doesn't cover the claimed damage area) — an honest "we can't tell," structurally the same category as the "mark uncertainty" discipline in `orchestrate-failure-handling`, just domain-specific to this challenge.

A system that only ever outputs `supported` or `contradicted`, never `not_enough_information`, is almost certainly over-confident — real claim photos are frequently ambiguous, off-angle, or incomplete, and a system that forces every case into a confident verdict is exhibiting exactly the "guessing instead of marking uncertainty" failure mode the organizers warn against generally.

## Evidence citation, per-verdict

`supporting_image_ids` and `claim_status_justification` together are the schema's evidence-anchoring mechanism — directly analogous to Chakra's own scoring philosophy (traceable to a specific, verbatim moment). A justification like "the image shows clear denting consistent with the claimed impact" citing `image_003` is checkable; "the evidence supports the claim" with no image ID is not, and reads the same way a vague interview answer reads to an evidence-anchored scorer.

## Severity and risk as separate, explicit fields

The schema separates `severity` (none/low/medium/high/unknown) from `risk_flags` — meaning "how bad is the damage" and "is something suspicious about this claim" are different axes that shouldn't be conflated into one confidence score. Build these as genuinely independent classification steps, not derived from each other — a low-severity claim can still carry risk flags (e.g., inconsistency with `user_history.csv`), and a high-severity claim can be entirely legitimate.

## Practical pipeline shape

1. Extract what the claim text asserts (issue type, affected part, described severity)
2. Independently assess what each image actually shows (per-image, not aggregated)
3. Compare assertion against visual evidence, per image, to determine `supporting_image_ids`
4. Roll up to a `claim_status` verdict — with explicit logic for when insufficient image coverage forces `not_enough_information` rather than a forced guess
5. Separately evaluate `risk_flags` against `user_history.csv` and `evidence_requirements.csv`, not folded into the image-comparison step

## Anti-pattern this prevents

A single end-to-end vision-language-model call asked to output the entire schema in one shot with no intermediate reasoning steps exposed. This is the multi-modal analog of the "single LLM call as your entire system" architecture anti-pattern flagged generally — and it's harder to debug or defend in an interview when there's no intermediate reasoning to point to.
