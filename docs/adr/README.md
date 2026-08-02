# Architecture Decision Records

Short, single-decision documents — context, decision, consequences,
alternatives considered — instead of the same reasoning scattered across
README prose. Format: [MADR](https://adr.github.io/madr/), lightly adapted.

Every ADR here is a **write-up** of a decision this repository already made
and shipped, cross-referenced to the Engineering Memory entry that has the
actual measurements (`orchestrate memory recall <key>`). An ADR without a
traceable measurement behind it would be exactly the kind of assertion this
project's own standard refuses to make.

| ADR | Decision | Status |
|---|---|---|
| [0001](./0001-deterministic-rule-engine.md) | Deterministic rule engine over an LLM classifier | Accepted |
| [0002](./0002-constrained-arbitration.md) | LLM arbitration is opt-in and structurally boxed in | Accepted |
| [0003](./0003-engineering-memory.md) | Engineering Memory as a first-class artifact, not tribal knowledge | Accepted |
| [0004](./0004-negative-controls.md) | Every audit requires a negative control before it ships | Accepted |
| [0005](./0005-plugin-architecture.md) | Black-box-first plugin architecture | Accepted |

## Writing a new one

Copy the shape of an existing ADR. A decision earns one when reversing it
would cost real rework — not every choice needs a record, only the ones a
future contributor would otherwise have to reverse-engineer from git blame.
