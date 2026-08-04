# Third-party notices

## TencentDB Agent Memory

**Source:** https://github.com/TencentCloud/TencentDB-Agent-Memory
**Copyright:** Copyright (C) 2026 Tencent
**License:** MIT

Two design *ideas* from that project's publicly documented architecture
informed changes to `orchestrate_kit`'s Engineering Memory, recorded in
[`docs/adr/0006-agent-memory-comparative-review.md`](./docs/adr/0006-agent-memory-comparative-review.md):

1. **Context/output budget capping** — their retrieval layer bounds results
   by item count, character budget, and timeout so memory doesn't overwhelm
   an agent's context window. Adapted (not copied) as `MAX_BENCHMARKS_SHOWN`
   in `orchestrate_kit/mentor/engine.py`, which caps how many benchmark
   lines a single prior-art entry shows in a mentor report.
2. **Relating memory records to the code they describe** — their CodeGraph
   asset type indexes code so an agent can check impact before modifying it.
   Adapted, scoped down to what this project can honestly build on a flat
   JSON store with no code parser, as `EngineeringMemory.verify_files()` /
   `orchestrate memory verify` in `orchestrate_kit/memory/store.py` —
   existence-checking for files an entry cites, not call-graph analysis.

**No source code, configuration, documentation text, or other content from
TencentDB Agent Memory is included, copied, or reproduced in this
repository.** Both features above are original Python implementations,
written to fit `orchestrate_kit`'s existing conventions (zero runtime
dependencies, flat JSON storage, CLI-first), reviewed and decided on the
merits documented in ADR-0006 — including several ideas from the same
project that were deliberately **not** adopted, with reasons, in that same
ADR.

This notice exists because good practice around building on someone else's
publicly documented work is to say so clearly, not because MIT requires
crediting an idea you didn't copy the expression of — only copied
*code or text* would carry that obligation, and none was copied.

---

Everything else in this repository — `skills/`, `orchestrate_kit/` outside
the two items above, and all documentation — is original work. See
[LICENSE](./LICENSE) for this repository's own MIT terms.
