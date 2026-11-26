"""Power of the seed-level test for confirmatory hypothesis C3 (paired - unpaired false-flip rate).

The test is a one-sided paired t-test over n seed pairs at alpha. The true effect delta and the between-seed SD of the
paired-minus-unpaired difference (sigma) are unknown: the pilot gives one seed per condition (per-family differences
+0.17 to +0.36 for the NLI initialisation), and no estimate of sigma. We therefore tabulate power over a grid.
Case-sampling noise within a seed (~0.03-0.04 SE with 200 cases per family) is folded into sigma.
Output: research_next/results/power_analysis.json and POWER_ANALYSIS.md
"""
import json
from pathlib import Path
import numpy as np
from scipy import stats
ROOT = Path(__file__).resolve().parents[2]
res, L = {}, ["| n seed pairs | delta | sigma=0.05 | sigma=0.10 | sigma=0.15 | sigma=0.20 | sigma=0.30 |", "|---|---|---|---|---|---|---|"]
for n in (3, 5, 8, 10):
    for delta in (0.10, 0.20):
        row = []
        for sigma in (0.05, 0.10, 0.15, 0.20, 0.30):
            df = n - 1
            tcrit = stats.t.ppf(0.95, df)
            ncp = delta / (sigma / np.sqrt(n))
            power = 1 - stats.nct.cdf(tcrit, df, ncp)
            res[f"n={n},delta={delta},sigma={sigma}"] = float(power)
            row.append(f"{power:.2f}")
        L.append(f"| {n} | {delta:.2f} | " + " | ".join(row) + " |")
(ROOT / "research_next/results/power_analysis.json").write_text(json.dumps(res, indent=1))
(ROOT / "research_next/results/POWER_ANALYSIS.md").write_text(
    "Power of a one-sided paired t-test (alpha = 0.05) on n seed-level differences; sigma = SD of the "
    "paired-minus-unpaired difference across seed pairs.\n\n" + "\n".join(L) + "\n")
print("\n".join(L))
