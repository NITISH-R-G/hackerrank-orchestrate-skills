---
name: orchestrate-input-tracing
description: Trace a single input through every stage of a HackerRank Orchestrate agent pipeline (input loading, context building, model invocation, response parsing, validation, fallback) to verify each stage does what you assume it does. Use as a design self-check right after scaffolding a pipeline, when debugging a specific wrong output, or before trusting an architecture diagram you haven't actually walked through with real data.
---

# Orchestrate: Input Tracing

**Source**: *The Engineer's Notebook*, "Getting better at HackerRank Orchestrate" (Shloka Shah) — the article's recommended self-check framework for verifying a layered agent architecture actually works as designed: pick one input and trace it through the entire system, checking where each stage occurs.

## Why tracing beats reading your own architecture diagram

The article's recommended architecture separates concerns explicitly — input loading & normalization, context building, LLM invocation, response parsing & validation, schema enforcement, retry/error handling, fallback/escalation. It's easy to *draw* that separation and never actually confirm each stage exists as a distinct, checkable step in the running code. Tracing forces the confirmation: pick one real ticket/claim, and for each stage, answer "what did this stage receive, what did it do, what did it hand to the next stage" — concretely, not from memory of what you intended to build.

## The practice

1. Pick one representative input — not a trivial one, one with some real complexity (references multiple corpus documents, or has ambiguous phrasing).
2. At **input loading**: confirm exactly what fields were extracted and normalized. Print or log the parsed representation.
3. At **context building**: confirm exactly which corpus documents/images were retrieved for this input, and why — not just "context was built," but the actual retrieved content.
4. At **LLM invocation**: confirm the actual prompt sent (not the template — the fully rendered prompt with this input's data substituted in).
5. At **response parsing**: confirm what the raw model response looked like, and what your parser extracted from it.
6. At **validation**: confirm which checks ran, and whether they passed or triggered a retry/fallback.
7. At **fallback/escalation** (if triggered): confirm the exact condition that caused it.

If any of these steps is hard to isolate and inspect — if "context building" and "LLM invocation" are tangled into one function you can't separately observe — that's the architecture gap this trace just found, before an interviewer finds it for you.

## What this catches that aggregate testing doesn't

`orchestrate-edge-case-testing` covers running the full dataset and inspecting failures in aggregate. Tracing is complementary and narrower: it verifies the *mechanism* is real for one case, which is often faster at catching "this stage doesn't actually do what I think it does" than staring at a CSV of outputs and reverse-engineering what must have happened internally.

## Interview payoff

This trace, done once deliberately, is exactly what the AI judge interview asks you to reconstruct verbally — "walk me through what happens when a ticket comes in." Having actually done the trace yourself means the answer is a real memory, not an improvisation from the architecture diagram.
