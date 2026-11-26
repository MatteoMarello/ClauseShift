# Adversarial review

Written as a hostile reviewer of the strongest claim (year blindness, A12) and of the pilot programme as a whole.
Each objection is followed by what we can say now and what would settle it.

## A. The year-blindness claim

1. **"This is a forking-paths result."** Correct in part. The cell (earlier year, later month-day) was chosen after
   seeing Pilot 1b; the training-group split was noticed after the addendum-2 test. Mitigation: the hypothesis was
   formed on probe items (vehicles and synthetic enrollment/research_funding probes), and the effect then appeared on
   the registered test split, which played no role in forming it. Still exploratory. *Settles it:* a preregistered
   training experiment with fresh seeds and fresh test items.
2. **"35 items."** The cell is small. But the separation is not marginal: all six runs with date edits are at
   0.26–0.51, all three without are at 1.00, and the bootstrap intervals do not overlap ([0.32, 0.63] and
   [0.18, 0.42] vs [1.00, 1.00]). A new test set with a few hundred cross-year items is cheap (generation only).
3. **"Training-set size, not date edits."** The hold-out models saw 4,200 items, the others 2,400 (A11). Size could
   make any comparison better. Against it: the hold-out models are *perfect* in exactly the cell a month-day
   comparison gets wrong, while in the other three date cells the groups differ by at most 0.14. Size predicts a general
   improvement, not a cell-specific one. Not decisive. *Settles it:* matched-size retraining without date edits.
4. **"The hold-out models may not compare dates at all; they might default to one reading."** Their accuracy is
   0.90–1.00 on all four cells, including after/not-after in both year conditions, so a default reading is excluded.
5. **"The mechanism story is a just-so story."** The Joshi & He mechanism predicts that edits that rarely change the
   year leave the year under-learned. The data are consistent (85% of date-edit items are solvable by month and day)
   but other mechanisms predict the same pattern, e.g. the edit operator teaching fine near-cutoff discrimination
   that reorganises the date representation. *Settles it:* retrain with date edits whose offsets span years
   (1–720 days); the mechanism predicts the effect disappears.
6. **"Pilot 1b used the paired/unpaired checkpoints only; is the probe effect the same phenomenon?"** The probe
   effect (P_sat 0.36–0.54 for earlier-year later-month dates vs 0.00–0.09) and the test effect point the same way.
   The operator-hold-out checkpoints were not saved locally, so the probe was not run on them — a gap.
7. **"Is it just research_funding?"** No: present in both test families (enrollment +0.37, research_funding +0.19).

## B. The pilot programme

8. **"You falsified your own favourite idea and then went looking for another."** Yes, and this is recorded. The
   protocol addenda were committed before each new analysis (see git log), and every failed prediction is reported:
   C1 (H_span, H_token, H_strict), P1b-1, P1b-2 (2 of 6 curves), P1b-3, H_lex, H_md (by the fixed criterion), H_prog,
   H_noise and the zero-shot consistency prediction for DeBERTa-v3-base NLI.
9. **"Pilot 2's independence baseline is ill-defined."** Agreed; it is kept because it was fixed in the script
   before the run, and a clearer statistic (error co-occurrence) is added and declared.
10. **"Inference on a single seed per model for Pilots 1, 1b, 2."** Yes; only the held-out test and the year
    breakdown use all seeds. Statements about Pilot 1/1b/2 are about these four checkpoints.
11. **"The DeBERTa-v3-xsmall models are tiny; who cares?"** The specific numbers do not transfer. The *diagnostic*
    (psychometric probes; checking which value sub-fields the training edits vary) does, and the mechanism (A12)
    would apply to any model trained on minimal pairs with a narrow edit distribution.
12. **"Zero-shot models were run with 4 threads on different hardware from the registered run."** The originals are
    the stored predictions; only the negated items were re-run. Small numerical differences cannot affect
    arg-max-level statistics materially, but this was not verified for the zero-shot models (it was for the four
    checkpoints).
13. **"Surface-form probes may themselves be unnatural."** `words` forms were unnatural enough to break the
    comparison (validity failed). This is why the protocol had a validity condition, and those DiDs are not used.

## Verdict of the review

The programme is honest and the negative results are solid. The one positive candidate (A12) is interesting enough to
deserve a small, preregistered confirmation, and not strong enough to be written up as a finding today.
