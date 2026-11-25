"""Occlusion evidence hit@1 for the zero-shot models (same fixed sample protocol as fine-tuning)."""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

import torch  # noqa: E402

from clauseshift.data import load  # noqa: E402
from clauseshift.nli import evidence_hit_rate  # noqa: E402
from clauseshift.nli import load as load_model  # noqa: E402
from clauseshift.predictions import ROOT, load_predictions  # noqa: E402

torch.set_num_threads(12)
test = load("test")
for d in sorted(ROOT.glob("zeroshot_*")):
    meta = json.loads((d / "meta.json").read_text())
    if "evidence_test" in meta:
        continue
    tok, model = load_model(meta["model"], meta["revision"])
    preds = {k: v["pred"] for k, v in load_predictions(d.name, "test").items()}
    meta["evidence_test"] = evidence_hit_rate(tok, model, test, preds)
    (d / "meta.json").write_text(json.dumps(meta, indent=2), encoding="utf-8")
    print(d.name, meta["evidence_test"], flush=True)
