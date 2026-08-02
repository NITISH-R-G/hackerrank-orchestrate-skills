"""Judge personas.

Four interviewers who disagree with each other about what matters. That
disagreement is the point: an answer tuned to please the Architect is often
exactly the answer the Skeptic tears apart.

A persona changes three things:

  weights        what the score is actually measuring
  pressure       how many follow-ups a weak answer draws
  openers        the shape of the first question on any topic

None of them changes the FACTS. A persona is a lens, not a different reality.
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class Persona:
    key: str
    name: str
    stance: str
    weights: dict[str, float]
    pressure: int                      # max follow-ups per question
    favours: list[str] = field(default_factory=list)   # topic keys
    opener: str = ""
    tell: str = ""                     # what a good answer looks like to them
    closing_style: str = ""


ARCHITECT = Persona(
    "architect", "The Architect",
    "Wants to know whether you chose the design or inherited it.",
    {"specificity": 1.0, "evidence": 1.0, "boundaries": 0.8,
     "alternatives": 1.6, "honesty": 0.8},
    pressure=2,
    favours=["architecture", "arbitration", "flow", "determinism"],
    opener="Walk me through the shape of the system, and tell me what you "
           "chose it OVER.",
    tell="Names the alternative that lost, and why it lost. A design with no "
         "rejected alternative was not designed.",
    closing_style="Assesses whether you own the architecture or are describing "
                  "a diagram of it.")

SKEPTIC = Persona(
    "skeptic", "The Skeptic",
    "Assumes every number you state is unverified until you say where it "
    "came from.",
    {"specificity": 1.4, "evidence": 1.8, "boundaries": 1.2,
     "alternatives": 0.7, "honesty": 1.0},
    pressure=3,
    favours=["retrieval", "confidence", "evaluation", "generalization"],
    opener="Give me a number from your system, and then tell me how you know "
           "it is true.",
    tell="Distinguishes measured from inferred without being asked. Says "
         "'I don't remember the value, but here is how it was chosen.'",
    closing_style="Assesses whether your confidence is calibrated to your "
                  "evidence.")

SECURITY = Persona(
    "security", "The Security Reviewer",
    "Treats every input as hostile and every component as a surface.",
    {"specificity": 1.0, "evidence": 1.2, "boundaries": 1.8,
     "alternatives": 0.9, "honesty": 1.2},
    pressure=3,
    favours=["security", "multimodal", "determinism", "arbitration"],
    opener="Where does untrusted text reach something that makes a decision?",
    tell="States a trust boundary explicitly, and names what is on each side.",
    closing_style="Assesses whether you thought about the adversary or only "
                  "about the average case.")

PRACTITIONER = Persona(
    "practitioner", "The Practitioner",
    "Has shipped things. Cares about cost, failure modes and what you would "
    "do at 3am.",
    {"specificity": 1.2, "evidence": 1.0, "boundaries": 1.2,
     "alternatives": 1.0, "honesty": 1.4},
    pressure=2,
    favours=["evaluation", "process", "limitations", "multimodal"],
    opener="What breaks first when this meets data you have not seen?",
    tell="Volunteers a limitation before being asked, and states its cost.",
    closing_style="Assesses whether you would be safe to hand a production "
                  "system to.")

PANEL = [ARCHITECT, SKEPTIC, SECURITY, PRACTITIONER]
BY_KEY = {p.key: p for p in PANEL}


# ----------------------------------------------------------------------
@dataclass
class Difficulty:
    key: str
    label: str
    min_level: int          # question difficulty floor
    max_level: int
    pressure_bonus: int     # extra follow-ups on top of persona pressure
    pass_mark: int
    note: str


LEVELS = {
    "warmup": Difficulty("warmup", "Warm-up", 1, 2, 0, 55,
                         "Core topics, minimal cross-examination. Use this to "
                         "find out what you can say fluently."),
    "standard": Difficulty("standard", "Standard", 1, 3, 1, 65,
                           "What a real interview feels like. Follow-ups on "
                           "anything vague."),
    "hard": Difficulty("hard", "Hard", 2, 4, 2, 72,
                       "Every unqualified claim is challenged. Assumes you have "
                       "already done a warm-up pass."),
    "adversarial": Difficulty("adversarial", "Adversarial", 3, 5, 3, 78,
                              "The interviewer is trying to find the thing you "
                              "do not know. Expect to be caught. That is the "
                              "product."),
}
