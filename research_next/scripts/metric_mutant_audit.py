"""Audit the joint transition metric with mutants (PROTOCOL_REVIEW.md, point 18). Exploratory, no model involved.

For each of the 648 lattice programs (program_fingerprint.py), compute on the same fixed item set as Pilot 4
(175 decided, well-posed flip-operator test items; 25 per operator) the joint decisive-transition accuracy:
the program is correct on the full document AND on the document with a decisive sentence removed. Post-removal
predictions are obtained by deleting the corresponding field from the specification. A valid metric should rank the
intended rule first and give low scores to programs that ignore the decisive clauses.
Output: research_next/results/metric_mutant_audit.json and METRIC_MUTANT_AUDIT.md
"""

import collections
import contextlib
import dataclasses
import io
import json
import random
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(Path(__file__).parent))
sys.path.insert(0, str(ROOT / "src"))

with contextlib.redirect_stdout(io.StringIO()):
    import program_fingerprint as pf  # noqa: E402

from clauseshift.evidence import expected_label_after_removal, removal_is_well_posed, removal_type  # noqa: E402

FIELD = {"threshold": "threshold", "date": "date_cutoff", "scope": "scope_loc", "exception": "exception_cat"}
test = pf.items["test"]
pool = collections.defaultdict(list)
for it in test:
    if removal_is_well_posed(it) and it["operator_class"] == "flip":
        pool[it["operator"]].append(it)
rng = random.Random(20261126)                      # same sampling as fixed_set_transitions.py
items = [x for op in sorted(pool) for x in rng.sample(pool[op], min(25, len(pool[op])))]

removals = []                                      # (item, k, spec_after) for decisive removals
for it in items:
    spec, case = pf.SPECS[it["id"]]
    for k, role in enumerate(it["sentence_roles"]):
        if removal_type(it, k) != "decisive":
            continue
        after = dataclasses.replace(spec, **{FIELD[role]: None})
        assert pf.run(pf.REFERENCE, after, case) == expected_label_after_removal(it, k), it["id"]
        removals.append((it, k, after))

scores = []
for p in pf.PROGRAMS:
    ok = [pf.run(p, *pf.SPECS[it["id"]]) == it["label"] and pf.run(p, after, pf.SPECS[it["id"]][1]) ==
          expected_label_after_removal(it, k) for it, k, after in removals]
    single = [pf.run(p, after, pf.SPECS[it["id"]][1]) == expected_label_after_removal(it, k) for it, k, after in removals]
    scores.append((sum(ok) / len(ok), sum(single) / len(single), p))
scores.sort(key=lambda t: -t[0])
ref = next(s for s in scores if s[2] == pf.REFERENCE)
lazy = pf.Program("ignore", "ignore", "ignore", "ignore", "ignore", "ignore", "read")
lz = next(s for s in scores if s[2] == lazy)
n_top = sum(1 for s in scores if s[0] >= ref[0] - 1e-12)
res = {"decisive_removals": len(removals), "reference_joint": ref[0], "reference_single": ref[1],
       "lazy_joint": lz[0], "lazy_single": lz[1], "programs_tied_with_reference_on_joint": n_top,
       "programs_scoring_1.0_on_single_input": sum(1 for s in scores if s[1] == 1.0),
       "top10_joint": [{"joint": s[0], "single": s[1], "program": dataclasses.asdict(s[2])} for s in scores[:10]]}
dist = collections.Counter(round(s[0], 2) for s in scores)
L = [f"Decisive removals in the fixed item set: {len(removals)}. Reference rule: joint {ref[0]:.3f}, single-input "
     f"{ref[1]:.3f}. Lazy program: joint {lz[0]:.3f}, single-input {lz[1]:.3f}.",
     f"Programs tied with the reference on the joint score: {n_top} of {len(scores)}. Programs with a perfect "
     f"single-input score: {res['programs_scoring_1.0_on_single_input']} of {len(scores)}.", "",
     "Top programs by joint score (dimensions differing from the reference):", ""]
for s in scores[:10]:
    diff = {k: v for k, v in dataclasses.asdict(s[2]).items() if v != getattr(pf.REFERENCE, k)}
    L.append(f"- joint {s[0]:.3f}, single {s[1]:.3f}: {diff or 'reference rule'}")
(ROOT / "research_next/results/metric_mutant_audit.json").write_text(json.dumps(res, indent=1))
(ROOT / "research_next/results/METRIC_MUTANT_AUDIT.md").write_text("\n".join(L) + "\n")
print("\n".join(L))
