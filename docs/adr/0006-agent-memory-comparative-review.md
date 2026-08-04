# ADR-0006: Comparative review against TencentDB Agent Memory

**Status:** Accepted
**Inspired by:** [TencentCloud/TencentDB-Agent-Memory](https://github.com/TencentCloud/TencentDB-Agent-Memory)
(MIT license). No code from that project is included here — see
[THIRD_PARTY_NOTICES.md](../../THIRD_PARTY_NOTICES.md) for exactly what is
and isn't attributed, and why.

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
