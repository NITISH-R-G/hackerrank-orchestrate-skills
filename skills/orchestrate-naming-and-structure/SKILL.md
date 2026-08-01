---
name: orchestrate-naming-and-structure
description: Structure a HackerRank Orchestrate codebase with clear separation of concerns and descriptive naming — the specific pattern HackerRank's own advice calls out as scored. Use when scaffolding a new Orchestrate project, when a codebase has accumulated files named "helper.py" or "utils.js", or before submission when reviewing whether a fresh reader (or interviewer) could find the entry point and understand the main flow in under a minute.
---

# Orchestrate: Naming and Structure

**Direct evidence**: HackerRank's guidance is explicit — code *"should be runnable and readable. Anyone should be able to open it, find the entry point, understand the main flow."* Named mistakes: *"Poor naming: Don't use generic filenames like 'helper' or 'utils'—use descriptive names reflecting file purpose."* Named recommended practice: *"Separate concerns clearly: input loading, prompts, agent logic, validation, evaluation."*

## The five concerns, kept separate

The organizer's own list is the checklist:

| Concern | What lives here | What doesn't |
|---|---|---|
| **Input loading** | Reading the corpus/CSVs, parsing tickets/claims into structured objects | Any decision-making logic |
| **Prompts** | The actual prompt templates, versioned and readable as text | Business logic that decides *which* prompt to use |
| **Agent logic** | The loop: decide next action, call tools, interpret results | Prompt text, validation rules |
| **Validation** | Schema checks, enum checks, the guardrail pattern from `orchestrate-schema-guardrails` | Agent decision-making |
| **Evaluation** | Comparing output against `sample_*.csv`, computing metrics | Production agent code |

A codebase where these five are tangled into one 400-line `main.py` fails this check even if it produces correct output — because "correct output" is only 30-60% of what's being scored (code quality is a separate 30%, and the interview probes architecture directly).

## Naming: the concrete test

Open your file tree with no other context. For each file, ask: does the name alone tell you what's inside? `helper.py`, `utils.js`, `main2.py`, `test_new.py` all fail this test. `ticket_classifier.py`, `corpus_retriever.py`, `output_validator.py` pass it.

This isn't cosmetic. A judge or interviewer navigating your zip under time pressure (the interview is 30 minutes, covering your whole system) reads file names before file contents — bad names cost real evaluation time and read as a proxy for care taken elsewhere.

## Practical scaffold

```
code/
  main.py                  # entry point — obvious from the name and from being at the root
  ingestion/
    corpus_loader.py
    ticket_parser.py
  agent/
    triage_agent.py         # the actual decide-and-act loop
    prompts.py               # prompt templates, kept as data, not inline strings
  validation/
    schema_guardrails.py
  evaluation/
    score_against_sample.py
  README.md                 # setup, dependencies, how to run — see orchestrate-submission-review
```

## Anti-pattern this prevents

A single-file or single-function submission where the "agent loop" is actually one big prompt with a giant system message trying to do retrieval, classification, and response generation all in one LLM call. This fails both the naming/structure check *and* the "actual agent loop vs. hardcoded workflow" architecture check from the rubric — the two are connected, not coincidental.
