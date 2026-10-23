"""Generate the static GitHub Pages site in site/ from the verified data.

    python scripts/build_site.py          # write site/
    python scripts/build_site.py --check  # fail if committed site files are stale

The site is NOT published by this script. Publishing needs the repository owner's
approval; see docs/DEPLOY_GITHUB_PAGES.md. The canonical base URL is the GitHub
Pages address that would be used if Pages is enabled for this repository.
"""

from __future__ import annotations

import html
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SITE = ROOT / "site"
BASE = "https://nitish-r-g.github.io/hackerrank-orchestrate-skills/"
REPO = "https://github.com/NITISH-R-G/hackerrank-orchestrate-skills"
PAGES = [
    ("", "Unofficial HackerRank Orchestrate skills and verified research",
     "Eight agent skills, a submission checker and an estimated scorer for HackerRank Orchestrate, with verified sources."),
]


def load(rel: str):
    return json.loads((ROOT / rel).read_text(encoding="utf-8"))


def page_html(summary: dict, research: dict) -> str:
    snaps = research["leaderboard_snapshots"]
    snap = next(iter(snaps.values()))
    ld = {
        "@context": "https://schema.org",
        "@type": "WebPage",
        "name": PAGES[0][1],
        "description": PAGES[0][2],
        "url": BASE,
        "isPartOf": {"@type": "WebSite", "name": "HackerRank Orchestrate skills (unofficial)", "url": BASE},
        "about": {"@type": "SoftwareSourceCode", "name": "HackerRank Orchestrate skills", "codeRepository": REPO,
                  "license": "https://spdx.org/licenses/MIT.html"},
        "disclaimer": "Unofficial community project. Not affiliated with HackerRank.",
    }
    body = f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{html.escape(PAGES[0][1])}</title>
<meta name="description" content="{html.escape(PAGES[0][2])}">
<link rel="canonical" href="{BASE}">
<meta property="og:title" content="{html.escape(PAGES[0][1])}">
<meta property="og:description" content="{html.escape(PAGES[0][2])}">
<meta property="og:url" content="{BASE}">
<meta property="og:type" content="website">
<script type="application/ld+json">{json.dumps(ld, ensure_ascii=False)}</script>
<style>
:root {{ color-scheme: light dark; --fg:#1d1d1f; --bg:#fff; --muted:#555; }}
body {{ font: 16px/1.5 system-ui, sans-serif; color: var(--fg); background: var(--bg); margin: 0 auto; max-width: 760px; padding: 16px; }}
h1 {{ font-size: 1.6rem; }}
table {{ border-collapse: collapse; width: 100%; }}
th, td {{ text-align: left; border-bottom: 1px solid #ddd; padding: 6px 4px; }}
.note {{ color: var(--muted); font-size: 0.9rem; }}
</style>
</head>
<body>
<main>
<h1>{html.escape(PAGES[0][1])}</h1>
<p><strong>Unofficial.</strong> This is a community project. It is not made by or affiliated with HackerRank.</p>
<p>{html.escape(PAGES[0][2])}</p>

<h2>Verified facts</h2>
<ul>
<li>HackerRank's published final score: 0.10 Chat + 0.30 Interview + 0.30 Output CSV + 0.30 Code ZIP (HackerRank blog, June 8, 2026).</li>
<li>The first edition had 12,885 registrations from 48 countries (same source). No public page names participant countries.</li>
<li>Public leaderboard snapshot: September 2026, page 1, {snap['rows']} rows. Final range {snap['final']['min']} to {snap['final']['max']}.</li>
</ul>

<h2>Search visibility tests</h2>
<p class="note">Observed on 2026-10-23 with country hints, not verified locations. Rankings are controlled by each search provider and are not guaranteed.</p>
<table>
<tr><th>Measure</th><th>Value</th></tr>
<tr><td>Country and query pairs planned</td><td>{summary['country_query_pairs_planned']}</td></tr>
<tr><td>Observed</td><td>{summary['observed']}</td></tr>
<tr><td>Repository in first place</td><td>{summary['first_place']}</td></tr>
<tr><td>Not tested</td><td>{summary['untested']}</td></tr>
</table>

<h2>Links</h2>
<ul>
<li><a href="{REPO}">Source repository on GitHub</a></li>
<li><a href="{REPO}/blob/master/docs/ORCHESTRATE_RESEARCH.md">Research summary with sources</a></li>
<li><a href="{REPO}/blob/master/docs/COUNTRY_VISIBILITY.md">Country visibility tests</a></li>
<li><a href="{REPO}/blob/master/docs/SEO_AEO_TEST_REPORT.md">SEO and AEO test report</a></li>
</ul>
</main>
</body>
</html>
"""
    return body


def sitemap() -> str:
    return ('<?xml version="1.0" encoding="UTF-8"?>\n'
            '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
            f"  <url><loc>{BASE}</loc></url>\n"
            "</urlset>\n")


def robots() -> str:
    return f"User-agent: *\nAllow: /\n\nSitemap: {BASE}sitemap.xml\n"


def main() -> int:
    matrix = load("data/country-query-matrix.json")
    research = load("data/orchestrate-research.json")
    outputs = {
        SITE / "index.html": page_html(matrix["summary"], research),
        SITE / "sitemap.xml": sitemap(),
        SITE / "robots.txt": robots(),
    }
    if "--check" in sys.argv:
        stale = [str(p.relative_to(ROOT)) for p, t in outputs.items()
                 if not p.exists() or p.read_text(encoding="utf-8") != t]
        if stale:
            print("STALE:", ", ".join(stale))
            return 1
        print("site is up to date")
        return 0
    SITE.mkdir(exist_ok=True)
    for p, t in outputs.items():
        p.write_text(t, encoding="utf-8")
        print("wrote", p.relative_to(ROOT))
    return 0


if __name__ == "__main__":
    sys.exit(main())
