"""Checks for the verified research data, the AEO files and the documentation.

Covers the mandatory tests in the SEO/AEO brief that apply to a repository with
no website: research schemas and sources, country attribution, duplicates,
reproducible statistics, internal links, citation metadata, secrets and private
participant data, and documentation that matches the data.
"""

from __future__ import annotations

import csv
import json
import re
import subprocess
import sys
from pathlib import Path
from urllib.parse import urlparse

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import build_research_data as brd  # noqa: E402

ALLOWED_HOSTS = {"github.com", "www.hackerrank.com", "hackerrank.com"}


def load(rel: str):
    return json.loads((ROOT / rel).read_text(encoding="utf-8"))


def tracked_text_files():
    out = subprocess.run(["git", "ls-files"], cwd=ROOT, capture_output=True, text=True, check=True).stdout
    for name in out.splitlines():
        p = ROOT / name
        if p.suffix in {".md", ".py", ".json", ".txt", ".cff", ".yml", ".yaml", ".toml", ".sh", ".ps1", ".csv"} and p.exists():
            yield name, p.read_text(encoding="utf-8", errors="ignore")


# 1. Research JSON schemas and source URLs
def test_research_json_has_required_schema():
    research = load("data/orchestrate-research.json")
    for key in ("schema_version", "editions", "sources", "leaderboard_snapshots", "country_coverage"):
        assert key in research, key
    assert research["schema_version"] == 1
    assert len(research["editions"]["editions"]) == 4


def test_every_source_has_https_url_on_allowed_host_and_a_retrieval_date():
    sources = load("data/sources.json")
    assert sources["retrieved_on"]
    for s in sources["sources"]:
        parsed = urlparse(s["url"])
        assert parsed.scheme == "https", s["id"]
        assert parsed.netloc in ALLOWED_HOSTS, s["id"]
        assert s["access"], s["id"]


def test_every_edition_source_id_resolves_to_a_source():
    ids = {s["id"] for s in load("data/sources.json")["sources"]}
    for ed in load("data/editions.json")["editions"]:
        for sid in ed["source_ids"]:
            assert sid in ids, (ed["id"], sid)


# 2. Country attribution has traceable evidence
def test_every_observation_country_is_listed_with_a_source_note():
    matrix = load("data/country-query-matrix.json")
    codes = {c["code"]: c for c in matrix["countries"]}
    for obs in matrix["observations"]:
        assert obs["country_code"] in codes, obs
        assert codes[obs["country_code"]]["source"], obs["country_code"]


def test_no_country_is_attributed_to_a_participant_without_a_source():
    research = load("data/orchestrate-research.json")
    assert research["country_coverage"]["publicly_named_countries"] == []
    for claim in research["country_coverage"]["aggregate_claims"]:
        assert claim["source_id"] in {s["id"] for s in load("data/sources.json")["sources"]}


# 3. Duplicate handling and reproducible statistics
def test_duplicate_observations_are_rejected():
    obs = load("data/country-observations.json")
    obs["observations"].append(dict(obs["observations"][0]))
    with pytest.raises(ValueError):
        brd.build_matrix(obs)


def test_statistics_are_reproducible_and_match_the_dataset():
    matrix = load("data/country-query-matrix.json")
    s = matrix["summary"]
    assert s["observed"] == len(matrix["observations"])
    assert s["country_query_pairs_planned"] == len(matrix["countries"]) * len(matrix["queries"])
    assert s["untested"] == s["country_query_pairs_planned"] - s["observed"]
    assert s["first_place"] == sum(1 for o in matrix["observations"] if o["status"] == "first")


def test_generated_outputs_are_up_to_date():
    # Re-running the build must reproduce every committed generated file exactly.
    assert subprocess.run([sys.executable, str(ROOT / "scripts" / "build_research_data.py"), "--check"],
                          cwd=ROOT, capture_output=True).returncode == 0


def test_leaderboard_snapshot_sums_match_final_scores():
    stats = brd.leaderboard_stats(ROOT / "data" / "raw" / "leaderboard-september26-buy-or-wait-page1.csv")
    assert stats["rows"] == 30
    assert stats["final"]["sum_check_all_rows"] is True


# 4. Internal links and canonical URLs (repository links; no website exists)
def test_relative_links_in_llms_txt_and_readme_resolve():
    for doc in ("llms.txt", "README.md", "docs/ORCHESTRATE_RESEARCH.md", "docs/SEO_AEO_AUDIT.md"):
        text = (ROOT / doc).read_text(encoding="utf-8")
        for target in re.findall(r"\]\(([^)#\s]+)\)", text):
            if target.startswith(("http://", "https://", "mailto:")):
                continue
            assert (ROOT / doc).parent.joinpath(target).resolve().exists() or (ROOT / target).exists(), (doc, target)


def test_canonical_repository_url_is_consistent():
    cff = (ROOT / "CITATION.cff").read_text(encoding="utf-8")
    assert "https://github.com/NITISH-R-G/hackerrank-orchestrate-skills" in cff


# 5. Sitemap validity and status codes: NOT APPLICABLE (no website). Documented.
def test_sitemap_is_documented_as_not_applicable_not_claimed():
    audit = (ROOT / "docs" / "SEO_AEO_AUDIT.md").read_text(encoding="utf-8")
    assert "NOT APPLICABLE" in audit
    assert not (ROOT / "sitemap.xml").exists()


# 6. Robots directives: no robots.txt exists, so none can block pages.
def test_no_robots_file_that_could_block_relevant_pages():
    assert not (ROOT / "robots.txt").exists()


# 7. JSON-LD / citation metadata validity and consistency
def test_citation_file_has_required_cff_fields():
    cff = (ROOT / "CITATION.cff").read_text(encoding="utf-8")
    for key in ("cff-version:", "message:", "title:", "authors:", "repository-code:", "license:"):
        assert key in cff, key
    assert 'cff-version: 1.2.0' in cff


def test_citation_title_matches_repo_description_claims():
    cff = (ROOT / "CITATION.cff").read_text(encoding="utf-8")
    assert "Eight agent skills" in cff.replace("\n", " ") or "Eight agent skills" in cff


# 8. Required metadata and crawlable content
def test_readme_has_unofficial_disclaimer_and_faq():
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    assert "Unofficial" in readme
    assert "## FAQ" in readme
    assert "Not affiliated" in readme or "not made by or affiliated" in readme


def test_llms_txt_declares_the_unofficial_status():
    assert "Unofficial" in (ROOT / "llms.txt").read_text(encoding="utf-8")


# 9. No committed secrets or private participant data
SECRET = re.compile(r"sk-[A-Za-z0-9_-]{20,}|AKIA[0-9A-Z]{16}|ghp_[A-Za-z0-9]{30,}|-----BEGIN [A-Z ]*PRIVATE KEY")


# tests/test_score.py holds a deliberately fake key so the kit's secret detector can be
# proven to fire. Nothing else is allowlisted.
ALLOWED_FIXTURE_FILES = {"tests/test_score.py"}


def test_no_secret_patterns_in_tracked_files():
    hits = []
    for name, text in tracked_text_files():
        if name in ALLOWED_FIXTURE_FILES:
            continue
        for m in SECRET.finditer(text):
            hits.append((name, m.group(0)[:12]))
    assert hits == [], hits


def test_raw_leaderboard_snapshot_has_no_participant_names_or_handles():
    path = ROOT / "data" / "raw" / "leaderboard-september26-buy-or-wait-page1.csv"
    header = next(csv.reader(path.open(encoding="utf-8")))
    assert header == ["rank", "chat_10", "interview_30", "output_csv_30", "code_zip_30", "final_100"]


def test_research_json_contains_no_handles():
    text = (ROOT / "data" / "orchestrate-research.json").read_text(encoding="utf-8")
    for handle in ("sunnyas1824", "shanupg", "vivpm99", "Jovan_Nadendla"):
        assert handle not in text


# 10. Documentation matches the implementation
def test_visibility_doc_numbers_match_the_dataset():
    matrix = load("data/country-query-matrix.json")
    doc = (ROOT / "docs" / "COUNTRY_VISIBILITY.md").read_text(encoding="utf-8")
    s = matrix["summary"]
    assert f"Observed: {s['observed']}" in doc
    assert f"Not tested: {s['untested']}" in doc
    assert f"Repository in first place: {s['first_place']}" in doc


def test_stale_skill_count_is_gone_from_readme():
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    assert "34 Agent Skills" not in readme
    assert "34 [Agent Skills]" not in readme


def test_research_doc_states_the_published_formula():
    doc = (ROOT / "docs" / "ORCHESTRATE_RESEARCH.md").read_text(encoding="utf-8")
    assert "0.10 Chat + 0.30 Interview + 0.30 Output CSV + 0.30 Code ZIP" in doc


def test_seo_test_report_numbers_match_the_dataset():
    matrix = load("data/country-query-matrix.json")
    report = (ROOT / "docs" / "SEO_AEO_TEST_REPORT.md").read_text(encoding="utf-8")
    s = matrix["summary"]
    assert f"| Observations recorded | {s['observed']} |" in report
    assert f"| Repository in first place | {s['first_place']} |" in report
    assert f"| Blocked by Google | {s['by_status'].get('blocked', 0)} |" in report


# --- Site and Bing checks added with the Pages preparation ---
import subprocess as _sp  # noqa: E402

SITE_BASE = "https://nitish-r-g.github.io/hackerrank-orchestrate-skills/"


def test_generated_site_is_up_to_date():
    rc = _sp.run([sys.executable, str(ROOT / "scripts" / "build_site.py"), "--check"], cwd=ROOT, capture_output=True)
    assert rc.returncode == 0, rc.stdout


def test_site_canonical_sitemap_and_robots_agree():
    html_text = (ROOT / "site" / "index.html").read_text(encoding="utf-8")
    assert f'<link rel="canonical" href="{SITE_BASE}">' in html_text
    sitemap = (ROOT / "site" / "sitemap.xml").read_text(encoding="utf-8")
    assert f"<loc>{SITE_BASE}</loc>" in sitemap
    robots = (ROOT / "site" / "robots.txt").read_text(encoding="utf-8")
    assert f"Sitemap: {SITE_BASE}sitemap.xml" in robots
    assert "Disallow: /" not in robots


def test_site_json_ld_parses_and_is_truthful():
    html_text = (ROOT / "site" / "index.html").read_text(encoding="utf-8")
    m = re.search(r'application/ld\+json">(.*?)</script>', html_text, re.S)
    assert m, "no JSON-LD block"
    ld = json.loads(m.group(1))
    assert ld["@type"] == "WebPage"
    assert "not affiliated" in ld["disclaimer"].lower()
    assert ld["url"] == SITE_BASE


def test_site_meta_and_visible_content_match():
    html_text = (ROOT / "site" / "index.html").read_text(encoding="utf-8")
    matrix = load("data/country-query-matrix.json")
    assert "<title>" in html_text and 'name="description"' in html_text
    assert f"<td>{matrix['summary']['first_place']}</td>" in html_text
    assert f"<td>{matrix['summary']['observed']}</td>" in html_text


def test_bing_observations_never_count_as_first_place_without_a_result():
    matrix = load("data/country-query-matrix.json")
    bing = [o for o in matrix["observations"] if o["provider"] == "bing-web"]
    assert bing, "Bing observations missing"
    assert all(o["status"] != "first" for o in bing)
    assert all(o["result_url"] is None for o in bing if o["status"] != "first")
    for o in bing:
        assert o["status"] in {"absent_top5", "anomalous", "blocked", "absent_top9"}, o


def test_deployment_doc_states_nothing_is_published():
    doc = (ROOT / "docs" / "DEPLOY_GITHUB_PAGES.md").read_text(encoding="utf-8")
    assert "not deployed" in doc.lower()
    assert "approval" in doc.lower()


# --- README visual checks ---
def test_readme_image_paths_exist_and_have_alt_text():
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    imgs = re.findall(r'<img [^>]*src="([^"]+)"[^>]*>', readme)
    assert len(imgs) >= 3, imgs
    for tag in re.findall(r"<img [^>]*>", readme):
        assert re.search(r'alt="[^"]{10,}"', tag), tag
    for src in imgs:
        assert (ROOT / src).exists(), src


def test_readme_details_blocks_are_balanced_and_diagrams_present():
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    assert readme.count("<details>") == readme.count("</details>") >= 2
    assert readme.count("```mermaid") >= 2


def test_readme_markdown_links_resolve():
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    for target in re.findall(r"\]\(([^)#\s]+)\)", readme):
        if target.startswith(("http://", "https://", "mailto:")):
            continue
        assert (ROOT / target).exists(), target
