"""Pilot 1: a "lazy reader" that ignores every condition, evaluated with the registered metrics.

The reader uses only the text: it predicts `insufficient` if no sentence of the document states the claimed
obligation; otherwise "required" (or "not required" if that sentence negates the obligation), mapped through the
claim polarity. Exemptions, thresholds, dates, scopes and cross-references are never read.

Outputs research_next/results/lazy_reader.json. Predictions fixed in research_next/PILOT_PLAN.md (Pilot 1).
"""

import collections
import json
import random
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

import numpy as np  # noqa: E402

from clauseshift.data import load  # noqa: E402
from clauseshift.evidence import expected_label_after_removal, removal_is_well_posed, removal_type  # noqa: E402
from clauseshift.metrics import breakdown, group_pairs, pair_metrics  # noqa: E402

CLAIM = re.compile(r"(?:is required to|must|has an obligation to|is not required to|does not have to|"
                   r"has no obligation to) (?P<ob>.+)\.$")
NEG_CLAIM = re.compile(r"is not required to|does not have to|has no obligation to")
NEG_OB = re.compile(r"\bnot required to\b|^No \w.* is obliged to|\bneed not\b|There is no obligation for")


def lazy_predict(doc_sentences: list[str], hypothesis: str) -> str:
    claim = re.split(r"(?<=\.) ", hypothesis)[-1]
    ob = CLAIM.search(claim).group("ob")
    stating = [s for s in doc_sentences if ob in s]
    if not stating:
        return "insufficient"
    required = not any(NEG_OB.search(s) for s in stating)
    positive_claim = not NEG_CLAIM.search(claim)
    return "entailed" if required == positive_claim else "contradicted"


def onehot(lab: str) -> dict:
    return {l: float(l == lab) for l in ("entailed", "contradicted", "insufficient")}


test = load("test", ROOT / "data")
preds = {i["id"]: lazy_predict(i["sentences"], i["hypothesis"]) for i in test}
pairs = group_pairs(test, preds)
m = pair_metrics(pairs)
by_op = {k: v.get("flip_accuracy") for k, v in breakdown(pairs, "operator").items() if "flip_accuracy" in v}

# registered occlusion protocol: same eligibility rule and sample (random.Random(0).sample of 300)
eligible = [i for i in test if i["label"] != "insufficient" and preds[i["id"]] == i["label"] and i["evidence"]]
sample = random.Random(0).sample(eligible, min(300, len(eligible)))
hits, roles, cf = [], collections.Counter(), collections.defaultdict(list)
for it in sample:
    p_removed = []
    pred_removed = []
    for k in range(len(it["sentences"])):
        kept = [s for j, s in enumerate(it["sentences"]) if j != k]
        lab = lazy_predict(kept, it["hypothesis"])
        p_removed.append(onehot(lab)[it["label"]])
        pred_removed.append(lab)
    top = min(range(len(p_removed)), key=lambda j: p_removed[j])
    hits.append(top in it["evidence"])
    roles[it["sentence_roles"][top]] += 1
    if removal_is_well_posed(it):
        for k in range(len(it["sentences"])):
            cf[removal_type(it, k)].append(pred_removed[k] == expected_label_after_removal(it, k))

res = {"accuracy": m["accuracy"], "pair_accuracy": m["pair_accuracy"], "flip_accuracy": m["flip_accuracy"],
       "flip_accuracy_by_operator": by_op, "evidence_sample": len(sample), "eligible": len(eligible),
       "hit_at_1": float(np.mean(hits)), "top_sentence_roles": dict(roles),
       "counterfactual_removal": {t: {"agreement": float(np.mean(v)), "n": len(v)} for t, v in cf.items()}}
out = ROOT / "research_next" / "results" / "lazy_reader.json"
out.write_text(json.dumps(res, indent=1), encoding="utf-8")
print(json.dumps(res, indent=1))
