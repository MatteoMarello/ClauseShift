# Scientific audit of the existing ClauseShift results

Scope: the 15 registered fine-tuning runs, 4 zero-shot models (two input formats) and baselines on `main` + PR #1.
Everything below is **exploratory**: it was computed after the original results were known, from saved predictions,
by `research_next/scripts/audit_saved_predictions.py` (tables: `results/AUDIT_TABLES.md`),
`program_fingerprint.py`, `lazy_reader.py` and `lazy_agreement.py`. No original result, prediction or data file was
changed.

## Summary of verdicts

| Phenomenon | Survives the checks? | Main threat found |
|---|---|---|
| 1. Unseen cross-references do not transfer (0.04) | The number is real, but the test is **unfair** in Geiger et al.'s sense, so it says nothing about compositional ability | The construction "Article k …" never occurs in training |
| 2. Inline exemption vs. the same exemption by reference | Matched on document length, the gap persists (0.977 vs 0.058 for the hold-out models) | In-distribution cross-reference accuracy is **not interpretable**: the label is a deterministic function of the article digit |
| 3. Numeric and date boundaries | Yes, and sharper than reported: **100%** of fine-tuned boundary errors reproduce the non-strict reading | Only 38 boundary pairs in test (23 + 17 distinguishing items) |
| 4. Occlusion hit@1 does not discriminate | Yes, and worse: a reader that ignores every condition scores hit@1 = 1.00 | – |
| 5. Counterfactual removal test | Discriminates fine-tuned from zero-shot models | Conditioning on correct items leaves few decisive removals for weak models; must use a fixed item set |
| 6. Pairing effect depends on initialisation and seed | Yes; the gain concentrates where pairs differ by one token | One non-converged run; three seeds |
| 7. Family difficulty vs. shift | Dev family is harder; within test, one family is harder on dates only | Two test families cannot separate vocabulary from template difficulty |

## 1. Cross-references not seen in training

The operator hold-out removes every `xref_redirect` pair from training. Audit A6 shows that cross-reference sentences
occur **only** in `xref_redirect` pairs (0 of 520 elsewhere). The hold-out models therefore never see the
construction "Article k does not apply to …" with any content. Under Geiger et al.'s (2019) fairness criterion (every
intermediate function must receive all its inputs in training), this test cannot distinguish "cannot compose
reference resolution with exemption semantics" from "has never seen a reference". The original report's sentence
"resolving 'Article 1' is a distinct skill that had to be seen in training" is supported, but only in this weak sense;
it does not establish a compositional failure. A fair design is given in `EXPERIMENT_PROTOCOL.md`.

## 2. Inline exemption vs. exemption by reference

Matched on the number of sentences (A2), the hold-out models solve inline exemptions (0.977) and fail references
(0.058), so length and number of conditions do not explain the gap. The in-distribution result (0.84–0.86 for models
trained on references) is **not evidence of reference resolution**: in all 520 cross-reference items the exempted
category is the case's own (A6), so

    label = f(refers to "Article 1", claim polarity)

holds without exception (table A6). The behavioural program identification confirms this as an identifiability
gap: of 2,560 test items, **0** distinguish "resolve the reference" from "react to the digit 1" (`PROGRAM_FINGERPRINT.md`,
identifiability table). Pilot 2 tests which of the two the models do.

## 3. Numeric and temporal boundaries

Audit A3 (38 boundary pairs): for every fine-tuned group, **all** boundary-side errors reproduce the label of the
pair's other side, i.e. the model reads "more than 50" as "at least 50" (or "after 3 May" as "on or after"); zero-shot
DeBERTa-base models do so in 92–95% of their errors. Correct boundary-side rates for fine-tuned NLI-initialised
models are 0.54–0.66 vs. 0.91–0.94 for the other side of the same pairs. Alternative explanations checked:
- *Number format / tokenisation*: threshold flip-pair accuracy is the same for plain integers (enrollment, 0.63–0.68)
  and €-amounts with thousands separators (research_funding, 0.65–0.68).
- *Label bias*: errors on threshold/date items are split between entailed and contradicted (A4), so no single label
  absorbs them; the error is relational, not a prior.
- *Training exposure*: 25% of the training threshold/date pairs are boundary pairs by design, so the strict reading
  was in the training signal.
Unexplained: date flip-pair accuracy differs strongly by family (enrollment 0.28–0.34 vs. research_funding 0.59–0.66
for paired/unpaired models), while thresholds do not. The date wording differs ("applications received after" vs.
"projects starting after"); we did not test why.
Statistical caveat: the boundary analysis rests on 38 pairs (23 threshold + 17 date items that distinguish strict
from non-strict); it motivates a dedicated test, it does not by itself establish a general claim.

## 4. Occlusion hit@1

Registered hit@1 is 0.97–1.00 for all neural models (accuracy 0.38–0.93). Pilot 1: the **lazy reader**, which never
reads a condition, obtains hit@1 = 1.00 under the identical protocol (300 sampled items; the top sentence is the
obligation in 300/300 cases). The metric is therefore satisfiable by a reader with no condition-level competence. The
cause is structural, not adversarial: one sentence (the obligation) is necessary for every decided label, so it wins
any "largest drop on removal" ranking. This is distinct from the adversarial inflation of ERASER metrics shown by
Hsia et al. (2024) and from the OOD argument of Hase et al. (2021), although both apply here as well (removal
variants also lose their article headers).

## 5. Counterfactual removal test

The test compares each post-removal prediction with the label the specification gives to the shortened document
(validated on 706 generator pairs). It separates the fine-tuned models (80–88% agreement on decisive removals) from
zero-shot ones (0–72%). Conceptual problem found: the test is computed on the items each model answered correctly,
so weak models contribute few decisive removals (4–32), and the lazy reader contributes **none** (it is never right
when a condition decides the label). A valid version must use one fixed item set for all models and report
agreement for all removal types, including the lazy reader as a negative control.

## 6. Pairing, initialisation and seeds

- The paired-minus-unpaired effect is +0.021 from the NLI checkpoint and −0.093 from the generic checkpoint, with
  per-seed values spanning −0.30 to +0.06; one generic paired run did not converge (dev macro-F1 0.56).
- In both initialisations the largest positive per-operator effect of pairing is on cross-references (+0.204 without
  NLI pre-training), i.e. exactly the operator whose two sides differ by one digit and whose label is a function of
  that digit. This is the motivation for the "edit-token shortcut" hypothesis (Pilot 2).
- Training budget: 12 of 15 runs select the last of three epochs (not converged); pairing could interact with
  convergence speed. Any confirmatory study needs a fixed, longer budget or learning curves.

## 7. Family difficulty, complexity and shift

- Dev (vehicles) is harder than both test families for every NLI-initialised group (A5: 0.84–0.89 vs. 0.87–0.96
  item accuracy), so "dev → test drop" is not a measure of shift.
- Complexity matters within operators: for fine-tuned groups, flip-pair accuracy is 0.07–0.16 lower on pairs with
  more conditions than the operator median (A1, within-operator analysis). Per-operator comparisons must therefore be
  complexity-matched (A2 does this for exemptions vs. references).
- Edit position: the hold-out models drop to 0.57 when the edit is in the last third of the document, which is where
  cross-reference articles are placed; position and operator are confounded by construction.

## 8. Other checks

- *Label distribution*: every operator has exactly balanced labels in test (80/80 for each two-label operator), so
  per-operator flip-pair accuracy is not driven by label priors.
- *Template shortcuts*: the hypothesis-only model is at 0.415 (majority 0.390) and 0 on flip pairs by construction;
  the new shortcut (A6) is document-side and invisible to hypothesis-only and partial-input baselines (cf. Feng et
  al., 2019).
- *Data leakage*: integrity checks pass (disjoint families, no duplicates, reserved templates test-only); the re-run
  of `verify_integrity.py` on the merged branch passes.
- *Input format*: the zero-shot conclusions hold in both formats, but see below.
- *Word frequency*: not tested.

## 9. A reinterpretation of the zero-shot results

With the facts in the premise, DeBERTa-v3-base (NLI), DeBERTa-v3-base (MNLI-FEVER-ANLI) and RoBERTa-large agree with
the lazy reader on 98.3%, 98.2% and 96.6% of the 2,560 test items (Cohen's κ 0.970, 0.968, 0.937; `lazy_agreement.json`).
Their behaviour is almost entirely described by "is the claimed obligation stated, and is it negated?". The original
report described these models as missing hard edits; the more accurate description is that they do not read
conditions at all. Their aggregate metrics (accuracy 0.53, flip-pair 0.30) coincide with those of the lazy reader
(0.529, 0.300), which solves exactly the negation and topic-swap pairs.

## 10. Problems in the metrics themselves

1. **Flip-pair accuracy and lazy readers.** A reader that only checks whether the obligation is stated solves 2 of 8
   flip operators perfectly; flip-pair accuracy averages over operators, so 0.30 can mean "reads nothing but the
   topic". Reporting per-operator results, or program identification, is necessary.
2. **Invariance rewards insensitivity.** Near-miss/invariance pairs are passed by any model that does not change its
   answer; a lazy reader has invariance 1.0 on all but topic-related pairs.
3. **Evidence sets mix necessary and decisive sentences.** For entailed items the gold evidence includes satisfied
   conditions, whose removal does not change the label; "evidence" in the registered sense is not "decisive".
4. **Benchmark identifiability is unmeasured.** No metric reports how many items separate plausible heuristics from
   the rule; the cross-reference dimension has zero such items.
