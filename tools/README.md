# tools/ — the Orchestrate Evaluator

Black-box evaluation for an Orchestrate repository. The core knows nothing about
Orchestrate; everything competition-specific lives in a plugin.

```bash
python -m aiev evaluate /path/to/your/orchestrate-repo --markdown report.md
```

```
READY   score 100/100   [generic, hackerrank-orchestrate]

   documentation    ########## 100  (1 audits, 1 findings)
   evidence         ########## 100  (1 audits, 0 findings)
   generalization   ########## 100  (1 audits, 0 findings)
   security         ########## 100  (1 audits, 0 findings)
   specification    ########## 100  (1 audits, 0 findings)
```

Exit code `2` on any blocker, so it drops into CI unchanged.

## Commands

| command | purpose |
|---|---|
| `evaluate <repo>` | run every applicable audit |
| `why-not <topic>` | why wasn't X shipped? |
| `recall <query>` | has this happened before? |
| `graph` | decision graph as Mermaid |

## Engineering Memory

Rejections are first-class records:

```bash
$ python -m aiev why-not "embeddings"

D-dense-retrieval  Dense embeddings / RRF / cross-encoder   [rejected]
  reason   : the relation scored is topical word overlap, not paraphrase
  evidence : 153 configurations benchmarked. F1 0.479 vs 0.512 shipped.
  lesson   : Benchmark the fashionable option; publish the number when it loses.
```

Seed it with the August 2026 findings:

```bash
python seed_orchestrate_memory.py /path/to/your/repo
```

Memory is written to `<repo>/.aiev/memory.json` — commit it. Memory that lives in
the tool is a cache; memory that lives with the code is institutional knowledge.

## Audits

**Generic** (any repo, any language): git hygiene · secrets in tree *and history* ·
fresh-clone simulation · artifact freshness · determinism across processes and hash
seeds · documentation claims · test isolation.

**Orchestrate plugin**: spec conformance · label leakage · output sanity · evidence
quality. Detected by dataset *shape*, not repo name, so it works for any season.

## Run a negative control first

A framework that only ever says READY is decoration. Inject known defects into a copy
and confirm it goes red. On the reference build, five injected defect classes were all
caught, plus the artifact staleness they induced.

## This tool caught itself

The first `label-leakage` audit reported a confident **BLOCKER on a healthy
repository** — three bugs at once. The postmortem is preserved at the top of
[`aiev/plugins/orchestrate/leakage.py`](aiev/plugins/orchestrate/leakage.py).
