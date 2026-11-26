"""Pilot 1 items (PILOT_PROTOCOL.md): boundary probes with the case value in different surface forms.

One condition per document (threshold "more than t" or date "after d"), case value at cutoff (eq), one unit below
(minus) or above (plus); the case value written as `same` (generator format), `reorder`, or `words`. The rule text is
never changed. Labels from `gold_label`. Generator functions are reused; data/ is untouched.
Output: project_anomaly/results/boundary_probes.jsonl
"""

import datetime as dt
import json
import random
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from clauseshift.domains import DOMAINS  # noqa: E402
from clauseshift.generator import PairBuilder, Spec, document_text, fmt_date, gold_label, render_document, render_hypothesis  # noqa: E402

ONES = "zero one two three four five six seven eight nine ten eleven twelve thirteen fourteen fifteen sixteen " \
       "seventeen eighteen nineteen".split()
TENS = "_ _ twenty thirty forty fifty sixty seventy eighty ninety".split()


def words(n: int) -> str:
    if n < 20:
        return ONES[n]
    if n < 100:
        return TENS[n // 10] + ("" if n % 10 == 0 else "-" + ONES[n % 10])
    if n < 1000:
        return ONES[n // 100] + " hundred" + ("" if n % 100 == 0 else " and " + words(n % 100))
    raise ValueError(n)


def ordinal(d: int) -> str:
    suf = "th" if 11 <= d % 100 <= 13 else {1: "st", 2: "nd", 3: "rd"}.get(d % 10, "th")
    return f"{d}{suf}"


def date_forms(d: dt.date) -> dict:
    return {"same": fmt_date(d), "reorder": f"{d.strftime('%B')} {d.day}, {d.year}",
            "words": f"{ordinal(d.day)} {d.strftime('%B')} {d.year}"}


def num_forms(family: str, v: int) -> dict:
    if family == "research_funding":                      # rendered as €{v:,}
        return {"same": f"€{v:,}", "reorder": f"€{v}", "words": f"{v // 1000} thousand euros" if v % 1000 == 0 else None}
    return {"same": str(v), "words": words(v)}            # integers without separators: no distinct reorder form


UNIT = {"vehicles": 1, "enrollment": 1, "research_funding": 5000}
N_BASE, SEED = 60, 20261127


def main():
    out = []
    for family in ("vehicles", "enrollment", "research_funding"):
        rng = random.Random(f"{SEED}-{family}-boundary")
        b = PairBuilder(family, rng, allow_reserved=False)
        dom = DOMAINS[family]
        lo, hi, step = dom["num_range"]
        for j in range(N_BASE):
            kind = "threshold" if j % 2 == 0 else "date"
            case = b.case()
            surf = b.surface()
            if kind == "threshold":
                t = rng.randrange(lo + step * 2, hi - step * 2, step)
                spec = Spec(threshold=t)
                positions = {"eq": t, "minus": t - UNIT[family], "plus": t + UNIT[family]}
            else:
                d = dt.date(2024, 1, 1) + dt.timedelta(days=rng.randrange(30, 870))
                spec = Spec(date_cutoff=d)
                positions = {"eq": d, "minus": d - dt.timedelta(days=1), "plus": d + dt.timedelta(days=1)}
            doc = document_text(render_document(dom, spec, surf))
            for pos, val in positions.items():
                if kind == "threshold":
                    case.num = val
                    forms = num_forms(family, val)
                    original = dom["case_num"].format(name=case.name, v=val)
                    variants = {f: (original.replace(forms["same"], s, 1) if f != "same" else original)
                                for f, s in forms.items() if s}
                else:
                    case.date = val
                    forms = date_forms(val)
                    original = dom["case_date"].format(name=case.name, d=fmt_date(val))
                    variants = {f: original.replace(forms["same"], s, 1) for f, s in forms.items()}
                hyp = render_hypothesis(dom, case)
                assert original in hyp, (family, original, hyp)
                label, _ = gold_label(spec, case)
                for form, sent in variants.items():
                    out.append({"id": f"{family}-{j:02d}-{kind}-{pos}-{form}", "base": f"{family}-{j:02d}", "family": family,
                                "kind": kind, "position": pos, "form": form, "premise": doc,
                                "hypothesis": hyp.replace(original, sent, 1), "label": label})
    path = ROOT / "project_anomaly/results/boundary_probes.jsonl"
    with open(path, "w", newline="\n") as f:
        for r in out:
            f.write(json.dumps(r) + "\n")
    print(len(out), "items")
    for r in out[:3] + [x for x in out if x["form"] == "words"][:2]:
        print(r["position"], r["form"], r["label"], "|", r["premise"][:110], "|", r["hypothesis"])


if __name__ == "__main__":
    main()
