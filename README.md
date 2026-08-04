# orchestrate-kit

[![CI](https://github.com/NITISH-R-G/hackerrank-orchestrate-skills/actions/workflows/ci.yml/badge.svg)](https://github.com/NITISH-R-G/hackerrank-orchestrate-skills/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](./LICENSE)
[![Python 3.10+](https://img.shields.io/badge/python-3.10%2B-blue)](./pyproject.toml)
[![Zero runtime deps](https://img.shields.io/badge/dependencies-0-brightgreen)](./pyproject.toml)

**The definitive toolkit for HackerRank Orchestrate.** HackerRank grades
every submission on four independent signals — Code ZIP, Output CSV, AI
Chat Transcript, AI Judge Interview — and their own published analysis
found no single one predicts the leaderboard: the top submissions were
balanced across all four, not excellent at one. Every tool here targets
one or more of those four signals directly, not generic "AI engineering
best practice."

| This repo gives you | Targets |
|---|---|
| `orchestrate transcript` — a rubric-verified linter for your chat transcript, not a prompt library | AI Chat Transcript |
| `orchestrate interview` — an adaptive judge simulator with cross-examination and contradiction-catching session memory | AI Judge Interview |
| `orchestrate evaluate` — black-box repo auditor: spec conformance, evidence quality, dataset-coupling, determinism | Code ZIP + Output CSV |
| `orchestrate memory` — every measured rejection from a real, completed submission, queryable so you don't re-build what already lost | All four — it's the corpus behind the other three |
| 34 [Agent Skills](https://agentskills.io) | Auto-triggering guidance across the whole build, sourced from HackerRank's own published material |

Nothing here claims to be general AI-engineering infrastructure. It
targets one leaderboard.

```bash
git clone https://github.com/NITISH-R-G/hackerrank-orchestrate-skills.git
cd hackerrank-orchestrate-skills
pip install -e .
python -m orchestrate_kit memory seed
python -m orchestrate_kit mentor "I want to add OCR"
```

`python -m orchestrate_kit` always works, in a venv or not. `pip install -e .`
also registers a plain `orchestrate` command — use it once its `Scripts`/`bin`
directory is on your `PATH` (a venv puts it there automatically; a bare
`pip install` on Windows often does not, and prints a warning telling you
where it landed).

Zero runtime dependencies. No API key. Everything runs offline.

---

## Why this exists

Most engineering tooling answers *"did the tests pass?"*

This answers the questions that actually decide whether you ship:

| Question | Command |
|---|---|
| If I ship today, what evidence says I'm better? | `orchestrate evaluate <repo>` |
| Should I build this at all? | `orchestrate mentor "add embeddings"` |
| Why *didn't* we do X? | `orchestrate memory why-not "embeddings"` |
| Can I survive being asked about it? | `orchestrate interview --difficulty hard` |
| Is this actually releasable? | `orchestrate release <repo>` |
| Can my audits even fail? | `orchestrate selftest` |

One rule runs through all of it: **nothing states a number it did not measure.**
Where a measurement is absent the tools print `UNKNOWN` and hand you the
experiment that would resolve it.

---

## The four systems

### 1. Engineering Memory — `orchestrate memory`

A commit log records what happened. It cannot record what you *considered*.

```
$ orchestrate memory why-not "embeddings"

D-dense-retrieval  Dense embeddings / RRF / cross-encoder   [rejected]
  because : the relation being scored is topical word OVERLAP, not paraphrase
  measured: evidence F1: 0.479 vs 0.512 (baseline)  [n=28 labeled]
  measured: configs dominating the shipped one on all 6 metrics: 0  [n=153]
  variants: dense MiniLM; reciprocal rank fusion; cross-encoder rerank; MMR
  RECONSIDER IF: the evidence relation becomes paraphrase-based -- graded
            evidence sharing NO tokens with the query. Measure token overlap
            between query and gold; if median drops below 2 terms, re-open.
  lesson  : Benchmark the fashionable option. Publish the number when it loses.
```

**40 entries, 9 of them measured rejections.** Every rejection carries a
`reconsider_if`, and this is enforced — `memory add --status rejected` without
one is refused:

> *a rejection without `--reconsider-if` is a prejudice, not a decision.*

A rejection with no reconsideration condition tells the next engineer "no"
without telling them what would change the answer. That is how a good idea
stays dead for the wrong reason.

Storage is a single JSON file. Commit it, diff it, review it in a PR.

### 2. The Mentor — `orchestrate mentor`

Accepts a proposal in plain English and answers eight questions before you
write any code.

```
$ orchestrate mentor "I want to add OCR"

1. WHAT KIND OF CHANGE IS THIS
   [add-model] Add or enable a model-based component
   The question to answer before writing any code:
     > How many rows can this component possibly fix? Count them first.

2. WHAT HAS BEEN TRIED BEFORE
   [shipped ] F-20-ocr-wrong-conclusion  'The images carry no signal' was a
              conclusion about two vendors
        measured: characters extracted: 0 -> 10,104  [n=20 images]
        blast radius: 0 of 110 output rows changed -- the channel is live and
                      redundant on THIS corpus
   [shipped ] F-48-ocr-cost  Local OCR cost 0.25s -> 45s, heap 7 MB -> 500 MB
   [REJECTED] D-visual-model  A visual model beyond OCR
        RECONSIDER IF: rows appear where message_text is empty AND the image
                       is not text-bearing

3. EXPECTED GAIN   ...
4. RISK REGISTER (6)   ...
5. BLAST RADIUS -- how to measure it, not what it is
6. EVALUATION PLAN -- run these, in this order
7. REGRESSION RISK
8. RELEASE RECOMMENDATION:  PROCEED-WITH-MEASUREMENT
```

Ten proposal classes (`add-model`, `swap-retrieval`, `tune`, `add-rule`,
`llm-decision`, `perf`, `confidence`, `personalize`, `refactor`, `test`), each
contributing a risk register and a required-evidence list.

**It refuses to predict your gain.** With no prior art it prints `UNKNOWN`:

> *No measurement exists. This tool will not estimate one — a predicted gain
> with no experiment behind it is the exact failure mode this framework exists
> to prevent.*

Blocking is deliberately narrow. `use dense embeddings` is blocked;
`add OCR` is not, because *"a visual model beyond OCR"* is a neighbour, not the
same proposal. Adjacent rejections are shown, not enforced. It also finds
rejections nested inside *accepted* entries — `tune the BM25 k1 parameter` is
blocked by the entry that shipped BM25 and rejected tuning it, which a status
filter alone cannot see.

### 3. The Judge — `orchestrate interview`

An adaptive simulator, not a question list.

```bash
orchestrate interview --persona skeptic --difficulty hard
orchestrate interview --panel --learn      # 4 judges, coaching after each answer
orchestrate interview --topics retrieval determinism -n 12
```

- **4 personas** who disagree with each other. The Architect wants the
  alternative you rejected; the Skeptic wants provenance for every number; the
  Security Reviewer wants trust boundaries; the Practitioner wants to know what
  breaks at 3am.
- **4 difficulty levels**, from `warmup` to `adversarial` (pass mark 55 → 78).
- **Adaptive**: the next question comes from your *weakest* dimension, and the
  level rises when you do well. Answer vaguely about retrieval and you get more
  retrieval, harder.
- **Cross-examination** fires for a named reason, not at random:

  > *"You gave me a number. Where did it come from — did you measure it, or is
  > that a recollection?"*
  > *"You said `fully deterministic`. Give me the boundary."*

- **Session memory.** Claim determinism in question 2, mention a hosted API in
  question 7, and the judge brings it back: *"Which is it, and where exactly is
  the boundary?"*
- **Weakness detection** names the habit and quotes the answer that showed it —
  `Guarantees with no boundary`, `Claims without provenance`,
  `Never said "I don't know"`.

Scoring runs on five dimensions: specificity, evidence, boundaries,
alternatives, honesty — weighted per persona.

**Stated limitation, not hidden:** this scores the *shape* of an answer. It
cannot know whether your F1 was really 0.512. A fluent answer full of invented
numbers scores well here and fails in the room. It trains form; truth is your
job.

### 4. The Evaluator — `orchestrate evaluate | certify | release`

Black-box first: it clones, runs commands, reads files, diffs artifacts. The
core knows nothing about your domain — everything specific lives in a plugin.

```
$ orchestrate evaluate ../my-submission

DO NOT SHIP   score 49/100   [generic, hackerrank-orchestrate]

   determinism      ########## 100  (1 audits, 0 findings)
   specification    ########## 100  (1 audits, 0 findings)
 ! release          ..........   0  (2 audits, 1 findings)
   testing          #######...  75  (1 audits, 1 findings)

BLOCKERS:
  - dataset/output.csv is STALE
```

Three verbs, three different questions:

| verb | asks | exit |
|---|---|---|
| `evaluate` | is this shippable? | `2` on any blocker |
| `certify` | is this *clean*? any finding above INFO fails | `3` on non-blocking findings |
| `release` | is this submittable? adds gates + manual items | `2` on gate failure |
| `selftest` | can the audits fail at all? | `2` if a defect slips through |

Every finding carries the literal command output plus a confidence label —
`measured` / `observed` / `inferred` / `unknown`. Inferred findings are
discounted. **A skipped audit is reported as UNKNOWN, never as a pass.**

Blockers print *above* the score, because an average that lets fourteen passes
outvote one release blocker is worse than no score at all.

`release` ends with the items no tool can check, including the one that matters
most:

> `[ ] Make the authorship attestation yourself. No tool may make it for you.`

### 5. Diagrams — `orchestrate viz`

Nine generated Mermaid diagrams. Generated, never hand-drawn: a hand-drawn
architecture diagram is a *claim* about the code, a generated one is a
projection of it.

```bash
orchestrate viz all --out diagrams/
orchestrate graph --focus retrieval > decisions.mmd
orchestrate graph --timeline
```

`architecture` (trust-coloured) · `trust` · `evaluation` · `rules` · `audit` ·
`regression` · `submission` · `decisions` · `timeline`

The decision graph renders **rejected branches as first-class nodes** beside
the chosen one — precisely what `git log` cannot show.

---

## Install

```bash
git clone https://github.com/NITISH-R-G/hackerrank-orchestrate-skills.git
cd hackerrank-orchestrate-skills
pip install -e ".[dev]"
python -m orchestrate_kit memory seed
python -m pytest                     # 53 tests
python -m orchestrate_kit selftest   # negative control
```

Every command in this README uses `python -m orchestrate_kit` because it works
unconditionally — no PATH configuration, venv or not. `pip install -e .` also
registers a shorter `orchestrate` command once its install location is on your
`PATH`; swap it in once you've confirmed `orchestrate --help` resolves.

## Writing a plugin

```bash
orchestrate plugin new rag --detect "eval/questions.jsonl" --category retrieval
```

Generates the plugin, a README, and **its negative control** — seven tests
including "the audit can actually fail" and "skips rather than passing when it
cannot run". The generated audit fails on purpose and one test is marked
`xfail`: your first run is red, and making it green is the exercise.

```python
class MyPlugin:
    name, description = "rag", "Retrieval-augmented generation"

    def detect(self, ctx) -> bool:          # detect on SHAPE, never on repo name
        return ctx.exists("eval/questions.jsonl")

    def audits(self):
        return [SimpleAudit("retrieval-ablation", "retrieval", my_audit)]
```

An audit gets a `RepoContext` (run commands, read files, glob) and returns an
`AuditResult`. **It must never raise** — a crash is reported as a finding, not
swallowed.

## Does it actually detect anything? — `orchestrate selftest`

A framework that reports 100/100 is worthless unless it can fail. This builds a
healthy fixture repo, confirms it passes, then injects defects one at a time:

```
$ orchestrate selftest

  baseline           CLEAN   (0 finding(s))
  CAUGHT illegal action value                             blocker
  CAUGHT illegal message_type value                       blocker
  CAUGHT confidence out of range                          blocker
  CAUGHT comma instead of the spec separator              blocker
  CAUGHT hallucinated evidence id                         blocker
  CAUGHT empty evidence written as blank, not 'none'      blocker
  CAUGHT row dropped from the artifact                    blocker
  CAUGHT degenerate output: one action for every row      high
  CAUGHT hardcoded answer table keyed by dataset id       blocker
  CAUGHT dataset id compared in decision logic            blocker
  quiet  dataset id in a comment                          (must stay quiet)
  quiet  dataset id in a docstring                        (must stay quiet)
  quiet  single fixture assignment                        (must stay quiet)

SELFTEST PASSED — baseline clean, 10/10 injected defects caught,
                  3/3 benign cases quiet.
```

Both halves matter. The three `quiet` rows are the positive control: an audit
that fires on everything is as useless as one that fires on nothing, and this
particular audit has a documented history of a confident BLOCKER on a healthy
repository.

**It found a real gap on its first run.** The leakage audit excluded assignment
lines — a fix for that earlier false positive — which meant
`SPECIAL = {"msg_002": ("notify", "urgent")}` slipped through: an assignment
*and* a hardcoded answer table. Two forms now survive the exclusion: an id used
as a mapping key, and two distinct ids on one line.

The test suite applies the same standard to itself, including a negative
control *on* the selftest — swap in an evaluator that finds nothing and
`selftest` must go red, otherwise a passing run proves only that it ran.

## The framework caught itself

Twice, and both are preserved rather than quietly patched.

The first `label-leakage` audit reported a confident **BLOCKER on a healthy
repository** — three bugs at once: it scanned exploratory scripts as
production, matched synthetic fixture variables as dataset ids, and treated
docstrings as executable code. Engineering Memory then attached an unrelated
entry as "prior art" on a single shared word. Postmortem in
[`leakage.py`](./orchestrate_kit/evaluator/plugins/orchestrate/leakage.py).

Later, memory search itself was matching *substrings*: `"code" in
"cross-encoder"` is true, which attached a retrieval decision to a source-code
question. Fixed with tokenized matching; the test is
`test_search_floor_suppresses_incidental_matches`.

> A clean, confirming result from a broken audit is the most dangerous output
> in engineering.

---

## The written methodology

| Document | What it is |
|---|---|
| **[PLAYBOOK.md](./PLAYBOOK.md)** | 20 rules for building AI systems whose correctness you can prove |
| **[TIMELINE.md](./TIMELINE.md)** | A real F-1…F-48 defect history — including three audits that were themselves wrong |
| **[JUDGE-PREP.md](./JUDGE-PREP.md)** | Topics an AI judge actually probed, verbatim feedback, and 10 claims never to make |
| **[RELEASE-CHECKLIST.md](./RELEASE-CHECKLIST.md)** | Final gate, ordered so the cheapest checks catch the worst defects |
| **[RESEARCH.md](./RESEARCH.md)** | Sourcing for every claim, tagged `[evidence]` or `[inference]` |
| **[SCORING-HEURISTIC.md](./SCORING-HEURISTIC.md)** · **[FAQ.md](./FAQ.md)** | Self-scoring rubric · common questions |
| **[docs/adr/](./docs/adr/)** | 6 Architecture Decision Records for the biggest engineering calls (deterministic routing, constrained arbitration, Engineering Memory, negative controls, plugin architecture, and a comparative review against TencentDB Agent Memory) — each cross-referenced to the `orchestrate memory recall` entry with the actual measurement behind it |
| **[ARCHITECTURE_EVOLUTION.md](./ARCHITECTURE_EVOLUTION.md)** | How the memory system's architecture should change across 4 growth stages (solo → small OSS → large community → multi-org), with numeric triggers (entry count, maintainer count, plugin count) for each transition |

Governance for a single-maintainer project with no external contributors
yet is folded into [CONTRIBUTING.md](./CONTRIBUTING.md#what-must-never-change)
rather than five separate documents — process built ahead of the team that
needs it is exactly the kind of generalization this project stays away
from. This repo has one mission: the highest-quality toolkit for
HackerRank Orchestrate. Everything here optimizes for that, not for
looking like infrastructure for a scale that doesn't exist yet.

The `orchestrate_kit` corpus is the same knowledge in executable form. Where
`TIMELINE.md` tells you dense embeddings lost, `orchestrate memory why-not
embeddings` gives you the number, the variants tried, and the condition under
which re-opening it would be correct.

Three things worth taking even if you read nothing else:

**Prove the counterfactual.** To claim a component drives an outcome, disable it
and show the outcome *stops*. "It works with OCR on" is compatible with OCR
being decorative.

**Rejection is a deliverable.** "We use embeddings" is a claim anyone can make.
"We measured embeddings at F1 0.479 against 0.512 and did not ship them" cannot
be faked.

**Attack your own measurement.** Three audits in the reference build were wrong,
and each produced a clean, confirming result.

---

## The 34 Agent Skills

Drop-in skills for Claude Code, Cursor, Codex, Cline, Gemini CLI, and anything
else that reads `SKILL.md`. They trigger automatically from their description —
no slash commands.

```bash
cp -r skills/* your-project/.claude/skills/
```

**Audit tier** — from building and auditing a complete submission to
destruction:

| Skill | Answers |
|---|---|
| [`spec-auditor`](./skills/orchestrate-spec-auditor) | Does it match the spec *literally*? |
| [`submission-validator`](./skills/orchestrate-submission-validator) | Are all artifacts current and consistent? |
| [`multimodal-auditor`](./skills/orchestrate-multimodal-auditor) | Does media actually change a decision? |
| [`dataset-coupling-auditor`](./skills/orchestrate-dataset-coupling-auditor) | Will it survive data I have not seen? |
| [`determinism-auditor`](./skills/orchestrate-determinism-auditor) | Is it reproducible, and where does that stop? |
| [`security-auditor`](./skills/orchestrate-security-auditor) | Does every hostile input yield a valid row? |
| [`confidence-calibrator`](./skills/orchestrate-confidence-calibrator) | Am I calibrating to the labels or to a textbook? |
| [`evidence-retrieval-expert`](./skills/orchestrate-evidence-retrieval-expert) | Is a retrieval gain even possible? |
| [`rule-engine-architect`](./skills/orchestrate-rule-engine-architect) | Rules or an LLM — and is any rule dead? |
| [`interview-coach`](./skills/orchestrate-interview-coach) | Do I own every number in my code? |
| [`release-engineer`](./skills/orchestrate-release-engineer) | Does it work on someone else's machine? |
| [`mentor`](./skills/orchestrate-mentor) · [`evaluator`](./skills/orchestrate-evaluator) | Should I make this change? Am I improving? |

**Core flow** — `phase-gates` · `agent-architecture` · `robustness` ·
`justification-quality` · `ai-collaboration-transcript` · `self-scoring` ·
`interview-readiness` · `submission-review`

**Tactical** — `schema-guardrails` · `failure-handling` · `naming-and-structure`
· `secrets-and-determinism` · `edge-case-testing` · `prompt-engineering` ·
`multi-strategy-evaluation` · `cost-and-ops-metrics` ·
`multimodal-evidence-grounding` · `escalation-design`

**Design & resilience** — `input-tracing` ·
`input-validation-and-overrides` · `checkpoint-resilience`

Every skill states its evidence tier. Nothing here claims access to
HackerRank's internal scoring.

---

## For HackerRank Orchestrate specifically

HackerRank has published how Orchestrate scores a submission. Most participants
never read it before they start:

| Artifact | Weight | What it measures |
|---|---|---|
| Code zip | 30% | Agent design, architecture, robustness — *"actual agent loops versus hardcoded workflows"* |
| Output CSV | 30% | Correctness against a golden dataset, **and whether each decision has a sound justification** |
| AI chat transcript | 10% | How you *directed* your AI tools — planning, constraints, debugging |
| AI judge interview | 30% | Technical depth, communication, and **self-awareness about your own system's limitations** |

From their own post-mortem: **"No single metric reproduces the leaderboard."**
The winners were balanced across all four signals.

The `hackerrank-orchestrate` plugin detects by dataset *shape*
(`dataset/messages.csv` + `problem_statement.md`), not by repo name, so it works
for any season.

## Beyond the contest

Strip away the HackerRank framing and what remains is general engineering
discipline: measure before you build, record what you rejected and why, attack
your own harnesses, state boundaries on every guarantee, and be able to defend
each number in your code. The evaluator's generic plugin, the mentor's taxonomy,
and every judge persona are domain-independent.

## Transcript engineering

```bash
orchestrate transcript analyze my-chat-log.txt
orchestrate transcript compose "choose a retrieval method" --stage design
```

HackerRank's own published methodology states the AI Chat Transcript score
measures how you *directed* your coding agent, not what it produced —
Direction & Architecture Ownership alone is weighted 35%. `analyze` scores
a transcript against the real published rubric (4 dimensions, real
weights) and names which behaviors are present or missing.
`compose` fills one of 9 prompt blueprints with your real inputs and
Engineering Memory hits, so the generated prompt makes the rubric's own
criteria the literal shape of your next message.

**Stated honestly, not hedged:** this scores the *shape* of a transcript —
ownership language, named alternatives, reported measurements — never
whether the underlying claims are true, and it is **not a prediction of
your real HackerRank score**: no ground-truth graded transcript exists to
calibrate against. Verified to actually discriminate — a weak sample
transcript scores 0.0, a strong one scores 81.8, on the real rubric
weights, not asserted. See
[`skills/orchestrate-transcript-engineering`](./skills/orchestrate-transcript-engineering).

## GitHub Action

```yaml
- uses: actions/checkout@v4
- uses: NITISH-R-G/hackerrank-orchestrate-skills/action@master
  with:
    path: "."
```

Evaluates your repo on every push/PR, uploads the report as a build
artifact, comments the result on the PR (updated in place, not spammed),
and fails the build on a release blocker. Outputs (`score`, `verdict`,
`blockers`, `report-path`) are read off the real `Evaluation` object, not
scraped from terminal text — see [`action/README.md`](./action/README.md).

Not a claim it works: `.github/workflows/action-selftest.yml` runs this
exact `uses:` line against this repository on every push, and the [Actions
tab](https://github.com/NITISH-R-G/hackerrank-orchestrate-skills/actions/workflows/action-selftest.yml)
shows the real, current result.

## Examples

[`examples/python-quality-plugin`](./examples/python-quality-plugin) — a
second, independent evaluator plugin (two AST-based Python static checks),
proving the plugin system generalizes beyond the first-party Orchestrate
plugin. Run against `orchestrate_kit`'s own production code, the measured
result is `READY score 100/100` — zero bare excepts, zero mutable default
arguments, checked, not asserted.

## Measured performance

[`BENCHMARKS.md`](./BENCHMARKS.md) — wall-clock and peak-memory numbers for
every CLI command, regenerable on your own machine with
`python -m orchestrate_kit.bench > BENCHMARKS.md`. Every number is a cold
subprocess run (real Python startup included, the way a user actually
experiences it), 5 repeats, mean/min/max/stdev reported — a property of this
repository on the machine that ran it, not a universal performance claim.

Coverage is measured the same way: **72%** total
(`pytest --cov=orchestrate_kit`), reported honestly with no target attached
— see [ROADMAP.md](./ROADMAP.md) for the two modules that are the real gaps.

## Project status

| | |
|---|---|
| Tested Python versions | 3.10 and 3.13 via CI matrix; `pyproject.toml` declares `>=3.10` with no upper cap (untested versions above 3.13 may work — they just aren't in the matrix yet) |
| Tested platforms | Ubuntu, Windows (CI matrix — Windows is there on purpose: a Windows-only path bug has already shipped once) |
| Runtime dependencies | 0 |
| Tests | 57, plus the example plugin's own 16 |
| Self-audit | Every CI run evaluates, self-tests, and interviews-against THIS repo — the `dogfood-self-audit` artifact on any run's [Actions tab](https://github.com/NITISH-R-G/hackerrank-orchestrate-skills/actions) is `orchestrate evaluate .` / `selftest` / `mentor` / `interview`'s real, current output, not a claim |
| Changelog | [CHANGELOG.md](./CHANGELOG.md) |
| Roadmap | [ROADMAP.md](./ROADMAP.md) |
| Security policy | [SECURITY.md](./SECURITY.md) |
| Getting help | [SUPPORT.md](./SUPPORT.md) |
| Code of conduct | [CODE_OF_CONDUCT.md](./CODE_OF_CONDUCT.md) |

## Contributing

See [CONTRIBUTING.md](./CONTRIBUTING.md). Every claim needs a traceable source.
For code: new audits need a negative control proving they can fail, and new
memory entries with `status: rejected` need a `reconsider_if`.

A `.devcontainer/` and `.vscode/launch.json` are included — clone, open in
VS Code / GitHub Codespaces, and `mentor`/`interview`/`selftest`/pytest are
all one-click debuggable runs, no manual setup.

Also available inside
**[skills-i-use](https://github.com/NITISH-R-G/skills-i-use)** — 480+ reviewed
Agent Skills.

## License

MIT — see [LICENSE](./LICENSE).

---

*Not affiliated with or endorsed by HackerRank. Built by studying their public
writing and official public repositories.*
