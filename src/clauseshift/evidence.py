"""Specification-based expectations for sentence-removal (occlusion) analyses.

For a document and a case, `expected_label_after_removal` returns the gold label that `gold_label` would assign
if sentence k were deleted from the document. It re-derives the label from the sentence roles, the evidence
indices and the case facts stated in the hypothesis, following the rules of `generator.gold_label`:

- no sentence stating the claimed obligation -> insufficient;
- a failing condition (any non-obligation sentence in the evidence of a "not required" decision) -> not required;
- otherwise a condition on an attribute the case does not state -> insufficient;
- otherwise -> required;
- a negative claim swaps entailed and contradicted.

The rule is validated in tests/test_evidence.py against the generator itself, on every minimal pair whose edit
adds exactly one sentence (the other side of the pair is then the document with that sentence removed).
Documents with a cross-reference are excluded by `removal_is_well_posed`: removal variants drop the article
headers, so "Article k" can no longer be resolved.
"""

from __future__ import annotations

import re

from .domains import DOMAINS
from .generator import CONTRADICTED, ENTAILED, INSUFFICIENT, T

CONDITION_ROLES = ("threshold", "date", "scope", "exception", "xref")
REQUIRED, NOT_REQUIRED = "required", "not_required"


def _template_regex(template: str) -> re.Pattern:
    pat = re.escape(template)
    pat = re.sub(r"\\\{name\\\}", r".+?", pat)
    pat = re.sub(r"\\\{v[^}]*\\\}", r"[\\d,]+", pat)
    pat = re.sub(r"\\\{d\\\}", r"\\d{1,2} [A-Z][a-z]+ \\d{4}", pat)
    return re.compile(pat)


_NUM = {f: _template_regex(d["case_num"]) for f, d in DOMAINS.items()}
_DATE = {f: _template_regex(d["case_date"]) for f, d in DOMAINS.items()}
_NEG_CLAIM = [re.compile(re.escape(t).replace(r"\{name\}", ".+?").replace(r"\{ob\}", ".+") + "$")
              for t in T["claim_neg"]]


def claim_is_negative(hypothesis: str) -> bool:
    claim = re.split(r"(?<=\.) ", hypothesis)[-1]
    return any(p.match(claim) for p in _NEG_CLAIM)


def case_states(item: dict) -> dict[str, bool]:
    return {"threshold": bool(_NUM[item["family"]].search(item["hypothesis"])),
            "date": bool(_DATE[item["family"]].search(item["hypothesis"]))}


def requirement(item: dict) -> str:
    """Gold label of the item expressed in claim-independent terms (required / not_required / insufficient)."""
    lab = item["label"]
    if lab == INSUFFICIENT:
        return INSUFFICIENT
    positive = not claim_is_negative(item["hypothesis"])
    return REQUIRED if (lab == ENTAILED) == positive else NOT_REQUIRED


def to_label(req: str, item: dict) -> str:
    if req == INSUFFICIENT:
        return INSUFFICIENT
    positive = not claim_is_negative(item["hypothesis"])
    return ENTAILED if (req == REQUIRED) == positive else CONTRADICTED


def removal_is_well_posed(item: dict) -> bool:
    return "xref" not in item["sentence_roles"] and requirement(item) != INSUFFICIENT


def expected_label_after_removal(item: dict, k: int) -> str:
    """Gold label of the document without sentence k (see module docstring)."""
    roles = item["sentence_roles"]
    req = requirement(item)
    if req == INSUFFICIENT:
        raise ValueError("defined for decided items only (insufficient items may have no stated obligation)")
    if roles[k] == "obligation":
        return INSUFFICIENT
    failing = {j for j in item["evidence"] if roles[j] != "obligation"} if req == NOT_REQUIRED else set()
    negated_obligation = req == NOT_REQUIRED and not failing        # "X are not required to ...", no conditions
    if negated_obligation:
        return to_label(NOT_REQUIRED, item)
    if failing - {k}:
        return to_label(NOT_REQUIRED, item)
    states = case_states(item)
    remaining = {r for j, r in enumerate(roles) if j != k}
    if any(r in remaining and not states[r] for r in ("threshold", "date")):
        return INSUFFICIENT
    return to_label(REQUIRED, item)


def removal_type(item: dict, k: int) -> str:
    """obligation / decisive (removal changes the gold label otherwise) / non-decisive."""
    if item["sentence_roles"][k] == "obligation":
        return "obligation"
    return "decisive" if expected_label_after_removal(item, k) != item["label"] else "non_decisive"
