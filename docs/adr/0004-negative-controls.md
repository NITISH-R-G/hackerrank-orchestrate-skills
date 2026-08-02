# ADR-0004: Every audit requires a negative control before it ships

**Status:** Accepted
**Memory:** `orchestrate memory recall F-leakage-false-blocker`,
`orchestrate memory recall F-ablation-harness`,
`orchestrate memory recall F-prober-artifacts`

## Context

Three separate audit harnesses built for this project's evaluator were
**confidently wrong**, and each produced a *clean, confirming* result:

- A label-leakage audit fired a BLOCKER on a healthy repository — it
  scanned exploratory scripts as production code, matched fixture
  variables as dataset ids, and treated docstrings as executable code.
- An ablation harness reported "0 of 110 rows changed" from disabling
  media — it had monkeypatched a name the consumer had already bound at
  import, so both arms of the comparison silently ran the same code.
- A rule-reachability prober reported 3 dead rules and 7 shadowed — it
  randomized only fields matching a naming prefix and returned the first
  matching condition, so a tier-1 rule won nearly every random draw.

None of these failed loudly. Each looked exactly like a working audit
doing its job.

## Decision

An audit is not considered trustworthy until there is a test proving it
**can produce a finding** — a deliberately broken input that it must
catch — in addition to tests proving it stays quiet on healthy input.
Enforced structurally: `orchestrate plugin new` scaffolds a plugin whose
generated audit *fails on purpose*, with one test marked `xfail`, so the
very first run is red. `orchestrate selftest` applies the same standard to
the evaluator as a whole: 10 injected defect classes must be caught, 3
deliberately benign cases must stay quiet.

## Consequences

- **Positive:** "the audit has always passed" stops being read as
  evidence of correctness — it's read as *untested*, until a negative
  control says otherwise.
- **Positive:** the failure mode this ADR exists to prevent — a clean
  result from a broken harness — is exactly the one hardest to catch by
  code review, because a broken harness that returns "0 findings" looks
  identical to a correct one that found nothing.
- **Negative:** every new audit costs more to write — a real negative
  control, not a rubber-stamp test. Treated as the correct tradeoff: a
  cheap audit that can't be trusted isn't actually cheap.

## Alternatives considered (and rejected, with the reason)

| Alternative | Rejected because |
|---|---|
| Code review as the quality gate | All three false results above passed code review — the bug was in what the code *actually matched*, not in whether it read cleanly |
| Trust a green run after enough time in production | A harness that has silently returned "clean" for months provides zero additional confidence over one that has never run — it has never been tested either way |

## Reconsider if

Never, as a principle — though the *mechanism* (scaffold template, 10/3
selftest split) should grow as new failure classes are discovered, the
same way the three findings above grew it from "write good tests" into an
enforced structural requirement.
