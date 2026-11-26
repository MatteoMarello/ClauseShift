# Human validation protocol

No human annotation has been carried out. This document specifies what should be done, by whom, and how it will be
analysed. Nothing here may be reported as a result until the annotations exist.

## 0. What is and is not human validation

| Activity | Status | Counts as human validation? |
|---|---|---|
| Generator-derived labels (`gold_label`) | exist | No |
| Unit tests and the 706-pair removal check | exist | No (they check internal consistency of the generator) |
| Single-LLM audit of the 112-item sample (`review/clauseshift_llm_audit.md`, 112/112 agreement) | exists | **No.** It is a consistency check by one model; it cannot establish human agreement |
| Blind human annotation (this protocol) | not done | Yes, once completed and scored with `scripts/score_review.py` (Part A) or the scripts named below |

The LLM annotations and the generator key must not be shown to human annotators before they submit.

## 1. Why humans are needed here

1. **Label validity.** Labels come from a specification; templates may express it imperfectly. The LLM audit flagged
   one convention (rows 24 and 78: does a document that never mentions an obligation settle a negative claim?).
2. **Strict comparisons are a convention.** The audit's sharpest finding is that models read "more than 50" with the
   value 50 as satisfied. If competent human readers also do so, part of the "error" is a property of the language,
   not of the models. This must be measured before any claim about boundary failures.
3. **New probes.** The cross-reference probes (Pilot 2 and the confirmatory study) introduce constructions such as
   "Article 1 does not apply to owners of electric cars" for a petrol-car owner. Their labels look obvious; that has
   to be checked, not assumed.

## 2. Annotation tasks

### Part A — label validity (existing sample)
- Items: the 112 blind items in `review/annotation_sheet.csv` (56 pairs, 4 per operator, 2 test families).
- Question: "Given only the document and the case facts, is the claim entailed, contradicted, or not settled
  (insufficient)?" plus a free-text comment and an ambiguity flag.

### Part B — strict boundaries (new)
- Items: 40 boundary items (case value exactly at a threshold or date cutoff; 20 numeric, 20 date; templates "more
  than", "exceeds", "above", "after") and 40 matched non-boundary items, drawn from new families (protocol §3 of
  `EXPERIMENT_PROTOCOL.md`), shuffled with 40 fillers from other operators.
- Same question as Part A. Additional question for boundary items only *after* the label is given: "How confident are
  you (1–5)?"
- Analysis: share of annotators who choose the strict reading; per-template breakdown; compare with model error
  direction.

### Part C — cross-reference probes (new)
- Items: 60 items from the confirmatory probe set: 20 `xref_other_art1`, 20 `xref_case_art1`, 20 `xref_case_art2`,
  shuffled with 40 fillers.
- Same question; plus a naturalness rating (1–5) of the document.

Estimated effort: Part A ≈ 112 items, B ≈ 120, C ≈ 100 → about 330 items, roughly 3–4 hours per annotator.

## 3. Annotators

- At least **three** independent annotators per item. Fluent readers of English; no legal training is required for
  these fictional rules (the task is reading comprehension of explicit conditions). Legal expertise is needed only
  for external-validity work on real contracts (Part D, optional, not planned).
- Annotators must not have seen the generator, the labels, the LLM annotations or model outputs.
- The project author may annotate only if they have not seen the labels of the specific items; otherwise they act as
  adjudicator only. Recommended: the author recruits two or three fellow students and acts as adjudicator.
- No personal data is collected beyond an anonymous annotator ID; informed consent text and the right to withdraw
  are given in the instructions. Check whether the university requires ethics approval for unpaid peer annotation of
  synthetic text (usually not, but it is the author's responsibility to check).

## 4. Instructions (to be given verbatim)

> You will read short fictional rule documents (numbered articles) and facts about one case, followed by a claim.
> Decide whether the claim is **entailed** (the document and facts make it true), **contradicted** (they make it
> false), or **insufficient** (they do not settle it). Use only what is written. Do not use knowledge of real law.
> Read conditions literally: "only if", "only to", "unless" restrict the rule. If you find an item ambiguous, choose the
> label you think a careful reader would choose and tick "ambiguous", explaining why in one sentence.

Calibration: six worked examples (one per main construction) shown before annotation, with their answers and a
one-line justification. None of the calibration items appears in the annotated sets. Rows 24 and 78 of the existing
sample are used as calibration cases for the open-world convention, as the LLM audit recommends, and are excluded from
the agreement statistics.

## 5. Analysis plan

- Agreement among humans: Krippendorff's α (nominal) and Fleiss' κ, with 95% bootstrap intervals over items; raw
  pairwise agreement.
- Agreement with generator labels: majority human label vs. generator, overall and per operator; Cohen's κ.
- Pair-level: share of minimal pairs where the human majority labels both sides as the generator does.
- Adjudication: items without a majority, or where the majority disagrees with the generator, are discussed by the
  adjudicator with the annotators; the pre-adjudication labels are reported, and every adjudication decision is
  logged with a reason. Items judged genuinely ambiguous are reported, not silently dropped.
- Error analysis: categorise disagreements (template wording, convention, case-fact parsing, annotator slip).
- Decision rule for the benchmark: if human–generator agreement on an operator is below 0.85, that operator's results
  are reported with a validity warning and the template is revised for future versions (v2 remains frozen).

## 6. Deliverables of the annotation

`review/human_annotations_<annotator-id>.csv` (raw), `review/human_agreement.json` (computed), and a short report.
The LLM audit and the human results are reported in separate sections.
