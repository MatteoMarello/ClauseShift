"""Uniform storage of per-item predictions: results/predictions/<system>/<split>.jsonl."""

from __future__ import annotations

import json
from pathlib import Path

from .generator import LABELS

ROOT = Path("results/predictions")


def save_predictions(system: str, split: str, items: list[dict], probs: list[dict], meta: dict | None = None,
                     root: Path | None = None) -> None:
    out = (root or ROOT) / system
    out.mkdir(parents=True, exist_ok=True)
    with open(out / f"{split}.jsonl", "w", encoding="utf-8", newline="\n") as f:
        for it, p in zip(items, probs):
            p = {lab: float(p.get(lab, 0.0)) for lab in LABELS}
            f.write(json.dumps({"id": it["id"], "pred": max(p, key=p.get), "probs": p}) + "\n")
    if meta is not None:
        (out / "meta.json").write_text(json.dumps(meta, indent=2), encoding="utf-8")


def load_predictions(system: str, split: str) -> dict[str, dict]:
    with open(ROOT / system / f"{split}.jsonl", encoding="utf-8") as f:
        return {r["id"]: r for r in map(json.loads, f)}
