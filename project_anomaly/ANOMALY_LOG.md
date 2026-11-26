# Anomaly log

Every entry: the observation (with its source file), competing explanations, and the experiment that would
distinguish them. Sources are existing results of the ClauseShift study and `research_next/` (all exploratory);
numbers marked † were computed for this log by `project_anomaly/scripts/mine_anomalies.py`.

## A1. A format fix raises accuracy and lowers condition reading †

Moving the case facts from the hypothesis into the premise raises overall test accuracy for all four zero-shot NLI
models, but accuracy on the 1,206 items whose label depends on a condition (items where the "lazy" program that
ignores conditions is wrong) falls in every model:

| Model | Accuracy std → facts-in-premise | On lazy-right items (1,354) | On condition-dependent items (1,206) |
|---|---|---|---|
| DeBERTa-v3-xsmall NLI | 0.399 → 0.427 | 0.597 → 0.673 | 0.177 → 0.150 |
| DeBERTa-v3-base NLI | 0.504 → 0.526 | 0.921 → 0.984 | 0.035 → 0.012 |
| DeBERTa-v3-base MNLI-FEVER-ANLI | 0.531 → 0.539 | 0.833 → 0.993 | 0.192 → 0.029 |
| RoBERTa-large-MNLI | 0.378 → 0.506 | 0.520 → 0.946 | 0.219 → 0.012 |

Competing explanations: (a) the standard format produced genuine, partial condition reading that the new format
destroys; (b) the standard format produced *accidental* correctness on condition-dependent items through a
"contradicted/neutral" bias (unsupported facts in the hypothesis), which disappears when the bias does. Distinguishing
evidence already available: pair-level flip accuracy (both sides right) cannot be produced by a constant bias. For
DeBERTa MNLI-FEVER-ANLI, exception/scope flip-pair accuracy falls 0.26 → 0.15 and 0.23 → 0.05 (`results/EXTENDED_ANALYSIS.md`)
— (a) holds for this model; for RoBERTa-large it rises from 0.00 (b). Status: real but model-dependent; a candidate
general lesson ("accuracy gains can be convergence to a degenerate program").

## A2. Strict comparisons read as non-strict — or identical strings read as "satisfied"?

100% of fine-tuned boundary errors reproduce the satisfied side's label (`research_next/results/AUDIT_TABLES.md`, A3;
38 boundary pairs). At the boundary, the case value is written with **exactly the same string** as the cutoff
("more than 9 credits" / "asks for 9 credits"; "after 15 December 2025" / "received on 15 December 2025").
Competing explanations: (a) non-strict semantics (the model computes ≥); (b) **string identity**: a value that
appears verbatim in the condition is treated as matching it, as in scope conditions, where a matching place name
*does* satisfy the condition; (c) approximate comparison (errors near the cutoff on both sides). Distinguishing
experiment: equality written in a different surface form (dates "15 December 2025" vs "December 15, 2025"; amounts
"€85,000" vs "€85000"), plus cutoff ± 1 controls. (a) predicts errors persist, (b) predicts they vanish when the strings
differ, (c) predicts errors at ± 1 as well. → Pilot candidate.

## A3. An irrelevant sentence flips almost every answer in one model, almost none in a model with equal accuracy

"Article 2 does not apply to <case category>" (irrelevant: Article 2 is another obligation) changes the answer of the
generic-init *unpaired* model in 85–97% of base cases and of the generic-init *paired* model in 8–19%
(`research_next/results/PROBE_TABLE.md`); their test accuracies are 0.752 and 0.778. Explanations: training regime
selects different programs (pairs contrast the digit); seed idiosyncrasy (one seed each). Distinguishing: more seeds
(not authorised); a tiny-model replication where many seeds are cheap.

## A4. The same date logic, halved by a change of noun

Fine-tuned date flip-pair accuracy: enrollment 0.28–0.34 vs research_funding 0.59–0.66 (paired/unpaired groups;
`AUDIT_TABLES.md` A3), with identical templates, date distributions and cutoff logic; the families differ in the event
phrase ("applications received after" vs "projects starting after") and the case-date sentence. Explanations: lexical
temporal priors of the event verb; tokenisation of the surrounding words; family-specific date distributions
(excluded by construction). Distinguishing: transplant the event phrase across families (inference only).

## A5. A three-line program matches or beats large NLI models

The lazy program (accuracy 0.529) beats DeBERTa-v3-base NLI (0.504) and RoBERTa-large-MNLI (0.378) in the standard
format and agrees with three models on 96.6–98.3% of items in the facts-in-premise format
(`research_next/results/lazy_agreement.json`). Known in kind (heuristics, partial-input baselines); striking in degree.

## A6. Pairing helps or hurts depending on initialisation

Paired − unpaired flip-pair accuracy: +0.021 (NLI init) vs −0.093 (generic init), driven by one non-converged run
(`results/EXTENDED_ANALYSIS.md`). Explanations: optimisation conflict when both sides of a pair share a hypothesis;
seed noise. Distinguishing: many seeds in a tiny setting.

## A7. A metric that cannot tell the rule from 23 wrong programs

On the pilot transition item set, 24 of 648 programs tie with the intended rule on the joint transition score, and
432 programs are perfect under single-input scoring (`research_next/results/METRIC_MUTANT_AUDIT.md`).

## A8. Two benchmarks, each insufficient

HANS cannot separate lexical overlap from constant entailment (0/30,000 items); MNLI dev separates them but has 27
items contradicting the overlap heuristic (`research_next/results/external/`). A claim needs the union.

## A9. Invariance is maximal for the least capable systems

Near-miss/invariance pairs are passed by models that never change their answer (lazy program: invariance 1.0 except
topic-related pairs; zero-shot models 0.89–0.97 while flip-pair accuracy is 0.07–0.30). Known metric property.

## A10. Decisive edits leave answers unchanged far more often than they change them wrongly

Zero-shot flip pairs: 61–77% insensitive vs 4–16% "changed but wrong" (`results/EXTENDED_ANALYSIS.md`). Models fail by
inertia, not by confusion.

## A11. Training-set size beats training-set relevance for dates

The operator hold-out models never saw a date edit but solve date flip pairs better (0.81) than models that did
(0.62–0.67); they also had 4,200 vs. 2,400 training items. Most likely a size effect; not an anomaly once controlled.
Listed to avoid over-interpretation.

## Entries added after the pilots

**A2 (re-evaluated).** Pilot 1 rejects the string-identity explanation. The "100%" was largely a counting artefact:
on an E/C flip pair, a non-"insufficient" error on the boundary side necessarily copies the other side's label.

**A12. Year-blind date comparison after training on date edits** (post hoc; `results/YEAR_BLINDNESS.md`). On test
items whose date is in an earlier year but later in the calendar than the cutoff (n = 35), accuracy is 0.476 / 0.295
for NLI-init paired / unpaired runs (all six runs ≤ 0.51) and 1.000 for all three operator-hold-out runs, which never
saw date edits. Competing explanations: (a) edits that move dates by 1–120 days rarely change the year, so the year is
under-learned (Joshi & He 2022 mechanism); (b) training-set size (4,200 vs 2,400 items); (c) operator mix. Distinguishing
experiment: retrain with date edits spanning years, and without date edits at matched size (needs approval).
Relevance to A11: part of the hold-out models' date advantage sits in this cell.

**A13. Lattice vs probe disagreement for generic-init models.** Pilot 1b: these models read an isolated threshold or
date condition as satisfied at every distance ("ignore"); the lattice (`research_next`) selected "non-strict" on dev.
Either the lattice's dev items do not separate "ignore" from "non-strict" for these models, or the models behave
differently when other conditions are present. Unresolved.

**A14. Better models have less systematic errors** (Pilot 2, descriptive). P(error recurs under claim negation):
0.35–0.39 (NLI-init fine-tuned), 0.61–0.70 (generic-init), 0.87 (zero-shot NLI). Program identification assumes
errors are program-like; for the strongest models two thirds of errors are not.
