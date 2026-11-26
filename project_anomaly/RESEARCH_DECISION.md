# Research decision — Project Anomaly

> **Superseded (2026-11-26).** The authorised year-blindness replication did not meet its frozen decision rule
> (validity failed for one of the two checkpoints), so the direction is **closed** and no training protocol is
> prepared. See `YEAR_PROBE_RESULTS.md`. The text below is kept unchanged as the record of the earlier decision.

Short answer: our own favourite idea ("copy is not compare") is **false**. The pilots turned up one observation
that is worth checking with a small, preregistered training experiment: **models fine-tuned on minimal pairs whose
date edits move the cutoff by days to months become blind to the year.** This is exploratory and has a clear
confound (training-set size). Recommendation: **CONDITIONAL GO** for that single check; **NO GO** for everything else.

## 1. What is the most surprising observation?

On test items where the case date is in an **earlier year but later in the calendar** than the cutoff (e.g. cutoff
"after 1 March 2025", event on 15 October 2024), the six NLI-init runs trained with date edits are right only
26–51% of the time, while the three runs trained **without any date edits** are right 100% of the time
(`results/YEAR_BLINDNESS.md`). Training on the edits meant to teach date comparison seems to have made the
models compare month and day while neglecting the year. In the training data a month-and-day comparison already gives
the right answer for 85% of the date-edit items.

Runner-up surprises: generic-init models that reach 0.75–0.78 test accuracy read a threshold or date condition as
satisfied at *any* distance, including a value at half the threshold (Pilot 1b); and in research_funding, the
NLI-init models read a budget at half the threshold as "exceeding" it more often than a budget just below it.

## 2. Is it scientifically original, or potentially original?

Potentially original as a concrete instance; not original as a mechanism. Joshi & He (ACL 2022) showed that
counterfactual edits leave the robust features they do not perturb under-learned. What we have not found in the
literature is a demonstration inside a minimal-pair benchmark that the *edit distribution of a single operator*
decides which sub-field of a value (day/month vs year) the model learns to compare, with a behavioural signature
that ordinary accuracy hides. The searches are listed in `NOVELTY_MATRIX.md`; a search that finds nothing is weak
evidence.

## 3. What is the strongest evidence against it?

- The cell has **35 test items**, and the comparison was chosen **after** seeing the data (forking paths).
- The no-date-edit runs had **more training items** (4,200 vs 2,400). Size, not edits, could be the cause. Against
  this: their advantage is concentrated in exactly the cell where a month-day comparison fails (other cells differ
  by at most 0.14), which size does not predict.
- The fixed criterion of the addendum-2 test (≥ 7 of 9 runs positive) **failed**, precisely because the three
  hold-out runs show no effect. The criterion was written before the split by training group was noticed.
- The probe evidence (Pilot 1b) covers only the paired/unpaired seed-0 checkpoints; hold-out checkpoints were not
  available locally.

## 4. What is the smallest defensible contribution?

Today: a **negative result plus a diagnostic**. (i) The boundary errors on ClauseShift are not caused by string
identity, and the "100% copy the satisfied label" statistic was largely a counting artefact; (ii) psychometric probes
(P(satisfied) as a function of signed distance from the cutoff) expose comparisons that are non-monotone and models
that ignore conditions entirely, none of which accuracy or flip-pair accuracy shows. This is a section of the
ClauseShift report, not a paper.

If the training check succeeds: "**Your minimal pairs decide what your model compares**" — a short paper (workshop
length) showing, with a preregistered design, that narrowing an edit operator's value range induces a specific blind
spot and that widening it removes it.

## 5. Does it justify a new architecture or algorithm?

No. The candidate cause is the data-generating edit distribution; the remedy, if confirmed, is a generator design
rule (vary every sub-field of a value that the rule depends on) plus a probe. Nothing here points to a missing
architectural component. Symmetrised decoding (Pilot 2) gives +0.008 to +0.029 at the cost of a second pass and is a
known kind of test-time consistency method; it does not justify an algorithmic contribution either.

## 6. What experiment would most efficiently decide whether to continue?

Two steps, the first free:

1. **No training (≈ 5 minutes of inference).** Generate a fresh probe set with a few hundred items per cell
   (same year / earlier year × month-day earlier / later), new seed, test families, and run the four local checkpoints.
   Decides whether the probe effect replicates at scale. It cannot separate the mechanisms.
2. **Training (needs your approval; ≈ 6 runs × 18 min ≈ 2 hours CPU).** NLI-init paired recipe, three seeds each, two
   new conditions: (b) date edits with offsets 1–720 days (the year changes in about half of them); (c) no date edits,
   training size matched at 2,400 items. Fixed predictions: accuracy in the critical cell ≥ 0.85 in (b) and (c) and
   ≤ 0.60 in the registered condition (already measured). If (c) succeeds and (b) fails, the edits are not the cause
   in the way proposed; if (b) succeeds and (c) fails, the effect is specific to edits that do not vary the year.

The training step changes no registered result and no frozen data; it would be a new, preregistered exploratory study.

## 7. Could it generalize outside ClauseShift?

The mechanism should apply wherever minimal pairs or counterfactual augmentations are generated with a narrow edit
distribution over structured values: amounts edited by small percentages (leading digits rarely change), version
numbers, dates in contracts and regulations, ages. The diagnostic transfers directly: sweep the value against a fixed
condition and look for non-monotone P(satisfied) curves. Whether *large* models show the same effect is unknown; we
tested 22M-parameter encoders only.

## 8. What would be required for a credible paper?

- The preregistered training experiment above, with ≥ 3 seeds per condition and fresh test items.
- A second model family (e.g. a base-size encoder) to show the effect is not specific to DeBERTa-v3-xsmall.
- A second value type (e.g. amounts with edits of ±1–10%) to show the mechanism is not date-specific.
- Positioning against Joshi & He (2022), contrast sets (Gardner et al. 2020) and numeracy work, read in full.
- A human baseline is *not* needed for this claim (it concerns what models learn from edits, not task difficulty).

## 9. What intellectual contribution should the human researcher make personally?

The following are yours to do; none has been done for you (see `AUTHOR_STUDY_GUIDE.md`):
- Decide whether the year-blindness question is the one you want to pursue, against the identifiability line in
  `research_next/`.
- Write down *your own* predictions for the training experiment before any run, and decide the decision criteria.
- Read Joshi & He (2022) in full and decide whether our case is an instance of their mechanism or something else;
  write the positioning paragraph yourself.
- Inspect the 35 critical test items by hand and check that the gold labels are right (a 15-minute task that only a
  human should sign off).
- Design the edit-distribution variants (which offsets, which values) — the scientific content of the experiment.

## 10. Recommendation

**CONDITIONAL GO** — for one narrowly defined follow-up: step 1 of question 6 immediately (no training), and step 2
only with your explicit approval of ≈ 2 hours of CPU training. Stop if step 1 does not replicate the probe effect at
scale (critical-cell P(satisfied) not clearly above the same-year baseline), or if step 2 shows the same accuracy in
conditions (b) and (c) as in the registered runs.

**NO GO** for: "copy is not compare" (falsified), symmetry-based error analysis as a research contribution (known),
symmetrised decoding (known kind, small gain), and any new architecture.

---

*AI-assisted work disclosure.* The pilots, code, analyses and this memo were produced by an AI coding assistant
working in this repository under the researcher's instructions. No human annotation, no human experiment and no
human-authored analysis is reported here. The decisions in question 9 are deliberately left to the researcher.
