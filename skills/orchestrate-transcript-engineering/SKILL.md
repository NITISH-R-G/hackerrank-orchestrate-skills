---
name: orchestrate-transcript-engineering
description: Score a chat transcript against HackerRank's published AI Chat Transcript rubric, and generate prompts that demonstrate the behaviors it rewards -- direction/ownership, technical specificity, iteration/verification, safety awareness. Use before submitting, or at the start of a build to prompt yourself better from turn one.
---

# Orchestrate: Transcript Engineering

**Evidence tier: HackerRank's own published methodology** ("Behind the
Scenes of HackerRank Orchestrate," hackerrank.com, June 2026) for the
rubric weights and dimensions — quoted numbers, paraphrased descriptions,
cited, not reproduced. **First-hand** for the pattern-detection heuristics
and the honesty boundary they carry, built and tested inside this
repository, same discipline as `orchestrate_kit/judge/scoring.py`.

## The realization this skill is built on

HackerRank's own writeup states plainly: the AI Chat Transcript score
measures how the **human directed the coding agent**, not what the agent
produced. A transcript full of working code with no visible direction
still scores low on this axis — and it's the highest-weighted rubric this
skill covers (35% for Direction & Architecture Ownership alone).

That means transcript quality is a **separate optimization target** from
code quality, and it's addressable the same way this repository addresses
everything else: measure the gap, build the tool, verify it discriminates.

## What this is not

Not a prediction of your real HackerRank score. **No ground-truth graded
transcript exists to calibrate against** — `orchestrate transcript
analyze` scores the *shape* of a transcript (ownership language, named
alternatives, reported measurements, named risk mechanisms), the same
honesty boundary `orchestrate interview` already states for spoken
answers. A transcript claiming "I measured X" scores the same whether X
was actually measured or invented. Use it as a self-review checklist, not
a scoreboard.

**Stated plainly, found by actually trying to break it, not assumed
safe:** the analyzer is regex pattern-matching, which means it can be
gamed by stuffing rubric-matching phrases into a transcript with no real
engineering behind them. A repetition penalty closes the cheapest version
of that (three copies of one boilerplate sentence dropped from 86 to 50
once the penalty landed), but a determined, novel-phrasing gamer could
still beat pattern-matching that isn't checking truth, only shape. This
is not a solved problem — it's the same honesty boundary every heuristic
text analyzer in this project states (`judge/scoring.py`'s docstring says
it explicitly too): it trains form, truth is your job, and a fluent
answer full of invented specifics scores well here and would fail a real
technical follow-up.

## Coverage against the published rubric

| Rubric dimension | Coverage | Why |
|---|---|---|
| Direction & architecture ownership | **Partial** | Detects ownership language and named alternatives; cannot verify the alternative was genuinely considered, not invented after the fact |
| Technical specificity & constraint | **Partial** | Detects named entities and stated constraints; cannot verify a named model/library was actually used correctly |
| Iteration & verification | **Partial** | Detects reported measurements and reversals; cannot verify a claimed test was actually run |
| Safety, edge case & quality awareness | **Partial** | Detects named risks and mechanisms; cannot verify the mechanism actually exists in the code |
| Genuine semantic understanding of *whether a claim is true* | **Impossible without an LLM call** (and even then, unverified without the actual repository + a real grading model) — explicitly not attempted, not faked |
| A trained scoring model calibrated to real HackerRank grades | **Impossible without ground-truth graded transcripts**, which don't exist publicly — explicitly not attempted, not faked |
| Multi-turn conversation-level reasoning (e.g. does turn 8 contradict turn 3) | **Missing** — the analyzer scores the transcript as one block of text, not turn-by-turn. Buildable without an LLM (a real gap, not declined on principle) — see `ROADMAP.md` |

## Commands

```bash
orchestrate transcript analyze <chat-log.txt>
orchestrate transcript compose "choose a retrieval method" --stage design
orchestrate transcript blueprints
```

## The four dimensions, and what actually demonstrates each one

| Dimension | Weight | What scores well | What scores low |
|---|---:|---|---|
| Direction & architecture ownership | 35% | "I chose X over Y because Z" — a named alternative and a reason | "the agent decided" / accepting every suggestion |
| Technical specificity & constraint | 25% | Real model/library/path/threshold names in the instruction | "make it better," no named constraint |
| Iteration & verification | 25% | A reported measurement, a regression named and reverted | No evidence any output was ever inspected |
| Safety, edge case & quality awareness | 15% | A named mechanism ("the gate runs before the model") | A stated goal with no mechanism ("it should be safe") |

## Nine prompt blueprints (`orchestrate transcript blueprints`)

Each one is built to make the rubric's own scoring criteria the literal
output format of your next message — e.g. `architecture-tradeoff` forces
your reply to be "here's what I chose and what I rejected," which is
exactly the Direction dimension's top signal. `orchestrate transcript
compose` fills a blueprint with your real inputs and surfaces related
Engineering Memory, so the generated prompt naturally cites what this (or
your own) project already measured and rejected — the same "prior art"
principle `orchestrate mentor` applies to code changes, applied here to
how you *talk about* code changes.

## The one published finding worth internalizing before you start

HackerRank's own interview-scoring analysis found turn count had a
**weak negative correlation** with score, while answer depth and
specificity correlated strongly (their published figures: r≈0.615 for
word count, r≈0.583 for specificity). `orchestrate transcript analyze`
surfaces the same signal for chat transcripts: a long, padded log with a
low score gets flagged explicitly, because more turns is not the fix —
depth per turn is.

## Related

[`orchestrate-ai-collaboration-transcript`](../orchestrate-ai-collaboration-transcript)
— the general-purpose skill for prompting well during the build itself.
This one is the executable, tested version: a real scorer and a real
generator, not prose alone.
