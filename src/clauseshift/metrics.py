"""Item-level and pair-level metrics with a pair-level bootstrap."""

from __future__ import annotations

import collections

import numpy as np

from .generator import LABELS


def macro_f1(gold: list[str], pred: list[str]) -> float:
    f1s = []
    for lab in LABELS:
        tp = sum(g == lab and p == lab for g, p in zip(gold, pred))
        fp = sum(g != lab and p == lab for g, p in zip(gold, pred))
        fn = sum(g == lab and p != lab for g, p in zip(gold, pred))
        f1s.append(0.0 if tp == 0 else 2 * tp / (2 * tp + fp + fn))
    return float(np.mean(f1s))


def group_pairs(items: list[dict], preds: dict[str, str]) -> list[dict]:
    by_pair = collections.defaultdict(dict)
    for it in items:
        by_pair[it["pair_id"]][it["side"]] = it
    pairs = []
    for pid, sides in by_pair.items():
        a, b = sides["A"], sides["B"]
        pa, pb = preds[a["id"]], preds[b["id"]]
        pairs.append({
            "pair_id": pid, "operator": a["operator"], "operator_class": a["operator_class"], "family": a["family"],
            "gold": (a["label"], b["label"]), "pred": (pa, pb),
            "reserved": a["uses_reserved_template"] or b["uses_reserved_template"],
        })
    return pairs


def pair_metrics(pairs: list[dict]) -> dict[str, float]:
    """All metrics computed from a list of pairs (so the bootstrap can resample pairs)."""
    gold = [g for p in pairs for g in p["gold"]]
    pred = [x for p in pairs for x in p["pred"]]
    both = [p["pred"][0] == p["gold"][0] and p["pred"][1] == p["gold"][1] for p in pairs]
    flip = [p for p in pairs if p["operator_class"] == "flip"]
    inv = [p for p in pairs if p["operator_class"] != "flip"]
    m = {
        "accuracy": float(np.mean([g == x for g, x in zip(gold, pred)])),
        "macro_f1": macro_f1(gold, pred),
        "pair_accuracy": float(np.mean(both)),
    }
    if flip:
        m["flip_item_accuracy"] = float(np.mean([x == g for p in flip for x, g in zip(p["pred"], p["gold"])]))
        m["flip_sensitivity"] = float(np.mean([p["pred"][0] != p["pred"][1] for p in flip]))
        m["flip_accuracy"] = float(np.mean([p["pred"] == p["gold"] for p in flip]))
    if inv:
        m["invariance"] = float(np.mean([p["pred"][0] == p["pred"][1] for p in inv]))
        m["invariant_pair_accuracy"] = float(np.mean([p["pred"] == p["gold"] for p in inv]))
    return m


def bootstrap(pairs: list[dict], n: int = 1000, seed: int = 0, keys: list[str] | None = None) -> dict:
    """Percentile 95% intervals, resampling pairs with replacement."""
    rng = np.random.default_rng(seed)
    point = pair_metrics(pairs)
    keys = keys or list(point)
    samples = collections.defaultdict(list)
    idx = np.arange(len(pairs))
    for _ in range(n):
        res = pair_metrics([pairs[i] for i in rng.choice(idx, len(idx))])
        for k in keys:
            if k in res:
                samples[k].append(res[k])
    return {k: {"point": point[k], "lo": float(np.percentile(samples[k], 2.5)),
                "hi": float(np.percentile(samples[k], 97.5))} for k in keys if k in point}


def paired_difference(pairs_a: list[dict], pairs_b: list[dict], key: str, n: int = 1000, seed: int = 0) -> dict:
    """Bootstrap the difference A - B on the same resampled pairs (pairs aligned by pair_id)."""
    order = {p["pair_id"]: i for i, p in enumerate(pairs_a)}
    pairs_b = sorted(pairs_b, key=lambda p: order[p["pair_id"]])
    rng = np.random.default_rng(seed)
    idx = np.arange(len(pairs_a))
    diffs = []
    for _ in range(n):
        s = rng.choice(idx, len(idx))
        diffs.append(pair_metrics([pairs_a[i] for i in s])[key] - pair_metrics([pairs_b[i] for i in s])[key])
    point = pair_metrics(pairs_a)[key] - pair_metrics(pairs_b)[key]
    return {"diff": point, "lo": float(np.percentile(diffs, 2.5)), "hi": float(np.percentile(diffs, 97.5))}


def breakdown(pairs: list[dict], field: str) -> dict[str, dict]:
    groups = collections.defaultdict(list)
    for p in pairs:
        groups[str(p[field])].append(p)
    return {k: {**pair_metrics(v), "n_pairs": len(v)} for k, v in sorted(groups.items())}
