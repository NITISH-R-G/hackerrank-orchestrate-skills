# The Orchestrate Intelligence Layer

Eight skills for maximizing performance in HackerRank Orchestrate — and, not incidentally, for building genuinely better AI agents regardless of who's grading.

## A note on scope

This document was originally requested as 16 separate deliverables (research report, judging model, dependency graph, orchestration engine, migration guide, CI/CD plan, and so on) plus a "runtime multi-agent orchestration engine" with retry logic and approval flows. Two honesty notes before you read further:

1. **This is one consolidated document, not sixteen.** The content those deliverables would have contained — research findings, the inferred judging model, dependency graph, roadmap — is here, organized by section. Splitting genuinely thin content across sixteen files would have optimized for the appearance of thoroughness over the substance of it.
2. **There is no runtime orchestration engine, because a skill collection can't run one.** Skills are markdown files an agent reads — they have no process, no scheduler, no retry loop of their own. What actually orchestrates skill invocation is the coding agent itself (Claude Code, Cursor, etc.), deciding from skill *descriptions* which one fits the current moment. The "orchestration" here is therefore a **phase-gate skill** (`orchestrate-phase-gates`) that documents the correct sequence and hands off to the right specialist skill at each stage — the same pattern this repository's `mattpocock/skills` flow and Sentry's skill package already use successfully. It's real, it works, and it isn't pretending to be software it isn't.

## Research findings

Grounded in four HackerRank blog posts (full text pulled and read, not inferred): *Behind the Scenes of Orchestrate*, *How HackerRank Is Rebuilding Developer Hiring for the Agentic Era*, *How Chakra Scores an Interview*, and *Nobody Knows What a Good Engineer Looks Like Anymore*. The two specific challenge pages (`support-agent`, `multi-modal-review`) are behind HackerRank's login wall and were **not** accessible — nothing below claims to represent their exact per-challenge rubric, which may differ from the general framework below. Always defer to the actual challenge page for the event you're in.

### The scored surface (from HackerRank's own published breakdown of the May 2026 event)

| Artifact | Weight | What it measures |
|---|---|---|
| Code zip | 30% | Agent design, architecture, tool integration, prompt quality, robustness, engineering standards — explicitly including "actual agent loops versus hardcoded workflows" |
| Output CSV | 30% | Functional correctness against a golden dataset, **and** the soundness of each decision's stated justification |
| AI chat transcript | 10% | How the participant *directed* AI coding tools — planning, constraint-setting, debugging, iteration |
| AI judge interview | 30% | Technical depth, problem understanding, communication clarity, self-awareness about limitations |

Published finding: **"No single metric reproduces the leaderboard."** Top performers were balanced across all four rather than exceptional at one.

### The evaluation philosophy behind the numbers

Three ideas recur across HackerRank's public writing and shape every skill in this collection:

1. **Process over output.** The stated shift is from "can you write code" to "can you plan a solution, direct an AI assistant, evaluate what it produces, and ship something that works." This is why the chat transcript is scored at all — it's the only artifact that captures *process* directly.
2. **Evidence-anchored scoring.** Chakra's interview scorer explicitly refuses to credit anything not traceable to a specific, verbatim moment — vague or theoretical answers score as "not met" regardless of whether the underlying understanding is real. This same disposition almost certainly extends to how justifications in the output CSV are read, and it's the design principle behind `orchestrate-justification-quality` and `orchestrate-interview-readiness`.
3. **Self-awareness is a scored trait, not a soft skill.** Both the interview rubric and the general philosophy pieces name limitation-awareness explicitly. Submissions that project false confidence score worse than ones that name real, specific weaknesses.

### What this implies about failure modes

Inferred from the above, not directly stated by HackerRank:

- **Decision-tree agents dressed as agentic ones.** Fixed control flow with LLM calls embedded in it, versus a loop where the model actually decides what happens next. The rubric names this distinction explicitly.
- **Correct-but-generic justifications.** A right verdict with a justification interchangeable across every row scores partial credit at best under an evidence-anchored rubric.
- **A silent chat transcript.** Request-accept-request-accept with no visible planning, constraint-setting, or critical evaluation — technically produces working code, scores near-zero on the 10% it's explicitly graded on.
- **Zero acknowledged limitations.** Reads as dishonest or unaware to an evidence-anchored interview scorer, independent of actual system quality.
- **Both-extremes failure on adversarial handling.** The published dataset description (edge cases, prompt injection, jailbreaking) is explicitly built so escalate-everything and respond-to-everything both fail — meaning the scoring signal lives almost entirely in the calibrated middle.

## The skill set

| Skill | Owns | Fires |
|---|---|---|
| `orchestrate-phase-gates` | Sequencing, time allocation | Start of the challenge; whenever "what's next" is unclear |
| `orchestrate-agent-architecture` | Real agent loops, tool design, prompt structure | Design phase, before and during implementation |
| `orchestrate-robustness` | Adversarial input, edge cases, calibration | Before implementing input handling — not after bugs appear |
| `orchestrate-justification-quality` | Evidence-anchored output reasoning | Writing/reviewing the CSV justification field |
| `orchestrate-ai-collaboration-transcript` | How you prompt, continuously | The entire session — this is a standing discipline, not a phase |
| `orchestrate-self-scoring` | Honest pre-submission self-audit | With meaningful time still left before deadline |
| `orchestrate-interview-readiness` | Concrete-answer prep for the AI interview | Before the interview, ideally starting well before |
| `orchestrate-submission-review` | Mechanical packaging correctness | Final 45–60 minutes, non-negotiable |

## Dependency graph

```
orchestrate-phase-gates (sequencer — reads this, hands off to the rest)
   │
   ├─▶ orchestrate-agent-architecture ──┐
   │                                     ├─▶ orchestrate-robustness
   │        (design decisions inform     │       (adversarial cases shape
   │         what needs defending)       │        the architecture back)
   │                                     │
   ├─▶ orchestrate-ai-collaboration-transcript
   │        (runs continuously alongside everything above — not sequential)
   │
   ├─▶ [implementation — tdd, implement, from the base collection]
   │
   ├─▶ orchestrate-justification-quality
   │        (depends on the agent and output schema already existing)
   │
   ├─▶ orchestrate-self-scoring
   │        (depends on code + output + transcript all existing to audit)
   │        │
   │        ├─▶ [gap found → loop back to the relevant skill above]
   │        │
   ├─▶ orchestrate-interview-readiness
   │        (strongest when it draws on real decisions already made,
   │         not fabricated post-hoc)
   │
   └─▶ orchestrate-submission-review (final, non-negotiable gate)
```

## Automatic invocation strategy

Every skill above ships with no `disable-model-invocation` flag, meaning it's **model-invoked by default** — a coding agent reading its description should reach for it when the moment matches, without you typing a slash command. This works because each description names concrete trigger conditions ("when starting to build an AI agent for a hackathon," "whenever an agent must justify a decision") rather than vague topic labels — specificity in the description is what makes automatic discovery reliable. If your agent under-triggers a skill, that's a description problem, fixable by editing the `description:` frontmatter to name the trigger more concretely — see `writing-great-skills` and `skill-scanner` elsewhere in this collection for how to diagnose and fix that.

## Validation framework

There is no CI that can grade "is this justification specific enough" — that's a judgment call, same as the real Chakra scorer. What *can* be mechanically checked, and should be, before submission:

- CSV parses cleanly and has the expected row/column shape
- Every referenced KB document ID in a justification actually exists (catches hallucinated citations)
- The code zip runs from a clean extract with only the documented setup steps
- No secrets committed
- Every output row has a non-null value in every required column

`orchestrate-submission-review` is the human-readable version of this list; a project-specific test suite can automate the mechanical subset of it.

## Roadmap / future improvements

- **A real scoring-estimator script** (not just a skill) that runs the mechanical validation checks above as an actual pre-commit or pre-submission hook, for projects that want a runnable artifact rather than a checklist. Scoped out of this pass per an explicit choice to keep this collection honest about what static skills can and can't do — flagged here as the natural next increment if wanted.
- **Per-challenge rubric skills** once a specific Orchestrate challenge's exact page content is available (the current skills are deliberately general to the four-signal framework, since the specific challenge pages weren't accessible during this research pass).
- **A post-event skill** for turning an Orchestrate submission into a portfolio artifact / blog writeup, since the underlying practices (justification discipline, transcript hygiene, architecture clarity) are reusable well beyond the contest.

## Beyond the contest

None of these eight skills are actually Orchestrate-specific in their substance — they're general AI-agent-engineering discipline that Orchestrate happens to score explicitly. Real agent loops over decision trees, evidence-anchored justification, honest limitation disclosure, and treating your AI-collaboration process as a first-class engineering artifact are all things worth doing whether or not anyone's grading them. That's the actual improvement-beyond-HackerRank: this collection optimizes for the contest by optimizing for the underlying competence the contest is (imperfectly, like every benchmark) trying to measure.
