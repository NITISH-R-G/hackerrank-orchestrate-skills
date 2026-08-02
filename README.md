# HackerRank Orchestrate Skills

**34 free AI agent skills, a working repo evaluator, and a full AI-judge prep package for HackerRank Orchestrate — evidence-cited line by line from HackerRank's published methodology, the official starter repositories for the May and June 2026 events, an independent engineering analysis, and a first-hand #1-ranked participant case study.** Drop them into Claude Code, Cursor, Codex, or any agent that supports the [Agent Skills](https://agentskills.io) standard, and they trigger automatically while you build — no slash commands, nothing to remember.

If you're competing in HackerRank Orchestrate (or prepping for one), this repo exists so you don't lose points to things that have nothing to do with your agent's actual quality — an unread rubric, an unscoreable justification, an interview answer that's true but too vague to score.

---

## The rubric these skills are built against

HackerRank has published exactly how Orchestrate scores a submission. Most participants never read this before they start building. That alone is a real edge:

| Artifact | Weight | What it actually measures |
|---|---|---|
| **Code zip** | 30% | Agent design, architecture, tool integration, prompt quality, robustness — explicitly, *"actual agent loops versus hardcoded workflows"* |
| **Output CSV** | 30% | Correctness against a golden dataset, **and whether each decision has a sound justification** |
| **AI chat transcript** | 10% | How you *directed* your AI coding tools — planning, constraints, debugging, iteration |
| **AI judge interview** | 30% | Technical depth, communication, and explicitly, **self-awareness about your own system's limitations** |

Published finding from HackerRank's own post-mortem: **"No single metric reproduces the leaderboard."** The winners weren't the best coders — they were balanced across all four signals.

Full research writeup, with sourcing for every claim: **[RESEARCH.md](./RESEARCH.md)** · Self-scoring rubric: **[SCORING-HEURISTIC.md](./SCORING-HEURISTIC.md)** · **[FAQ](./FAQ.md)**

---

## v4 — the audit tier

Everything above came from *reading about* Orchestrate. v4 comes from **building a
complete August 2026 submission and auditing it to destruction**: 48 logged defects
(F-1…F-48), 9 measured-and-rejected optimisations, 17 certification scripts, and one
completed AI-judge interview.

That is a new evidence tier, and it is labelled as such in every v4 skill. It is *not*
access to HackerRank's internal scoring, and nothing here claims to be.

| Deliverable | What it is |
|---|---|
| **[PLAYBOOK.md](./PLAYBOOK.md)** | 20 rules for building AI systems whose correctness you can prove |
| **[TIMELINE.md](./TIMELINE.md)** | The real F-1…F-48 history — including three audits that were themselves wrong |
| **[JUDGE-PREP.md](./JUDGE-PREP.md)** | Topics the judge actually probed, verbatim feedback, model answers, and 10 claims never to make |
| **[RELEASE-CHECKLIST.md](./RELEASE-CHECKLIST.md)** | Final gate, ordered so the cheapest checks catch the worst defects |
| **[tools/](./tools)** | `aiev` — a working evaluator you point at a repo |

```bash
python -m aiev evaluate /path/to/your/orchestrate-repo --markdown report.md
```

### The 13 v4 skills

| Skill | Answers |
|---|---|
| [`orchestrate-spec-auditor`](./skills/orchestrate-spec-auditor) | Does it match the spec *literally*? |
| [`orchestrate-submission-validator`](./skills/orchestrate-submission-validator) | Are all three artifacts current and consistent? |
| [`orchestrate-multimodal-auditor`](./skills/orchestrate-multimodal-auditor) | Does media actually change a decision? |
| [`orchestrate-dataset-coupling-auditor`](./skills/orchestrate-dataset-coupling-auditor) | Will it survive data I have not seen? |
| [`orchestrate-determinism-auditor`](./skills/orchestrate-determinism-auditor) | Is it reproducible, and where does that stop? |
| [`orchestrate-security-auditor`](./skills/orchestrate-security-auditor) | Does every hostile input yield a valid row? |
| [`orchestrate-confidence-calibrator`](./skills/orchestrate-confidence-calibrator) | Am I calibrating to the labels or to a textbook? |
| [`orchestrate-evidence-retrieval-expert`](./skills/orchestrate-evidence-retrieval-expert) | Is a retrieval gain even possible? |
| [`orchestrate-rule-engine-architect`](./skills/orchestrate-rule-engine-architect) | Rules or an LLM — and is any rule dead? |
| [`orchestrate-interview-coach`](./skills/orchestrate-interview-coach) | Do I own every number in my code? |
| [`orchestrate-release-engineer`](./skills/orchestrate-release-engineer) | Does it work on someone else's machine? |
| [`orchestrate-mentor`](./skills/orchestrate-mentor) | Should I make this change **before** I make it? |
| [`orchestrate-evaluator`](./skills/orchestrate-evaluator) | Am I moving toward Rank 1? |

### Three things worth taking even if you read nothing else

**Prove the counterfactual.** To claim a component drives an outcome, disable it and
show the outcome *stops*. "It works with OCR on" is compatible with OCR being
decorative.

**Rejection is a deliverable.** "We use embeddings" is a claim anyone can make. "We
measured embeddings at F1 0.479 against 0.512 and did not ship them" cannot be faked —
and a real judge praised exactly this: *"measuring your own assumptions and being
willing to reject changes that didn't improve things."*

**Attack your own measurement.** Three audits in the reference build were wrong, and
each produced a clean, confirming result. Two would have shipped a false conclusion.

## What's new in this version

The first version was built from four HackerRank blog posts. This version adds a second research pass that found the **official public GitHub starter repositories** for both events (`interviewstreet/hackerrank-orchestrate-may26` and `-june26`) and a direct organizer post, *"Getting better at Orchestrate,"* naming specific mistakes and practices. That's direct-quote evidence, not inference — and it's why this version has 10 new tactical skills, not a round-number expansion. Every skill states its evidence tier; nothing here claims access to HackerRank's actual internal scoring.

## What's new in this version

A third research pass studied *The Engineer's Notebook* (an independent engineering Substack) and a first-hand #1-ranked participant's writeup ("How I went from 122 to 1 in 24 hours"). This added 3 new skills — `orchestrate-input-tracing`, `orchestrate-input-validation-and-overrides`, `orchestrate-checkpoint-resilience` — and meaningfully strengthened 3 existing ones (a Plan/Build/Review transcript structure, a specific interview-delivery technique plus mock-drilling practice, and a single-agent-vs-multi-agent architecture lesson). These sources are clearly labeled as secondary evidence (an independent author's analysis, one participant's account) — distinct from the primary-source tiers (official blog, official starter repo) elsewhere in this collection. Full sourcing: [RESEARCH.md](./RESEARCH.md).

## The 21 skills

**Core flow** — the general four-signal framework, stable across events:

| Skill | What it does | When it fires |
|---|---|---|
| [`orchestrate-phase-gates`](./skills/orchestrate-phase-gates) | The master sequencer — time allocation across all 4 signals, gate order | Start of the challenge |
| [`orchestrate-agent-architecture`](./skills/orchestrate-agent-architecture) | Real agent loops vs. hardcoded workflows, tool design, prompt structure | Design & implementation |
| [`orchestrate-robustness`](./skills/orchestrate-robustness) | Prompt injection, jailbreak attempts, edge-case calibration | Before writing input handling |
| [`orchestrate-justification-quality`](./skills/orchestrate-justification-quality) | Evidence-anchored reasoning for every agent decision | Writing/reviewing your CSV output |
| [`orchestrate-ai-collaboration-transcript`](./skills/orchestrate-ai-collaboration-transcript) | Prompting so your chat transcript itself scores well | Continuously, the whole session |
| [`orchestrate-self-scoring`](./skills/orchestrate-self-scoring) | Honest pre-submission audit against all 4 signals | With time left before deadline |
| [`orchestrate-interview-readiness`](./skills/orchestrate-interview-readiness) | Concrete-answer prep for the AI judge interview | Before your interview |
| [`orchestrate-submission-review`](./skills/orchestrate-submission-review) | Final packaging checklist | Final 45–60 minutes |

**Tactical** — directly quoted from the official starter repos and organizer advice post:

| Skill | What it does | Source |
|---|---|---|
| [`orchestrate-schema-guardrails`](./skills/orchestrate-schema-guardrails) | Validate model output against schema, reject bad enum values, retry malformed responses | "Getting better at Orchestrate" |
| [`orchestrate-failure-handling`](./skills/orchestrate-failure-handling) | Per-row error handling, logging, and explicit uncertainty-marking | "Getting better at Orchestrate" |
| [`orchestrate-naming-and-structure`](./skills/orchestrate-naming-and-structure) | Separate concerns, no `helper.py`/`utils.js` | "Getting better at Orchestrate" |
| [`orchestrate-secrets-and-determinism`](./skills/orchestrate-secrets-and-determinism) | Env-var-only secrets, seeded randomness, no local paths | Official starter repo |
| [`orchestrate-edge-case-testing`](./skills/orchestrate-edge-case-testing) | Inspect failures not just successes; catch inconsistent handling of similar cases | "Getting better at Orchestrate" |
| [`orchestrate-prompt-engineering`](./skills/orchestrate-prompt-engineering) | Write prompts with code-level rigor — allowed outputs, required evidence, format specs | "Getting better at Orchestrate" |
| [`orchestrate-multi-strategy-evaluation`](./skills/orchestrate-multi-strategy-evaluation) | Compare ≥2 approaches against the sample dataset, document the reasoning | June (multi-modal) challenge, required |
| [`orchestrate-cost-and-ops-metrics`](./skills/orchestrate-cost-and-ops-metrics) | Track model calls, tokens, cost, runtime, rate limits | June (multi-modal) challenge, required |
| [`orchestrate-multimodal-evidence-grounding`](./skills/orchestrate-multimodal-evidence-grounding) | Image-to-claim reasoning: supported/contradicted/insufficient-info, per-image citation | June (multi-modal) challenge schema |
| [`orchestrate-escalation-design`](./skills/orchestrate-escalation-design) | Calibrated, category-based escalation — not one global confidence threshold | Official starter repo + dataset design |

**Design & resilience** — from an independent analysis and a #1-ranked participant's case study:

| Skill | What it does | Source |
|---|---|---|
| [`orchestrate-input-tracing`](./skills/orchestrate-input-tracing) | Trace one input through every pipeline stage to verify the architecture is real, not just drawn | The Engineer's Notebook |
| [`orchestrate-input-validation-and-overrides`](./skills/orchestrate-input-validation-and-overrides) | Validate inputs *before* model calls; use confidence-gated (not binary) safety overrides | The Engineer's Notebook + #1-ranked case study |
| [`orchestrate-checkpoint-resilience`](./skills/orchestrate-checkpoint-resilience) | Checkpoint-and-resume so a rate limit mid-run doesn't force full reprocessing | #1-ranked case study |

## Install

**Everything:**
```bash
git clone https://github.com/NITISH-R-G/hackerrank-orchestrate-skills.git
cp -r hackerrank-orchestrate-skills/skills/* your-project/.claude/skills/
```

**One skill:**
```bash
cp -r hackerrank-orchestrate-skills/skills/orchestrate-robustness your-project/.claude/skills/
```

Works with Claude Code, Cursor, Codex, Antigravity, Cline, Gemini CLI, and every other agent that reads `SKILL.md` files — the format is an open standard, not tied to one tool. Skills trigger automatically based on their description; nothing to invoke manually.

## Why these and not a generic prompt-engineering list

Every other resource you'll find for a hackathon like this is generic advice — "write good prompts," "test your code." These 18 skills are built from **direct quotes**: HackerRank's stated evaluation philosophy, the exact rubric weights, the official starter repository's hard requirements, and an organizer post naming specific scored mistakes. Read [RESEARCH.md](./RESEARCH.md) — every claim links back to what HackerRank actually published, tagged `[evidence]` or `[inference]` so you always know which.

## This isn't just for the contest

Strip away the HackerRank framing and what's left is genuinely good agent-engineering discipline: real agent loops instead of decision trees, evidence-anchored justification for every automated decision, schema guardrails on LLM output, honest failure handling, calibrated escalation logic, and treating your AI-collaboration process as a first-class artifact worth doing well. Use these skills for any agent you build, contest or not.

## Part of a larger collection

These 18 skills are also available inside **[skills-i-use](https://github.com/NITISH-R-G/skills-i-use)** — a curated, cross-agent collection of 480+ reviewed Agent Skills covering everything from TDD to API design to DevSecOps.

## Contributing

See [CONTRIBUTING.md](./CONTRIBUTING.md). The short version: every claim needs a traceable, quoted source — competed in Orchestrate and learned something this got wrong? Open a PR with the correction and a source.

## License

MIT — see [LICENSE](./LICENSE). These skills were written from scratch for this collection, grounded in publicly available HackerRank material (quoted with attribution, never reproduced wholesale) — see [RESEARCH.md](./RESEARCH.md) for full sourcing.

---

*Not affiliated with or endorsed by HackerRank. Built entirely by studying their public writing and official public repositories about how Orchestrate and Chakra work.*
