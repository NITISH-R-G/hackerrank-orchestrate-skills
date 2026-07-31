---
name: orchestrate-submission-review
description: Final pre-submission checklist for a HackerRank Orchestrate (or similar multi-artifact hackathon) submission — packaging, file format compliance, and the mechanical failure modes that lose points for reasons unrelated to your agent's quality. Use in the final phase before submitting, or whenever the user asks to do a final check / final pass before turning something in.
---

# Orchestrate Submission Review

This is the last gate, and it exists because a meaningful fraction of lost points in any timeboxed contest are **mechanical, not intellectual** — a malformed CSV, a missing file, a zip with the wrong structure, a README that doesn't explain how to run the thing. None of that reflects your agent's quality, and all of it is 100% preventable with a checklist run at a fixed point before the deadline, not "whenever there's time."

## Do this with time to spare, not at the deadline

Run this pass **at least 45–60 minutes before the actual deadline.** Submission portals fail, uploads time out, and a discovered problem at T-minus-10-minutes is a crisis; the same problem at T-minus-60 is a fix.

## Mechanical checks

**The code zip:**
- Does it actually contain everything needed to run the agent, or does it reference local files/paths that only exist on your machine?
- Does a fresh clone/extract + the documented setup steps actually work? (Test this literally — don't assume.)
- Are secrets/API keys excluded, and is there a clear `.env.example` or equivalent instead of a hardcoded key?
- Is there a README, and does it explain **design decisions**, not just run commands? (See `orchestrate-agent-architecture` — this is scored, not cosmetic.)
- Is the zip structured the way the submission instructions ask, or did you guess?

**The output CSV:**
- Does it parse cleanly with a standard CSV reader — no broken quoting, no stray delimiters from unescaped commas in justification text?
- Does the column structure match exactly what was specified (names, order, types)?
- Does every row have a value in every required column — no silent nulls from an unhandled exception mid-run?
- Row count: does it match the number of input tickets? A missing row is worse than a wrong row — it's not partial credit, it's an obvious gap.
- Re-run the full pipeline once, end to end, from a clean state, and diff the output against what you're about to submit. Catches stale/cached output being submitted by accident — a real and common failure.

**The chat transcript:**
- Is it exported in the format requested?
- Does it cover the actual working session, or did an export accidentally capture only part of it?
- Skim the start and end — does it look complete, or does it cut off mid-session?

**General:**
- Did you follow the exact naming/format conventions in the submission instructions? Judges' tooling often parses submissions programmatically — a renamed file can mean it's silently not read at all, which scores as if it doesn't exist.
- Is everything uploaded to the actual right place, under the actual right identity/team, before the actual deadline (accounting for any timezone ambiguity)?

## The fresh-eyes pass

After the mechanical checklist, do one more thing if time allows: **step away for 10 minutes, then re-read your README as if you'd never seen this project.** Does it make sense cold? This catches the "I know what I meant" gap that's invisible to the person who built it and completely visible to a reviewer meeting it for the first time.

## Priority if you're out of time

If the deadline is close and you can't do everything above, do these three, in this order — they're the ones with the highest points-lost-to-effort-required ratio:

1. **Verify the CSV actually parses and has the right row count.** A broken output file can zero out 30% of your score for a reason that has nothing to do with your agent's quality.
2. **Verify the zip runs from a clean extract.** Same logic — a submission that doesn't run can't be evaluated on its merits.
3. **Confirm the upload actually completed** before the deadline, not just that you clicked submit.

Everything else is worth doing, but these three are the ones where a five-minute check prevents a score-destroying, unrelated-to-your-actual-work failure.
