# ADR-0006: Comparative review against TencentDB Agent Memory

**Status:** Accepted
**Inspired by:** [TencentCloud/TencentDB-Agent-Memory](https://github.com/TencentCloud/TencentDB-Agent-Memory)
(MIT license). No code from that project is included here — see
[THIRD_PARTY_NOTICES.md](../../THIRD_PARTY_NOTICES.md) for exactly what is
and isn't attributed, and why.
**See also:** [ARCHITECTURE_EVOLUTION.md](../../ARCHITECTURE_EVOLUTION.md)
reopens every concept rejected below from first principles, against a
5-year, thousands-of-entries, multi-organization scale, with a measured
trigger for each one.

## Context

TencentDB Agent Memory is a production-oriented, DB-backed memory *service*
for live conversational AI agents: a Node.js/TypeScript system (MemoryCore +
Memory Hub + Proxy) that extracts four asset types — Chat Memory, Skill,
Wiki, CodeGraph — from conversations, documents, and codebases, and serves
them to multiple agents and human team members with ownership, versioning,
and access control. It was asked to be evaluated as a candidate to replace
or substantially redesign `orchestrate_kit`'s Engineering Memory.

## What was actually reviewed

The public README's stated architecture (installation model, the four asset
types, the L0→L3 layered distillation pipeline for Chat Memory, the
BM25+vector+RRF retrieval strategy with item/character/timeout budget caps,
the ownership/visibility/ACL model, and the published PersonaMem benchmark).
Not the implementation source — a fair comparison of engineering decisions
doesn't require re-deriving code, and reproducing theirs here would exceed
what a design review needs.

## The finding that matters most: these solve different problems

TencentDB Agent Memory answers *"what does this live agent, across many
users, sessions, and teams, need to recall right now, retrieved from a
potentially huge and growing corpus of raw conversation history?"* — a
multi-tenant runtime retrieval problem, which is why it needs a database, an
access-control model, an async distillation pipeline, and a hybrid
retrieval stack with context-budget caps.

`orchestrate_kit`'s Engineering Memory answers *"what did this repository's
engineers already try, measure, and reject, and under what condition should
that be reconsidered?"* — a curated, human-authored decision log for ONE
codebase's own history. It has ~45 entries, not an open-ended, growing
corpus of raw text; every entry is written and reviewed by a person, not
distilled from raw conversation; and there are no other users, teams, or
agents to grant access to.

Treating this as "which implementation is better" would be a category
error — the honest engineering comparison is "which of Tencent's *design
decisions*, if any, address a real gap in ours, independent of the runtime
substrate they built it on."

## Decision, subsystem by subsystem

| Subsystem | Their approach | Ours | Verdict |
|---|---|---|---|
| Storage | TencentDB, multi-service, DB-backed | Flat JSON file, git-diffable | **Kept.** A DB and three services would be pure overhead for ~45 human-curated records meant to be reviewed in a PR diff. This is a scale mismatch, not an inferiority. |
| Access control | private / team / restricted / agent, two-tier roles + ACLs | None — single maintainer | **Kept as-is (correctly).** [ADR-0003](./0003-engineering-memory.md) and [ROADMAP.md](../../ROADMAP.md)'s "explicitly not planned" section already cover why: there are no other users to gate yet. Building ACL infrastructure for a single-maintainer repo would be ceremony without substance. |
| Chat Memory's L0→L3 distillation | Async pipeline turning raw conversation into progressively distilled layers | Entries are written directly by a human at the "distilled" level | **Kept.** We have no raw material (chat logs) to distill — an entry IS already the L2/L3-equivalent output. Building an ingestion pipeline with nothing to ingest would be speculative infrastructure. |
| Retrieval | BM25 + vector + RRF hybrid, with fallback tiers | Term-overlap scoring with a title-weighted floor | **Kept**, and for a reason already recorded in *this repository's own* Engineering Memory before this review started: `D-dense-retrieval` measured dense/RRF retrieval against lexical on a comparable small, curated corpus and found no improvement (F1 0.479 vs 0.512). Adding a heavier retrieval stack for ~45 entries — small enough for a human to read every title in seconds — would violate a decision this project already made and measured, and would cost the zero-runtime-dependency guarantee `pyproject.toml` states as a deliberate constraint. |
| **Context/output budget capping** | Explicitly caps retrieved memory by item count, character budget, and timeout, "to prevent memory from overwhelming the context window" | No cap existed — a heavily-benchmarked prior-art entry could dominate a mentor report | **Adopted.** This is the one idea that transfers cleanly regardless of runtime: bounding how much of a single record gets surfaced by default, with an explicit way to see the rest. Implemented as `MAX_BENCHMARKS_SHOWN` in `orchestrate_kit/mentor/engine.py` — caps benchmarks *shown per entry* to 4, with an honest "+N more — `orchestrate memory recall <key>`" pointer to the full record. |
| **CodeGraph's "does this affect what changed"** | Indexes code symbols/calls so an agent can check impact before modifying code | The `files` field existed in the schema but was populated on 0 of 40 entries | **Adopted, honestly scoped down.** Full call-graph indexing is disproportionate to a JSON file with no code parser. What's genuinely buildable and valuable: let entries that describe *this repository's own code* cite the real file(s), and verify those paths still exist. `EngineeringMemory.verify_files()` / `orchestrate memory verify` does exactly that — existence-checking, not the deeper staleness-by-content-change analysis CodeGraph performs, because this project has no timestamp on an entry to compare a file's last-modified time against, and guessing would be exactly the kind of invented claim this project refuses elsewhere. |
| Skills as versioned, ACL'd runtime assets | Full lifecycle: versions, resource files, trigger boundaries, validation rules, private-by-default sharing | `skills/` is a flat directory of Markdown files, no runtime registry | **Not adopted, flagged for later.** A real gap likely exists (nothing currently links a skill to the measured finding that justified writing it), but building a "skill lifecycle" system on a guess, with no measured demand, would repeat the exact mistake `D-dense-retrieval` and `D-visual-model` both document: building the fashionable version of an idea before establishing there's headroom for it. Recorded in `ROADMAP.md` instead of built. |

## Consequences

- Engineering Memory's schema now has two categories of entry: those
  describing the historical Orchestrate submission (no `files`, correctly),
  and — new as of this ADR — a `5-orchestrate-kit` phase describing
  `orchestrate_kit`'s own real, verified development decisions, WITH
  accurate `files`. Five entries seeded this way; `orchestrate memory
  verify` checks them on demand (not yet wired into CI — see Roadmap below).
- A mentor report can no longer be dominated by one entry with many
  benchmarks; the cap is on display, never on the underlying record.
- Nothing about the storage format, retrieval algorithm, or access model
  changed. That is a decision, not an omission — see the table above for
  why each was measured against and kept.

## What was explicitly rejected, and why that's a real decision, not inaction

Rewriting the storage layer to a database, adding vector retrieval, or
building an ACL model would all have made this project's memory system
*more architecturally similar to Tencent's* without making it *better at
the problem it actually has*. "Looks more sophisticated" and "solves the
problem better" are different claims, and this repository's own standard
— stated in `PLAYBOOK.md` and enforced by `orchestrate mentor` on every
proposal — is to keep them separate.

## Reconsider if

`orchestrate_kit` grows multiple maintainers with genuinely private
in-progress entries (revisit access control), the memory corpus grows past
a size a human can skim (revisit retrieval), or a real, measured gap
appears in how skills relate to the findings that justify them (revisit
the skill-lifecycle idea, with numbers, the way every other entry in this
memory system is required to.)

---

## Addendum: mining the architecture concept by concept

The table above compared subsystems. This addendum treats
TencentDB Agent Memory purely as a source of *engineering concepts* —
ignoring their runtime (database, TypeScript, ACLs, distributed services)
entirely — and checks each one against this project independently. Facts
about their system are drawn from their public README; anything not stated
there is marked unknown rather than guessed.

| Concept | How Tencent uses it | Do we have an equivalent? | Would it genuinely help? | Verdict |
|---|---|---|---|---|
| **Memory hierarchy** | L0 raw conversation → L1 atoms → L2 scenarios → L3 persona; each layer distilled from the one below | No — an entry is authored directly at what would be their L2/L3 level | No: there is no raw L0 material to distill FROM. Building the layers with nothing under them is scaffolding, not architecture | **Rejected.** Solves an ingestion problem we don't have. |
| **Memory lifecycle** | private → reviewed → team-shared; ownership and status tracked | Partially — `status` (accepted/rejected/superseded) IS a lifecycle | A private/shared distinction needs more than one person to mean anything | **Kept minimal**, correctly — see ADR-0003, ROADMAP.md. |
| **Memory evolution** | assets get new versions as understanding changes | `supersedes` field, rendered in the decision graph | Already present and tested | **Already satisfied** — no action needed. |
| **Memory compression** | not explicitly named as a mechanism in the README beyond the layering itself | `Benchmark.line()` renders a full record's measurement as one compact string; `orchestrate memory list` shows title-only vs `recall` showing full detail | Already present in a form suited to a static store (no distillation pipeline needed to compress something a human wrote concisely to begin with) | **Already satisfied.** |
| **Memory importance** | usage counts are tracked and shown per asset in the panel | None — no ranking beyond text relevance existed before this pass | Yes: an entry many others depend on is more load-bearing, and that's cheap and honest to compute from data already in the schema | **Adopted** — `centrality()` / `<-N` in `memory list`. |
| **Memory relationships / graph** | assets have ownership and version relationships; not described as a full dependency graph in the README | `depends_on`, `supersedes`, rendered as a real Mermaid decision graph (`orchestrate graph`) | Already present, and arguably more explicit than what's documented of theirs | **Already satisfied.** |
| **Provenance** | ownership (who), version, status shown per asset | `commit` field existed in the schema, populated on 0/40 entries before this pass | Yes — concretely: "which commit made this true" is checkable and cheap | **Adopted** — `commit=` on the 5 orchestrate_kit-native entries, `verify_commits()`. |
| **Retrieval planning** | quick L2/L3 bootstrap first; fall back to precise BM25+vector+RRF over L1/L0 only when needed | `memory list` (compressed overview) vs `memory recall <key>` (full detail) vs `search()` (ranked, capped) is already a two-tier plan of the same SHAPE | Already present, at a complexity appropriate to ~45 entries vs their unbounded corpus | **Already satisfied** (independently arrived at, not copied). |
| **Memory quality** | Skills carry validation rules and trigger boundaries before being trusted | `reconsider_if` is enforced (refused without one) for rejections only; non-rejected findings have no equivalent enforcement | A real, if minor, gap — but low urgency: every entry is already reviewed by the sole author before merging | **Not adopted.** Flagged in ROADMAP.md rather than built on a guess at what "enough evidence" means for a non-rejection. |
| **Memory scoring** | implicit in BM25+vector+RRF ranking | `score()` term-overlap ranking exists; no separate "quality score" | Covered by "importance" above; a second, different scoring axis isn't justified without a demonstrated need | **Not adopted**, folded into the importance decision above. |
| **Memory consolidation** | not explicitly described as automatic merging in the README | None | At ~45 human-curated entries with one author, duplicate/near-duplicate entries haven't occurred — the failure mode consolidation prevents doesn't exist here | **Rejected**, explicitly: no evidence of the problem it would solve. |
| **Memory aging / expiration** | usage counts tracked; no explicit TTL/expiration mechanism stated in the README | None | Rejected on a design-principle ground, not a laziness one: any usage-tracking mechanism would require mutating `memory.json` on every read (search/recall), which conflicts with ADR-0003's explicit design goal — a store meant to be reviewed in a git diff, not one that changes on every CLI invocation | **Rejected**, with a stated principled conflict, not "not built yet." |
| **Conflict resolution** | not described in enough detail in the README to characterize honestly | None | At one author reviewing every entry before it merges, the review step IS the conflict-resolution mechanism | **Rejected** — the human-curation model already provides this. |
| **Memory indexing** | BM25 + vector, chosen for corpus sizes large enough to need it | Term-overlap over the full in-memory corpus | This project's OWN prior measurement (`D-dense-retrieval`) already tested exactly this question on a comparably small, curated corpus and found no benefit | **Rejected**, on this project's own prior evidence, not assumption. |
| **Automatic summarization** | conversations are distilled into atoms/scenarios by an async pipeline (implies a model call) | None — entries are authored directly, already concise | Would require an LLM call, breaking the zero-runtime-dependency, offline-by-design guarantee this whole toolkit is built on, to summarize material that's already hand-written and concise | **Rejected**, on a stated architectural constraint, not oversight. |
| **Structured metadata** | ownership, version, status, visibility, usage counts | `kind`, `status`, `tags`, `phase`, `blast_radius`, `reconsider_if`, `depends_on`, `supersedes`, `files`, `commit` | Already extensive; this pass populated two previously-unused fields (`files`, `commit`) rather than adding new ones | **Already satisfied** — this pass improved population, not the schema. |

### What this addendum changes about the verdict above

Nothing reverses. Of 18 concepts examined, **3 were genuinely adopted**
(context-budget capping, file-linkage/`verify_files`, and — new in this
pass — commit-provenance/`verify_commits` plus `centrality()`), **6 were
already independently satisfied** by this project's existing design in a
form suited to its own scale, and **9 were explicitly rejected**, each
with a stated reason tied to either a scale mismatch, a missing
precondition (no raw material, no multiple users), or a documented,
already-measured prior decision. None were rejected by default or by
inertia — that distinction is the entire point of doing this exercise
concept-by-concept instead of subsystem-by-subsystem.
