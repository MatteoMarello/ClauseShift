# ClauseShift: do NLI models notice the one sentence that changes the answer?

Technical report. Matteo Marello. Code, data and predictions: this repository.
Every number below is taken from `results/RESULTS.md` (registered analyses, `scripts/analyze.py`) or
`results/EXTENDED_ANALYSIS.md` (decision rules, paired and cluster bootstraps, exploratory analyses,
`scripts/analyze_extended.py`). Labels are generator-derived; human validation is pending (Section 7).

## 1. Motivation

Rule-like documents — tender conditions, eligibility criteria, internal policies — are routinely summarised or
checked by language models. In such documents the answer for a specific case often hinges on one clause: an
exemption, a threshold, a cutoff date, a reference to another article. A model that reads the document
"approximately" can get most items right and still fail exactly where a clause changes the conclusion.

Item-level accuracy hides this. ClauseShift therefore evaluates models on **minimal pairs**: two documents that
differ by a single edit, paired with the same hypothesis about a case. A model passes a pair only if it answers
both sides correctly.

## 2. Task and data

*Input*: a document of numbered articles (an obligation, its conditions and exemptions, unrelated provisions) and a
hypothesis (facts about one case + the claim that the case is / is not subject to the obligation).
*Output*: `entailed`, `contradicted`, or `insufficient`.

Documents are rendered from a rule specification; the gold label is computed from the specification and the case
(`src/clauseshift/generator.py`, `gold_label`). Fourteen operators edit the specification: eight change the label
(exemption added, cross-reference redirected, negation, numeric threshold crossed, date cutoff crossed, scope
restricted, condition on an unstated attribute added, obligation replaced), three are near misses that change the
text but not the label for the case (exemption of another category, threshold moved on the same side, scope set to
the case's own location), and three are surface invariances (paraphrase, reordering, distractor article).
A quarter of the threshold and date edits put the cutoff exactly at the case value, testing strict comparisons.

Eight fictional families (procurement, library, travel, housing, food safety, vehicles, enrollment, research
funding) define vocabulary. Train, dev and test use disjoint families, and the last surface variant of every
template appears only in test. Train: 4,800 items / 2,400 pairs; dev: 960 / 480; test: 2,560 / 1,280.

Shortcut control. A hypothesis-only classifier on the first data version reached 0.60 dev accuracy, because
near-miss pairs always had the label "required". The generator was changed before any neural model was run
(`results/design_iterations/`). On v2 the hypothesis-only model reaches 0.43 (majority 0.36), and, by construction,
0.00 flip-pair accuracy.

## 3. Systems

- Majority class; TF-IDF + logistic regression on the hypothesis alone and on document ⊕ hypothesis.
- Zero-shot NLI cross-encoders trained on MNLI-style data (entailment / contradiction / neutral mapped to
  entailed / contradicted / insufficient): DeBERTa-v3 xsmall and base (cross-encoder), DeBERTa-v3-base
  MNLI-FEVER-ANLI, RoBERTa-large-MNLI. Each is run in the registered *standard* format (premise = document,
  hypothesis = case facts + claim) and, as an exploratory control for format mismatch, in a *facts-in-premise*
  format (premise = document + "Case:" + facts, hypothesis = claim only).
- Fine-tuned `cross-encoder/nli-deberta-v3-xsmall` (CPU), three seeds per condition:
  - **paired**: 1,200 complete training pairs (2,400 items);
  - **unpaired**: one random side of each of 2,400 training pairs (2,400 items);
  - **operator hold-out**: all training pairs except `xref_redirect` and `date_cross`;
  - **no NLI pre-training**: the same recipe from `microsoft/deberta-v3-xsmall`.

Epochs are selected on dev macro-F1; each final model is applied to test once.

## 4. Metrics

Accuracy and macro-F1 per item; **pair accuracy** (both sides correct); for flip pairs **flip accuracy** (both
correct) and **flip sensitivity** (the prediction changes); for near-miss and invariant pairs **invariance** and
invariant-pair accuracy. 95% intervals: percentile bootstrap over pairs; model differences: paired bootstrap on
the same resamples; seed groups: mean over seeds with a cluster bootstrap that keeps all seeds of a test pair
together (the registered seed-pooled bootstrap is also reported). Evidence: occlusion hit@1 on 300 correctly
answered test items, plus two exploratory measures introduced because hit@1 turned out to be weakly informative
(Section 5.5): a strict hit@1 ignoring the obligation sentence, and a counterfactual removal test against labels
derived from the specification.

## 5. Results

To be written from `results/RESULTS.md` once all runs have finished.

## 6. Discussion

To be written after the results.

## 7. Limitations

- Synthetic, template-generated text with short documents (about 100 tokens) and few conditions per rule. Results
  describe behaviour on controlled rule language, not on real contracts or regulations.
- Labels are derived from the specification. They are as reliable as the templates; a blind human annotation of
  112 test items is prepared but not yet done.
- MNLI "neutral" is not the same concept as "insufficient evidence for this case"; zero-shot numbers partly measure
  this label mismatch, which is why fine-tuned models are reported separately.
- CPU-only compute (a 4-core cloud CPU): compact encoders, at most three seeds, no hyper-parameter search, no
  instruction-tuned LLMs.
- Occlusion measures sensitivity to removing a sentence, not whether the model reasons faithfully; removal variants
  also drop the article headers (Section 5.5).
- Per-operator results are confounded with document complexity: negation documents carry no conditions.
- Only two test families; family-level conclusions rest on two vocabularies.

## 8. Reproducibility

`python scripts/build_data.py` regenerates the data (hashes in `data/manifest.json`); `scripts/verify_integrity.py`
checks data, prediction files and reported metrics without writing data. `scripts/run_baselines.py`,
`scripts/run_zero_shot.py`, `scripts/run_cloud_queue.sh` (fine-tuning, facts-in-premise, evidence),
`scripts/analyze.py`, `scripts/analyze_extended.py` and `scripts/error_analysis.py` reproduce every number. Model
revisions, hardware and selected epochs are stored in `results/predictions/*/meta.json`; training logs in `logs/`.
Fine-tuned weights are not distributed.

## AI-assisted development

The code, data generator, analyses and documentation were produced with substantial assistance from an AI coding
assistant, working from the author's instructions. All reported numbers are generated by the scripts listed in
Section 8 from saved predictions; none was entered by hand. The labels have not been validated by human annotators,
and no claim in this report rests on human verification that has not taken place.
