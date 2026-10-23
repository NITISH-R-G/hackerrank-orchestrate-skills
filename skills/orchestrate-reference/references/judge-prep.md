# AI Judge Interview Preparation

**Evidence tier: first-hand (August 2026).** One completed Orchestrate interview.

---

## What this document is, and is not

**IS**: the topics an Orchestrate AI judge actually probed, the judge's own closing
feedback verbatim, model answers, follow-up traps, and the constants discipline the
judge explicitly asked for.

**IS NOT**: a transcript. The interview was not recorded question-by-question.

> **This matters.** A prep guide that invents "the question the judge asked and the
> answer I gave" is worthless — you would rehearse fiction. Everything below is either
> quoted from the real interview, or clearly marked as a **model answer** written
> afterwards.

| Label | Meaning |
|---|---|
| **QUOTED** | verbatim from the real interview |
| **TOPIC (confirmed)** | the judge probed this area; exact wording not recorded |
| **MODEL** | an answer written for this guide, not one that was given |
| **UNKNOWN** | not determinable |

---

## 1. What the judge actually said

**QUOTED — the praise:**

> *"...measuring your own assumptions and being willing to reject changes that didn't
> improve things..."*

**QUOTED — the one criticism:**

> *"knowing your own constants... In production AI systems, owning every number in your
> code is part of owning the decision."*

Context: the judge asked about retrieval hyperparameters that had shipped. The
participant could not recall them.

**What this tells you about scoring.** The judge did not challenge the architecture,
the evaluation methodology, the AI-assisted workflow, or the honesty about limitations.
The strongest available criticism after a deep technical discussion was *depth of
ownership over implementation details*. That is a high bar being applied, not a
rejection.

---

## 2. Topics probed — TOPIC (confirmed)

The interview covered:

1. High-level architecture
2. Deterministic vs LLM-based reasoning
3. Arbitration design
4. End-to-end execution flow
5. BM25 retrieval
6. Confidence calibration
7. AI-assisted development workflow
8. Engineering tradeoffs
9. Honesty about limitations

Prepare all nine. They are not exotic — they are the load-bearing decisions of any
Orchestrate submission.

---

## 3. The constants drill — do this first

The judge's criticism converts directly into an exercise. Build `CONSTANTS.md` with a
**provenance** column:

| Provenance | Meaning | How to answer if asked |
|---|---|---|
| **MEASURED** | an experiment chose it; another value scored worse | give the number **and** the losing alternative |
| **SPEC** | fixed by the problem statement or the observed labels | cite the line |
| **STANDARD** | canonical value from the literature, **not tuned by you** | say exactly that |
| **BOUND** | derived from an external standard | cite the standard |
| **JUDGEMENT** | reasoned, not measured | say so, and give the reasoning |

**The provenance column matters more than the numbers.**

A generic prep template will tell you to write *"BM25 k1 — chosen after evaluation."*
If you did not sweep it, that is a fabrication, and it dies to one follow-up: *"show me
the sweep."*

**MODEL answer for an untuned standard value:**

> *"k1=1.5, b=0.75 — the canonical Robertson/Spärck Jones defaults. I deliberately did
> not tune them. My tokens are sets, so term frequency is 1 by construction and k1 only
> scales the length-normalisation denominator. Tuning two hyperparameters against 28
> labeled rows is how you overfit a hidden set."*

That answer turns the weakest point into a demonstration of the exact discipline the
judge praised.

**Constants worth having ready** (yours will differ — these are the *categories*):
retrieval hyperparameters · confidence floor and ceiling · evidence count · any
downscale or resize dimension · confidence threshold for a provider · every numeric
threshold in a rule · every regex quantifier bound · every timeout.

---

## 4. Model answers for the nine topics

Each is **MODEL** — written for this guide. Substitute your own measurements.

### Architecture

**Structure:** claim → evidence → boundary → rejected alternative.

> *"A deterministic rule engine, three tiers: safety, relationship/urgency, engagement.
> I chose it over an LLM classifier on three measurements: the labeled reasons were
> templated — 24 distinct strings across 30 rows — so ground truth states which rule
> fired, not what the message said. One labeled row was a prompt-injection attack whose
> correct label was mute/scam, and a rule engine is structurally immune because message
> text never enters a decision-making prompt. And the safety-critical signals were all
> structured fields, not prose. The model layer earns its place only where structured
> data can't reach: reading a poster, hearing a voice note."*

**Trap:** *"Isn't that just if-statements?"*
> *"Yes — and that's the property I wanted. Every decision is attributable to a named
> rule with a stated tier, and I can prove no rule is dead or shadowed. I measured the
> LLM alternative's cost: non-determinism and an injection surface, for semantic nuance
> I couldn't demonstrate a need for."*

### Deterministic vs LLM reasoning

**Trap:** *"So you didn't use AI at all?"* — Do not get defensive.
> *"I used it where it was the only thing that could work — OCR and speech — and kept
> it out of the decision path, where it would have cost determinism and added an
> injection surface. That's a scoping decision, not an avoidance of AI."*

### Arbitration

State whether it is **on or off by default**, and why.
> *"Opt-in, off by default. It was eligible on 6 of 110 rows. On the labeled rows where
> it could fire, the deterministic verdict was already correct — and escalation was its
> only possible action, so every intervention it could make there was a guaranteed
> regression. It also put a network call and raw message text into a prompt. I kept the
> capability and disabled the default."*

### Execution flow

Be able to trace **one row end to end**, naming each module. Judges ask this to check
you know your own system rather than a diagram of it.

### Retrieval

Lead with the ceiling, then the bake-off, then the diagnosed mechanism. See
[`orchestrate-evidence-retrieval-expert`](./skills/orchestrate-evidence-retrieval-expert).

**Trap:** *"Why not embeddings?"*
> *"I benchmarked them: F1 0.479 against 0.512 for lexical. The relation being scored
> is topical word overlap, not paraphrase — which is what bi-encoders are built for."*

### Confidence calibration

The counter-intuitive one, and a strong differentiator.
> *"My ECE was 0.138, which looks under-confident. Before fixing it I measured the
> ground truth's own ECE: 0.1597 — worse. The labels are deliberately under-confident,
> so every ECE-improving shift moved my error against the actual target from 0.026 to
> 0.147. I calibrated to the labeling policy, not to textbook calibration."*

### AI-assisted workflow

**Check the rules first** — most Orchestrate events explicitly permit AI assistance and
say the deliverable is what the system does, not how it was written.
> *"I used an AI assistant, which the rules allow. I set the acceptance bar — every
> change had to name the metric it improved before it was written — and I rejected nine
> proposed optimisations that failed it."*

**Never say:** *"I wrote every line myself"* if you did not.

### Tradeoffs

Have three ready, each with a number and a cost. The best ones are **rejections**.

### Limitations

Volunteer them. Unprompted limitation-naming converts an accusation into evidence of
rigour.

---

## 5. Follow-up traps

| Trap | Weak | Strong |
|---|---|---|
| *"Why that number?"* | "It seemed reasonable" | provenance + losing alternative, or "judgement call, here's the reasoning" |
| *"Is it deterministic?"* | "Yes" | "Offline yes — one hash across N processes and hash seeds. With the hosted provider, no, and here's the row where it varied." |
| *"Did you overfit?"* | "No" | "Here are six ideas I rejected *because* they overfit, with the numbers." |
| *"Does OCR help?"* | "Yes, it's multimodal" | "It changed 0 of 110 rows. It's there for spec compliance and safety — and here's the counterfactual proving the channel is live." |
| *"What's your score?"* | "100%" | "100% on 30 labeled rows. That's 30 rows, disjoint from the graded set. I can't verify the hidden set." |
| *"Walk me through a row"* | vague | name every module in order, with the actual field names |
| *"What would you do with more time?"* | a feature list | the specific uncertainty you could not resolve, and the experiment that would resolve it |

---

## 6. Claims that must never be made unless directly supported

1. "I committed incrementally" — **read your `git log` first.** A single squashed commit is common and checkable in seconds.
2. "I wrote every line myself" — if an assistant was involved, say so.
3. "My system is deterministic" — unqualified, usually false. State the boundary.
4. "OCR/vision improves my score" — only if measured. It may be exactly zero.
5. "I score 100%" — always name the set and its size.
6. "My retrieval is optimal" — "Pareto-optimal among N tested configurations" is the defensible form.
7. "There are no dataset-specific assumptions" — "I hunted them and removed the ones I found" is honest.
8. "It handles every scam type" — 58/58 on a battery *you wrote* is not coverage.
9. "The tests prove it generalises" — a labeled sample is not a held-out set.
10. "I know it will rank well" — you do not, and saying so costs credibility.

---

## 7. The hour before

- [ ] `CONSTANTS.md` written, provenance filled in, read once aloud
- [ ] Three rejections memorised **with numbers**
- [ ] One row traced end to end, module by module
- [ ] Every guarantee has a boundary sentence prepared
- [ ] `git log` actually read
- [ ] Two limitations chosen to volunteer unprompted
- [ ] "I don't remember, but I can tell you how it was chosen" — rehearsed

**The last one is not a fallback, it is a strategy.** A judge who catches an invented
number discounts everything else you said. One that hears an honest "I don't recall"
alongside a correct account of *how* it was chosen sees an engineer with calibrated
confidence.
