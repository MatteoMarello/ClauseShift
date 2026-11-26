"""Held-out test of H_lex and H_md (PILOT_PROTOCOL.md, addendum 2) on stored registered test predictions.

No inference. Specs/cases regenerated in memory (manifest hashes checked by program_fingerprint).
Outputs project_anomaly/results/lexical_comparison_test.json and LEXICAL_COMPARISON_TEST.md
"""

import contextlib
import dataclasses
import datetime as dt
import io
import json
import sys
from collections import defaultdict
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "research_next/scripts"))
with contextlib.redirect_stdout(io.StringIO()):
    from program_fingerprint import SPECS  # noqa: E402

from clauseshift.generator import gold_label  # noqa: E402

UNIT = {"enrollment": 1, "research_funding": 5000}
NLI_RUNS = [f"ft_nli-deberta-v3-xsmall_{c}_s{s}" for c in ("paired", "unpaired", "op_holdout") for s in range(3)]
GENERIC_RUNS = [f"ft_deberta-v3-xsmall_{c}_s{s}" for c in ("paired", "unpaired") for s in range(3)]
B = 2000


def build_items():
    test = [json.loads(line) for line in open(ROOT / "data/test.jsonl")]
    out = []
    for it in test:
        spec, case = SPECS[it["id"]]
        fam = it["family"]
        for kind in ("threshold", "date"):
            cut = spec.threshold if kind == "threshold" else spec.date_cutoff
            val = case.num if kind == "threshold" else case.date
            if cut is None or val is None:
                continue
            step = UNIT[fam] if kind == "threshold" else dt.timedelta(days=1)
            field = "num" if kind == "threshold" else "date"
            sat = gold_label(spec, dataclasses.replace(case, **{field: cut + step}))[0]
            unsat = gold_label(spec, dataclasses.replace(case, **{field: cut}))[0]
            if sat == unsat or val > cut:
                continue
            assert gold_label(spec, case)[0] == unsat == it["label"]
            rec = {"id": it["id"], "pair_id": it["pair_id"], "family": fam, "kind": kind, "sat_label": sat}
            if kind == "threshold":
                v, c = str(val), str(cut)
                rec["group"] = "lex_greater" if (len(v) < len(c) and v[0] > c[0]) else "other"
                rec["ratio"] = val / cut
            else:
                rec["group"] = "md_later" if (val.month, val.day) > (cut.month, cut.day) else \
                    ("md_equal" if (val.month, val.day) == (cut.month, cut.day) else "md_earlier")
                rec["days_before"] = (cut - val).days
            out.append(rec)
    return out


def contrast(rows, preds_by_run, runs, g1, g0, rng, keep=lambda r: True):
    rows = [r for r in rows if keep(r) and r["group"] in (g1, g0)]
    n1, n0 = sum(r["group"] == g1 for r in rows), sum(r["group"] == g0 for r in rows)
    if n1 < 10 or n0 < 10:
        return {"testable": False, "n": [n1, n0]}
    sat = np.array([[preds_by_run[u][r["id"]] == r["sat_label"] for r in rows] for u in runs], float)  # runs x items
    is1 = np.array([r["group"] == g1 for r in rows])
    per_run = [float(s[is1].mean() - s[~is1].mean()) for s in sat]
    pooled = sat.mean(0)
    pairs = sorted({r["pair_id"] for r in rows})
    pid = np.array([pairs.index(r["pair_id"]) for r in rows])
    boots = []
    for _ in range(B):
        w = np.bincount(rng.integers(0, len(pairs), len(pairs)), minlength=len(pairs))[pid]
        a = (w * pooled * is1).sum() / max((w * is1).sum(), 1)
        b = (w * pooled * ~is1).sum() / max((w * ~is1).sum(), 1)
        boots.append(a - b)
    return {"testable": True, "n": [n1, n0], "p_sat": [float(pooled[is1].mean()), float(pooled[~is1].mean())],
            "contrast": float(pooled[is1].mean() - pooled[~is1].mean()),
            "ci95": [float(np.percentile(boots, 2.5)), float(np.percentile(boots, 97.5))],
            "per_run": dict(zip(runs, per_run)), "runs_positive": int(sum(x > 0 for x in per_run))}


def main():
    rng = np.random.default_rng(0)
    rows = build_items()
    preds = {}
    for u in NLI_RUNS + GENERIC_RUNS:
        preds[u] = {r["id"]: r["pred"] for r in map(json.loads, open(ROOT / f"results/predictions/{u}/test.jsonl"))}
    rf_th = [r for r in rows if r["kind"] == "threshold" and r["family"] == "research_funding"]
    en_th = [r for r in rows if r["kind"] == "threshold" and r["family"] == "enrollment"]
    dates = [r for r in rows if r["kind"] == "date"]
    res = {"counts": {k: len(v) for k, v in (("rf_threshold", rf_th), ("en_threshold", en_th), ("date", dates))}}
    for label, runs in (("nli_init", NLI_RUNS), ("generic_init", GENERIC_RUNS)):
        r = {
            "H_lex": contrast(rf_th, preds, runs, "lex_greater", "other", rng),
            "H_lex_distance_controlled": contrast(rf_th, preds, runs, "lex_greater", "other", rng,
                                                  keep=lambda x: 0.3 <= x["ratio"] <= 0.9),
            "H_lex_enrollment (reference)": contrast(en_th, preds, runs, "lex_greater", "other", rng),
            "H_md": contrast(dates, preds, runs, "md_later", "md_earlier", rng),
            "H_md_distance_controlled": contrast(dates, preds, runs, "md_later", "md_earlier", rng,
                                                 keep=lambda x: 1 <= x["days_before"] <= 365),
        }
        for fam in ("enrollment", "research_funding"):
            r[f"H_md_{fam}"] = contrast([d for d in dates if d["family"] == fam], preds, runs, "md_later",
                                        "md_earlier", rng)
        res[label] = r
    for h in ("H_lex", "H_md"):
        a, b = res["nli_init"][h], res["nli_init"][f"{h}_distance_controlled"]
        res["nli_init"][f"{h}_verdict"] = (
            "not testable" if not (a["testable"] and b["testable"]) else
            "supported" if (a["contrast"] >= 0.15 and a["ci95"][0] > 0 and b["contrast"] >= 0.10
                            and a["runs_positive"] >= 7) else "not supported")
    json.dump(res, open(ROOT / "project_anomaly/results/lexical_comparison_test.json", "w", newline="\n"), indent=2)

    L = ["# Held-out test of surface comparison heuristics (generated by "
         "`project_anomaly/scripts/lexical_comparison_test.py`)", "",
         "Registered test split, stored predictions, value at or below the cutoff, condition decisive. P_sat = share "
         "of predictions equal to the label the item would have if the condition held (correct value: 0). "
         "Pooled over runs; 95% cluster-bootstrap CI over minimal pairs.", "",
         f"Items: research_funding thresholds {res['counts']['rf_threshold']}, enrollment thresholds "
         f"{res['counts']['en_threshold']}, dates {res['counts']['date']}.", "",
         "| Runs | Contrast | n (group, other) | P_sat group | P_sat other | Difference [95% CI] | Runs positive |",
         "|---|---|---|---|---|---|---|"]
    for label in ("nli_init", "generic_init"):
        for k, c in res[label].items():
            if k.endswith("verdict"):
                continue
            if not c["testable"]:
                L.append(f"| {label} | {k} | {c['n']} | – | – | not testable | – |")
                continue
            L.append(f"| {label} | {k} | {c['n'][0]}, {c['n'][1]} | {c['p_sat'][0]:.3f} | {c['p_sat'][1]:.3f} | "
                     f"{c['contrast']:+.3f} [{c['ci95'][0]:+.3f}, {c['ci95'][1]:+.3f}] | {c['runs_positive']}/"
                     f"{len(c['per_run'])} |")
    L += ["", f"Verdicts (NLI-init, fixed criteria): H_lex = {res['nli_init']['H_lex_verdict']}; "
               f"H_md = {res['nli_init']['H_md_verdict']}."]
    (ROOT / "project_anomaly/results/LEXICAL_COMPARISON_TEST.md").write_text("\n".join(L) + "\n")
    print("\n".join(L))


if __name__ == "__main__":
    main()
