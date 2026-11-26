"""Run the pilot models on a JSONL item file and save raw probabilities (one JSONL per model).

Usage: python project_anomaly/scripts/run_models.py ITEMS.jsonl OUT_PREFIX [--zero-shot]
Models: the four local checkpoints that reproduce registered seed-0 runs (checkpoints/ is gitignored), and with
--zero-shot also the two zero-shot DeBERTa-v3-base NLI models used in the registered study.
"""

import json
import sys
import time
from pathlib import Path

import torch

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))
from clauseshift.nli import load, predict_probs  # noqa: E402
from clauseshift.runtime import hardware_string, num_threads  # noqa: E402

CHECKPOINTS = ["ft_nli-deberta-v3-xsmall_paired_s0", "ft_nli-deberta-v3-xsmall_unpaired_s0",
               "ft_deberta-v3-xsmall_paired_s0", "ft_deberta-v3-xsmall_unpaired_s0"]
ZERO_SHOT = {"zs_deberta-v3-base-nli": "zeroshot_nli-deberta-v3-base",
             "zs_deberta-v3-base-mnli-fever-anli": "zeroshot_DeBERTa-v3-base-mnli-fever-anli"}  # revisions pinned


def zero_shot_source(stored: str) -> tuple[str, str]:
    meta = json.load(open(ROOT / "results/predictions" / stored / "meta.json"))
    return meta["model"], meta["revision"]


def main():
    items_path, prefix = Path(sys.argv[1]).resolve(), sys.argv[2]
    torch.set_num_threads(num_threads())
    items = [json.loads(line) for line in open(items_path)]
    models = {c: (str(ROOT / "checkpoints" / c), None) for c in CHECKPOINTS}
    if "--zero-shot" in sys.argv:
        models.update({k: zero_shot_source(v) for k, v in ZERO_SHOT.items()})
    out_dir = ROOT / "project_anomaly/results/predictions"
    out_dir.mkdir(parents=True, exist_ok=True)
    log = {"hardware": hardware_string(num_threads()), "items": str(items_path.relative_to(ROOT)), "n": len(items), "models": {}}
    for name, (path, revision) in models.items():
        t0 = time.time()
        tok, model = load(path, revision=revision)
        probs = predict_probs(tok, model, [r["premise"] for r in items], [r["hypothesis"] for r in items])
        with open(out_dir / f"{prefix}__{name}.jsonl", "w", newline="\n") as f:
            for r, p in zip(items, probs):
                f.write(json.dumps({"id": r["id"], "probs": {k: round(v, 6) for k, v in p.items()},
                                    "pred": max(p, key=p.get)}) + "\n")
        log["models"][name] = {"source": path if not path.startswith(str(ROOT)) else f"checkpoints/{name}",
                               "revision": revision,
                               "seconds": round(time.time() - t0, 1)}
        print(name, log["models"][name]["seconds"], "s", flush=True)
    with open(out_dir / f"{prefix}__runlog.json", "w", newline="\n") as f:
        json.dump(log, f, indent=2)


if __name__ == "__main__":
    main()
