# FAQ

**Is this affiliated with HackerRank?**
No. This is an independent, community-built collection based entirely on publicly published material — blog posts, the official public starter repositories, and organizer advice posts. See [ORCHESTRATE.md](./ORCHESTRATE.md) for exact sources.

**Does using these skills guarantee a better score?**
No, and be skeptical of anything that claims otherwise. HackerRank's own published finding is that "no single metric reproduces the leaderboard" — balance across all four scored signals (code, output, transcript, interview) mattered more than excellence in one. These skills are built to help with that balance, grounded in what's actually been published, not a guarantee.

**How do I know which advice here is a direct HackerRank quote versus a guess?**
Every skill's `SKILL.md` opens with a "Direct evidence" line naming its source. [ORCHESTRATE.md](./ORCHESTRATE.md) and [SCORING-HEURISTIC.md](./SCORING-HEURISTIC.md) explicitly tag every claim `[evidence]` or `[inference]`.

**Do these skills only work for the May/June 2026 challenges?**
The 8 core skills (`orchestrate-phase-gates` through `orchestrate-submission-review`) target the general four-signal framework, which is stable across events. The 10 tactical skills are grounded in the specific May (support-agent) and June (multi-modal-review) challenge requirements — a future Orchestrate event may have a different schema, but the underlying disciplines (guardrails, failure handling, evidence-grounded justification) should transfer.

**Can I use these outside HackerRank Orchestrate?**
Yes — see the "Beyond the contest" section of [ORCHESTRATE.md](./ORCHESTRATE.md). Nothing here is contest-specific in substance; it's general AI-agent-engineering discipline the contest happens to score explicitly.

**How do I install just the Orchestrate skills?**
```bash
git clone https://github.com/NITISH-R-G/hackerrank-orchestrate-skills.git
cp -r hackerrank-orchestrate-skills/skills/* your-project/.claude/skills/
```
Or from the full collection: `cp -r skills-i-use/skills/orchestrate-* your-project/.claude/skills/`

**I found a challenge page or a piece of official documentation this collection missed. What do you want?**
Open an issue or PR with the link. This collection is meant to stay accurate to what's actually published — corrections and additions from real sources are exactly the kind of contribution it needs most.

**Why isn't there a runtime "orchestration engine"?**
Because a skill collection can't run one — skills are files an agent reads, not a process with its own scheduler. See the "A note on scope" section of [ORCHESTRATE.md](./ORCHESTRATE.md) for the honest version of what the "orchestration" here actually is.
