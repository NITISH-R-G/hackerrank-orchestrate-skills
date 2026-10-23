# SEO and AEO audit

Audit date: 2026-10-23. Repository: `NITISH-R-G/hackerrank-orchestrate-skills`.

## Scope
This repository has **no public website**. Its only public surface is the GitHub repository page and the raw files it serves. The website items in the brief (sitemap, robots.txt, canonical URLs, Open Graph, JSON-LD on pages, mobile tests, live Lighthouse) are therefore **NOT APPLICABLE** until a site exists. GitHub Pages was not enabled, because publishing externally needs your approval.

## Baseline (before this change)

| Item | Status before | Evidence |
|---|---|---|
| Repository description | Stale: said "34 auto-triggering Agent Skills" | `gh repo view`, 2026-10-23 |
| Topics | 20 topics, some weak | `gh repo view` |
| README FAQ | Added earlier this session | commit `9494e1c` |
| Stale claim "34 Agent Skills" in README | Present in two places (line 69 table, line 439 heading) | `grep -n 34 README.md` |
| Machine-readable summary (llms.txt) | Missing | `ls` |
| Citation metadata (CITATION.cff) | Missing | `ls` |
| Website, sitemap, robots.txt | None | `ls` |
| Secrets in tracked files | None found by pattern scan (`sk-`, `AKIA`, `ghp_`) | scan, 2026-10-23 |
| Test suite | Passing before this change | `python -m pytest -q` |

## Changes in this audit
1. Corrected the stale "34 skills" claims in the README to the current eight-skill set.
2. Added `llms.txt`: a short, factual, machine-readable summary with links to the verified data and the methodology.
3. Added `CITATION.cff`: citation metadata for the repository.
4. Added the verified research pipeline, data and generated tables described in `docs/ORCHESTRATE_RESEARCH.md`.
5. Added automated tests for the points in `docs/SEO_AEO_TEST_REPORT.md`.

## Pages site prepared (not published)
- `scripts/build_site.py` generates `site/index.html`, `site/sitemap.xml` and `site/robots.txt` from the verified data.
- The canonical URL is `https://nitish-r-g.github.io/hackerrank-orchestrate-skills/`. It is used only if Pages is enabled. Nothing is published.
- Deployment steps and the approval gate are in `docs/DEPLOY_GITHUB_PAGES.md`.

## Not done, and why
- **Live sitemap and robots.txt:** the files are generated in `site/`, but no live site exists until Pages is enabled.
- **JSON-LD on a live page:** the JSON-LD is in `site/index.html` and parses, but it is not live until Pages is enabled. `CITATION.cff` is the citation file GitHub reads.
- **Country pages:** not created. Verified data names no participant countries, so any country page would be doorway content, which the brief forbids.
- **External directories and backlinks:** not submitted. Submitting to external sites requires your authorisation and must not use fake endorsements.
- **Ranking claims:** none made. Search rankings are controlled by each provider. See `docs/COUNTRY_VISIBILITY.md`.
