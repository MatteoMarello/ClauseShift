from clauseshift.metrics import bootstrap, group_pairs, macro_f1, pair_metrics


def _items():
    rows = []
    for pid, op, cls, la, lb in [("p1", "negation", "flip", "entailed", "contradicted"),
                                 ("p2", "paraphrase", "invariant", "insufficient", "insufficient")]:
        for side, lab in (("A", la), ("B", lb)):
            rows.append({"id": f"{pid}-{side}", "pair_id": pid, "side": side, "label": lab, "operator": op,
                         "operator_class": cls, "family": "f", "uses_reserved_template": False})
    return rows


def test_macro_f1_perfect_and_constant():
    g = ["entailed", "contradicted", "insufficient"]
    assert macro_f1(g, g) == 1.0
    assert abs(macro_f1(g, ["entailed"] * 3) - 0.5 / 3) < 1e-9   # F1(entailed)=0.5, others 0


def test_pair_metrics_counts_both_sides():
    items = _items()
    preds = {"p1-A": "entailed", "p1-B": "entailed", "p2-A": "insufficient", "p2-B": "insufficient"}
    m = pair_metrics(group_pairs(items, preds))
    assert m["accuracy"] == 0.75
    assert m["pair_accuracy"] == 0.5          # p1 fails on side B
    assert m["flip_sensitivity"] == 0.0       # model did not change its answer
    assert m["invariance"] == 1.0


def test_bootstrap_interval_contains_point():
    items = _items()
    preds = {i["id"]: i["label"] for i in items}
    b = bootstrap(group_pairs(items, preds), n=50)
    assert b["accuracy"]["lo"] <= b["accuracy"]["point"] <= b["accuracy"]["hi"]
