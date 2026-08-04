"""The AI Chat Transcript rubric, as HackerRank publishes it for Orchestrate.

Source: HackerRank's own "Behind the Scenes of HackerRank Orchestrate"
writeup (hackerrank.com blog, June 2026). Facts transcribed here --
dimension names and weights -- are public and factual; every description
below is written in this project's own words, not the article's, the same
way `RESEARCH.md` treats every other HackerRank source: paraphrased and
cited, never reproduced.

The article states plainly that the transcript is scored on how the HUMAN
directed the coding agent, not on what the agent produced. That's the
premise this whole module exists to serve: a transcript full of good code
with no visible direction still scores low on this axis.

HackerRank's own published finding, already quoted elsewhere in this
project's skills (`orchestrate-ai-collaboration-transcript`): interview
turn-count had a weak NEGATIVE correlation with the interview score, while
answer depth and specificity correlated strongly (r=0.615 words, r=0.583
specificity). The transcript rubric rewards the same property the
interview rubric does -- depth and ownership, not volume -- which is why
this module's pattern library targets specificity and ownership language,
not turn count.
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class Behavior:
    name: str
    observable_as: str      # what this looks like in real transcript text
    example_shape: str      # the SHAPE of a strong instance, not a script
    anti_pattern: str        # the low-signal version of the same topic


@dataclass
class Dimension:
    key: str
    label: str
    weight: float            # published weight, 0-1
    summary: str
    behaviors: list[Behavior] = field(default_factory=list)


DIMENSIONS: list[Dimension] = [
    Dimension(
        "direction", "Direction & architecture ownership", 0.35,
        "Whether the human leads the build -- naming the architecture, "
        "making the tradeoff calls, and pushing back on the agent's "
        "suggestions rather than accepting the first thing it proposes.",
        [
            Behavior(
                "names the alternative rejected",
                "a sentence stating what was chosen INSTEAD of, and why",
                "'X because Y measured better than Z' -- alternative named, "
                "reason given",
                "accepting a design with no comparison ever stated"),
            Behavior(
                "overrides or redirects the agent",
                "an instruction that changes or rejects what the agent just "
                "proposed",
                "'don't do X, do Y instead, because...' -- a real redirect, "
                "with a reason",
                "purely accepting every suggestion in sequence"),
            Behavior(
                "states ownership of the decision",
                "first-person framing of a design choice",
                "'I chose...' / 'we decided...' / 'I rejected...'",
                "third-person narration of the tool's actions: 'it created "
                "the pipeline', 'the agent decided'"),
        ]),
    Dimension(
        "specificity", "Technical specificity & constraint", 0.25,
        "Whether instructions name real things -- models, libraries, file "
        "paths, schemas, thresholds, output formats -- instead of staying "
        "at the level of a feature request.",
        [
            Behavior(
                "names concrete technical entities",
                "a real model name, library, file path, schema, or numeric "
                "threshold in an instruction",
                "a specific model/library/path/number appears in context "
                "that constrains the agent's choice",
                "'make it better' / 'add error handling' with nothing "
                "naming HOW"),
            Behavior(
                "sets an explicit constraint",
                "a stated boundary the agent must respect",
                "'must run with zero network calls' / 'keep it under N "
                "lines' / 'output must validate against this schema'",
                "no constraint stated anywhere in the instruction"),
        ]),
    Dimension(
        "iteration", "Iteration & verification", 0.25,
        "Whether the human actually tested output, inspected failures, and "
        "directed a fix based on what broke -- a real debugging loop, not "
        "a single build-and-submit pass.",
        [
            Behavior(
                "reports a real measurement or test result",
                "a number, a test result, or an inspected output, not a "
                "vague 'it works'",
                "'ran it on the sample set, 3 of 29 rows wrong' -- a real "
                "measurement, stated",
                "no evidence any output was ever inspected"),
            Behavior(
                "reverts or changes course based on evidence",
                "a stated regression followed by a reversal or fix",
                "'that regressed row 14, reverted, tried X instead'",
                "every change kept regardless of whether it helped"),
        ]),
    Dimension(
        "safety", "Safety, edge case & quality awareness", 0.15,
        "Whether adversarial input, ambiguous cases, and escalation logic "
        "were considered as a deliberate part of the design, not an "
        "afterthought.",
        [
            Behavior(
                "names a specific adversarial or edge case",
                "a concrete attack or ambiguous-input scenario, not the "
                "word 'safety' alone",
                "'prompt injection in a ticket body should not change the "
                "escalation decision' -- a named mechanism",
                "'we made sure it's safe' with no scenario named"),
            Behavior(
                "states a mechanism, not a goal",
                "HOW a risk is mitigated, not just that it should be",
                "'the deterministic gate runs before the model, so it "
                "can't downgrade a flagged case' -- named mechanism",
                "'high-risk tickets should be escalated' -- states the "
                "goal, not the mechanism"),
        ]),
]

TOTAL_WEIGHT = sum(d.weight for d in DIMENSIONS)
assert abs(TOTAL_WEIGHT - 1.0) < 1e-9, "published weights must sum to 1.0"

BY_KEY = {d.key: d for d in DIMENSIONS}
