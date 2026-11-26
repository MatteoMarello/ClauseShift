"""Validate a hand-written ClauseShift family (research_next/FAMILY_DESIGN_EXERCISE.md, Part 6).

Checks only; never generates or edits content. Usage: python validate_family.py <family.yaml> [<family2.yaml> ...]
Exit status 1 if any check fails.
"""

import itertools
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from clauseshift.domains import DOMAINS  # noqa: E402

try:
    import yaml
except ImportError:  # minimal fallback is not attempted: YAML needs a parser
    sys.exit("PyYAML is required: pip install pyyaml")

REQUIRED = {"family_id": str, "subj": str, "subj_pl": str, "obligation": str, "other_obligations": list,
            "categories": list, "category_paraphrases": list, "nonce_category": list, "loc_rel": str,
            "locations": list, "case_loc": str, "num_rule": str, "num_rule_fmt": str, "case_num": str,
            "num_range": list, "date_events": str, "case_date": str, "distractors": list, "names": list}
STOP = {"a", "an", "the", "of", "to", "in", "for", "and", "or", "on", "at", "with", "by"}


def toks(s: str) -> set[str]:
    return {t for t in re.findall(r"[a-z0-9\-]+", s.lower()) if t not in STOP}


def jaccard(a: str, b: str) -> float:
    ta, tb = toks(a), toks(b)
    return len(ta & tb) / max(len(ta | tb), 1)


def check(path: Path, others: list[dict]) -> list[str]:
    f = yaml.safe_load(path.read_text())
    errs = []
    for k, t in REQUIRED.items():
        if k not in f or not isinstance(f[k], t) or (isinstance(f[k], (str, list)) and not f[k]):
            errs.append(f"missing or empty field: {k}")
    if errs:
        return errs
    if f["family_id"] in DOMAINS:
        errs.append("family_id already exists in domains.py")
    sizes = {"other_obligations": 3, "categories": 4, "category_paraphrases": 4, "locations": 6, "distractors": 5}
    for k, n in sizes.items():
        if len(f[k]) != n:
            errs.append(f"{k}: expected {n} entries, got {len(f[k])}")
    if len(f["names"]) < 15 or len(set(f["names"])) != len(f["names"]):
        errs.append("names: need at least 15 unique names")
    for k, ph in (("case_loc", ["{name}", "{loc}"]), ("case_num", ["{name}", "{v"]), ("case_date", ["{name}", "{d}"]),
                  ("num_rule_fmt", ["{v"])):
        if not all(p in f[k] for p in ph):
            errs.append(f"{k}: must contain placeholders {ph}")
    lo, hi, step = f["num_range"]
    if not (isinstance(lo, int) and isinstance(hi, int) and isinstance(step, int) and step > 0 and hi - lo >= 10 * step):
        errs.append("num_range: need integers [lo, hi, step] with hi - lo >= 10 * step")
    cats = [c[1] for c in f["categories"]]
    sim = f.get("similar_pair") or []
    for i, j in itertools.combinations(range(4), 2):
        jac = jaccard(cats[i], cats[j])
        planned = sorted(sim) == [i, j]
        if jac > 0.34 and not planned:
            errs.append(f"categories {i},{j} too similar (Jaccard {jac:.2f} > 0.34): '{cats[i]}' / '{cats[j]}'")
    lens = [len(c.split()) for c in cats]
    if max(lens) - min(lens) > 2:
        errs.append(f"category phrase lengths differ by more than 2 tokens: {lens}")
    cat_tokens = set().union(*(toks(c) for c in cats)) - toks(f["subj_pl"]) - toks(f["subj"])
    for k in ("obligation", "other_obligations", "distractors", "locations"):
        vals = f[k] if isinstance(f[k], list) else [f[k]]
        for v in vals:
            leak = toks(v) & cat_tokens
            if leak:
                errs.append(f"{k}: contains category word(s) {sorted(leak)} in '{v}'")
    ob = toks(f["obligation"])
    for o in f["other_obligations"]:
        if len(ob & toks(o)) >= 2:
            errs.append(f"other obligation shares content words with the claimed obligation: '{o}'")
    for name, d in list(DOMAINS.items()) + [(o["family_id"], o) for o in others if o is not f]:
        if name == f["family_id"]:
            continue
        shared = set(f["names"]) & set(d["names"])
        if shared:
            errs.append(f"names shared with family '{name}': {sorted(shared)}")
        if toks(f["obligation"]) == toks(d["obligation"]):
            errs.append(f"same obligation as family '{name}'")
        dc = [c[1] for c in d["categories"]]
        for c in cats:
            if any(jaccard(c, x) > 0.5 for x in dc):
                errs.append(f"category '{c}' too close to a category of family '{name}'")
    return errs


paths = [Path(p) for p in sys.argv[1:]]
loaded = [yaml.safe_load(p.read_text()) for p in paths]
bad = False
for p in paths:
    e = check(p, loaded)
    print(f"{p}: {'OK' if not e else str(len(e)) + ' problem(s)'}")
    for x in e:
        print("  -", x)
    bad |= bool(e)
sys.exit(1 if bad else 0)
