"""Pilot 2 analysis exactly as fixed in PILOT_PROTOCOL.md (symmetry under claim negation).

sigma: entailed <-> contradicted, insufficient fixed.
- symmetry consistency  P(pred_flip = sigma(pred_orig))
- covariant error share among items wrong on the original: P(pred_flip = sigma(pred_orig) | orig wrong)
  (+ an independence baseline: the same quantity if pred_flip were drawn from its marginal among those items)
- symmetrised decoding p_sym(y) ∝ p_orig(y) * p_flip(sigma(y)); accuracy change vs. original
Cluster bootstrap over minimal pairs (pair_id), 2,000 resamples. Original predictions are the stored registered ones.
Output: project_anomaly/results/pilot2_results.json and PILOT2_TABLES.md
"""

import json
from collections import Counter
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
RES = ROOT / "project_anomaly/results"
LABELS = ["entailed", "contradicted", "insufficient"]
SIGMA = {"entailed": "contradicted", "contradicted": "entailed", "insufficient": "insufficient"}
MODELS = {  # pilot name -> stored registered predictions
    "ft_nli-deberta-v3-xsmall_paired_s0": "ft_nli-deberta-v3-xsmall_paired_s0",
    "ft_nli-deberta-v3-xsmall_unpaired_s0": "ft_nli-deberta-v3-xsmall_unpaired_s0",
    "ft_deberta-v3-xsmall_paired_s0": "ft_deberta-v3-xsmall_paired_s0",
    "ft_deberta-v3-xsmall_unpaired_s0": "ft_deberta-v3-xsmall_unpaired_s0",
    "zs_deberta-v3-base-nli": "zeroshot_nli-deberta-v3-base",
    "zs_deberta-v3-base-mnli-fever-anli": "zeroshot_DeBERTa-v3-base-mnli-fever-anli",
}
B = 2000


def load(path):
    return {r["id"]: r for r in map(json.loads, open(path))}


def stats(rows):
    """rows: list of dicts with keys gold, gold_f, p_o, p_f (prob vectors in LABELS order)."""
    y = np.array([LABELS.index(r["gold"]) for r in rows])
    yf = np.array([LABELS.index(r["gold_f"]) for r in rows])
    po = np.array([r["p_o"] for r in rows])
    pf = np.array([r["p_f"] for r in rows])
    perm = [LABELS.index(SIGMA[l]) for l in LABELS]           # index of sigma(y) for each y
    a_o, a_f = po.argmax(1), pf.argmax(1)
    sig_a_o = np.array(perm)[a_o]
    consistent = (a_f == sig_a_o)
    wrong = a_o != y
    psym = po * pf[:, perm]
    psym /= psym.sum(1, keepdims=True)
    sym_acc_o = psym.argmax(1) == y
    psym_f = pf * po[:, perm]                                 # the same decoder applied to the flipped item
    sym_acc_f = (psym_f / psym_f.sum(1, keepdims=True)).argmax(1) == yf
    return {"acc_orig": a_o == y, "acc_flip": a_f == yf, "consistent": consistent, "wrong": wrong,
            "sym_acc_orig": sym_acc_o, "sym_acc_flip": sym_acc_f, "sig_a_o": sig_a_o, "a_f": a_f}


def summarise(rows, pair_ids, rng):
    s = stats(rows)
    pairs = sorted(set(pair_ids))
    pidx = {p: i for i, p in enumerate(pairs)}
    member = np.array([pidx[p] for p in pair_ids])
    counts = np.zeros((B, len(pairs)))
    draws = rng.integers(0, len(pairs), size=(B, len(pairs)))
    for b in range(B):
        counts[b] = np.bincount(draws[b], minlength=len(pairs))
    W = counts[:, member]                                     # item weights per resample

    def est(vals, mask=None):
        m = np.ones(len(vals), bool) if mask is None else mask
        v = vals.astype(float) * m
        point = float(v.sum() / max(m.sum(), 1))
        boots = (W * v).sum(1) / np.maximum((W * m).sum(1), 1)
        return {"estimate": point, "ci95": [float(np.percentile(boots, 2.5)), float(np.percentile(boots, 97.5))],
                "n": int(m.sum())}

    w = s["wrong"]
    # independence baseline for covariance: P(a_f = sigma(a_o)) if a_f ~ its marginal among wrong items
    mf = Counter(s["a_f"][w].tolist())
    mo = Counter(s["sig_a_o"][w].tolist())
    nw = max(int(w.sum()), 1)
    baseline = sum(mo[k] / nw * mf[k] / nw for k in mo)
    gain = s["sym_acc_orig"].astype(float) - s["acc_orig"]
    return {
        "accuracy_orig": est(s["acc_orig"]), "accuracy_flip": est(s["acc_flip"]),
        "symmetry_consistency": est(s["consistent"]),
        "covariant_error_share": est(s["consistent"], w), "covariant_independence_baseline": baseline,
        "symmetrised_accuracy_orig": est(s["sym_acc_orig"]), "symmetrised_accuracy_flip": est(s["sym_acc_flip"]),
        "symmetrisation_gain_orig": est(gain),
    }


def main():
    rng = np.random.default_rng(0)
    probes = load(RES / "negation_probes.jsonl")
    results = {}
    for name, stored in MODELS.items():
        orig = load(ROOT / f"results/predictions/{stored}/test.jsonl")
        flip = load(RES / f"predictions/pilot2__{name}.jsonl")
        rows, pids, ops = [], [], []
        for i, pr in probes.items():
            rows.append({"gold": pr["orig_label"], "gold_f": pr["label"],
                         "p_o": [orig[i]["probs"][l] for l in LABELS], "p_f": [flip[i]["probs"][l] for l in LABELS]})
            pids.append(pr["pair_id"])
            ops.append(pr["operator"])
        res = {"all": summarise(rows, pids, rng)}
        for fam in ("enrollment", "research_funding"):
            sel = [k for k, i in enumerate(probes) if probes[i]["family"] == fam]
            res[fam] = summarise([rows[k] for k in sel], [pids[k] for k in sel], rng)
        res["by_operator"] = {}
        for op in sorted(set(ops)):
            sel = [k for k, o in enumerate(ops) if o == op]
            s = stats([rows[k] for k in sel])
            res["by_operator"][op] = {"n": len(sel), "acc_orig": float(s["acc_orig"].mean()),
                                      "acc_flip": float(s["acc_flip"].mean()),
                                      "consistency": float(s["consistent"].mean()),
                                      "covariant_share": float(s["consistent"][s["wrong"]].mean()) if s["wrong"].any()
                                      else None, "n_wrong": int(s["wrong"].sum())}
        a = res["all"]
        ft = name.startswith("ft_")
        res["verdict"] = {
            "H_prog": bool(a["covariant_error_share"]["estimate"] >= 0.70 and
                           abs(a["symmetrisation_gain_orig"]["estimate"]) < 0.02) if ft else None,
            "H_noise": bool(a["covariant_error_share"]["estimate"] < 0.50 and
                            a["symmetrisation_gain_orig"]["estimate"] >= 0.03),
        }
        results[name] = res
    json.dump(results, open(RES / "pilot2_results.json", "w", newline="\n"), indent=2)

    f = lambda d: f"{d['estimate']:.3f} [{d['ci95'][0]:.3f}, {d['ci95'][1]:.3f}]"  # noqa: E731
    L = ["# Pilot 2 tables (generated by `project_anomaly/scripts/analyze_pilot2.py`)", "",
         "Test split (2,560 items) and the same items with the claim negated. 95% cluster-bootstrap CIs over minimal "
         "pairs. Covariant share = among items wrong on the original, the share whose negated-claim prediction is "
         "σ(original prediction); baseline = the same share expected if the two predictions were independent.", "",
         "| Model | Acc. original | Acc. negated | Symmetry consistency | Covariant error share (n wrong) | "
         "Independence baseline | Symmetrised acc. | Gain | H_prog | H_noise |", "|" + "---|" * 10]
    for name, r in results.items():
        a = r["all"]
        L.append(f"| {name} | {f(a['accuracy_orig'])} | {f(a['accuracy_flip'])} | {f(a['symmetry_consistency'])} | "
                 f"{f(a['covariant_error_share'])} (n={a['covariant_error_share']['n']}) | "
                 f"{a['covariant_independence_baseline']:.3f} | {f(a['symmetrised_accuracy_orig'])} | "
                 f"{f(a['symmetrisation_gain_orig'])} | {r['verdict']['H_prog']} | {r['verdict']['H_noise']} |")
    L += ["", "## By family", "", "| Model | Family | Acc. original | Acc. negated | Consistency | Covariant share | Gain |",
          "|" + "---|" * 7]
    for name, r in results.items():
        for fam in ("enrollment", "research_funding"):
            a = r[fam]
            L.append(f"| {name} | {fam} | {a['accuracy_orig']['estimate']:.3f} | {a['accuracy_flip']['estimate']:.3f} | "
                     f"{a['symmetry_consistency']['estimate']:.3f} | {a['covariant_error_share']['estimate']:.3f} | "
                     f"{a['symmetrisation_gain_orig']['estimate']:+.3f} |")
    L += ["", "## By operator (point estimates)", "", "| Model | Operator | n | Acc. orig | Acc. negated | Consistency | "
          "Covariant share (n wrong) |", "|" + "---|" * 7]
    for name, r in results.items():
        for op, o in r["by_operator"].items():
            cs = "–" if o["covariant_share"] is None else f"{o['covariant_share']:.2f}"
            L.append(f"| {name} | {op} | {o['n']} | {o['acc_orig']:.2f} | {o['acc_flip']:.2f} | {o['consistency']:.2f} | "
                     f"{cs} ({o['n_wrong']}) |")
    (RES / "PILOT2_TABLES.md").write_text("\n".join(L) + "\n")
    print("\n".join(L[:14]))


if __name__ == "__main__":
    main()
