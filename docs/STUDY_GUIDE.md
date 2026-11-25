# Study guide: understanding and defending ClauseShift

This guide explains every component of the project so that it can be reviewed and defended without the code
open. Each section ends with questions an examiner is likely to ask, with short answers. Numbers quoted here come
from `results/RESULTS.md` and `results/EXTENDED_ANALYSIS.md`; if they disagree, the results files are correct.

---

## 0. The project in one minute

ClauseShift asks whether NLI models notice the single clause that decides a case. Test items come in minimal pairs:
two rule documents that differ by one controlled edit, with labels computed from a rule specification. Off-the-shelf
NLI models solve at most 30% of label-changing pairs and mostly ignore the edit; thresholds, dates and
cross-references are almost never handled, and this survives a control for input format. Fine-tuning a small
DeBERTa-v3 on 2,400 synthetic items from other domains reaches about 80%, with numeric boundaries still weakest and
cross-references unlearnable unless seen in training. Training on complete pairs instead of single sides gives
+2 points, which passes the preregistered test but not a seed-level one, and reverses without NLI pre-training.
Methodologically, the preregistered occlusion evidence metric turned out to be uninformative (≈ 1.0 for every
model); a counterfactual removal test with specification-derived labels replaces it. Every hypothesis, deviation
and negative result is reported.

---

## 1. The research question in one paragraph

Rule-like documents (eligibility criteria, tender conditions, internal policies) often decide a case through one
clause: an exemption, a threshold, a date cutoff, a cross-reference. A model can be right on most items and still
ignore exactly that clause. ClauseShift measures this with **minimal pairs**: two documents that differ by one
controlled edit and share the same hypothesis. If the edit changes the gold label, a model that reads the clause
must change its answer. The questions are (RQ1) how much item accuracy overstates pair-level consistency,
(RQ2) which edits are missed, (RQ3) whether training on complete pairs helps more than training on the same number
of unpaired items, (RQ4) how much survives a change of vocabulary and templates, (RQ5) whether labels can be
guessed without reading the document.

**Likely questions.**
- *Why not use real contracts?* Real text gives no exact counterfactual: one cannot change one clause and know the
  new label without annotation. Synthetic rules give exact labels and per-operator attribution; the price is
  external validity (Section 9). CLAUSE (2026) and ContractNLI cover real text without exact single-edit control.
- *What is new?* Not minimal pairs (contrast sets, CAD) nor legal perturbations (CLAUSE). The contribution is
  methodological: exact single-edit operators with spec-derived labels, an explicit "insufficient" class reached by
  edits, near-miss controls, and a size-matched paired-vs-unpaired training comparison under family and template
  shift. See `docs/LITERATURE_REVIEW.md`.

---

## 2. Data generation

**Specification → text → label.** `src/clauseshift/generator.py` samples a rule specification `Spec` (polarity,
topic, optional threshold, date cutoff, location scope, exempted category, cross-reference) and a case `Case`
(category, location, number, date, claim polarity). The document is *rendered* from the spec with surface
templates; the label is *computed* from (spec, case) by `gold_label`, never from the text:

```
if topic != claimed obligation          -> insufficient
elif obligation negated                  -> not required
else:
    failing  = conditions the case violates (threshold, date, scope, own-category exemption, xref to Article 1)
    unknown  = threshold/date conditions on an attribute the case does not state
    if failing   -> not required
    elif unknown -> insufficient
    else         -> required
claim "is required"     : required -> entailed,     not required -> contradicted
claim "is not required" : required -> contradicted, not required -> entailed
```

Conditions are restrictive ("applies only if"), comparisons strict ("more than", "after"). Note the precedence:
a failing condition decides the case even if another condition is unknown.

**Operators** (14): 8 *flip* operators change the label (exception_add, xref_redirect, negation, threshold_cross,
date_cross, scope_restrict, condition_unknown, topic_swap); 3 *near-miss* operators make a lexically similar edit
that does not change the label for this case; 3 *invariant* operators change only surface form (paraphrase,
reorder, distractor_add). The edit direction of flip pairs is randomised (A→B or B→A).

**Splits.** Families (vocabulary domains) are disjoint: train = 5 families, dev = vehicles, test = enrollment and
research_funding. The last surface variant of every template is reserved for test. Train 4,800 items / 2,400 pairs;
dev 960 / 480; test 2,560 / 1,280.

**Shortcut control (design iteration v1 → v2).** A hypothesis-only TF-IDF classifier reached 0.60 dev accuracy on
v1 because near-miss pairs always had the label "required", so claim polarity predicted the label. The generator was
fixed *before* any neural model was run (`results/design_iterations/`), and the change is in the preregistration
changelog. This is the correct order: fixing a dataset after seeing model results would be HARKing-adjacent.

**Integrity.** `clauseshift.data.check` asserts pair structure, label relations per operator class, disjoint
families, no cross-split duplicates, no conflicting labels for identical inputs, and reserved templates absent from
train/dev. `scripts/verify_integrity.py` regenerates the data in memory and compares content hashes with
`data/manifest.json`.

**Likely questions.**
- *Are the labels correct?* They are correct if the templates express the spec faithfully. Unit tests check
  hand-written cases, and `tests/test_evidence.py` checks that deleting the added sentence of single-sentence edits
  reproduces the other side's label (706 pairs). Human agreement has **not** been measured: a blind sample of 112
  items is prepared in `review/` but not annotated.
- *Why double weight for condition_unknown and topic_swap?* They are the only operators that create
  "insufficient" items; without upweighting the class would be too rare for stable macro-F1.

---

## 3. Models

### 3.1 Baselines
- **Majority class**: predicts the most frequent training label (entailed).
- **TF-IDF + logistic regression**: unigram+bigram TF-IDF (sublinear tf, min_df=2), multinomial logistic
  regression, C chosen on dev from {0.1, 1, 10}. Two inputs: hypothesis only (shortcut control) and document ⊕
  hypothesis. A bag of n-grams cannot represent which category an exemption names relative to the case, so it is a
  floor, not a competitor.

### 3.2 Cross-encoder NLI models
Input: `[CLS] premise [SEP] hypothesis [SEP]` (RoBERTa uses `<s> … </s></s> … </s>`). The final hidden state of the
first token goes through a classification head to three logits z, and p = softmax(z). Every token of the premise can
attend to every token of the hypothesis in every layer, which is why cross-encoders are the standard architecture for
NLI (as opposed to bi-encoders that embed the two texts separately).

**DeBERTa-v3** (He et al., 2021/2023), used in xsmall (12 layers, hidden size 384) and base (12 layers, 768):
- *Disentangled attention*: each token has a content vector and a relative-position embedding; the attention score
  sums content→content, content→position and position→content terms, so relative position enters every layer.
- *Enhanced mask decoder*: absolute positions are added only near the output.
- *v3 pre-training*: ELECTRA-style replaced-token detection (a discriminator predicts which tokens a small generator
  replaced) with gradient-disentangled embedding sharing. Vocabulary of 128k tokens, so most parameters of the
  xsmall model are in the embedding matrix.
- The checkpoints used are already fine-tuned for NLI (SNLI+MNLI for the `cross-encoder/*` models;
  MNLI, FEVER-NLI and ANLI for MoritzLaurer's model; see the model cards).

**RoBERTa-large-MNLI**: 24 layers, hidden size 1024, BERT architecture with improved pre-training (dynamic
masking, more data, no next-sentence prediction), fine-tuned on MNLI.

**Label mapping**: entailment → entailed, contradiction → contradicted, neutral → insufficient. This mapping is a
modelling assumption: MNLI "neutral" means "the premise does not settle the hypothesis", which is close to, but not
the same as, "the rule does not settle this case".

### 3.3 Fine-tuning recipe (preregistered)
`cross-encoder/nli-deberta-v3-xsmall`, all parameters updated. Loss: cross-entropy
L = −(1/N) Σ log p(y_i | x_i). Optimiser AdamW (lr 3e-5, weight decay 0.01, decoupled from the gradient step),
linear warm-up over the first 10% of steps then linear decay to 0, batch size 16, 3 epochs, gradient-norm clipping
at 1.0, max length 320 tokens (documents are at most ~145 tokens, so nothing is truncated). The epoch with the best
**dev** macro-F1 is kept; test is evaluated once. Ablation: the same recipe from `microsoft/deberta-v3-xsmall`
(no NLI fine-tuning, new randomly initialised head, lr 5e-5).

**Conditions (RQ3), equal training size (2,400 items):**
- *paired*: 1,200 randomly chosen training pairs, both sides;
- *unpaired*: one random side of each of the 2,400 training pairs.

Both see the same operator mix in expectation. Paired training shows the model the contrast "same hypothesis,
one edit, different label"; unpaired training sees twice as many distinct documents/hypotheses, but never the
contrast. That trade-off — contrast vs. diversity — is exactly what Huang et al. (2020) and Joshi & He (2022)
debated for CAD.

*Operator hold-out*: all training pairs except xref_redirect and date_cross, testing whether sensitivity to an edit
type transfers from other edit types.

**Likely questions.**
- *Why only xsmall?* CPU-only compute. One run took ~15–20 minutes on 4 cores; base (hidden size 768 instead of
  384) would be an estimated ~4× slower. The
  zero-shot results show base models are better, so absolute numbers are a lower bound for the architecture.
- *Why epoch selection on dev macro-F1, not accuracy?* The "insufficient" class is the minority; macro-F1 does not
  reward ignoring it.
- *Is three seeds enough?* It shows whether the sign of an effect is stable, not its size precisely; per-seed
  differences are reported next to the mean.

---

## 4. Metrics

Let a test pair be (x_A, y_A), (x_B, y_B) with predictions ŷ_A, ŷ_B.

- **Accuracy** = mean over items of 1[ŷ = y]. **Macro-F1** = mean over the three labels of
  F1_l = 2TP_l / (2TP_l + FP_l + FN_l).
- **Pair accuracy** = mean over pairs of 1[ŷ_A = y_A ∧ ŷ_B = y_B].
- For flip pairs (y_A ≠ y_B): **flip-pair accuracy** = pair accuracy restricted to flip pairs;
  **flip sensitivity** = mean of 1[ŷ_A ≠ ŷ_B] (the answer changes at all).
- For near-miss/invariant pairs (y_A = y_B): **invariance** = mean of 1[ŷ_A = ŷ_B].
- **Failure decomposition** of flip pairs: solved (both correct) + insensitive (ŷ_A = ŷ_B, necessarily at
  least one wrong) + sensitive-but-wrong = 1.

Why pair accuracy matters: if a model answered each side independently with accuracy a, expected pair accuracy
would be a² (≈ 0.25 at a = 0.5). A model that ignores the edit gets exactly one side of every flip pair right when
its constant answer matches one side, so item accuracy 0.5 and flip-pair accuracy 0. The gap between the two is
therefore a direct reading of edit insensitivity.

**Calibration**: expected calibration error with 10 equal-width confidence bins,
ECE = Σ_b (n_b/N) |acc_b − conf_b|.

---

## 5. Statistics

**Unit of resampling = the minimal pair.** The two sides of a pair share a hypothesis and are highly dependent,
so resampling items would understate variance.

**Percentile bootstrap.** Draw B resamples of the n test pairs with replacement, recompute the metric on each,
and report the 2.5th and 97.5th percentiles. Implementation trick (`analyze_extended.py`): a resample is a vector
of counts w (how often each pair is drawn); any metric that is a ratio of sums is (wᵀa)/(wᵀb), so all B resamples
are one matrix product W·a.

**Paired comparison.** Two systems are evaluated on the same resample (same W row), and the difference is computed
per resample. Pairs that are hard for both systems cancel out, which makes the interval much narrower than
comparing two independent intervals.

**Seeds (H3).** With 3 seeds per condition there are two sources of variation: which test pairs (sampling) and
which training run (seed). The registered analysis pools seeds as if they were extra pairs. The extended analysis
uses a *cluster* bootstrap: resample test pairs and keep every seed's prediction on that pair, then average over
seeds. Per-seed differences are also listed, because with three seeds the seed variation is better shown than
modelled.

**Decision rules (preregistered).** A directional hypothesis is supported if the 95% interval of the relevant
difference excludes 0 in the predicted direction. The interval is not a p-value; a supported hypothesis means the
data are hard to reconcile with no effect *on this test set and these seeds*.

**Multiple comparisons.** Per-operator tables contain many intervals; they are descriptive. Only the registered
hypotheses carry decision rules.

---

## 6. Evidence analysis (occlusion)

For a correctly answered entailed/contradicted test item, remove each sentence in turn and find the sentence whose
removal lowers p(gold label) most; **hit@1** = that sentence is in the gold evidence set (computed on a fixed
random sample of 300 such items).

Two weaknesses, found during this work and documented in the preregistration deviations:
1. The **obligation sentence is in the evidence set of every decided item**, and removing it always makes the
   document silent on the claim. A model that only checks whether the obligation is mentioned obtains hit@1 ≈ 1.
   Hence the *strict* hit@1 that ignores the obligation sentence, compared with the hit rate of a random sentence.
2. Removal variants are rebuilt by joining sentences, which **drops the "Article k." headers**. A cross-reference
   ("Article 1 does not apply to …") cannot be resolved in any variant; the header-free full document is stored as
   a control, and cross-reference items are excluded from the counterfactual test.

**Counterfactual removal test** (exploratory). For every sentence, `clauseshift.evidence` derives the label of the
document without that sentence from the specification: removing the obligation → insufficient; removing the only
failing condition → the case becomes required (or insufficient, if another condition is unknown); removing any
other sentence → unchanged. The rule was validated against the generator. The test then asks whether the model's
prediction after each removal matches that label. This turns occlusion from "which sentence matters most" into a
behavioural test of whether the model's dependence on each sentence is the dependence the rule implies.

---

## 7. Experimental choices and why

| Choice | Reason | Alternative and why not |
|---|---|---|
| Disjoint families per split | measures transfer to new vocabulary, not memorised entities | random split: leaks names and objects |
| Reserved templates in test only | separates surface-form shift from vocabulary shift | none |
| Restrictive "only if" conditions | makes failure of a condition decide the case | permissive wording would make labels ambiguous |
| Equal-size paired vs. unpaired | isolates pairing from data quantity (the confound in early CAD work) | "add pairs to the full set": confounds size |
| Epoch selection on dev | test must be untouched | test-based selection inflates results |
| Preregistration before model runs | protects against choosing hypotheses after seeing results | — |
| Pair-level bootstrap | sides of a pair are dependent | item bootstrap: too narrow |

---

## 8. Results and how to defend them

Numbers below are test-set values from `results/EXTENDED_ANALYSIS.md` (95% bootstrap intervals over pairs).

**Zero-shot (RQ1, RQ2).** Flip-pair accuracy 0.07–0.30; item accuracy on the same pairs is 0.32–0.36 higher (H1
supported for all four models). Most failures are *insensitive*: the same answer on both sides of 61–77% of flip
pairs. Thresholds and dates ≤ 0.04, cross-references ≤ 0.11, negation up to 0.88 (H2 supported for the three
DeBERTa models; RoBERTa scores 0 on negation, so H2 cannot hold for it). Every zero-shot model is wrong on all 41
exact-boundary items.
- *Defence*: "Isn't this just label-semantics mismatch?" Partly, which is why the facts-in-premise control was
  run. It removes RoBERTa's never-entailed anomaly (+0.155 flip-pair accuracy) but leaves thresholds, dates and
  cross-references unsolved in both formats.

**Fine-tuning (RQ3).** Flip-pair accuracy ≈ 0.80 after 2,400 training items from other families. Paired − unpaired:
+0.021 [+0.006, +0.036], H3 supported by the registered rule.
- *Defence of the nuance*: the interval treats the three training runs as fixed. Per-seed differences are −0.002,
  +0.039, +0.026; a t-interval over seeds is [−0.032, +0.073]. The honest summary is "a small positive effect
  that is consistent across test families but not robust to training-run variance with three seeds". This sits
  between Huang et al. (2020, no gain at equal size) and the positive CAD results: with edit diversity controlled by
  design, the contrast signal helps a little, mostly on the hardest operators (scope restriction +0.125).
- *Why paired might help*: a pair is a direct contrastive signal: identical hypothesis, one clause changed,
  different label. The gradient on such a pair pushes the representation of exactly the changed clause.
- *Why it might not help much*: unpaired training sees twice as many distinct cases and documents; with
  synthetic templates the model may learn the clause semantics from diversity alone.

**Ablations.** Operator hold-out (3 seeds): unseen cross-reference edits 0.04, unseen date edits 0.81. No NLI
pre-training (3 seeds): flip-pair accuracy 0.43 (paired) and 0.52 (unpaired); thresholds and dates ≤ 0.03.
- *"One no-NLI run failed. Why not re-run it?"* Re-running only the runs one dislikes is a form of selection. The
  failure is visible on dev alone (dev macro-F1 0.56 against ≥ 0.75 for every other run), it is reported in the
  training-diagnostics table, and its effect on the comparison is shown by the per-seed values. A fair remedy would
  be a pre-specified longer budget or more seeds for every condition, not a replacement of one run.
- *"Why do cross-references not transfer from exemptions?"* With an inline exemption the case's category and the
  exempted category are in the same sentence as the rule. A cross-reference requires binding "Article 1" to the
  first article's obligation, which never occurs in the other operators. The model has to see that binding.

**Shift (RQ4).** H4 not supported: reserved templates cost ≈ 4 points (also after stratifying by operator), but
test accuracy exceeds dev accuracy because the dev family is harder. Lesson: with one dev family, "dev → test drop"
measures family difficulty as much as shift; a leave-one-family-out design would separate them.

**Evidence.** The registered hit@1 is 0.97–1.00 for *every* neural model, including zero-shot models that ignore
most edits, so it does not discriminate between them. In 87–98% of the sampled items the top sentence is the
obligation, and the strict hit@1 (ignoring the obligation) is *below* the random-sentence rate for every model. The
counterfactual removal test does discriminate: when the decisive condition is removed, the fine-tuned models
produce the label the specification predicts in 80–88% of cases, the zero-shot models in 0–72% (on 4–32 removals,
so those estimates are noisy). Lesson: top-1 occlusion is dominated by the sentence whose removal changes the label most
radically (to "insufficient"), so it under-reports the use of conditions; a behavioural test with a known
counterfactual label is more informative.

## 9. Limitations to state before being asked

- Synthetic template text, ~100-token documents, few conditions per rule: results describe controlled rule
  language, not real regulations or contracts.
- Labels are specification-derived; no human agreement yet.
- CPU budget: compact encoders, three seeds, no instruction-tuned LLMs, no hyper-parameter search.
- Zero-shot numbers mix edit sensitivity with label-semantics mismatch (MNLI neutral ≠ insufficient) and input
  format (tested with facts_in_premise).
- Occlusion is a perturbation measure; removing a sentence creates an input the model has never seen.
- Per-operator accuracy is confounded with document complexity (negation documents have no conditions).

---

## 10. Glossary

- **Minimal pair**: two inputs differing by one controlled edit.
- **Flip / near-miss / invariant operator**: edit that changes / looks like it should change but does not / only
  rephrases.
- **Contrast set**: expert-written minimal perturbations of test items (Gardner et al., 2020).
- **CAD**: counterfactually augmented data, human-edited training examples with flipped labels (Kaushik et al., 2020).
- **Hypothesis-only baseline**: classifier that sees only the hypothesis; above-chance accuracy reveals annotation
  artefacts (Poliak et al., 2018; Gururangan et al., 2018).
- **Cross-encoder**: a model that encodes premise and hypothesis jointly in one sequence.
- **Percentile bootstrap / paired bootstrap / cluster bootstrap**: see Section 5.
