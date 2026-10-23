---
name: orchestrate-agent-architecture
description: Designing the agent itself for an Orchestrate-style challenge — real agent loops versus hardcoded workflows, tool boundaries, prompt structure, and the design decisions a judge can actually see in your code. Use when starting to build an AI agent for a hackathon or evaluation, when deciding between a scripted pipeline and an agentic loop, when structuring tools/prompts for an agent, or when reviewing whether an agent design would read as genuinely agentic to a reviewer.
---

# Orchestrate Agent Architecture

HackerRank's own description of the code rubric is unusually specific and worth quoting directly: it measures **"whether submissions contain actual agent loops versus hardcoded workflows."** That is a stated, explicit discriminator. It's also the single easiest place to lose 30% of your score while producing something that technically works.

## The hardcoded-workflow trap

Under time pressure the tempting shape is:

```python
for ticket in tickets:
    category = classify(ticket)          # one LLM call
    if category == "billing":
        urgency = check_billing_rules(ticket)
    elif category == "technical":
        urgency = check_tech_rules(ticket)
    ...
    if urgency > THRESHOLD:
        escalate(ticket)
    else:
        respond(ticket)
```

This can score well on raw correctness and still read as a **decision tree with LLM calls embedded in it**, not an agent. Every branch was decided by you, at authoring time. The model fills in blanks; it doesn't decide anything about *how to approach* the problem.

## What an actual agent loop looks like

The distinguishing property: **the model decides what to do next, and the loop continues until the model says it's done** — rather than the control flow being fixed in advance by the author.

```python
def run_agent(ticket, tools, max_steps=10):
    messages = [system_prompt(), user_prompt(ticket)]
    for step in range(max_steps):
        response = model.call(messages, tools=tools)
        if response.is_final_answer:
            return response.answer
        result = execute_tool(response.tool_call)   # agent chose this tool
        messages.append(response)
        messages.append(result)
    return fallback(messages)   # hit step limit — handle explicitly
```

The agent chose: which tool, with which arguments, how many times, and when to stop. That's the thing being scored.

**This is not an argument for maximum autonomy.** A loop that wanders for 40 steps is worse than a tight pipeline. The point is that the *structure* should let the model make decisions where judgment is genuinely required, with bounded steps and explicit fallbacks — not that you should remove all structure.

## The honest middle ground

Real submissions usually want a hybrid, and that's defensible if you can articulate it. Deterministic scaffolding around an agentic core:

- **Deterministic**: loading the ticket, retrieving candidate KB documents, writing the output row, enforcing the step cap. These don't need judgment and shouldn't burn model calls.
- **Agentic**: deciding whether retrieved context is sufficient, whether to search again with a different query, whether this ticket is a jailbreak attempt, whether to escalate, and how to justify that call.

If you build a hybrid, **say so explicitly in your README and be ready to defend the boundary in the interview** — "I made retrieval deterministic because the KB is static and search quality was measurable offline; I kept escalation agentic because it's the judgment call the task actually turns on" is a strong answer. Getting asked "why isn't this just a script?" and having no answer is a weak one.

## Tool design

Tools are the agent's action surface, and their design is directly visible to a reviewer.

- **Name and describe tools for the model, not for yourself.** `search_knowledge_base(query: str)` with a description explaining when to use it beats `kb_lookup(q)` with no description. The description *is* prompt engineering.
- **Fewer, well-chosen tools beat many overlapping ones.** If two tools have similar descriptions, the model will pick wrong sometimes, and that's your bug, not the model's.
- **Return structured, informative errors.** A tool that returns `"error"` teaches the agent nothing. `"No documents matched 'refund policy 2019'. The KB covers 2021-2026."` lets the agent recover on the next step — and recovery behavior is exactly what a robustness rubric looks for.
- **Make tools individually testable.** A tool with a clean signature can be unit tested without the model in the loop, which is both good engineering and a thing you can point to under review.

## Prompt structure

Prompt quality is named explicitly in the rubric. What's visibly different between a strong and weak prompt:

- **Role and task are specific**, not "You are a helpful assistant." What system, what decisions, what stakes.
- **Decision criteria are stated**, not implied. If escalation depends on something, say what.
- **Output format is constrained and parseable** — and you validate that the model actually complied rather than assuming.
- **Refusal/uncertainty is explicitly permitted.** A prompt with no path to "I'm not sure, escalating" forces confident wrong answers. This directly affects your justification quality (see `orchestrate-justification-quality`).
- **Prompts live in named files or constants**, not inline f-strings scattered through logic. A reviewer should be able to find and read your prompts in one place — this is a real, cheap scoring signal.

## Architecture signals a reviewer can see

These are things that read well in a code review of an agent, in rough priority order:

1. The agent loop is a **named, readable function** — someone can find it in 10 seconds.
2. **Step limits and termination conditions are explicit**, not implicit in a `while True` with a `break` buried three levels deep.
3. **Prompts are extracted and versioned**, not inline.
4. **Tool definitions are declarative and colocated.**
5. **Failure paths exist and are deliberate** — what happens when the model returns malformed output, when a tool errors, when the step cap is hit.
6. **Configuration is separated from logic** — model name, thresholds, and limits aren't magic numbers mid-function.
7. **The README explains the design decisions and their tradeoffs**, not just how to run it.

Point 7 is the highest-leverage thing most people skip. Your architecture is only scored to the extent a reviewer perceives it, and a 200-word "design decisions" section costs almost nothing.

## Single-agent-with-tools versus multi-agent, for cross-context reasoning

**Added source**: a first-hand #1-ranked participant case study (Medium, "How I went from 122 to 1 in 24 hours"), specific to the multi-modal-review challenge but generalizable to any task requiring reasoning across several related pieces of evidence. The author explicitly chose a single-agent-with-tools architecture over a multi-agent one that split cross-image reasoning across separate agents passing text summaries to each other. Through direct empirical testing, they found the multi-agent split lost information at the summary-handoff boundary — weaker models failed on cases requiring nuanced comparison *between* images specifically because the comparison had to happen after lossy summarization, while stronger single-agent reasoning (with the full evidence still in context) solved the same cases correctly. Their conclusion: the bottleneck was reasoning capacity applied to the full evidence set, not image-analysis capability per se — splitting into multiple agents didn't add capability, it added an information-loss boundary.

**What this implies as a design default**: when a task's core difficulty is reasoning *across* several related pieces of evidence (multiple images for one claim, multiple KB documents for one ticket), default to a single agent holding all the relevant evidence in context and using tools to gather more of it, rather than fanning out to sub-agents that each see a slice and hand back a summary — unless you have a specific, tested reason the split doesn't lose the cross-evidence signal you need. This is one credited case study's finding, not general HackerRank guidance, but it's a concrete, testable claim worth checking against your own task rather than assuming multi-agent decomposition is always the more sophisticated (and therefore better-scoring) choice.

## Where this generalizes

None of this is Orchestrate-specific. "Does the model make decisions or does it fill in blanks in your decision tree" is the central design question for any production agent, and the tool/prompt/failure-path discipline above is what separates an agent that survives contact with real inputs from a demo. See `minimal-agent-design` in this collection for the complementary argument about keeping the harness itself simple.
