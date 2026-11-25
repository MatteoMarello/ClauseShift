"""Transformer NLI inference: label mapping, batched prediction and occlusion-based evidence."""

from __future__ import annotations

import torch
from transformers import AutoModelForSequenceClassification, AutoTokenizer

from .generator import CONTRADICTED, ENTAILED, INSUFFICIENT

NAME_MAP = {"entailment": ENTAILED, "contradiction": CONTRADICTED, "neutral": INSUFFICIENT,
            ENTAILED: ENTAILED, CONTRADICTED: CONTRADICTED, INSUFFICIENT: INSUFFICIENT}


def label_mapping(model) -> dict[int, str]:
    return {i: NAME_MAP[name.lower()] for i, name in model.config.id2label.items()}


def load(name: str, revision: str | None = None):
    tok = AutoTokenizer.from_pretrained(name, revision=revision)
    model = AutoModelForSequenceClassification.from_pretrained(name, revision=revision).eval()
    return tok, model


@torch.no_grad()
def predict_probs(tok, model, premises: list[str], hypotheses: list[str], batch_size: int = 16,
                  max_length: int = 384) -> list[dict[str, float]]:
    mapping = label_mapping(model)
    out = []
    for i in range(0, len(premises), batch_size):
        enc = tok(premises[i:i + batch_size], hypotheses[i:i + batch_size], truncation="only_first",
                  max_length=max_length, padding=True, return_tensors="pt")
        probs = torch.softmax(model(**enc).logits.float(), dim=-1)
        out += [{mapping[j]: float(p[j]) for j in range(p.shape[0])} for p in probs]
    return out


def occlusion_scores(tok, model, item: dict, label: str) -> dict:
    """p(label) and predicted label for: the full document, the full document without "Article k." headers, and
    the document with each sentence removed.

    The removal variants are built (as preregistered) by joining the remaining sentences, which also drops the
    article headers; the header-free full document is the matching no-removal control.
    """
    variants = []
    for k in range(len(item["sentences"])):
        kept = [s for j, s in enumerate(item["sentences"]) if j != k]
        variants.append(" ".join(kept))
    texts = [item["premise"], " ".join(item["sentences"])] + variants
    probs = predict_probs(tok, model, texts, [item["hypothesis"]] * len(texts))
    arg = [max(p, key=p.get) for p in probs]
    return {"p_full": probs[0][label], "pred_full": arg[0], "p_full_noheaders": probs[1][label],
            "pred_full_noheaders": arg[1], "p_removed": [p[label] for p in probs[2:]], "pred_removed": arg[2:]}


def occlusion_evidence(tok, model, item: dict, label: str) -> int:
    """Index of the sentence whose removal lowers p(label) the most."""
    p_removed = occlusion_scores(tok, model, item, label)["p_removed"]
    return min(range(len(p_removed)), key=lambda k: p_removed[k])


def evidence_hit_rate(tok, model, items: list[dict], preds: dict[str, str], n: int = 300, seed: int = 0,
                      records: list | None = None) -> dict:
    """Occlusion evidence hit@1 on a fixed random sample of correctly predicted entailed/contradicted items.

    The sample is drawn from items the model got right, so the measure asks whether a correct answer rests on
    the decisive sentence, not whether the answer is correct. If `records` is a list, one record per sampled
    item is appended (per-sentence p(label) after removal), for post-hoc evidence analyses.
    """
    import random

    eligible = [i for i in items if i["label"] != "insufficient" and preds[i["id"]] == i["label"] and i["evidence"]]
    sample = random.Random(seed).sample(eligible, min(n, len(eligible)))
    hits, by_role = [], {}
    for it in sample:
        sc = occlusion_scores(tok, model, it, it["label"])
        k = min(range(len(sc["p_removed"])), key=lambda j: sc["p_removed"][j])
        hit = k in it["evidence"]
        hits.append(hit)
        by_role.setdefault(it["sentence_roles"][k], []).append(hit)
        if records is not None:
            records.append({"id": it["id"], "label": it["label"], **sc, "top": k, "evidence": it["evidence"],
                            "roles": it["sentence_roles"]})
    return {"n": len(sample), "eligible": len(eligible), "hit_at_1": sum(hits) / max(len(hits), 1),
            "top_sentence_role_counts": {r: len(v) for r, v in by_role.items()}}


def save_evidence_records(system: str, records: list[dict], root=None) -> None:
    import json
    from pathlib import Path

    path = Path(root or "results/predictions") / system / "evidence_test.jsonl"
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        for r in records:
            f.write(json.dumps(r) + "\n")
