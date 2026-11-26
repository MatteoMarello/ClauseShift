"""Behavioural program identification (exploratory).

Idea: describe each model by the *program* it behaves like. A lattice of candidate programs is built by altering
the reference rule (`gold_label`) along independent dimensions: which clause types are read, whether threshold and
date comparisons are strict, how cross-references and exemptions are interpreted, and how missing attributes are
treated. For every model, the program with the highest item-level agreement on the **dev** split is selected, and
its agreement is then reported on **test** (selection and evaluation on different data).

Specifications and cases are re-generated in memory with the original generator (data/ is not touched); the content
hashes are checked against data/manifest.json before anything else runs.

Outputs research_next/results/program_fingerprint.json and PROGRAM_FINGERPRINT.md.
"""

import collections
import dataclasses
import itertools
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

import numpy as np  # noqa: E402

import clauseshift.generator as gen  # noqa: E402
from clauseshift.data import build  # noqa: E402
from clauseshift.generator import CONTRADICTED, ENTAILED, INSUFFICIENT, content_hash  # noqa: E402

# ---- regenerate items together with their (spec, case) -----------------------------------------------------
SPECS = {}
_orig_item = gen._item


def _capturing_item(family, dom, spec, surf, case, pair_id, side):
    it = _orig_item(family, dom, spec, surf, case, pair_id, side)
    SPECS[it["id"]] = (dataclasses.replace(spec), dataclasses.replace(case))
    return it


gen._item = _capturing_item
config = json.loads((ROOT / "configs/data.json").read_text())
splits = build(config)
gen._item = _orig_item
manifest = json.loads((ROOT / "data/manifest.json").read_text())
for s in ("dev", "test"):
    assert content_hash(splits[s]) == manifest["files"][s]["sha256_content"], f"hash mismatch {s}"


# ---- program lattice ---------------------------------------------------------------------------------------
@dataclasses.dataclass(frozen=True)
class Program:
    threshold: str   # ignore | nonstrict | strict
    date: str        # ignore | nonstrict | strict
    scope: str       # ignore | read
    exception: str   # ignore | any_category | read
    xref: str        # ignore | article_token | read
    unknown: str     # ignore | read   (read = condition on an unstated attribute -> insufficient)
    negation: str    # ignore | read

    def name(self) -> str:
        return ",".join(f"{k}={v}" for k, v in dataclasses.asdict(self).items())


REFERENCE = Program("strict", "strict", "read", "read", "read", "read", "read")


def run(p: Program, spec, case) -> str:
    if spec.topic != 0:
        lab = INSUFFICIENT
    elif spec.polarity < 0 and p.negation == "read":
        lab = CONTRADICTED
    else:
        failing, unknown = False, False
        for kind, cut, val in (("threshold", spec.threshold, case.num), ("date", spec.date_cutoff, case.date)):
            mode = getattr(p, kind)
            if cut is None or mode == "ignore":
                continue
            if val is None:
                unknown = True
            elif (val <= cut) if mode == "strict" else (val < cut):
                failing = True
        if spec.scope_loc is not None and p.scope == "read" and case.loc != spec.scope_loc:
            failing = True
        if spec.exception_cat is not None and (p.exception == "any_category" or
                                               (p.exception == "read" and spec.exception_cat == case.cat)):
            failing = True
        if spec.xref is not None and ((p.xref == "article_token" and spec.xref[1] == 1) or
                                      (p.xref == "read" and spec.xref == (case.cat, 1))):
            failing = True
        lab = CONTRADICTED if failing else (INSUFFICIENT if unknown and p.unknown == "read" else ENTAILED)
    if case.claim_polarity < 0 and lab != INSUFFICIENT:
        lab = ENTAILED if lab == CONTRADICTED else CONTRADICTED
    return lab


DIMS = {"threshold": ["ignore", "nonstrict", "strict"], "date": ["ignore", "nonstrict", "strict"],
        "scope": ["ignore", "read"], "exception": ["ignore", "any_category", "read"],
        "xref": ["ignore", "article_token", "read"], "unknown": ["ignore", "read"], "negation": ["ignore", "read"]}
PROGRAMS = [Program(*v) for v in itertools.product(*DIMS.values())]

items = {s: splits[s] for s in ("dev", "test")}
prog_preds = {s: np.array([[run(p, *SPECS[i["id"]]) for i in items[s]] for p in PROGRAMS]) for s in items}
gold = {s: np.array([i["label"] for i in items[s]]) for s in items}
ref_idx = PROGRAMS.index(REFERENCE)
assert (prog_preds["test"][ref_idx] == gold["test"]).all(), "reference program must reproduce gold labels"

# ---- fingerprint each saved system ---------------------------------------------------------------------------
PRED = ROOT / "results/predictions"
systems = sorted(d.name for d in PRED.iterdir() if (d / "test.jsonl").exists() and (d / "dev.jsonl").exists())
extra = ROOT / "research_next/results/predictions"
res, L = {}, ["# Behavioural program identification (exploratory; generated by research_next/scripts/program_fingerprint.py)",
              "", f"{len(PROGRAMS)} candidate programs. Program selected by item agreement on dev (vehicles, 960 items); "
              "agreement reported on test (2,560 items). 'Gold' = agreement of the system with the reference rule "
              "(= its accuracy). The lazy reader corresponds to the program that reads only topic and negation.", "",
              "| System | Test accuracy | Best program (selected on dev) | Test agreement with it | Runner-up agreement on test |",
              "|---|---|---|---|---|"]


def load_preds(d: Path, split: str) -> np.ndarray:
    P = {r["id"]: r["pred"] for r in map(json.loads, open(d / f"{split}.jsonl"))}
    return np.array([P[i["id"]] for i in items[split]])


for s in systems:
    d = PRED / s
    pd_, pt = load_preds(d, "dev"), load_preds(d, "test")
    agree_dev = (prog_preds["dev"] == pd_).mean(1)
    agree_test = (prog_preds["test"] == pt).mean(1)
    best = int(agree_dev.argmax())
    order = np.argsort(-agree_test)
    runner = next(int(k) for k in order if k != best)
    res[s] = {"best_program": dataclasses.asdict(PROGRAMS[best]), "dev_agreement": float(agree_dev[best]),
              "test_agreement": float(agree_test[best]), "test_accuracy": float((pt == gold["test"]).mean()),
              "best_on_test": dataclasses.asdict(PROGRAMS[int(order[0])]), "best_on_test_agreement": float(agree_test[order[0]]),
              "runner_up_test": float(agree_test[runner])}
    # identifiability: options of each dimension that tie with the selected one on dev (other dims fixed)
    ties = {}
    for dim, options in DIMS.items():
        same = []
        for o in options:
            q = dataclasses.replace(PROGRAMS[best], **{dim: o})
            if (prog_preds["dev"][PROGRAMS.index(q)] == prog_preds["dev"][best]).all():
                same.append(o)
        ties[dim] = same
    res[s]["dev_indistinguishable_options"] = ties
    parts = []
    for k, v in dataclasses.asdict(PROGRAMS[best]).items():
        opts = ties[k]
        if len(opts) > 1:
            if getattr(REFERENCE, k) in opts and len(opts) < len(DIMS[k]):
                parts.append(f"{k}={'|'.join(opts)}")
            elif getattr(REFERENCE, k) not in opts:
                parts.append(f"{k}={'|'.join(opts)}")
        elif v != getattr(REFERENCE, k):
            parts.append(f"{k}={v}")
    short = ", ".join(parts)
    L.append(f"| {s} | {res[s]['test_accuracy']:.3f} | {short or 'reference rule'} | {agree_test[best]:.3f} | "
             f"{agree_test[runner]:.3f} |")

# marginal view: for each dimension, which option fits best given the other dims at their best values
L += ["", "Cells list the dimensions where the selected program differs from the reference rule, and dimensions whose "
      "options cannot be distinguished on dev (shown as a|b: the data give identical predictions for both). "
      "Dimensions: threshold/date comparison (ignore / non-strict / strict), scope, exception (ignore / any category "
      "/ read), cross-reference (ignore / article token only / read), unstated attribute (ignore / read), negation.", ""]
ident = {}
for dim, options in DIMS.items():
    ref_alt = [o for o in options if o != getattr(REFERENCE, dim)]
    ident[dim] = {o: int((prog_preds["test"][PROGRAMS.index(dataclasses.replace(REFERENCE, **{dim: o}))]
                          != prog_preds["test"][ref_idx]).sum()) for o in ref_alt}
L += ["## Identifiability of the benchmark", "",
      "Number of test items (of 2,560) on which a one-dimension deviation from the reference rule changes the "
      "prediction. Zero means the test set cannot tell that deviation apart from the correct rule.", "",
      "| Dimension | Alternative | Items that distinguish it |", "|---|---|---|"]
for dim, d in ident.items():
    for o, n in d.items():
        L.append(f"| {dim} | {o} | {n} |")
res["_identifiability_test"] = ident
(ROOT / "research_next/results/program_fingerprint.json").write_text(json.dumps(res, indent=1), encoding="utf-8")
(ROOT / "research_next/results/PROGRAM_FINGERPRINT.md").write_text("\n".join(L) + "\n", encoding="utf-8")
print("\n".join(L))
