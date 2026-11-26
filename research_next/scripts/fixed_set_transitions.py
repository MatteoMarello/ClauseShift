"""Pilot 4 (exploratory): expected-label-transition test on one fixed item set for every system.

Fixes the conceptual problem found in the audit: the original counterfactual removal test was computed on each
model's correctly answered items, so weak models (and the lazy reader) contributed few or no decisive removals.
Here a single stratified sample of well-posed, decided test items (no cross-reference) is used for all systems.

For each item and each sentence k, the input is the remaining sentences joined (as in the registered occlusion
protocol); the expected label is `expected_label_after_removal`. Reported per removal type (obligation / decisive /
non-decisive):
  - v1 "single-input" agreement: prediction after removal == expected label (kept for transparency: the lazy reader
    scores 1.00 on decisive removals under it, because it never needed to change its answer);
  - v2 "joint" (transition) accuracy: prediction on the full header-free document == gold label AND prediction after
    removal == expected label. Only v2 credits a model for getting the *change* right.
Also reported: the registered-style hit@1 on the same items.
"""

import collections
import contextlib
import io
import json
import random
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(Path(__file__).parent))

import numpy as np  # noqa: E402
import torch  # noqa: E402

from clauseshift.data import load  # noqa: E402
from clauseshift.evidence import expected_label_after_removal, removal_is_well_posed, removal_type  # noqa: E402
from clauseshift.nli import load as load_model  # noqa: E402
from clauseshift.nli import predict_probs  # noqa: E402
from clauseshift.runtime import num_threads  # noqa: E402

with contextlib.redirect_stdout(io.StringIO()):
    from lazy_reader import lazy_predict  # noqa: E402

torch.set_num_threads(num_threads())
test = load("test", ROOT / "data")
pool = collections.defaultdict(list)
for it in test:
    if removal_is_well_posed(it) and it["operator_class"] == "flip":
        pool[it["operator"]].append(it)
rng = random.Random(20261126)
items = [x for op in sorted(pool) for x in rng.sample(pool[op], min(25, len(pool[op])))]
variants = [(it, k, " ".join(s for j, s in enumerate(it["sentences"]) if j != k))
            for it in items for k in range(len(it["sentences"]))]
full = [(it, -1, " ".join(it["sentences"])) for it in items]


def evaluate(predict) -> dict:
    """predict(list_of_(premise, hypothesis, sentences)) -> list of label-probability dicts."""
    probs = predict([(v[2], v[0]["hypothesis"], [s for j, s in enumerate(v[0]["sentences"]) if j != v[1]])
                     for v in variants])
    pf = predict([(v[2], v[0]["hypothesis"], v[0]["sentences"]) for v in full])
    full_ok = {it["id"]: max(p, key=p.get) == it["label"] for (it, _, _), p in zip(full, pf)}
    joint = collections.defaultdict(list)
    agree = collections.defaultdict(list)
    by_item = collections.defaultdict(list)
    for (it, k, _), p in zip(variants, probs):
        pred = max(p, key=p.get)
        t = removal_type(it, k)
        agree[t].append(pred == expected_label_after_removal(it, k))
        joint[t].append(full_ok[it["id"]] and pred == expected_label_after_removal(it, k))
        by_item[it["id"]].append((k, p[it["label"]]))
    hit = [min(v, key=lambda x: x[1])[0] in next(i for i in items if i["id"] == iid)["evidence"]
           for iid, v in by_item.items()]
    return {**{t: {"agreement": float(np.mean(v)), "joint": float(np.mean(joint[t])), "n": len(v)}
               for t, v in agree.items()}, "full_doc_accuracy": float(np.mean(list(full_ok.values()))),
            "hit_at_1_fixed_set": float(np.mean(hit)), "items": len(items)}


def lazy(batch):
    return [{l: float(l == lazy_predict(sents, h)) for l in ("entailed", "contradicted", "insufficient")}
            for _, h, sents in batch]


def neural(path, revision=None):
    tok, model = load_model(path, revision)
    return lambda batch: predict_probs(tok, model, [b[0] for b in batch], [b[1] for b in batch])


res = {"lazy_reader": evaluate(lazy)}
for d in sorted((ROOT / "checkpoints").iterdir()):
    res[d.name] = evaluate(neural(str(d)))
    print(d.name, res[d.name], flush=True)
for s in ("zeroshot_nli-deberta-v3-base", "zeroshot_DeBERTa-v3-base-mnli-fever-anli"):
    meta = json.loads((ROOT / "results/predictions" / s / "meta.json").read_text())
    res[s] = evaluate(neural(meta["model"], meta["revision"]))
    print(s, res[s], flush=True)
(ROOT / "research_next/results/fixed_set_transitions.json").write_text(json.dumps(res, indent=1))
L = [f"Fixed item set: {len(items)} decided, well-posed flip-operator test items (25 per operator, no cross-reference), "
     f"{len(variants)} sentence removals. Cells: v2 joint transition accuracy (correct on the full header-free document "
     "AND on the shortened one); in brackets v1 single-input agreement (shortened document only).", "",
     "| System | Full-doc acc. | Obligation removed → insufficient | Decisive removed → expected change | Non-decisive removed → kept | hit@1 |",
     "|---|---|---|---|---|---|"]
for s_, r in res.items():
    c = lambda t: f"{r[t]['joint']:.3f} ({r[t]['agreement']:.3f}; n={r[t]['n']})" if t in r else "–"  # noqa: E731
    L.append(f"| {s_} | {r['full_doc_accuracy']:.3f} | {c('obligation')} | {c('decisive')} | {c('non_decisive')} | "
             f"{r['hit_at_1_fixed_set']:.3f} |")
(ROOT / "research_next/results/FIXED_SET_TRANSITIONS.md").write_text("\n".join(L) + "\n")
print("\n".join(L))
