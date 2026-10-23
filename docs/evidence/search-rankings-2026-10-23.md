# Search ranking check: 2026-10-23

Method: Google web search, logged-out, `pws=0` (no personalisation), `num=20`, read from the page's result headings. Region set with the `gl=` parameter (a country hint, not a real location). Browser: one Chromium tab in the Claude desktop app, not a set of incognito windows.

## Results

| Query | Region (`gl`) | Repo position |
|---|---|---|
| hackerrank orchestrate agent skills github | in | **1** |
| hackerrank orchestrate agent skills github | us | **1** |
| hackerrank orchestrate agent skills github | br | **1** |
| hackerrank orchestrate agent skills github | gb | not tested: Google showed a "sorry" (unusual traffic) page |
| hackerrank orchestrate agent skills github | de | not tested: same block |
| hackerrank orchestrate agent skills github | jp | not tested: same block |
| hackerrank orchestrate | us | not in the top 9 (official HackerRank pages and blog rank first) |

## What this does and does not show
- For a query that names the skills and GitHub, the repo ranked first in the three regions tested.
- For the broad query "hackerrank orchestrate", the repo did not appear on page 1. Official HackerRank pages rank above it.
- Three regions are not "all regions". The `gl=` value does not change the searcher's real location, and the browser was not in separate incognito sessions.
- The blocked regions were not retried or worked around.

## What the repo does to help
- The GitHub description and topics name the challenge, the agent platforms, and the skills. The description states the project is unofficial.
- The README has a short FAQ with the scoring formula, the past rounds covered, and install steps.
