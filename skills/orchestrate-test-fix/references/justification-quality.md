---
name: orchestrate-justification-quality
description: Writing agent decision justifications that are scored well — evidence-anchored, specific, calibrated, and honest about uncertainty. Use whenever an agent must explain or justify a decision it made (an escalation, a classification, a refusal), when producing an output file that includes reasoning alongside verdicts, or when reviewing agent output for reasoning quality rather than just correctness.
---

# Orchestrate Justification Quality

Two published facts should shape how you treat this:

1. The Orchestrate output rubric evaluates **"whether agents provide sound justifications for decisions"** — the CSV is not scored on verdicts alone.
2. HackerRank's Chakra scoring engine is **evidence-anchored**: *"every score traces back to a specific, verbatim moment in the transcript"* and *"nothing in the report is inferred beyond what's in the transcript."*

Point 2 is about their interview scorer, not your CSV — but it reveals the evaluation philosophy of the organization designing your rubric. **They score specific, traceable evidence and refuse to credit vague generalities.** Write your agent's justifications for a reader with that disposition.

## The Chakra rubric, read as a writing guide

Chakra's 4-point scale, translated into what it implies about output quality:

| Score | Chakra's criterion | What that means for a justification |
|---|---|---|
| 3 — Met | "clarity, ownership, structured reasoning, specific examples" | Names the specific evidence, states the decision rule, commits to the call |
| 2 — Partially met | "relevant evidence but lacking depth or specificity" | Gestures at the right reason without citing what actually drove it |
| 1 — Not met | "incorrect reasoning or only vague, theoretical responses" | Generic filler that could apply to any ticket |
| 0 — Not assessed | no relevant evidence exists | Empty or off-topic |

The gap between a 2 and a 3 is almost entirely **specificity**. That's the cheapest available improvement in the entire rubric.

## What a weak justification looks like

> "This ticket appears to require escalation based on its content and complexity."

Nothing here is wrong. Nothing here is *evidence*, either. It could be pasted onto any of the 29 tickets without modification — which is exactly the tell. If a justification is portable across cases, it justified nothing.

## What a strong one looks like

> "Escalated. The customer reports being charged twice for order #4471 on 2026-03-14. KB doc `billing-refunds-v3` covers single-charge refunds but explicitly routes duplicate-charge cases to the billing team (§4.2) because they require ledger access the agent doesn't have. No KB document covers duplicate charges directly."

What's doing the work:
- **Specific evidence from the input** (order number, date, the actual complaint)
- **Specific evidence from the knowledge base** (named document, named section)
- **The decision rule that connects them** (KB explicitly routes this class of case)
- **The gap acknowledged** (no doc covers this directly) — honest, not padded

## The structure worth defaulting to

For each decision, answer four things in order:

1. **Verdict** — the decision, stated first, unhedged.
2. **Evidence from input** — what in this specific ticket drove it.
3. **Evidence from knowledge** — which KB doc/policy applies, named.
4. **The rule** — why that evidence implies that verdict.

Add a fifth when it applies: **what you're uncertain about**. This is not a weakness; see below.

## Calibrated uncertainty is a scored strength

The interview rubric explicitly evaluates **"self-awareness regarding system limitations."** The same disposition applies to output. An agent that says:

> "Escalated. Low confidence — the ticket mentions both a password reset (covered by `auth-selfserve-v2`) and a possible account compromise (not covered). Escalating on the compromise signal since the security risk dominates; the reset alone would have been answerable."

...has demonstrated more judgment than one that escalates with false confidence. **Hedging is bad; calibration is good** — the difference is that calibration names *what specifically* is uncertain and *what it decided anyway*.

What to avoid: uncertainty as filler ("this may or may not require escalation depending on various factors"). That's a 1, not a 3.

## Making the agent actually do this

Justification quality is a prompt-engineering outcome, not a post-processing one:

- **Require the structure in the output schema.** If your schema is `{action, justification}` you'll get prose. If it's `{action, ticket_evidence, kb_reference, decision_rule, confidence, uncertainty_note}` you get structure, and you can concatenate it into a justification field at write time.
- **Force a KB citation field.** An agent required to name a document is an agent that must actually retrieve one — this also surfaces hallucinated citations, since you can validate the doc ID exists.
- **Validate citations programmatically.** If `kb_reference` isn't a real document ID, that's a caught hallucination. This check costs ten lines and is a strong thing to mention in the interview.
- **Give the model an explicit "insufficient information" path.** Without one, you're forcing confabulation on the tickets where the honest answer is "not covered."

## Review pass before submission

Read a random sample of your own output rows — 5 is enough to find systemic problems:

- Could this justification be pasted onto a different ticket unchanged? (If yes → it's generic, score 2 at best.)
- Does it cite specific evidence from the input?
- Does it cite a KB document, and **does that document actually exist**?
- Does the stated reasoning actually support the verdict, or does it describe the ticket and then jump to a conclusion?
- Where the agent was genuinely uncertain, did it say so, or did it fake confidence?

The "describe then jump" pattern is the most common real failure: a paragraph accurately summarizing the ticket, followed by a verdict with no connecting logic. Summary is not justification.

## Beyond the contest

Every production agent making consequential decisions needs this — an escalation, a content moderation call, a fraud flag. The audit trail *is* the product in regulated contexts, and "specific evidence + explicit rule + named uncertainty" is the shape that survives an actual audit. See `engineering-culture` in this collection on blameless postmortems for the same evidence-over-assertion discipline applied to incidents.
