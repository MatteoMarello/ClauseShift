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


def occlusion_evidence(tok, model, item: dict, label: str) -> int:
    """Index of the sentence whose removal lowers p(label) the most."""
    variants = []
    for k in range(len(item["sentences"])):
        kept = [s for j, s in enumerate(item["sentences"]) if j != k]
        variants.append(" ".join(kept))
    probs = predict_probs(tok, model, variants, [item["hypothesis"]] * len(variants))
    return min(range(len(variants)), key=lambda k: probs[k][label])


def evidence_hit_rate(tok, model, items: list[dict], preds: dict[str, str], n: int = 300, seed: int = 0) -> dict:
    """Occlusion evidence hit@1 on a fixed random sample of correctly predicted entailed/contradicted items.

    The sample is drawn from items the model got right, so the measure asks whether a correct answer rests on
    the decisive sentence, not whether the answer is correct.
    """
    import random

    eligible = [i for i in items if i["label"] != "insufficient" and preds[i["id"]] == i["label"] and i["evidence"]]
    sample = random.Random(seed).sample(eligible, min(n, len(eligible)))
    hits, by_role = [], {}
    for it in sample:
        k = occlusion_evidence(tok, model, it, it["label"])
        hit = k in it["evidence"]
        hits.append(hit)
        by_role.setdefault(it["sentence_roles"][k], []).append(hit)
    return {"n": len(sample), "eligible": len(eligible), "hit_at_1": sum(hits) / max(len(hits), 1),
            "top_sentence_role_counts": {r: len(v) for r, v in by_role.items()}}
