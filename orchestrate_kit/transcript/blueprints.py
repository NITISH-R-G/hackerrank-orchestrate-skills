"""Prompt blueprints -- structured patterns for directing a coding agent
through a specific engineering task, each one built to demonstrate the
transcript rubric's actual dimensions rather than just get work done.

Scoped to 9 task types, not the full 25+ a general engineering-prompting
system could eventually cover. Each blueprint here is checked against a
real test asserting its own prompt template actually contains the
ownership/specificity/verification/safety language it claims to teach --
a blueprint that doesn't practice what it prescribes would be exactly the
kind of unverified claim this project refuses elsewhere. Growing this
library is additive and cheap once the pattern is right; padding it to a
round number before verifying the pattern works would not be.
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class Blueprint:
    key: str
    label: str
    stage: str
    targets: list[str]              # rubric dimension keys this demonstrates
    why_it_scores: str
    template: str                   # {placeholders} filled by the composer
    demonstrates: dict[str, str] = field(default_factory=dict)


BLUEPRINTS: list[Blueprint] = [
    Blueprint(
        "repo-audit", "Repository audit before changing anything",
        "understanding",
        ["direction", "specificity"],
        "Naming what you found before proposing a change is the "
        "ownership signal a rubric can actually see -- 'I looked and "
        "found X' beats 'let's add Y'.",
        "Read {target_paths} and report: existing patterns for "
        "{concern}, the specific files that would be touched by "
        "{proposed_change}, and any existing test covering this area. "
        "Do not propose a change yet -- report findings only.",
        {"direction": "requires the agent to report before acting, which "
                      "forces YOUR next message to be the decision",
         "specificity": "{target_paths} and {concern} force real paths and "
                        "a real question, not a vague ask"}),

    Blueprint(
        "architecture-tradeoff", "Architecture / design tradeoff",
        "design",
        ["direction", "specificity"],
        "The rubric's top-weighted dimension (35%) rewards naming what "
        "you rejected and why -- this blueprint makes that the literal "
        "output format.",
        "Propose {n_alternatives} approaches to {problem}, each with: "
        "what it costs, what it gains, and which existing code it "
        "touches. I will choose one and state why the others lose.",
        {"direction": "the human's next message is forced to be an "
                      "explicit choice-and-reason, not an acceptance",
         "specificity": "{problem} anchors it to something real"}),

    Blueprint(
        "requirements-extraction", "Requirements / constraint extraction",
        "planning",
        ["specificity"],
        "A constraint stated before code is written is checkable later; "
        "one discovered after is a bug report.",
        "Before writing any code for {feature}: list every constraint "
        "(performance, format, dependency, security) implied by "
        "{context}. I will confirm or correct this list before you "
        "start.",
        {"specificity": "forces enumeration of real constraints instead "
                        "of leaving them implicit"}),

    Blueprint(
        "api-design", "API / interface design",
        "design",
        ["direction", "specificity"],
        "Naming the exact contract (types, error modes, versioning) "
        "before implementation is the specificity dimension made "
        "concrete.",
        "Design the {interface_name} interface for {purpose}. State: "
        "the exact method signatures, what each error condition returns, "
        "and whether this is Stable or Experimental per our stability "
        "policy. Do not implement yet.",
        {"specificity": "signatures and error modes are unambiguous, "
                        "checkable claims",
         "direction": "the stability-tier question forces a real design "
                      "decision, not just code"}),

    Blueprint(
        "rag-retrieval", "RAG / retrieval pipeline",
        "implementation",
        ["direction", "specificity", "iteration"],
        "Retrieval is exactly the topic HackerRank's own writeup singles "
        "out: 'we used RAG' scores low, naming the retrieval method and "
        "why it fits the corpus scores high.",
        "Before choosing a retrieval method for {corpus_description}: "
        "state whether this needs exact-term matching or semantic "
        "similarity, and why. Then implement it and run it against "
        "{n_sample_queries} sample queries, reporting exact hit/miss "
        "counts.",
        {"direction": "forces a stated reason for the retrieval choice, "
                      "not just 'add RAG'",
         "iteration": "the sample-query run is a real, reportable "
                      "measurement, not a claim"}),

    Blueprint(
        "agent-safety", "Agent safety / guardrail design",
        "implementation",
        ["safety", "direction"],
        "The rubric's safety dimension explicitly rewards a stated "
        "MECHANISM ('the gate runs before the model and cannot be "
        "overridden') over a stated GOAL ('handle it safely').",
        "For {risk_category}: design a mechanism (not a policy "
        "statement) that prevents the model from producing an unsafe "
        "output even if the prompt is adversarial. State exactly what "
        "runs before the model call and what it's allowed to do.",
        {"safety": "'mechanism, not policy' is the literal instruction",
         "direction": "requires the human to specify the enforcement "
                      "point, a real architecture decision"}),

    Blueprint(
        "regression-check", "Regression / benchmark verification",
        "verification",
        ["iteration", "specificity"],
        "A reported regression-and-revert is one of the strongest "
        "iteration-dimension signals a transcript can contain -- it's "
        "proof a real test loop happened.",
        "Run {test_command} before and after this change and report "
        "exact pass/fail counts for both. If anything regresses, name "
        "the specific case and either fix it or revert -- do not ship a "
        "known regression silently.",
        {"iteration": "forces a before/after measurement pair, the "
                      "clearest form of the pattern"}),

    Blueprint(
        "security-review", "Security review of a change",
        "verification",
        ["safety", "specificity"],
        "Same as agent-safety, applied to code review: naming the "
        "specific attack surface beats a generic 'looks secure'.",
        "Review {diff_or_files} specifically for: injection via "
        "{input_source}, secrets in code vs. env vars, and whether any "
        "new dependency changes the trust boundary. Name the specific "
        "risk, not a general assessment.",
        {"safety": "requires a named attack surface, not a checkbox",
         "specificity": "{diff_or_files} and {input_source} anchor it"}),

    Blueprint(
        "release-readiness", "Pre-release / production-readiness check",
        "release",
        ["iteration", "safety", "direction"],
        "Combines all three non-specificity dimensions: a real gate run, "
        "a stated risk, and an explicit go/no-go decision the human "
        "owns.",
        "Run the full release gate for {component}. Report every check "
        "that failed or was skipped -- a skipped check is UNKNOWN, not a "
        "pass. I will make the ship/no-ship call based on what you "
        "report, not on your recommendation alone.",
        {"iteration": "requires the actual gate to run, not a summary",
         "direction": "the human explicitly reserves the final decision",
         "safety": "'skipped is UNKNOWN, not a pass' forces honest "
                   "reporting of gaps"}),
]

BY_KEY = {b.key: b for b in BLUEPRINTS}


def for_dimension(key: str) -> list[Blueprint]:
    return [b for b in BLUEPRINTS if key in b.targets]


def for_stage(stage: str) -> list[Blueprint]:
    return [b for b in BLUEPRINTS if b.stage == stage]
