"""Zero-shot predictions of the ClauseShift NLI models on the ScoNe-NLI test split (inference only, CPU).

Data: github.com/selenashe/ScoNe (CC0 1.0), cloned outside this repository; pass its path as the first argument.
3-way outputs are mapped to ScoNe's labels: entailment -> entailment; contradiction and neutral -> neutral.
Output: research_next/results/external/scone_predictions.jsonl
"""

import csv
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

import torch  # noqa: E402

from clauseshift.nli import load as load_model  # noqa: E402
from clauseshift.nli import predict_probs  # noqa: E402
from clauseshift.runtime import num_threads  # noqa: E402

SPLITS = ["no_negation", "one_not_scoped", "one_scoped", "one_scoped_one_not_scoped", "two_not_scoped", "two_scoped"]
scone = Path(sys.argv[1]) / "scone_nli" / "test"
items = []
for sp in SPLITS:
    for i, r in enumerate(csv.DictReader(open(scone / f"{sp}.csv"))):
        p = r.get("sentence1_edited") or r["sentence1"]
        h = r.get("sentence2_edited") or r["sentence2"]
        g = r.get("gold_label_edited") or r["gold_label"]
        items.append({"split": sp, "row": i, "premise": p, "hypothesis": h, "gold": g})
torch.set_num_threads(num_threads())
out = ROOT / "research_next/results/external/scone_predictions.jsonl"
out.parent.mkdir(parents=True, exist_ok=True)
with open(out, "w") as f:
    for s in ("zeroshot_nli-deberta-v3-xsmall", "zeroshot_nli-deberta-v3-base",
              "zeroshot_DeBERTa-v3-base-mnli-fever-anli", "zeroshot_roberta-large-mnli"):
        meta = json.loads((ROOT / "results/predictions" / s / "meta.json").read_text())
        tok, model = load_model(meta["model"], meta["revision"])
        probs = predict_probs(tok, model, [i["premise"] for i in items], [i["hypothesis"] for i in items])
        for it, p in zip(items, probs):
            lab = "entailment" if max(p, key=p.get) == "entailed" else "neutral"
            f.write(json.dumps({"model": s, "split": it["split"], "row": it["row"], "pred": lab}) + "\n")
        print(s, "done", flush=True)
