---
name: orchestrate-ai-collaboration-transcript
description: Working with an AI coding assistant in a way that produces a strong, scorable chat transcript — visible planning, explicit constraints, real debugging dialogue, deliberate iteration. Use continuously throughout any session where the transcript itself will be evaluated (HackerRank Orchestrate's AI chat transcript signal, or any process similarly graded on how AI tools were directed rather than only on the output). This is a standing discipline, not a one-time checklist — apply it to how you write every prompt, not just at the end.
---

# Orchestrate AI Collaboration Transcript

HackerRank's published philosophy is explicit that the target has shifted: *"stop measuring whether a candidate can work without AI, and start measuring whether they can work well with it."* The chat transcript signal (10% of Orchestrate's score) is the direct instrument for that — and it evaluates **"planning, constraint-setting, debugging, and iteration patterns rather than the final product itself."**

This is the one signal that cannot be fixed retroactively. It's a record of your actual process, not an artifact you produce at the end. Everything here is about *how to prompt*, applied from message one.

## What a weak transcript looks like

A transcript that reads like a vending machine: terse requests, accepted output, no visible reasoning.

> "write a function to classify tickets"
> *(accepts output)*
> "now add escalation logic"
> *(accepts output)*
> "fix this error"
> *(pastes traceback, accepts fix)*

Technically this could produce working code. It demonstrates nothing about planning, judgment, or debugging skill — because none of that is visible. If the transcript is graded on *process*, a transcript with no visible process caps out low regardless of the final code quality.

## What a strong transcript looks like

The same work, with the reasoning made explicit:

> "Before implementing: I want the agent to decide per-ticket whether to search the KB again with a refined query, rather than doing one fixed retrieval. Reasoning: the KB is 774 docs and a single embedding search will miss cases where the right doc uses different terminology than the ticket. Plan: retrieval as a tool the agent can call multiple times, capped at 3 calls, with the agent deciding when it has enough. Does this fit a ReAct-style loop cleanly, or is there a simpler structure for this specific case?"

This single message demonstrates: a design decision, the reasoning behind it, an explicit constraint (the cap), and an invitation for the tool to push back. That's plan visibility, and it's exactly what the philosophy piece says is being measured: *"can this person plan a solution, direct an AI assistant, evaluate what it produces, and ship something that works."*

## The four things to make visible, deliberately

**1. Planning — state the plan before asking for code.**
Don't ask for a function in isolation; state what it's for, what the alternatives were, and why you're picking this approach. A one-paragraph rationale before a code request costs 30 seconds and converts an invisible decision into a scored one.

**2. Constraints — state them explicitly, don't rely on the tool guessing.**
"Keep this under 50 lines," "no new dependencies," "must handle the case where the KB search returns nothing" — constraints are evidence of judgment about what matters. An unconstrained request that happens to produce good output hides that judgment.

**3. Debugging as dialogue, not a paste-and-accept loop.**
When something breaks, articulate your hypothesis before asking the tool to fix it: "This is returning None on the third ticket — my guess is the KB search is returning an empty list and we're not handling that case. Can you confirm and fix, or tell me if you see a different cause?" This demonstrates the debugging methodology itself, not just that a bug got fixed. Compare to `systematic-debugging` and `diagnosing-bugs` in this collection — the same discipline, made visible in the transcript rather than only in your head.

**4. Iteration — show you evaluated output critically, not just accepted it.**
When output isn't quite right, say what's wrong and why, not just "no, different." "This handles the happy path but the escalation threshold is hardcoded — I want it derived from the confidence score instead, because a fixed threshold is exactly the kind of thing that'll misfire on edge cases we haven't seen." Rejecting or revising output *with stated reasoning* is the highest-signal moment in a transcript, because it's the clearest evidence you're evaluating rather than accepting.

## The discipline this requires

None of the above is about writing *more* — a padded, verbose transcript is not the goal, and artificially inflating messages with reasoning that isn't real is both obvious to a reviewer and a waste of your limited time. The discipline is: **when you're already making a decision, say the decision out loud instead of only acting on it.** You're doing the reasoning anyway; the transcript technique is just not hiding it.

Concretely: pause before sending a request and ask "if someone read only this message, would they know why I'm asking for this?" If the answer is no, that's the sentence to add.

## What NOT to do

- **Don't retroactively narrate.** Padding an already-completed session with fake planning messages after the fact reads as exactly what it is, and dishonest self-presentation is the opposite of the "self-awareness" trait being scored elsewhere in this same evaluation.
- **Don't perform for the transcript at the expense of actually building.** A transcript full of eloquent planning attached to a broken agent scores badly everywhere else — this is 10% of the score, not the whole thing. See `orchestrate-phase-gates` for time allocation.
- **Don't over-explain trivial requests.** Constraint-stating and reasoning are for decisions that matter. "Fix this typo" doesn't need a paragraph. Reserve the discipline for moments where judgment is actually being exercised.

## Beyond the contest

This is, without qualification, just how effective AI-assisted engineering works — the entire premise of `grill-with-docs`, `grilling`, and `writing-plans` elsewhere in this collection is that making planning and reasoning explicit produces better outcomes, independent of whether anyone is grading the transcript. Orchestrate scores a skill worth having regardless.
