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
    memory_hits: list[MemoryEntry] = field(default_factory=list)


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
    pool = [b for b in BLUEPRINTS if not stage or b.stage == stage] or BLUEPRINTS
    terms = _tokens(goal)

    def score(b: Blueprint) -> int:
        hay = _tokens(f"{b.label} {b.key} {b.stage} {' '.join(b.targets)}")
        return len(terms & hay)

    return max(pool, key=score) if terms else pool[0]


def compose(goal: str, values: dict[str, str] | None = None,
           stage: str = "", memory: EngineeringMemory | None = None,
           memory_limit: int = 3) -> ComposedPrompt:
    bp = select(goal, stage)
    text, unfilled = _fill(bp.template, values or {})
    hits = memory.search(goal, limit=memory_limit) if memory else []
    return ComposedPrompt(bp, text, unfilled, hits)


def render(cp: ComposedPrompt) -> str:
    out = [f"BLUEPRINT: {cp.blueprint.label}  ({cp.blueprint.stage})",
          f"targets: {', '.join(cp.blueprint.targets)}", "",
          "WHY THIS SCORES WELL", "  " + cp.blueprint.why_it_scores, "",
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
