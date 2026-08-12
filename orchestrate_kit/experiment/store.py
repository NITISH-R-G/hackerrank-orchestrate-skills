"""JSON-backed experiment store. Same discipline as Engineering Memory:
no database, no service -- commit it, diff it, review it."""

from __future__ import annotations

import json
from pathlib import Path

from .model import Experiment

_FILE = ".orchestrate_experiments.json"


class ExperimentStore:
    def __init__(self, repo_root: Path) -> None:
        self.path = Path(repo_root) / _FILE
        self.experiments: dict[str, Experiment] = {}
        if self.path.exists():
            try:
                raw = json.loads(self.path.read_text(encoding="utf-8"))
            except (json.JSONDecodeError, OSError):
                raw = {"experiments": []}
            for item in raw.get("experiments", []):
                exp = Experiment.from_dict(item)
                self.experiments[exp.id] = exp

    def next_id(self) -> str:
        nums = [int(k.split("-")[1]) for k in self.experiments if k.startswith("EXP-")
               and k.split("-")[1].isdigit()]
        return f"EXP-{(max(nums) + 1) if nums else 1:04d}"

    def add(self, exp: Experiment) -> None:
        self.experiments[exp.id] = exp

    def get(self, exp_id: str) -> Experiment | None:
        return self.experiments.get(exp_id)

    def all(self) -> list[Experiment]:
        return sorted(self.experiments.values(), key=lambda e: e.id)

    def save(self) -> None:
        self.path.write_text(
            json.dumps({"version": 1,
                       "experiments": [e.to_dict() for e in self.all()]},
                      indent=2, ensure_ascii=False),
            encoding="utf-8")
