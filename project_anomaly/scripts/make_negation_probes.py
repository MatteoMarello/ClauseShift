"""Pilot 2 items (PILOT_PROTOCOL.md): every test item with the claim polarity flipped.

Same document, same case facts, same template index ("is required to" <-> "is not required to"). The expected
label is sigma(original label) with sigma: entailed <-> contradicted, insufficient fixed; this is checked against
`gold_label` for every item. Specs are regenerated in memory (hashes checked); data/ is untouched.
Output: project_anomaly/results/negation_probes.jsonl
"""

import dataclasses
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "research_next/scripts"))

from program_fingerprint import SPECS  # noqa: E402  (regenerates splits and checks manifest hashes)

from clauseshift.domains import DOMAINS  # noqa: E402
from clauseshift.generator import CONTRADICTED, ENTAILED, INSUFFICIENT, gold_label, render_hypothesis  # noqa: E402

SIGMA = {ENTAILED: CONTRADICTED, CONTRADICTED: ENTAILED, INSUFFICIENT: INSUFFICIENT}


def main():
    test = [json.loads(line) for line in open(ROOT / "data/test.jsonl")]
    out, mismatch = [], 0
    for it in test:
        spec, case = SPECS[it["id"]]
        dom = DOMAINS[it["family"]]
        assert render_hypothesis(dom, case) == it["hypothesis"], it["id"]
        assert gold_label(spec, case)[0] == it["label"], it["id"]
        flipped = dataclasses.replace(case, claim_polarity=-case.claim_polarity)
        label = gold_label(spec, flipped)[0]
        mismatch += label != SIGMA[it["label"]]
        out.append({"id": it["id"], "family": it["family"], "operator": it["operator"], "pair_id": it["pair_id"],
                    "premise": it["premise"], "hypothesis": render_hypothesis(dom, flipped), "label": label,
                    "orig_label": it["label"]})
    assert mismatch == 0, mismatch
    with open(ROOT / "project_anomaly/results/negation_probes.jsonl", "w", newline="\n") as f:
        for r in out:
            f.write(json.dumps(r) + "\n")
    print(len(out), "items; sigma mapping verified for all")


if __name__ == "__main__":
    main()
