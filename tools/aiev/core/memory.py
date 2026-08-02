"""Engineering Memory — the knowledge graph of what was tried, and why.

CI logs tell you a check failed. Engineering Memory tells you:

    "This regression happened before. Here is the commit that fixed it, the
     evidence, and the two alternatives that were rejected -- and here is why
     the obvious fix is the one that made it worse last time."

Two record types, deliberately symmetric:

  Finding  a defect that was found and fixed
  Decision a choice that was made -- including choices to REJECT something

Most repositories preserve only successes. Rejections are first-class here,
because "we measured embeddings at F1 0.479 against 0.512 and did not ship them"
is the single least-fakeable statement an engineer can make (PLAYBOOK P5).

Storage is a JSON file. No database, no service. It is meant to be committed,
diffed and reviewed like source.
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from pathlib import Path


@dataclass
class MemoryEntry:
    key: str                       # stable id, e.g. "F-42" or "D-bm25"
    kind: str                      # "finding" | "decision"
    title: str
    problem: str = ""
    root_cause: str = ""
    chosen: str = ""
    rejected: list[str] = field(default_factory=list)
    evidence: str = ""
    impact: str = ""
    commit: str = ""
    files: list[str] = field(default_factory=list)
    tags: list[str] = field(default_factory=list)
    status: str = "accepted"       # accepted | rejected | superseded
    supersedes: str = ""
    lesson: str = ""

    def matches(self, q: str) -> bool:
        q = q.lower()
        hay = " ".join([
            self.key, self.title, self.problem, self.root_cause, self.chosen,
            " ".join(self.rejected), self.evidence, self.impact,
            " ".join(self.tags), self.lesson,
        ]).lower()
        return q in hay


class EngineeringMemory:
    def __init__(self, path: Path) -> None:
        self.path = path
        self.entries: dict[str, MemoryEntry] = {}
        if path.exists():
            raw = json.loads(path.read_text(encoding="utf-8"))
            for item in raw.get("entries", []):
                e = MemoryEntry(**item)
                self.entries[e.key] = e

    # ---------------------------------------------------------------- write
    def add(self, entry: MemoryEntry) -> None:
        self.entries[entry.key] = entry

    def save(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        payload = {"version": 1,
                   "entries": [asdict(e) for e in self.entries.values()]}
        self.path.write_text(json.dumps(payload, indent=2, ensure_ascii=False),
                             encoding="utf-8")

    # ---------------------------------------------------------------- read
    def search(self, query: str) -> list[MemoryEntry]:
        return [e for e in self.entries.values() if e.matches(query)]

    def rejections(self) -> list[MemoryEntry]:
        """Every idea that was measured and NOT shipped."""
        return [e for e in self.entries.values() if e.status == "rejected"]

    def by_tag(self, tag: str) -> list[MemoryEntry]:
        return [e for e in self.entries.values() if tag in e.tags]

    def recall(self, finding_title: str, limit: int = 3) -> list[MemoryEntry]:
        """Given a fresh finding, surface prior art.

        Scored on term overlap -- deliberately simple and explainable. The point
        is to surface 'you have seen this before', not to be a search engine.
        """
        terms = {t for t in finding_title.lower().split() if len(t) > 3}
        if not terms:
            return []
        scored: list[tuple[int, MemoryEntry]] = []
        for e in self.entries.values():
            hay = f"{e.title} {e.problem} {' '.join(e.tags)}".lower()
            hits = sum(1 for t in terms if t in hay)
            if hits:
                scored.append((hits, e))
        scored.sort(key=lambda x: -x[0])
        # Require a real overlap, not a single incidental word. Attaching weak
        # matches as "seen before" is worse than attaching nothing: it presents
        # an unrelated entry as prior art and invites the wrong fix.
        floor = max(2, len(terms) // 3)
        return [e for score, e in scored[:limit] if score >= floor]

    def why_not(self, topic: str) -> list[MemoryEntry]:
        """'Why wasn't X shipped?' -- rejections matching a topic."""
        return [e for e in self.rejections() if e.matches(topic)]

    # ---------------------------------------------------------------- graph
    def decision_graph(self) -> str:
        """Render the decision history as Mermaid.

        A decision graph beats a commit log because it records the branches NOT
        taken. `git log` shows what happened; this shows what was considered.
        """
        lines = ["graph LR"]
        for e in sorted(self.entries.values(), key=lambda x: x.key):
            node = e.key.replace("-", "_")
            label = e.title.replace('"', "'")[:60]
            lines.append(f'  {node}["{e.key}: {label}"]')
            for i, rej in enumerate(e.rejected):
                rn = f"{node}_r{i}"
                lines.append(f'  {rn}("{rej[:52]}"):::rejected')
                lines.append(f"  {node} -.rejected.-> {rn}")
            if e.chosen:
                cn = f"{node}_c"
                lines.append(f'  {cn}["{e.chosen[:52]}"]:::accepted')
                lines.append(f"  {node} ==chosen==> {cn}")
            if e.supersedes:
                lines.append(f"  {e.supersedes.replace('-', '_')} -.superseded by.-> {node}")
        lines += [
            "  classDef rejected fill:#3a1f1f,stroke:#a33,color:#eee;",
            "  classDef accepted fill:#1f3a24,stroke:#3a3,color:#eee;",
        ]
        return "\n".join(lines)
