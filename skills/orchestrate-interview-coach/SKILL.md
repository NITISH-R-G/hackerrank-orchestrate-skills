---
name: orchestrate-interview-coach
description: Prepare for the AI judge interview: know your constants, state boundaries, and never claim what the repository cannot support. Use in the hours before the interview and when writing any defensive documentation.
---

# Orchestrate: Interview Coach

**Evidence tier: first-hand build (August 2026).** Grounded in a completed Orchestrate submission that was audited to destruction — 48 logged defects, 9 measured-and-rejected optimisations, 17 certification scripts. Every number below was measured on that system. Nothing here claims access to HackerRank's internal scoring.

## The single highest-value preparation

**Know your constants.** Direct feedback from an actual Orchestrate AI judge:

> *"Owning every number in your code is part of owning the decision."*

The criticism came after a deep, otherwise-positive technical discussion. The
participant could not recall the retrieval hyperparameters they had shipped.

Build a `CONSTANTS.md` with a **provenance** column before the interview:

| Provenance | Meaning | How to answer |
|---|---|---|
| MEASURED | an experiment chose it; another value scored worse | give the number *and* the losing alternative |
| SPEC | fixed by the problem statement or observed labels | cite the line |
| STANDARD | a canonical value from the literature, **not tuned by you** | say exactly that |
| BOUND | derived from an external standard | cite the standard |
| JUDGEMENT | reasoned, not measured | say so, and give the reasoning |

**Why the provenance column matters more than the numbers.** Claiming "chosen after
evaluation" for a value you took from a textbook is a fabrication that collapses under
one follow-up ("show me the sweep"). The strong answer is:

> *"Those are the canonical defaults. I deliberately did not tune them — tuning two
> hyperparameters against 28 labeled rows is how you overfit a hidden set."*

That converts the weakest point into a demonstration of discipline.

## What judges reward

Observed in a real interview: the judge closed by praising *"measuring your own
assumptions and being willing to reject changes that didn't improve things."*

So lead with your **rejections**. "We use embeddings" is a claim anyone can make.
"We measured embeddings at F1 0.479 against 0.512 for lexical and did not ship them"
cannot be faked.

## Never say these

Each is unprovable unless your repository specifically supports it:

1. "I committed incrementally" — check your git log first; one squashed commit is common
2. "I wrote every line myself" — if you used an AI assistant, say so; most rules explicitly allow it
3. "My system is deterministic" — unqualified, this is usually false; state the boundary
4. "OCR improves my score" — only if you measured it; it may be 0 impact
5. "I get 100%" — say *on which set*, and how many rows that is
6. "My retrieval is optimal" — "Pareto-optimal among N tested configurations" is the defensible version
7. "No dataset-specific assumptions exist" — say "I hunted them and removed the ones I found"

## Structure for a hard question

1. **Claim** — one sentence
2. **Evidence** — the measurement and where it lives
3. **Boundary** — where it stops being true
4. **Alternative** — what you rejected and why

## The checklist

- [ ] `CONSTANTS.md` written, with provenance
- [ ] Rejection log memorised — three examples with numbers
- [ ] Every guarantee has a stated boundary
- [ ] Limitations volunteered *before* being asked
- [ ] `git log` actually read before describing your process
- [ ] "I don't remember" rehearsed — it beats inventing a number
