# SEO and AEO test report

Date: 2026-10-23. Commands and results below were run on the working tree before the commit that adds this file. The test suite is in `tests/test_seo_research.py`.

## Visibility results (from `data/country-query-matrix.json`)

| Measure | Value |
|---|---|
| Country and query pairs planned | 20 |
| Observations recorded | 11 |
| Not tested | 9 |
| Repository in first place | 6 |
| Blocked by Google | 4 |
| Absent from top nine | 1 |

Notes on these numbers:
- "Observations recorded" includes the four blocked attempts. Those are recorded as blocked, not as results.
- The six first-place results are for one query (`hackerrank orchestrate agent skills github`) in India, the United States, Brazil, Canada, Mexico and Australia. These are search-location hints, not verified locations.
- The one absent result is for the broad query `hackerrank orchestrate` in the United States. The top nine results did not include the repository.
- Google's "unusual traffic" page blocked Singapore, the United Kingdom, Germany and Japan. Those were not retried.

## Providers not tested
- Bing, DuckDuckGo and other search engines: not tested in this run.
- AI assistants (ChatGPT, Claude, Gemini, Perplexity): not tested. The browser available here cannot run them logged out in a reproducible way, and no authorised access was provided.
- Google only, and only with the `gl=` hint.

## Automated tests

Command: `python -m pytest -q`

Result: all 186 tests in the suite pass, of which 24 are the new checks in `tests/test_seo_research.py`. Zero failures. Each of the ten mandatory checks maps to a test:

| # | Check | Test or evidence | Result |
|---|---|---|---|
| 1 | Research JSON schema and source URLs | `test_research_json_has_required_schema`, `test_every_source_has_https_url_on_allowed_host_and_a_retrieval_date`, `test_every_edition_source_id_resolves_to_a_source` | pass |
| 2 | Country attribution has traceable evidence | `test_every_observation_country_is_listed_with_a_source_note`, `test_no_country_is_attributed_to_a_participant_without_a_source` | pass |
| 3 | Duplicate handling and reproducible statistics | `test_duplicate_observations_are_rejected`, `test_statistics_are_reproducible_and_match_the_dataset`, `test_generated_outputs_are_up_to_date`, `test_leaderboard_snapshot_sums_match_final_scores` | pass |
| 4 | Internal links and canonical URLs | `test_relative_links_in_llms_txt_and_readme_resolve`, `test_canonical_repository_url_is_consistent` | pass |
| 5 | Sitemap validity and status codes | Not applicable: no website. `test_sitemap_is_documented_as_not_applicable_not_claimed` | pass |
| 6 | Robots directives | Not applicable: no website. `test_no_robots_file_that_could_block_relevant_pages` | pass |
| 7 | JSON-LD and citation validity | `test_citation_file_has_required_cff_fields`, `test_citation_abstract_matches_the_eight_skill_count`. JSON-LD on a web page: not applicable. | pass |
| 8 | Required metadata and crawlable content | `test_readme_has_unofficial_disclaimer_and_faq`, `test_llms_txt_declares_the_unofficial_status` | pass |
| 9 | No committed secrets or private participant data | `test_no_secret_patterns_in_tracked_files` (allowlists only `tests/test_score.py`, which holds a deliberately fake key), `test_raw_leaderboard_snapshot_has_no_participant_names_or_handles`, `test_research_json_contains_no_handles` | pass |
| 10 | Documentation matches implementation | `test_visibility_doc_numbers_match_the_dataset`, `test_stale_skill_count_is_gone_from_readme`, `test_research_doc_states_the_published_formula`, `test_seo_test_report_numbers_match_the_dataset` | pass |

## Existing checks
- `python -m pytest -q`: runs the whole suite, including the older kit tests.
- `ruff`: available (version 0.15.14), but the repository has no lint configuration, so no lint result is claimed.

## Deployment
- No website exists, so no live site was validated.
- Live search-ranking checks are in `docs/COUNTRY_VISIBILITY.md`.

## Refresh commands

```bash
python scripts/build_research_data.py          # regenerate data and COUNTRY_VISIBILITY.md
python scripts/build_research_data.py --check  # fail if committed outputs are stale
python -m pytest -q tests/test_seo_research.py
```

## Limitations
- The matrix covers 10 countries, not all APAC and North American countries.
- Each result is one query at one moment, logged out, with a country hint.
- Search rankings are controlled by each provider. These results do not show that the repository will rank the same way for other users.
