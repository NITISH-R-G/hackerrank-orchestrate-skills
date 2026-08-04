"""Compose a prompt from a blueprint, filling in the caller's real context
and surfacing related Engineering Memory -- not an LLM call. This picks a
matching blueprint and fills placeholders deterministically, then queries
memory the same way `orchestrate mentor` already does, so a generated
prompt naturally references what this project (or the one you're
composing for) already measured and rejected.

Why not generate the prompt text with an LLM? Two reasons, both already
load-bearing elsewhere in this codebase: it would break the
zero-runtime-dependency core (DESIGN_INVARIANTS.md), and an LLM-authored
prompt-about-prompting would be exactly the kind of unverifiable claim
this project refuses to ship as if it were measured. A template with your
real inputs filled in is honest about being a template.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field

from ..memory.store import EngineeringMemory, MemoryEntry
from .blueprints import BLUEPRINTS, Blueprint


@dataclass
class ComposedPrompt:
    blueprint: Blueprint
    text: str
    unfilled: list[str]           # placeholders that had no value supplied
    match_score: int = 0          # shared tokens between the goal and the
                                   # chosen blueprint -- 0 means "nothing
                                   # matched, this is a fallback, not a fit"
    memory_hits: list[MemoryEntry] = field(default_factory=list)

    @property
    def low_confidence(self) -> bool:
        return self.match_score == 0


_PLACEHOLDER = re.compile(r"\{(\w+)\}")


def _fill(template: str, values: dict[str, str]) -> tuple[str, list[str]]:
    unfilled: list[str] = []

    def repl(m: re.Match) -> str:
        key = m.group(1)
        if key in values and values[key]:
            return values[key]
        unfilled.append(key)
        return f"<{key}>"

    return _PLACEHOLDER.sub(repl, template), unfilled


def _tokens(text: str) -> set[str]:
    return {t for t in re.findall(r"[a-z0-9]+", text.lower()) if len(t) > 2}


def select(goal: str, stage: str = "") -> Blueprint:
    """Pick the blueprint whose label/stage best matches a plain-English
    goal. Deliberately simple term overlap -- the same choice this
    project's own memory search already made and measured
    (D-dense-retrieval): a small, curated set of ~10 blueprints doesn't
    need embeddings to search.

    Tokenized on BOTH sides, not substring-in-haystack -- an earlier draft
    used `t in hay`, which made 'for' match inside 'before' (a literal
    substring) and pick the wrong blueprint. This project already found
    and fixed the identical bug once in memory/store.py's search()
    ('code' in 'cross-encoder'); it recurred here because the fix wasn't
    reused, only the lesson was remembered in prose. Caught by actually
    running a realistic query, not by review."""
    return select_scored(goal, stage)[0]


def select_scored(goal: str, stage: str = "") -> tuple[Blueprint, int]:
    """Same as `select`, but also returns the match score -- so a caller
    can tell a confident match from a fallback. `select()` alone silently
    returned the "best of a bad lot" with no signal that nothing actually
    matched, which is a real gap: a caller has no way to know whether
    "repo-audit" was chosen because it fit, or because it was simply
    first in a tie of zero-scoring blueprints. Found the same way the
    substring bug was -- by using the function for something real, not by
    inspection."""
    pool = [b for b in BLUEPRINTS if not stage or b.stage == stage] or BLUEPRINTS
    terms = _tokens(goal)
    if not terms:
        return pool[0], 0

    def score(b: Blueprint) -> int:
        hay = _tokens(f"{b.label} {b.key} {b.stage} {' '.join(b.targets)}")
        return len(terms & hay)

    best = max(pool, key=score)
    return best, score(best)


def compose(goal: str, values: dict[str, str] | None = None,
           stage: str = "", memory: EngineeringMemory | None = None,
           memory_limit: int = 3) -> ComposedPrompt:
    bp, match_score = select_scored(goal, stage)
    text, unfilled = _fill(bp.template, values or {})
    hits = memory.search(goal, limit=memory_limit) if memory else []
    return ComposedPrompt(bp, text, unfilled, match_score, hits)


def render(cp: ComposedPrompt) -> str:
    out = [f"BLUEPRINT: {cp.blueprint.label}  ({cp.blueprint.stage})",
          f"targets: {', '.join(cp.blueprint.targets)}"]
    if cp.low_confidence:
        out += ["", "LOW CONFIDENCE MATCH: nothing in your goal matched this "
               "blueprint's label, key, stage, or targets -- this is the "
               "least-bad option in the pool, not a real fit. Run "
               "`orchestrate transcript blueprints` and pick manually, or "
               "narrow the goal."]
    out += ["", "WHY THIS SCORES WELL", "  " + cp.blueprint.why_it_scores, "",
           "PROMPT", "  " + cp.text]
    if cp.unfilled:
        out += ["", "UNFILLED PLACEHOLDERS (fill these in before using it)",
               "  " + ", ".join(f"<{u}>" for u in cp.unfilled)]
    if cp.memory_hits:
        out += ["", "RELATED ENGINEERING MEMORY"]
        for e in cp.memory_hits:
            flag = "REJECTED" if e.status == "rejected" else "shipped"
            out.append(f"  [{flag}] {e.key}  {e.title}")
            if e.status == "rejected" and e.reconsider_if:
                out.append(f"      reconsider if: {e.reconsider_if}")
    return "\n".join(out)
