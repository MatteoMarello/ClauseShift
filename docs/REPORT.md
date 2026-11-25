# ClauseShift: do NLI models notice the one sentence that changes the answer?

Technical report, preliminary. Matteo Marello. Code, data and predictions: this repository.
Status: all numbers below come from `results/summary.json`, produced by `scripts/analyze.py`. Labels are
generator-derived; the human validation is pending (Section 7).

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
  MNLI-FEVER-ANLI, RoBERTa-large-MNLI.
- Fine-tuned `cross-encoder/nli-deberta-v3-xsmall` (CPU), three seeds per condition:
  - **paired**: 1,200 complete training pairs (2,400 items);
  - **unpaired**: one random side of each of 2,400 training pairs (2,400 items);
  - **operator hold-out**: all training pairs except `xref_redirect` and `date_cross`;
  - **no NLI pre-training**: the same recipe from `microsoft/deberta-v3-xsmall`.

Epochs are selected on dev macro-F1; each final model is applied to test once.

## 4. Metrics

Accuracy and macro-F1 per item; **pair accuracy** (both sides correct); for flip pairs **flip accuracy** (both
correct) and **flip sensitivity** (the prediction changes); for near-miss and invariant pairs **invariance** and
invariant-pair accuracy. 95% intervals: bootstrap over pairs; model differences: paired bootstrap on the same
resamples. Evidence: occlusion hit@1 on 300 correctly answered test items.

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
- CPU-only compute: compact encoders, three seeds, no instruction-tuned LLMs.
- Occlusion measures sensitivity to removing a sentence, not whether the model reasons faithfully.

## 8. Reproducibility

`python scripts/build_data.py` regenerates the data (hashes in `data/manifest.json`). `scripts/run_baselines.py`,
`scripts/run_zero_shot.py`, `scripts/run_finetune_queue.sh`, `scripts/run_evidence_zero_shot.py`,
`scripts/analyze.py`, `scripts/error_analysis.py` reproduce every number. Model revisions are pinned in
`results/predictions/*/meta.json`.

## AI assistance

The code, data generator and this report were drafted with an AI coding assistant (Claude Code) under Matteo's
direction. The design choices, results and limitations are documented so that each step can be checked
independently.
