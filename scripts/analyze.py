"""Aggregate saved predictions into tables, hypothesis tests and figures.

Writes results/summary.json, results/RESULTS.md (generated; do not edit by hand) and results/figures/*.png.
"""

import collections
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

import matplotlib  # noqa: E402

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402

from clauseshift.data import load  # noqa: E402
from clauseshift.generator import OPERATORS  # noqa: E402
from clauseshift.metrics import bootstrap, breakdown, group_pairs, pair_metrics, paired_difference  # noqa: E402
from clauseshift.predictions import ROOT, load_predictions  # noqa: E402

N_BOOT = 1000
KEYS = ["accuracy", "macro_f1", "pair_accuracy", "flip_item_accuracy", "flip_sensitivity", "flip_accuracy",
        "invariance", "invariant_pair_accuracy"]
FIG = Path("results/figures")
FIG.mkdir(parents=True, exist_ok=True)

data = {s: load(s) for s in ("dev", "test")}


def systems() -> list[str]:
    out = []
    for d in sorted(ROOT.iterdir()):
        meta = json.loads((d / "meta.json").read_text()) if (d / "meta.json").exists() else {}
        if (d / "test.jsonl").exists() and not meta.get("smoke_test"):
            out.append(d.name)
    return out


def pairs_for(system: str, split: str) -> list[dict]:
    preds = {k: v["pred"] for k, v in load_predictions(system, split).items()}
    return group_pairs(data[split], preds)


def fmt(b: dict) -> str:
    return f"{b['point']:.3f} [{b['lo']:.3f}, {b['hi']:.3f}]"


summary = {"systems": {}, "hypotheses": {}}
all_systems = systems()
single = [s for s in all_systems if not s.startswith("ft_")]
ft = [s for s in all_systems if s.startswith("ft_")]
ft_groups = collections.defaultdict(list)
for s in ft:
    ft_groups[re.sub(r"_s\d+$", "", s)].append(s)

# ---- per-system metrics ---------------------------------------------------------------------
for s in all_systems:
    tp, dp = pairs_for(s, "test"), pairs_for(s, "dev")
    summary["systems"][s] = {
        "test": bootstrap(tp, N_BOOT, keys=KEYS),
        "dev": pair_metrics(dp),
        "test_by_operator": breakdown(tp, "operator"),
        "test_by_family": breakdown(tp, "family"),
        "test_by_reserved_template": breakdown(tp, "reserved"),
    }

# Seed-pooled view for fine-tuned groups: mean ± SD over seeds of the point estimates.
group_stats = {}
for g, members in ft_groups.items():
    vals = {k: [summary["systems"][m]["test"][k]["point"] for m in members] for k in KEYS}
    group_stats[g] = {k: (float(np.mean(v)), float(np.std(v, ddof=1)) if len(v) > 1 else 0.0) for k, v in vals.items()}
    group_stats[g]["n_seeds"] = len(members)
    group_stats[g]["dev_accuracy"] = float(np.mean([summary["systems"][m]["dev"]["accuracy"] for m in members]))
summary["ft_groups"] = group_stats

# ---- preregistered hypotheses --------------------------------------------------------------
zs = [s for s in single if s.startswith("zeroshot_")]
h1 = {}
for s in zs:
    m = summary["systems"][s]["test"]
    h1[s] = {"item_accuracy_flip": m["flip_item_accuracy"]["point"], "flip_pair_accuracy": m["flip_accuracy"]["point"],
             "gap": m["flip_item_accuracy"]["point"] - m["flip_accuracy"]["point"]}
summary["hypotheses"]["H1_item_vs_pair_gap"] = h1

h2 = {}
for s in zs + list(ft_groups):
    members = ft_groups.get(s, [s])
    acc = collections.defaultdict(list)
    for m in members:
        for op, v in summary["systems"][m]["test_by_operator"].items():
            if "flip_accuracy" in v:
                acc[op].append(v["flip_accuracy"])
    h2[s] = {op: float(np.mean(v)) for op, v in acc.items()}
summary["hypotheses"]["H2_flip_accuracy_by_operator"] = h2


def pooled_pairs(members: list[str]) -> list[dict]:
    """Concatenate pairs from several seeds, keeping pair ids distinct per seed."""
    out = []
    for m in members:
        for p in pairs_for(m, "test"):
            out.append({**p, "pair_id": f"{p['pair_id']}#{m[-2:]}"})
    return out


h3 = {}
for model_prefix in sorted({re.sub(r"_(paired|unpaired|full|op_holdout).*$", "", g) for g in ft_groups}):
    gp, gu = f"{model_prefix}_paired", f"{model_prefix}_unpaired"
    if gp in ft_groups and gu in ft_groups and len(ft_groups[gp]) == len(ft_groups[gu]):
        pa = pooled_pairs(sorted(ft_groups[gp]))
        pu = pooled_pairs(sorted(ft_groups[gu]))
        h3[model_prefix] = {k: paired_difference(pa, pu, k, N_BOOT) for k in
                            ("flip_accuracy", "pair_accuracy", "accuracy", "invariance")}
        h3[model_prefix]["seed_means"] = {"paired": group_stats[gp]["flip_accuracy"],
                                          "unpaired": group_stats[gu]["flip_accuracy"]}
summary["hypotheses"]["H3_paired_minus_unpaired"] = h3

h4 = {}
for g, members in list(ft_groups.items()):
    dev_acc = np.mean([summary["systems"][m]["dev"]["accuracy"] for m in members])
    test_acc = np.mean([summary["systems"][m]["test"]["accuracy"]["point"] for m in members])
    res = [summary["systems"][m]["test_by_reserved_template"] for m in members]
    h4[g] = {"dev_accuracy": float(dev_acc), "test_accuracy": float(test_acc),
             "test_acc_reserved": float(np.mean([r.get("True", {}).get("accuracy", np.nan) for r in res])),
             "test_acc_not_reserved": float(np.mean([r.get("False", {}).get("accuracy", np.nan) for r in res]))}
summary["hypotheses"]["H4_shift"] = h4

hyp_only = "tfidf_lr_hypothesis_only"
if hyp_only in summary["systems"]:
    summary["hypotheses"]["H5_hypothesis_only_flip_pair_accuracy"] = summary["systems"][hyp_only]["test"]["flip_accuracy"]

Path("results/summary.json").write_text(json.dumps(summary, indent=1), encoding="utf-8")

# ---- markdown -------------------------------------------------------------------------------
L = ["# Results (generated by scripts/analyze.py)", "",
     f"Test split: {len(data['test'])} items, {len(data['test']) // 2} minimal pairs, families "
     f"{sorted({i['family'] for i in data['test']})}. 95% intervals: percentile bootstrap over pairs, {N_BOOT} resamples.",
     "", "## Main table (test)", "",
     "| System | Accuracy | Macro-F1 | Pair accuracy | Flip accuracy | Flip sensitivity | Invariance | Invariant-pair accuracy |",
     "|---|---|---|---|---|---|---|---|"]
for s in single:
    m = summary["systems"][s]["test"]
    L.append(f"| {s} | {fmt(m['accuracy'])} | {fmt(m['macro_f1'])} | {fmt(m['pair_accuracy'])} | "
             f"{fmt(m['flip_accuracy'])} | {fmt(m['flip_sensitivity'])} | {fmt(m['invariance'])} | "
             f"{fmt(m['invariant_pair_accuracy'])} |")
if ft_groups:
    L += ["", "## Fine-tuned models (test, mean ± SD over seeds)", "",
          "| Group | Seeds | Dev acc. | Accuracy | Macro-F1 | Pair accuracy | Flip accuracy | Invariance | Invariant-pair acc. |",
          "|---|---|---|---|---|---|---|---|---|"]
    for g, st in sorted(group_stats.items()):
        c = lambda k: f"{st[k][0]:.3f} ± {st[k][1]:.3f}"  # noqa: E731
        L.append(f"| {g} | {st['n_seeds']} | {st['dev_accuracy']:.3f} | {c('accuracy')} | {c('macro_f1')} | "
                 f"{c('pair_accuracy')} | {c('flip_accuracy')} | {c('invariance')} | {c('invariant_pair_accuracy')} |")
L += ["", "## Flip accuracy by operator (test)", "",
      "| System | " + " | ".join(o for o in OPERATORS if o in h2[next(iter(h2))]) + " |",
      "|---|" + "---|" * len([o for o in OPERATORS if o in h2[next(iter(h2))]])]
for s, d in h2.items():
    L.append(f"| {s} | " + " | ".join(f"{d.get(o, float('nan')):.2f}" for o in OPERATORS if o in d) + " |")
L += ["", "## Invariance by operator (test; near-miss and invariant operators)", "",
      "| System | " + " | ".join(o for o in OPERATORS[8:]) + " |", "|---|" + "---|" * len(OPERATORS[8:])]
for s in single + sorted(ft_groups):
    members = ft_groups.get(s, [s])
    vals = [np.mean([summary["systems"][m]["test_by_operator"][o]["invariance"] for m in members]) for o in OPERATORS[8:]]
    L.append(f"| {s} | " + " | ".join(f"{v:.2f}" for v in vals) + " |")
if h3:
    L += ["", "## H3: paired minus unpaired training (seed-pooled test pairs, paired bootstrap)", ""]
    for mp, d in h3.items():
        for k in ("flip_accuracy", "pair_accuracy", "accuracy", "invariance"):
            L.append(f"- {mp} {k}: {d[k]['diff']:+.3f} [{d[k]['lo']:+.3f}, {d[k]['hi']:+.3f}]")
if h4:
    L += ["", "## H4: shift (fine-tuned, mean over seeds)", "",
          "| Group | Dev acc. (vehicles) | Test acc. | Test, reserved templates | Test, seen templates |", "|---|---|---|---|---|"]
    for g, d in sorted(h4.items()):
        L.append(f"| {g} | {d['dev_accuracy']:.3f} | {d['test_accuracy']:.3f} | {d['test_acc_reserved']:.3f} | "
                 f"{d['test_acc_not_reserved']:.3f} |")
Path("results/RESULTS.md").write_text("\n".join(L) + "\n", encoding="utf-8")

# ---- figures --------------------------------------------------------------------------------
rows = [s for s in single if s != "majority"] + sorted(ft_groups)
flip_ops = [o for o in OPERATORS if o in h2[next(iter(h2))]]
if rows:
    mat = np.array([[h2.get(r, {}).get(o, np.nan) if r in h2 else
                     summary["systems"][r]["test_by_operator"][o].get("flip_accuracy", np.nan) for o in flip_ops]
                    for r in rows])
    fig, ax = plt.subplots(figsize=(1.1 * len(flip_ops) + 3, 0.45 * len(rows) + 1.5))
    im = ax.imshow(mat, vmin=0, vmax=1, cmap="viridis", aspect="auto")
    ax.set_xticks(range(len(flip_ops)), flip_ops, rotation=35, ha="right", fontsize=8)
    ax.set_yticks(range(len(rows)), rows, fontsize=8)
    for i in range(mat.shape[0]):
        for j in range(mat.shape[1]):
            ax.text(j, i, f"{mat[i, j]:.2f}", ha="center", va="center", fontsize=7,
                    color="white" if mat[i, j] < 0.6 else "black")
    fig.colorbar(im, ax=ax, label="flip-pair accuracy (both sides correct)")
    ax.set_title("ClauseShift test: flip-pair accuracy by edit operator", fontsize=10)
    fig.tight_layout()
    fig.savefig(FIG / "flip_accuracy_by_operator.png", dpi=150)

    fig, ax = plt.subplots(figsize=(7.5, 0.4 * len(rows) + 1.2))
    y = np.arange(len(rows))
    item = [group_stats[r]["flip_item_accuracy"][0] if r in group_stats else
            summary["systems"][r]["test"]["flip_item_accuracy"]["point"] for r in rows]
    pair = [group_stats[r]["flip_accuracy"][0] if r in group_stats else
            summary["systems"][r]["test"]["flip_accuracy"]["point"] for r in rows]
    ax.barh(y + 0.2, item, 0.4, label="item accuracy (flip pairs)", color="#9ab")
    ax.barh(y - 0.2, pair, 0.4, label="pair accuracy (both sides correct)", color="#1f4e79")
    ax.set_yticks(y, rows, fontsize=8)
    ax.set_xlim(0, 1)
    ax.legend(fontsize=8, loc="lower right")
    ax.set_title("Item vs. pair accuracy on flip pairs (test)", fontsize=10)
    fig.tight_layout()
    fig.savefig(FIG / "item_vs_pair_accuracy.png", dpi=150)
print("\n".join(L))
