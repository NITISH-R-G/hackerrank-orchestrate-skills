"""Generic row-by-row runner for an Orchestrate challenge.

    python run_pipeline.py --input dataset/messages.csv --output output.csv \
        --decider baseline_aug_router:decide \
        --columns message_id,action,message_type,reason,confidence,evidence_message_ids \
        --allowed action=notify,digest,mute --failure-default action=digest \
        --checkpoint .checkpoint.jsonl

Each row goes through `decider(row) -> dict`. The runner:
  * never lets one bad row stop the run: an exception becomes a failure row
  * validates every enum column and replaces an invalid value with the failure default
  * checkpoints each finished row, so a rerun resumes instead of starting over
  * writes one output row per input row, in input order
"""

from __future__ import annotations

import argparse
import csv
import importlib
import json
import sys
from pathlib import Path


def load_decider(spec: str):
    module, _, func = spec.partition(":")
    return getattr(importlib.import_module(module), func or "decide")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--input", required=True, type=Path)
    ap.add_argument("--output", required=True, type=Path)
    ap.add_argument("--decider", required=True, help="module:function returning a dict of output columns")
    ap.add_argument("--columns", required=True)
    ap.add_argument("--key", default=None, help="input ID column (default: first input column)")
    ap.add_argument("--allowed", action="append", default=[], help="column=v1,v2 for enum columns")
    ap.add_argument("--failure-default", action="append", default=[],
                    help="column=value used when a row fails or an enum value is invalid")
    ap.add_argument("--checkpoint", type=Path, default=None)
    args = ap.parse_args()

    sys.path.insert(0, str(Path.cwd()))
    decide = load_decider(args.decider)
    columns = [c.strip() for c in args.columns.split(",")]
    allowed = {}
    for spec in args.allowed:
        col, _, vals = spec.partition("=")
        allowed[col] = {v.strip() for v in vals.split(",")}
    defaults = {}
    for spec in args.failure_default:
        col, _, val = spec.partition("=")
        defaults[col] = val

    with args.input.open(encoding="utf-8", newline="") as fh:
        rows = list(csv.DictReader(fh))
    key = args.key or next(iter(rows[0]))

    done = {}
    if args.checkpoint and args.checkpoint.exists():
        for line in args.checkpoint.read_text(encoding="utf-8").splitlines():
            rec = json.loads(line)
            done[rec["key"]] = rec["out"]

    failures = 0
    out_rows = []
    for row in rows:
        k = row[key]
        if k in done:
            out_rows.append(done[k])
            continue
        try:
            result = decide(row)
            out = {c: str(result.get(c, "")) for c in columns}
        except Exception as exc:  # one bad row must not stop the run
            failures += 1
            out = {c: defaults.get(c, "") for c in columns}
            print(f"row {k} failed: {type(exc).__name__}: {exc}", file=sys.stderr)
        for col, ok in allowed.items():
            if col in out and out[col] not in ok:
                failures += 1
                out[col] = defaults.get(col, sorted(ok)[0])
        out[columns[0]] = k
        out_rows.append(out)
        if args.checkpoint:
            with args.checkpoint.open("a", encoding="utf-8") as fh:
                fh.write(json.dumps({"key": k, "out": out}) + "\n")

    with args.output.open("w", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=columns)
        writer.writeheader()
        writer.writerows(out_rows)
    print(f"wrote {len(out_rows)} rows to {args.output}; {failures} row/column failures handled")
    return 0


if __name__ == "__main__":
    sys.exit(main())
