# Self-Scoring Heuristic

**This is an evidence-informed heuristic based on publicly available HackerRank material — not a reproduction of HackerRank's internal scoring system, which is not public.** Use it to self-audit before submission, not as a guarantee of any particular score. Where a line item is a direct quote or requirement from official sources, it's marked **[evidence]**. Where it's a reasonable inference from that evidence, it's marked **[inference]**.

Score yourself 0-3 on each line (0 = not present, 1 = attempted but weak, 2 = present and solid, 3 = clearly excellent) and read the pattern, not the sum — a 2.9 average with one 0 is a bigger risk than a flat 2.0 average, because the organizers' own framing ("no single metric reproduces the leaderboard") implies balance matters more than any one peak.

## Code (target weight: ~30%, per the May event's published breakdown) **[evidence: weight]**

| Check | Evidence basis |
|---|---|
| Real agent loop — the model decides what happens next, not a fixed if/else tree with LLM calls embedded | **[evidence]** "actual agent loops versus hardcoded workflows" named directly in the rubric |
| Concerns separated: input loading / prompts / agent logic / validation / evaluation each in their own module | **[evidence]** direct organizer quote |
| Every file name is specific to its contents — no `helper.py`/`utils.js` | **[evidence]** direct organizer quote, named as a mistake when absent |
| README lets a stranger find the entry point and understand the main flow in under a minute | **[evidence]** direct organizer quote |
| No hardcoded secrets or local absolute paths anywhere in the code | **[evidence]** direct organizer quote + starter repo hard constraint |
| Deterministic output — same input produces the same output across runs | **[evidence]** starter repo hard constraint |

## Architecture & Robustness **[inference from rubric + dataset design]**

| Check | Evidence basis |
|---|---|
| Escalation logic is category-based (high-risk / sensitive / unsupported), not a single confidence threshold | **[evidence]** starter repo names these three categories explicitly |
| Tested against deliberately adversarial cases (prompt injection, jailbreak-style input), not just clean happy-path input | **[evidence]** organizer description of the dataset's design intent |
| Neither "escalate everything" nor "respond to everything" — genuinely calibrated in between | **[evidence]** explicitly stated as the failure mode both extremes hit |
| Output guardrails validate schema and retry on malformed model output, not just hope for compliant JSON | **[evidence]** direct organizer quote |

## Output Correctness & Justification (target weight: ~30%) **[evidence: weight]**

| Check | Evidence basis |
|---|---|
| Every output row has a specific, evidence-citing justification — not a generic template reused across rows | **[inference]** from Chakra's stated evidence-anchored scoring philosophy, extended by analogy |
| Justifications reference specific corpus documents / image IDs that actually exist (no hallucinated citations) | **[inference]** direct extension of "must use only the provided corpus," "avoid hallucinated policies" |
| Full CSV present — every input row has a corresponding output row, including failed/uncertain cases | **[evidence]** "silent failures" named as a mistake |
| At least two implementation strategies were compared against the sample dataset with documented reasoning for the final choice | **[evidence]** explicit requirement in the June (multi-modal) challenge; **[inference]** worth doing regardless of challenge |

## AI Collaboration / Chat Transcript (target weight: ~10%) **[evidence: weight]**

| Check | Evidence basis |
|---|---|
| Transcript shows visible planning before implementation starts, not just immediate code requests | **[evidence]** direct organizer recommendation |
| Transcript shows you reviewing AI-generated code and pushing back on unnecessary complexity at least once | **[evidence]** direct organizer recommendation |
| Transcript shows real errors encountered and your reasoning for the fix, not just successful first-try generations | **[evidence]** direct organizer recommendation |
| Uses the AGENTS.md format the platform expects | **[evidence]** direct organizer recommendation |

## Interview Readiness (target weight: ~30%, per the May event's published breakdown) **[evidence: weight]**

| Check | Evidence basis |
|---|---|
| Can explain the architecture, validation logic, and failure paths without notes | **[evidence]** direct organizer recommendation |
| Has 2-3 specific, nameable edge cases ready to discuss (not "I handled edge cases generally") | **[evidence]** direct organizer recommendation; **[inference]** from Chakra's evidence-anchored scoring — specificity is what scores, vagueness doesn't |
| Can name at least one real limitation of the system honestly, with specifics | **[evidence]** direct organizer recommendation; **[inference]** extended from Chakra's self-awareness scoring in the general interview philosophy pieces |
| Answers are grounded in decisions actually made during building, not fabricated post-hoc for the interview | **[inference]** from Chakra's "nothing is inferred beyond what's in the transcript" — an evidence-anchored scorer is built to catch exactly this gap |

## Operational Awareness **[evidence: June-challenge requirement, generalized by inference]**

| Check | Evidence basis |
|---|---|
| Model call count, token usage, and an estimated dollar cost for a full run are known and documented | **[evidence]** explicit requirement in the June (multi-modal) challenge |
| Runtime and any rate-limit (TPM/RPM) considerations are documented | **[evidence]** explicit requirement in the June (multi-modal) challenge |

---

**How to use this**: run through it honestly with real evidence for each line (a file path, a transcript excerpt, a specific test case) rather than a gut-feel score. If you can't point to concrete evidence for a "3," it's probably a "1" or "2" — the same discipline the evidence-anchored scorer itself applies to you.
