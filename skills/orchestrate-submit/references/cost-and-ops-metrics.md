---
name: orchestrate-cost-and-ops-metrics
description: Track and report operational metrics — model calls, token usage, cost estimates, runtime, and rate-limit (TPM/RPM) considerations — for a HackerRank Orchestrate submission, a graded requirement in the multi-modal-review challenge. Use when instrumenting an agent's LLM calls, when preparing final approach documentation, or when the interview is likely to ask "how would this scale" or "what does this cost to run."
---

# Orchestrate: Cost and Operational Metrics

**Direct evidence**: the multi-modal-review (June) challenge's evaluation criteria explicitly list *"operational metrics: model calls, token usage, image usage, cost estimates, runtime, and TPM/RPM considerations"* as mandatory analysis. This reflects a broader signal from HackerRank's stated philosophy — evaluating whether a candidate/agent-builder thinks like someone who has to actually operate the system, not just get it to work once.

## What to instrument, concretely

- **Model call count**: total calls made across the full run, broken down by purpose (classification calls vs. retrieval calls vs. validation-retry calls) if your architecture has distinct stages.
- **Token usage**: input and output tokens, ideally per-call-type, summed for the full dataset run.
- **Image usage** (multi-modal challenge specifically): how many images were sent to a vision model, at what resolution/size, since this is often the dominant cost driver in multi-modal pipelines.
- **Cost estimate**: token/image counts × the provider's published per-unit pricing, presented as a real dollar figure for the full run — not just "it uses tokens."
- **Runtime**: wall-clock time for the full dataset, and whether that's dominated by model latency, retrieval, or something else.
- **TPM/RPM considerations**: whether your call pattern would hit a provider's tokens-per-minute or requests-per-minute limit at production scale, and what you'd do about it (batching, backoff, a different model tier).

## Why this belongs in a hackathon submission, not just a production system

This is the clearest evidence in the entire published record that HackerRank is explicitly grading **production-mindedness**, not just "does it work in the demo." A submission that produces a correct `output.csv` with zero visibility into what it cost to produce demonstrates exactly the gap the organizers' broader philosophy pieces describe — treating AI output as a black box to be accepted rather than something to evaluate and reason about operationally.

## Practical implementation

A lightweight wrapper around your model client that increments counters on every call (`calls += 1`, `input_tokens += response.usage.prompt_tokens`, etc.) and dumps a summary at the end of the run is enough — this doesn't need dedicated observability tooling for a 24-hour hackathon, just deliberate tracking rather than none.

## Anti-pattern this prevents

Discovering, only when asked in the interview, that you have no idea how many model calls your system made or what it would cost to run against 10x the data. "I didn't think about that" is a materially worse answer than an approximate number with reasoning behind it — the interview rewards demonstrated awareness of limitations, and cost/scale is one of the most natural places for a real limitation to live.
