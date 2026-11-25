"""Pilot-2 probe set: cross-reference and inline exemptions of the case's own vs. another category.

Uses the original generator's rendering and labelling functions without modifying them (data/ is untouched).
Family: vehicles (dev); non-reserved templates only. Output: research_next/results/probes_xref.jsonl.
See research_next/PILOT_PLAN.md for the predictions fixed before this script was run.
"""

import dataclasses
import json
import random
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from clauseshift.domains import DOMAINS  # noqa: E402
from clauseshift.generator import PairBuilder, document_text, gold_label, render_document, render_hypothesis  # noqa: E402

FAMILY, N, SEED = "vehicles", 200, 20261126
rng = random.Random(f"{SEED}-{FAMILY}-probes")
b = PairBuilder(FAMILY, rng, allow_reserved=False)
dom = DOMAINS[FAMILY]
out = []
for j in range(N):
    case = b.case()
    base = b.satisfied_background(case, {"exception"})   # all stated conditions satisfied; no exemption, no xref
    surf = b.surface()
    other = b.other_cat(case.cat)
    variants = {
        "base": base,
        "xref_case_art1": dataclasses.replace(base, xref=(case.cat, 1)),
        "xref_case_art2": dataclasses.replace(base, xref=(case.cat, 2)),
        "xref_other_art1": dataclasses.replace(base, xref=(other, 1)),
        "inline_case": dataclasses.replace(base, exception_cat=case.cat),
        "inline_other": dataclasses.replace(base, exception_cat=other),
    }
    hyp = render_hypothesis(dom, case)
    for name, spec in variants.items():
        sents = render_document(dom, spec, surf)
        label, ev_roles = gold_label(spec, case)
        out.append({"id": f"probe-{j:03d}-{name}", "case_id": j, "variant": name, "family": FAMILY,
                    "premise": document_text(sents), "sentences": [s["text"] for s in sents],
                    "sentence_roles": [s["role"] for s in sents], "hypothesis": hyp, "label": label})
path = ROOT / "research_next" / "results" / "probes_xref.jsonl"
path.parent.mkdir(parents=True, exist_ok=True)
with open(path, "w", encoding="utf-8", newline="\n") as f:
    for r in out:
        f.write(json.dumps(r) + "\n")
by = {}
for r in out:
    by.setdefault(r["variant"], []).append(r["label"])
print({k: {l: v.count(l) for l in set(v)} for k, v in by.items()})
print(out[3]["premise"], "||", out[3]["hypothesis"], "||", out[3]["label"])
