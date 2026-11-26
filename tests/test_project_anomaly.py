"""Tests for the project_anomaly pilot code: probe construction and the exact propositions in MATHEMATICAL_NOTES.md."""

import dataclasses
import random
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "project_anomaly/scripts"))
sys.path.insert(0, str(ROOT / "src"))

from analyze_pilot2 import LABELS, SIGMA, stats  # noqa: E402
from make_boundary_probes import date_forms, num_forms, ordinal, words  # noqa: E402
from make_psychometric_probes import threshold_offsets  # noqa: E402

from clauseshift.generator import CONTRADICTED, ENTAILED, INSUFFICIENT, PairBuilder, gold_label  # noqa: E402


def test_number_words_and_ordinals():
    assert words(48) == "forty-eight"
    assert words(120) == "one hundred and twenty"
    assert words(7) == "seven"
    assert [ordinal(d) for d in (1, 2, 3, 4, 11, 12, 13, 21, 22, 23)] == \
        ["1st", "2nd", "3rd", "4th", "11th", "12th", "13th", "21st", "22nd", "23rd"]


def test_surface_forms_preserve_value():
    import datetime as dt
    f = date_forms(dt.date(2025, 12, 15))
    assert f == {"same": "15 December 2025", "reorder": "December 15, 2025", "words": "15th December 2025"}
    m = num_forms("research_funding", 85000)
    assert m == {"same": "€85,000", "reorder": "€85000", "words": "85 thousand euros"}
    assert "reorder" not in num_forms("enrollment", 48)


def test_threshold_offsets_never_zero_and_signed():
    for t, unit in ((6, 1), (48, 1), (1_440_000, 5000), (20000, 5000)):
        offs = threshold_offsets(t, unit)
        for k, d in offs.items():
            if k != "rel+0.00":
                assert d != 0 and (d > 0) == ("+" in k), (t, k, d)
            assert d % unit == 0


def test_claim_negation_is_an_exact_label_symmetry():
    """R(nu x) = sigma R(x) for random specs covering all three labels (the premise of Pilot 2)."""
    sigma = {ENTAILED: CONTRADICTED, CONTRADICTED: ENTAILED, INSUFFICIENT: INSUFFICIENT}
    seen = set()
    for family in ("vehicles", "enrollment", "research_funding"):
        b = PairBuilder(family, random.Random(f"sym-{family}"), allow_reserved=False)
        for k in range(300):
            case = b.case()
            spec = b.mix_label(b.satisfied_background(case, set()), case, set())
            if k % 10 == 0:
                spec = dataclasses.replace(spec, topic=1)
            flipped = dataclasses.replace(case, claim_polarity=-case.claim_polarity)
            label = gold_label(spec, case)[0]
            assert gold_label(spec, flipped)[0] == sigma[label]
            seen.add(label)
    assert seen == {ENTAILED, CONTRADICTED, INSUFFICIENT}


def test_stored_negation_probes_follow_sigma():
    import json
    path = ROOT / "project_anomaly/results/negation_probes.jsonl"
    rows = [json.loads(line) for line in open(path)]
    assert len(rows) == 2560
    assert all(r["label"] == SIGMA[r["orig_label"]] for r in rows)


def test_sigma_is_an_involution():
    assert all(SIGMA[SIGMA[l]] == l for l in LABELS)


def test_symmetrised_decoding_never_changes_consistent_items():
    """Proposition 4: if argmax p(.|nu x) = sigma(argmax p(.|x)), the symmetrised prediction equals the original."""
    rng = np.random.default_rng(1)
    rows = []
    for _ in range(3000):
        po, pf = rng.dirichlet(np.ones(3) * 0.5), rng.dirichlet(np.ones(3) * 0.5)
        y = LABELS[rng.integers(3)]
        rows.append({"gold": y, "gold_f": SIGMA[y], "p_o": list(po), "p_f": list(pf)})
    s = stats(rows)          # stats() asserts Proposition 4 internally
    gain = s["sym_acc_orig"].mean() - s["acc_orig"].mean()
    assert abs(gain) <= 1 - s["consistent"].mean() + 1e-12


def test_year_probes_are_balanced_and_correctly_labelled():
    import json
    from collections import Counter
    rows = [json.loads(line) for line in open(ROOT / "project_anomaly/results/year_probes.jsonl")]
    assert len(rows) == 2520
    main = [r for r in rows if r["block"] == "main" and r["format"] == "G"]
    cells = Counter((r["direction"], r["year_rel"], r["bin"], r["label"]) for r in main)
    assert set(cells.values()) == {30}
    for r in rows:
        assert r["truth_after"] == (r["case_date"] > r["cutoff"])            # ISO strings order like dates
        assert (r["label"] == r["sat_label"]) == r["truth_after"]
        if r["block"] == "main":
            same = r["case_date"][:4] == r["cutoff"][:4]
            assert same == (r["year_rel"] == "same")
            assert (r["md_after"] == r["truth_after"]) == same               # cross-year cells are month-day misleading
