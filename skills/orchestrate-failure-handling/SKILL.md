---
name: orchestrate-failure-handling
description: Design failure handling for a HackerRank Orchestrate agent so failures degrade safely instead of silently — logging failed rows, continuing processing when safe, and explicitly marking uncertainty rather than guessing. Use whenever writing the main processing loop that iterates over tickets/claims, when deciding what happens if one row's model call errors or times out, or when reviewing whether a submission's error handling would survive a full test run without one bad row crashing the whole batch.
---

# Orchestrate: Failure Handling

**Direct evidence**: HackerRank's organizer guidance states plainly — *"Log failed rows. Continue safely when possible. Mark uncertainty when that is the responsible thing to do."* The same post lists **"silent failures"** — letting invalid outputs pass into final results unvalidated — as a named, explicit scoring mistake, alongside **"incomplete testing... don't only inspect successful cases; examine failures and edge cases."*

## The three-part discipline this implies

1. **Log, don't swallow.** Every row that fails — a timeout, a malformed model response after retries exhausted, a missing input file — gets logged with enough detail (row ID, failure reason, timestamp) that you can explain it in the interview without having to reconstruct what happened from memory.
2. **Continue safely, don't halt the batch.** One bad row shouldn't take down the whole run. The processing loop needs a try/except boundary *per row*, not one wrapping the entire batch — a single failure should produce one logged failure and one degraded-but-present output row, not zero output rows for the remaining N-1 tickets.
3. **Mark uncertainty as a first-class output state, not an absence.** When the model genuinely can't determine an answer with confidence, the responsible output is an explicit "uncertain / insufficient evidence" value your schema supports — not a forced guess dressed up as a confident answer, and not a missing row either.

## Why this is scored as architecture, not just robustness

This connects directly to the rubric's stated distinction between "actual agent loops versus hardcoded workflows." A hardcoded workflow with no failure path is a script that works on the happy path and crashes on the first surprise. An agent with designed failure handling demonstrates the same engineering judgment the interview explicitly probes for: "discuss edge cases explicitly: missing data, conflicting signals."

## Concrete implementation checklist

- [ ] Per-row try/except in the main loop, not a single outer try/except
- [ ] A structured failure log (row ID, error type, message) — not just stdout prints that vanish
- [ ] A defined "uncertain" output state distinct from both success and hard-failure
- [ ] The final `output.csv` has a row for every input row — degraded is acceptable, missing is not
- [ ] You can point to the log and explain, specifically, what failed and why during the interview

## Anti-pattern this prevents

"It worked on my test run" as the only evidence of robustness. HackerRank's own advice explicitly separates inspecting successes from inspecting failures — a submission that's never been run against a deliberately broken input (bad file path, empty ticket, malformed corpus entry) hasn't actually tested its failure handling, only assumed it.
