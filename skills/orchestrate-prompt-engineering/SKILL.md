---
name: orchestrate-prompt-engineering
description: Write prompts for a HackerRank Orchestrate agent with the same engineering rigor as code — explicit allowed-output specifications, required-evidence framing, and format requirements, treating the prompt as a reviewable artifact rather than throwaway text. Use whenever writing or revising a system/task prompt for the agent, or when reviewing whether prompts would survive being read by an interviewer as carefully as the code will be.
---

# Orchestrate: Prompt Engineering as a Reviewed Artifact

**Direct evidence**: HackerRank's guidance states this directly — *"Write prompts with same care as code—specify allowed outputs, required evidence, format requirements."* This sits under "Code Quality," meaning prompts are implicitly graded as part of that 30%, not treated as separate from "real" engineering.

## What "same care as code" concretely means

A prompt written with code-level rigor has the same properties good code has:

- **Explicit allowed outputs.** Not "classify the ticket" but "classify as exactly one of: `product_issue`, `feature_request`, `bug`, `invalid` — no other values." This is the prompt-side half of `orchestrate-schema-guardrails`'s validation-side guardrail; the two should agree exactly.
- **Required evidence, stated as a constraint, not a hope.** "Ground your response only in the provided corpus documents; if no relevant document exists, say so explicitly rather than answering from general knowledge" — directly enforcing the "must use only the provided support corpus" hard constraint and preventing hallucinated policy citations, which the starter repo names as something to avoid.
- **Format requirements stated precisely.** If you need JSON, specify the exact keys and types, not "respond in JSON." If you need a justification under a certain length, say so — vague format instructions produce vague, inconsistently-parseable output.

## Treat prompts as versioned, readable files — not inline strings

Per `orchestrate-naming-and-structure`, prompts belong in their own module (`prompts.py`, `prompts/*.txt`), not embedded as multi-line strings buried inside the agent loop's control flow. A reviewer — human or interviewer — should be able to open one file and read every prompt the system uses, the same way they'd read your validation logic.

## The review test

Read your own prompt back as if you were a stranger with no context. Could you, from the prompt text alone, write the validator that checks its output? If the prompt says "classify appropriately" and your validator separately enforces a strict enum, there's a mismatch — the prompt is under-specifying what the validator over-specifies, and the gap is exactly where the model will produce output your guardrails have to catch (and sometimes won't).

## Anti-pattern this prevents

A single sprawling system prompt trying to do retrieval instructions, classification rules, tone guidance, and output formatting all at once, revised ad hoc by trial and error with no record of what changed or why. This is the prompt-engineering equivalent of the "single LLM call as your entire system" architecture anti-pattern — and it's just as visible to an interviewer who asks "walk me through your prompt design" as bad code structure is to a code reviewer.
