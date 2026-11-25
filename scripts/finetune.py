"""Fine-tune a compact NLI cross-encoder on ClauseShift (CPU).

Training conditions (docs/PREREGISTRATION.md):
  paired     1,200 complete minimal pairs (2,400 items)
  unpaired   one random side of each of 2,400 pairs (2,400 items)
  full       all training items (4,800)
  op_holdout all training pairs except the held-out operators (default: xref_redirect, date_cross)

Epoch selection uses dev macro-F1 only; the selected model is then applied once to dev and test.
"""

import argparse
import copy
import json
import random
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

import numpy as np  # noqa: E402
import torch  # noqa: E402
from huggingface_hub import HfApi  # noqa: E402
from transformers import AutoModelForSequenceClassification, AutoTokenizer, get_linear_schedule_with_warmup  # noqa: E402

from clauseshift.data import load  # noqa: E402
from clauseshift.generator import LABELS  # noqa: E402
from clauseshift.metrics import macro_f1  # noqa: E402
from clauseshift.nli import NAME_MAP, evidence_hit_rate, label_mapping, predict_probs  # noqa: E402
from clauseshift.predictions import save_predictions  # noqa: E402


def select_training_items(train: list[dict], condition: str, seed: int, holdout: list[str]) -> list[dict]:
    rng = random.Random(seed)
    pairs = {}
    for it in train:
        pairs.setdefault(it["pair_id"], {})[it["side"]] = it
    pair_ids = sorted(pairs)
    if condition == "full":
        return list(train)
    if condition == "paired":
        chosen = rng.sample(pair_ids, len(pair_ids) // 2)
        return [pairs[p][s] for p in chosen for s in ("A", "B")]
    if condition == "unpaired":
        return [pairs[p][rng.choice("AB")] for p in pair_ids]
    if condition == "op_holdout":
        return [it for it in train if it["operator"] not in holdout]
    raise ValueError(condition)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", default="cross-encoder/nli-deberta-v3-xsmall")
    ap.add_argument("--condition", default="paired", choices=["paired", "unpaired", "full", "op_holdout"])
    ap.add_argument("--holdout", nargs="+", default=["xref_redirect", "date_cross"])
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--epochs", type=int, default=3)
    ap.add_argument("--lr", type=float, default=3e-5)
    ap.add_argument("--batch-size", type=int, default=16)
    ap.add_argument("--max-length", type=int, default=320)
    ap.add_argument("--max-steps", type=int, default=None, help="smoke tests only")
    ap.add_argument("--tag", default="")
    args = ap.parse_args()

    torch.set_num_threads(12)
    random.seed(args.seed)
    np.random.seed(args.seed)
    torch.manual_seed(args.seed)

    revision = HfApi().model_info(args.model).sha
    tok = AutoTokenizer.from_pretrained(args.model, revision=revision)
    model = AutoModelForSequenceClassification.from_pretrained(args.model, revision=revision)
    if model.config.num_labels != 3 or any(n.lower() not in NAME_MAP for n in model.config.id2label.values()):
        model = AutoModelForSequenceClassification.from_pretrained(
            args.model, revision=revision, num_labels=3, id2label=dict(enumerate(LABELS)),
            label2id={lab: i for i, lab in enumerate(LABELS)}, ignore_mismatched_sizes=True)
    to_index = {lab: i for i, lab in label_mapping(model).items()}

    train_items = select_training_items(load("train"), args.condition, args.seed, args.holdout)
    dev, test = load("dev"), load("test")
    system = f"ft_{args.model.split('/')[-1]}_{args.condition}_s{args.seed}{args.tag}"
    out_dir = Path("results/predictions") / system
    out_dir.mkdir(parents=True, exist_ok=True)

    steps_per_epoch = (len(train_items) + args.batch_size - 1) // args.batch_size
    total = min(args.max_steps or 10**9, steps_per_epoch * args.epochs)
    opt = torch.optim.AdamW(model.parameters(), lr=args.lr, weight_decay=0.01)
    sched = get_linear_schedule_with_warmup(opt, int(0.1 * total), total)

    log, best, step, t0 = [], None, 0, time.time()
    for epoch in range(args.epochs):
        model.train()
        order = list(range(len(train_items)))
        random.shuffle(order)
        losses = []
        for b in range(0, len(order), args.batch_size):
            batch = [train_items[i] for i in order[b:b + args.batch_size]]
            enc = tok([i["premise"] for i in batch], [i["hypothesis"] for i in batch], truncation="only_first",
                      max_length=args.max_length, padding=True, return_tensors="pt")
            labels = torch.tensor([to_index[i["label"]] for i in batch])
            loss = model(**enc, labels=labels).loss
            loss.backward()
            torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0)
            opt.step()
            sched.step()
            opt.zero_grad()
            losses.append(loss.item())
            step += 1
            if step % 50 == 0:
                print(f"epoch {epoch} step {step}/{total} loss {np.mean(losses[-50:]):.4f} "
                      f"{time.time() - t0:.0f}s", flush=True)
            if step >= total:
                break
        model.eval()
        dev_probs = predict_probs(tok, model, [i["premise"] for i in dev], [i["hypothesis"] for i in dev])
        dev_f1 = macro_f1([i["label"] for i in dev], [max(p, key=p.get) for p in dev_probs])
        log.append({"epoch": epoch, "train_loss": float(np.mean(losses)), "dev_macro_f1": dev_f1,
                    "seconds": round(time.time() - t0, 1)})
        print(json.dumps(log[-1]), flush=True)
        if best is None or dev_f1 > best[0]:
            best = (dev_f1, epoch, copy.deepcopy(model.state_dict()))
        if step >= total:
            break

    model.load_state_dict(best[2])
    model.eval()
    meta = {"model": args.model, "revision": revision, "condition": args.condition, "seed": args.seed,
            "holdout_operators": args.holdout if args.condition == "op_holdout" else None,
            "train_items": len(train_items), "train_pairs_complete": len({i["pair_id"] for i in train_items})
            if args.condition != "unpaired" else 0, "epochs": args.epochs, "lr": args.lr,
            "batch_size": args.batch_size, "max_length": args.max_length, "selected_epoch": best[1],
            "selected_dev_macro_f1": best[0], "log": log, "torch": torch.__version__,
            "hardware": "CPU, AMD Ryzen 5 4600H, 12 threads", "smoke_test": args.max_steps is not None}
    for split, items in (("dev", dev), ("test", test)):
        probs = predict_probs(tok, model, [i["premise"] for i in items], [i["hypothesis"] for i in items])
        if split == "test" and args.max_steps is None:
            preds = {i["id"]: max(p, key=p.get) for i, p in zip(items, probs)}
            meta["evidence_test"] = evidence_hit_rate(tok, model, items, preds)
        save_predictions(system, split, items, probs, meta=meta)
    print("done", system, f"{time.time() - t0:.0f}s")


if __name__ == "__main__":
    main()
