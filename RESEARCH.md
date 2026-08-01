# The Orchestrate Intelligence Layer

**21 skills** for maximizing performance in HackerRank Orchestrate — and, not incidentally, for building genuinely better AI agents regardless of who's grading.

## A note on scope

This document was originally requested as 16 separate deliverables (research report, judging model, dependency graph, orchestration engine, migration guide, CI/CD plan, and so on) plus a "runtime multi-agent orchestration engine" with retry logic and approval flows. Two honesty notes before you read further:

1. **This is one consolidated document, not sixteen.** The content those deliverables would have contained — research findings, the inferred judging model, dependency graph, roadmap — is here, organized by section. Splitting genuinely thin content across sixteen files would have optimized for the appearance of thoroughness over the substance of it.
2. **There is no runtime orchestration engine, because a skill collection can't run one.** Skills are markdown files an agent reads — they have no process, no scheduler, no retry loop of their own. What actually orchestrates skill invocation is the coding agent itself (Claude Code, Cursor, etc.), deciding from skill *descriptions* which one fits the current moment. The "orchestration" here is therefore a **phase-gate skill** (`orchestrate-phase-gates`) that documents the correct sequence and hands off to the right specialist skill at each stage — the same pattern this repository's `mattpocock/skills` flow and Sentry's skill package already use successfully. It's real, it works, and it isn't pretending to be software it isn't.
3. **On the "40 skills" ask, specifically:** a second research pass (below) found genuinely new, specific, quotable evidence — enough to responsibly expand from 8 to 18. It did not find evidence for 40 distinct categories. Padding to a round number by inventing categories the evidence doesn't support would fail the collection's own stated test ("would this become the repository people recommend") the moment anyone who's actually read the source material opens a skill and finds generic advice dressed up as a distinct discipline. 18 evidence-backed skills beats 40 diluted ones.

## Research findings — round one (four blog posts)

Grounded in four HackerRank blog posts (full text pulled and read, not inferred): *Behind the Scenes of Orchestrate*, *How HackerRank Is Rebuilding Developer Hiring for the Agentic Era*, *How Chakra Scores an Interview*, and *Nobody Knows What a Good Engineer Looks Like Anymore*.

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

## Research findings — round two (official starter repos + organizer advice post)

The May and June challenge pages themselves were login-gated and inaccessible in round one. A second pass found the **official public GitHub starter repositories** for both events (`interviewstreet/hackerrank-orchestrate-may26` and `-june26`), which mirror the actual challenge READMEs — real requirements, real constraints, real evaluation criteria, not paraphrase. It also found *"Getting better at Orchestrate,"* a direct organizer post naming specific mistakes and specific recommended practices. This is the strongest evidence tier in this document — direct quotes from HackerRank, not inference.

**Directly quoted, hard requirements (support-agent / May challenge):**
- Output schema: `status` (replied/escalated), `product_area`, `response`, `justification`, `request_type` (product_issue/feature_request/bug/invalid)
- "Must be terminal-based," "must use only the provided support corpus," "must escalate high-risk, sensitive, or unsupported cases"
- "Store secrets in environment variables only; never hardcode keys" — "Be deterministic; seed random sampling"
- Submission = code zip + `output.csv` + AGENTS.md-format chat log at a fixed OS-specific path

**Directly quoted, hard requirements (multi-modal-review / June challenge):**
- Output schema: `evidence_standard_met`, `risk_flags`, `issue_type`, `object_part`, `claim_status` (supported/contradicted/not_enough_information), `claim_status_justification`, `supporting_image_ids`, `valid_image`, `severity`
- Mandatory analysis: metrics against `sample_claims.csv`, **comparison of ≥2 strategies/prompts/configurations**, final approach documentation, **operational metrics** (model calls, token usage, image usage, cost, runtime, TPM/RPM)
- "Must avoid hardcoded test labels or file-specific answers"

**Directly quoted, named mistakes ("Getting better at Orchestrate"):** unclear architecture / single-LLM-call systems / hidden critical logic; poor naming ("helper," "utils"); hardcoded paths/secrets; silent failures (invalid output reaching final results); incomplete testing (successes only, no failure/edge inspection); inconsistent handling of similar cases without justification.

**Directly quoted, named recommended practices:** separate concerns (input loading / prompts / agent logic / validation / evaluation); guardrails on LLM output (validate schema, reject unsupported labels, retry malformed); "log failed rows, continue safely when possible, mark uncertainty when responsible"; prompts written with code-level care (allowed outputs, required evidence, format requirements); clear README with entry point; justifications that reference specific evidence; interview prep that names specific tested edge cases and specific known limitations.

This round-two evidence is what the 10 new skills below (`orchestrate-schema-guardrails` through `orchestrate-escalation-design`) are built directly from — each cites its specific source line in its own `SKILL.md`.

## The skill set

**Core flow (round one, general four-signal framework):**

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

**Tactical/implementation (round two, directly quoted requirements):**

| Skill | Owns | Fires |
|---|---|---|
| `orchestrate-schema-guardrails` | Output validation, retry-on-malformed | Writing the model-response-to-CSV-row code path |
| `orchestrate-failure-handling` | Per-row error handling, uncertainty marking | Writing the main processing loop |
| `orchestrate-naming-and-structure` | File/module organization, descriptive naming | Scaffolding the project; before submission review |
| `orchestrate-secrets-and-determinism` | Env-var secrets, seeded randomness | Writing config/setup code; pre-submission zip check |
| `orchestrate-edge-case-testing` | Failure inspection, consistency checks | Before submission, after a working end-to-end run exists |
| `orchestrate-prompt-engineering` | Prompt rigor, versioned prompt files | Writing/revising any system or task prompt |
| `orchestrate-multi-strategy-evaluation` | ≥2-approach comparison, documented choice | Any nontrivial implementation decision point |
| `orchestrate-cost-and-ops-metrics` | Call/token/cost/runtime tracking | Instrumenting the agent's model client |
| `orchestrate-multimodal-evidence-grounding` | Image-to-claim reasoning (June challenge) | Building the multi-modal claim pipeline |
| `orchestrate-escalation-design` | Calibrated, category-based escalation logic | Designing the escalate-vs-respond decision boundary |

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

## Research findings — round three (The Engineer's Notebook + a first-hand case study)

A third pass studied *The Engineer's Notebook* (Shloka Shah's Substack), specifically "Getting better at HackerRank Orchestrate," plus one of its three linked developer case studies. **Honesty notes on this round**: the site's root/archive page listed no article index reachable without search, so "every relevant subpage" wasn't literally navigable — only the one primary post and its explicit outbound links were available to follow. Of the three linked case studies, only the highest-signal one (a #1-ranked finisher's writeup) was fetched and read; the other two (`saai.syvendra.com`, a second Medium post by `swayam-mishra`) are cited as pointers only — their content is **not** represented anywhere in this document, to avoid fabricating what wasn't actually read.

**Directly quoted / clearly evidenced, from the Substack article (an independent author's analysis, not an official HackerRank source — treated as strong secondary evidence, distinct from the primary-source tiers above):**
- The self-check framework of tracing one input through every architectural stage to verify the separation of concerns is real, not just diagrammed
- Input validation *before* model calls, as a distinct discipline from output validation after
- "Rule-based overrides for cases where model discretion shouldn't apply" as deliberate design, not a fallback of last resort
- A specific three-phase AGENTS.md transcript structure: **Plan** (problem understanding before implementation) → **Build** (technical specificity) → **Review** (treating your own output behavior as code review)
- A specific interview-answer delivery structure: "start with the direct answer, add one concrete detail, tie it back to the task, and then stop"
- The evaluation-loop framing: reliability comes from "someone looked at the failures and made the system less fragile," not from a perfect first prompt

**From one credited, first-hand participant case study (a #1-ranked finisher, "How I went from 122 to 1 in 24 hours") — explicitly labeled as one person's account, not organizer guidance:**
- Single-agent-with-tools outperformed a multi-agent split for cross-image reasoning, because the multi-agent handoff lost signal at the summarization boundary
- Conditional, confidence-gated safety overrides (fire only when the model can't cite specific evidence) outperformed a binary safety flag (fire on any low-confidence signal), which was producing false positives on legitimate findings
- Checkpoint-and-resume processing turned an API-rate-limit hit from "reprocess everything" into "resume exactly where it stopped"
- Mock interview drilling with an AI playing the judge, focused on defending specific tradeoffs, was credited alongside a reported finding that interview score outweighed code score in this participant's final rank

This round produced 3 new skills (`orchestrate-input-tracing`, `orchestrate-input-validation-and-overrides`, `orchestrate-checkpoint-resilience`) and meaningful additions to 3 existing skills (`orchestrate-ai-collaboration-transcript`, `orchestrate-interview-readiness`, `orchestrate-agent-architecture`) rather than duplicating what those skills already covered.

## Scoring heuristic

A separate document, [SCORING-HEURISTIC.md](./SCORING-HEURISTIC.md), gives a rough self-assessment rubric across ten dimensions. It is explicitly **not** a reproduction of HackerRank's internal system — it's an evidence-informed heuristic for self-checking before submission, labeled as such throughout.

## Roadmap / future improvements

- **A real scoring-estimator script** (not just a skill) that runs the mechanical validation checks above as an actual pre-commit or pre-submission hook, for projects that want a runnable artifact rather than a checklist. Still scoped out — flagged here as the natural next increment.
- **A post-event skill** for turning an Orchestrate submission into a portfolio artifact / blog writeup, since the underlying practices (justification discipline, transcript hygiene, architecture clarity) are reusable well beyond the contest.
- **A third research pass once a fresh Orchestrate event runs** — challenge specifics (schema fields, domain) change between events (support triage in May, multi-modal claims in June); the *pattern* of what's rewarded has been stable across both, which is what this collection is built around, but a new event may surface new specifics worth a new tactical skill.

## Beyond the contest

None of these eight skills are actually Orchestrate-specific in their substance — they're general AI-agent-engineering discipline that Orchestrate happens to score explicitly. Real agent loops over decision trees, evidence-anchored justification, honest limitation disclosure, and treating your AI-collaboration process as a first-class engineering artifact are all things worth doing whether or not anyone's grading them. That's the actual improvement-beyond-HackerRank: this collection optimizes for the contest by optimizing for the underlying competence the contest is (imperfectly, like every benchmark) trying to measure.
