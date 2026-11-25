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

Test set: 2,560 items in 1,280 minimal pairs from two families never seen in training. Brackets are 95% bootstrap
intervals over pairs. Figures are in `results/figures/`.

### 5.1 Baselines and shortcut control (RQ5)

The majority class reaches 0.390 accuracy, the hypothesis-only TF-IDF model 0.415 [0.398, 0.432], and the
document + hypothesis TF-IDF model 0.413 [0.395, 0.432] with flip-pair accuracy 0.083 [0.064, 0.102]. H5
(hypothesis-only flip-pair accuracy ≤ 0.05) is supported with 0.000, but this holds by construction: both sides of
a pair share the hypothesis and flip pairs have different labels, so any deterministic hypothesis-only classifier
scores 0. The informative number is the small item-accuracy margin of the hypothesis-only model over the majority
class (+0.025), which bounds the remaining hypothesis-side cues after design iteration v2.

### 5.2 Zero-shot NLI models (RQ1, RQ2)

| Model (standard format) | Accuracy | Item acc. on flip pairs | Flip-pair acc. | Gap |
|---|---|---|---|---|
| DeBERTa-v3-xsmall NLI | 0.399 [0.380, 0.419] | 0.472 [0.452, 0.491] | 0.129 [0.107, 0.153] | 0.343 [0.327, 0.359] |
| DeBERTa-v3-base NLI | 0.504 [0.484, 0.524] | 0.612 [0.595, 0.628] | 0.263 [0.233, 0.293] | 0.349 [0.333, 0.365] |
| DeBERTa-v3-base MNLI-FEVER-ANLI | 0.531 [0.511, 0.551] | 0.623 [0.603, 0.642] | 0.304 [0.272, 0.337] | 0.319 [0.303, 0.335] |
| RoBERTa-large-MNLI | 0.378 [0.358, 0.397] | 0.426 [0.408, 0.444] | 0.070 [0.053, 0.088] | 0.356 [0.340, 0.371] |

**H1 is supported for all four models**: the lower bound of every gap exceeds 0.10. The gap is mostly explained by
*insensitivity*: 61–77% of flip pairs receive the same prediction on both sides, against 4–16% that change the
prediction but get a side wrong (Figure 4). High invariance on near-miss and invariant pairs (0.89–0.97) must be
read together with this: a model that rarely changes its answer is invariant for free.

**H2 is supported for the three DeBERTa models and not for RoBERTa-large-MNLI.** For the DeBERTa models, flip-pair
accuracy on exception, cross-reference, threshold and date edits is 0.30 to 0.88 below negation, with every
interval excluding 0. Thresholds and dates reach at most 0.04, cross-references at most 0.11, and conditions on an
unstated attribute at most 0.04. RoBERTa-large-MNLI scores 0.00 on negation in the standard format, so the
comparison cannot go in the predicted direction (Figure 3). On the exact-boundary side of threshold and date pairs
("more than 50" with the value 50; 41 test items), every zero-shot model is wrong on every item, in both formats.

### 5.3 Input format: a control for the zero-shot setting (exploratory)

In the registered format, the case facts are part of the hypothesis. To an MNLI-trained model these facts are
unsupported by the premise, which pushes predictions away from `entailment`; RoBERTa-large-MNLI never predicts
`entailed` (0 of 2,560 items). Moving the facts into the premise (Figure 1, Figure 2):

| Model | Flip-pair acc., standard → facts in premise | Difference | `entailed` share of predictions |
|---|---|---|---|
| DeBERTa-v3-xsmall NLI | 0.129 → 0.176 | +0.047 [+0.028, +0.067] | 0.047 → 0.112 |
| DeBERTa-v3-base NLI | 0.263 → 0.290 | +0.027 [+0.013, +0.042] | 0.379 → 0.443 |
| DeBERTa-v3-base MNLI-FEVER-ANLI | 0.304 → 0.320 | +0.016 [−0.008, +0.041] | 0.293 → 0.460 |
| RoBERTa-large-MNLI | 0.070 → 0.225 | +0.155 [+0.122, +0.190] | 0.000 → 0.448 |

The format accounts for RoBERTa's anomaly (its negation flip-pair accuracy rises from 0.00 to 1.00) and gives small
gains for the DeBERTa models, while the share of `insufficient` predictions falls to 0.04–0.37 (gold: 0.24). It
does not change the operator ranking: threshold and date edits remain at ≤ 0.04 and cross-references at ≤ 0.11 in
both formats. The zero-shot failure on decisive clauses is therefore not an artefact of where the facts are placed.

### 5.4 Fine-tuning and the paired-vs-unpaired comparison (RQ3)

DeBERTa-v3-xsmall (NLI-initialised) fine-tuned on 2,400 training items, three seeds per condition, epoch selected on
dev macro-F1 (Figure 5):

| Condition | Dev acc. | Test acc. | Pair acc. | Flip-pair acc. | Invariance |
|---|---|---|---|---|---|
| paired (1,200 pairs) | 0.838 | 0.904 ± 0.019 | 0.836 ± 0.025 | 0.815 ± 0.021 | 0.937 ± 0.012 |
| unpaired (2,400 single sides) | 0.843 | 0.891 ± 0.005 | 0.814 ± 0.008 | 0.795 ± 0.007 | 0.919 ± 0.012 |

(mean ± SD over seeds). Fine-tuning on 2,400 items of five other families raises flip-pair accuracy from 0.129 for
the same model zero-shot to about 0.80 on unseen families; insensitive flip pairs fall from 75% to 13–15%. The
fine-tuned models are also well calibrated (ECE 0.013–0.026, against 0.35–0.56 for the zero-shot models).

**H3 (paired > unpaired in flip-pair accuracy).** Seed-averaged difference **+0.021**; registered seed-pooled
bootstrap [+0.006, +0.036], cluster bootstrap over test pairs [+0.007, +0.035]. By the preregistered rule H3 is
**supported**. The evidence is weak in two respects. First, the per-seed differences are −0.002, +0.039 and +0.026;
treating training runs as the random unit gives a 95% t-interval of [−0.032, +0.073] (df = 2), which includes 0.
The registered rule treats seeds as fixed, so its interval reflects test-set sampling only. Second, the effect is
small relative to the gain from fine-tuning itself (+0.67 to +0.69), and paired training is more seed-dependent (SD 0.021
vs. 0.007). The direction is consistent across both test families (enrollment +0.027 [+0.009, +0.045];
research_funding +0.015 [−0.007, +0.038]) and the per-operator differences are largest on the hardest edits
(scope restriction +0.125 [+0.067, +0.187]; thresholds +0.054 and dates +0.046, both intervals including 0). These
per-operator comparisons are descriptive and uncorrected for multiplicity.

**H2 after fine-tuning.** Negation is solved (1.00) and the H2 ordering still holds for both conditions: thresholds
(0.46–0.51), dates (0.62–0.67) and scope restriction (0.54–0.67) remain the hardest edits; exceptions (0.92–0.94)
and cross-references (0.84–0.86) are largely learned. On the exact-boundary side of threshold and date pairs,
accuracy varies between 0.39 and 0.83 across runs, against 0.76–0.84 on the other items of these operators.

### 5.5 Shift (RQ4)

| Condition | Dev − test accuracy | Seen − reserved templates (raw) | Seen − reserved (operator-stratified) |
|---|---|---|---|
| paired | −0.066 [−0.091, −0.042] | +0.042 [+0.022, +0.061] | +0.038 [+0.019, +0.056] |
| unpaired | −0.047 [−0.074, −0.022] | +0.041 [+0.019, +0.062] | +0.037 [+0.015, +0.057] |

**H4 is not supported.** Its second half holds: test items with a reserved template are about 4 points harder, also
after stratifying by operator. Its first half fails in the opposite direction: test accuracy is *higher* than dev
accuracy. The dev family (vehicles) is harder than the two test families for these models, so "dev → test"
conflates family difficulty with distribution shift. With one dev family and two test families, family difficulty
cannot be separated from shift; this is a design limitation, not evidence that the models are robust to shift.

### 5.6 Ablations

Operator hold-out and the no-NLI-pre-training ablation: runs in progress; completed from
`results/EXTENDED_ANALYSIS.md` when the queue finishes.

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
