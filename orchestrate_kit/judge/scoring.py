"""Answer analysis, cross-examination triggers, and scoring.

Deliberately deterministic and offline. No model call, no network, no API key.
Two reasons:

  1. A practice tool you cannot run on a plane is a practice tool you do not use.
  2. A rubric you can READ is a rubric you can argue with. If you disagree with
     a deduction here you can open the file and see exactly what fired.

What it measures is the SHAPE of an answer, not its truth. It cannot know
whether your F1 was really 0.512. It can know that you said a number, said
where it came from, and stated the size of the set -- and that those three
habits are what separate an answer that survives cross-examination from one
that does not.

Known limitation, stated rather than hidden: a fluent answer full of invented
numbers scores well here. This tool trains FORM. Truth is your job.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field

DIMENSIONS = ["specificity", "evidence", "boundaries", "alternatives", "honesty"]

# ---------------------------------------------------------------- signals
_NUMBER = re.compile(r"(?<![\w.])\d+(?:[./]\d+)?%?(?![\w])")
_RATIO = re.compile(r"\b\d+\s*(?:/|of|out of)\s*\d+\b", re.I)
_IDENT = re.compile(r"\b(?:[a-z_]+\.py|[a-z_]{3,}_[a-z_]{2,}|[A-Z]{2,}[A-Z_]*)\b")

_EVIDENCE = re.compile(
    r"\b(measur\w+|benchmark\w*|ablat\w+|counterfactual|diff(?:ed|ing)?|"
    r"profil\w+|sweep|experiment\w*|probe[ds]?|verified|reproduc\w+|"
    r"hash(?:ed)?|byte-?(?:identical|compared)|regression test|"
    r"i ran|i tested|i timed|i counted|i injected)\b", re.I)

_BOUNDARY = re.compile(
    r"\b(only|except|unless|offline|boundary|caveat|scoped? to|limited to|"
    r"cannot verify|can'?t verify|does ?n[o']?t (?:generali[sz]e|hold)|"
    r"on (?:the )?\d+ (?:labeled |labelled )?rows?|"
    r"that (?:said|is a)|with .* (?:enabled|disabled)|assum\w+)\b", re.I)

_ALTERNATIVE = re.compile(
    r"\b(instead of|rather than|chose it over|as opposed to|"
    r"reject\w*|considered|alternative|versus|\bvs\.?\b|compared (?:to|with)|"
    r"i tried|i benchmarked|the other option|would have)\b", re.I)

_HONESTY = re.compile(
    r"\b(i (?:don'?t|do not) (?:know|remember|recall)|unknown|unverified|"
    r"i'?m not sure|i cannot say|no basis|i was wrong|that was a mistake|"
    r"i got that wrong|i have not measured|untested)\b", re.I)

# `100%` cannot end with \b -- '%' is a non-word character, so a trailing \b
# requires a word char after it and the pattern silently never matches. That
# bug meant the single most common overclaim in an interview scored clean.
_OVERCLAIM = re.compile(
    r"\b(?:always|never fails?|perfectly|fully deterministic|guaranteed|"
    r"completely (?:safe|robust|correct)|handles everything|"
    r"every (?:case|scenario)|impossible to|bullet.?proof|"
    r"no (?:bugs|issues|problems))\b|\b100\s*%", re.I)

_HEDGE = re.compile(
    r"\b(basically|sort of|kind of|pretty much|i think|i guess|probably|"
    r"more or less|somewhat|maybe|i believe|should be|it just)\b", re.I)

_LIBRARY_NAME_ONLY = re.compile(
    r"\b(i use[d]? (?:sklearn|scikit|langchain|faiss|openai|transformers|"
    r"huggingface|pandas|numpy))\b", re.I)


@dataclass
class Analysis:
    scores: dict[str, float] = field(default_factory=dict)
    total: int = 0
    signals: dict[str, int] = field(default_factory=dict)
    triggers: list[str] = field(default_factory=list)   # follow-up question texts
    notes: list[str] = field(default_factory=list)
    missing_probes: list[str] = field(default_factory=list)
    words: int = 0


# ---------------------------------------------------------------- analysis
def analyse(answer: str, question, persona) -> Analysis:
    a = Analysis()
    text = (answer or "").strip()
    a.words = len(text.split())

    numbers = _NUMBER.findall(text)
    ratios = _RATIO.findall(text)
    idents = _IDENT.findall(text)
    ev = _EVIDENCE.findall(text)
    bd = _BOUNDARY.findall(text)
    alt = _ALTERNATIVE.findall(text)
    hon = _HONESTY.findall(text)
    over = _OVERCLAIM.findall(text)
    hedge = _HEDGE.findall(text)

    a.signals = {"numbers": len(numbers), "ratios": len(ratios),
                 "identifiers": len(idents), "evidence_verbs": len(ev),
                 "boundaries": len(bd), "alternatives": len(alt),
                 "admissions": len(hon), "overclaims": len(over),
                 "hedges": len(hedge)}

    if a.words < 12:
        a.notes.append("Answer is very short. In an interview this reads as "
                       "either mastery or absence, and the follow-up decides "
                       "which.")

    # ---- dimension scores, 0..100 --------------------------------------
    a.scores["specificity"] = _cap(
        18 * len(numbers) + 22 * len(ratios) + 14 * len(idents)
        - 8 * len(hedge))
    a.scores["evidence"] = _cap(30 * len(ev) + 10 * len(ratios))
    a.scores["boundaries"] = _cap(32 * len(bd) - 30 * len(over))
    a.scores["alternatives"] = _cap(34 * len(alt))
    a.scores["honesty"] = _cap(
        40 * len(hon) + 12 * len(bd) - 25 * len(over)
        + (25 if not over and not hedge and a.words >= 25 else 0))

    # An answer of pure length with no signal should not drift upward.
    if a.words > 90 and not (numbers or ev or alt):
        a.notes.append("Long answer, no numbers, no measurement verbs, no named "
                       "alternative. Length is not depth.")
        for d in DIMENSIONS:
            a.scores[d] = min(a.scores[d], 40)

    weights = persona.weights
    num = sum(a.scores[d] * weights.get(d, 1.0) for d in DIMENSIONS)
    den = sum(weights.get(d, 1.0) for d in DIMENSIONS)
    a.total = int(round(num / den)) if den else 0

    # ---- missing probes -------------------------------------------------
    low = text.lower()
    for probe in question.probes:
        head = probe.split()[0].lower().rstrip(",.")
        if head and head not in low and not _probe_satisfied(probe, a):
            a.missing_probes.append(probe)

    # ---- cross-examination triggers -------------------------------------
    a.triggers = _triggers(text, a, question)
    return a


def _probe_satisfied(probe: str, a: Analysis) -> bool:
    p = probe.lower()
    if "number" in p or "count" in p or "ceiling" in p:
        return a.signals["numbers"] > 0 or a.signals["ratios"] > 0
    if "alternative" in p or "rejected" in p:
        return a.signals["alternatives"] > 0
    if "boundary" in p or "honest" in p or "admission" in p:
        return a.signals["boundaries"] > 0 or a.signals["admissions"] > 0
    if "measur" in p or "benchmark" in p or "ablation" in p or "counterfactual" in p:
        return a.signals["evidence_verbs"] > 0
    return False


def _triggers(text: str, a: Analysis, question) -> list[str]:
    """Cross-examination. Each trigger is a follow-up a real interviewer asks
    for a specific, nameable reason -- not a random deepening."""
    t: list[str] = []
    low = text.lower()

    if a.signals["numbers"] and not a.signals["evidence_verbs"]:
        t.append("You gave me a number. Where did it come from -- did you "
                 "measure it, or is that a recollection?")

    if a.signals["overclaims"]:
        word = _OVERCLAIM.search(text).group(0)
        t.append(f"You said \"{word}\". Give me the boundary. Under what "
                 f"condition is that not true?")

    if re.search(r"\b100\s*%|\b(?:perfect|all (?:of )?(?:the )?rows|everything)\b",
                 low) and not _RATIO.search(text):
        t.append("On what set, and how big is it? A percentage without a "
                 "denominator is not a result.")

    if re.search(r"\bdeterministic\b", low) and not a.signals["boundaries"]:
        t.append("Deterministic under what conditions? Same process, or "
                 "separate processes with different hash seeds? What about "
                 "with the hosted provider enabled?")

    if a.signals["hedges"] >= 2 and a.signals["numbers"] == 0:
        t.append("That was hedged. Give me the concrete version: what "
                 "specifically happens, in your code, with real names.")

    if _LIBRARY_NAME_ONLY.search(text):
        t.append("You named a library. I asked about a mechanism. What does it "
                 "actually compute, and why is that the right computation here?")

    if a.words < 12:
        t.append("Expand that. Take the same claim and give me the evidence "
                 "and the boundary.")

    if a.signals["alternatives"] == 0 and question.topic in (
            "architecture", "retrieval", "determinism", "multimodal"):
        t.append("What did you choose that OVER? A design with no rejected "
                 "alternative was not designed.")

    if re.search(r"\b(better|improve[ds]?|helps?|works well)\b", low) \
            and not a.signals["numbers"]:
        t.append("Better by how much, measured how? 'It helps' is a hypothesis.")

    if re.search(r"\b(git|commit)", low) and re.search(r"increment", low):
        t.append("Have you read your own git log recently? How many commits, "
                 "actually?")

    return t


def _cap(v: float) -> float:
    return float(max(0, min(100, v)))
