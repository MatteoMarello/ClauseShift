# Pilot results

All results are exploratory. Predictions were fixed in `PILOT_PROTOCOL.md` before each pilot (commit history shows
the order: protocol → Pilot 1 → addendum → Pilot 1b → addendum 2 → held-out test). Every number below is produced by
a script in `project_anomaly/scripts/` and stored in `project_anomaly/results/`. Hardware: 4 CPU cores, no GPU.

**Compute used:** model inference 1,558 s ≈ 26 minutes in total (Pilot 1: 219 s; Pilot 2: 1,090 s; Pilot 1b: 250 s;
per-model times in `results/predictions/*__runlog.json`). The held-out test and the year-blindness breakdown reuse
stored predictions (no inference). No training was run. Budget: 2 hours.

## Deviations from the protocol (complete list)

1. **Pilot 3 was not run.** It needs a new fine-tuning run, which the standing instructions do not authorise.
   The slot was used by Pilot 1b (inference only), chosen *after* seeing Pilot 1 (addendum, committed before 1b ran).
2. **Addendum 2** (hypotheses H_lex and H_md) was formed by exploring the Pilot 1b items and tested on independent
   items (registered test split, stored predictions). It was committed before the test ran.
3. **The year-blindness breakdown** (`year_blindness.py`) was designed *after* seeing the per-run results of the
   addendum-2 test. It is post hoc on the test split and is reported as a hypothesis, not as a finding.
4. Pilot 2: an error co-occurrence statistic (P(negated item wrong | original wrong)) was added after the primary table
   had been seen, because the protocol's "independence baseline" turned out to be hard to interpret (see below).
5. Pilot 1 `reorder` form exists only for research_funding thresholds (integers have no thousands separator), as the
   protocol anticipated; the pooled threshold analysis therefore uses `same` and `words` only.

## Pilot 1 — "Copy is not compare" (C1): **falsified**

Tables: `results/PILOT1_TABLES.md`; raw predictions `results/predictions/pilot1__*.jsonl`; 30 base cases per family
and condition type (90 pooled), one condition per document.

NLI-init fine-tuned models, families pooled (accuracy; same form unless stated):

| Model | Threshold eq | minus (−1 unit) | plus (+1 unit) | DiD(words) [95% CI] | Date eq | minus (−1 day) | plus (+1 day) | DiD(reorder) | DiD(words) |
|---|---|---|---|---|---|---|---|---|---|
| NLI paired | 0.61 | 0.66 | 0.77 | −0.40 [−0.56, −0.26] | 1.00 | 0.96 | 0.54 | −0.03 [−0.09, +0.02] | −0.02 [−0.08, +0.03] |
| NLI unpaired | 0.70 | 0.68 | 0.91 | −0.38 [−0.49, −0.27] | 1.00 | 1.00 | 0.34 | +0.13 [+0.04, +0.22] | +0.01 [−0.07, +0.09] |

Generic-init models: accuracy 0.00 at eq and minus and 1.00 at plus for thresholds, in every form and family; for
dates 0.01–0.07 at eq/minus and 0.93–0.99 at plus. They give the "satisfied" reading regardless of the value.

Against the fixed predictions:
- **H_span (string identity) — not supported for any model.** At the date boundary the NLI-init models are *correct*
  (1.00) whatever the surface form; for thresholds, changing the form to words *lowers* boundary accuracy (DiD −0.40).
- **H_token — not supported.** **H_strict — not supported** (minus/plus accuracy is not ≥ 0.8).
- **H_approx — "supported" by its criterion** for NLI thresholds (minus accuracy 0.66 / 0.68 < 0.7) and, trivially,
  for generic-init models (0.00), whose cause is not approximation but not reading the condition at all.
- **Validity condition:** fails for `words` everywhere (minus < 0.70) and for most date forms (plus < 0.70). By the
  protocol's own rule most DiD values are uninterpretable: the models do not resolve a one-unit difference, so a
  test of what happens *exactly* at the cutoff has no footing.

**What this changes.** The anomaly A2 ("100% of fine-tuned boundary errors copy the satisfied label") is largely an
artefact of how it was counted: on a flip pair whose labels are E/C, an error on the boundary side that is not
"insufficient" *must* take the other side's label. The pilot shows the boundary is not special: for thresholds the
error rate one unit below equals that at the cutoff; for dates the errors are on the other side (just *after* the
cutoff). Our own direction (C1) is therefore rejected.

## Pilot 1b — the comparison as a psychophysical observer (post hoc)

Tables: `results/PILOT1B_TABLES.md`; figure `figures/psychometric.png` (x-axis is categorical, not to scale).

P(satisfied reading) for the NLI-init paired model (unpaired in `PILOT1B_TABLES.md`, same pattern):

| Family | −50% | −10% | −1 unit | cutoff | +1 unit | +10% | +50% |
|---|---|---|---|---|---|---|---|
| vehicles | 0.23 | 0.13 | 0.13 | 0.10 | 0.77 | 0.77 | 0.80 |
| enrollment | 0.37 | 0.33 | 0.30 | 0.57 | 0.83 | 0.93 | 1.00 |
| research_funding | **0.80** | 0.63 | 0.60 | 0.50 | 0.70 | 0.90 | 1.00 |

| Family | −365 d | −90 d | −30 d | −1 d | cutoff | +1 d | +30 d | +90 d | +365 d |
|---|---|---|---|---|---|---|---|---|---|
| vehicles | 0.07 | **0.20** | 0.13 | 0.03 | 0.00 | 0.43 | 0.73 | 0.83 | **0.50** |
| enrollment | 0.17 | **0.43** | 0.10 | 0.07 | 0.00 | 0.70 | 0.93 | 0.93 | **0.63** |
| research_funding | 0.17 | **0.53** | 0.20 | 0.03 | 0.00 | 0.50 | 0.83 | 1.00 | **0.50** |

Against the fixed predictions:
- **P1b-1 (monotone, resolution > 1 unit) — monotonicity fails** for every NLI-init curve. Below the cutoff the
  threshold curves never reach ≤ 0.1 (no below-side resolution at any distance), and in research_funding a value at
  *half* the cutoff is read as satisfied *more* often (0.80) than a value one unit below (0.60).
- **P1b-2 (late bias for dates: P_sat(+1 day) < 0.5 and P_sat(+7) < P_sat(+365)) — supported for 2 of 6 curves
  only** (unpaired vehicles and enrollment). A late bias is visible everywhere — P_sat(+1 day) = 0.03–0.70 against
  1.00 accuracy at the cutoff, and P_sat(+7) < P_sat(+90) in all six curves — but the fixed criterion fails because
  P_sat(+365) *falls* again (0.50–0.80), which no biased comparator predicts.
- **P1b-3 (Weber-like relative scale) — not supported in a useful sense**: the research_funding curve is not a
  rescaled enrollment curve; it is non-monotone.
- **Generic-init models: P_sat ≈ 1 at every distance** (0.83–1.00 in all cells), including a value at half the
  threshold and a date a year before the cutoff. Confirmed: these models ignore an isolated threshold or date
  condition. (Their seed-0 test accuracies are 0.75–0.78. The lattice in `research_next` selected "non-strict"
  rather than "ignore" for their threshold reading on dev; Pilot 1b says "ignore" describes isolated conditions
  better. This discrepancy is unresolved and logged as A13.)

**Reading.** The non-monotonicities sit exactly where surface features of the value disagree with its magnitude: a
date 90 days before a cutoff early in the year falls late in the *previous* year (later month, earlier year); a date
365 days later has the *same* day and month; an amount at half a seven-digit cutoff has six digits and a larger
leading digit. This suggested the two hypotheses of addendum 2.

## Held-out test of the surface heuristics (addendum 2): **neither meets the fixed criteria**

`results/LEXICAL_COMPARISON_TEST.md`; registered test split, stored predictions of the nine NLI-init runs, values at or
below the cutoff with the condition decisive (96 research_funding threshold items, 222 date items).

| Contrast | P_sat (group vs other) | Difference [95% CI] | Distance-controlled | Runs positive | Verdict |
|---|---|---|---|---|---|
| H_lex: fewer digits & larger leading digit (n = 26 vs 70) | 0.376 vs 0.254 | +0.122 [−0.037, +0.285] | +0.249 [+0.058, +0.440] | 8/9 | not supported (< 0.15, CI includes 0) |
| H_md: month-day later, earlier year (n = 35 vs 170) | 0.410 vs 0.120 | +0.289 [+0.205, +0.376] | identical (all items within 365 days) | 6/9 | not supported (< 7/9 runs) |

H_lex has the predicted sign but is weak and imprecise at this sample size; for small integers (enrollment, reference)
the contrast is negative (−0.091). H_md is large and precise in the pooled analysis but fails the run-consistency
criterion, and the per-run values explain why: **+0.28 to +0.60 in all six paired/unpaired runs and exactly 0.00 in
all three operator-hold-out runs** (`results/lexical_comparison_test.json`).

## Exploratory follow-up (post hoc): year blindness is acquired with date edits

`results/YEAR_BLINDNESS.md`; date-decisive test items, accuracy averaged over three seeds:

| Training group | same year, not after | **earlier year, later month-day** (n = 35) | per seed |
|---|---|---|---|
| NLI paired (date edits in training) | 0.841 [0.81, 0.87] | **0.476** [0.32, 0.63] | 0.40, 0.51, 0.51 |
| NLI unpaired (date edits in training) | 0.811 [0.76, 0.86] | **0.295** [0.18, 0.42] | 0.26, 0.37, 0.26 |
| NLI operator hold-out (no date edits) | 0.948 [0.92, 0.97] | **1.000** [1.00, 1.00] | 1.00, 1.00, 1.00 |

The cell where comparing only month and day gives the wrong answer is the only one where the groups separate this
much. In the training data, comparing month and day alone is correct for 85.0% of date-decisive items produced by the
date edit operator (cutoff moved 1–120 days, mostly within one year) and 70.7% of the others; the critical cell
(earlier year, later month-day) makes up 29 of 1,205 date-decisive training items (2.4%).

**Hypothesis (not established):** minimal-pair edits that move a date by days to a few months vary month and day but
rarely the year, so training on them teaches a comparison that leans on month and day. This is a concrete instance of
the mechanism Joshi & He (ACL 2022) describe for counterfactually augmented data — robust features that the edits do
not perturb are under-learned. Alternatives that the stored runs cannot exclude: the hold-out models had more training
items (4,200 vs 2,400; A11), different operator mix, and three seeds per group. The decisive experiment needs training
and therefore approval (see `RESEARCH_DECISION.md`).

## Pilot 2 — errors and the negation symmetry (C2)

`results/PILOT2_TABLES.md`; test split (2,560 items) and the same items with the claim negated; 95% cluster
bootstrap over minimal pairs.

| Model | Acc. original | Acc. negated | Symmetry consistency | Negated wrong given original wrong (marginal) | Symmetrised acc. (gain) |
|---|---|---|---|---|---|
| NLI paired | 0.882 | 0.888 | 0.851 | 0.351 (0.112) | 0.911 (+0.029 [+0.017, +0.041]) |
| NLI unpaired | 0.896 | 0.900 | 0.877 | 0.389 (0.100) | 0.914 (+0.018 [+0.007, +0.029]) |
| generic paired | 0.778 | 0.780 | 0.828 | 0.609 (0.220) | 0.791 (+0.013 [+0.002, +0.023]) |
| generic unpaired | 0.752 | 0.754 | 0.851 | 0.696 (0.246) | 0.761 (+0.008 [−0.001, +0.017]) |
| zero-shot DeBERTa-v3-base NLI | 0.504 | 0.506 | 0.835 | 0.874 (0.494) | 0.523 (+0.020 [+0.011, +0.028]) |
| zero-shot DeBERTa-v3-base MNLI-FEVER-ANLI | 0.531 | 0.557 | 0.676 | 0.683 (0.443) | 0.552 (+0.020 [+0.005, +0.036]) |

Against the fixed predictions:
- **H_prog** (covariant share ≥ 0.70 and gain < 0.02 for fine-tuned models) — **not supported** for any model
  (covariant shares 0.33, 0.39, 0.61, 0.70 — the last is 0.696).
- **H_noise** (covariant share < 0.50 and gain ≥ 0.03) — **not supported** for any model (largest gain 0.029).
- **Zero-shot consistency prediction** (lower than fine-tuned) — **fails for DeBERTa-v3-base NLI** (0.835, inside
  the fine-tuned range 0.828–0.877), so by the protocol its errors are a consistent misreading (87% of its errors
  recur under negation); holds for MNLI-FEVER-ANLI (0.676).
- **Proposition 4** (symmetrised decoding changes only inconsistent items) holds exactly in all six models (asserted
  in `analyze_pilot2.py`).

Descriptive pattern (not predicted): the more accurate the model, the less its errors recur under the symmetry —
0.35–0.39 for NLI-init fine-tuned models, 0.61–0.70 for generic-init, 0.87 for zero-shot NLI. Errors of the best
models are therefore *only partly* a fixed program; one third recur, two thirds are view-specific. The
"independence baseline" in the protocol table is not a good reference (it conditions on the marginal of wrong
predictions only); the co-occurrence lift (2.8–3.9 for fine-tuned models) is the clearer statement: errors are
correlated, but far from deterministic. Symmetrised decoding gives a small, reliable gain (+0.008 to +0.029) at the
cost of a second forward pass; this is a known kind of test-time consistency method and is not claimed as new.

## Zero-cost analyses carried alongside

- C4 (A1, accuracy up / reading down) — reported in `ANOMALY_LOG.md`; model-dependent.
- C14 (single-input criteria) — Proposition 1–2 in `MATHEMATICAL_NOTES.md`.
- C15 (confidence as program signature) — not done; left as an exercise in `AUTHOR_STUDY_GUIDE.md`.
