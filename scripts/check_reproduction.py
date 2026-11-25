"""Re-run one stored zero-shot system on dev and compare with the saved predictions (nothing is overwritten).

Writes results/reproduction_check.json: label agreement and maximum absolute probability difference.
"""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

import torch  # noqa: E402

from clauseshift.data import load  # noqa: E402
from clauseshift.nli import load as load_model  # noqa: E402
from clauseshift.nli import predict_probs  # noqa: E402
from clauseshift.predictions import ROOT, load_predictions  # noqa: E402
from clauseshift.runtime import hardware_string, num_threads  # noqa: E402

SYSTEM = sys.argv[1] if len(sys.argv) > 1 else "zeroshot_nli-deberta-v3-xsmall"
torch.set_num_threads(num_threads())
meta = json.loads((ROOT / SYSTEM / "meta.json").read_text())
tok, model = load_model(meta["model"], meta["revision"])
dev = load("dev")
probs = predict_probs(tok, model, [i["premise"] for i in dev], [i["hypothesis"] for i in dev])
stored = load_predictions(SYSTEM, "dev")
agree = sum(max(p, key=p.get) == stored[i["id"]]["pred"] for i, p in zip(dev, probs)) / len(dev)
max_diff = max(abs(p[k] - stored[i["id"]]["probs"][k]) for i, p in zip(dev, probs) for k in p)
out = {"system": SYSTEM, "split": "dev", "items": len(dev), "label_agreement": agree, "max_abs_prob_diff": max_diff,
       "stored_hardware": meta.get("hardware"), "rerun_hardware": hardware_string(num_threads()),
       "torch": torch.__version__}
Path("results/reproduction_check.json").write_text(json.dumps(out, indent=2), encoding="utf-8")
print(json.dumps(out, indent=2))
