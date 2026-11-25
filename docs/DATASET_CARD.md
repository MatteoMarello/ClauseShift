# Dataset card: ClauseShift v2

## Summary
Synthetic English minimal pairs for three-way inference over short rule-like documents. Each item is a document,
a hypothesis (facts about a case plus a claim that the case is or is not subject to an obligation), a label
(`entailed`, `contradicted`, `insufficient`), and the indices of the decisive sentences. The two items of a pair
share the hypothesis, and their documents differ by one edit operator.

| Split | Families | Items | Pairs | entailed / contradicted / insufficient |
|---|---|---:|---:|---|
| train | procurement, library, travel, housing, food_safety | 4,800 | 2,400 | 1,814 / 1,806 / 1,180 |
| dev | vehicles | 960 | 480 | 346 / 366 / 248 |
| test | enrollment, research_funding | 2,560 | 1,280 | 999 / 943 / 618 |

Content hashes are in `data/manifest.json`; `python scripts/build_data.py` regenerates identical files.

## Operators
| Class | Operator | Edit | Effect on label |
|---|---|---|---|
| flip | exception_add | add an exemption covering the case's category | required ↔ not required |
| flip | xref_redirect | "Article 1 does not apply to X" ↔ "Article 2 …" | required ↔ not required |
| flip | negation | "must" ↔ "are not required to" | required ↔ not required |
| flip | threshold_cross | move a numeric threshold across the case value (25% exact boundary) | required ↔ not required |
| flip | date_cross | move a date cutoff across the case date (25% exact boundary) | required ↔ not required |
| flip | scope_restrict | restrict the rule to another location | required ↔ not required |
| flip | condition_unknown | add a condition on an attribute the case does not state | decided ↔ insufficient |
| flip | topic_swap | Article 1 states a different obligation | decided ↔ insufficient |
| near-miss | exception_near_miss | exemption for a different category | unchanged |
| near-miss | threshold_near_miss | threshold moves but stays on the same side | unchanged |
| near-miss | scope_near_miss | rule restricted to the case's own location | unchanged |
| invariant | paraphrase | different surface templates | unchanged |
| invariant | reorder | conditions of Article 1 reordered | unchanged |
| invariant | distractor_add | an unrelated article is added | unchanged |

Claims are positive ("is required to") or negative ("is not required to") with equal probability; a negative claim
swaps entailed and contradicted. The direction of each flip edit is randomized.

## Provenance and licensing
All documents, names and rules were written for this project (`src/clauseshift/domains.py`) and are fictional.
Names of people and organizations are invented combinations; any resemblance to real entities is unintended. No
real regulation, contract or personal data is used. Released under the repository's MIT license.

## Annotation status
Labels are **generator-derived**: computed from the rule specification by `gold_label`, not by annotators. They are
correct only if the templates express the specification faithfully, which unit tests check for a set of hand-written
cases. A single LLM annotated the blinded, operator-stratified sample of 112 test items (56 pairs) and
matched every generator label (Cohen's κ = 1.000), with two wording flags. See the [audit](../review/clauseshift_llm_audit.md).
The original blinded sample is available in `review/annotation_sheet.csv` for independent human annotation.

## Interpretation conventions (annotation guideline)
- "Applies only if / only to / only … after" is restrictive: a case that fails the condition is not subject to the
  obligation → a positive claim is contradicted.
- "more than", "exceeds", "above", "after" are strict: equality fails the condition.
- An exemption of a category from "Article k" applies only to the obligation stated in Article k.
- If the document does not state the claimed obligation, or the case lacks an attribute that a condition depends on
  (and no other stated condition already fails), the answer is `insufficient`.

## Known artifacts and checks
- Design iteration v1 → v2 removed a claim-polarity shortcut (`results/design_iterations/README.md`).
- Remaining shortcut, measured: a hypothesis-only TF-IDF model reaches 0.431 dev accuracy (majority 0.360) and
  0.000 flip-pair accuracy by construction.
- Integrity checks (`clauseshift.data.check`): pair structure, label relation per operator class, disjoint families,
  no cross-split duplicates, no conflicting labels for identical inputs, reserved templates absent from train/dev,
  zero test entity names seen in train.

## Intended use and limits
Diagnostic evaluation of sensitivity to decisive minimal edits. Not a measure of legal competence, and not
representative of real contracts (sentence variety, length and ambiguity are far lower). Results on ClauseShift
should not be extrapolated to real documents without validation on real text.
