# HackerRank Orchestrate Skills

**18 free AI agent skills for HackerRank Orchestrate — evidence-cited line by line from HackerRank's published methodology *and* the official starter repositories for the May and June 2026 events.** Drop them into Claude Code, Cursor, Codex, or any agent that supports the [Agent Skills](https://agentskills.io) standard, and they trigger automatically while you build — no slash commands, nothing to remember.

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

## What's new in this version

The first version was built from four HackerRank blog posts. This version adds a second research pass that found the **official public GitHub starter repositories** for both events (`interviewstreet/hackerrank-orchestrate-may26` and `-june26`) and a direct organizer post, *"Getting better at Orchestrate,"* naming specific mistakes and practices. That's direct-quote evidence, not inference — and it's why this version has 10 new tactical skills, not a round-number expansion. Every skill states its evidence tier; nothing here claims access to HackerRank's actual internal scoring.

## The 18 skills

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
