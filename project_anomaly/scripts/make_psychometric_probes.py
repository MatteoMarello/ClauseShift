"""Pilot 1b items (PILOT_PROTOCOL.md addendum, post hoc): psychometric probes around the cutoff.

Same base cases as Pilot 1 (same seed and the same sequence of random draws), `same` surface form only, case value at
a signed distance from the cutoff. Each item stores `sat_label`, the label the item would have if the condition held,
so that the "satisfied reading" can be scored. Output: project_anomaly/results/psychometric_probes.jsonl
"""

import dataclasses
import datetime as dt
import json
import random
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from clauseshift.domains import DOMAINS  # noqa: E402
from clauseshift.generator import PairBuilder, Spec, document_text, gold_label, render_document, render_hypothesis  # noqa: E402

UNIT = {"vehicles": 1, "enrollment": 1, "research_funding": 5000}
REL = [-0.5, -0.25, -0.1, -0.05, -0.02, 0.0, 0.02, 0.05, 0.1, 0.25, 0.5]
DAYS = [-365, -90, -30, -7, -2, -1, 0, 1, 2, 7, 30, 90, 365]
N_BASE, SEED = 60, 20261127          # identical to make_boundary_probes.py


def threshold_offsets(t: int, unit: int) -> dict:
    offs = {}
    for r in REL:
        d = round(r * t / unit) * unit
        if r != 0 and d == 0:
            d = unit if r > 0 else -unit
        offs[f"rel{r:+.2f}"] = d
    offs["unit-1"], offs["unit+1"] = -unit, unit
    return offs


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
                positions = {k: (d, t + d) for k, d in threshold_offsets(t, UNIT[family]).items()}
                sat_value = t + UNIT[family]
            else:
                cut = dt.date(2024, 1, 1) + dt.timedelta(days=rng.randrange(30, 870))
                spec = Spec(date_cutoff=cut)
                positions = {f"day{d:+d}": (d, cut + dt.timedelta(days=d)) for d in DAYS}
                sat_value = cut + dt.timedelta(days=1)
            doc = document_text(render_document(dom, spec, surf))
            sat_case = dataclasses.replace(case, **({"num": sat_value} if kind == "threshold" else {"date": sat_value}))
            sat_label = gold_label(spec, sat_case)[0]
            for tag, (delta, val) in positions.items():
                c = dataclasses.replace(case, **({"num": val} if kind == "threshold" else {"date": val}))
                label = gold_label(spec, c)[0]
                assert (label == sat_label) == (delta > 0), (family, tag, label, sat_label)
                out.append({"id": f"{family}-{j:02d}-{kind}-{tag}", "base": f"{family}-{j:02d}", "family": family,
                            "kind": kind, "tag": tag, "delta": delta,
                            "rel": (delta / t) if kind == "threshold" else None,
                            "premise": doc, "hypothesis": render_hypothesis(dom, c), "label": label,
                            "sat_label": sat_label})
    with open(ROOT / "project_anomaly/results/psychometric_probes.jsonl", "w", newline="\n") as f:
        for r in out:
            f.write(json.dumps(r) + "\n")
    print(len(out), "items")


if __name__ == "__main__":
    main()
