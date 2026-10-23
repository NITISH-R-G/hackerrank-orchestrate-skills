"""Check a repo against the challenge's submission rules and build submission/.

    python package_submission.py --repo . --input dataset/requests.csv \
        --columns request_id,amount_safe_to_pay,affordability_status \
        --allowed affordability_status=affordable_now,affordable_later \
        --transcript log.txt --out submission

Checks (each prints PASS or FAIL with the evidence):
  1. output.csv exists at the repo root
  2. header equals --columns exactly (names and order)
  3. one output row per input row, same request/row IDs in the same order
  4. no empty cells in --columns
  5. every --allowed column has only allowed values
  6. code.zip-able code exists (code/ or src/), README exists, no secrets in tracked text
  7. transcript file exists (if --transcript given)

Then it writes --out/ with: output.csv, code.zip (no .git, .venv, __pycache__,
dataset/, .env), README.md, the transcript, and evaluation/usage_report.md if present.

Exit code 0 only when every check passes. Nothing is written when a check fails.
"""

from __future__ import annotations

import argparse
import csv
import re
import shutil
import sys
import zipfile
from pathlib import Path

SKIP_DIRS = {".git", ".venv", "venv", "__pycache__", "dataset", ".pytest_cache", "submission", "node_modules"}
SECRET_PATTERNS = [
    re.compile(r"sk-[A-Za-z0-9_-]{20,}"),
    re.compile(r"AKIA[0-9A-Z]{16}"),
    re.compile(r"(?i)(api[_-]?key|secret|token)\s*=\s*['\"][^'\"]{12,}['\"]"),
]


def report(ok: bool, title: str, evidence: str, results: list) -> None:
    results.append(ok)
    print(f"{'PASS' if ok else 'FAIL'}  {title}")
    if evidence:
        print(f"      {evidence}")


def read_rows(path: Path) -> tuple[list[str], list[dict]]:
    with path.open(encoding="utf-8", newline="") as fh:
        reader = csv.DictReader(fh)
        return reader.fieldnames or [], list(reader)


def files_for_zip(repo: Path) -> list[Path]:
    out = []
    for p in repo.rglob("*"):
        if not p.is_file():
            continue
        rel = p.relative_to(repo)
        if any(part in SKIP_DIRS for part in rel.parts):
            continue
        if p.name in {".env", "output.csv"} or p.suffix in {".pyc", ".log"} and p.name != "log.txt":
            continue
        out.append(p)
    return out


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--repo", default=".", type=Path)
    ap.add_argument("--input", required=True, type=Path, help="the input file the output must cover")
    ap.add_argument("--key", default=None, help="ID column to match rows on (default: first input column)")
    ap.add_argument("--columns", required=True, help="comma-separated required output columns, in order")
    ap.add_argument("--allowed", action="append", default=[],
                    help="column=value1,value2 (repeatable) for enum columns")
    ap.add_argument("--transcript", type=Path, default=None)
    ap.add_argument("--out", type=Path, default=Path("submission"))
    args = ap.parse_args()

    repo = args.repo.resolve()
    columns = [c.strip() for c in args.columns.split(",") if c.strip()]
    results: list[bool] = []

    output = repo / "output.csv"
    report(output.exists(), "output.csv exists at repo root", str(output), results)
    if not output.exists():
        return finish(results)

    header, out_rows = read_rows(output)
    report(header == columns, "header matches required columns exactly",
           f"found {header}" if header != columns else f"{len(columns)} columns in order", results)

    in_header, in_rows = read_rows(args.input)
    key = args.key or in_header[0]
    in_keys = [r[key] for r in in_rows]
    out_keys = [r.get(key, "") for r in out_rows]
    missing = sorted(set(in_keys) - set(out_keys))
    extra = sorted(set(out_keys) - set(in_keys))
    dupes = sorted({k for k in out_keys if out_keys.count(k) > 1})
    report(not missing and not extra and not dupes and len(out_rows) == len(in_rows),
           f"one output row per input row ({len(out_rows)} out, {len(in_rows)} in)",
           f"missing={missing[:5]} extra={extra[:5]} duplicated={dupes[:5]}", results)
    report(out_keys == in_keys, "output rows in the same order as the input",
           "" if out_keys == in_keys else "order differs", results)

    empties = [(i + 1, c) for i, r in enumerate(out_rows) for c in columns if not (r.get(c) or "").strip()]
    report(not empties, "no empty required cells",
           f"first empties (row,col): {empties[:5]}" if empties else "", results)

    for spec in args.allowed:
        col, _, vals = spec.partition("=")
        allowed = {v.strip() for v in vals.split(",") if v.strip()}
        bad = sorted({r.get(col, "") for r in out_rows} - allowed)
        report(not bad, f"{col} uses only allowed values", f"bad values: {bad[:5]}" if bad else "", results)

    code_dir = next((repo / d for d in ("code", "src") if (repo / d).is_dir()), None)
    readme = repo / "README.md"
    report(code_dir is not None, "code folder present", str(code_dir) if code_dir else "no code/ or src/", results)
    report(readme.exists(), "README.md present", "", results)

    leaks = []
    for p in files_for_zip(repo):
        if p.suffix in {".py", ".md", ".txt", ".json", ".yaml", ".yml", ".toml", ".env", ".sh", ".ps1"}:
            text = p.read_text(encoding="utf-8", errors="ignore")
            for pat in SECRET_PATTERNS:
                if pat.search(text):
                    leaks.append(str(p.relative_to(repo)))
                    break
    report(not leaks, "no secrets in code or docs", f"possible secrets in: {leaks[:5]}" if leaks else "", results)

    if args.transcript is not None:
        t = args.transcript if args.transcript.is_absolute() else repo / args.transcript
        report(t.exists() and t.stat().st_size > 0, "transcript present and non-empty", str(t), results)
        transcript_path = t
    else:
        transcript_path = None

    if not all(results):
        return finish(results)

    out = args.out if args.out.is_absolute() else repo / args.out
    out.mkdir(parents=True, exist_ok=True)
    shutil.copy2(output, out / "output.csv")
    shutil.copy2(readme, out / "README.md")
    if transcript_path:
        shutil.copy2(transcript_path, out / transcript_path.name)
    usage = repo / "evaluation" / "usage_report.md"
    if usage.exists():
        (out / "evaluation").mkdir(exist_ok=True)
        shutil.copy2(usage, out / "evaluation" / "usage_report.md")
    zip_path = out / "code.zip"
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
        for p in files_for_zip(repo):
            if out in p.parents:
                continue
            zf.write(p, p.relative_to(repo).as_posix())
    print(f"\nBuilt {out}")
    for p in sorted(out.rglob("*")):
        if p.is_file():
            print(f"  {p.relative_to(out)}  ({p.stat().st_size} bytes)")
    return finish(results)


def finish(results: list[bool]) -> int:
    ok = all(results) and bool(results)
    print("\nREADY TO SUBMIT" if ok else "\nNOT READY - fix the FAIL lines above, then rerun")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
