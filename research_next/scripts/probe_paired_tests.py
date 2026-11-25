"""Paired (within-case) comparisons on the Pilot-2 probes for the re-trained checkpoints (exploratory).

For each checkpoint and family: among base cases answered correctly, the difference between the false-flip rate on
xref_other_art1 and on inline_other (same base case, so the comparison is paired), with a 95% bootstrap interval over
base cases. Also paired vs. unpaired training on xref_other_art1 false flips (different models, same cases).
Per-item predictions are saved to research_next/results/probe_item_predictions.jsonl.
"""
import json, sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))
import numpy as np, torch
from clauseshift.nli import load as load_model, predict_probs
from clauseshift.runtime import num_threads
torch.set_num_threads(num_threads())
FILES = {"vehicles": "probes_xref.jsonl", "enrollment": "probes_xref_enrollment.jsonl",
         "research_funding": "probes_xref_research_funding.jsonl"}
probes = [dict(json.loads(l), family=f) for f, fn in FILES.items() for l in open(ROOT / "research_next/results" / fn)]
out_items = ROOT / "research_next/results/probe_item_predictions.jsonl"
preds = {}
if out_items.exists():
    for r in map(json.loads, open(out_items)):
        preds[(r["model"], r["family"], r["case_id"], r["variant"])] = r["pred"]
models = sorted(d.name for d in (ROOT / "checkpoints").iterdir())
for m in models:
    if any(k[0] == m for k in preds):
        continue
    tok, model = load_model(str(ROOT / "checkpoints" / m))
    pr = predict_probs(tok, model, [p["premise"] for p in probes], [p["hypothesis"] for p in probes])
    with open(out_items, "a") as f:
        for p, q in zip(probes, pr):
            lab = max(q, key=q.get)
            preds[(m, p["family"], p["case_id"], p["variant"])] = lab
            f.write(json.dumps({"model": m, "family": p["family"], "case_id": p["case_id"], "variant": p["variant"],
                                "pred": lab, "gold": p["label"]}) + "\n")
    print(m, "done", flush=True)
gold = {(p["family"], p["case_id"], p["variant"]): p["label"] for p in probes}
rng = np.random.default_rng(0)
def boot(x):
    bs = [x[rng.integers(0, len(x), len(x))].mean() for _ in range(5000)]
    return float(x.mean()), float(np.percentile(bs, 2.5)), float(np.percentile(bs, 97.5))
res, L = {}, ["| Model | Family | ff xref_other − ff inline_other (paired over cases) | n cases |", "|---|---|---|---|"]
for m in models:
    for fam in FILES:
        cases = sorted({p["case_id"] for p in probes if p["family"] == fam})
        ok = [c for c in cases if preds[(m, fam, c, "base")] == gold[(fam, c, "base")]]
        d = np.array([float(preds[(m, fam, c, "xref_other_art1")] != preds[(m, fam, c, "base")]) -
                      float(preds[(m, fam, c, "inline_other")] != preds[(m, fam, c, "base")]) for c in ok])
        res[f"{m}|{fam}|xref_minus_inline"] = boot(d)
        t = res[f"{m}|{fam}|xref_minus_inline"]
        L.append(f"| {m} | {fam} | {t[0]:+.3f} [{t[1]:+.3f}, {t[2]:+.3f}] | {len(ok)} |")
L += ["", "| Initialisation | Family | ff xref_other: paired − unpaired (cases correct on base for both) |", "|---|---|---|"]
for init in ("ft_nli-deberta-v3-xsmall", "ft_deberta-v3-xsmall"):
    for fam in FILES:
        cases = sorted({p["case_id"] for p in probes if p["family"] == fam})
        a, b = f"{init}_paired_s0", f"{init}_unpaired_s0"
        ok = [c for c in cases if preds[(a, fam, c, "base")] == gold[(fam, c, "base")] == preds[(b, fam, c, "base")]]
        d = np.array([float(preds[(a, fam, c, "xref_other_art1")] != preds[(a, fam, c, "base")]) -
                      float(preds[(b, fam, c, "xref_other_art1")] != preds[(b, fam, c, "base")]) for c in ok])
        t = boot(d); res[f"{init}|{fam}|paired_minus_unpaired"] = t
        L.append(f"| {init} | {fam} | {t[0]:+.3f} [{t[1]:+.3f}, {t[2]:+.3f}] (n={len(ok)}) |")
(ROOT / "research_next/results/probe_paired_tests.json").write_text(json.dumps(res, indent=1))
(ROOT / "research_next/results/PROBE_PAIRED_TESTS.md").write_text("\n".join(L) + "\n")
print("\n".join(L))
