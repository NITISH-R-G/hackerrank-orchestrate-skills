"""The question bank.

Topics are drawn from a real Orchestrate AI-judge interview (the nine areas it
actually probed) plus the areas that interview did NOT reach but that any
serious reviewer would.

Every question carries:

  level      1 (foundational) .. 5 (adversarial)
  probes     what a strong answer must contain -- used for weakness detection
  trap       the common weak answer, so the report can name it
  strong     the SHAPE of a good answer, never the content

`strong` is deliberately structural. A bank that supplied model answers would
be a script to memorise, and a judge who hears a memorised script asks the one
follow-up it does not cover.
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class Question:
    key: str
    topic: str
    level: int
    text: str
    probes: list[str] = field(default_factory=list)
    trap: str = ""
    strong: str = ""
    follow_ups: list[str] = field(default_factory=list)


TOPICS = {
    "architecture": "System design and why it is that shape",
    "determinism": "Deterministic vs model-based reasoning",
    "arbitration": "When a model is allowed to overrule rules",
    "flow": "End-to-end execution",
    "retrieval": "Evidence retrieval and ranking",
    "confidence": "Confidence and calibration",
    "multimodal": "Images, audio, and what they are allowed to decide",
    "evaluation": "How you know it works",
    "generalization": "Behaviour on data you have not seen",
    "security": "Adversarial input",
    "process": "How the work was done, including AI assistance",
    "limitations": "What you do not know",
}

BANK: list[Question] = [
    # ---------------------------------------------------- architecture
    Question("arch-1", "architecture", 1,
             "Describe your system's architecture at a high level.",
             probes=["named components", "ordering or precedence", "why"],
             trap="A component list with no reason attached to any of it.",
             strong="claim -> evidence -> boundary -> the alternative you rejected",
             follow_ups=["arch-2", "arch-3"]),
    Question("arch-2", "architecture", 2,
             "What did you choose that over, and what measurement made the "
             "decision?",
             probes=["a named alternative", "a number", "a property of the data"],
             trap="'It seemed simpler' -- a preference, not a decision.",
             strong="Name the alternative, name the property of the DATA that "
                    "ruled it out, give the measurement."),
    Question("arch-3", "architecture", 3,
             "A rule engine is just if-statements. Why is that engineering?",
             probes=["attributability", "determinism", "proof of reachability",
                     "the cost you avoided"],
             trap="Getting defensive, or claiming sophistication it does not have.",
             strong="Agree with the premise, then state the property that made "
                    "it the right choice, and the measured cost of the "
                    "alternative."),
    Question("arch-4", "architecture", 4,
             "Which single component, if removed, would degrade your output "
             "the most? Show me you have measured that rather than assumed it.",
             probes=["a counterfactual", "row counts", "an ablation"],
             trap="Naming the component you spent the most time on.",
             strong="An ablation table. The honest answer is often 'the "
                    "component I spent longest on changes zero rows.'"),
    Question("arch-5", "architecture", 5,
             "Suppose I tell you a submission with the opposite architecture "
             "scored higher. What in your design would you keep, and what "
             "would you concede?",
             probes=["a genuine concession", "a defended invariant",
                     "no capitulation"],
             trap="Total capitulation, or total defence. Both read as "
                  "un-calibrated.",
             strong="Concede the parts that were judgement calls; defend the "
                    "parts that were measured, with the measurement."),

    # ---------------------------------------------------- determinism
    Question("det-1", "determinism", 1,
             "Is your system deterministic?",
             probes=["a boundary", "the condition under which it is not"],
             trap="An unqualified 'yes'. Almost always false, and one follow-up "
                  "away from exposure.",
             strong="'Offline, yes -- one hash across N processes and N hash "
                    "seeds. With the hosted provider enabled, no, and here is "
                    "the row where it varied.'",
             follow_ups=["det-2", "det-3"]),
    Question("det-2", "determinism", 2,
             "How did you verify that claim? Be specific about what you varied.",
             probes=["repeated runs", "hash seed", "process boundary",
                     "byte comparison"],
             trap="'The tests pass.' Tests in one process share a hash seed.",
             strong="Separate processes, varied PYTHONHASHSEED, byte-compared "
                    "artifacts."),
    Question("det-3", "determinism", 3,
             "You said you used AI. Where exactly does a model output enter a "
             "decision, and what stops it from making the run irreproducible?",
             probes=["the scoping decision", "which tier", "a default-off gate"],
             trap="Confusing 'I used AI for extraction' with 'AI makes decisions'.",
             strong="Name the modality boundary, and the gate that keeps the "
                    "model out of the decision path by default."),
    Question("det-4", "determinism", 4,
             "If determinism mattered so much, why is any hosted call in the "
             "shipped path at all?",
             probes=["what the local alternative loses", "a measured comparison",
                     "the boundary you documented"],
             trap="'Determinism is nice to have.' You already argued it was "
                  "load-bearing.",
             strong="State the specific capability only the hosted path has, "
                    "with the probe that showed the local one losing it."),

    # ---------------------------------------------------- arbitration
    Question("arb-1", "arbitration", 2,
             "Do you have a mechanism where a model can overrule your "
             "deterministic decision? Is it on or off by default?",
             probes=["on/off stated explicitly", "eligibility count", "why"],
             trap="Not knowing the default. This is the classic finding: gated "
                  "on credential presence, therefore silently on.",
             strong="State the default, the number of eligible rows, and the "
                    "measured effect on those rows.",
             follow_ups=["arb-2"]),
    Question("arb-2", "arbitration", 3,
             "On the rows where it was eligible, did it ever improve anything?",
             probes=["a row count", "the direction of its only possible action"],
             trap="'It would help on hard cases' -- speculation.",
             strong="'It was eligible on N rows. On the labeled subset the "
                    "deterministic verdict was already correct, and escalation "
                    "was its only possible action, so every intervention was a "
                    "guaranteed regression.'"),

    # ---------------------------------------------------- flow
    Question("flow-1", "flow", 2,
             "Take one input row and trace it end to end. Name every module it "
             "passes through, in order.",
             probes=["module names", "ordering", "actual field names"],
             trap="Describing the diagram instead of the code. Judges ask this "
                  "specifically to tell those apart.",
             strong="Named modules in real order, with the actual field names "
                    "that get set along the way."),
    Question("flow-2", "flow", 3,
             "Where in that flow can a single malformed row take down the "
             "entire run?",
             probes=["error isolation", "where the handler sits", "a test"],
             trap="'It's wrapped in try/except.' Where, exactly? A handler "
                  "below the raising line catches nothing.",
             strong="Name the isolation boundary and the injected-failure test "
                    "that proves it."),

    # ---------------------------------------------------- retrieval
    Question("ret-1", "retrieval", 1,
             "How do you select supporting evidence?",
             probes=["the method", "the candidate pool", "the scoring function"],
             trap="Naming a library instead of a mechanism.",
             strong="Pool construction first, then the ranking function, then "
                    "the cap.",
             follow_ups=["ret-2", "ret-3"]),
    Question("ret-2", "retrieval", 2,
             "Why not embeddings?",
             probes=["a measured comparison", "the nature of the relation",
                     "a number"],
             trap="'Embeddings are overkill.' Untestable, and reads as avoidance.",
             strong="Give the benchmark, then diagnose WHY: the relation being "
                    "scored is topical overlap, not paraphrase."),
    Question("ret-3", "retrieval", 3,
             "What are your retrieval hyperparameters, and how were they chosen?",
             probes=["the actual values", "provenance", "whether they were tuned"],
             trap="Claiming a sweep you did not run. This dies instantly to "
                  "'show me the sweep.'",
             strong="'Canonical defaults, deliberately untuned -- tuning two "
                    "parameters against N labeled rows is how you overfit a "
                    "hidden set.' Owning an untuned constant beats inventing a "
                    "tuned one."),
    Question("ret-4", "retrieval", 4,
             "What is the ceiling of your retrieval -- the best score achievable "
             "with a perfect ranker over your current candidate pool?",
             probes=["a ceiling number", "pool construction", "the tradeoff"],
             trap="Not having computed it. Then every ranking improvement is "
                  "unbounded guesswork.",
             strong="Give the ceiling, then explain why you did NOT widen the "
                    "pool to raise it."),
    Question("ret-5", "retrieval", 5,
             "Your evidence misses some rows. Take one and tell me precisely "
             "why it is unfixable -- or admit it is fixable and you ran out of "
             "time.",
             probes=["a specific row", "a mechanism", "an honest admission"],
             trap="Claiming all remaining errors are unfixable. Usually false.",
             strong="Separate the genuinely impossible (the gold id is not in "
                    "any reachable pool) from the merely hard, and say which is "
                    "which."),

    # ---------------------------------------------------- confidence
    Question("conf-1", "confidence", 2,
             "How is confidence computed, and what is it calibrated against?",
             probes=["the mechanism", "the target", "a measurement"],
             trap="'It reflects how sure the system is' -- unfalsifiable.",
             strong="Name what the number is fit to, and the error against it.",
             follow_ups=["conf-2"]),
    Question("conf-2", "confidence", 4,
             "Your calibration error looks poor. Why did you not fix it?",
             probes=["ground truth's own calibration", "the scored quantity",
                     "a measured tradeoff"],
             trap="Fixing it. Improving ECE can move you away from the scored "
                  "value if the labels are deliberately under-confident.",
             strong="'I measured the ground truth's own ECE first -- it was "
                    "worse than mine. Every ECE-improving shift made MAE "
                    "against the actual target worse.'"),

    # ---------------------------------------------------- multimodal
    Question("mm-1", "multimodal", 1,
             "How does your system handle images and audio?",
             probes=["the extraction path", "what it is allowed to affect"],
             trap="'It's multimodal' as a feature claim rather than a mechanism.",
             strong="Extraction method per modality, then the SCOPE of what "
                    "each is permitted to change.",
             follow_ups=["mm-2", "mm-3"]),
    Question("mm-2", "multimodal", 3,
             "Does reading images actually change your output? Give me a number.",
             probes=["a row count", "a counterfactual", "honesty about zero"],
             trap="Implying it helps when it changes zero rows.",
             strong="'It changed 0 of N rows. It is there for spec compliance "
                    "and safety, and here is the counterfactual showing the "
                    "channel is live: with OCR disabled, 7 pixel-only scams "
                    "escape.'"),
    Question("mm-3", "multimodal", 4,
             "Should text found inside an image be able to change what you "
             "think the SENDER meant?",
             probes=["a trust boundary", "authorship", "an asymmetry"],
             trap="Treating OCR text as equivalent to message text. It has a "
                  "different author.",
             strong="'A poster is authored by a third party. It may escalate "
                    "safety; it must not redefine intent. Voice is different -- "
                    "the transcript IS the message.'"),
    Question("mm-4", "multimodal", 5,
             "If a judge assumes OCR-only submissions are lazy, what do you say?",
             probes=["headroom analysis", "the strongest rejected version",
                     "no capitulation to fashion"],
             trap="Adding a vision model to look serious.",
             strong="Show the headroom is zero, and show you built the "
                    "strongest version of the alternative before rejecting it."),

    # ---------------------------------------------------- evaluation
    Question("eval-1", "evaluation", 1,
             "What is your score, and on what?",
             probes=["a number", "the set", "the SIZE of the set"],
             trap="A bare percentage. Always name the set and its size.",
             strong="'N/N on M labeled rows. That is M rows, with an id space "
                    "disjoint from the graded set. I cannot verify the hidden "
                    "set.'",
             follow_ups=["eval-2", "eval-3"]),
    Question("eval-2", "evaluation", 3,
             "Did you overfit?",
             probes=["rejected optimisations", "numbers", "coupling audit"],
             trap="'No.' Unfalsifiable and unconvincing.",
             strong="'Here are N ideas I rejected BECAUSE they overfit, with "
                    "the measurements.' Rejections are the evidence."),
    Question("eval-3", "evaluation", 4,
             "Tell me about a time your own measurement was wrong.",
             probes=["a specific broken harness", "how it was caught",
                     "what changed"],
             trap="Not having one. Either the harnesses were never audited, or "
                  "this is being hidden. Both are worse than the bug.",
             strong="Name the harness, the clean-but-false result, the real "
                    "answer after the fix, and the process change."),
    Question("eval-4", "evaluation", 5,
             "Every check in your repository is green. Convince me that is "
             "informative rather than decorative.",
             probes=["a negative control", "a deliberately injected defect"],
             trap="Listing the checks. The number of checks is not the point.",
             strong="'I injected N defect classes into a healthy repository and "
                    "confirmed the harness caught each one.' A suite that has "
                    "never failed has never been tested."),

    # ---------------------------------------------------- generalization
    Question("gen-1", "generalization", 3,
             "What in your code depends on something specific to the sample "
             "data you were given?",
             probes=["id shape", "timestamp format", "row order",
                     "file extensions", "an actual finding"],
             trap="'Nothing.' Nobody has ever been right about this.",
             strong="'I hunted them and removed the ones I found -- here are "
                    "four, and here is the probe that found each.'"),
    Question("gen-2", "generalization", 4,
             "If I renamed every identifier and reformatted every timestamp, "
             "what would break?",
             probes=["a mutation test", "row counts before and after"],
             trap="Reasoning about it instead of having run it.",
             strong="Report the mutation experiment: N decisions broke before "
                    "the fix, 0 after."),
    Question("gen-3", "generalization", 5,
             "Your accuracy on the visible set is perfect. Give me your honest "
             "estimate for the hidden set, and defend the number.",
             probes=["refusal to fabricate", "the reason it is unknowable",
                     "what WOULD be predictive"],
             trap="Any confident number. There is no basis for one.",
             strong="'UNKNOWN, and here is why: the labeled set is M rows with "
                    "a disjoint id space. That information is absent from the "
                    "data, not merely unexamined.'"),

    # ---------------------------------------------------- security
    Question("sec-1", "security", 2,
             "Someone sends a message containing instructions aimed at your "
             "system. What happens?",
             probes=["the structural property", "where text does and does not go"],
             trap="'I sanitise the input.' Sanitising is a filter; structure is "
                  "a guarantee.",
             strong="'Message text never enters a decision-making prompt, so "
                    "there is nothing to inject into. Here is the labeled row "
                    "that was exactly this attack.'"),
    Question("sec-2", "security", 3,
             "What is the worst thing an attacker can do to your runtime with "
             "a single message?",
             probes=["a latency or memory bound", "a measured number",
                     "the fix and its provenance"],
             trap="Not having looked. Unbounded quantifiers are the default.",
             strong="Name the measured worst case, the bound you applied, and "
                    "where the bound comes from -- a real standard, not a guess."),
    Question("sec-3", "security", 4,
             "Which of your components would you not trust if the input corpus "
             "were written by an adversary who had read your code?",
             probes=["a specific weak component", "a stated residual risk"],
             trap="'All of them are fine.'",
             strong="Name the weakest one and its residual risk. Everyone has "
                    "one."),

    # ---------------------------------------------------- process
    Question("proc-1", "process", 1,
             "How did you build this? Did you use AI assistance?",
             probes=["honesty", "the acceptance bar you set", "what you rejected"],
             trap="'I wrote every line myself', if untrue. Also: apologising "
                  "for using AI when the rules permit it.",
             strong="'Yes, which the rules allow. I set the acceptance bar -- "
                    "every change had to name the metric it improved before it "
                    "was written -- and I rejected N proposals that failed it.'"),
    Question("proc-2", "process", 2,
             "Walk me through your commit history.",
             probes=["having actually read it", "no fabricated incrementalism"],
             trap="'I committed incrementally.' Squashed history is normal and "
                  "checkable in ten seconds.",
             strong="If it is one commit, say so, and point to where the "
                    "process actually lives: numbered defects annotated at each "
                    "fix site."),
    Question("proc-3", "process", 4,
             "Name a decision you reversed, and what reversed it.",
             probes=["a specific reversal", "the evidence", "no ego"],
             trap="Not having one, or naming a trivial one.",
             strong="A reversal that cost real work, with the measurement that "
                    "forced it."),

    # ---------------------------------------------------- limitations
    Question("lim-1", "limitations", 2,
             "What does your system not handle?",
             probes=["a volunteered limitation", "specificity", "cost"],
             trap="A humblebrag ('it's maybe too thorough').",
             strong="Two real limitations with their cost, offered before "
                    "being pushed."),
    Question("lim-2", "limitations", 3,
             "What would you do with another week?",
             probes=["a specific uncertainty", "the experiment that resolves it"],
             trap="A feature list. Features are not the bottleneck; unresolved "
                  "uncertainty is.",
             strong="Name the uncertainty you could not resolve and the exact "
                    "experiment that would resolve it."),
    Question("lim-3", "limitations", 5,
             "What is the single strongest argument AGAINST your submission? "
             "Make it better than I could.",
             probes=["a genuine strong argument", "no strawman",
                     "an honest response"],
             trap="A weak argument you can easily knock down. The interviewer "
                  "notices.",
             strong="State the real one -- usually that a perfect visible score "
                    "on a small set predicts little -- then say what you did "
                    "about it anyway."),
]

BY_KEY = {q.key: q for q in BANK}


def by_topic(topic: str) -> list[Question]:
    return [q for q in BANK if q.topic == topic]


def select(topics: list[str] | None, lo: int, hi: int) -> list[Question]:
    pool = [q for q in BANK if lo <= q.level <= hi]
    if topics:
        pool = [q for q in pool if q.topic in topics]
    return pool
