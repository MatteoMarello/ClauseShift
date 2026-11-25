"""Minimal-pair generator for ClauseShift.

A document is rendered from a *rule specification* (`Spec`), a hypothesis from a *case* (`Case`).
The gold label is computed from (Spec, Case) by `gold_label`, never from the rendered text, so the
label is exactly as reliable as the templates are faithful to the specification. Template
faithfulness is what the human review queue (review/) checks.

Each pair (A, B) shares the hypothesis and differs by one operator applied to the document.
"""

from __future__ import annotations

import dataclasses
import datetime as dt
import hashlib
import random
from dataclasses import dataclass, field

from .domains import DOMAINS

ENTAILED, CONTRADICTED, INSUFFICIENT = "entailed", "contradicted", "insufficient"
LABELS = (ENTAILED, CONTRADICTED, INSUFFICIENT)

# Surface templates. The LAST variant of every list is reserved: it never appears in train/dev
# documents, only in test documents (template shift on top of family shift).
T = {
    "ob_pos": ["{Subj_pl} must {ob}.", "Every {subj} is required to {ob}.", "{Subj_pl} are obliged to {ob}.",
               "It is mandatory for {subj_pl} to {ob}."],
    "ob_neg": ["{Subj_pl} are not required to {ob}.", "No {subj} is obliged to {ob}.", "{Subj_pl} need not {ob}.",
               "There is no obligation for {subj_pl} to {ob}."],
    "threshold": ["This requirement applies only if {num_rule} is more than {t}.",
                  "The obligation is limited to cases in which {num_rule} exceeds {t}.",
                  "Only cases where {num_rule} is above {t} are covered by this requirement.",
                  "Unless {num_rule} is greater than {t}, this requirement does not apply."],
    "date": ["This requirement applies only to {date_events} after {d}.",
             "Only {date_events} after {d} are subject to this requirement.",
             "The obligation covers {date_events} after {d} and no others.",
             "Unless they are {date_events} after {d}, this requirement does not apply."],
    "scope": ["This requirement applies only to {subj_pl} {loc_rel} {loc}.",
              "Only {subj_pl} {loc_rel} {loc} are subject to this requirement.",
              "The obligation is restricted to {subj_pl} {loc_rel} {loc}.",
              "Unless they are {loc_rel} {loc}, {subj_pl} are not subject to this requirement."],
    "exception": ["This requirement does not apply to {cat_pl}.", "{Cat_pl} are exempt from this requirement.",
                  "The obligation does not extend to {cat_pl}.", "{Cat_pl} fall outside the scope of this requirement."],
    "xref": ["Article {k} does not apply to {cat_pl}.", "{Cat_pl} are exempt from Article {k}.",
             "The requirements of Article {k} do not extend to {cat_pl}.",
             "{Cat_pl} fall outside the scope of Article {k}."],
    "claim_pos": ["{name} is required to {ob}.", "{name} must {ob}.", "{name} has an obligation to {ob}."],
    "claim_neg": ["{name} is not required to {ob}.", "{name} does not have to {ob}.",
                  "{name} has no obligation to {ob}."],
}

OPERATORS_FLIP = ["exception_add", "xref_redirect", "negation", "threshold_cross", "date_cross",
                  "scope_restrict", "condition_unknown", "topic_swap"]
OPERATORS_NEAR_MISS = ["exception_near_miss", "threshold_near_miss", "scope_near_miss"]
OPERATORS_INVARIANT = ["paraphrase", "reorder", "distractor_add"]
OPERATORS = OPERATORS_FLIP + OPERATORS_NEAR_MISS + OPERATORS_INVARIANT


@dataclass
class Spec:
    """Semantic content of a document."""
    polarity: int = 1                    # +1 "must", -1 "not required" (only without conditions)
    topic: int = 0                       # 0 = the claimed obligation; >0 = another obligation
    threshold: int | None = None         # applies only if value > threshold
    date_cutoff: dt.date | None = None   # applies only to events strictly after cutoff
    scope_loc: str | None = None         # applies only to subjects at this location
    exception_cat: int | None = None     # inline exemption of a category
    xref: tuple[int, int] | None = None  # (category, article): "Article k does not apply to <category>"
    distractors: list[int] = field(default_factory=list)


@dataclass
class Surface:
    """Surface choices; changing these must never change the label."""
    v: dict[str, int]
    cond_order: list[str]                # order of condition sentences inside Article 1
    other_ob: int                        # which other obligation fills Article 2


@dataclass
class Case:
    name: str
    cat: int
    loc: str
    num: int | None
    date: dt.date | None
    claim_polarity: int                  # +1 "is required", -1 "is not required"
    claim_v: int
    fact_order: list[str]


def fmt_date(d: dt.date) -> str:
    return f"{d.day} {d.strftime('%B')} {d.year}"


def cap(s: str) -> str:
    return s[0].upper() + s[1:]


# ----------------------------------------------------------------------------------------------
# Gold label
# ----------------------------------------------------------------------------------------------

def gold_label(spec: Spec, case: Case) -> tuple[str, list[str]]:
    """Return (label, evidence roles). Evidence roles name the decisive sentences."""
    if spec.topic != 0:
        label, ev = INSUFFICIENT, []
    elif spec.polarity < 0:
        label, ev = CONTRADICTED, ["obligation"]
    else:
        failing, unknown, satisfied = [], [], []
        if spec.threshold is not None:
            if case.num is None:
                unknown.append("threshold")
            elif case.num > spec.threshold:
                satisfied.append("threshold")
            else:
                failing.append("threshold")
        if spec.date_cutoff is not None:
            if case.date is None:
                unknown.append("date")
            elif case.date > spec.date_cutoff:
                satisfied.append("date")
            else:
                failing.append("date")
        if spec.scope_loc is not None:
            (satisfied if case.loc == spec.scope_loc else failing).append("scope")
        if spec.exception_cat is not None and spec.exception_cat == case.cat:
            failing.append("exception")
        if spec.xref is not None and spec.xref == (case.cat, 1):
            failing.append("xref")
        if failing:
            label, ev = CONTRADICTED, ["obligation"] + failing
        elif unknown:
            label, ev = INSUFFICIENT, ["obligation"] + unknown
        else:
            label, ev = ENTAILED, ["obligation"] + satisfied
    if case.claim_polarity < 0 and label != INSUFFICIENT:
        label = ENTAILED if label == CONTRADICTED else CONTRADICTED
    return label, ev


# ----------------------------------------------------------------------------------------------
# Rendering
# ----------------------------------------------------------------------------------------------

def render_document(dom: dict, spec: Spec, surf: Surface) -> list[dict]:
    """Return a list of sentences: {article, role, text}."""
    sub = {"subj": dom["subj"], "subj_pl": dom["subj_pl"], "Subj_pl": cap(dom["subj_pl"])}
    ob = dom["obligation"] if spec.topic == 0 else dom["other_obligations"][spec.topic - 1]
    sents = []
    key = "ob_pos" if spec.polarity > 0 else "ob_neg"
    sents.append({"article": 1, "role": "obligation", "tkey": key, "text": T[key][surf.v[key]].format(ob=ob, **sub)})
    cond = {}
    if spec.threshold is not None:
        cond["threshold"] = T["threshold"][surf.v["threshold"]].format(
            num_rule=dom["num_rule"], t=dom["num_rule_fmt"].format(v=spec.threshold))
    if spec.date_cutoff is not None:
        cond["date"] = T["date"][surf.v["date"]].format(date_events=dom["date_events"], d=fmt_date(spec.date_cutoff))
    if spec.scope_loc is not None:
        cond["scope"] = T["scope"][surf.v["scope"]].format(loc_rel=dom["loc_rel"], loc=spec.scope_loc, **sub)
    if spec.exception_cat is not None:
        cat_pl = dom["categories"][spec.exception_cat][1]
        cond["exception"] = T["exception"][surf.v["exception"]].format(cat_pl=cat_pl, Cat_pl=cap(cat_pl))
    for role in surf.cond_order:
        if role in cond:
            sents.append({"article": 1, "role": role, "tkey": role, "text": cond[role]})
    other = dom["other_obligations"][surf.other_ob]
    if spec.topic != 0 and surf.other_ob == spec.topic - 1:      # keep Article 2 different from Article 1
        other = dom["other_obligations"][(surf.other_ob + 1) % len(dom["other_obligations"])]
    sents.append({"article": 2, "role": "article2", "tkey": "ob_pos", "text": T["ob_pos"][surf.v["ob_pos"]].format(ob=other, **sub)})
    art = 3
    if spec.xref is not None:
        cat_pl = dom["categories"][spec.xref[0]][1]
        sents.append({"article": art, "role": "xref", "tkey": "xref",
                      "text": T["xref"][surf.v["xref"]].format(k=spec.xref[1], cat_pl=cat_pl, Cat_pl=cap(cat_pl))})
        art += 1
    for d in spec.distractors:
        sents.append({"article": art, "role": "distractor", "tkey": None, "text": dom["distractors"][d]})
        art += 1
    return sents


def document_text(sents: list[dict]) -> str:
    out, current = [], None
    for s in sents:
        if s["article"] != current:
            current = s["article"]
            out.append(f"Article {current}.")
        out.append(s["text"])
    return " ".join(out)


def render_hypothesis(dom: dict, case: Case) -> str:
    a_cat = dom["categories"][case.cat][0]
    facts = {"cat": f"{case.name} is {a_cat}.", "loc": dom["case_loc"].format(name=case.name, loc=case.loc)}
    if case.num is not None:
        facts["num"] = dom["case_num"].format(name=case.name, v=case.num)
    if case.date is not None:
        facts["date"] = dom["case_date"].format(name=case.name, d=fmt_date(case.date))
    key = "claim_pos" if case.claim_polarity > 0 else "claim_neg"
    claim = T[key][case.claim_v].format(name=case.name, ob=dom["obligation"])
    return " ".join([facts[k] for k in case.fact_order if k in facts] + [claim])


# ----------------------------------------------------------------------------------------------
# Pair construction
# ----------------------------------------------------------------------------------------------

def getattr_cond(spec: Spec, role: str) -> bool:
    return {"threshold": spec.threshold, "date": spec.date_cutoff, "scope": spec.scope_loc,
            "exception": spec.exception_cat}[role] is not None


class PairBuilder:
    def __init__(self, family: str, rng: random.Random, allow_reserved: bool):
        self.family, self.dom, self.rng = family, DOMAINS[family], rng
        self.allow_reserved = allow_reserved

    # -- sampling helpers --------------------------------------------------------------------
    def _variant(self, key: str) -> int:
        n = len(T[key]) if self.allow_reserved else len(T[key]) - 1
        return self.rng.randrange(n)

    def surface(self) -> Surface:
        keys = ["ob_pos", "ob_neg", "threshold", "date", "scope", "exception", "xref"]
        order = ["threshold", "date", "scope", "exception"]
        self.rng.shuffle(order)
        return Surface(v={k: self._variant(k) for k in keys}, cond_order=order,
                       other_ob=self.rng.randrange(len(self.dom["other_obligations"])))

    def num(self) -> int:
        lo, hi, step = self.dom["num_range"]
        return self.rng.randrange(lo + step, hi - step, step)

    def date(self) -> dt.date:
        return dt.date(2024, 1, 1) + dt.timedelta(days=self.rng.randrange(0, 900))

    def case(self) -> Case:
        n_claim = len(T["claim_pos"]) if self.allow_reserved else len(T["claim_pos"]) - 1
        order = ["cat", "loc", "num", "date"]
        self.rng.shuffle(order)
        return Case(name=self.rng.choice(self.dom["names"]), cat=self.rng.randrange(4),
                    loc=self.rng.choice(self.dom["locations"]), num=self.num(), date=self.date(),
                    claim_polarity=self.rng.choice([1, -1]), claim_v=self.rng.randrange(n_claim), fact_order=order)

    def other_cat(self, c: int) -> int:
        return self.rng.choice([x for x in range(4) if x != c])

    def other_loc(self, loc: str) -> str:
        return self.rng.choice([x for x in self.dom["locations"] if x != loc])

    def satisfied_background(self, case: Case, exclude: set[str]) -> Spec:
        """Random conditions that the case satisfies (label stays 'required')."""
        s = Spec(distractors=self.rng.sample(range(5), self.rng.choice([0, 0, 1])))
        lo, _, step = self.dom["num_range"]
        if "threshold" not in exclude and self.rng.random() < 0.35:
            s.threshold = self.rng.randrange(lo, case.num, step)
        if "date" not in exclude and self.rng.random() < 0.35:
            s.date_cutoff = case.date - dt.timedelta(days=self.rng.randrange(1, 200))
        if "scope" not in exclude and self.rng.random() < 0.25:
            s.scope_loc = case.loc
        if "exception" not in exclude and self.rng.random() < 0.3:
            s.exception_cat = self.other_cat(case.cat)
        return s

    def random_background(self, case: Case) -> Spec:
        """Random spec of any label, used for invariance operators."""
        s = self.satisfied_background(case, set())
        r = self.rng.random()
        hi = self.dom["num_range"][1]
        if r < 0.2:
            s.threshold = self.rng.randrange(case.num, hi, self.dom["num_range"][2])
        elif r < 0.35:
            s.exception_cat = case.cat
        elif r < 0.45:
            s.threshold = s.threshold or self.num()
            case.num = None
        return s

    # -- operators -------------------------------------------------------------------------
    def build(self, op: str) -> tuple[Spec, Spec, Surface, Surface, Case]:
        case = self.case()
        surf_a = self.surface()
        surf_b = dataclasses.replace(surf_a, v=dict(surf_a.v), cond_order=list(surf_a.cond_order))
        if op == "exception_add":
            a = self.satisfied_background(case, {"exception"})
            b = dataclasses.replace(a, exception_cat=case.cat)
        elif op == "exception_near_miss":
            a = self.satisfied_background(case, {"exception"})
            b = dataclasses.replace(a, exception_cat=self.other_cat(case.cat))
        elif op == "xref_redirect":
            a = self.satisfied_background(case, set())
            a.xref = (case.cat, 1)
            b = dataclasses.replace(a, xref=(case.cat, 2))
        elif op == "negation":
            a = Spec(distractors=self.rng.sample(range(5), self.rng.choice([0, 1])))
            b = dataclasses.replace(a, polarity=-1)
        elif op in ("threshold_cross", "threshold_near_miss"):
            a = self.satisfied_background(case, {"threshold"})
            lo, hi, step = self.dom["num_range"]
            a.threshold = self.rng.randrange(lo, case.num, step)
            if op == "threshold_cross":
                boundary = self.rng.random() < 0.25          # "more than v" with value == v is not satisfied
                t_b = case.num if boundary else self.rng.randrange(case.num + step, hi + step, step)
            else:
                t_b = self.rng.choice([t for t in range(lo, case.num, step) if t != a.threshold] or [a.threshold])
            b = dataclasses.replace(a, threshold=t_b)
        elif op == "date_cross":
            a = self.satisfied_background(case, {"date"})
            a.date_cutoff = case.date - dt.timedelta(days=self.rng.randrange(1, 120))
            boundary = self.rng.random() < 0.25              # "after d" with event on d is not satisfied
            b = dataclasses.replace(a, date_cutoff=case.date if boundary
                                    else case.date + dt.timedelta(days=self.rng.randrange(1, 120)))
        elif op == "scope_restrict":
            a = self.satisfied_background(case, {"scope"})
            b = dataclasses.replace(a, scope_loc=self.other_loc(case.loc))
        elif op == "scope_near_miss":
            a = self.satisfied_background(case, {"scope"})
            b = dataclasses.replace(a, scope_loc=case.loc)
        elif op == "condition_unknown":
            which = self.rng.choice(["threshold", "date"])
            a = self.satisfied_background(case, {which})
            if which == "threshold":
                b = dataclasses.replace(a, threshold=self.num())
                case.num = None
            else:
                b = dataclasses.replace(a, date_cutoff=self.date())
                case.date = None
        elif op == "topic_swap":
            a = self.satisfied_background(case, set())
            b = dataclasses.replace(a, topic=self.rng.randrange(1, 4))
        elif op == "paraphrase":
            a = self.random_background(case)
            b = dataclasses.replace(a)
            for k in surf_b.v:
                surf_b.v[k] = self._variant(k)
            n_ob = len(T["ob_pos"]) - (0 if self.allow_reserved else 1)
            for k in ("ob_pos", "ob_neg"):                  # the obligation sentence always changes form
                if surf_b.v[k] == surf_a.v[k]:
                    surf_b.v[k] = (surf_a.v[k] + 1 + self.rng.randrange(n_ob - 1)) % n_ob
        elif op == "reorder":
            a = self.random_background(case)
            a.exception_cat = a.exception_cat if a.exception_cat is not None else self.other_cat(case.cat)
            a.threshold = a.threshold if a.threshold is not None else self.rng.randrange(
                self.dom["num_range"][0], (case.num or self.dom["num_range"][1]), self.dom["num_range"][2])
            b = dataclasses.replace(a)
            present = [r for r in surf_a.cond_order if getattr_cond(a, r)]
            while [r for r in surf_b.cond_order if r in present] == present:
                self.rng.shuffle(surf_b.cond_order)
        elif op == "distractor_add":
            a = self.random_background(case)
            b = dataclasses.replace(a, distractors=a.distractors + [x for x in range(5) if x not in a.distractors][:1])
        else:
            raise ValueError(op)
        # Attributes not used by either document are dropped from the case at random, so that
        # "the hypothesis omits an attribute" is not by itself a cue for the insufficient label.
        if a.threshold is None and b.threshold is None and self.rng.random() < 0.3:
            case.num = None
        if a.date_cutoff is None and b.date_cutoff is None and self.rng.random() < 0.3:
            case.date = None
        return a, b, surf_a, surf_b, case


def _item(family: str, dom: dict, spec: Spec, surf: Surface, case: Case, pair_id: str, side: str) -> dict:
    sents = render_document(dom, spec, surf)
    label, ev_roles = gold_label(spec, case)
    roles = [s["role"] for s in sents]
    evidence = [i for i, r in enumerate(roles) if r in ev_roles]
    return {
        "id": f"{pair_id}-{side}",
        "pair_id": pair_id,
        "side": side,
        "family": family,
        "premise": document_text(sents),
        "sentences": [s["text"] for s in sents],
        "sentence_roles": roles,
        "hypothesis": render_hypothesis(dom, case),
        "label": label,
        "evidence": evidence,
        "uses_reserved_template": any(s["tkey"] and surf.v[s["tkey"]] == len(T[s["tkey"]]) - 1 for s in sents)
        or case.claim_v == len(T["claim_pos"]) - 1,
        "annotation_status": "generator-derived",
    }


def generate_family(family: str, pairs_per_operator: int, seed: int, allow_reserved: bool) -> list[dict]:
    rng = random.Random(f"{seed}-{family}")
    builder = PairBuilder(family, rng, allow_reserved)
    dom = DOMAINS[family]
    items = []
    for op in OPERATORS:
        # The two operators that create an "insufficient" side get double weight so that the
        # insufficient class is not too rare for a stable macro-F1 (preregistered).
        for j in range(pairs_per_operator * (2 if op in ("condition_unknown", "topic_swap") else 1)):
            while True:                                      # resample degenerate pairs (identical documents)
                a, b, sa, sb, case = builder.build(op)
                if document_text(render_document(dom, a, sa)) != document_text(render_document(dom, b, sb)):
                    break
            if rng.random() < 0.5 and op in OPERATORS_FLIP:          # randomize edit direction
                a, b, sa, sb = b, a, sb, sa
            pid = f"{family}-{op}-{j:03d}"
            ia = _item(family, dom, a, sa, case, pid, "A")
            ib = _item(family, dom, b, sb, case, pid, "B")
            for it in (ia, ib):
                it["operator"] = op
                it["operator_class"] = ("flip" if op in OPERATORS_FLIP else
                                        "near_miss" if op in OPERATORS_NEAR_MISS else "invariant")
                it["pair_flips"] = ia["label"] != ib["label"]
            items += [ia, ib]
    return items


def content_hash(items: list[dict]) -> str:
    h = hashlib.sha256()
    for it in items:
        h.update((it["id"] + "\t" + it["premise"] + "\t" + it["hypothesis"] + "\t" + it["label"]).encode())
    return h.hexdigest()
