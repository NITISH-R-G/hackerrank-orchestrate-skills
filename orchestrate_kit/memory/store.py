"""Engineering Memory — searchable institutional knowledge.

CI logs tell you a check failed. Engineering Memory tells you:

    "You tried this before. Here is the benchmark, the blast radius, the
     alternatives that were rejected, and the condition under which it would be
     worth reconsidering."

Two record kinds, deliberately symmetric:

  finding   a defect that was found and fixed
  decision  a choice that was made -- INCLUDING a choice to reject something

Most repositories preserve only successes. Rejections are first-class here,
because "we measured embeddings at F1 0.479 against 0.512 and did not ship them"
is the least-fakeable statement an engineer can make.

Storage is JSON. No database, no service. Commit it, diff it, review it.
"""

from __future__ import annotations

import json
import re
from dataclasses import asdict, dataclass, field
from pathlib import Path

_STOP = frozenset("""the a an and or but for to of in on at by with from is are was
were be been being this that these those it its as if then than so not no do does
did can could should would will shall may might must have has had i we you they""".split())

_WORD = re.compile(r"[a-z0-9]+")
_NONWORD = re.compile(r"\W")


def _stem(word: str) -> str:
    """Four suffixes, no library. Enough to make `embedding`/`embeddings` and
    `reject`/`rejected`/`rejection` collide, which is all that is needed."""
    for suffix in ("ations", "ation", "ings", "ing", "ions", "ion", "ers",
                   "es", "ed", "s"):
        if len(word) > len(suffix) + 2 and word.endswith(suffix):
            return word[: -len(suffix)]
    return word


def _stems(text: str) -> set[str]:
    return {_stem(t) for t in _WORD.findall(text.lower())
            if len(t) > 2 and t not in _STOP}


@dataclass
class Benchmark:
    """A measurement that decided something."""

    metric: str
    before: str = ""
    after: str = ""
    baseline: str = ""
    sample_size: str = ""
    note: str = ""

    def line(self) -> str:
        if self.before and self.after:
            core = f"{self.metric}: {self.before} -> {self.after}"
        elif self.baseline:
            core = f"{self.metric}: {self.after or '?'} vs {self.baseline} (baseline)"
        else:
            core = f"{self.metric}: {self.after or self.before}"
        if self.sample_size:
            core += f"  [n={self.sample_size}]"
        return core + (f"  -- {self.note}" if self.note else "")


@dataclass
class MemoryEntry:
    key: str
    kind: str = "finding"                       # finding | decision
    title: str = ""
    problem: str = ""
    root_cause: str = ""
    chosen: str = ""
    rejected: list[str] = field(default_factory=list)
    evidence: str = ""
    benchmarks: list[Benchmark] = field(default_factory=list)
    blast_radius: str = ""
    impact: str = ""
    reconsider_if: str = ""                     # what would justify revisiting this
    commit: str = ""
    files: list[str] = field(default_factory=list)
    tags: list[str] = field(default_factory=list)
    status: str = "accepted"                    # accepted | rejected | superseded
    supersedes: str = ""
    depends_on: list[str] = field(default_factory=list)
    phase: str = ""
    lesson: str = ""

    def haystack(self) -> str:
        return " ".join([
            self.key, self.title, self.problem, self.root_cause, self.chosen,
            " ".join(self.rejected), self.evidence, self.impact,
            self.reconsider_if, " ".join(self.tags), self.lesson,
            " ".join(b.line() for b in self.benchmarks),
        ]).lower()

    def score(self, query: str) -> float:
        """Term-overlap relevance, deliberately simple and explainable.

        Title and tag hits weigh 3x body hits: an entry whose TITLE is about
        embeddings is more relevant than one mentioning it once in a footnote.

        Matching is on TOKENS, not substrings. Substring matching looks
        harmless and is not: `"code" in "cross-encoder"` is true, which quietly
        attached a retrieval decision to a source-code question. Same class of
        bug as the one this repository already recorded in
        F-leakage-false-blocker -- a plausible match that nobody checks.
        """
        terms = _stems(query)
        if not terms:
            return 0.0
        title = _stems(f"{self.title} {' '.join(self.tags)}")
        body = _stems(self.haystack())
        hits = 3.0 * len(terms & title)
        hits += 1.0 * len(((terms & body) - title))
        return hits / (len(terms) * 3.0)


class EngineeringMemory:
    def __init__(self, path: Path) -> None:
        self.path = Path(path)
        self.entries: dict[str, MemoryEntry] = {}
        if self.path.exists():
            raw = json.loads(self.path.read_text(encoding="utf-8"))
            for item in raw.get("entries", []):
                bm = [Benchmark(**b) for b in item.pop("benchmarks", [])]
                item.pop("memory_key", None)
                self.entries[item["key"]] = MemoryEntry(benchmarks=bm, **item)

    # ---------------------------------------------------------------- write
    def add(self, entry: MemoryEntry) -> None:
        self.entries[entry.key] = entry

    def save(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        out = []
        for e in self.entries.values():
            d = asdict(e)
            d["benchmarks"] = [asdict(b) for b in e.benchmarks]
            out.append(d)
        self.path.write_text(
            json.dumps({"version": 2, "entries": out}, indent=2, ensure_ascii=False),
            encoding="utf-8")

    # ---------------------------------------------------------------- read
    def search(self, query: str, limit: int = 5, floor: float = 0.25) -> list[MemoryEntry]:
        """Ranked search. `floor` stops a single incidental word from surfacing
        an unrelated entry as if it were prior art."""
        scored = [(e.score(query), e) for e in self.entries.values()]
        scored = [(s, e) for s, e in scored if s >= floor]
        scored.sort(key=lambda x: (-x[0], x[1].key))
        return [e for _, e in scored[:limit]]

    def rejections(self) -> list[MemoryEntry]:
        return sorted((e for e in self.entries.values() if e.status == "rejected"),
                      key=lambda e: e.key)

    def by_tag(self, tag: str) -> list[MemoryEntry]:
        return sorted((e for e in self.entries.values() if tag in e.tags),
                      key=lambda e: e.key)

    def tags(self) -> dict[str, int]:
        counts: dict[str, int] = {}
        for e in self.entries.values():
            for t in e.tags:
                counts[t] = counts.get(t, 0) + 1
        return dict(sorted(counts.items(), key=lambda kv: (-kv[1], kv[0])))

    def why_not(self, topic: str) -> list[MemoryEntry]:
        scored = [(e.score(topic), e) for e in self.rejections()]
        return [e for s, e in sorted(scored, key=lambda x: -x[0]) if s >= 0.25]

    # ------------------------------------------------------------- centrality
    def referenced_by(self, key: str) -> list[str]:
        """Which other entries name this one via depends_on or supersedes.

        Not a ranking signal folded into search() -- deliberately kept
        separate and explicit. An entry many others build on is worth
        knowing about, but "cited often" and "relevant to THIS query" are
        different questions; conflating them would make search results
        harder to reason about, not easier."""
        return sorted(e.key for e in self.entries.values()
                      if key in e.depends_on or e.supersedes == key)

    def centrality(self) -> dict[str, int]:
        """How many other entries reference each entry. A cheap, honest
        substitute for "importance": load-bearing entries -- the ones a
        reversal would ripple through -- surface without guessing at a
        weighting scheme this corpus is too small to tune meaningfully."""
        counts = {k: 0 for k in self.entries}
        for e in self.entries.values():
            for dep in e.depends_on:
                if dep in counts:
                    counts[dep] += 1
            if e.supersedes in counts:
                counts[e.supersedes] += 1
        return counts

    # ------------------------------------------------------------- freshness
    def verify_files(self, repo_root: Path) -> dict:
        """Do the files an entry cites still exist?

        Deliberately scoped to existence, not staleness-by-content: an entry
        has no timestamp to compare a file's mtime against, so claiming to
        detect "this decision may now be out of date" would be a guess
        dressed up as a check. Existence is the honest, buildable subset of
        that idea -- inspired by the general principle that a memory system
        should relate its records to the code they describe, not just store
        prose, without claiming the deeper impact-analysis this repo cannot
        actually perform on a flat JSON store.

        Returns a report, not a pass/fail -- most entries legitimately have
        no `files`, because they describe decisions in a DIFFERENT codebase
        (the historical Orchestrate submission this repo's memory corpus was
        seeded from). Silently treating "no files" as "verified" would be
        exactly the kind of false-coverage this project's audits exist to
        catch elsewhere.
        """
        with_files = [e for e in self.entries.values() if e.files]
        missing: list[tuple[str, str]] = []
        for e in with_files:
            for f in e.files:
                if not (repo_root / f).exists():
                    missing.append((e.key, f))
        return {
            "total_entries": len(self.entries),
            "with_files": len(with_files),
            "without_files": len(self.entries) - len(with_files),
            "missing": missing,
        }

    def verify_commits(self, repo_root: Path) -> dict:
        """Do the commits an entry cites (provenance) actually exist in this
        repository's history?

        Same honesty rule as verify_files: most entries have no `commit`
        because they describe a different codebase, and that is correctly
        NOT a failure -- only a cited commit that turns out not to exist is.

        A shallow clone (`git clone --depth N`, or GitHub Actions'
        `actions/checkout` default) genuinely does not contain older commits
        -- `git cat-file -e` correctly reports them missing, but "missing"
        there means "not fetched," not "never existed." This shipped once
        without the distinction: the first real CI run for this method
        reported 5 valid commits as missing, because the checkout step
        hadn't been given `fetch-depth: 0`. `is_shallow` makes that failure
        mode self-diagnosing instead of looking like corrupted provenance.
        """
        import subprocess

        is_shallow = (repo_root / ".git" / "shallow").exists()
        with_commit = [e for e in self.entries.values() if e.commit]
        missing: list[tuple[str, str]] = []
        for e in with_commit:
            result = subprocess.run(
                ["git", "cat-file", "-e", f"{e.commit}^{{commit}}"],
                cwd=repo_root, capture_output=True, timeout=10)
            if result.returncode != 0:
                missing.append((e.key, e.commit))
        return {
            "shallow_clone": is_shallow,
            "total_entries": len(self.entries),
            "with_commit": len(with_commit),
            "without_commit": len(self.entries) - len(with_commit),
            "missing": missing,
        }

    # ---------------------------------------------------------------- graph
    def mermaid(self, focus: str = "") -> str:
        """Decision graph: records the branches NOT taken, which is precisely
        what a commit log cannot show."""
        entries = (self.search(focus, limit=12, floor=0.2) if focus
                   else sorted(self.entries.values(), key=lambda e: e.key))
        lines = ["graph LR"]
        for e in entries:
            n = _NONWORD.sub("_", e.key)
            lines.append(f'  {n}["{_esc(e.key)}<br/>{_esc(e.title)[:52]}"]')
            lines.append(f"  class {n} {'rej' if e.status == 'rejected' else 'acc'};")
            for i, r in enumerate(e.rejected):
                rn = f"{n}_r{i}"
                lines.append(f'  {rn}("{_esc(r)[:44]}")')
                lines.append(f"  class {rn} rej;")
                lines.append(f"  {n} -. rejected .-> {rn}")
            if e.chosen:
                cn = f"{n}_c"
                lines.append(f'  {cn}["{_esc(e.chosen)[:44]}"]')
                lines.append(f"  class {cn} acc;")
                lines.append(f"  {n} ==> {cn}")
            for dep in e.depends_on:
                lines.append(f"  {_NONWORD.sub('_', dep)} --> {n}")
            if e.supersedes:
                lines.append(f"  {_NONWORD.sub('_', e.supersedes)} -. superseded .-> {n}")
        lines += [
            "  classDef rej fill:#3b1d1d,stroke:#b04141,color:#f2e6e6;",
            "  classDef acc fill:#17331f,stroke:#3f8f52,color:#e6f2e9;",
        ]
        return "\n".join(lines)

    def timeline(self) -> str:
        """Engineering history grouped by phase -- not by commit."""
        phases: dict[str, list[MemoryEntry]] = {}
        for e in sorted(self.entries.values(), key=lambda x: x.key):
            phases.setdefault(e.phase or "unphased", []).append(e)
        out = ["timeline", "  title Engineering history"]
        for phase in sorted(phases):
            out.append(f"  section {phase}")
            for e in phases[phase]:
                mark = "REJECTED " if e.status == "rejected" else ""
                # `:` is the event separator in a Mermaid timeline; a colon in
                # a title would silently split the row.
                title = _esc(e.title)[:58].replace(":", " -")
                out.append(f"    {e.key} : {mark}{title}")
        return "\n".join(out)


def _esc(s: str) -> str:
    return s.replace('"', "'").replace("\n", " ")


def default_path(repo: Path | None = None) -> Path:
    """Memory lives WITH the code under audit. Memory in the tool is a cache;
    memory beside the code is institutional knowledge.

    The bundled seed corpus resolves to `orchestrate_kit/data/memory.json` --
    INSIDE the package, not the repo root. A path reaching outside the package
    (`parents[2]`, `../data`) only "works" for an editable install run from a
    git checkout; it silently breaks for a real `pip install` from a wheel,
    where the package is copied into `site-packages` with nothing beside it.
    That failure mode is invisible in local testing and only shows up for the
    first real PyPI user -- exactly the kind of measured-in-the-wrong-
    -configuration mistake this project's own Engineering Memory warns about
    (see F-16-distress-lexicon)."""
    if repo and (Path(repo) / ".orchestrate" / "memory.json").exists():
        return Path(repo) / ".orchestrate" / "memory.json"
    return Path(__file__).resolve().parents[1] / "data" / "memory.json"
