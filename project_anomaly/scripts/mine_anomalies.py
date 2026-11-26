"""Anomaly A1 (ANOMALY_LOG.md): accuracy of zero-shot models on lazy-right vs condition-dependent items, by format.
Reads only saved predictions. Output: project_anomaly/results/a1_format_decomposition.json"""
import contextlib, io, json, sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src")); sys.path.insert(0, str(ROOT / "research_next/scripts"))
from clauseshift.data import load  # noqa: E402
with contextlib.redirect_stdout(io.StringIO()):
    from lazy_reader import lazy_predict  # noqa: E402
test = load("test", ROOT / "data")
lazy = {i["id"]: lazy_predict(i["sentences"], i["hypothesis"]) for i in test}
SL = [i for i in test if lazy[i["id"]] == i["label"]]
SN = [i for i in test if lazy[i["id"]] != i["label"]]
res = {"n_lazy_right": len(SL), "n_condition_dependent": len(SN), "models": {}}
for m in ["nli-deberta-v3-xsmall", "nli-deberta-v3-base", "DeBERTa-v3-base-mnli-fever-anli", "roberta-large-mnli"]:
    for fmt in ("", "_factsinpremise"):
        s = f"zeroshot_{m}{fmt}"
        p = {json.loads(l)["id"]: json.loads(l)["pred"] for l in open(ROOT / "results/predictions" / s / "test.jsonl")}
        acc = lambda S: sum(p[i["id"]] == i["label"] for i in S) / len(S)  # noqa: E731
        res["models"][s] = {"accuracy": acc(test), "lazy_right": acc(SL), "condition_dependent": acc(SN)}
out = ROOT / "project_anomaly/results/a1_format_decomposition.json"
out.write_text(json.dumps(res, indent=1)); print(json.dumps(res, indent=1))
