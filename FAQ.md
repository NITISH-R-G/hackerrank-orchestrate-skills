# FAQ

**Is this affiliated with HackerRank?**
No. This is an independent, community-built project based on publicly published material — blog posts, the official public starter repositories, organizer advice posts — plus a first-hand completed submission for the `orchestrate_kit` tooling and audit-tier skills. See [README.md](./README.md) for exact sources, and [TIMELINE.md](./TIMELINE.md) for the first-hand evidence tier specifically.

**Does using these skills, or `orchestrate_kit`, guarantee a better score?**
No, and be skeptical of anything that claims otherwise. HackerRank's own published finding is that "no single metric reproduces the leaderboard" — balance across all four scored signals (code, output, transcript, interview) mattered more than excellence in one. The mentor, the evaluator, and the skills are built to help with that balance; none of it is a guarantee, and `orchestrate_kit` will tell you `UNKNOWN` rather than invent one.

**How do I know which advice here is a direct HackerRank quote versus a guess?**
Every skill's `SKILL.md` opens with a "Direct evidence" line naming its source. [RESEARCH.md](./RESEARCH.md) and [SCORING-HEURISTIC.md](./SCORING-HEURISTIC.md) explicitly tag every claim `[evidence]` or `[inference]`. Inside `orchestrate_kit`, every `Finding` carries a `Confidence` label (`measured` / `observed` / `inferred` / `unknown`) for the same reason.

**Do these skills only work for the May/June 2026 challenges?**
The 8 core skills (`orchestrate-phase-gates` through `orchestrate-submission-review`) target the general four-signal framework, which is stable across events. The 10 tactical skills are grounded in the specific May (support-agent) and June (multi-modal-review) challenge requirements — a future event may have a different schema, but the underlying disciplines (guardrails, failure handling, evidence-grounded justification) should transfer. The 13 audit-tier skills and all of `orchestrate_kit` are built from first-hand experience running a full submission through certification, and are similarly schema-independent — the evaluator's Orchestrate plugin detects by dataset *shape* (`dataset/messages.csv` + `problem_statement.md`), not by season, so it applies to any future event with that shape.

**Can I use any of this outside HackerRank Orchestrate?**
Yes — see the ["Beyond the contest"](./README.md#beyond-the-contest) section of the README. Nothing here is contest-specific in substance; it's general AI-agent-engineering discipline the contest happens to score explicitly. `orchestrate_kit`'s generic evaluator plugin, mentor taxonomy, and judge personas are entirely domain-independent — the Orchestrate plugin is one registered plugin among however many you write.

**How do I install just the Orchestrate skills?**
```bash
git clone https://github.com/NITISH-R-G/hackerrank-orchestrate-skills.git
cp -r hackerrank-orchestrate-skills/skills/* your-project/.claude/skills/
```
Or from the full collection: `cp -r skills-i-use/skills/orchestrate-* your-project/.claude/skills/`

**How do I install the `orchestrate` CLI, mentor, judge, memory, and evaluator?**
```bash
pip install -e ".[dev]"
python -m orchestrate_kit memory seed
python -m orchestrate_kit mentor "I want to add OCR"
```
See the [README's "The four systems" section](./README.md#the-four-systems) for what each piece does, and the [Install section](./README.md#install) for the full setup including a note on the `orchestrate` shorthand command and `PATH`.

**I found a challenge page or a piece of official documentation this collection missed. What do you want?**
Open an issue or PR with the link. This project is meant to stay accurate to what's actually published — corrections and additions from real sources are exactly the kind of contribution it needs most, matching [CONTRIBUTING.md](./CONTRIBUTING.md)'s "reporting a factual error" process.

**Is there a runtime "orchestration engine"?**
Yes, as of `orchestrate_kit` — but it's worth being precise about what runs and what doesn't. The **skills** in `skills/` are still just files an agent reads; they have no scheduler of their own, by design, because that's what "auto-triggering Agent Skill" means. The **CLI** in `orchestrate_kit/` is real, executable software with state: an Engineering Memory JSON store, a mentor that queries it, an adaptive interview simulator with session memory and cross-examination, and a plugin-based evaluator with a negative-control self-test. If "orchestration engine" means "something with actual control flow and persisted state you can run and test," that's `orchestrate_kit`, not the skill files.
