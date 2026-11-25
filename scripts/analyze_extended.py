"""Extended analysis: preregistered decision rules, format comparison, seed-aware H3 inference, evidence
sensitivity, failure decomposition, and publication figures.

Reads only saved predictions (results/predictions/) and data/. Writes results/EXTENDED_ANALYSIS.md,
results/extended_summary.json and results/figures/fig*.png. Generated file; do not edit the outputs by hand.

Statistics. Every interval is a 95% percentile bootstrap over minimal pairs (B = 2000). All systems evaluated on
the same split share one matrix of resampling weights, so every difference between two systems is a paired
bootstrap. For fine-tuned groups (several seeds) the statistic is the mean over seeds, and each resample keeps all
seeds of a pair together (cluster bootstrap over test pairs); this treats seeds as fixed and pairs as the random
unit. The preregistered H3 implementation (seeds pooled as independent pairs) remains in scripts/analyze.py.
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
from clauseshift.evidence import expected_label_after_removal, removal_is_well_posed, removal_type  # noqa: E402
from clauseshift.generator import LABELS, OPERATORS, OPERATORS_FLIP  # noqa: E402
from clauseshift.predictions import ROOT, load_predictions  # noqa: E402

B = 2000
FIG = Path("results/figures")
FIG.mkdir(parents=True, exist_ok=True)
LAB = {l: i for i, l in enumerate(LABELS)}
ZS_MODELS = ["nli-deberta-v3-xsmall", "nli-deberta-v3-base", "DeBERTa-v3-base-mnli-fever-anli", "roberta-large-mnli"]
SHORT = {"nli-deberta-v3-xsmall": "DeBERTa-v3-xsmall (NLI)", "nli-deberta-v3-base": "DeBERTa-v3-base (NLI)",
         "DeBERTa-v3-base-mnli-fever-anli": "DeBERTa-v3-base (MNLI-FEVER-ANLI)",
         "roberta-large-mnli": "RoBERTa-large (MNLI)"}

# palette (dataviz reference instance, light mode)
BLUE, ORANGE, AQUA, GRAY, INK, INK2 = "#257de0", "#f47230", "#00b894", "#9c9c9c", "#191919", "#666666"
plt.rcParams.update({"font.size": 8, "axes.edgecolor": "#c8c8c8", "axes.labelcolor": INK, "xtick.color": INK2,
                     "ytick.color": INK2, "axes.spines.top": False, "axes.spines.right": False,
                     "axes.grid": True, "grid.color": "#ececec", "grid.linewidth": 0.6, "axes.axisbelow": True,
                     "font.family": "DejaVu Sans", "savefig.dpi": 200, "savefig.bbox": "tight"})

data = {s: load(s) for s in ("dev", "test")}
by_id = {i["id"]: i for i in data["test"]}


# ---------------------------------------------------------------------------------------------------------------
# Vectorised pair tables
# ---------------------------------------------------------------------------------------------------------------
class PairTable:
    """One row per minimal pair (sorted by pair_id) with integer-coded gold labels and predictions."""

    def __init__(self, split: str, preds: dict[str, str] | None = None):
        sides = collections.defaultdict(dict)
        for it in data[split]:
            sides[it["pair_id"]][it["side"]] = it
        self.ids = sorted(sides)
        a = [sides[p]["A"] for p in self.ids]
        b = [sides[p]["B"] for p in self.ids]
        self.op = np.array([x["operator"] for x in a])
        self.cls = np.array([x["operator_class"] for x in a])
        self.reserved = np.array([x["uses_reserved_template"] or y["uses_reserved_template"] for x, y in zip(a, b)])
        self.ga = np.array([LAB[x["label"]] for x in a])
        self.gb = np.array([LAB[x["label"]] for x in b])
        self.a_ids, self.b_ids = [x["id"] for x in a], [x["id"] for x in b]
        if preds is not None:
            self.pa = np.array([LAB[preds[i]] for i in self.a_ids])
            self.pb = np.array([LAB[preds[i]] for i in self.b_ids])

    def indicators(self) -> dict[str, np.ndarray]:
        ca, cb = self.pa == self.ga, self.pb == self.gb
        flip, inv = self.cls == "flip", self.cls != "flip"
        d = {"n": np.ones(len(self.ids)), "correct": ca.astype(float) + cb, "both": (ca & cb).astype(float),
             "flip": flip.astype(float), "flip_both": (flip & ca & cb).astype(float),
             "flip_correct": flip * (ca.astype(float) + cb), "flip_changed": (flip & (self.pa != self.pb)).astype(float),
             "inv": inv.astype(float), "inv_same": (inv & (self.pa == self.pb)).astype(float),
             "inv_both": (inv & ca & cb).astype(float)}
        for l in range(3):
            d[f"tp{l}"] = ((self.ga == l) & (self.pa == l)).astype(float) + ((self.gb == l) & (self.pb == l))
            d[f"fp{l}"] = ((self.ga != l) & (self.pa == l)).astype(float) + ((self.gb != l) & (self.pb == l))
            d[f"fn{l}"] = ((self.ga == l) & (self.pa != l)).astype(float) + ((self.gb == l) & (self.pb != l))
            d[f"pred{l}"] = (self.pa == l).astype(float) + (self.pb == l)
        return d


def weights(n: int, seed: int) -> np.ndarray:
    rng = np.random.default_rng(seed)
    W = np.empty((B + 1, n))
    W[0] = 1.0                                           # row 0 = the observed sample (point estimate)
    for r in range(1, B + 1):
        W[r] = np.bincount(rng.integers(0, n, n), minlength=n)
    return W


def metrics(ind: dict, W: np.ndarray, mask: np.ndarray | None = None) -> dict[str, np.ndarray]:
    """Metric vectors of length B+1 (index 0 = point estimate) for one system, optionally on a subset of pairs."""
    m = np.ones(W.shape[1]) if mask is None else mask.astype(float)
    S = lambda k: W @ (ind[k] * m)  # noqa: E731
    with np.errstate(invalid="ignore", divide="ignore"):
        n = S("n")
        out = {"accuracy": S("correct") / (2 * n), "pair_accuracy": S("both") / n,
               "flip_item_accuracy": S("flip_correct") / (2 * S("flip")), "flip_accuracy": S("flip_both") / S("flip"),
               "flip_sensitivity": S("flip_changed") / S("flip"), "invariance": S("inv_same") / S("inv"),
               "invariant_pair_accuracy": S("inv_both") / S("inv")}
        f1 = []
        for l in range(3):
            tp, fp, fn = S(f"tp{l}"), S(f"fp{l}"), S(f"fn{l}")
            f1.append(np.where(tp > 0, 2 * tp / (2 * tp + fp + fn), 0.0))
            out[f"pred_share_{LABELS[l]}"] = S(f"pred{l}") / (2 * n)
        out["macro_f1"] = np.mean(f1, axis=0)
    return out


def summarize(v: np.ndarray) -> dict:
    return {"point": float(v[0]), "lo": float(np.nanpercentile(v[1:], 2.5)), "hi": float(np.nanpercentile(v[1:], 97.5))}


def fmt(s: dict, signed: bool = False) -> str:
    f = "{:+.3f}" if signed else "{:.3f}"
    return f"{f.format(s['point'])} [{f.format(s['lo'])}, {f.format(s['hi'])}]"


# ---------------------------------------------------------------------------------------------------------------
# Systems
# ---------------------------------------------------------------------------------------------------------------
def available() -> list[str]:
    out = []
    for d in sorted(ROOT.iterdir()):
        meta = json.loads((d / "meta.json").read_text()) if (d / "meta.json").exists() else {}
        if (d / "test.jsonl").exists() and (d / "dev.jsonl").exists() and not meta.get("smoke_test"):
            out.append(d.name)
    return out


SYSTEMS = available()
GROUPS = collections.defaultdict(list)          # fine-tuned: group -> seeds
for s in SYSTEMS:
    if s.startswith("ft_"):
        GROUPS[re.sub(r"_s\d+$", "", s)].append(s)
for g in GROUPS:
    GROUPS[g].sort()
def _order(u: str) -> tuple:
    if u in ("majority", "tfidf_lr_hypothesis_only", "tfidf_lr_document_hypothesis"):
        return (0, ["majority", "tfidf_lr_hypothesis_only", "tfidf_lr_document_hypothesis"].index(u), 0)
    if u.startswith("zeroshot_"):
        m = u[len("zeroshot_"):].replace("_factsinpremise", "")
        return (1, ZS_MODELS.index(m) if m in ZS_MODELS else 99, u.endswith("_factsinpremise"))
    cond = ["paired", "unpaired", "op_holdout", "full"]
    c = next((i for i, x in enumerate(cond) if u.endswith("_" + x)), 9)
    return (2, "nli-deberta" not in u, c)


UNITS = sorted([s for s in SYSTEMS if not s.startswith("ft_")] + list(GROUPS), key=_order)   # evaluation units

tables = {split: {} for split in ("dev", "test")}
for split in ("dev", "test"):
    for s in SYSTEMS:
        preds = {k: v["pred"] for k, v in load_predictions(s, split).items()}
        tables[split][s] = PairTable(split, preds)
base = {split: PairTable(split) for split in ("dev", "test")}
W = {"test": weights(len(base["test"].ids), 0), "dev": weights(len(base["dev"].ids), 1)}


def unit_metrics(unit: str, split: str = "test", mask: np.ndarray | None = None) -> dict[str, np.ndarray]:
    members = GROUPS.get(unit, [unit])
    per = [metrics(tables[split][m].indicators(), W[split], mask) for m in members]
    return {k: np.mean([p[k] for p in per], axis=0) for k in per[0]}


M = {u: unit_metrics(u) for u in UNITS}
OPM = {u: {op: unit_metrics(u, mask=base["test"].op == op) for op in OPERATORS} for u in UNITS}
summary = {"bootstrap": {"B": B, "unit": "minimal pair", "seed_groups": "mean over seeds, cluster bootstrap"},
           "units": {u: {"seeds": GROUPS.get(u, [u]), "test": {k: summarize(v) for k, v in M[u].items()}} for u in UNITS}}
L = ["# Extended analysis (generated by scripts/analyze_extended.py)", "",
     f"95% percentile bootstrap intervals over test minimal pairs (B = {B}), one shared resampling matrix, so all "
     "differences are paired. Fine-tuned groups: mean over seeds, cluster bootstrap (all seeds of a pair are "
     "resampled together). Sections marked *exploratory* were not preregistered.", ""]

zs_std = [f"zeroshot_{m}" for m in ZS_MODELS if f"zeroshot_{m}" in SYSTEMS]
zs_fip = [f"zeroshot_{m}_factsinpremise" for m in ZS_MODELS if f"zeroshot_{m}_factsinpremise" in SYSTEMS]

# ---------------------------------------------------------------------------------------------------------------
# Preregistered decision rules
# ---------------------------------------------------------------------------------------------------------------
L += ["## 1. Preregistered hypotheses: decision rules applied", ""]
# H1
L += ["### H1: flip-pair accuracy at least 10 points below item accuracy (off-the-shelf models)", "",
      "Gap = item accuracy on flip pairs − flip-pair accuracy. Decision: supported if the lower bound of the 95% "
      "interval of (gap − 0.10) is above 0.", "",
      "| System | Item acc. (flip pairs) | Flip-pair acc. | Gap | Verdict |", "|---|---|---|---|---|"]
h1 = {}
for s in zs_std:
    gap = M[s]["flip_item_accuracy"] - M[s]["flip_accuracy"]
    g = summarize(gap)
    h1[s] = {"gap": g, "supported": g["lo"] > 0.10}
    L.append(f"| {s} | {fmt(summarize(M[s]['flip_item_accuracy']))} | {fmt(summarize(M[s]['flip_accuracy']))} | "
             f"{fmt(g)} | {'supported' if g['lo'] > 0.10 else 'not supported'} |")
L += ["", "Note: the gap is largest for a model that ignores the edit (it cannot exceed item accuracy, and a "
      "constant prediction has flip-pair accuracy 0), so H1 is a necessary rather than a demanding condition; "
      "Section 5 decomposes the failures.", ""]
summary["H1"] = h1

# H2
H2_OPS = ["exception_add", "xref_redirect", "threshold_cross", "date_cross"]
L += ["### H2: exception and boundary edits below negation", "",
      "Difference = flip-pair accuracy(operator) − flip-pair accuracy(negation). Supported for an operator if the "
      "upper bound is below 0; H2 is supported for a system if it holds for all four operators.", "",
      "| System | " + " | ".join(H2_OPS) + " | All four |", "|---|" + "---|" * (len(H2_OPS) + 1)]
h2 = {}
for u in zs_std + sorted(GROUPS):
    row, ok = [], []
    for op in H2_OPS:
        d = summarize(OPM[u][op]["flip_accuracy"] - OPM[u]["negation"]["flip_accuracy"])
        ok.append(d["hi"] < 0)
        row.append(fmt(d, True))
    h2[u] = {"supported_all": all(ok), "per_operator": dict(zip(H2_OPS, ok))}
    L.append(f"| {u} | " + " | ".join(row) + f" | {'yes' if all(ok) else 'no'} |")
L.append("")
summary["H2"] = h2

# H3
L += ["### H3: paired vs. unpaired training (equal size)", ""]
h3 = {}
for prefix in sorted({re.sub(r"_(paired|unpaired|op_holdout|full)$", "", g) for g in GROUPS}):
    gp, gu = f"{prefix}_paired", f"{prefix}_unpaired"
    if gp not in GROUPS or gu not in GROUPS:
        continue
    seeds_p = [int(m[-1]) for m in GROUPS[gp]]
    seeds_u = [int(m[-1]) for m in GROUPS[gu]]
    common = sorted(set(seeds_p) & set(seeds_u))
    if not common:
        continue
    mp = {k: np.mean([metrics(tables["test"][f"{gp}_s{s}"].indicators(), W["test"])[k] for s in common], axis=0)
          for k in M[gp]}
    mu = {k: np.mean([metrics(tables["test"][f"{gu}_s{s}"].indicators(), W["test"])[k] for s in common], axis=0)
          for k in M[gu]}
    res = {"seeds": common}
    L += [f"**{prefix}** (seeds {common}; paired − unpaired, mean over seeds, cluster bootstrap)", "",
          "| Metric | Paired | Unpaired | Difference | Per-seed differences |", "|---|---|---|---|---|"]
    for k in ("flip_accuracy", "pair_accuracy", "accuracy", "macro_f1", "flip_sensitivity", "invariance"):
        d = summarize(mp[k] - mu[k])
        per_seed = [float(metrics(tables["test"][f"{gp}_s{s}"].indicators(), W["test"][:1])[k][0] -
                          metrics(tables["test"][f"{gu}_s{s}"].indicators(), W["test"][:1])[k][0]) for s in common]
        res[k] = {**d, "per_seed": per_seed}
        L.append(f"| {k} | {mp[k][0]:.3f} | {mu[k][0]:.3f} | {fmt(d, True)} | "
                 + ", ".join(f"{x:+.3f}" for x in per_seed) + " |")
    verdict = res["flip_accuracy"]["point"] > 0 and res["flip_accuracy"]["lo"] > 0
    res["supported_cluster"] = verdict
    res["n_seeds"] = len(common)
    reg = json.loads(Path("results/summary.json").read_text())["hypotheses"].get(
        "H3_paired_minus_unpaired", {}).get(prefix, {}).get("flip_accuracy")
    if reg:
        res["registered"] = reg
        res["supported_registered"] = reg["diff"] > 0 and reg["lo"] > 0
        L += ["", f"Registered analysis (`scripts/analyze.py`, seeds pooled as independent pairs): flip-accuracy "
              f"difference {reg['diff']:+.3f} [{reg['lo']:+.3f}, {reg['hi']:+.3f}] → "
              f"**{'supported' if res['supported_registered'] else 'not supported'}**. "
              f"Cluster bootstrap (above): **{'supported' if verdict else 'not supported'}**."
              + ("" if len(common) >= 3 else f" Only {len(common)} of 3 preregistered seeds available: provisional.")]
    fam = np.array([pid.split("-")[0] for pid in base["test"].ids])
    res["by_family"] = {}
    L += ["", "By test family (flip-pair accuracy, paired − unpaired): " + "; ".join(
        f"{f}: " + fmt(res["by_family"].setdefault(f, summarize(
            np.mean([metrics(tables["test"][f"{gp}_s{s}"].indicators(), W["test"], fam == f)["flip_accuracy"]
                     for s in common], axis=0) -
            np.mean([metrics(tables["test"][f"{gu}_s{s}"].indicators(), W["test"], fam == f)["flip_accuracy"]
                     for s in common], axis=0))), True)
        for f in sorted(set(fam)))]
    L += ["", "Per-operator flip-pair accuracy difference (paired − unpaired):", "",
          "| Operator | Paired | Unpaired | Difference |", "|---|---|---|---|"]
    res["by_operator"] = {}
    for op in OPERATORS_FLIP:
        mask = base["test"].op == op
        a = np.mean([metrics(tables["test"][f"{gp}_s{s}"].indicators(), W["test"], mask)["flip_accuracy"]
                     for s in common], axis=0)
        b = np.mean([metrics(tables["test"][f"{gu}_s{s}"].indicators(), W["test"], mask)["flip_accuracy"]
                     for s in common], axis=0)
        d = summarize(a - b)
        res["by_operator"][op] = d
        L.append(f"| {op} | {a[0]:.3f} | {b[0]:.3f} | {fmt(d, True)} |")
    L.append("")
    h3[prefix] = res
summary["H3"] = h3
if not h3:
    L += ["Not yet available (fine-tuning runs pending).", ""]

# H4
L += ["### H4: shift from dev (vehicles) to test families, and to reserved templates", "",
      "Dev and test are independent samples (independent bootstraps). Reserved vs. seen templates is computed "
      "within test, raw and stratified by operator (mean of per-operator differences weighted by pair count), "
      "because reserved templates are not spread evenly over operators.", ""]
h4 = {}
if GROUPS:
    L += ["| Group | Dev acc. | Test acc. | Dev − test | Seen − reserved (raw) | Seen − reserved (operator-stratified) |",
          "|---|---|---|---|---|---|"]
    for g in sorted(GROUPS):
        dev = unit_metrics(g, "dev")["accuracy"]
        test = M[g]["accuracy"]
        drop = summarize(dev - test)
        res, seen = base["test"].reserved, ~base["test"].reserved
        raw = summarize(unit_metrics(g, mask=seen)["accuracy"] - unit_metrics(g, mask=res)["accuracy"])
        strat, wsum = np.zeros(B + 1), 0
        for op in OPERATORS:
            mo = base["test"].op == op
            if (mo & res).sum() < 5 or (mo & seen).sum() < 5:
                continue
            w = mo.sum()
            strat = strat + w * (unit_metrics(g, mask=mo & seen)["accuracy"] - unit_metrics(g, mask=mo & res)["accuracy"])
            wsum += w
        strat = summarize(strat / wsum)
        h4[g] = {"dev_minus_test": drop, "seen_minus_reserved_raw": raw, "seen_minus_reserved_stratified": strat,
                 "supported": drop["lo"] > 0 and strat["lo"] > 0}
        L.append(f"| {g} | {dev[0]:.3f} | {test[0]:.3f} | {fmt(drop, True)} | {fmt(raw, True)} | {fmt(strat, True)} |")
    L += ["", f"Reserved-template pairs in test: {int(base['test'].reserved.sum())} of {len(base['test'].ids)}.", ""]
else:
    L += ["Not yet available (fine-tuning runs pending).", ""]
summary["H4"] = h4

# H5
if "tfidf_lr_hypothesis_only" in M:
    h5 = summarize(M["tfidf_lr_hypothesis_only"]["flip_accuracy"])
    summary["H5"] = {**h5, "supported": h5["point"] <= 0.05}
    L += ["### H5: hypothesis-only flip-pair accuracy ≤ 0.05", "",
          f"Flip-pair accuracy {fmt(h5)}: **{'supported' if h5['point'] <= 0.05 else 'not supported'}**. This holds "
          "by construction (both sides share the hypothesis and have different labels, so any deterministic "
          "hypothesis-only classifier scores 0); it is a sanity check, not an empirical finding. The informative "
          "shortcut measure is item accuracy: "
          f"{fmt(summarize(M['tfidf_lr_hypothesis_only']['accuracy']))} vs. majority "
          f"{fmt(summarize(M['majority']['accuracy']))}.", ""]

# ---------------------------------------------------------------------------------------------------------------
# Format comparison (exploratory)
# ---------------------------------------------------------------------------------------------------------------
gold_share = {l: float(np.mean([i["label"] == l for i in data["test"]])) for l in LABELS}
fmt_res = {}
if zs_fip:
    L += ["## 2. Input format: facts in the hypothesis vs. facts in the premise (exploratory)", "",
          "Standard: premise = document, hypothesis = case facts + claim. facts_in_premise: premise = document + "
          "\"Case:\" + facts, hypothesis = claim only. Same model weights, same items. Difference = "
          "facts_in_premise − standard (paired bootstrap).", "",
          "| Model | Metric | Standard | Facts in premise | Difference |", "|---|---|---|---|---|"]
    for m in ZS_MODELS:
        s, f = f"zeroshot_{m}", f"zeroshot_{m}_factsinpremise"
        if s not in M or f not in M:
            continue
        fmt_res[m] = {}
        for k in ("accuracy", "macro_f1", "pair_accuracy", "flip_accuracy", "invariance"):
            d = summarize(M[f][k] - M[s][k])
            fmt_res[m][k] = d
            L.append(f"| {SHORT[m]} | {k} | {M[s][k][0]:.3f} | {M[f][k][0]:.3f} | {fmt(d, True)} |")
    L += ["", "Predicted label distribution (test; gold: " +
          ", ".join(f"{l} {gold_share[l]:.3f}" for l in LABELS) + ")", "",
          "| Model | Format | entailed | contradicted | insufficient |", "|---|---|---|---|---|"]
    for m in ZS_MODELS:
        for s, name in ((f"zeroshot_{m}", "standard"), (f"zeroshot_{m}_factsinpremise", "facts_in_premise")):
            if s in M:
                L.append(f"| {SHORT[m]} | {name} | " +
                         " | ".join(f"{M[s][f'pred_share_{l}'][0]:.3f}" for l in LABELS) + " |")
    L += ["", "Flip-pair accuracy by operator:", "", "| Model | Format | " + " | ".join(OPERATORS_FLIP) + " |",
          "|---|---|" + "---|" * len(OPERATORS_FLIP)]
    for m in ZS_MODELS:
        for s, name in ((f"zeroshot_{m}", "standard"), (f"zeroshot_{m}_factsinpremise", "facts_in_premise")):
            if s in M:
                L.append(f"| {SHORT[m]} | {name} | " +
                         " | ".join(f"{OPM[s][op]['flip_accuracy'][0]:.2f}" for op in OPERATORS_FLIP) + " |")
    L.append("")
summary["format_comparison"] = fmt_res

# ---------------------------------------------------------------------------------------------------------------
# Main table, all units
# ---------------------------------------------------------------------------------------------------------------
L += ["## 3. All systems (test)", "",
      "| System | Seeds | Accuracy | Macro-F1 | Pair acc. | Flip-pair acc. | Flip sensitivity | Invariance |",
      "|---|---|---|---|---|---|---|---|"]
for u in UNITS:
    L.append(f"| {u} | {len(GROUPS.get(u, [u])) if u in GROUPS else '–'} | " + " | ".join(
        fmt(summarize(M[u][k])) for k in ("accuracy", "macro_f1", "pair_accuracy", "flip_accuracy",
                                           "flip_sensitivity", "invariance")) + " |")
L.append("")

# ---------------------------------------------------------------------------------------------------------------
# Operator hold-out (preregistered ablation)
# ---------------------------------------------------------------------------------------------------------------
ho = [g for g in GROUPS if g.endswith("_op_holdout")]
if ho:
    L += ["## 4. Operator hold-out (preregistered ablation)", "",
          "Training excludes xref_redirect and date_cross pairs. Compared with the full-size paired condition is not "
          "possible (different training size); the comparison below is with the unpaired and paired groups of the "
          "same model, on the held-out and on the seen operators.", "",
          "| Group | Seeds | xref_redirect | date_cross | Other flip operators (mean) |", "|---|---|---|---|---|"]
    for g in sorted(GROUPS):
        if not g.startswith(ho[0].replace("_op_holdout", "")):
            continue
        other = [op for op in OPERATORS_FLIP if op not in ("xref_redirect", "date_cross")]
        oth = np.mean([OPM[g][op]["flip_accuracy"][0] for op in other])
        L.append(f"| {g} | {len(GROUPS[g])} | {fmt(summarize(OPM[g]['xref_redirect']['flip_accuracy']))} | "
                 f"{fmt(summarize(OPM[g]['date_cross']['flip_accuracy']))} | {oth:.3f} |")
    L.append("")

# ---------------------------------------------------------------------------------------------------------------
# Failure decomposition (exploratory)
# ---------------------------------------------------------------------------------------------------------------
L += ["## 5. How flip pairs fail (exploratory)", "",
      "Each flip pair is either solved (both sides correct), *insensitive* (same prediction on both sides: the edit "
      "is ignored), or *sensitive but wrong* (the prediction changes, but at least one side is wrong).", "",
      "| System | Solved | Insensitive | Sensitive but wrong |", "|---|---|---|---|"]
decomp = {}
for u in UNITS:
    solved = M[u]["flip_accuracy"][0]
    insens = 1 - M[u]["flip_sensitivity"][0]
    decomp[u] = {"solved": solved, "insensitive": insens, "sensitive_wrong": 1 - solved - insens}
    L.append(f"| {u} | {solved:.3f} | {insens:.3f} | {1 - solved - insens:.3f} |")
L.append("")
summary["flip_decomposition"] = decomp

# Document complexity by operator
L += ["## 6. Document complexity by operator (test, exploratory)", "",
      "Operators differ in how many conditions their documents carry (negation pairs are built without "
      "conditions), so per-operator accuracy mixes edit type with document complexity.", "",
      "| Operator | Mean sentences | Mean condition sentences | Share with ≥1 distractor |", "|---|---|---|---|"]
complexity = {}
for op in OPERATORS:
    its = [i for i in data["test"] if i["operator"] == op]
    ns = np.mean([len(i["sentences"]) for i in its])
    nc = np.mean([sum(r in ("threshold", "date", "scope", "exception", "xref") for r in i["sentence_roles"]) for i in its])
    nd = np.mean([("distractor" in i["sentence_roles"]) for i in its])
    complexity[op] = {"sentences": ns, "conditions": nc, "distractor": nd}
    L.append(f"| {op} | {ns:.2f} | {nc:.2f} | {nd:.2f} |")
L.append("")
summary["complexity_by_operator"] = complexity

# ---------------------------------------------------------------------------------------------------------------
# Evidence sensitivity (exploratory, from saved occlusion records)
# ---------------------------------------------------------------------------------------------------------------
ev_units = {}
for s in SYSTEMS:
    p = ROOT / s / "evidence_test.jsonl"
    if p.exists():
        ev_units[s] = [json.loads(x) for x in p.read_text().splitlines()]
ev_res = {}
L += ["## 7. Evidence sensitivity (exploratory)", ""]
meta_hits = {}
for s in SYSTEMS:
    meta = json.loads((ROOT / s / "meta.json").read_text())
    if "evidence_test" in meta:
        meta_hits[s] = meta["evidence_test"]
if meta_hits:
    L += ["Preregistered occlusion hit@1 (sentence whose removal most lowers p(gold) is in the gold evidence set; "
          "300 correctly answered entailed/contradicted test items) next to two reference points: the hit rate of a "
          "random sentence, and a strict variant that ignores the obligation sentence (which belongs to every "
          "decided item's evidence set).", ""]
if ev_units:
    L += ["| System | hit@1 | Random-sentence hit rate | Top sentence = obligation | Strict hit@1 (non-obligation "
          "evidence) | Random, strict |", "|---|---|---|---|---|---|"]
    for s, recs in ev_units.items():
        rng = np.random.default_rng(0)
        hit = np.array([r["top"] in r["evidence"] for r in recs], float)
        rand = np.array([len(r["evidence"]) / len(r["roles"]) for r in recs])
        ob = np.array([r["roles"][r["top"]] == "obligation" for r in recs], float)
        strict_recs = [r for r in recs if any(r["roles"][j] != "obligation" for j in r["evidence"])]
        sh = np.array([r["top"] in r["evidence"] and r["roles"][r["top"]] != "obligation" for r in strict_recs], float)
        sr = np.array([sum(r["roles"][j] != "obligation" for j in r["evidence"]) / len(r["roles"]) for r in strict_recs])

        def ci(x):
            bs = [x[rng.integers(0, len(x), len(x))].mean() for _ in range(B)] if len(x) else [np.nan]
            return {"point": float(x.mean()) if len(x) else float("nan"), "lo": float(np.percentile(bs, 2.5)),
                    "hi": float(np.percentile(bs, 97.5)), "n": int(len(x))}
        ev_res[s] = {"hit_at_1": ci(hit), "random": float(rand.mean()), "top_is_obligation": float(ob.mean()),
                     "strict_hit_at_1": ci(sh), "strict_random": float(sr.mean()) if len(sr) else float("nan")}
        L.append(f"| {s} | {fmt(ev_res[s]['hit_at_1'])} | {rand.mean():.3f} | {ob.mean():.3f} | "
                 f"{fmt(ev_res[s]['strict_hit_at_1'])} (n={len(sh)}) | {ev_res[s]['strict_random']:.3f} |")
    L += ["", "**Counterfactual removal test.** For each sampled item and each sentence, the expected label after "
          "deleting that sentence is derived from the rule specification (`clauseshift.evidence`, validated against "
          "the generator on 706 pairs). Removals are grouped as: the obligation sentence (expected: insufficient), a "
          "*decisive* condition (expected: the label changes), and a *non-decisive* sentence (expected: unchanged). "
          "Items with a cross-reference are excluded: removal variants drop the article headers, so \"Article k\" "
          "cannot be resolved. The header-free full document (no sentence removed) is the format control.", "",
          "| System | Items | Header-free control correct | Obligation removed → insufficient | Decisive removed → "
          "label changes as expected | Non-decisive removed → label kept |", "|---|---|---|---|---|---|"]
    for s, recs in ev_units.items():
        agree = collections.defaultdict(list)
        n_items, ctrl = 0, []
        for r in recs:
            it = by_id[r["id"]]
            if not removal_is_well_posed(it):
                continue
            n_items += 1
            if "pred_full_noheaders" in r:
                ctrl.append(r["pred_full_noheaders"] == it["label"])
            for k in range(len(it["sentences"])):
                t = removal_type(it, k)
                agree[t].append(r["pred_removed"][k] == expected_label_after_removal(it, k))
        rate = {t: (float(np.mean(v)), len(v)) for t, v in agree.items()}
        ev_res[s]["counterfactual_removal"] = {t: {"agreement": a, "n": n} for t, (a, n) in rate.items()}
        ev_res[s]["header_free_control_correct"] = float(np.mean(ctrl)) if ctrl else None
        cell = lambda t: f"{rate[t][0]:.3f} (n={rate[t][1]})" if t in rate else "–"  # noqa: E731
        L.append(f"| {s} | {n_items} | {np.mean(ctrl):.3f} | {cell('obligation')} | {cell('decisive')} | "
                 f"{cell('non_decisive')} |" if ctrl else
                 f"| {s} | {n_items} | – | {cell('obligation')} | {cell('decisive')} | {cell('non_decisive')} |")
    L.append("")
elif meta_hits:
    L += ["| System | hit@1 | n |", "|---|---|---|"] + [f"| {s} | {v['hit_at_1']:.3f} | {v['n']} |"
                                                       for s, v in meta_hits.items()] + [""]
else:
    L += ["Not yet available.", ""]
summary["evidence"] = ev_res

Path("results/extended_summary.json").write_text(json.dumps(summary, indent=1, default=float), encoding="utf-8")
Path("results/EXTENDED_ANALYSIS.md").write_text("\n".join(L) + "\n", encoding="utf-8")

# ---------------------------------------------------------------------------------------------------------------
# Figures
# ---------------------------------------------------------------------------------------------------------------
def label(u: str) -> str:
    if u.startswith("zeroshot_"):
        m = u[len("zeroshot_"):].replace("_factsinpremise", "")
        return SHORT.get(m, m) + (", facts in premise" if u.endswith("_factsinpremise") else "")
    if u.startswith("ft_"):
        m = re.match(r"ft_(.+?)_(paired|unpaired|op_holdout|full)$", u)
        model = "DeBERTa-v3-xsmall (NLI init.)" if m.group(1) == "nli-deberta-v3-xsmall" else "DeBERTa-v3-xsmall (no NLI)"
        return f"FT {model}, {m.group(2).replace('_', ' ')} ({len(GROUPS[u])} seed{'s' if len(GROUPS[u]) > 1 else ''})"
    return {"majority": "Majority class", "tfidf_lr_hypothesis_only": "TF-IDF+LR, hypothesis only",
            "tfidf_lr_document_hypothesis": "TF-IDF+LR, document+hypothesis"}.get(u, u)


def errbar(ax, y, s, color, marker="o", dy=0.0, hollow=False):
    ax.errorbar(s["point"], y + dy, xerr=[[s["point"] - s["lo"]], [s["hi"] - s["point"]]], fmt=marker,
                color=color, mfc="white" if hollow else color, ms=5, lw=1.4, capsize=0)


# Fig 1: format comparison
if fmt_res:
    ms = [m for m in ZS_MODELS if m in fmt_res]
    keys = [("accuracy", "Item accuracy"), ("pair_accuracy", "Pair accuracy"), ("flip_accuracy", "Flip-pair accuracy")]
    fig, axes = plt.subplots(1, 3, figsize=(7.2, 0.55 * len(ms) + 1.1), sharey=True)
    for ax, (k, t) in zip(axes, keys):
        for j, m in enumerate(ms):
            errbar(ax, j, summarize(M[f"zeroshot_{m}"][k]), BLUE, dy=0.13)
            errbar(ax, j, summarize(M[f"zeroshot_{m}_factsinpremise"][k]), ORANGE, marker="s", dy=-0.13)
        ax.set_title(t, fontsize=8.5, color=INK)
        ax.set_xlim(0, 1)
        ax.set_ylim(len(ms) - 0.5, -0.5)
        ax.grid(axis="y", visible=False)
    axes[0].set_yticks(range(len(ms)), [SHORT[m] for m in ms])
    h = [plt.Line2D([], [], color=BLUE, marker="o", lw=0, label="facts in hypothesis (standard format)"),
         plt.Line2D([], [], color=ORANGE, marker="s", lw=0, label="facts in premise")]
    fig.legend(handles=h, loc="upper center", ncol=2, frameon=False, bbox_to_anchor=(0.6, 0.0))
    fig.suptitle("Zero-shot NLI on ClauseShift test: effect of input format (95% bootstrap CIs over pairs)",
                 fontsize=9, color=INK, x=0.6, y=1.0 + 0.25 / (0.55 * len(ms) + 1.1))
    fig.tight_layout()
    fig.savefig(FIG / "fig1_format_comparison.png")
    plt.close(fig)

    # Fig 2: predicted label distribution
    rows = []
    for m in ms:
        rows += [(f"zeroshot_{m}", f"{SHORT[m]}\nstandard"), (f"zeroshot_{m}_factsinpremise", "facts in premise")]
    fig, ax = plt.subplots(figsize=(6.4, 0.32 * len(rows) + 1.3))
    cols = [BLUE, ORANGE, AQUA]
    ys = np.arange(len(rows) + 1)
    data_rows = [[gold_share[l] for l in LABELS]] + [[M[s][f"pred_share_{l}"][0] for l in LABELS] for s, _ in rows]
    names = ["Gold labels"] + [n for _, n in rows]
    for y, vals in zip(ys, data_rows):
        left = 0
        for v, c, l in zip(vals, cols, LABELS):
            ax.barh(y, v - 0.004 if v > 0.004 else v, left=left, color=c, height=0.62, label=l if y == 0 else None)
            if v > 0.07:
                ax.text(left + v / 2, y, f"{v:.2f}", ha="center", va="center", fontsize=6.5, color="white")
            left += v
    ax.set_yticks(ys, names, fontsize=7)
    ax.invert_yaxis()
    ax.set_xlim(0, 1)
    ax.grid(False)
    ax.set_xlabel("share of test predictions")
    ax.legend(loc="lower center", ncol=3, frameon=False, bbox_to_anchor=(0.5, 1.0))
    fig.savefig(FIG / "fig2_label_distribution.png")
    plt.close(fig)

# Fig 3: flip-pair accuracy by operator heatmap (sequential blue)
from matplotlib.colors import LinearSegmentedColormap  # noqa: E402

seq = LinearSegmentedColormap.from_list("seqblue", ["#f4f8fd", "#cce3fd", "#84b9f3", "#338ced", "#1b64be", "#0e3d7e"])
rows = [u for u in UNITS if u not in ("majority", "tfidf_lr_hypothesis_only")]
mat = np.array([[OPM[u][op]["flip_accuracy"][0] for op in OPERATORS_FLIP] for u in rows])
fig, ax = plt.subplots(figsize=(7.4, 0.34 * len(rows) + 1.4))
im = ax.imshow(mat, vmin=0, vmax=1, cmap=seq, aspect="auto")
ax.set_xticks(range(len(OPERATORS_FLIP)), [o.replace("_", "\n") for o in OPERATORS_FLIP], fontsize=7)
ax.set_yticks(range(len(rows)), [label(u) for u in rows], fontsize=7)
ax.grid(False)
for i in range(mat.shape[0]):
    for j in range(mat.shape[1]):
        ax.text(j, i, f"{mat[i, j]:.2f}", ha="center", va="center", fontsize=6.5,
                color="white" if mat[i, j] > 0.55 else INK)
cb = fig.colorbar(im, ax=ax, fraction=0.03, pad=0.02)
cb.set_label("flip-pair accuracy (both sides correct)", fontsize=7)
cb.outline.set_visible(False)
ax.set_title("ClauseShift test: flip-pair accuracy by edit operator", fontsize=9, color=INK)
fig.savefig(FIG / "fig3_flip_accuracy_by_operator.png")
plt.close(fig)

# Fig 4: flip-pair failure decomposition
fig, ax = plt.subplots(figsize=(6.8, 0.3 * len(UNITS) + 1.2))
for y, u in enumerate(UNITS):
    left = 0
    for key, c, l in (("solved", BLUE, "solved (both sides correct)"), ("insensitive", GRAY, "insensitive (same answer on both sides)"),
                      ("sensitive_wrong", ORANGE, "answer changes, but wrong")):
        v = decomp[u][key]
        ax.barh(y, max(v - 0.004, 0), left=left, color=c, height=0.62, label=l if y == 0 else None)
        if v > 0.08:
            ax.text(left + v / 2, y, f"{v:.2f}", ha="center", va="center", fontsize=6.5, color="white")
        left += v
ax.set_yticks(range(len(UNITS)), [label(u) for u in UNITS], fontsize=7)
ax.invert_yaxis()
ax.set_xlim(0, 1)
ax.grid(False)
ax.set_xlabel("share of flip pairs (test)")
ax.legend(loc="lower center", ncol=3, frameon=False, bbox_to_anchor=(0.4, 1.0), fontsize=7)
fig.savefig(FIG / "fig4_flip_failure_decomposition.png")
plt.close(fig)

# Fig 5: H3 forest plot
if h3:
    prefix = "ft_nli-deberta-v3-xsmall" if "ft_nli-deberta-v3-xsmall" in h3 else next(iter(h3))
    r = h3[prefix]
    items = [("flip_accuracy", "Flip-pair accuracy"), ("pair_accuracy", "Pair accuracy"), ("accuracy", "Item accuracy"),
             ("macro_f1", "Macro-F1"), ("invariance", "Invariance")] + \
            [(op, f"flip acc.: {op}") for op in OPERATORS_FLIP]
    fig, ax = plt.subplots(figsize=(6.2, 0.3 * len(items) + 1.2))
    for y, (k, t) in enumerate(items):
        s = r[k] if k in r else r["by_operator"][k]
        errbar(ax, y, s, BLUE if y < 5 else INK2)
        if "per_seed" in s:
            ax.scatter(s["per_seed"], [y] * len(s["per_seed"]), s=9, color=ORANGE, zorder=3, lw=0)
    ax.axvline(0, color=INK2, lw=0.8)
    ax.axhline(4.5, color="#dddddd", lw=0.8)
    ax.set_yticks(range(len(items)), [t for _, t in items], fontsize=7)
    ax.invert_yaxis()
    ax.grid(axis="y", visible=False)
    ax.set_xlabel("paired − unpaired (test; mean over seeds, 95% cluster-bootstrap CI)")
    ax.set_title(f"H3: training on complete minimal pairs vs. one side per pair ({label(prefix + '_paired').split(',')[0][3:]}, "
                 f"{r['n_seeds']} seed{'s' if r['n_seeds'] > 1 else ''})", fontsize=8.5, color=INK)
    h = [plt.Line2D([], [], color=BLUE, marker="o", lw=1.4, label="mean difference, 95% CI"),
         plt.Line2D([], [], color=ORANGE, marker="o", lw=0, ms=3, label="single seed")]
    ax.legend(handles=h, loc="upper center", frameon=False, fontsize=7, ncol=2, bbox_to_anchor=(0.4, -0.09))
    fig.savefig(FIG / "fig5_h3_paired_vs_unpaired.png")
    plt.close(fig)

# Fig 6: evidence
if ev_res and any("counterfactual_removal" in v for v in ev_res.values()):
    us = [s for s in ev_res if "counterfactual_removal" in ev_res[s]]
    us = sorted(us, key=lambda s: (not s.startswith("zeroshot"), s))
    cats = [("obligation", "obligation removed\n→ insufficient"), ("decisive", "decisive condition removed\n→ label changes"),
            ("non_decisive", "other sentence removed\n→ label kept")]
    fig, ax = plt.subplots(figsize=(6.8, 0.42 * len(us) + 1.4))
    for y, s in enumerate(us):
        for j, (t, _) in enumerate(cats):
            v = ev_res[s]["counterfactual_removal"].get(t, {}).get("agreement", np.nan)
            ax.barh(y + (j - 1) * 0.26, v, height=0.24, color=[GRAY, BLUE, AQUA][j], label=cats[j][1] if y == 0 else None)
    def single(s: str) -> str:
        if not s.startswith("ft_"):
            return label(s)
        m = re.match(r"ft_(.+?)_(paired|unpaired|op_holdout|full)_s(\d+)$", s)
        init = "NLI init." if m.group(1) == "nli-deberta-v3-xsmall" else "no NLI"
        return f"FT xsmall ({init}), {m.group(2).replace('_', ' ')}, seed {m.group(3)}"
    ax.set_yticks(range(len(us)), [single(s) for s in us], fontsize=7)
    ax.invert_yaxis()
    ax.set_xlim(0, 1)
    ax.grid(axis="y", visible=False)
    ax.set_xlabel("share of sentence removals where the prediction matches the specification")
    ax.legend(loc="lower center", ncol=3, frameon=False, bbox_to_anchor=(0.45, 1.0), fontsize=7)
    fig.savefig(FIG / "fig6_counterfactual_removal.png")
    plt.close(fig)

print("\n".join(L))
