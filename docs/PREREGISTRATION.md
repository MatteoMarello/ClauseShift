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

## Changelog
- 2026-11-25: initial version (data v1, commit 8bed406).
- 2026-11-25: data v2, before any neural model. The hypothesis-only control exposed a claim-polarity shortcut in
  near-miss/invariant pairs (v1 dev accuracy 0.604). Near-miss and invariant pairs now have balanced shared labels.
  See `results/design_iterations/README.md`. Splits, operators, models, metrics and hypotheses are unchanged.
