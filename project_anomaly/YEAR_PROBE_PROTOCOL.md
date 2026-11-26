# Year-blindness replication — frozen protocol

Authorised scope: **one light inference test**. No training. Written and committed before any model was run on the
probe items below (`scripts/make_year_probes.py` generates them; only their labels and balance were inspected).

## Background (exploratory, post hoc — `PILOT_RESULTS.md`)

On 35 registered test items with a case date in an earlier year but later in the calendar than the cutoff, six NLI-init
runs trained with date edits scored 0.26–0.51 and three runs trained without date edits scored 1.00. The 35 labels were
re-derived by specification logic along three independent routes (stored gold label, the separately implemented
reference program, a text-only derivation): 35/35 agree (`results/CRITICAL_LABEL_CHECK.md`). This is a consistency
check of generator-derived labels, **not** a human validation.

## What this test can and cannot decide

Only four fine-tuned checkpoints are available locally (seed 0: NLI-init paired/unpaired, generic-init
paired/unpaired). The checkpoints trained without date edits are not available, so this test **cannot** address the
cause (date edits vs training-set size). It decides only whether the behavioural signature — failure when month and day
point the wrong way across a year boundary — is a stable property of the NLI-init checkpoints on fresh, balanced items
with year, month, day, format and distance controlled.

## Items (2,520; fresh seed 20261201; families vehicles, enrollment, research_funding; one date condition per document)

- **MAIN** (2,160): direction {before, after the cutoff} × year relation {same year, adjacent year} × distance
  {1–30, 31–120, 121–300 days} × format {G "15 October 2024", US "October 15, 2024", ISO "2024-10-15"}; 20 base
  cases per family and cell; the three formats share the base case. Distances are drawn identically in same- and
  cross-year cells (mean |days| 99.7–110.2 per cell). Month-day relation is implied by the design: same-year cells are
  month-day *consistent*; cross-year cells are month-day *misleading*. Labels balanced (E/C 50/50 in every cell);
  claim polarity alternates.
- **YEAR** (180): identical month and day, case year = cutoff year + k, k ∈ {−2, −1, +1, +2}; format G.
- **DAYMONTH** (180): same year; day-only differences (same month, 1–15 days) and month-only differences (same day,
  1–5 months), before/after; format G.

Known residual confound: at a fixed distance, a cross-year item needs a cutoff near the start (before) or end (after)
of the year, so the cutoff's month differs between cells (mean month 2.5 vs 8.3 for before-cross vs before-same). A
secondary control restricts to cutoffs in January–March (see C3).

## Quantities

P_sat = share of predictions equal to the label the item would have if the condition held. Ideal: 0 before, 1 after.
Bootstrap: 2,000 resamples over base cases (formats of one base case resampled together).

## Hypotheses and decision criteria (fixed now)

Primary analysis per NLI-init checkpoint (paired_s0, unpaired_s0), format G, families pooled, distance bins weighted
equally.

- **V (validity).** Accuracy on the month-day-consistent cells (same year, both directions) ≥ 0.80. If V fails for a
  checkpoint, its result is uninterpretable and counts as *not replicated*.
- **H1 (replication; primary).** Δ_before = P_sat(before, cross-year) − P_sat(before, same-year) ≥ 0.20, with the
  95% CI lower bound > 0.05, positive in every distance bin, and positive in at least 2 of 3 families.

**Decision rule.** The phenomenon *replicates* if and only if V and H1 hold for **both** NLI-init checkpoints. Otherwise
the direction is **closed** and no training protocol is written beyond recording the closure.

Secondary (reported, do not change the decision):
- **H2 (asymmetry).** Δ_after = P_sat(after, same-year) − P_sat(after, cross-year). Pilot 1b suggests the after side is
  unaffected: predicted Δ_after < 0.10.
- **H3 (year-only).** Y = P_sat(k > 0) − P_sat(k < 0) on YEAR items. A year-aware reader gives Y ≈ 1. Predicted under
  year blindness: Y < 0.50.
- **H4 (format).** Δ_before ≥ 0.10 in US and in ISO format (where V holds in that format).
- **H5 (day and month work within a year).** Accuracy on DAYMONTH items ≥ 0.80 for day-only and month-only
  separately; if not, the failure is not specific to the year.
- **C3 (cutoff-month control).** Δ_before restricted to cutoffs in January–March (same-year items with such cutoffs
  exist at short distances): reported with its n; predicted ≥ 0.10.
- Generic-init checkpoints: reported for reference; expected P_sat ≈ 1 everywhere (Pilot 1b).

## Relation to the literature (checked before running)

Known: language models are weak at comparing dates and temporal expressions (Thukral et al. 2021, probing MNLI models:
accuracy drops when month-days are added to month-year comparisons; Date understanding in multi-hop QA, arXiv
2210.05208); date tokenisation and format affect accuracy (Date Fragments, arXiv 2505.16088; DateLogicQA, arXiv
2412.13377); counterfactual or minimal edits can leave unperturbed robust features under-learned (Joshi & He, ACL 2022)
and need not deliver the intended invariance (Chandra Mouli et al., arXiv 2209.05104). Not found: a demonstration
that the *value distribution of one edit operator* makes a fine-tuned model compare dates by month and day while
neglecting the year. This replication cannot establish that causal claim; it can only show whether the signature is
stable. Any write-up must present the signature as an instance of known date-comparison weakness unless the training
experiment establishes the cause.
