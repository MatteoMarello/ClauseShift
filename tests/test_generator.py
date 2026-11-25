import datetime as dt

import pytest

from clauseshift.data import build, check
from clauseshift.domains import DOMAINS
from clauseshift.generator import (CONTRADICTED, ENTAILED, INSUFFICIENT, Case, Spec, Surface, generate_family,
                                   gold_label, render_document, render_hypothesis)

CASE = dict(name="Alder Tools", cat=0, loc="Italy", num=50_000, date=dt.date(2025, 5, 1),
            claim_polarity=1, claim_v=0, fact_order=["cat", "loc", "num", "date"])


def case(**kw):
    return Case(**{**CASE, **kw})


@pytest.mark.parametrize("spec,kw,expected", [
    (Spec(), {}, ENTAILED),
    (Spec(polarity=-1), {}, CONTRADICTED),
    (Spec(topic=2), {}, INSUFFICIENT),
    (Spec(exception_cat=0), {}, CONTRADICTED),                  # case category exempted
    (Spec(exception_cat=1), {}, ENTAILED),                      # near miss: other category
    (Spec(threshold=40_000), {}, ENTAILED),
    (Spec(threshold=50_000), {}, CONTRADICTED),                 # boundary: "more than 50,000" excludes 50,000
    (Spec(threshold=60_000), {}, CONTRADICTED),
    (Spec(threshold=60_000), {"num": None}, INSUFFICIENT),
    (Spec(date_cutoff=dt.date(2025, 5, 1)), {}, CONTRADICTED),  # boundary: "after 1 May" excludes 1 May
    (Spec(date_cutoff=dt.date(2025, 4, 30)), {}, ENTAILED),
    (Spec(scope_loc="France"), {}, CONTRADICTED),
    (Spec(scope_loc="Italy"), {}, ENTAILED),
    (Spec(xref=(0, 1)), {}, CONTRADICTED),
    (Spec(xref=(0, 2)), {}, ENTAILED),                          # exemption from another article
    (Spec(threshold=60_000, date_cutoff=dt.date(2026, 1, 1)), {"num": None}, CONTRADICTED),  # known failure wins
    (Spec(exception_cat=0), {"claim_polarity": -1}, ENTAILED),  # negative claim swaps E/C
    (Spec(topic=1), {"claim_polarity": -1}, INSUFFICIENT),      # ... but not insufficient
])
def test_gold_label(spec, kw, expected):
    assert gold_label(spec, case(**kw))[0] == expected


def test_rendering_mentions_spec_values():
    dom = DOMAINS["procurement"]
    surf = Surface(v={k: 0 for k in ["ob_pos", "ob_neg", "threshold", "date", "scope", "exception", "xref"]},
                   cond_order=["threshold", "date", "scope", "exception"], other_ob=0)
    text = " ".join(s["text"] for s in render_document(dom, Spec(threshold=40_000, exception_cat=1), surf))
    assert "€40,000" in text and "small enterprises" in text and dom["obligation"] in text
    hyp = render_hypothesis(dom, case())
    assert "€50,000" in hyp and "1 May 2025" in hyp and hyp.endswith("is required to " + dom["obligation"] + ".")


def test_evidence_points_to_decisive_sentence():
    dom = DOMAINS["procurement"]
    surf = Surface(v={k: 0 for k in ["ob_pos", "ob_neg", "threshold", "date", "scope", "exception", "xref"]},
                   cond_order=["exception", "threshold", "date", "scope"], other_ob=0)
    spec = Spec(exception_cat=0, threshold=10_000)
    sents = render_document(dom, spec, surf)
    label, roles = gold_label(spec, case())
    assert label == CONTRADICTED and roles == ["obligation", "exception"]
    assert sents[1]["role"] == "exception"


def test_generation_is_deterministic():
    a = generate_family("library", 2, seed=7, allow_reserved=False)
    b = generate_family("library", 2, seed=7, allow_reserved=False)
    assert a == b


def test_full_build_passes_integrity_checks():
    splits = build({"seed": 3, "pairs_per_operator": {"train": 3, "dev": 3, "test": 3}})
    stats = check(splits)
    assert stats["test_entity_names_seen_in_train"] == 0


def test_pairs_differ_minimally():
    items = generate_family("travel", 5, seed=1, allow_reserved=False)
    pairs = {}
    for it in items:
        pairs.setdefault(it["pair_id"], []).append(it)
    for pid, (a, b) in pairs.items():
        if a["operator"] in ("paraphrase", "reorder"):
            continue
        diff = set(a["sentences"]) ^ set(b["sentences"])
        assert 1 <= len(diff) <= 2, (pid, diff)      # one sentence edited (or one added)
