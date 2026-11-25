# Preregistration

Written and committed on 2026-11-25, together with the frozen dataset (`data/manifest.json`), **before any model
was run on ClauseShift**. Later changes to this file are listed in the changelog at the bottom; analyses not listed
here are reported as exploratory.

## Task

Three-way inference over short rule-like documents. Input: a document (numbered articles stating an obligation,
its conditions, exemptions and unrelated provisions) and a hypothesis (facts about one case + a claim that the case
is / is not subject to the obligation). Output: `entailed`, `contradicted`, or `insufficient` (the document does not
settle the claim for this case).

Conditions are phrased restrictively ("applies only if …"), so a failed condition licenses `contradicted`. A
condition on an attribute the case does not state licenses `insufficient`. This is a reading-comprehension task over
fictional rules, not legal reasoning about real law.

## Research questions and hypotheses

- **RQ1 (paired consistency).** Off-the-shelf NLI models: how much lower is pair accuracy (both sides of a minimal
  pair correct) than item accuracy?
  - H1: for every off-the-shelf model, pair accuracy on flip pairs is at least 10 points below item accuracy.
- **RQ2 (operators).** Which minimal edits do models miss?
  - H2: exception-based edits (`exception_add`, `xref_redirect`) and numeric/date boundary edits
    (`threshold_cross`, `date_cross`) have lower flip-pair accuracy than `negation`.
- **RQ3 (counterfactual training).** At equal training size, does fine-tuning on complete minimal pairs improve
  pair-level consistency on held-out families compared with fine-tuning on one side of each pair?
  - H3: paired training gives higher flip-pair accuracy on the test families. (Prior evidence is mixed:
    Huang et al. 2020; Joshi & He 2022. A null result is a valid outcome.)
- **RQ4 (shift).** How much of the in-distribution performance survives a change of family (vocabulary) and of
  surface templates?
  - H4: fine-tuned models lose accuracy from dev to test, and lose more on test items that use reserved templates.
- **RQ5 (shortcuts).** Can labels be predicted without reading the document?
  - H5: a hypothesis-only classifier stays near chance on flip pairs (pair accuracy ≤ 5%), because each hypothesis
    occurs with two different labels.

## Data and splits (frozen)

- Generator: `src/clauseshift/generator.py`; config `configs/data.json` (seed 20261125).
- 14 operators: 8 flip, 3 near-miss (lexical change, same label), 3 invariant (paraphrase, reorder, distractor).
- Families: train = procurement, library, travel, housing, food_safety; dev = vehicles; test = enrollment,
  research_funding. The last surface variant of every template is reserved for test.
- Labels are **generator-derived** (computed from the rule specification). They are not human-validated. A blind
  stratified sample is queued for human annotation (`review/`); its agreement will be reported when available.

## Models

1. Majority class; TF-IDF + logistic regression on the hypothesis only; TF-IDF + logistic regression on
   document ⊕ hypothesis (vocabulary fitted on train only).
2. Off-the-shelf NLI cross-encoders, zero-shot, labels mapped entailment→entailed, contradiction→contradicted,
   neutral→insufficient: `cross-encoder/nli-deberta-v3-xsmall`, `cross-encoder/nli-deberta-v3-base`,
   `MoritzLaurer/DeBERTa-v3-base-mnli-fever-anli`, `FacebookAI/roberta-large-mnli`.
   (Revisions pinned in the results files.)
3. Fine-tuning (CPU budget): `cross-encoder/nli-deberta-v3-xsmall`, 3 seeds per condition.
   - RQ3 conditions, equal size (2,400 items): **paired** = 1,200 complete pairs; **unpaired** = one randomly chosen
     side of each of 2,400 pairs.
   - Ablation: same recipe from `microsoft/deberta-v3-xsmall` (no NLI pre-training).
   - Ablation: operator hold-out — train without `xref_redirect` and `date_cross` pairs, test on them.
   - Epoch selection on dev macro-F1 only. The test split is evaluated once per final model.

## Metrics

- Item level: accuracy, macro-F1.
- Pair level (unit = minimal pair): **pair accuracy** (both sides correct); for flip pairs, **flip sensitivity**
  (prediction changes between sides) and **flip accuracy** (both correct); for near-miss and invariant pairs,
  **invariance** (same prediction on both sides).
- Per operator, per family, reserved vs. non-reserved templates.
- Evidence (transformers): occlusion — remove each sentence, the sentence whose removal most lowers the probability
  of the predicted label is the model's evidence; **evidence hit@1** = it belongs to the gold evidence set
  (computed on correctly predicted entailed/contradicted test items).
- Uncertainty: 95% percentile bootstrap intervals, 1,000 resamples of **pairs** (pairs are the independent unit;
  both sides stay together). Model comparisons: paired bootstrap of the difference on the same resamples.
  Fine-tuning: mean ± SD over 3 seeds, plus the bootstrap on the seed-pooled predictions.

## Decision rules

- H1/H2/H4: supported if the bootstrap 95% interval of the relevant difference excludes 0 in the stated direction.
- H3: supported if the seed-averaged difference is positive and its paired bootstrap interval excludes 0.

## Known limitations at registration

Synthetic, template-generated English text; four categories and a handful of conditions per family; labels derived
from a specification rather than annotated; zero-shot models were trained on MNLI-style data whose neutral class
does not exactly match "insufficient evidence".

## Deviations and additions after registration

Recorded on 2026-11-25, before any fine-tuned model was evaluated on test. The sections above are unchanged.

1. **Compute.** The fine-tuning runs were planned for a 6-core laptop CPU (12 threads). They were executed in a cloud
   container with a 4-core Intel Xeon CPU and no GPU. The training recipe (model, data selection, optimiser,
   learning rates, epochs, batch size, max length, seeds, epoch selection on dev) is unchanged. Hardware and thread
   count are now detected at run time and stored in each `meta.json`. A re-run of a stored zero-shot system on the
   new hardware reproduced its dev predictions exactly (`results/reproduction_check.json`).
2. **Order and scope of the fine-tuning runs.** One run took about 20 minutes (paired/unpaired) to 30 minutes
   (operator hold-out) on this hardware. Runs were executed in order of informativeness
   (`scripts/run_cloud_queue.sh`): paired and unpaired, seeds 0–2, interleaved by seed (H3); operator hold-out,
   seed 0; the no-NLI-pre-training ablation, seed 0; operator hold-out, seeds 1–2 last and only if the budget
   allowed. The model section above specifies three seeds per condition; the original run list
   (`scripts/run_finetune_queue.sh`) already planned a single seed for the no-NLI ablation. Its seeds 1–2 were
   not run, so results for that ablation rest on one seed per condition and are reported as indicative only. Any run not completed is listed as such in `CLOUD_RESUME.md` and in
   the report; no missing run is replaced by an estimate.
3. **H1 decision rule, made explicit.** "At least 10 points below" is evaluated as: the 95% bootstrap interval
   of (item accuracy on flip pairs − flip-pair accuracy − 0.10) lies above 0.
4. **H3 inference.** The registered analysis (seed-pooled predictions, pairs from different seeds treated as
   independent units) is kept in `scripts/analyze.py`. Because the same test pair appears once per seed, that
   bootstrap can understate uncertainty; `scripts/analyze_extended.py` adds a cluster bootstrap that resamples
   test pairs and keeps all seeds of a pair together. Both are reported; the decision uses the registered one, and
   any disagreement between the two is stated. Because both bootstraps treat the seeds as fixed, a seed-level
   t-interval over the per-seed differences is reported as a further sensitivity check.
5. **Evidence (occlusion).** The registered hit@1 metric and its sample are unchanged. Two problems with it were
   found while implementing the analysis and are reported, not fixed silently: (a) the obligation sentence belongs
   to the gold evidence of every decided item, and removing it always makes the document silent on the claim, so
   hit@1 can be high without the model using the edited clause; (b) removal variants are built by joining the
   remaining sentences, which drops the "Article k." headers, so cross-references cannot be resolved in any
   variant. Per-item occlusion records (including a header-free, no-removal control) are now saved, and two
   exploratory measures are added: a strict hit@1 that ignores the obligation sentence, and a counterfactual
   removal test that compares each prediction after a sentence is removed with the label the specification
   assigns to the shortened document (`src/clauseshift/evidence.py`, validated against the generator in
   `tests/test_evidence.py`).
6. **Exploratory analyses (not registered).** Zero-shot evaluation with the case facts moved into the premise
   (`--format facts_in_premise`); decomposition of flip-pair failures into insensitive and sensitive-but-wrong;
   document complexity by operator; operator-stratified reserved-template comparison for H4; 2,000 bootstrap
   resamples in the extended analysis (1,000 in the registered tables).

## Changelog
- 2026-11-25: initial version (data v1, commit 8bed406).
- 2026-11-25: data v2, before any neural model. The hypothesis-only control exposed a claim-polarity shortcut in
  near-miss/invariant pairs (v1 dev accuracy 0.604). Near-miss and invariant pairs now have balanced shared labels.
  See `results/design_iterations/README.md`. Splits, operators, models, metrics and hypotheses are unchanged.
- 2026-11-25: added "Deviations and additions after registration" (compute, run order and scope, explicit H1
  rule, seed-aware H3 bootstrap, occlusion caveats, exploratory analyses). Hypotheses, splits, models and metrics
  are unchanged.
