# Author study guide — Project Anomaly

For the researcher. Everything in `project_anomaly/` was produced by an AI assistant; this guide lists what you need
to understand to own the work, and the parts that should be *your* contribution. Nothing in this repository claims
that you have done any of the exercises below.

## 1. Read in this order (about 2 hours)

1. `ANOMALY_LOG.md` — the anomalies we started from (A1–A11) and the ones the pilots added (A12–A14).
2. `PILOT_PROTOCOL.md` — note the order: predictions, then data. Check the git log to see that each addendum was
   committed before its analysis ran (`git log --oneline -- project_anomaly/PILOT_PROTOCOL.md`).
3. `PILOT_RESULTS.md` — for every prediction, find the number in `results/` that decides it.
4. `MATHEMATICAL_NOTES.md`, then `ADVERSARIAL_REVIEW.md`, then `RESEARCH_DECISION.md`.

## 2. Concepts to master

- **Validity conditions in probing.** Why a difference-in-differences at the cutoff means nothing if the model does
  not resolve one unit (Pilot 1). Be able to explain this to a reviewer in two sentences.
- **Psychometric functions.** P(response) vs stimulus; point of subjective equality (bias), slope (resolution),
  guess and lapse rates. Why a *non-monotone* curve rules out any single-threshold comparator.
- **Equivariance and symmetrised decoding.** A task symmetry (ν, σ); why the product p(y|x)·p(σy|νx) is
  equivariant (Prop. 3); why it cannot change a consistent prediction (Prop. 4).
- **Under-learning of unperturbed features** (Joshi & He 2022): their linear-Gaussian argument, and how it maps to
  "edits change day/month, rarely the year".
- **Forking paths.** Which of our results are confirmatory-in-spirit (predictions fixed before data) and which are
  post hoc (year blindness). Be able to label each number in `PILOT_RESULTS.md`.

## 3. Exercises (pen and paper)

1. Prove Proposition 4 yourself without looking. Then construct a 3-label example where the two views are
   *inconsistent* and symmetrised decoding makes the prediction *worse*.
2. A date d and a cutoff c are less than one year apart and in different calendar years. Show that the month-day
   comparison then always disagrees with the true comparison. What fraction of pairs drawn as in `date_cross`
   (offsets uniform in 1–120 days, cutoff uniform over two years) cross a year boundary? Compare with the 15%
   observed (`YEAR_BLINDNESS.md`, training rows).
3. For a comparator with P_sat(Δ) = Φ((Δ − μ)/s), what is the expected accuracy at Δ = 0, −1, +1 unit as a function of
   μ and s? For which (μ, s) would Pilot 1's H_strict prediction hold?
4. Prove Proposition 1 for a rule with an exemption *and* a cross-reference. Is there an edit T (other than deletion)
   for which a single-input criterion is *not* maximised by the lazy program?
5. In Pilot 2, why is "P(negated wrong | original wrong)" a better statistic than the protocol's independence
   baseline? Write the two definitions and find a toy confusion pattern where they disagree in sign.

## 4. Implementation tasks (each ≤ 1 hour; no training needed)

1. **Inspect the 35 critical items.** Run `python project_anomaly/scripts/year_blindness.py`, then list the item ids
   of the "cross / not_after" cell and read each premise and hypothesis. Check every gold label by hand and write
   down any doubt. (This is a check only you should sign off.)
2. **Step 1 of the decision memo.** Write `make_year_probes.py`: a fresh seed, test families, 4 cells × ≥ 150 items
   (same/cross year × month-day earlier/later), dates only, one condition per document. Fix your predictions in a
   short text file *before* running `run_models.py` on it.
3. **Confidence as a program signature (C15, not done).** Using `pilot2__*.jsonl` and the stored originals, test
   whether errors that recur under negation have higher confidence than those that do not.
4. **A13.** Find why the lattice chose "non-strict" over "ignore" for generic-init models: count the dev items that
   separate the two programs and look at the models' predictions on them.

## 5. Open questions (genuinely unresolved)

- Is year blindness caused by the date edits, by training-set size, or by something else? (Needs training.)
- Why does `+365 days` (same day and month, one year later) lower P(satisfied) for NLI-init models? Is it the same
  phenomenon seen from the other side?
- Why are research_funding amounts far below the threshold read as satisfied, but enrollment credits are not?
  Thousands separators, the € sign, digit count, or tokenisation?
- Would a base-size or a decoder model show any of this?
- Why do the most accurate models have the *least* systematic errors (A14)? Is that a property of fine-tuning or of
  accuracy itself (fewer errors left, mostly near decision boundaries)?

## 6. What should be visibly yours

Your predictions for the training experiment, the choice of edit-distribution variants, the hand check of the 35
items, the positioning against Joshi & He, and the decision whether to pursue this at all. Keep a dated note of each
(e.g. in a personal `notes/` folder or in the PR discussion), so that authorship of the ideas is documented.
