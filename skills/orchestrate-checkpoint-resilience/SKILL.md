---
name: orchestrate-checkpoint-resilience
description: Build checkpoint-and-resume capability into a HackerRank Orchestrate agent's batch processing run, so an API rate limit or crash partway through a full-dataset run doesn't force reprocessing everything from scratch. Use when writing the main loop that processes the full ticket/claim dataset, or after a rate limit or timeout has already forced an expensive full rerun once.
---

# Orchestrate: Checkpoint-and-Resume Resilience

**Source**: first-hand participant case study (Medium, "How I went from 122 to 1 in 24 hours"). After hitting API rate limits mid-run — which forced an expensive full reprocessing pass — the author built deterministic checkpointing after each processed claim, so the next invocation skips already-completed work and resumes exactly where it left off. This is a single, specific, credited technique from a #1-ranked submission, not general HackerRank guidance — cited and labeled as such.

## Why this matters specifically for a 24-hour hackathon

Both Orchestrate challenges process a batch dataset (support tickets or damage claims) through model calls, sometimes involving expensive multi-image vision calls. A rate limit hit at row 400 of 500, with no checkpointing, means either: waiting out the rate limit and reprocessing all 500 rows again (burning time and API budget you don't have much of), or submitting a partial, incomplete `output.csv`. Neither is acceptable with a fixed 24-hour clock and a hard requirement that every input row have an output row (see `orchestrate-failure-handling`).

## The pattern

1. **Persist progress after every row, not at the end.** Write a small state file (or append to a results file directly) recording which input IDs have been fully processed, immediately after each one completes — not batched, not buffered until the end of the run.
2. **On startup, check for existing progress and skip completed work.** The main loop's first action is: load the checkpoint state, filter the input dataset down to unprocessed rows only, and continue from there.
3. **Make the resume deterministic.** The same input, reprocessed, should be identical to what it would have been the first time (this connects to `orchestrate-secrets-and-determinism`'s seeded-randomness requirement) — a checkpoint system built on top of nondeterministic processing produces inconsistent results depending on exactly where a run happened to stop.
4. **Treat a rate-limit error as a distinct, expected failure mode**, not a generic exception. Catch it specifically, back off, and let checkpointing handle the "what's already done" bookkeeping rather than crashing the whole run.

## Minimal implementation shape

```python
processed_ids = load_checkpoint()  # e.g., read a set of IDs from a jsonl file
remaining = [row for row in dataset if row.id not in processed_ids]

for row in remaining:
    try:
        result = process(row)
        append_result(result)
        append_checkpoint(row.id)   # persisted immediately, not batched
    except RateLimitError:
        wait_and_backoff()
        # next invocation picks up exactly here — no reprocessing of completed rows
```

## Why this belongs in the same conversation as cost/ops metrics

`orchestrate-cost-and-ops-metrics` covers *measuring* token usage, call counts, and cost. This skill is about *not wasting* that budget on redundant reprocessing when something interrupts the run — the two are complementary: one tells you what a run costs, the other keeps an interrupted run from costing double.
