"""The interview simulator.

    $ orchestrate interview --persona skeptic --difficulty hard
    $ orchestrate interview --learn            # coaching after every answer
    $ orchestrate interview --panel            # all four judges, rotating

Four properties that make this a simulator rather than a question list:

  ADAPTIVE     the next question is chosen from your weakest dimension, and the
               level rises when you are doing well. Answer vaguely about
               retrieval and you get more retrieval, harder.

  CROSS-EXAM   follow-ups fire for a NAMED reason ("you gave me a number and no
               provenance"), not at random. Section-level scoring includes how
               you handled being pushed.

  MEMORY       the session remembers what you claimed. Say "fully
               deterministic" in question 2 and mention a hosted API in
               question 7, and the judge brings it back.

  WEAKNESS     the report names the habit, not just the score -- and quotes the
               answer that showed it.
"""

from __future__ import annotations

import random
import re
import textwrap
from pathlib import Path
from dataclasses import dataclass, field

from . import bank
from .personas import BY_KEY, LEVELS, PANEL, Difficulty, Persona
from .scoring import DIMENSIONS, Analysis, analyse

WIDTH = 84


@dataclass
class Turn:
    question: bank.Question
    persona: Persona
    answer: str
    analysis: Analysis
    follow_ups: list[tuple[str, str, Analysis]] = field(default_factory=list)

    @property
    def score(self) -> int:
        if not self.follow_ups:
            return self.analysis.total
        # Recovery under pressure counts. Weight the opener 60/40 against the
        # mean of the follow-ups: an interview is largely about what you say
        # after being challenged.
        fu = sum(a.total for _, _, a in self.follow_ups) / len(self.follow_ups)
        return int(round(0.6 * self.analysis.total + 0.4 * fu))


@dataclass
class Claim:
    text: str
    turn_index: int
    kind: str


class Interview:
    def __init__(self, persona: Persona, difficulty: Difficulty,
                 topics: list[str] | None = None, n: int = 8,
                 learn: bool = False, panel: bool = False,
                 seed: int | None = None) -> None:
        self.persona = persona
        self.difficulty = difficulty
        self.topics = topics
        self.n = n
        self.learn = learn
        self.panel = panel
        self.rng = random.Random(seed if seed is not None else 20260802)
        self.turns: list[Turn] = []
        self.asked: set[str] = set()
        self.claims: list[Claim] = []
        self.level = difficulty.min_level

    # ------------------------------------------------------- adaptivity
    def dimension_means(self) -> dict[str, float]:
        if not self.turns:
            return {d: 50.0 for d in DIMENSIONS}
        return {d: sum(t.analysis.scores.get(d, 0) for t in self.turns) / len(self.turns)
                for d in DIMENSIONS}

    def _weakest_topics(self) -> list[str]:
        """Map the weakest dimension onto the topics that exercise it."""
        means = self.dimension_means()
        weakest = min(means, key=means.get)
        return {
            "specificity": ["flow", "retrieval", "architecture"],
            "evidence": ["evaluation", "multimodal", "confidence"],
            "boundaries": ["determinism", "generalization", "security"],
            "alternatives": ["architecture", "retrieval", "arbitration"],
            "honesty": ["limitations", "generalization", "process"],
        }[weakest]

    def next_question(self) -> bank.Question | None:
        lo, hi = self.difficulty.min_level, min(self.level, self.difficulty.max_level)
        pool = [q for q in bank.select(self.topics, lo, hi) if q.key not in self.asked]
        if not pool:
            pool = [q for q in bank.select(self.topics, 1, self.difficulty.max_level)
                    if q.key not in self.asked]
        if not pool:
            return None

        want = set(self._weakest_topics()) if self.turns else set(self.persona.favours)
        preferred = [q for q in pool if q.topic in want]
        # Always leave a channel open to an unexplored topic, so the interview
        # cannot collapse into a single subject.
        seen_topics = {t.question.topic for t in self.turns}
        fresh = [q for q in pool if q.topic not in seen_topics]
        bucket = (preferred if preferred and self.rng.random() < 0.65
                  else fresh or pool)
        q = self.rng.choice(bucket)
        self.asked.add(q.key)
        return q

    def _adapt(self, turn: Turn) -> None:
        s = turn.score
        if s >= 75:
            self.level = min(self.difficulty.max_level, self.level + 1)
        elif s < 45:
            self.level = max(self.difficulty.min_level, self.level - 1)

    def _persona_for_turn(self) -> Persona:
        if not self.panel:
            return self.persona
        return PANEL[len(self.turns) % len(PANEL)]

    # ------------------------------------------------------- memory
    _CLAIM_PATTERNS = [
        (r"\b(?:fully |completely )?deterministic\b", "determinism"),
        (r"\b100%|\bperfect\b|\ball rows\b", "perfection"),
        (r"\b(?:never|always)\b", "absolute"),
        (r"\bno (?:bugs|issues|problems|regressions)\b", "absolute"),
        (r"\bi (?:wrote|built) (?:every|all)\b", "authorship"),
        (r"\bincremental(?:ly)? commit", "process"),
    ]
    _CONTRADICTIONS = {
        "determinism": (r"\b(hosted|api|remote|network|groq|openai|whisper|"
                        r"third.?party|cloud)\b",
                        "Earlier you said the system was deterministic. Now you "
                        "have described a hosted call in the path. Which is it, "
                        "and where exactly is the boundary?"),
        "perfection": (r"\b(miss(?:es|ed)?|wrong|fail(?:s|ed)?|regress|error)\b",
                       "A moment ago this was perfect. Now you are describing a "
                       "failure. Reconcile those for me."),
        "authorship": (r"\b(ai|assistant|copilot|claude|gpt|generated)\b",
                       "You told me you wrote every line. You have just "
                       "mentioned an assistant. I would rather hear the "
                       "accurate version."),
    }

    def _record_claims(self, text: str) -> None:
        for pattern, kind in self._CLAIM_PATTERNS:
            if re.search(pattern, text, re.I):
                self.claims.append(Claim(text[:160], len(self.turns), kind))

    def _callback(self, text: str) -> str | None:
        """A follow-up drawn from an EARLIER answer -- the thing a question list
        structurally cannot do."""
        for claim in self.claims:
            rule = self._CONTRADICTIONS.get(claim.kind)
            if not rule:
                continue
            pattern, prompt = rule
            if re.search(pattern, text, re.I):
                self.claims.remove(claim)
                return prompt
        return None

    # ------------------------------------------------------- driving
    def ask(self, question: bank.Question, persona: Persona,
            answer_fn) -> Turn:
        """answer_fn(prompt_text, kind) -> str. Injecting it keeps the engine
        testable and lets a different front end drive the same interview."""
        answer = answer_fn(question.text, "question")
        analysis = analyse(answer, question, persona)
        turn = Turn(question, persona, answer, analysis)

        budget = persona.pressure + self.difficulty.pressure_bonus
        pending = list(analysis.triggers)
        cb = self._callback(answer)
        if cb:
            pending.insert(0, cb)

        while pending and len(turn.follow_ups) < budget:
            probe = pending.pop(0)
            reply = answer_fn(probe, "follow-up")
            fa = analyse(reply, question, persona)
            turn.follow_ups.append((probe, reply, fa))
            self._record_claims(reply)
            for extra in fa.triggers:
                if extra not in pending and len(turn.follow_ups) < budget:
                    pending.append(extra)

        self._record_claims(answer)
        self.turns.append(turn)
        self._adapt(turn)
        return turn

    # ------------------------------------------------------- report
    def weaknesses(self) -> list[tuple[str, str, str]]:
        """(habit, why it costs you, the quoted answer that showed it)"""
        out: list[tuple[str, str, str]] = []
        if not self.turns:
            return out
        agg = {k: sum(t.analysis.signals.get(k, 0) for t in self.turns)
               for k in self.turns[0].analysis.signals}
        n = len(self.turns)

        def quote(pred) -> str:
            for t in self.turns:
                if pred(t):
                    return " ".join(t.answer.split())[:150]
            return ""

        if agg["numbers"] + agg["ratios"] < n:
            out.append((
                "Answers without numbers",
                "Fewer than one quantity per answer. Every claim you make "
                "invites 'how much?', and you are spending the follow-up budget "
                "answering it instead of advancing.",
                quote(lambda t: t.analysis.signals["numbers"] == 0)))
        if agg["evidence_verbs"] < n * 0.5:
            out.append((
                "Claims without provenance",
                "You rarely say HOW you know. 'I measured' / 'I diffed' / 'I "
                "injected' is the difference between a result and a belief.",
                quote(lambda t: t.analysis.signals["evidence_verbs"] == 0)))
        if agg["overclaims"]:
            out.append((
                f"Unbounded claims ({agg['overclaims']})",
                "Absolutes are the cheapest thing to disprove. One "
                "counterexample discredits everything else you said.",
                quote(lambda t: t.analysis.signals["overclaims"] > 0)))
        if agg["alternatives"] < n * 0.5:
            out.append((
                "No rejected alternatives",
                "You describe what you built, not what you chose it over. The "
                "rejection IS the engineering judgement.",
                quote(lambda t: t.analysis.signals["alternatives"] == 0)))
        if agg["boundaries"] < n * 0.5:
            out.append((
                "Guarantees with no boundary",
                "Every guarantee has a condition. Stating it unprompted reads "
                "as rigour; being forced to state it reads as being caught.",
                quote(lambda t: t.analysis.signals["boundaries"] == 0)))
        if agg["hedges"] > n * 1.5:
            out.append((
                f"Hedging ({agg['hedges']} instances)",
                "'Basically', 'sort of', 'I think' -- these signal uncertainty "
                "about things you actually know, which makes an interviewer "
                "discount the things you are right about.",
                quote(lambda t: t.analysis.signals["hedges"] >= 2)))
        if agg["admissions"] == 0 and n >= 5:
            out.append((
                "Never said 'I don't know'",
                "Across the whole interview you conceded nothing. That is not "
                "a strength: an interviewer who never hears an honest "
                "admission stops believing the confident answers.",
                ""))
        return out

    def strengths(self) -> list[str]:
        if not self.turns:
            return []
        agg = {k: sum(t.analysis.signals.get(k, 0) for t in self.turns)
               for k in self.turns[0].analysis.signals}
        n = len(self.turns)
        out = []
        if agg["ratios"] >= n * 0.5:
            out.append("You quote results as ratios with a denominator, which "
                       "pre-empts the 'on what set?' follow-up.")
        if agg["evidence_verbs"] >= n:
            out.append("You routinely say how you know something, not just "
                       "what you know.")
        if agg["alternatives"] >= n * 0.7:
            out.append("You consistently name what you chose against. That is "
                       "the single strongest interview habit.")
        if agg["admissions"] and not agg["overclaims"]:
            out.append("You concede uncertainty without over-conceding, and you "
                       "made no unbounded claims.")
        if agg["boundaries"] >= n:
            out.append("You attach boundaries to guarantees without being "
                       "pushed.")
        return out

    def report(self) -> str:
        out: list[str] = []
        w = out.append
        w("=" * WIDTH)
        w("INTERVIEW REPORT")
        w("=" * WIDTH)
        if not self.turns:
            w("No questions answered.")
            return "\n".join(out)

        total = int(round(sum(t.score for t in self.turns) / len(self.turns)))
        mark = self.difficulty.pass_mark
        verdict = ("STRONG" if total >= mark + 12 else
                   "PASS" if total >= mark else
                   "BORDERLINE" if total >= mark - 15 else "NOT READY")
        who = "Full panel" if self.panel else self.persona.name
        w("")
        w(f"  {verdict}    {total}/100    (pass mark {mark} at "
          f"{self.difficulty.label.lower()})")
        w(f"  interviewer: {who}   questions: {len(self.turns)}   "
          f"follow-ups: {sum(len(t.follow_ups) for t in self.turns)}")
        w("")

        w("DIMENSIONS")
        for d, v in sorted(self.dimension_means().items(), key=lambda kv: kv[1]):
            bar = "#" * int(v // 10) + "." * (10 - int(v // 10))
            w(f"  {d:<14} {bar} {int(v):>3}")
        w("")

        w("BY TOPIC")
        topics: dict[str, list[int]] = {}
        for t in self.turns:
            topics.setdefault(t.question.topic, []).append(t.score)
        for topic, scores in sorted(topics.items(),
                                    key=lambda kv: sum(kv[1]) / len(kv[1])):
            avg = int(round(sum(scores) / len(scores)))
            w(f"  {topic:<16} {avg:>3}   ({len(scores)} q)")
        w("")

        st = self.strengths()
        if st:
            w("WHAT IS WORKING")
            for s in st:
                _wrap(w, s, "  + ")
            w("")

        weak = self.weaknesses()
        w(f"WEAKNESSES ({len(weak)})")
        if not weak:
            w("  None detected by the habit rules. That is a statement about "
              "form, not about truth.")
        for habit, why, quoted in weak:
            w(f"  - {habit}")
            _wrap(w, why, "      ")
            if quoted:
                _wrap(w, f'you said: "{quoted}"', "      ")
            w("")

        worst = min(self.turns, key=lambda t: t.score)
        w("WEAKEST ANSWER")
        w(f"  Q ({worst.question.topic}, level {worst.question.level}, "
          f"scored {worst.score})")
        _wrap(w, worst.question.text, "    ")
        if worst.question.trap:
            _wrap(w, f"the trap here: {worst.question.trap}", "    ! ")
        if worst.question.strong:
            _wrap(w, f"shape of a strong answer: {worst.question.strong}",
                  "    > ")
        w("")

        unasked = [t for t in bank.TOPICS if t not in topics]
        if unasked:
            w("NOT COVERED THIS SESSION")
            _wrap(w, ", ".join(unasked), "  ")
            _wrap(w, "An unasked topic is not a passed topic. Re-run with "
                     "--topics to force coverage.", "  ")
            w("")

        w("=" * WIDTH)
        _wrap(w, f"{who}: {self.persona.closing_style}", "  ")
        _wrap(w, "This tool scores the SHAPE of your answers -- specificity, "
                 "provenance, boundaries, alternatives, honesty. It cannot "
                 "check whether your numbers are true. A fluent answer full of "
                 "invented figures scores well here and fails in the room.",
              "  ")
        w("=" * WIDTH)
        return "\n".join(out)


def _wrap(w, text: str, prefix: str = "  ") -> None:
    pad = " " * len(prefix)
    lines = textwrap.wrap(text, width=WIDTH - len(prefix)) or [""]
    for i, line in enumerate(lines):
        w((prefix if i == 0 else pad) + line)


# ----------------------------------------------------------------- driver
def run_terminal(persona_key: str = "skeptic", difficulty_key: str = "standard",
                 topics: list[str] | None = None, n: int = 8,
                 learn: bool = False, panel: bool = False,
                 seed: int | None = None, save_path: str | None = None) -> int:
    persona = BY_KEY.get(persona_key, BY_KEY["skeptic"])
    diff = LEVELS.get(difficulty_key, LEVELS["standard"])
    iv = Interview(persona, diff, topics, n, learn, panel, seed)

    print("=" * WIDTH)
    print(f"  {'PANEL INTERVIEW' if panel else persona.name.upper()}"
          f"   ·   {diff.label}   ·   {n} questions")
    print("=" * WIDTH)
    if not panel:
        _wrap(print, persona.stance, "  ")
        _wrap(print, f"looks for: {persona.tell}", "  ")
    _wrap(print, diff.note, "  ")
    print()
    print("  Type your answer and press Enter. Blank line = skip.")
    print("  Ctrl-C ends the interview and still prints the report.")
    print("=" * WIDTH)

    try:
        for i in range(n):
            q = iv.next_question()
            if q is None:
                break
            p = iv._persona_for_turn()

            def answer_fn(text: str, kind: str) -> str:
                tag = f"Q{i + 1}" if kind == "question" else "  ..."
                print()
                if kind == "question":
                    print(f"[{tag}] {p.name} · {q.topic} · level {q.level}")
                    _wrap(print, text, "  ")
                else:
                    print(f"[{tag}] {p.name} presses:")
                    _wrap(print, text, "      ")
                try:
                    return input("\n  > ").strip()
                except EOFError:
                    return ""

            turn = iv.ask(q, p, answer_fn)

            if learn:
                print()
                print("  " + "-" * (WIDTH - 4))
                _wrap(print, f"scored {turn.score}/100", "  [coach] ")
                if q.trap:
                    _wrap(print, f"the trap: {q.trap}", "  [coach] ")
                if q.strong:
                    _wrap(print, f"strong shape: {q.strong}", "  [coach] ")
                if turn.analysis.missing_probes:
                    _wrap(print, "did not address: "
                          + "; ".join(turn.analysis.missing_probes), "  [coach] ")
                print("  " + "-" * (WIDTH - 4))
    except KeyboardInterrupt:
        print("\n\n  (interview ended early)\n")

    print()
    print(iv.report())

    if save_path and iv.turns:
        import json
        from datetime import datetime, timezone

        total = int(round(sum(t.score for t in iv.turns) / len(iv.turns)))
        record = {
            "score": total,
            "persona": "panel" if panel else persona.key,
            "difficulty": diff.key,
            "questions_answered": len(iv.turns),
            "questions_requested": n,
            "saved_at": datetime.now(timezone.utc).isoformat(),
        }
        Path(save_path).write_text(json.dumps(record, indent=2), encoding="utf-8")
        print(f"\nsaved interview result -> {save_path}")

    return 0
