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
