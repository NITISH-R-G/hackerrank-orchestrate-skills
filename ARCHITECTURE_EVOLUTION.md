# Architecture Evolution

`orchestrate_kit`'s current architecture is correct **for its current
scale**. That sentence has a trap in it: every rejection recorded in
[`docs/adr/0006`](./docs/adr/0006-agent-memory-comparative-review.md) was
tested against *today's* repository — a solo maintainer, ~45 memory
entries, one plugin author. None of those rejections were tested against
"what if this becomes one of the largest engineering-memory projects on
GitHub." This document does that test, concept by concept, from first
principles — not to justify a rewrite, but to find out which "no"s were
actually "not yet," and to write down the exact condition that flips each
one, so scaling this project is a sequence of deliberate, measured
decisions instead of a scramble.

**Nothing in this document is implemented today.** Where a trigger has
already been reached, or is cheap enough to be worth building now anyway,
that's called out explicitly — everything else stays a documented
intention until its condition is met.

---

## Part 1 — Reopening every rejected concept

Method, per concept: restate the original reason → find the assumptions
hiding inside it → test each assumption against thousands of entries,
dozens of contributors, hundreds of plugins/ADRs, multiple maintainers,
multiple organizations → decide: still correct / becomes optional /
becomes plugin-based / moves to roadmap / should be built now → if not
now, the exact trigger.

### 1. Memory hierarchy (L0 raw → distilled layers)

**Original reason:** no raw material exists to distill from — entries are
authored directly by a human.

**Hidden assumptions:** (a) entries will always be *authored*, never
*extracted* from something rawer; (b) one flat layer is skimmable
regardless of corpus size.

**At scale:** (a) breaks the moment entries start being *proposed* by
automation — a bot surfacing candidate memory entries from repeated CI
failures, flagged PR discussions, or recurring `orchestrate mentor`
queries. At that point there genuinely is a "raw" layer (the automated
proposal) distinct from a "distilled" one (the reviewed, merged entry).
(b) breaks on volume alone: nobody skims 5,000 entries the way they skim
45.

**Decision: moves to roadmap, activates in two independent stages.**
- **Trigger A (raw layer):** the first time entry authorship becomes
  partly automated rather than 100% human-written — i.e., the moment a
  "proposed, unreviewed" status is needed at all.
- **Trigger B (digest layer):** entry count crosses roughly **500** —
  the point past which `orchestrate memory list`'s flat listing stops
  being something a new contributor reads end-to-end in one sitting.

**Design today, build later:** a `status: "proposed"` value already fits
the existing `status` field (currently `accepted | rejected | superseded`)
without a schema change — the extension point already exists.

### 2. Full lifecycle / access control

**Original reason:** no second user exists to gate.

**Hidden assumptions:** (a) one person remains the sole point of
curation indefinitely; (b) everything in memory is safe to be fully
visible to everyone with repo access.

**At scale:** both break, for different reasons. Dozens of contributors
breaks (a) — unilateral write access to a shared decision log doesn't
scale past a couple of trusted maintainers. Multiple *organizations*
breaks (b) completely: two companies both running `orchestrate_kit`
against their own codebases must never see each other's rejected ideas,
which today isn't even a *risk* — the memory store is one JSON file per
repository checkout, so cross-organization leakage is structurally
impossible until a shared/hosted deployment model exists at all.

**Decision: two different features, two different triggers — don't
conflate them the way the original rejection did.**
- **Write protection** (not full ACL — just "who can merge a memory
  change"): trigger = **second regular maintainer**. This is a PR-review
  policy question (CODEOWNERS already exists for this), not new code.
- **Multi-tenant visibility** (real ACL, Tencent's actual model):
  trigger = the first time `orchestrate_kit` is deployed as a **shared
  service** rather than "one JSON file per git checkout" — which is a
  deployment-model change, not a feature to bolt onto the current one.
  Not worth designing in detail until that deployment model is real;
  premature ACL design for a file format would guess at requirements a
  service architecture would actually define.

### 3. Memory quality gate beyond rejections

**Original reason:** real but minor gap; not worth guessing at what
"enough evidence" means for a non-rejection.

**Hidden assumptions:** (a) the sole author's judgment scales as the only
quality gate; (b) an unfounded *finding* is less costly than an unfounded
*rejection* because it doesn't block anything.

**At scale:** (a) is the load-bearing assumption and it fails outright
past a couple of contributors — "I'll just review it myself" stops being
a policy once review volume exceeds one person's bandwidth. (b) doesn't
even hold today: a wrong "finding" misleads a mentor query exactly like a
wrong rejection would, it's simply less visible because rejections are
the ones enforced.

**Decision: should actually be built, and cheaply — this is the one
rejection in this whole review that the original ADR under-weighted.**
The enforcement pattern already exists for rejections (`reconsider_if` is
refused if empty). Extending "evidence OR benchmarks required" to every
entry, not just rejections, is the same mechanism, not a new one.
- **Trigger:** entry count exceeds **150**, OR a second regular
  contributor joins — whichever comes first. Below that, one author's
  self-review is a real, sufficient gate; above it, it structurally isn't.

### 4. Consolidation (duplicate / near-duplicate entries)

**Original reason:** no duplicate-entry problem exists at ~45
single-author entries.

**Hidden assumptions:** (a) low contributor count keeps duplication low
because one person remembers the whole corpus; (b) manually running
`orchestrate memory search` before adding an entry is sufficient
prevention.

**At scale:** (a) fails precisely the way the *code*-decision problem
this whole system exists to solve fails without it — dozens of
contributors independently rediscovering and re-rejecting the same idea
is the exact failure mode Engineering Memory prevents for code, recurring
one level up, for the memory records themselves.

**Decision: moves to roadmap, mechanically cheap when it arrives** — the
`score()` function driving `search()` already computes the similarity
number a duplicate-warning needs; no new retrieval mechanism is required,
only a threshold and a warning path in `memory add`.
- **Trigger:** corpus exceeds **150 entries**, OR **3 near-duplicate
  submissions** have actually occurred (tracked informally until then —
  building automated detection before a single real duplicate has
  happened would be solving a hypothetical).

### 5. Aging / expiration

**Original reason:** any usage-tracking mechanism requires mutating
`memory.json` on every read, which conflicts with ADR-0003's stated goal
of a store reviewed in a git diff, not one that changes on every CLI
invocation.

**Hidden assumptions — this is the one where re-examining from first
principles changes the answer:** the original rejection conflated **two
different mechanisms** under one label. (a) *Usage-count tracking*
("how many times has this been retrieved") genuinely requires a write on
every read, and that conflict is real. (b) *Staleness-by-content*
("has the file this entry describes changed materially since the entry
was written") requires no such thing — it's a comparison made *at
`orchestrate memory verify` time*, against a hash captured once, at
authoring time, as a normal reviewed write.

**At scale:** with hundreds of entries citing real files (once `files=`
population becomes routine rather than exceptional, per ADR-0006), a
decision entry silently going stale — the code it describes was rewritten
years after the entry was written — becomes a real, recurring risk. This
is a case where the assumptions from the *first* review (small corpus, one
author who happens to remember the codebase) were doing real work, and
they clearly don't hold at scale.

**Decision: split the concept — usage-count tracking stays rejected;
content-staleness detection should actually be built, as a natural
extension of the already-shipped `verify_files()`.**
- Add an optional `files_hash` field, populated at authoring time
  (a normal, reviewed write — not a read-time mutation), compared against
  the current file content during `orchestrate memory verify`.
- **Trigger:** the next time a `files=`-bearing entry is added, since the
  mechanism costs almost nothing beyond what `verify_files()` already
  does. This is the cheapest trigger in this document, precisely because
  the infrastructure it extends already shipped.
- Usage-count tracking itself stays rejected at every stage in this
  document — the read/write conflict with the git-diff design goal
  doesn't change with scale, only the value of the feature does, and it's
  never worth trading away diff-cleanliness for it while the store stays
  a flat file.

### 6. Conflict resolution

**Original reason:** human review-before-merge already is the
conflict-resolution mechanism at this scale.

**Hidden assumptions:** (a) a single reviewer holds the whole corpus in
their head well enough to catch a contradiction at merge time.

**At scale:** (a) fails outright past a few hundred entries — nobody
holds a corpus that size in working memory, and a contradiction between
two 2-year-apart entries is exactly the kind of thing that survives
individual review indefinitely.

**Decision: moves to roadmap**, and can share machinery with
consolidation (§4) — a contradiction check is a near-duplicate check with
a different question ("do these overlapping-tag entries reach opposite
`chosen` conclusions?" instead of "are these the same idea twice?").
- **Trigger:** corpus exceeds **300 entries**, OR **3+ regular
  maintainers**, whichever first — the same order-of-magnitude signal as
  consolidation, roughly double the threshold, because contradiction is
  rarer than duplication.

### 7. Indexing (BM25 / vector retrieval)

**Original reason:** rejected on this project's own prior measurement,
`D-dense-retrieval` — dense retrieval lost to lexical, F1 0.479 vs 0.512.

**Hidden assumptions — the most important catch in this whole
review:** that measurement was run on a **different corpus and a
different task** — matching short evidence-citation ids against a query,
on ~28 labeled rows, where the relation being scored was near-exact
topical overlap. Treating it as settled evidence for *Engineering
Memory's own* prose search — much longer documents, freer vocabulary,
paraphrase-shaped queries like "why did we decide against X" — is
reusing a measurement outside the conditions that produced it. That's a
methodological gap the original rejection didn't flag, and this review
should be honest that it exists.

**At scale:** a corpus of thousands of prose entries is exactly the
regime where lexical-only search starts missing paraphrased queries a
human would recognize as relevant. Whether dense/hybrid retrieval
actually wins THERE is unmeasured — the old result doesn't transfer, and
guessing which way it goes would be exactly the kind of invented claim
this project refuses elsewhere.

**Decision: not "adopt dense retrieval" — architect for a re-measurement,
without paying the cost until the measurement says to.**
- Extract `search()`'s scoring into a swappable interface (a `Scorer`
  protocol `EngineeringMemory` delegates to) now that the concept has been
  named — cheap, and it's the same pattern `evaluator/plugin_api.py`
  already uses for audits.
- **Trigger to re-measure (not to adopt):** corpus exceeds **500
  entries**, OR 3+ anecdotal reports of "I know this is in memory and
  search didn't find it." Re-measure lexical vs dense vs hybrid *on the
  actual Engineering Memory corpus*, the same rigor `D-dense-retrieval`
  used, not a re-application of its number to a different problem.
- Ships as **optional** even if the re-measurement favors a heavier
  method — the zero-runtime-dependency core stays the default; a vector
  backend becomes an install extra (`orchestrate-kit[retrieval]`), the
  same pattern proposed for summarization below.

### 8. Automatic summarization

**Original reason:** requires an LLM call, breaking the
zero-runtime-dependency, offline-by-design guarantee `pyproject.toml`
states as a deliberate constraint.

**Hidden assumptions:** (a) summarization always requires a live model
call; (b) the zero-dependency constraint must apply to *every* feature,
not just the core install.

**At scale:** (a) is largely still true — extractive/statistical
summarization is weak compared to what an LLM produces, and this
project's own standard (never fabricate, always attribute a claim to its
source) makes a *lossy, unreviewed* auto-summary of a thousand-entry
corpus a real integrity risk if presented as authoritative. (b) is where
the rejection over-reached: the core guarantee protects `pip install
orchestrate-kit` working on a plane with no key — it was never a claim
that *no* optional feature may ever touch a network.

**Decision: plugin-based, matching ADR-0005's existing architecture
exactly** — an optional extra, not a core dependency, and its output
explicitly labeled as generated/unreviewed rather than presented as a
memory entry with the same authority as a human-authored one.
- **Trigger:** entry count exceeds **1,000**, OR a new contributor's
  first full read-through of the corpus is reported to exceed roughly
  **30 minutes** — the point where skimming stops working and *something*
  needs to compress the corpus for a first pass, with the human still
  reading the real entries for anything that matters.

### 9. Retrieval-planning improvements beyond what already exists

Not actually rejected in ADR-0006 — marked "already satisfied"
(`list` → `recall` → `search()` already forms a tiered plan). Restated
here only because it's the foundation §7's `Scorer` interface builds on:
nothing about tiering needs to change at scale, only what backs the
`search()` tier once §7's trigger is reached.

---

## Part 2 — The four stages

Each stage lists what's true about the project at that point, which
triggers from Part 1 have fired, and what the architecture looks like as
a result. Moving between stages is driven by the measured triggers above,
not a calendar.

### Stage 1 — Solo developer *(current)*

- ~45–150 memory entries, one maintainer, one first-party plugin + one
  example plugin.
- Flat JSON store, term-overlap search, no ACL, no consolidation, no
  usage tracking. Every rejection in Part 1 is still fully correct here —
  none of the triggers have fired.
- Quality gate: the author's own review, enforced structurally only for
  rejections (`reconsider_if`).

### Stage 2 — Small open-source project

**Enters when:** entry count crosses ~150, OR a second regular
contributor joins.

- **Quality gate extends to every entry** (§3) — the cheapest trigger to
  reach, because it reuses existing enforcement machinery.
- **Duplicate warning on `memory add`** (§4) activates around the same
  entry count, using the existing scorer.
- **Write protection** (§2) becomes a PR-review policy question the
  moment there's a second maintainer — `CODEOWNERS` already exists for
  this; no new code.
- **Staleness-by-hash** (§5) is live from the first `files=`-bearing
  entry onward — it doesn't wait for Stage 2, it's cheap enough to ship
  as soon as it's built.
- Storage, retrieval, and hierarchy are unchanged from Stage 1 — nothing
  here yet requires them.

### Stage 3 — Large community project

**Enters when:** entry count crosses ~300–500, OR 3+ regular maintainers,
OR dozens of plugins/hundreds of ADRs exist.

- **Contradiction detection** (§6) activates, sharing machinery with
  Stage 2's duplicate detector.
- **Retrieval re-measurement** (§7) happens here — the `Scorer` interface
  built in Stage 2 gets its first real alternative backend measured
  against it, on the actual corpus, not a borrowed number.
- **Raw/proposed entry layer** (§1, trigger A) activates *if and only if*
  entry authorship has started including automated proposals by this
  point — otherwise it stays deferred, because the precondition
  (something raw to distill), not the corpus size, is what actually
  gates it.
- **Digest/summary layer** (§1 trigger B, §8) becomes worth building once
  a full read-through stops being feasible in one sitting — likely
  somewhere in this stage, confirmed by the ~30-minute anecdotal signal
  rather than assumed from entry count alone.
- Plugin ecosystem: the scaffold (`orchestrate plugin new`) and the
  negative-control requirement already scale to "hundreds of plugins"
  without change — that architecture was built plugin-first from
  ADR-0005 onward specifically so this stage wouldn't need a redesign.

### Stage 4 — Multi-organization engineering platform

**Enters when:** `orchestrate_kit` is deployed as a shared service across
more than one organization, rather than one JSON file per git checkout.

- This is a **deployment-model change, not a feature addition** — the
  honest position from §2 stands: designing multi-tenant ACL in detail
  before this deployment model is real would be guessing at requirements
  a service architecture should define, not the file format extending to
  meet them.
- What *should* carry forward unchanged into this stage: the `Scorer`
  interface, the plugin contract, the Engineering Memory schema itself
  (kind/status/tags/phase/blast_radius/reconsider_if/depends_on/
  supersedes/files/commit already generalize past a single repository).
  What changes is the transport and the access model around them, not the
  data model documenting a decision.
- If this stage is ever reached, it deserves its own ADR at that time,
  written against the real requirements of whoever is running it — not
  spelled out speculatively here.

---

## What this document is not

Not a commitment to build all of this. Every item above stays
undesigned-in-detail and unimplemented until its trigger fires, exactly
as [`ROADMAP.md`](./ROADMAP.md) already treats every other future item —
the difference here is that "not now" comes with the specific, measurable
condition that would make it "now," instead of standing as a flat no.
