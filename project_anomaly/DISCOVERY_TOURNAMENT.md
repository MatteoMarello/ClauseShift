# Discovery tournament

Sixteen candidates, written before any pilot was run. Each is scored 1–5 on eight criteria; the total is not a
precise measurement, only a way to make the choice explicit. Cost is CPU time on the 4-core machine.

## Candidates

**C1. Copy is not compare.** Phenomenon: 100% of fine-tuned boundary errors take the "satisfied" reading; at the
boundary the case value and the cutoff are the same string. Question: are these errors caused by string identity
rather than by non-strict comparison? Closest work: numeracy-as-NLI (Mahendra et al. 2025), numerical representation
invariance (arXiv 2609.25009), semantic sensitivity (EACL 2024). Difference: a minimal intervention that keeps the
value and changes only the form, at the boundary. Alternative: non-strict semantics; approximate comparison. Cheapest
experiment: equal values in different surface forms + cutoff ± 1 controls, inference on 4 saved checkpoints (~10 min).
Falsified if boundary accuracy does not improve when the forms differ (difference-in-differences ≤ 0.10). Useful if
falsified: evidence for genuine non-strict semantics, which then needs the human baseline. Generalises to any
comparison of literals (amounts, dates, versions, IDs).

**C2. Errors that respect the symmetry.** Phenomenon: the task has an exact label symmetry (negating the claim swaps
entailed/contradicted, fixes insufficient). Question: are model errors covariant under it (a consistent wrong reading)
or not (instability)? Does symmetrised decoding help? Closest: negation consistency and negation augmentation
(arXiv 2405.04872; EACL 2024 negation studies), ConCoRD-style consistency correction. Difference: using the share of
*covariant errors* as a measure of how program-like a model's errors are, and predicting the gain of symmetrisation
from it. Alternative: models simply cannot process "not required" claims. Cheapest: negated-claim test set, inference
(~15 min). Falsified if covariance does not separate model classes or the gain is not predicted by it. Useful if
falsified: a clean negation-consistency measurement on rule documents.

**C3. Strategy trajectories during fine-tuning.** Question: does the identified program change abruptly and in a
fixed order during training? Closest: Juneja et al. 2023 (basins), McCoy et al. 2020 (seed variability),
Vandermeerschen & de Lhoneux 2025 (emergence of syntactic heuristics), "Reasoning stabilization point" (arXiv
2601.11625). Difference: identification of a full rule-reading program at each checkpoint, using minimum
discriminating sets for cheap evaluation. Alternative: smooth improvement in all dimensions. Cheapest: one
re-training run with evaluation every 25 steps on ~100 discriminating items (~25–30 min). Falsified if the program
changes gradually with no plateau structure. Useful anyway: acquisition order of rule dimensions.

**C4. Accuracy up, reading down.** Phenomenon A1. Question: are accuracy gains from input-format changes explained by
convergence towards a degenerate program? Closest: prompt/format sensitivity literature. Difference: decomposing
accuracy on lazy-right vs condition-dependent items. Alternative: label-bias artefacts (shown for RoBERTa).
Cost: zero (saved predictions). Status: observed; model-dependent; a supporting lesson, not a study.

**C5. How many killing examples fix a non-identified shortcut?** Question: dose–response of adding k
mutant-killing items (cross-references naming another category) to training. Closest: minority-example studies
(Tu et al. 2020), HANS augmentation, machine teaching (teaching dimension). Difference: targeted at a lattice mutant.
Cost: ≥ 6 fine-tuning runs (~1.6 h) — over budget for a pilot. Deferred.

**C6. Renaming symmetry vs. reference sensitivity.** Question: are models invariant to consistently renaming
categories/places (a symmetry) while being wrongly sensitive to renumbering articles (references)? Closest: "Names
Don't Matter" (ICML 2026, symbol-invariant Transformer), entity-swap consistency. Difference: relational reasoning
where some renamings are symmetries and others are not. Cost: inference (~15 min). Overlaps C1/C2; lower surprise.

**C7. Event-noun transplant.** Phenomenon A4. Question: does swapping "applications received after" ↔ "projects
starting after" move date accuracy across families? Cost: inference (~10 min). Narrow; might explain A4 but
generalises little.

**C8. Seeds as a distribution over programs.** Phenomenon A3. Question: across many seeds, what is the distribution of
identified programs under underspecification? Needs many seeds; feasible only with a tiny model on a symbolic version
of the task. Cost: moderate engineering, low compute. Deferred.

**C9. Inertia / edit-response function.** Question: how much probability mass moves per decisive edit; is inertia a
model-class constant? Cost: zero. Mostly descriptive of A10.

**C10. Simplicity bias among equivalent programs (MDL).** Question: does SGD choose the shortest-description program
among those equivalent on training data? Hard to define description length non-circularly. Deferred.

**C11. Category anonymisation as a beneficial restriction.** Question: does replacing category phrases by abstract
symbols (consistent per document) remove the lexical-similarity confound and improve category checking? Needs
re-training (2 runs, ~35 min); compare with an inline-normalisation preprocessing. Candidate for later.

**C12. Pair-difference regulariser.** Conventional (contrastive). Rejected without a mechanism.

**C13. Critical number of distinguishing items.** Same as C5 phrased as a transition; deferred with C5.

**C14. A theorem on single-input evidence criteria.** Question: is there a general reason single-input criteria are
satisfiable by programs that ignore the decisive clause? Pen-and-paper; feeds MATHEMATICAL_NOTES.

**C15. Confidence as a program signature.** Do confidently wrong predictions coincide with a lattice program's
prediction more than unconfident ones? Cost: zero. Supporting analysis for C2.

**C16. Reference normalisation preprocessing.** Rewrite cross-references into inline exemptions at test time; does
the cross-reference category insensitivity vanish? Cost: inference (~10 min). Mechanism control for research_next
rather than a discovery.

## Scores (1–5)

| | Originality | Surprise | Falsifiability | Info/compute | Generality | Value to NLP | Feasibility | Educational | Total |
|---|---|---|---|---|---|---|---|---|---|
| C1 Copy is not compare | 4 | 5 | 5 | 5 | 4 | 4 | 5 | 5 | **37** |
| C2 Covariant errors | 3 | 3 | 4 | 4 | 4 | 3 | 5 | 5 | **31** |
| C3 Strategy trajectories | 3 | 4 | 3 | 3 | 4 | 4 | 4 | 5 | **30** |
| C4 Accuracy up, reading down | 3 | 4 | 3 | 5 | 3 | 3 | 5 | 4 | 30 |
| C6 Renaming vs. references | 2 | 3 | 4 | 4 | 4 | 3 | 5 | 4 | 29 |
| C11 Anonymisation restriction | 2 | 3 | 4 | 3 | 3 | 3 | 4 | 4 | 26 |
| C16 Reference normalisation | 2 | 2 | 5 | 4 | 2 | 3 | 5 | 3 | 26 |
| C7 Event-noun transplant | 2 | 3 | 5 | 4 | 1 | 2 | 5 | 3 | 25 |
| C9 Inertia | 2 | 2 | 3 | 5 | 3 | 3 | 5 | 3 | 26 |
| C15 Confidence signature | 2 | 2 | 3 | 5 | 3 | 2 | 5 | 3 | 25 |
| C5/C13 Killing-example dose | 3 | 3 | 4 | 2 | 3 | 4 | 2 | 4 | 25 |
| C8 Seed distribution | 3 | 3 | 3 | 3 | 4 | 3 | 3 | 4 | 26 |
| C14 Single-input theorem | 3 | 2 | 4 | 5 | 3 | 3 | 4 | 4 | 28 |
| C10 MDL preference | 4 | 3 | 2 | 2 | 4 | 3 | 2 | 4 | 24 |
| C12 Pair regulariser | 1 | 1 | 3 | 3 | 3 | 2 | 4 | 2 | 19 |

## Selection for pilots (at most three)

1. **C1** — highest surprise per unit of compute; one surface-form intervention; a clean pre-registered contrast.
2. **C2** — a different perspective (symmetry) on the same models, cheap, and it tests whether errors are
   program-like, which is the hidden assumption of all program-identification work.
3. **C3** — only if C1 and C2 leave budget; one re-training run is the most expensive item.

C4, C14 and C15 are pursued as zero-cost analyses alongside. C5/C13 and C11 are recorded as next steps that need
authorisation for additional training.

## Outcome (added after the pilots)

C1 was falsified (Pilot 1). C2 gave neither predicted pattern (Pilot 2). C3 was not run (needs training). The
inference-only follow-up Pilot 1b (post hoc, declared) and the held-out test led to a new candidate not in the list
above — year blindness after training on date edits (A12) — which is the only direction recommended for a check.
See `PILOT_RESULTS.md` and `RESEARCH_DECISION.md`.
