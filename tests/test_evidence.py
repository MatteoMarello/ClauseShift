"""Validate the sentence-removal expectations against the generator's own minimal pairs."""

import collections

import pytest

from clauseshift.data import load
from clauseshift.evidence import (case_states, claim_is_negative, expected_label_after_removal, removal_is_well_posed,
                                  requirement)

SINGLE_SENTENCE_EDITS = ("exception_add", "scope_restrict", "condition_unknown", "distractor_add")


@pytest.fixture(scope="module")
def items():
    return [i for s in ("train", "dev", "test") for i in load(s)]


def test_claim_polarity_parsed_for_every_item(items):
    neg = [claim_is_negative(i["hypothesis"]) for i in items]
    assert 0.4 < sum(neg) / len(neg) < 0.6           # claims are negative with probability 1/2


def test_case_facts_detected(items):
    # condition_unknown removes exactly one attribute from the case; the detector must see it missing
    for i in items:
        if i["operator"] == "condition_unknown" and i["label"] == "insufficient":
            st = case_states(i)
            assert not all(st[r] for r in ("threshold", "date") if r in i["sentence_roles"]), i["id"]


def test_removal_reproduces_the_other_side_of_single_sentence_pairs(items):
    pairs = collections.defaultdict(dict)
    for i in items:
        if i["operator"] in SINGLE_SENTENCE_EDITS:
            pairs[i["pair_id"]][i["side"]] = i
    checked = 0
    for p in pairs.values():
        long_, short = sorted(p.values(), key=lambda x: -len(x["sentences"]))
        added = [k for k, s in enumerate(long_["sentences"]) if s not in short["sentences"]]
        assert len(added) == 1, long_["id"]
        if not removal_is_well_posed(long_):
            continue
        assert expected_label_after_removal(long_, added[0]) == short["label"], long_["id"]
        checked += 1
    assert checked > 600          # 706 pairs: insufficient long sides (condition_unknown) are out of scope


def test_removing_a_non_evidence_sentence_keeps_the_label(items):
    for i in items:
        if not removal_is_well_posed(i):
            continue
        for k, role in enumerate(i["sentence_roles"]):
            if role in ("article2", "distractor"):
                assert expected_label_after_removal(i, k) == i["label"], i["id"]


def test_requirement_round_trip(items):
    for i in items[:500]:
        r = requirement(i)
        assert r in ("required", "not_required", "insufficient")
