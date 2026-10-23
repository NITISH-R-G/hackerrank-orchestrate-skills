# HackerRank Orchestrate: verified research

Retrieved 2026-10-23. Machine-readable version: `data/orchestrate-research.json`. Sources: `data/sources.json`. Regenerate with `python scripts/build_research_data.py`.

## Confirmed facts (with sources)

| Fact | Source |
|---|---|
| Four public editions have starter repositories: May, June, August and September 2026 | GitHub `interviewstreet/hackerrank-orchestrate-{may26,june26,august26,september26}` |
| The first edition started May 1, 2026 | HackerRank blog, June 8, 2026 (`hackerrank-blog-behind-the-scenes-2026-06-08`) |
| The first edition had 12,885 registrations from 48 countries | Same blog post. Aggregate count only. No country names. |
| Final score = 0.10 Chat + 0.30 Interview + 0.30 Output CSV + 0.30 Code ZIP | HackerRank blog (June 8, 2026 and July 24, 2026) |
| Interview scores correlate with answer depth (total words r = 0.615) | HackerRank blog, June 8, 2026 |
| Leaderboard final equals the sum of the four displayed section points | September leaderboard page 1, all 30 rows checked |

## Leaderboard coverage

Only the September 2026 "Buy or Wait" leaderboard page 1 was public (30 of 3,062 entries, 103 pages). It shows points per section, not countries. A privacy-safe snapshot (ranks and points, no names or handles) is in `data/raw/`.

Summary of that snapshot (30 rows):

- Final score range: 72.7 to 80.0
- Output CSV is the section with the widest spread (12.6 to 21.9 out of 30)

Pages 2 to 103 were not collected. Collecting them would need one request per page, and the page-1 snapshot is enough for the statistics above.

## Editions without public leaderboards

The contest pages for May, June, August and October 2026 require login (checked 2026-10-23). No leaderboard data for those editions is in this repository.

## Countries

- **No public page names the countries of participants.** The leaderboard has no country column. Contest pages are login-gated.
- The only country-level figure is the aggregate "48 countries" for the first edition's registrations.
- This repository does not infer any participant's country from any other data.
- The country list in `data/country-query-matrix.json` is the list of **countries used as search-location hints** in the visibility tests. It is not a list of participating countries.

## Unknowns and conflicts

- Exact dates for the June, August and September rounds are not confirmed by a public source.
- The June 8 blog says the second edition would be on June 19. This repository does not know whether that happened.
- The September leaderboard page shows 0.0 in its "Final Results" banner for the top three, while its table shows 80.0, 79.6 and 77.8. The table values are used. The banner is ignored.
- No public grader code exists. `code/evaluation/` in the September repository is empty.

## Rejected or failed records

- None rejected. Failed or blocked search checks are listed in `docs/COUNTRY_VISIBILITY.md`.
