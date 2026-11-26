"""Pilot 2 evaluation: cross-reference / inline-exemption probes (see research_next/PILOT_PLAN.md).

Evaluates locally saved re-trained checkpoints (checkpoints/, never committed), the four zero-shot models and the
lazy reader on research_next/results/probes_xref.jsonl. Also checks that each re-trained run reproduces the stored
test predictions of the same registered configuration.

Primary quantity: false-flip rate = among base cases answered correctly on `base`, the share whose prediction changes
when a label-preserving sentence is added (`xref_other_art1`, `xref_case_art2`, `inline_other`). For label-changing
variants (`xref_case_art1`, `inline_case`) we report accuracy. 95% bootstrap intervals over base cases.
"""

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(Path(__file__).parent))

import numpy as np  # noqa: E402
import torch  # noqa: E402

from clauseshift.nli import load as load_model  # noqa: E402
from clauseshift.nli import predict_probs  # noqa: E402
from clauseshift.runtime import num_threads  # noqa: E402

torch.set_num_threads(num_threads())
RNG = np.random.default_rng(0)
FILES = {"vehicles": "probes_xref.jsonl", "enrollment": "probes_xref_enrollment.jsonl",
         "research_funding": "probes_xref_research_funding.jsonl"}   # test families added post hoc (PILOT_RESULTS.md)
ALL = {fam: [json.loads(l) for l in open(ROOT / "research_next/results" / fn)] for fam, fn in FILES.items()}
probes = [dict(p, case_id=f"{fam}-{p['case_id']}") for fam, ps in ALL.items() for p in ps]
VARIANTS = ["base", "xref_case_art1", "xref_case_art2", "xref_other_art1", "inline_case", "inline_other"]
by = {(p["case_id"], p["variant"]): p for p in probes}


def summarize(preds: dict) -> dict:
    return {fam: summarize_family(preds, sorted({p["case_id"] for p in probes if p["family"] == fam})) for fam in FILES}


def summarize_family(preds: dict, CASES: list) -> dict:
    out = {}
    base_ok = np.array([preds[(c, "base")] == by[(c, "base")]["label"] for c in CASES])
    for v in VARIANTS:
        acc = np.array([preds[(c, v)] == by[(c, v)]["label"] for c in CASES], float)
        out[f"acc_{v}"] = acc
        if v in ("xref_case_art2", "xref_other_art1", "inline_other"):
            ff = np.array([preds[(c, v)] != preds[(c, "base")] for c in CASES], float)[base_ok]
            out[f"falseflip_{v}"] = ff
    res = {}
    for k, x in out.items():
        bs = [x[RNG.integers(0, len(x), len(x))].mean() for _ in range(2000)] if len(x) else [np.nan]
        res[k] = {"point": float(x.mean()) if len(x) else float("nan"), "lo": float(np.percentile(bs, 2.5)),
                  "hi": float(np.percentile(bs, 97.5)), "n": int(len(x))}
    return res


def model_preds(path_or_name: str, revision=None) -> dict:
    tok, model = load_model(path_or_name, revision)
    probs = predict_probs(tok, model, [p["premise"] for p in probes], [p["hypothesis"] for p in probes])
    return {(p["case_id"], p["variant"]): max(q, key=q.get) for p, q in zip(probes, probs)}


results = {}
# lazy reader (negative control: ignores every condition)
import contextlib, io  # noqa: E401,E402
with contextlib.redirect_stdout(io.StringIO()):
    from lazy_reader import lazy_predict  # noqa: E402
results["lazy_reader"] = summarize({(p["case_id"], p["variant"]): lazy_predict(p["sentences"], p["hypothesis"])
                                    for p in probes})

# re-trained checkpoints + reproduction check against the registered runs
ck = ROOT / "checkpoints"
repro = {}
for d in sorted(ck.iterdir()) if ck.exists() else []:
    results[d.name] = summarize(model_preds(str(d)))
    new = ROOT / "research_next/results/predictions" / d.name / "test.jsonl"
    old = ROOT / "results/predictions" / d.name / "test.jsonl"
    if new.exists() and old.exists():
        a = {r["id"]: r["pred"] for r in map(json.loads, open(new))}
        b = {r["id"]: r["pred"] for r in map(json.loads, open(old))}
        repro[d.name] = float(np.mean([a[k] == b[k] for k in b]))
    print(d.name, "done", flush=True)

# zero-shot models (standard format), pinned revisions from the stored meta files
for s in ("zeroshot_nli-deberta-v3-xsmall", "zeroshot_nli-deberta-v3-base", "zeroshot_DeBERTa-v3-base-mnli-fever-anli"):
    meta = json.loads((ROOT / "results/predictions" / s / "meta.json").read_text())
    results[s] = summarize(model_preds(meta["model"], meta["revision"]))
    print(s, "done", flush=True)

out = {"results": results, "reproduction_test_agreement": repro}
(ROOT / "research_next/results/probe_results.json").write_text(json.dumps(out, indent=1), encoding="utf-8")
L = []
f = lambda r: f"{r['point']:.2f} [{r['lo']:.2f}, {r['hi']:.2f}]"  # noqa: E731
for fam in FILES:
    L += [f"### {fam}" + (" (pre-specified)" if fam == "vehicles" else " (added after the vehicles results; exploratory)"), "",
          "| System | acc base | acc xref_case_art1 (flip) | acc inline_case (flip) | false flips: xref_other_art1 | "
          "false flips: inline_other | false flips: xref_case_art2 |", "|---|---|---|---|---|---|---|"]
    for s_, R in results.items():
        r = R[fam]
        L.append(f"| {s_} | {f(r['acc_base'])} | {f(r['acc_xref_case_art1'])} | {f(r['acc_inline_case'])} | "
                 f"{f(r['falseflip_xref_other_art1'])} | {f(r['falseflip_inline_other'])} | {f(r['falseflip_xref_case_art2'])} |")
    L.append("")
L += ["Reproduction (re-trained vs. stored test predictions, item agreement): " +
      ", ".join(f"{k}: {v:.4f}" for k, v in repro.items())]
(ROOT / "research_next/results/PROBE_TABLE.md").write_text("\n".join(L) + "\n", encoding="utf-8")
print("\n".join(L))
