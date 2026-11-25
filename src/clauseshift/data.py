"""Build the dataset, run integrity checks and write data/ with a manifest of content hashes."""

from __future__ import annotations

import collections
import json
import re
from pathlib import Path

from .domains import SPLIT_FAMILIES
from .generator import LABELS, content_hash, generate_family


def normalize(text: str) -> str:
    return re.sub(r"\s+", " ", re.sub(r"[^a-z0-9 ]", " ", text.lower())).strip()


def build(config: dict) -> dict[str, list[dict]]:
    splits = {}
    for split, families in SPLIT_FAMILIES.items():
        items = []
        for fam in families:
            items += generate_family(fam, config["pairs_per_operator"][split], config["seed"],
                                     allow_reserved=(split == "test"))
        for it in items:
            it["split"] = split
        splits[split] = items
    return splits


def check(splits: dict[str, list[dict]]) -> dict:
    """Integrity and leakage checks. Raises AssertionError on a violation; returns statistics."""
    stats = {}
    all_ids = [it["id"] for items in splits.values() for it in items]
    assert len(all_ids) == len(set(all_ids)), "duplicate item ids"
    # 1. both sides of a pair in the same split, exactly two sides, identical hypothesis
    for split, items in splits.items():
        by_pair = collections.defaultdict(list)
        for it in items:
            by_pair[it["pair_id"]].append(it)
        for pid, pair in by_pair.items():
            assert sorted(x["side"] for x in pair) == ["A", "B"], pid
            assert pair[0]["hypothesis"] == pair[1]["hypothesis"], pid
            assert pair[0]["premise"] != pair[1]["premise"], f"identical premises in {pid}"
            if pair[0]["operator_class"] == "flip":
                assert pair[0]["label"] != pair[1]["label"], f"flip operator without flip: {pid}"
            else:
                assert pair[0]["label"] == pair[1]["label"], f"invariant operator flipped: {pid}"
    # 2. no family in two splits
    fams = {s: {it["family"] for it in items} for s, items in splits.items()}
    assert not (fams["train"] & fams["test"]) and not (fams["train"] & fams["dev"]) and not (fams["dev"] & fams["test"])
    # 3. exact duplicates of (premise, hypothesis) across splits; within-split duplicates counted
    keys = {s: collections.Counter((normalize(i["premise"]), normalize(i["hypothesis"])) for i in items)
            for s, items in splits.items()}
    assert not (set(keys["train"]) & set(keys["test"])), "train/test duplicate"
    assert not (set(keys["train"]) & set(keys["dev"])), "train/dev duplicate"
    stats["within_split_duplicate_items"] = {s: sum(c - 1 for c in k.values() if c > 1) for s, k in keys.items()}
    # 4. conflicting labels for identical inputs (would make the task ill-posed)
    for s, items in splits.items():
        seen = {}
        for it in items:
            k = (normalize(it["premise"]), normalize(it["hypothesis"]))
            assert seen.setdefault(k, it["label"]) == it["label"], f"conflicting labels for identical input in {s}"
    # 5. lexical leakage: share of test hypotheses' entity names that also occur in train
    train_text = " ".join(i["hypothesis"] for i in splits["train"])
    test_names = {i["hypothesis"].split(" is ")[0] for i in splits["test"]}
    stats["test_entity_names_seen_in_train"] = sum(n in train_text for n in test_names)
    # 6. reserved templates absent from train/dev
    for s in ("train", "dev"):
        assert not any(i["uses_reserved_template"] for i in splits[s]), f"reserved template in {s}"
    stats["test_items_with_reserved_template"] = sum(i["uses_reserved_template"] for i in splits["test"])
    for s, items in splits.items():
        stats[s] = {
            "items": len(items),
            "pairs": len(items) // 2,
            "labels": dict(collections.Counter(i["label"] for i in items)),
            "operators": dict(collections.Counter(i["operator"] for i in items[::2])),
            "families": sorted(fams[s]),
        }
    for lab in LABELS:
        assert all(lab in stats[s]["labels"] for s in splits), f"label {lab} missing in a split"
    return stats


def write(splits: dict[str, list[dict]], stats: dict, config: dict, out_dir: Path) -> dict:
    out_dir.mkdir(parents=True, exist_ok=True)
    manifest = {"config": config, "stats": stats, "files": {}}
    for split, items in splits.items():
        path = out_dir / f"{split}.jsonl"
        with open(path, "w", encoding="utf-8", newline="\n") as f:
            for it in items:
                f.write(json.dumps(it, ensure_ascii=False, default=str) + "\n")
        manifest["files"][split] = {"path": path.name, "sha256_content": content_hash(items), "items": len(items)}
    (out_dir / "manifest.json").write_text(json.dumps(manifest, indent=2, ensure_ascii=False), encoding="utf-8")
    return manifest


def load(split: str, data_dir: Path = Path("data")) -> list[dict]:
    with open(data_dir / f"{split}.jsonl", encoding="utf-8") as f:
        return [json.loads(line) for line in f]
