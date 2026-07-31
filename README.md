# HackerRank Orchestrate Skills

**8 free AI agent skills for HackerRank Orchestrate — reverse-engineered from HackerRank's own published scoring methodology.** Drop them into Claude Code, Cursor, Codex, or any agent that supports the [Agent Skills](https://agentskills.io) standard, and they trigger automatically while you build — no slash commands, nothing to remember.

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

Published finding from HackerRank's own post-mortem: **"No single metric reproduces the leaderboard."** The winners weren't the best coders — they were balanced across all four signals. If you're planning to spend 90% of your 24 hours on code, you're optimizing for 30% of the score.

Full research writeup, with sourcing: **[RESEARCH.md](./RESEARCH.md)**.

## The 8 skills

| Skill | What it does | When it fires |
|---|---|---|
| [`orchestrate-phase-gates`](./skills/orchestrate-phase-gates) | The master sequencer — time allocation across all 4 signals, gate order | Start of the challenge |
| [`orchestrate-agent-architecture`](./skills/orchestrate-agent-architecture) | Real agent loops vs. hardcoded workflows, tool design, prompt structure | Design & implementation |
| [`orchestrate-robustness`](./skills/orchestrate-robustness) | Prompt injection, jailbreak attempts, edge-case calibration | Before writing input handling |
| [`orchestrate-justification-quality`](./skills/orchestrate-justification-quality) | Evidence-anchored reasoning for every agent decision — this is what separates a 2 from a 3 on the output rubric | Writing/reviewing your CSV output |
| [`orchestrate-ai-collaboration-transcript`](./skills/orchestrate-ai-collaboration-transcript) | Prompting so your chat transcript itself scores well | Continuously, the whole session |
| [`orchestrate-self-scoring`](./skills/orchestrate-self-scoring) | Honest pre-submission audit against all 4 signals — find your weak spot before a judge does | With time left before deadline |
| [`orchestrate-interview-readiness`](./skills/orchestrate-interview-readiness) | Concrete-answer prep for the AI judge interview — including how to disclose limitations well | Before your interview |
| [`orchestrate-submission-review`](./skills/orchestrate-submission-review) | Final packaging checklist — the mechanical failures that cost points for no good reason | Final 45–60 minutes |

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

Works with Claude Code, Cursor, Codex, Antigravity, Cline, Gemini CLI, and every other agent that reads `SKILL.md` files — the format is an open standard, not tied to one tool.

## Why these and not a generic prompt-engineering list

Every other resource you'll find for a hackathon like this is generic advice — "write good prompts," "test your code." These 8 skills are built from **HackerRank's own published statements** about how Chakra scores work: the evidence-anchored philosophy ("every score traces back to a specific, verbatim moment"), the explicit rubric weights, and the specific failure modes their own writing calls out (decision trees pretending to be agents, vague justifications, zero self-awareness about limitations). Read [RESEARCH.md](./RESEARCH.md) for the sourcing — every claim links back to what HackerRank actually published, not speculation.

**One honest limitation of this repo, stated up front** (fittingly, since that's exactly the discipline `orchestrate-interview-readiness` argues for): the specific per-challenge rubric pages (e.g. the exact `support-agent` or `multi-modal-review` challenge instructions) are behind HackerRank's contest login and weren't accessible while building this. These skills are built on the general four-signal framework HackerRank has published publicly — **always defer to your actual challenge page** if it says something different.

## This isn't just for the contest

Strip away the HackerRank framing and what's left is genuinely good agent-engineering discipline: real agent loops instead of decision trees, evidence-anchored justification for every automated decision, honest disclosure of system limitations, and treating your AI-collaboration process as a first-class artifact worth doing well. Use these skills for any agent you build, contest or not.

## Part of a larger collection

These 8 skills are also available inside **[skills-i-use](https://github.com/NITISH-R-G/skills-i-use)** — a curated, cross-agent collection of 480+ reviewed Agent Skills covering everything from TDD to API design to DevSecOps. If Orchestrate is your entry point into agent skills generally, that's where to look next.

## Contributing

Competed in Orchestrate and learned something these skills got wrong or missed? Open a PR or an issue. This repo gets more accurate the more real contest experience feeds back into it.

## License

MIT — see [LICENSE](./LICENSE). These 8 skills were written from scratch for this collection, grounded in publicly available HackerRank blog posts (cited, never reproduced) — see [RESEARCH.md](./RESEARCH.md) for full sourcing.

---

*Not affiliated with or endorsed by HackerRank. Built by studying their public writing about how Orchestrate and Chakra work.*
