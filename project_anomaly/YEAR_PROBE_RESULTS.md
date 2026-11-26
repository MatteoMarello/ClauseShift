# Year-blindness replication — results and closure

Protocol frozen and committed before inference (`YEAR_PROBE_PROTOCOL.md`, commit `f747c88`). Tables:
`results/YEAR_PROBE_RESULTS_TABLES.md`; raw predictions `results/predictions/yearprobe__*.jsonl`. Inference: 4 models ×
2,520 items, 297 s on 4 CPU cores. No training.

## Decision: **not replicated under the frozen rule — the direction is closed**

The frozen rule required, for **both** NLI-init checkpoints, validity V (accuracy ≥ 0.80 on month-day-consistent
same-year items, format G) **and** H1. H1 holds for both. V fails for the paired checkpoint: **0.797** (unpaired:
0.908). The rule is applied as written. No training protocol is prepared, and the direction is not reopened in this
project. Reopening it would be a deviation from a frozen rule and is a decision for the researcher, not for this
analysis.

The closure is a consequence of the validity criterion, not of a missing effect. The paired checkpoint's same-year
comparison is itself only about 80% reliable (P_sat 0.211 before / 0.806 after the cutoff on same-year items), so by
the protocol's own standard its cross-year contrast cannot be attributed to the year specifically.

## Observations (all exploratory; reported for completeness, not pursued)

| Checkpoint (format G) | V | P_sat before, same year | P_sat before, earlier year (month-day later) | Δ_before [95% CI] | Δ_before per bin | Families positive |
|---|---|---|---|---|---|---|
| NLI paired s0 | **0.797 (fails)** | 0.211 | 0.789 | +0.578 [+0.500, +0.661] | +0.63 / +0.63 / +0.47 | 3/3 |
| NLI unpaired s0 | 0.908 | 0.061 | 0.739 | +0.678 [+0.606, +0.744] | +0.60 / +0.70 / +0.73 | 3/3 |

- **H1 (primary):** holds for both checkpoints, in every distance bin and every family. Under the January–March
  cutoff control (C3) the contrast is +0.69 / +0.68 (138 cross-year and 16 same-year items; the same-year group is
  small).
- **H2 (asymmetry, predicted Δ_after < 0.10):** holds. After the cutoff, a later year with an earlier month-day is
  read as satisfied (P_sat 0.94 / 0.99), even more often than same-year items (0.81 / 0.88).
- **H3 (year-only, predicted Y < 0.50 under year blindness):** **fails.** With identical month and day, an earlier
  year is never read as satisfied (P_sat 0.00) and a later year often is (0.56–0.78; Y = +0.62 / +0.74). The models
  are not blind to the year.
- **H4 (format):** for the unpaired checkpoint the contrast persists in US (+0.53) and ISO (+0.51) formats. For the
  paired checkpoint V fails in every format, so those cells are uninterpretable.
- **H5 (day and month within a year):** holds (day-only 0.82 / 0.81, month-only 0.90 / 0.98).
- **Generic-init checkpoints:** P_sat ≈ 0.9–1.0 everywhere and V ≈ 0.50. They do not read the date condition at all,
  as in Pilot 1b.

**Description of the pattern (post hoc, not a tested hypothesis).** On these probes the NLI-init checkpoints behave as
if a date is "after" the cutoff when *either* its year *or* its month-day is later. That explains the failure in the
cell "earlier year, later month-day", the success in "later year, earlier month-day", and Y > 0. "Year blindness",
the label used earlier, was therefore inaccurate even as a description. This is recorded and not investigated
further, as instructed.

## What happens to the earlier claims

- `PILOT_RESULTS.md` (year blindness, A12) and `RESEARCH_DECISION.md` (CONDITIONAL GO) are **superseded**: the
  direction is closed. They are kept unchanged as the record of what was believed at the time. `README.md` and
  `RESEARCH_DECISION.md` carry a pointer to this file.
- The 35 critical test items have correct generator labels by three independent specification routes
  (`results/CRITICAL_LABEL_CHECK.md`). This is not a human validation.
- **Literature (checked before running):** weak date comparison in language models is known (Thukral et al. 2021;
  arXiv 2210.05208; Date Fragments, arXiv 2505.16088; DateLogicQA, arXiv 2412.13377), and so is the mechanism class
  (Joshi & He 2022; Chandra Mouli et al., arXiv 2209.05104). Without the causal training experiment, the observation
  would in any case be an instance of known date-comparison weakness, not a new phenomenon.
