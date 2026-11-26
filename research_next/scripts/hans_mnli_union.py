"""How many MNLI validation-matched items separate the lexical-overlap heuristic (LO) from constant entailment (ALL_E)?

On HANS the two are indistinguishable (every HANS item has full lexical overlap). This script counts, on MNLI dev
(GLUE copy, downloaded to a local cache outside the repository; not redistributed), the items where LO and ALL_E
disagree, and the items where LO disagrees with the gold label. Output: research_next/results/external/hans_mnli_union.json
Usage: python hans_mnli_union.py <path to validation_matched parquet>
"""
import json, re, sys
from pathlib import Path
import pandas as pd
ROOT = Path(__file__).resolve().parents[2]
df = pd.read_parquet(sys.argv[1])
tok = lambda s: set(re.findall(r"[a-z0-9']+", s.lower()))
lo_e = df.apply(lambda r: tok(r["hypothesis"]) <= tok(r["premise"]), axis=1)
gold_e = df["label"] == 0            # GLUE MNLI: 0 entailment, 1 neutral, 2 contradiction
res = {"items": int(len(df)),
       "LO_predicts_entailment (full overlap)": int(lo_e.sum()),
       "LO_vs_ALL_E_distinguishing_items": int((~lo_e).sum()),
       "full_overlap_and_non_entailment (LO wrong)": int((lo_e & ~gold_e).sum()),
       "no_full_overlap_and_entailment (LO wrong)": int((~lo_e & gold_e).sum()),
       "LO_agreement_with_gold_binary": float((lo_e == gold_e).mean()),
       "ALL_E_agreement_with_gold_binary": float(gold_e.mean())}
out = ROOT / "research_next/results/external/hans_mnli_union.json"
out.write_text(json.dumps(res, indent=1)); print(json.dumps(res, indent=1))
