"""Next-experiment recommendation, built on the "start simple" ladder.

The central optimization principle this file enforces: never recommend a
higher-complexity intervention (agentic changes, model swaps, fine-tuning)
before the cheaper rungs below it have been tried for the SAME weakness.
A rubric wanting "agent shape" is not license to jump straight to
"add another agent" -- if deterministic validation could plausibly fix
the observed weakness, that is the rung to try first.
"""

from __future__ import annotations

from dataclasses import dataclass

from ..score.scoreboard import counterfactual
from ..score.signals import ScoreCard
from .model import Status
from .store import ExperimentStore

LADDER = [
    (1, "prompt-wording", "Reword prompts/system messages for clarity."),
    (2, "prompt-structure", "Restructure prompt sections (roles, ordering, delimiters)."),
    (3, "constraints", "Add explicit constraints or refusal conditions."),
    (4, "examples", "Add few-shot examples."),
    (5, "output-schema", "Tighten the output schema / structured-output enforcement."),
    (6, "retrieval-configuration", "Tune retrieval parameters (top_k, thresholds)."),
    (7, "ranking-changes", "Change the ranking/scoring function."),
    (8, "deterministic-guardrails", "Add deterministic validation or a guardrail check."),
    (9, "workflow-changes", "Restructure the processing workflow/pipeline."),
    (10, "agentic-changes", "Introduce an agent loop or multi-step reasoning."),
    (11, "model-changes", "Swap the underlying model or provider."),
    (12, "fine-tuning", "Fine-tune a model -- most expensive, last resort."),
]

# Per-signal, which rungs are even plausible -- an Output CSV justification
# problem is not fixed by "swap the model" and a Code ZIP architecture
# question is not fixed by "add few-shot examples". Ladder order is
# preserved; this only restricts WHICH rungs apply to WHICH signal.
_APPLICABLE_RUNGS = {
    "output": [1, 2, 3, 4, 5, 8],
    "code": [3, 5, 8, 9, 10],
    "transcript": [1, 2, 3, 4],
    "interview": [1, 3, 4],
}


@dataclass
class Recommendation:
    target_signal: str
    target_dimension: str
    current_score: float | None
    observed_weakness: str
    suggested_change: str
    ladder_rung: int
    max_possible_impact: str
    why: str
    prior_experiments: list[str]
    success_condition: str
    failure_condition: str
    measurement: str


def _prior_targeting(store: ExperimentStore, signal: str) -> list:
    return [e for e in store.all() if e.target_signal == signal]


def recommend_next(card: ScoreCard, store: ExperimentStore) -> Recommendation:
    weakest = card.weakest_known_signal
    unknown = [s for s in card.signals if s.is_unknown]

    # An UNKNOWN signal at official weight >0 is often higher-leverage to
    # resolve than nudging an already-known weak one -- but resolving it
    # means supplying the missing artifact, not an "experiment" in the
    # code-change sense. Surface it plainly rather than silently ignoring it.
    if unknown and (weakest is None or
                    max(s.official_weight for s in unknown) > weakest.official_weight):
        u = max(unknown, key=lambda s: s.official_weight)
        return Recommendation(
            target_signal=u.name, target_dimension="",
            current_score=None,
            observed_weakness=f"{u.label} is UNKNOWN -- {u.official_weight*100:.0f}% "
                              "of the official score is not being measured at all",
            suggested_change=f"supply the missing artifact for {u.label} "
                             "(a transcript file, or a saved interview session)",
            ladder_rung=0,
            max_possible_impact="UNKNOWN -- not a code experiment, an artifact gap",
            why="an unmeasured signal cannot be improved by ANY code change "
               "until it is at least observable",
            prior_experiments=[], success_condition="signal becomes measurable",
            failure_condition="n/a", measurement="orchestrate score")

    if weakest is None:
        return Recommendation(
            target_signal="", target_dimension="", current_score=None,
            observed_weakness="no signal is currently measurable",
            suggested_change="supply at least one artifact (code, "
                             "dataset/output.csv, transcript, or a saved "
                             "interview session)",
            ladder_rung=0, max_possible_impact="UNKNOWN", why="",
            prior_experiments=[], success_condition="", failure_condition="",
            measurement="orchestrate score")

    prior = _prior_targeting(store, weakest.name)
    tried_rungs = {r for e in prior if (r := _rung_of(e.title)) is not None}
    rungs = [r for r in _APPLICABLE_RUNGS.get(weakest.name, [r for r, *_ in LADDER])]
    untried = [r for r in rungs if r not in tried_rungs] or rungs
    rung_num = min(untried)
    rung_name, rung_desc = next((n, d) for r, n, d in LADDER if r == rung_num)

    cf = counterfactual(card, weakest.name, 5.0)
    max_impact = (f"IF {weakest.label} improved by 5 points: "
                 f"+{cf['weighted_impact']:.2f} weighted (upper bound only, "
                 "not a prediction this rung achieves it)"
                 if "weighted_impact" in cf else "UNKNOWN")

    weakness = "; ".join(f.label for f in weakest.findings[:3]) or \
              f"{weakest.label} score is {weakest.estimated_score:.1f}/100 " \
              "with no specific finding named"

    return Recommendation(
        target_signal=weakest.name, target_dimension=rung_name,
        current_score=weakest.estimated_score,
        observed_weakness=weakness,
        suggested_change=f"[ladder rung {rung_num}: {rung_name}] {rung_desc}",
        ladder_rung=rung_num, max_possible_impact=max_impact,
        why=f"cheapest untried intervention for {weakest.label} -- "
           f"{len(prior)} prior experiment(s) already target this signal, "
           "so a higher rung is only offered if the simpler ones are "
           "exhausted or already rejected",
        prior_experiments=[f"{e.id} ({e.status}, delta={e.delta.get(weakest.name)})"
                          for e in prior],
        success_condition=f"{weakest.name} signal improves with no signal "
                          "regressing more than 2.0 points",
        failure_condition=f"{weakest.name} signal does not improve, or "
                          "another signal regresses materially",
        measurement="orchestrate experiment start/finish against this change")


def _rung_of(title: str) -> int | None:
    low = title.lower()
    for r, name, _ in LADDER:
        if name.replace("-", " ") in low or name in low:
            return r
    return None


def render_recommendation(rec: Recommendation) -> str:
    lines = ["NEXT EXPERIMENT", "=" * 34, "",
            f"Target:", f"  {rec.target_signal} / {rec.target_dimension}" if
            rec.target_dimension else f"  {rec.target_signal}", "",
            f"Current:",
            f"  {rec.current_score:.1f}/100" if rec.current_score is not None
            else "  UNKNOWN", "",
            "Observed weakness:", f"  {rec.observed_weakness}", "",
            "Suggested change:", f"  {rec.suggested_change}", "",
            "Expected impact:", f"  {rec.max_possible_impact}", "",
            "Why this experiment:", f"  {rec.why}", ""]
    if rec.prior_experiments:
        lines.append("Prior experiments targeting this signal:")
        for p in rec.prior_experiments:
            lines.append(f"  - {p}")
        lines.append("")
    lines.extend(["Success condition:", f"  {rec.success_condition}", "",
                 "Failure condition:", f"  {rec.failure_condition}", "",
                 "Measurement:", f"  {rec.measurement}"])
    return "\n".join(lines)
