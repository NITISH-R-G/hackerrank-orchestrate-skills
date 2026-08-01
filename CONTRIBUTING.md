# Contributing

## Adding a general skill

1. Check it's not already covered (browse `skills/` or search the README's category tables).
2. Add its source repo and license to `LICENSE-AND-ATTRIBUTION.md` — skills without a verifiable source aren't merged.
3. Open a PR adding the `skills/<name>/SKILL.md` folder.

## Adding or improving an Orchestrate skill

The bar here is higher: **every claim needs a traceable source.** Before opening a PR:

1. Find the specific official source (a HackerRank blog post, the official starter repo, an organizer advice post) — not a forum post repeating a rumor.
2. Quote it directly in the skill's "Direct evidence" section, and link the source.
3. If you're making an inference rather than citing a direct quote, label it `[inference]` explicitly — see [SCORING-HEURISTIC.md](./SCORING-HEURISTIC.md) for the pattern.
4. If you're proposing a new challenge-specific skill (a new Orchestrate event shipped a new challenge type), include a link to that event's official starter repo or challenge page.

PRs that add generic "AI engineering best practices" dressed up as Orchestrate-specific insight, without a traceable HackerRank source, won't be merged into the Orchestrate skill set — they can go in the general "Software Engineering Reference" category instead, where original/general content is welcome.

## Reporting a factual error

If something here misrepresents what HackerRank has actually published, that's a priority fix — open an issue with the correct source, or a PR with the correction. Accuracy is this repo's entire value proposition.

## Code of conduct

Be direct, be kind, cite your sources.
