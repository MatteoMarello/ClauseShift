"""Analysis of the year-blindness replication exactly as frozen in YEAR_PROBE_PROTOCOL.md.

Outputs project_anomaly/results/year_probe_results.json and YEAR_PROBE_RESULTS_TABLES.md
"""

import json
import sys
from collections import defaultdict
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
RES = ROOT / "project_anomaly/results"
sys.path.insert(0, str(Path(__file__).resolve().parent))
from run_models import CHECKPOINTS  # noqa: E402

B = 2000
BINS = ["d001-030", "d031-120", "d121-300"]
FAMILIES = ["vehicles", "enrollment", "research_funding"]
NLI = CHECKPOINTS[:2]
items = [json.loads(line) for line in open(RES / "year_probes.jsonl")]


def boot_mean_diff(a_groups: dict, b_groups: dict, rng, weights=None):
    """Difference of (bin-weighted) means. a_groups/b_groups: bin -> {base: value}. Resample bases within each group."""
    keys = list(a_groups)
    w = weights or {k: 1 / len(keys) for k in keys}

    def point(ga, gb):
        return sum(w[k] * (np.mean(list(ga[k].values())) - np.mean(list(gb[k].values()))) for k in keys)

    est = point(a_groups, b_groups)
    boots = []
    arrs = {k: (np.array(list(a_groups[k].values())), np.array(list(b_groups[k].values()))) for k in keys}
    for _ in range(B):
        s = 0.0
        for k in keys:
            a, b = arrs[k]
            s += w[k] * (a[rng.integers(0, len(a), len(a))].mean() - b[rng.integers(0, len(b), len(b))].mean())
        boots.append(s)
    return {"estimate": float(est), "ci95": [float(np.percentile(boots, 2.5)), float(np.percentile(boots, 97.5))]}


def analyse(model, rng):
    pred = {r["id"]: r["pred"] for r in map(json.loads, open(RES / f"predictions/yearprobe__{model}.jsonl"))}
    sat = {r["id"]: float(pred[r["id"]] == r["sat_label"]) for r in items}
    acc = {r["id"]: float(pred[r["id"]] == r["label"]) for r in items}
    out = {}

    def groups(fmt, direction, rel, family=None, extra=lambda r: True):
        g = defaultdict(dict)
        for r in items:
            if (r["block"] == "main" and r["format"] == fmt and r["direction"] == direction and r["year_rel"] == rel
                    and (family is None or r["family"] == family) and extra(r)):
                g[r["bin"]][r["base"]] = sat[r["id"]]
        return g

    for fmt in ("G", "US", "ISO"):
        consistent = [acc[r["id"]] for r in items if r["block"] == "main" and r["format"] == fmt and r["year_rel"] == "same"]
        cell = {f"{d}/{rel}": float(np.mean([sat[r["id"]] for r in items if r["block"] == "main" and r["format"] == fmt
                                             and r["direction"] == d and r["year_rel"] == rel]))
                for d in ("before", "after") for rel in ("same", "cross")}
        res = {"validity_accuracy_same_year": float(np.mean(consistent)), "p_sat": cell,
               "delta_before": boot_mean_diff(groups(fmt, "before", "cross"), groups(fmt, "before", "same"), rng),
               "delta_after": boot_mean_diff(groups(fmt, "after", "same"), groups(fmt, "after", "cross"), rng)}
        res["delta_before_by_bin"] = {
            b: float(np.mean(list(groups(fmt, "before", "cross")[b].values())) -
                     np.mean(list(groups(fmt, "before", "same")[b].values()))) for b in BINS}
        res["delta_before_by_family"] = {
            f: float(np.mean([np.mean(list(groups(fmt, "before", "cross", f)[b].values())) -
                              np.mean(list(groups(fmt, "before", "same", f)[b].values())) for b in BINS]))
            for f in FAMILIES}
        out[fmt] = res
    # C3: cutoffs in January-March only (pooled bins; reported with n)
    early = lambda r: int(r["cutoff"][5:7]) <= 3  # noqa: E731
    a = [sat[r["id"]] for r in items if r["block"] == "main" and r["format"] == "G" and r["direction"] == "before"
         and r["year_rel"] == "cross" and early(r)]
    bb = [sat[r["id"]] for r in items if r["block"] == "main" and r["format"] == "G" and r["direction"] == "before"
          and r["year_rel"] == "same" and early(r)]
    out["C3_cutoff_jan_mar"] = {"n_cross": len(a), "n_same": len(bb), "p_sat_cross": float(np.mean(a)),
                                "p_sat_same": float(np.mean(bb)) if bb else None,
                                "delta_before": float(np.mean(a) - np.mean(bb)) if bb else None}
    # also distance-matched within C3: same-year early cutoffs only exist at short distances
    a1 = [sat[r["id"]] for r in items if r["block"] == "main" and r["format"] == "G" and r["direction"] == "before"
          and r["year_rel"] == "cross" and early(r) and r["bin"] == "d001-030"]
    b1 = [sat[r["id"]] for r in items if r["block"] == "main" and r["format"] == "G" and r["direction"] == "before"
          and r["year_rel"] == "same" and early(r) and r["bin"] == "d001-030"]
    out["C3_cutoff_jan_mar"]["bin_d001_030"] = {"n_cross": len(a1), "n_same": len(b1),
                                                "delta_before": float(np.mean(a1) - np.mean(b1)) if a1 and b1 else None}
    # YEAR block
    yr = {k: float(np.mean([sat[r["id"]] for r in items if r["block"] == "year" and r["year_offset"] == k]))
          for k in (-2, -1, 1, 2)}
    out["year_only"] = {"p_sat_by_offset": yr, "Y": float(np.mean([yr[1], yr[2]]) - np.mean([yr[-1], yr[-2]]))}
    # DAYMONTH block
    out["day_month_only"] = {f"{k}/{d}": float(np.mean([acc[r["id"]] for r in items if r["block"] == "daymonth"
                                                         and r["kind"] == k and r["direction"] == d]))
                             for k in ("day_only", "month_only") for d in ("before", "after")}
    out["day_month_only"]["day_only"] = float(np.mean([acc[r["id"]] for r in items if r["block"] == "daymonth"
                                                       and r["kind"] == "day_only"]))
    out["day_month_only"]["month_only"] = float(np.mean([acc[r["id"]] for r in items if r["block"] == "daymonth"
                                                         and r["kind"] == "month_only"]))
    g = out["G"]
    out["verdict"] = {
        "V": g["validity_accuracy_same_year"] >= 0.80,
        "H1": bool(g["delta_before"]["estimate"] >= 0.20 and g["delta_before"]["ci95"][0] > 0.05
                   and all(v > 0 for v in g["delta_before_by_bin"].values())
                   and sum(v > 0 for v in g["delta_before_by_family"].values()) >= 2),
        "H2_asymmetry (Δ_after < 0.10)": g["delta_after"]["estimate"] < 0.10,
        "H3_year_only (Y < 0.50)": out["year_only"]["Y"] < 0.50,
        "H4_format": {f: (out[f]["delta_before"]["estimate"] >= 0.10 if out[f]["validity_accuracy_same_year"] >= 0.80
                          else "uninterpretable (V fails)") for f in ("US", "ISO")},
        "H5_day_month (both ≥ 0.80)": out["day_month_only"]["day_only"] >= 0.80 and out["day_month_only"]["month_only"] >= 0.80,
        "C3 (Δ_before ≥ 0.10 with Jan–Mar cutoffs)": (out["C3_cutoff_jan_mar"]["delta_before"] or -1) >= 0.10,
    }
    return out


def main():
    rng = np.random.default_rng(0)
    res = {m: analyse(m, rng) for m in CHECKPOINTS}
    replicated = all(res[m]["verdict"]["V"] and res[m]["verdict"]["H1"] for m in NLI)
    res["decision"] = "REPLICATED" if replicated else "NOT REPLICATED — direction closed"
    json.dump(res, open(RES / "year_probe_results.json", "w", newline="\n"), indent=2, default=str)
    L = ["# Year-blindness replication (generated by `project_anomaly/scripts/analyze_year_probes.py`)", "",
         "Frozen protocol: `YEAR_PROBE_PROTOCOL.md`. P_sat = P(satisfied reading); ideal 0 before the cutoff, 1 after. "
         "95% bootstrap CIs over base cases.", "",
         f"**Decision (frozen rule): {res['decision']}**", "",
         "| Model | Format | Accuracy same-year (V) | P_sat before/same | P_sat before/cross | Δ_before [95% CI] | "
         "P_sat after/same | P_sat after/cross | Δ_after [95% CI] |", "|" + "---|" * 9]
    for m in CHECKPOINTS:
        for f in ("G", "US", "ISO"):
            r = res[m][f]
            p = r["p_sat"]
            ci = lambda d: f"{d['estimate']:+.3f} [{d['ci95'][0]:+.3f}, {d['ci95'][1]:+.3f}]"  # noqa: E731
            L.append(f"| {m} | {f} | {r['validity_accuracy_same_year']:.3f} | {p['before/same']:.3f} | "
                     f"{p['before/cross']:.3f} | {ci(r['delta_before'])} | {p['after/same']:.3f} | "
                     f"{p['after/cross']:.3f} | {ci(r['delta_after'])} |")
    L += ["", "Δ_before by distance bin and by family (format G):", "",
          "| Model | " + " | ".join(BINS) + " | " + " | ".join(FAMILIES) + " |", "|" + "---|" * 7]
    for m in CHECKPOINTS:
        r = res[m]["G"]
        L.append(f"| {m} | " + " | ".join(f"{r['delta_before_by_bin'][b]:+.3f}" for b in BINS) + " | "
                 + " | ".join(f"{r['delta_before_by_family'][f]:+.3f}" for f in FAMILIES) + " |")
    L += ["", "Year-only (same month and day), day-only and month-only (same year), cutoff-month control:", "",
          "| Model | P_sat k=−2 | k=−1 | k=+1 | k=+2 | Y | Acc. day-only | Acc. month-only | C3 Δ_before (n cross, n same) |",
          "|" + "---|" * 9]
    for m in CHECKPOINTS:
        r = res[m]
        y = r["year_only"]["p_sat_by_offset"]
        c3 = r["C3_cutoff_jan_mar"]
        c3s = "n/a" if c3["delta_before"] is None else f"{c3['delta_before']:+.3f} ({c3['n_cross']}, {c3['n_same']})"
        L.append(f"| {m} | {y[-2]:.2f} | {y[-1]:.2f} | {y[1]:.2f} | {y[2]:.2f} | {r['year_only']['Y']:+.2f} | "
                 f"{r['day_month_only']['day_only']:.2f} | {r['day_month_only']['month_only']:.2f} | {c3s} |")
    L += ["", "Verdicts per model:", ""]
    for m in CHECKPOINTS:
        L.append(f"- {m}: " + "; ".join(f"{k} = {v}" for k, v in res[m]["verdict"].items()))
    (RES / "YEAR_PROBE_RESULTS_TABLES.md").write_text("\n".join(L) + "\n")
    print("\n".join(L))


if __name__ == "__main__":
    main()
