"""The Mentor.

    $ orchestrate mentor "I want to add OCR"

It answers eight questions, in this order, and refuses to answer any of them
with a number it did not measure:

    1. What kind of change is this?
    2. What has been tried before?          <- Engineering Memory
    3. Expected gain
    4. Risk register
    5. Blast radius (how to measure it)
    6. Evaluation plan
    7. Regression risk
    8. Release recommendation

**Design commitment.** A mentor that predicts your gain has no way to be right.
Where prior art exists, the mentor quotes the measured number and names the
entry. Where it does not, it prints `UNKNOWN` and hands you the experiment that
would resolve it. `UNKNOWN` is the honest output, not a failure of the tool.
"""

from __future__ import annotations

import re
import textwrap
from dataclasses import dataclass, field

from ..memory.store import EngineeringMemory, MemoryEntry
from .taxonomy import ProposalClass, Risk, classify

VERDICTS = {
    "BLOCKED-BY-PRIOR-ART": "This was measured and rejected. Do not re-propose "
                            "it without meeting the stated reconsideration "
                            "condition.",
    "MEASURE-FIRST": "Do not write the change yet. One cheap measurement "
                     "decides whether it is worth writing at all.",
    "PROCEED-WITH-MEASUREMENT": "Reasonable to build, provided the evidence "
                                "below is produced BEFORE it ships.",
    "PROCEED": "No prior art against it and no blocker-class risk. Standard "
               "evidence still applies.",
}


@dataclass
class Advice:
    proposal: str
    classes: list[ProposalClass]
    prior_art: list[MemoryEntry] = field(default_factory=list)
    blocking: list[MemoryEntry] = field(default_factory=list)
    risks: list[Risk] = field(default_factory=list)
    evidence_required: list[str] = field(default_factory=list)
    verdict: str = "PROCEED"
    adjacent: list[MemoryEntry] = field(default_factory=list)

    @property
    def gain_is_known(self) -> bool:
        return any(e.benchmarks for e in self.prior_art)


_SKIP = frozenset("the a an and or to of in on at by with from for i we want "
                  "would like use using add adding try trying should could my "
                  "our it its this that instead than".split())


def _terms(text: str) -> set[str]:
    # Two characters, not three: `k1`, `b`, `bm` and `k2` are exactly the
    # hyperparameter names people re-propose tuning.
    return {t for t in re.findall(r"[a-z0-9]+", text.lower())
            if len(t) >= 2 and t not in _SKIP}


class Mentor:
    def __init__(self, memory: EngineeringMemory) -> None:
        self.memory = memory

    # ------------------------------------------------------------------
    def advise(self, proposal: str) -> Advice:
        classes = classify(proposal)

        # Two searches, deliberately different.
        #
        # PRIOR ART is broad: the proposal plus the class tags, so "I want to
        # add OCR" also surfaces entries tagged multimodal that never say OCR.
        # Over-recall is cheap here -- an extra entry costs the reader a
        # paragraph.
        #
        # BLOCKING is narrow: the proposal ALONE, at a much higher floor. A
        # rejection that merely shares a topic must not veto a different idea.
        # "Add OCR" and "a visual model beyond OCR" are neighbours, not the
        # same proposal, and blocking the first on the second would make the
        # mentor an obstacle instead of an advisor.
        tags = " ".join(t for c in classes for t in c.tags)
        prior = self.memory.search(f"{proposal} {tags}", limit=6, floor=0.2)
        blocking = [e for e in self.memory.search(proposal, limit=4, floor=0.40)
                    if e.status == "rejected"]

        # An ACCEPTED entry can still contain a rejection: "chose BM25, rejected
        # tuning k1/b". Those alternatives are invisible to a status filter, and
        # they are exactly what someone re-proposes six months later. Match the
        # proposal against each rejected-alternative string directly.
        terms = {t for t in _terms(proposal)}
        for e in self.memory.entries.values():
            if e in blocking or not e.rejected:
                continue
            for alt in e.rejected:
                at = _terms(alt)
                if not at:
                    continue
                shared = terms & at
                # Two independent bars, both required. Coverage alone lets
                # "add OCR" match "hosted OCR" on the single word they share;
                # a raw count alone lets a long proposal match anything.
                if len(shared) >= 2 and len(shared) / len(at) >= 0.6:
                    blocking.append(e)
                    break

        adjacent = [e for e in prior
                    if e.status == "rejected" and e not in blocking]

        risks: list[Risk] = []
        seen: set[str] = set()
        for c in classes:
            for r in c.risks:
                if r.name not in seen:
                    seen.add(r.name)
                    risks.append(r)
        order = {"blocker": 0, "high": 1, "medium": 2, "low": 3}
        risks.sort(key=lambda r: order.get(r.severity, 9))

        evidence: list[str] = []
        for c in classes:
            for e in c.evidence_required:
                if e not in evidence:
                    evidence.append(e)

        if blocking:
            verdict = "BLOCKED-BY-PRIOR-ART"
        elif any(c.ceiling_question for c in classes) and not prior:
            verdict = "MEASURE-FIRST"
        elif any(r.severity == "blocker" for r in risks):
            verdict = "PROCEED-WITH-MEASUREMENT"
        else:
            verdict = "PROCEED"

        adv = Advice(proposal, classes, prior, blocking, risks, evidence, verdict)
        adv.adjacent = adjacent
        return adv

    # ------------------------------------------------------------------
    def render(self, advice: Advice, width: int = 84) -> str:
        a = advice
        out: list[str] = []
        w = out.append

        def rule(ch: str = "-") -> None:
            w(ch * width)

        def wrap(text: str, indent: str = "  ") -> None:
            for line in textwrap.wrap(text, width=width - len(indent)) or [""]:
                w(indent + line)

        rule("=")
        w(f"MENTOR  ::  {a.proposal}")
        rule("=")

        # ---- 1. classification ---------------------------------------
        w("")
        w("1. WHAT KIND OF CHANGE IS THIS")
        for c in a.classes:
            w(f"   [{c.key}] {c.label}")
        ceilings = [c.ceiling_question for c in a.classes if c.ceiling_question]
        if ceilings:
            w("")
            w("   The question to answer before writing any code:")
            wrap(ceilings[0], "     > ")

        # ---- 2. prior art --------------------------------------------
        w("")
        w("2. WHAT HAS BEEN TRIED BEFORE")
        if not a.prior_art:
            wrap("Nothing in memory matches. That is not the same as 'nobody "
                 "tried it' -- it means this repository has no record. Treat "
                 "the gain as UNKNOWN.")
        for e in a.prior_art:
            flag = "REJECTED" if e.status == "rejected" else "shipped "
            w(f"   [{flag}] {e.key}  {e.title}")
            if e.root_cause:
                wrap(f"why: {e.root_cause}", "        ")
            for b in e.benchmarks:
                w(f"        measured: {b.line()}")
            if e.blast_radius:
                wrap(f"blast radius: {e.blast_radius}", "        ")
            if e.status == "rejected" and e.reconsider_if:
                wrap(f"RECONSIDER IF: {e.reconsider_if}", "        ")
            w("")

        # ---- 3. expected gain ----------------------------------------
        w("3. EXPECTED GAIN")
        if a.gain_is_known:
            wrap("Measured previously in this repository:")
            for e in a.prior_art:
                for b in e.benchmarks:
                    w(f"     {b.line()}     [{e.key}]")
            wrap("Those numbers describe THAT dataset in THAT configuration. "
                 "They bound your expectation; they do not predict your result.")
        else:
            w("   UNKNOWN.")
            wrap("No measurement exists. This tool will not estimate one -- a "
                 "predicted gain with no experiment behind it is the exact "
                 "failure mode this whole framework exists to prevent. Run the "
                 "ceiling analysis in section 6 and the number becomes real.")

        # ---- 4. risks -------------------------------------------------
        w("")
        w(f"4. RISK REGISTER  ({len(a.risks)})")
        for r in a.risks:
            w(f"   ({r.severity.upper():<7}) {r.name}")
            wrap(r.why, "        ")
            wrap(f"detect: {r.detect}", "        ")
            w("")

        # ---- 5. blast radius ------------------------------------------
        w("5. BLAST RADIUS -- how to measure it, not what it is")
        wrap("Produce the full output artifact before and after, with every "
             "OTHER component in its SHIPPED state. Count changed rows. For "
             "each one, state why the new value is correct.")
        wrap("A blast radius measured with a neighbouring component disabled "
             "is not a blast radius. That mistake shipped a regression in the "
             "reference build (F-16-distress-lexicon).")

        # ---- 6. evaluation plan ---------------------------------------
        w("")
        w("6. EVALUATION PLAN -- run these, in this order")
        w("   0. Pin the current output hash, if it is not already pinned.")
        for i, e in enumerate(a.evidence_required, start=1):
            wrap(f"{i}. {e}", "   ")
        n = len(a.evidence_required)
        wrap(f"{n + 1}. Negative control: break the new component on purpose "
             "and confirm your harness NOTICES. A harness that has never "
             "failed has never been tested.", "   ")

        # ---- 7. regression risk ---------------------------------------
        w("")
        w("7. REGRESSION RISK")
        blockers = [r for r in a.risks if r.severity == "blocker"]
        if blockers:
            wrap(f"{len(blockers)} blocker-class risk(s) present: "
                 f"{', '.join(r.name for r in blockers)}. Any one of these can "
                 "regress rows without failing a single existing test.")
        else:
            wrap("No blocker-class risk for this change class. The ordinary "
                 "risk remains: a change that improves the aggregate while "
                 "breaking the specific row that matters. Probe entities, not "
                 "averages (D-local-asr).")

        # ---- 8. recommendation ----------------------------------------
        w("")
        rule("=")
        w(f"8. RELEASE RECOMMENDATION:  {a.verdict}")
        wrap(VERDICTS[a.verdict])
        if a.blocking:
            w("")
            wrap("Blocked by:")
            for e in a.blocking:
                w(f"     {e.key}  {e.title}")
                if e.reconsider_if:
                    wrap(f"unblock by demonstrating: {e.reconsider_if}", "       ")
        if a.adjacent:
            w("")
            wrap("Adjacent rejections -- related topic, NOT the same proposal. "
                 "They do not block you; read them so you do not walk into the "
                 "same wall from a different direction:")
            for e in a.adjacent:
                w(f"     {e.key}  {e.title}")
        rule("=")
        return "\n".join(out)
