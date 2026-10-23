# Deploying the site to GitHub Pages

Status: **not deployed**. Nothing here has been published. Each step below needs the repository owner's approval.

## What is ready
- `site/index.html`: unofficial landing page with verified facts, visibility-test counts and links to the sources.
- `site/sitemap.xml`: lists the one page.
- `site/robots.txt`: allows all crawlers and points to the sitemap.
- Canonical URL and JSON-LD are set to `https://nitish-r-g.github.io/hackerrank-orchestrate-skills/`.

Regenerate with `python scripts/build_site.py`, and check with `python scripts/build_site.py --check`.

## Steps (need approval first)
1. Approve publishing the `site/` folder.
2. In the repository settings, choose **Pages**, source **Deploy from a branch**, branch `master`, folder `/site`. (Do not change any other setting.)
3. Wait for the Pages build to finish, then open the URL above.
4. Check the live page: status 200, canonical tag, `robots.txt` and `sitemap.xml` return 200.
5. Record the deployment date and the observed status codes in `docs/SEO_AEO_TEST_REPORT.md`.

## Not included
- No external directory submissions, backlinks or social posts. Those need separate approval.
- No webmaster-tool registration. That needs your account access.
