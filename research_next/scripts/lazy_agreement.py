"""Item-level agreement between each saved system and the lazy reader (Pilot 1, exploratory)."""
import json, sys, re, collections
from pathlib import Path
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src")); sys.path.insert(0, str(Path(__file__).parent))
import numpy as np
from clauseshift.data import load
from lazy_reader import lazy_predict  # noqa: E402  (module runs its own evaluation on import)

test = load("test", ROOT / "data")
lazy = {i["id"]: lazy_predict(i["sentences"], i["hypothesis"]) for i in test}
L = ["| System | Agreement with lazy reader | Cohen's κ | Accuracy | Accuracy of lazy reader on same items |", "|---|---|---|---|---|"]
res = {}
for d in sorted((ROOT / "results/predictions").iterdir()):
    if not (d / "test.jsonl").exists(): continue
    P = {r["id"]: r["pred"] for r in map(json.loads, open(d / "test.jsonl"))}
    a = np.array([P[i["id"]] == lazy[i["id"]] for i in test], float)
    labs = ("entailed", "contradicted", "insufficient")
    pe = sum(np.mean([P[i["id"]] == l for i in test]) * np.mean([lazy[i["id"]] == l for i in test]) for l in labs)
    k = (a.mean() - pe) / (1 - pe)
    acc = np.mean([P[i["id"]] == i["label"] for i in test])
    res[d.name] = {"agreement": float(a.mean()), "kappa": float(k), "accuracy": float(acc)}
    L.append(f"| {d.name} | {a.mean():.3f} | {k:.3f} | {acc:.3f} | {np.mean([lazy[i['id']] == i['label'] for i in test]):.3f} |")
(ROOT / "research_next/results/lazy_agreement.json").write_text(json.dumps(res, indent=1))
print("\n".join(L))
