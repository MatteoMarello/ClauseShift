"""Zero-shot evaluation of off-the-shelf NLI cross-encoders on dev and test."""

import argparse
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

import torch  # noqa: E402
from huggingface_hub import HfApi  # noqa: E402

from clauseshift.data import load  # noqa: E402
from clauseshift.nli import label_mapping, predict_probs  # noqa: E402
from clauseshift.nli import load as load_model  # noqa: E402
from clauseshift.predictions import save_predictions  # noqa: E402

MODELS = ["cross-encoder/nli-deberta-v3-xsmall", "cross-encoder/nli-deberta-v3-base",
          "MoritzLaurer/DeBERTa-v3-base-mnli-fever-anli", "FacebookAI/roberta-large-mnli"]

ap = argparse.ArgumentParser()
ap.add_argument("--models", nargs="+", default=MODELS)
ap.add_argument("--splits", nargs="+", default=["dev", "test"])
args = ap.parse_args()
torch.set_num_threads(12)

for name in args.models:
    info = HfApi().model_info(name)
    tok, model = load_model(name, revision=info.sha)
    system = "zeroshot_" + name.split("/")[-1]
    for split in args.splits:
        items = load(split)
        t0 = time.time()
        probs = predict_probs(tok, model, [i["premise"] for i in items], [i["hypothesis"] for i in items])
        secs = time.time() - t0
        save_predictions(system, split, items, probs, meta={
            "model": name, "revision": info.sha, "license": (info.card_data or {}).get("license"),
            "label_mapping": label_mapping(model), "max_length": 384, "seconds_" + split: round(secs, 1),
            "hardware": "CPU, AMD Ryzen 5 4600H, 12 threads", "torch": torch.__version__})
        print(f"{system} {split}: {len(items)} items in {secs:.0f}s", flush=True)
